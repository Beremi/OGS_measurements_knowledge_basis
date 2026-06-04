#!/usr/bin/env python3
"""Build normalized CD-A measurement tables from the collected local sources."""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


R_GAS = 8.31446261815324
KELVIN_TEMPERATURE_K = 298.15
LIQUID_DENSITY_KG_M3 = 1095.0
MOLAR_MASS_WATER_KG_MOL = 0.01801528
ATM_PRESSURE_PA = 101325.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("inversion_workflow/observation_manifest.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    return parser.parse_args()


def resolve_path(base: Path, rel: str | Path) -> Path:
    path = Path(rel)
    if path.is_absolute():
        return path
    return (base / path).resolve()


def relative_to_repo(path: Path, repo_root: Path) -> str:
    path = path.resolve()
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def read_manifest(manifest_path: Path) -> tuple[dict[str, Any], Path, Path]:
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_root = resolve_path(manifest_path.parent, manifest["data_root"])
    repo_root = manifest_path.parents[2]
    return manifest, data_root, repo_root


def write_csv(output_dir: Path, name: str, df: pd.DataFrame) -> dict[str, Any]:
    path = output_dir / name
    df.to_csv(path, index=False)
    return {
        "file": name,
        "rows": int(df.shape[0]),
        "columns": list(map(str, df.columns)),
    }


def clean_token(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def to_float(value: Any) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(numeric) if pd.notna(numeric) else math.nan


def parse_german_datetime(value: Any) -> str:
    text = clean_token(value)
    match = re.match(
        r"^(\d{1,2})-([A-Za-z]+)-(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})$",
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii"),
    )
    if not match:
        return ""
    day, month_token, year, hour, minute, second = match.groups()
    month_key = month_token.lower()
    months = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "mrz": 3,
        "apr": 4,
        "mai": 5,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "okt": 10,
        "oct": 10,
        "nov": 11,
        "dez": 12,
        "dec": 12,
    }
    month = months.get(month_key)
    if month is None:
        return ""
    return datetime(
        int(year),
        month,
        int(day),
        int(hour),
        int(minute),
        int(second),
    ).isoformat(sep=" ")


def date_iso(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    parsed = pd.to_datetime(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(parsed):
        return ""
    return parsed.isoformat()


def find_observation(manifest: dict[str, Any], observation_id: str) -> dict[str, Any]:
    for observation in manifest["observations"]:
        if observation["id"] == observation_id:
            return observation
    raise KeyError(observation_id)


def build_nmr_weekly(data_root: Path, repo_root: Path) -> pd.DataFrame:
    base = data_root / "nmr" / "source_files"
    files = [
        base / "2025-09-15_Weekly_2021-2022_at_4S.dat",
        base / "2025-09-15_Weekly_2022-2025_at_4E.dat",
    ]
    frames: list[pd.DataFrame] = []
    for path in files:
        station_match = re.search(r"_at_(4[SE])\.dat$", path.name)
        station = station_match.group(1) if station_match else ""
        df = pd.read_csv(path)
        rows = pd.DataFrame(
            {
                "source_file": relative_to_repo(path, repo_root),
                "station": station,
                "date_raw": df["Date"].astype(str),
                "date_iso": df["Date"].map(parse_german_datetime),
                "water_content_vol_percent": pd.to_numeric(df["Vol.Wat.Content[%]"], errors="coerce"),
                "wc_ci95_vol_percent": pd.to_numeric(df["WC-Conf.Int.95%"], errors="coerce"),
                "t2_ms": pd.to_numeric(df["T2[ms]"], errors="coerce"),
                "t2_ci95_ms": pd.to_numeric(df["T2-Conf.Int.95%"], errors="coerce"),
            }
        )
        caveats: list[str] = []
        for parsed in pd.to_datetime(rows["date_iso"], errors="coerce"):
            if station == "4E" and pd.notna(parsed) and datetime(2025, 2, 1) <= parsed.to_pydatetime() <= datetime(2025, 4, 30, 23, 59, 59):
                caveats.append("device detuned Feb-Apr 2025; email caveat says water content likely overestimated by about 1 vol.%")
            else:
                caveats.append("")
        rows["caveat"] = caveats
        frames.append(rows)
    return pd.concat(frames, ignore_index=True)


def build_nmr_seasonal(data_root: Path, repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    path = data_root / "nmr" / "source_files" / "2025-09-15_saisonally.zip"
    rows: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        for name in sorted(names):
            info = archive.getinfo(name)
            inventory.append(
                {
                    "source_file": relative_to_repo(path, repo_root),
                    "source_member": name,
                    "suffix": Path(name).suffix.lower() or "<none>",
                    "size_bytes": int(info.file_size),
                }
            )
            if not name.lower().endswith(".dat"):
                continue
            match = re.search(r"Niche(\d+)_Y_(\d{4})_M_(\d{2})_D_(\d{2})\.dat$", name)
            if not match:
                niche, campaign_date = "", ""
            else:
                niche_number, year, month, day = match.groups()
                niche = f"Niche {niche_number}"
                campaign_date = f"{year}-{month}-{day}"
            df = pd.read_csv(io.BytesIO(archive.read(name)))
            for _, row in df.iterrows():
                position = clean_token(row.get("Position"))
                if not position:
                    continue
                rows.append(
                    {
                        "source_file": relative_to_repo(path, repo_root),
                        "source_member": name,
                        "niche": niche,
                        "campaign_date": campaign_date,
                        "position": position,
                        "water_content_vol_percent": to_float(row.get("Vol.Wat.Content[%]")),
                        "wc_ci95_vol_percent": to_float(row.get("WC-95%Conf.Int.")),
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(inventory)


def build_taupe_tdr(data_root: Path, repo_root: Path) -> pd.DataFrame:
    path = data_root / "taupe_tdr" / "source_files" / "Taupe_WC.xlsx"
    rows: list[dict[str, Any]] = []
    workbook = pd.ExcelFile(path)
    for sheet in workbook.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        for _, record in df.iterrows():
            record_date = date_iso(record.get("Datum"))
            for column in df.columns:
                column_name = str(column)
                if column_name == "Datum" or not column_name.startswith("MV EDZ"):
                    continue
                band = column_name.replace("MV EDZ", "").strip()
                match = re.match(r"^(\d+)-(\d+)$", band)
                rows.append(
                    {
                        "source_file": relative_to_repo(path, repo_root),
                        "source_sheet": sheet,
                        "sensor": sheet,
                        "date_iso": record_date,
                        "source_column": column_name,
                        "edz_band_cm": band,
                        "edz_min_cm": int(match.group(1)) if match else np.nan,
                        "edz_max_cm": int(match.group(2)) if match else np.nan,
                        "taupe_value": to_float(record.get(column)),
                        "quantity_note": "Taupe workbook EDZ-band mean value; physical unit/conversion remains to be confirmed",
                    }
                )
    return pd.DataFrame(rows)


def kelvin_liquid_pressure_gauge_pa(rh_percent: float) -> float:
    if not (0.0 < rh_percent < 100.0):
        return math.nan
    coefficient = LIQUID_DENSITY_KG_M3 * R_GAS * KELVIN_TEMPERATURE_K / MOLAR_MASS_WATER_KG_MOL
    return coefficient * math.log(rh_percent / 100.0)


def build_rh(data_root: Path, repo_root: Path) -> pd.DataFrame:
    base = data_root / "suction_relative_humidity" / "source_files"
    rows: list[dict[str, Any]] = []
    coefficient = LIQUID_DENSITY_KG_M3 * R_GAS * KELVIN_TEMPERATURE_K / MOLAR_MASS_WATER_KG_MOL
    for sensor_number in [5, 6, 7, 8]:
        path = base / f"OT_RH{sensor_number}.xlsx"
        sheet = f"OT_RH{sensor_number}"
        time_col = f"time{sensor_number}"
        rh_col = f"RH{sensor_number}"
        df = pd.read_excel(path, sheet_name=sheet)
        for _, record in df.iterrows():
            rh = to_float(record.get(rh_col))
            pressure_gauge = kelvin_liquid_pressure_gauge_pa(rh)
            rows.append(
                {
                    "source_file": relative_to_repo(path, repo_root),
                    "source_sheet": sheet,
                    "sensor": f"RH{sensor_number}",
                    "date_iso": date_iso(record.get(time_col)),
                    "rh_percent": rh,
                    "valid_rh_0_100": bool(0.0 < rh < 100.0),
                    "low_outlier_rh_lt_50": bool(rh < 50.0),
                    "above_95_percent_open_twin_caution": bool(rh > 95.0),
                    "liquid_pressure_gauge_pa_kelvin": pressure_gauge,
                    "liquid_pressure_abs_pa_if_gas_101325pa": pressure_gauge + ATM_PRESSURE_PA if not math.isnan(pressure_gauge) else math.nan,
                    "assumed_temperature_K": KELVIN_TEMPERATURE_K,
                    "assumed_liquid_density_kg_m3": LIQUID_DENSITY_KG_M3,
                    "kelvin_coefficient_pa": coefficient,
                }
            )
    return pd.DataFrame(rows)


def infer_campaign_year(text: str) -> str:
    match = re.search(r"(20\d{2})", text)
    return match.group(1) if match else ""


def infer_twin(sheet: str, block_label: str) -> str:
    combined = f"{sheet} {block_label}".lower()
    if "open" in combined or "_ot" in combined:
        return "open"
    if "closed" in combined or "_ct" in combined:
        return "closed"
    borehole = re.search(r"B[C]?D[A_-]?A[_-]?(\d+)", block_label, re.IGNORECASE)
    if borehole and borehole.group(1) in {"32", "33"}:
        return "open"
    if borehole and borehole.group(1) in {"34", "35"}:
        return "closed"
    return ""


def infer_direction(block_label: str) -> str:
    lower = block_label.lower()
    if "horizontal" in lower:
        return "horizontal"
    if "vertical" in lower:
        return "vertical"
    maps = {
        "32": "horizontal",
        "33": "vertical",
        "34": "vertical",
        "35": "horizontal",
        "24": "vertical",
        "25": "horizontal",
        "26": "vertical",
        "27": "horizontal",
    }
    borehole = re.search(r"B[C]?D[A_-]?A[_-]?(\d+)", block_label, re.IGNORECASE)
    if borehole:
        return maps.get(borehole.group(1), "")
    if re.search(r"BFM[-_ ]?D[-_ ]?19", block_label, re.IGNORECASE):
        return "nearly horizontal"
    return ""


def find_header_row(df: pd.DataFrame, needle: str) -> int | None:
    needle = needle.lower()
    for row_idx in range(min(10, df.shape[0])):
        values = [clean_token(value).lower() for value in df.iloc[row_idx].tolist()]
        if any(needle in value for value in values):
            return row_idx
    return None


def extract_interpreted_permeability(path: Path, repo_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    workbook = pd.ExcelFile(path)
    for sheet in workbook.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        header_row = find_header_row(df, "bohrloch tiefe")
        if header_row is None:
            continue
        campaign_note = " | ".join(
            clean_token(value)
            for value in df.iloc[: header_row + 1].to_numpy().flatten().tolist()
            if "MessEinsatz" in clean_token(value) or re.search(r"20\d{2}", clean_token(value))
        )
        year = infer_campaign_year(f"{sheet} {campaign_note}") or infer_campaign_year(path.name)
        for col in range(df.shape[1]):
            if "bohrloch tiefe" not in clean_token(df.iat[header_row, col]).lower():
                continue
            block_label = clean_token(df.iat[header_row - 1, col]) if header_row > 0 else ""
            if not block_label and header_row > 1:
                block_label = clean_token(df.iat[header_row - 2, col])
            perm_col = None
            trans_col = None
            for candidate in range(col + 1, min(col + 5, df.shape[1])):
                header = clean_token(df.iat[header_row, candidate]).lower()
                if "permeab" in header:
                    perm_col = candidate
                if "transmiss" in header:
                    trans_col = candidate
            if perm_col is None and trans_col is None:
                continue
            interval_col = col - 1 if col > 0 else None
            for row_idx in range(header_row + 1, df.shape[0]):
                depth = to_float(df.iat[row_idx, col])
                permeability = to_float(df.iat[row_idx, perm_col]) if perm_col is not None else math.nan
                transmissibility = to_float(df.iat[row_idx, trans_col]) if trans_col is not None else math.nan
                interval_id = to_float(df.iat[row_idx, interval_col]) if interval_col is not None else math.nan
                if math.isnan(depth) and math.isnan(permeability) and math.isnan(transmissibility):
                    continue
                if math.isnan(depth):
                    continue
                rows.append(
                    {
                        "source_file": relative_to_repo(path, repo_root),
                        "source_sheet": sheet,
                        "source_row_1based": int(row_idx + 1),
                        "campaign_year": year,
                        "campaign_note": campaign_note,
                        "block_label": block_label,
                        "twin": infer_twin(sheet, block_label),
                        "direction_inferred": infer_direction(block_label),
                        "interval_id": interval_id,
                        "borehole_depth_m": depth,
                        "permeability_m2": permeability,
                        "transmissibility_m3": transmissibility,
                        "log10_permeability_m2": math.log10(permeability) if permeability > 0 else math.nan,
                        "positive_permeability": bool(permeability > 0),
                    }
                )
    return pd.DataFrame(rows)


def build_permeability_interpreted(data_root: Path, repo_root: Path) -> pd.DataFrame:
    base = data_root / "permeability_pulse_tests" / "source_files"
    files = [
        base / "2025-09-05_CD-A_Permeability.xlsx",
        base / "Permeability_CDA_all_2025.xlsx",
    ]
    frames = [extract_interpreted_permeability(path, repo_root) for path in files]
    return pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)


def build_permeability_pressure_decay(data_root: Path, repo_root: Path) -> pd.DataFrame:
    path = data_root / "permeability_pulse_tests" / "source_files" / "2025-09-05_CD-A_Permeability.xlsx"
    rows: list[dict[str, Any]] = []
    workbook = pd.ExcelFile(path)
    for sheet in workbook.sheet_names:
        if not sheet.startswith("Messdaten_"):
            continue
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        header_row = find_header_row(df, "zeit in s")
        if header_row is None:
            continue
        for col in range(df.shape[1] - 1):
            if "zeit in s" not in clean_token(df.iat[header_row, col]).lower():
                continue
            pressure_header = clean_token(df.iat[header_row, col + 1]).lower()
            if "intervalldruck" not in pressure_header:
                continue
            interval_label = clean_token(df.iat[header_row - 1, col]) if header_row > 0 else ""
            interval_depth_m = to_float(interval_label)
            for row_idx in range(header_row + 1, df.shape[0]):
                time_s = to_float(df.iat[row_idx, col])
                pressure_pa = to_float(df.iat[row_idx, col + 1])
                if math.isnan(time_s) and math.isnan(pressure_pa):
                    continue
                rows.append(
                    {
                        "source_file": relative_to_repo(path, repo_root),
                        "source_sheet": sheet,
                        "source_row_1based": int(row_idx + 1),
                        "interval_label": interval_label,
                        "interval_depth_m": interval_depth_m,
                        "time_s": time_s,
                        "normalized_interval_pressure_pa": pressure_pa,
                    }
                )
    return pd.DataFrame(rows)


def build_permeability_inventory(data_root: Path, repo_root: Path) -> pd.DataFrame:
    base = data_root / "permeability_pulse_tests" / "source_files"
    rows: list[dict[str, Any]] = []
    for path in [
        base / "2025-09-05_CD-A_Permeability.xlsx",
        base / "Permeability_CDA_all_2025.xlsx",
    ]:
        workbook = pd.ExcelFile(path)
        for sheet in workbook.sheet_names:
            df = pd.read_excel(path, sheet_name=sheet, header=None)
            numeric = pd.to_numeric(df.stack(), errors="coerce").dropna()
            positive = numeric[numeric > 0]
            preview = [
                clean_token(value)
                for value in df.iloc[:3].to_numpy().flatten().tolist()
                if clean_token(value)
            ][:12]
            rows.append(
                {
                    "source_file": relative_to_repo(path, repo_root),
                    "source_sheet": sheet,
                    "rows": int(df.shape[0]),
                    "columns": int(df.shape[1]),
                    "non_empty_cells": int(df.notna().sum().sum()),
                    "numeric_cells": int(numeric.shape[0]),
                    "positive_numeric_cells": int(positive.shape[0]),
                    "positive_numeric_min": float(positive.min()) if not positive.empty else math.nan,
                    "positive_numeric_max": float(positive.max()) if not positive.empty else math.nan,
                    "top_left_content_preview": " | ".join(preview),
                }
            )
    return pd.DataFrame(rows)


def parse_ert_timestamp(filename: str) -> str:
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})_open\.data$", filename)
    if not match:
        return ""
    year, month, day, hour, minute = match.groups()
    return f"{year}-{month}-{day}T{hour}:{minute}:00"


def vtk_name_for_index(folder: str, index: int, name_set: set[str]) -> str:
    candidates = [
        f"{folder}/dcinv.result_{index:02d}.vtk",
        f"{folder}/dcinv.result_{index:03d}.vtk",
        f"{folder}/dcinv.result_{index}.vtk",
    ]
    for candidate in candidates:
        if candidate in name_set:
            return candidate
    return ""


def extract_vtk_metadata(text: str) -> dict[str, Any]:
    scalars: list[str] = []
    metadata: dict[str, Any] = {"points": math.nan, "cells": math.nan, "cell_data": math.nan, "point_data": math.nan}
    for line in text.splitlines():
        if line.startswith("POINTS "):
            parts = line.split()
            if len(parts) >= 2:
                metadata["points"] = int(parts[1])
        elif line.startswith("CELLS "):
            parts = line.split()
            if len(parts) >= 2:
                metadata["cells"] = int(parts[1])
        elif line.startswith("CELL_DATA "):
            parts = line.split()
            if len(parts) >= 2:
                metadata["cell_data"] = int(parts[1])
        elif line.startswith("POINT_DATA "):
            parts = line.split()
            if len(parts) >= 2:
                metadata["point_data"] = int(parts[1])
        elif line.startswith("SCALARS "):
            parts = line.split()
            if len(parts) >= 2:
                scalars.append(parts[1])
    metadata["scalars"] = ";".join(scalars)
    return metadata


def build_ert_tables(data_root: Path, repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    zip_path = data_root / "ert" / "source_files" / "ERT_meas_Niche_open.zip"
    timesteps: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    vtk_samples: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        name_set = set(names)
        by_folder: dict[str, dict[str, list[str]]] = {}
        for name in names:
            folder = str(Path(name).parent).replace("\\", "/")
            by_folder.setdefault(folder, {"vtk": [], "txt": []})
            if name.lower().endswith(".vtk"):
                by_folder[folder]["vtk"].append(name)
            elif name.lower().endswith(".txt"):
                by_folder[folder]["txt"].append(name)
        for folder, grouped in sorted(by_folder.items()):
            if not grouped["vtk"] and not grouped["txt"]:
                continue
            folder_timestamps: list[str] = []
            for timestep_file in sorted(grouped["txt"]):
                lines = [
                    line.strip()
                    for line in archive.read(timestep_file).decode("utf-8", errors="replace").splitlines()
                    if line.strip()
                ]
                for idx, data_filename in enumerate(lines, start=1):
                    timestamp = parse_ert_timestamp(data_filename)
                    if timestamp:
                        folder_timestamps.append(timestamp)
                    matching_vtk = vtk_name_for_index(folder, idx, name_set)
                    timesteps.append(
                        {
                            "source_file": relative_to_repo(zip_path, repo_root),
                            "source_member": timestep_file,
                            "folder": folder,
                            "timestep_index_in_file": idx,
                            "data_filename": data_filename,
                            "timestamp_iso": timestamp,
                            "matching_vtk_member": matching_vtk,
                            "has_matching_vtk": bool(matching_vtk),
                        }
                    )
            sample_vtk = sorted(grouped["vtk"])[0] if grouped["vtk"] else ""
            sample_metadata: dict[str, Any] = {}
            if sample_vtk:
                sample_metadata = extract_vtk_metadata(archive.read(sample_vtk).decode("utf-8", errors="replace"))
                vtk_samples.append(
                    {
                        "source_file": relative_to_repo(zip_path, repo_root),
                        "sample_vtk_member": sample_vtk,
                        **sample_metadata,
                    }
                )
            inventory.append(
                {
                    "source_file": relative_to_repo(zip_path, repo_root),
                    "folder": folder,
                    "vtk_files": len(grouped["vtk"]),
                    "txt_files": len(grouped["txt"]),
                    "timestep_entries": len([row for row in timesteps if row["folder"] == folder]),
                    "missing_vtk_matches": len([row for row in timesteps if row["folder"] == folder and not row["has_matching_vtk"]]),
                    "first_timestamp_iso": min(folder_timestamps) if folder_timestamps else "",
                    "last_timestamp_iso": max(folder_timestamps) if folder_timestamps else "",
                    "sample_vtk_member": sample_vtk,
                    "sample_points": sample_metadata.get("points", math.nan),
                    "sample_cells": sample_metadata.get("cells", math.nan),
                    "sample_scalars": sample_metadata.get("scalars", ""),
                }
            )

    relation_path = data_root / "ert" / "source_files" / "2025-04-04_WC_vs_RHO_2025-02.xlsx"
    pairs: list[dict[str, Any]] = []
    data = pd.read_excel(relation_path, sheet_name="Data2019+", header=None)
    blocks = [
        ("N3", 0),
        ("N4", 5),
    ]
    for niche, start_col in blocks:
        last_date = ""
        for row_idx in range(2, data.shape[0]):
            raw_date = data.iat[row_idx, start_col]
            if pd.notna(raw_date):
                last_date = date_iso(raw_date)
            water = to_float(data.iat[row_idx, start_col + 1])
            std = to_float(data.iat[row_idx, start_col + 2])
            resistivity = to_float(data.iat[row_idx, start_col + 3])
            location = clean_token(data.iat[row_idx, start_col + 4])
            if math.isnan(water) and math.isnan(resistivity):
                continue
            pairs.append(
                {
                    "source_file": relative_to_repo(relation_path, repo_root),
                    "source_sheet": "Data2019+",
                    "niche": niche,
                    "date_iso": last_date,
                    "location": location,
                    "nmr_water_content_fraction": water,
                    "nmr_water_content_vol_percent": water * 100.0 if not math.isnan(water) else math.nan,
                    "nmr_water_content_std_fraction": std,
                    "resistivity_ohm_m": resistivity,
                }
            )
    kruschwitz = pd.read_excel(relation_path, sheet_name="Kruschwitz2004")
    kruschwitz.insert(0, "source_sheet", "Kruschwitz2004")
    kruschwitz.insert(0, "source_file", relative_to_repo(relation_path, repo_root))
    kruschwitz.columns = [
        re.sub(r"[^a-zA-Z0-9]+", "_", str(column)).strip("_").lower() or "unnamed"
        for column in kruschwitz.columns
    ]
    return pd.DataFrame(inventory), pd.DataFrame(timesteps), pd.DataFrame(vtk_samples), pd.DataFrame(pairs), kruschwitz


def build_coordinates(data_root: Path, repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    coordinate_path = data_root / "coordinates_geometry_layout" / "source_files" / "2025-09-05_Mess_Koord_XY.xlsx"
    coordinate_df = pd.read_excel(coordinate_path, sheet_name="Tabelle1", header=None)
    coordinate_rows: list[dict[str, Any]] = []
    for row_idx in range(2, coordinate_df.shape[0]):
        measurement_type = clean_token(coordinate_df.iat[row_idx, 0])
        if not measurement_type:
            continue
        coordinate_rows.append(
            {
                "source_file": relative_to_repo(coordinate_path, repo_root),
                "source_sheet": "Tabelle1",
                "source_row_1based": int(row_idx + 1),
                "measurement_type": measurement_type,
                "original_3d_x": to_float(coordinate_df.iat[row_idx, 1]),
                "original_3d_y": to_float(coordinate_df.iat[row_idx, 2]),
                "original_3d_z": to_float(coordinate_df.iat[row_idx, 3]),
                "model_xz_x": to_float(coordinate_df.iat[row_idx, 4]),
                "model_xz_y": to_float(coordinate_df.iat[row_idx, 5]),
                "model_xz_z": to_float(coordinate_df.iat[row_idx, 6]),
                "model_xy_x": to_float(coordinate_df.iat[row_idx, 7]),
                "model_xy_y": to_float(coordinate_df.iat[row_idx, 8]),
                "model_xy_z": to_float(coordinate_df.iat[row_idx, 9]),
            }
        )

    borehole_path = data_root / "coordinates_geometry_layout" / "source_files" / "Coordinates_NMR_Taupe_characborehole.xlsx"
    borehole_df = pd.read_excel(borehole_path, sheet_name="Tabelle1", header=None)
    borehole_rows: list[dict[str, Any]] = []
    current_group = "NMR"
    for row_idx in range(2, borehole_df.shape[0]):
        label = clean_token(borehole_df.iat[row_idx, 0])
        if not label:
            continue
        original_x = to_float(borehole_df.iat[row_idx, 1])
        bgr_x = to_float(borehole_df.iat[row_idx, 5])
        if math.isnan(original_x) and math.isnan(bgr_x):
            current_group = label
            continue
        borehole_rows.append(
            {
                "source_file": relative_to_repo(borehole_path, repo_root),
                "source_sheet": "Tabelle1",
                "source_row_1based": int(row_idx + 1),
                "group": current_group,
                "label": label,
                "original_x": original_x,
                "original_y": to_float(borehole_df.iat[row_idx, 2]),
                "original_z": to_float(borehole_df.iat[row_idx, 3]),
                "bgr_model_x": bgr_x,
                "bgr_model_y": to_float(borehole_df.iat[row_idx, 6]),
                "bgr_model_z": to_float(borehole_df.iat[row_idx, 7]),
            }
        )
    return pd.DataFrame(coordinate_rows), pd.DataFrame(borehole_rows)


def build_manifest_summary(manifest: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for observation in manifest["observations"]:
        rows.append(
            {
                "observation_id": observation["id"],
                "measurement_type": observation["measurement_type"],
                "model_role": observation["model_role"],
                "state_or_parameter": observation["state_or_parameter"],
                "primary_quantity": observation["primary_quantity"],
                "model_quantity": observation["model_quantity"],
                "check_count": len(observation["checks"]),
                "check_types": ";".join(sorted({check["type"] for check in observation["checks"]})),
            }
        )
    return pd.DataFrame(rows)


def write_readme(output_dir: Path, generated: list[dict[str, Any]]) -> None:
    generated_rows = "\n".join(
        f"| `{item['file']}` | {item['rows']} | {len(item['columns'])} |"
        for item in sorted(generated, key=lambda row: row["file"])
    )
    readme = f"""# Processed Observation Tables

This folder contains normalized CSV tables built from the collected CD-A measurement
sources.  The tables are derived products: keep the raw files in
`../../../cda_knowledge_base/measurements/` as the authority, and use the
`source_file`, `source_sheet`, and `source_member` columns here to trace every row
back to its original source.

## Generated Tables

| File | Rows | Columns |
| --- | ---: | ---: |
{generated_rows}

## Measurement-Specific Notes

- `nmr_weekly.csv` combines the weekly 4S and 4E NMR monitoring files.  It parses the
  German month names into ISO-like timestamps and flags the February-April 2025 4E
  detuning caveat from the email discussion.
- `nmr_seasonal_profiles.csv` mines the seasonal NMR ZIP directly, without requiring
  a separate extracted folder.  Each row is a campaign-date/position water-content
  value from one `.dat` member in the ZIP.
- `ert_archive_inventory.csv` and `ert_timesteps.csv` mine the open-niche ERT ZIP
  structure.  They do not unpack all VTK files; they map monthly folders, timestep
  lists, timestamps, and matching VTK members for later targeted extraction.
- `ert_nmr_resistivity_pairs.csv` and `ert_kruschwitz2004_relation.csv` normalize the
  water-content/resistivity workbook used for the Archie-type local conversion.
- `permeability_interpreted_values.csv` extracts the interpreted permeability and
  transmissibility interval tables from both permeability workbooks.  It preserves
  zeros and missing values as found; use `positive_permeability` and
  `log10_permeability_m2` for fitting.
- `permeability_pressure_decay.csv` converts the raw pressure-decay sheets
  `Messdaten_BCDA26` and `Messdaten_BCDA27` into a long table of time and normalized
  interval pressure.  No additional test interpretation is applied.
- `rh_open_twin_kelvin.csv` converts RH to Kelvin-equation liquid pressure using
  rho_l = {LIQUID_DENSITY_KG_M3:g} kg/m3, T = {KELVIN_TEMPERATURE_K:g} K, and
  M_w = {MOLAR_MASS_WATER_KG_MOL:g} kg/mol.  The pressure column
  `liquid_pressure_gauge_pa_kelvin` is relative to gas pressure; the absolute column
  adds {ATM_PRESSURE_PA:g} Pa as a documented convention.  Use
  `../scripts/audit_rh_boundary_curve.py` to compare this table with the active OGS
  open-niche pressure curve in a prepared run directory.
- `taupe_tdr_bands.csv` reshapes the Taupe workbook into one row per
  sensor/date/EDZ-band value.  The physical unit/conversion is still flagged as
  unresolved because the workbook itself does not document it; use the separate
  Taupe observation-operator builder for baseline-normalized trend diagnostics and
  candidate absolute conversions.
- `measurement_coordinates_xy.csv` and `borehole_coordinates.csv` preserve the
  coordinate-workbook rows used for model lookup.
- Secondary HM monitoring sources are intentionally parsed by the separate
  `../scripts/build_other_hm_monitoring_inventory.py` companion script because it
  streams a large Tecplot layout file and writes qualitative validation gates rather
  than the main water-content/permeability observation tables.

## Intended Use

These CSVs are the first model-facing layer for observation operators.  They are not
yet an inversion driver and they do not execute OGS.  The next step is to connect
these rows to mesh lookup/sampling code and to define likelihood/error models for
each measurement stream.

## Mesh Lookup Layer

After rebuilding the processed tables, run
`../scripts/build_mesh_observation_lookup.py` from `SOTA_OGS_Mont_Terri_work` to map
coordinate rows and borehole intervals onto the OGS bulk mesh.  That second script
currently writes:

| File | Purpose |
| --- | --- |
| `measurement_mesh_lookup.csv` | Point lookup for rows in `measurement_coordinates_xy.csv`. |
| `borehole_mesh_lookup.csv` | Point lookup for labelled NMR, characterization-borehole, and Taupe endpoints. |
| `borehole_line_mesh_samples.csv` | Line samples for borehole/Taupe segments, for interval-style observation operators. |
| `ogs_bulk_mesh_cells.csv` | Cell centroids and material IDs for the bulk mesh. |
| `mesh_lookup_summary.json` | Mesh bounds, transform convention, and lookup status counts. |

The mesh domain is local.  Rows outside the mesh bounding box are intentionally
retained and flagged as `outside_mesh_bbox_nearest_cell`; rows inside the bounding
box but not inside a triangle are flagged as `inside_mesh_bbox_nearest_cell`.

## Permeability Observation Target Layer

After the mesh lookup exists, run
`../scripts/build_permeability_observation_targets.py` from
`SOTA_OGS_Mont_Terri_work`.  It writes:

| File | Purpose |
| --- | --- |
| `permeability_observation_targets.csv` | One row per interpreted permeability workbook row, with fit usability status. |
| `permeability_observation_cells.csv` | Cell weights for mapped interval targets. |
| `permeability_segment_geometry.csv` | Segment lengths, tangents, and in/out-of-mesh sample counts. |
| `permeability_missing_geometry_audit.csv` | Grouped audit of interpreted rows with source-backed orientation but missing endpoint geometry. |
| `permeability_missing_geometry_audit.md` | Human-readable missing-geometry audit and activation requirements. |
| `permeability_target_summary.json` | Status counts and assumptions. |

The scalar gas pulse-test value is not treated as a tensor component.  The target
rows describe a noisy interval-scale constraint on intrinsic permeability; a later
likelihood should compare it to an interval average of the model tensor field using
an explicitly chosen sensitivity approximation.  Older BCD-A24/25/26/27 and BFM-D19
rows retain direction/orientation evidence from the characterization paper, but stay
outside the active objective until labelled endpoints or an explicitly approved
digitized trace exists.

## State Observation Target Layer

After the mesh lookup exists, run
`../scripts/build_state_observation_targets.py` from `SOTA_OGS_Mont_Terri_work`.  It
writes:

| File | Purpose |
| --- | --- |
| `state_observation_targets.csv` | NMR, RH, Taupe/TDR, and ERT target rows with operator semantics and usability flags. |
| `state_observation_samples.csv` | Mapping from state target rows to OGS lookup cells or line-sample cells where applicable. |
| `state_observation_target_summary.json` | Target counts by measurement family, status, and sample layer. |

This layer keeps different measurement semantics separate: NMR compares to model
`porosity * saturation` with the bound/interlayer-water caveat, RH is boundary
forcing through Kelvin pressure, Taupe/TDR is a trend diagnostic until absolute
calibration is documented, and ERT remains an external field-projection target even
though first-pass Taupe trend, ERT theta-to-resistivity calibration, and ERT spatial
lookup artifacts are now explicit.

## Other HM Monitoring Inventory

After the collected TD minutes, levelling slides, modelling slides and Tecplot layout
exist, run `../scripts/build_other_hm_monitoring_inventory.py` from
`SOTA_OGS_Mont_Terri_work`.  It writes:

| File | Purpose |
| --- | --- |
| `other_hm_visualisation_zones.csv` | Tecplot zones from `VisualisationCDA.dat`, classified by monitoring/support role with coordinate bounds. |
| `other_hm_visualisation_text_labels.csv` | Legend/display labels from the Tecplot layout. |
| `other_hm_levelling_displacements.csv` | Pointwise vertical displacement values from the 2026 precision-levelling slides. |
| `other_hm_qualitative_targets.csv` | Structured validation statements from the 2026 minutes, BGR modelling slides and HERMES input note. |
| `other_hm_monitoring_summary.json` | Status, counts and remaining raw-export blocker. |
| `other_hm_monitoring.md` | Human-readable inventory and missing-export list. |

These artifacts make mini-piezometer, extensometer, crackmeter, laser-scan and
levelling evidence visible to the workflow, but they do not make the stream an active
objective term.  Hard pressure/deformation residuals still need the underlying
Geoscope time-series exports and laser-scan statistical files.

## Taupe/TDR Observation Operator

After the processed tables and mesh lookup exist, run
`../scripts/build_taupe_observation_operator.py` from `SOTA_OGS_Mont_Terri_work`.
It writes:

| File | Purpose |
| --- | --- |
| `taupe_tdr_trend_operator.csv` | Baseline-normalized Taupe anomalies, mapped EDZ-band porosity diagnostics, and candidate absolute conversions. |
| `taupe_tdr_series_summary.csv` | One row per sensor/EDZ-band series with baseline, scale, and net change. |
| `taupe_tdr_observation_operator_summary.json` | Operator status, mapped row counts, physical-range sanity checks, and remaining blocker. |
| `taupe_tdr_observation_operator.md` | Human-readable operator description. |

The current recommended Taupe role is a trend diagnostic against band-averaged
`theta_model = porosity * liquid_saturation`.  Absolute saturation residuals remain
blocked until the Taupe workbook unit or sensor-specific dielectric/water-content
calibration is confirmed.  Run the builder with a Python environment that has
`meshio`, because it reads the OGS `n_rd` porosity field from the VTU mesh.

## ERT Observation Operator

After the processed tables exist, run
`../scripts/build_ert_observation_operator.py` from `SOTA_OGS_Mont_Terri_work`.  It
writes:

| File | Purpose |
| --- | --- |
| `ert_water_content_resistivity_operator.csv` | Power-law theta-to-resistivity fits from paired NMR/resistivity and workbook relation columns. |
| `ert_observation_operator_summary.json` | Recommended first-test relation, ERT timestep coverage, and remaining blocker. |
| `ert_observation_operator.md` | Human-readable operator description. |

The current default first-test relation is `kruschwitz_model_data2019`:
`rho_ohm_m = 1.108 * theta_fraction ** -1.58`, where
`theta_fraction = porosity * liquid_saturation`.

## ERT Spatial Projection Operator

After the ERT calibration exists, run
`../scripts/build_ert_spatial_projection_lookup.py` from
`SOTA_OGS_Mont_Terri_work`.  Use a Python environment with `meshio`, because the
script reads a reference ERT VTK from the ZIP archive.  It writes:

| File | Purpose |
| --- | --- |
| `ert_spatial_projection_lookup.csv` | ERT-cell centroid lookup to OGS cells, with transformed coordinates, sample ERT resistivity, and support flags. |
| `ert_spatial_projection_summary.json` | Transform assumption, lookup counts, ERT timestep coverage, and remaining blocker. |
| `ert_spatial_projection_operator.md` | Human-readable spatial operator description. |

The current lookup uses `model_x = raw_x` and `model_y = raw_y + 500` to place the
ERT x/z mesh in the local OGS x/y frame.  It maps 5,966 ERT cells, with 4,676 inside
an OGS cell and 2,035 also inside the approximate 1.5 m central support mask.  ERT
residuals still need OGS output sampling, transform confirmation, and the exact
near-niche support mask before they should carry numerical weights.

## State Observation Evaluation

After OGS output files are sampled with
`../scripts/sample_ogs_state_outputs.py`, run
`../scripts/evaluate_state_observation_targets.py`.  It writes
`state_observation_evaluation.csv` and `state_observation_evaluation_summary.json`
inside the selected run directory.  NMR rows can become numerical residuals against
model `porosity * saturation`; RH remains boundary forcing, Taupe/TDR has a
baseline-normalized trend diagnostic but remains pending absolute calibration, and
ERT has calibration and spatial lookup artifacts but remains pending OGS outputs and
support confirmation.

## Permeability Target Evaluation

After preparing a run directory with a generated `k_i_rd` field, run
`../scripts/evaluate_permeability_targets.py`.  It writes
`permeability_fit_evaluation.csv` and `permeability_fit_summary.json` into the run
directory.  The evaluator computes directional `e^T K e` predictions for the direct
pulse-test targets and reports duplicate-aware log-space residuals.

Use `../scripts/assemble_inversion_objective.py` after the direct permeability and
state evaluations exist.  It writes a component table and strict JSON summary of the
currently active objective terms.

Use `../scripts/build_measurement_operator_coverage.py` after the candidate
evaluation is refreshed to write `../measurement_operator_coverage.csv`,
`../measurement_operator_coverage_summary.json`, and
`../measurement_operator_coverage.md`.  That audit gives one row per measurement
stream and records whether the stream is an active objective term, a state residual
waiting for OGS outputs, boundary-forcing evidence, diagnostic support, or workflow
support data.

For a full per-candidate pass, use `../scripts/evaluate_inversion_candidate.py`.
It runs the preparation, direct permeability evaluation, optional OGS execution,
state-output sampling, RH boundary audit, state-target evaluation, and combined
objective assembly for one candidate run directory.

Use `../scripts/run_direct_permeability_prior_sweep.py` to rank generated
heterogeneous anisotropic prior/proposal fields by the direct pulse-test objective
before spending OGS runtime on a candidate.

Use `../scripts/fit_smooth_permeability_field_from_targets.py` to build smooth
interval-anchored candidate fields from the direct pulse-test multipliers.  The
script writes length-scale-ranked fields that preserve tensor orientation/anisotropy
while spreading local permeability corrections over nearby cells.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    args = parse_args()
    manifest, data_root, repo_root = read_manifest(args.manifest)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[dict[str, Any]] = []

    generated.append(write_csv(output_dir, "manifest_summary.csv", build_manifest_summary(manifest)))
    generated.append(write_csv(output_dir, "nmr_weekly.csv", build_nmr_weekly(data_root, repo_root)))
    nmr_seasonal, nmr_zip_inventory = build_nmr_seasonal(data_root, repo_root)
    generated.append(write_csv(output_dir, "nmr_seasonal_profiles.csv", nmr_seasonal))
    generated.append(write_csv(output_dir, "nmr_seasonal_zip_inventory.csv", nmr_zip_inventory))
    generated.append(write_csv(output_dir, "taupe_tdr_bands.csv", build_taupe_tdr(data_root, repo_root)))
    generated.append(write_csv(output_dir, "rh_open_twin_kelvin.csv", build_rh(data_root, repo_root)))
    generated.append(write_csv(output_dir, "permeability_interpreted_values.csv", build_permeability_interpreted(data_root, repo_root)))
    generated.append(write_csv(output_dir, "permeability_pressure_decay.csv", build_permeability_pressure_decay(data_root, repo_root)))
    generated.append(write_csv(output_dir, "permeability_workbook_inventory.csv", build_permeability_inventory(data_root, repo_root)))
    ert_inventory, ert_timesteps, ert_vtk_samples, ert_pairs, kruschwitz = build_ert_tables(data_root, repo_root)
    generated.append(write_csv(output_dir, "ert_archive_inventory.csv", ert_inventory))
    generated.append(write_csv(output_dir, "ert_timesteps.csv", ert_timesteps))
    generated.append(write_csv(output_dir, "ert_vtk_sample_metadata.csv", ert_vtk_samples))
    generated.append(write_csv(output_dir, "ert_nmr_resistivity_pairs.csv", ert_pairs))
    generated.append(write_csv(output_dir, "ert_kruschwitz2004_relation.csv", kruschwitz))
    measurement_coordinates, borehole_coordinates = build_coordinates(data_root, repo_root)
    generated.append(write_csv(output_dir, "measurement_coordinates_xy.csv", measurement_coordinates))
    generated.append(write_csv(output_dir, "borehole_coordinates.csv", borehole_coordinates))

    summary_path = output_dir / "processed_observation_summary.json"
    summary_path.write_text(json.dumps({"generated": generated}, indent=2), encoding="utf-8")
    write_readme(output_dir, generated)

    print(f"wrote {len(generated)} processed observation tables to {output_dir}")
    for item in sorted(generated, key=lambda row: row["file"]):
        print(f"{item['file']}: {item['rows']} rows, {len(item['columns'])} columns")


if __name__ == "__main__":
    main()
