#!/usr/bin/env python3
"""Inventory OGS VTK outputs and sample state fields at measurement lookup cells."""

from __future__ import annotations

import argparse
import base64
import json
import lzma
import math
import re
import zlib
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd
from meshio.vtu import _vtu


DEFAULT_FIELDS = ["pressure", "saturation", "temperature", "porosity", "displacement"]


def patch_meshio_vtu_compressed_appended_reader() -> None:
    """Limit compressed appended VTU reads to the current DataArray payload.

    OGS 6.5.4 writes appended-base64 VTUs as adjacent base64 records, each with its
    own padding. meshio 5.3.5 tries to base64-decode from the current offset to the
    end of the appended section, so the next DataArray can corrupt the decode. The
    header tells us the compressed byte count for the current array; slicing to that
    encoded length keeps the read bounded and leaves meshio's public API unchanged.
    """

    def read_compressed_binary_bounded(self: Any, data: str | bytes, dtype: np.dtype) -> np.ndarray:
        header_dtype = _vtu.vtu_to_numpy_type[self.header_type]
        if self.byte_order is not None:
            header_dtype = header_dtype.newbyteorder("<" if self.byte_order == "LittleEndian" else ">")
        num_bytes_per_item = np.dtype(header_dtype).itemsize
        num_chars = _vtu.num_bytes_to_num_base64_chars(num_bytes_per_item)
        byte_string = base64.b64decode(data[:num_chars])[:num_bytes_per_item]
        num_blocks = np.frombuffer(byte_string, header_dtype)[0]

        num_header_items = 3 + int(num_blocks)
        num_header_bytes = num_bytes_per_item * num_header_items
        num_header_chars = _vtu.num_bytes_to_num_base64_chars(num_header_bytes)
        byte_string = base64.b64decode(data[:num_header_chars])
        header = np.frombuffer(byte_string, header_dtype)
        block_sizes = header[3:]
        compressed_bytes = int(np.sum(block_sizes))
        compressed_chars = _vtu.num_bytes_to_num_base64_chars(compressed_bytes)
        encoded_payload = data[num_header_chars : num_header_chars + compressed_chars]
        byte_array = base64.b64decode(encoded_payload)[:compressed_bytes]

        if self.byte_order is not None:
            dtype = dtype.newbyteorder("<" if self.byte_order == "LittleEndian" else ">")

        byte_offsets = np.empty(block_sizes.shape[0] + 1, dtype=block_sizes.dtype)
        byte_offsets[0] = 0
        np.cumsum(block_sizes, out=byte_offsets[1:])

        compressor = {"vtkLZMADataCompressor": lzma, "vtkZLibDataCompressor": zlib}[self.compression]
        return np.concatenate(
            [
                np.frombuffer(
                    compressor.decompress(byte_array[byte_offsets[index] : byte_offsets[index + 1]]),
                    dtype=dtype,
                )
                for index in range(int(num_blocks))
            ]
        )

    _vtu.VtuReader.read_compressed_binary = read_compressed_binary_bounded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ogs_output"),
        help="Directory containing OGS .vtu outputs.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("inversion_workflow/processed_observations"),
    )
    parser.add_argument("--fields", nargs="*", default=DEFAULT_FIELDS)
    parser.add_argument(
        "--support-mesh",
        type=Path,
        help=(
            "Prepared bulk mesh containing fixed support fields such as n_rd. "
            "Defaults to <output-dir>/../bulk_w_projections.vtu when present."
        ),
    )
    parser.add_argument(
        "--porosity-field",
        default="n_rd",
        help="Cell-data field in --support-mesh used as porosity fallback when OGS outputs omit porosity.",
    )
    parser.add_argument(
        "--inventory-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ogs_output_inventory.csv"),
    )
    parser.add_argument(
        "--samples-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ogs_state_samples.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("inversion_workflow/runs/direct_fit_observation_run/ogs_state_sampling_summary.json"),
    )
    return parser.parse_args()


def parse_output_name(path: Path) -> dict[str, Any]:
    match = re.search(r"_ts_(\d+)_t_([0-9.+\-eE]+)", path.stem)
    if not match:
        return {"timestep": math.nan, "time_s": math.nan}
    return {"timestep": int(match.group(1)), "time_s": float(match.group(2))}


def first_cell_block(mesh: meshio.Mesh) -> tuple[str, np.ndarray]:
    if not mesh.cells:
        raise ValueError("mesh contains no cells")
    block = mesh.cells[0]
    return block.type, np.asarray(block.data)


def data_dict_for_first_block(mesh: meshio.Mesh) -> dict[str, np.ndarray]:
    cell_type, _ = first_cell_block(mesh)
    return {
        name: np.asarray(values[cell_type])
        for name, values in mesh.cell_data_dict.items()
        if cell_type in values
    }


def field_columns(prefix: str, value: Any) -> dict[str, float]:
    array = np.asarray(value, dtype=float).ravel()
    if array.size == 0:
        return {prefix: math.nan}
    if array.size == 1:
        return {prefix: float(array[0])}
    return {f"{prefix}_{index}": float(component) for index, component in enumerate(array)}


def sample_field(
    field_name: str,
    mesh: meshio.Mesh,
    cell_data: dict[str, np.ndarray],
    cells: np.ndarray,
    cell_id: int,
    support_cell_data: dict[str, np.ndarray] | None = None,
    porosity_field: str = "n_rd",
) -> tuple[str, dict[str, float]]:
    if field_name in cell_data and cell_id < cell_data[field_name].shape[0]:
        return "cell", field_columns(field_name, cell_data[field_name][cell_id])
    if field_name in mesh.point_data and cell_id < cells.shape[0]:
        point_ids = cells[cell_id]
        values = np.asarray(mesh.point_data[field_name], dtype=float)[point_ids]
        return "point_cell_mean", field_columns(field_name, np.mean(values, axis=0))
    if (
        field_name == "porosity"
        and support_cell_data
        and porosity_field in support_cell_data
        and cell_id < support_cell_data[porosity_field].shape[0]
    ):
        return f"support_mesh_cell:{porosity_field}", field_columns(field_name, support_cell_data[porosity_field][cell_id])
    return "missing", field_columns(field_name, [math.nan])


def inventory_output(path: Path) -> tuple[dict[str, Any], meshio.Mesh]:
    mesh = meshio.read(path)
    cell_type, cells = first_cell_block(mesh)
    cell_data = data_dict_for_first_block(mesh)
    metadata = parse_output_name(path)
    row = {
        "file": str(path),
        "name": path.name,
        "timestep": metadata["timestep"],
        "time_s": metadata["time_s"],
        "point_count": int(mesh.points.shape[0]),
        "cell_type": cell_type,
        "cell_count": int(cells.shape[0]),
        "point_fields": ";".join(sorted(mesh.point_data.keys())),
        "cell_fields": ";".join(sorted(cell_data.keys())),
    }
    return row, mesh


def build_lookup_rows(processed_dir: Path) -> pd.DataFrame:
    point_lookup = pd.read_csv(processed_dir / "measurement_mesh_lookup.csv")
    point_rows = point_lookup.assign(
        sample_source="measurement_point",
        sample_label=point_lookup["measurement_type"].astype(str) + "_row_" + point_lookup["source_row_1based"].astype(str),
        segment_label="",
        sample_index=np.nan,
    )
    line_lookup = pd.read_csv(processed_dir / "borehole_line_mesh_samples.csv")
    line_rows = line_lookup.assign(
        sample_source="borehole_line_sample",
        sample_label=line_lookup["segment_label"].astype(str) + "_sample_" + line_lookup["sample_index"].astype(str),
        measurement_type=line_lookup["group"],
        source_file="",
        source_sheet="",
        source_row_1based=np.nan,
    )
    common_columns = [
        "sample_source",
        "sample_label",
        "measurement_type",
        "source_file",
        "source_sheet",
        "source_row_1based",
        "segment_label",
        "sample_index",
        "lookup_x",
        "lookup_y",
        "lookup_status",
        "lookup_cell_id",
        "lookup_material_id",
        "nearest_centroid_distance_m",
    ]
    return pd.concat([point_rows[common_columns], line_rows[common_columns]], ignore_index=True)


def default_support_mesh(output_dir: Path) -> Path | None:
    candidate = output_dir.parent / "bulk_w_projections.vtu"
    return candidate if candidate.is_file() else None


def load_support_cell_data(path: Path | None) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    if path is None:
        return {}, {"support_mesh": None, "support_cell_count": 0, "support_cell_fields": []}
    mesh = meshio.read(path)
    _, cells = first_cell_block(mesh)
    cell_data = data_dict_for_first_block(mesh)
    return cell_data, {
        "support_mesh": str(path),
        "support_cell_count": int(cells.shape[0]),
        "support_cell_fields": sorted(cell_data.keys()),
    }


def sample_outputs(
    output_paths: list[Path],
    lookup_rows: pd.DataFrame,
    fields: list[str],
    support_cell_data: dict[str, np.ndarray] | None = None,
    porosity_field: str = "n_rd",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    inventory_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []

    for path in output_paths:
        inventory_row, mesh = inventory_output(path)
        inventory_rows.append(inventory_row)
        metadata = parse_output_name(path)
        cell_data = data_dict_for_first_block(mesh)
        _, cells = first_cell_block(mesh)
        cell_count = cells.shape[0]

        for _, lookup in lookup_rows.iterrows():
            cell_id = int(lookup["lookup_cell_id"])
            row = {
                "output_file": path.name,
                "timestep": metadata["timestep"],
                "time_s": metadata["time_s"],
                "sample_source": lookup["sample_source"],
                "sample_label": lookup["sample_label"],
                "measurement_type": lookup["measurement_type"],
                "source_file": lookup["source_file"],
                "source_sheet": lookup["source_sheet"],
                "source_row_1based": lookup["source_row_1based"],
                "segment_label": lookup["segment_label"],
                "sample_index": lookup["sample_index"],
                "lookup_x": lookup["lookup_x"],
                "lookup_y": lookup["lookup_y"],
                "lookup_status": lookup["lookup_status"],
                "lookup_cell_id": cell_id,
                "lookup_cell_valid": 0 <= cell_id < cell_count,
                "lookup_material_id": lookup["lookup_material_id"],
                "nearest_centroid_distance_m": lookup["nearest_centroid_distance_m"],
            }
            field_locations = {}
            if row["lookup_cell_valid"]:
                for field in fields:
                    location, values = sample_field(
                        field,
                        mesh,
                        cell_data,
                        cells,
                        cell_id,
                        support_cell_data=support_cell_data,
                        porosity_field=porosity_field,
                    )
                    field_locations[field] = location
                    row.update(values)
            else:
                for field in fields:
                    field_locations[field] = "invalid_cell"
                    row.update(field_columns(field, [math.nan]))
            row["field_locations"] = json.dumps(field_locations, sort_keys=True)
            saturation = row.get("saturation")
            porosity = row.get("porosity")
            if saturation is not None and porosity is not None and np.isfinite(saturation) and np.isfinite(porosity):
                row["theta_from_porosity_times_saturation"] = saturation * porosity
            else:
                row["theta_from_porosity_times_saturation"] = math.nan
            sample_rows.append(row)

    return pd.DataFrame(inventory_rows), pd.DataFrame(sample_rows)


def main() -> None:
    args = parse_args()
    patch_meshio_vtu_compressed_appended_reader()
    output_paths = sorted(args.output_dir.glob("*.vtu")) if args.output_dir.is_dir() else []
    lookup_rows = build_lookup_rows(args.processed_dir)
    support_mesh = args.support_mesh or default_support_mesh(args.output_dir)
    support_cell_data, support_summary = load_support_cell_data(support_mesh)

    if output_paths:
        inventory, samples = sample_outputs(
            output_paths,
            lookup_rows,
            args.fields,
            support_cell_data=support_cell_data,
            porosity_field=args.porosity_field,
        )
    else:
        inventory = pd.DataFrame(
            columns=["file", "name", "timestep", "time_s", "point_count", "cell_type", "cell_count", "point_fields", "cell_fields"]
        )
        samples = pd.DataFrame(
            columns=[
                "output_file",
                "timestep",
                "time_s",
                "sample_source",
                "sample_label",
                "measurement_type",
                "lookup_cell_id",
                "lookup_cell_valid",
                "field_locations",
                "theta_from_porosity_times_saturation",
            ]
        )

    args.inventory_output.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(args.inventory_output, index=False)
    samples.to_csv(args.samples_output, index=False)
    summary = {
        "output_dir": str(args.output_dir),
        "output_file_count": len(output_paths),
        "inventory_output": str(args.inventory_output),
        "samples_output": str(args.samples_output),
        "sample_row_count": int(samples.shape[0]),
        "lookup_row_count_per_output": int(lookup_rows.shape[0]),
        "fields_requested": args.fields,
        "support_mesh": support_summary["support_mesh"],
        "support_mesh_cell_count": support_summary["support_cell_count"],
        "support_mesh_cell_fields": support_summary["support_cell_fields"],
        "porosity_fallback_field": args.porosity_field,
        "notes": [
            "No OGS outputs are generated by this script; it samples existing .vtu files only.",
            "theta_from_porosity_times_saturation is a model-side water-content proxy and does not correct for NMR-bound/interlayer water.",
            "Point-data fields are averaged over the vertices of the lookup cell; cell-data fields are read directly by lookup_cell_id.",
            "If OGS output omits porosity, porosity is read from the prepared support mesh cell field named by porosity_fallback_field.",
        ],
    }
    args.summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"output files: {len(output_paths)}")
    print(f"wrote {args.inventory_output}")
    print(f"wrote {args.samples_output}")
    print(f"wrote {args.summary_output}")


if __name__ == "__main__":
    main()
