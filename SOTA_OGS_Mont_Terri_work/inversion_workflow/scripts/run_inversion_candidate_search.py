#!/usr/bin/env python3
"""Run and rank multiple permeability-field candidates through the evaluation driver."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_OUTPUT_VARIABLES = ["pressure", "saturation", "temperature", "displacement", "porosity"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-table",
        type=Path,
        default=Path("inversion_workflow/runs/smooth_permeability_candidate_search/smooth_fit_results.csv"),
        help="CSV table containing candidate ids and mesh paths.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("inversion_workflow/run_config.example.json"),
        help="Run-preparation config passed to evaluate_inversion_candidate.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/inversion_candidate_search"),
        help="Directory for search summaries and command logs.",
    )
    parser.add_argument("--candidate-id-column", default="candidate_id")
    parser.add_argument("--mesh-column", default="mesh")
    parser.add_argument(
        "--sort-column",
        default="rank_by_objective",
        help="Column used to select candidates before running the full driver.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=4,
        help="Number of candidates from the table to evaluate.",
    )
    parser.add_argument("--run-id-prefix", default="inversion_search")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing search output and run directories.")
    parser.add_argument(
        "--ogs-mode",
        choices=["skip", "dry-run", "execute"],
        default="dry-run",
        help="Passed through to evaluate_inversion_candidate.py.",
    )
    parser.add_argument("--ogs", type=Path, help="Optional OGS executable path for dry-run or execute modes.")
    parser.add_argument("--sif", type=Path, help="Optional Apptainer/Singularity SIF image containing OGS.")
    parser.add_argument("--container-runtime", help="Container runtime for --sif.")
    parser.add_argument("--docker-apptainer-image", help="Docker image providing apptainer for running --sif.")
    parser.add_argument("--docker-workspace-root", type=Path, help="Host directory mounted at /work for Dockerized Apptainer.")
    parser.add_argument("--ogs-timeout-s", type=int, help="Optional OGS command timeout in seconds.")
    parser.add_argument(
        "--output-variables",
        nargs="*",
        default=DEFAULT_OUTPUT_VARIABLES,
        help="Output variables requested in each prepared run.",
    )
    return parser.parse_args()


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def slugify(value: Any) -> str:
    text = str(value).strip()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    text = text.strip("._-")
    return text or "candidate"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(command: list[str], cwd: Path, allow_failure: bool = False) -> dict[str, Any]:
    started = time.time()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    finished = time.time()
    record = {
        "command": command,
        "returncode": result.returncode,
        "started_at_unix": started,
        "finished_at_unix": finished,
        "duration_s": finished - started,
        "stdout_tail": result.stdout.splitlines()[-80:],
        "stderr_tail": result.stderr.splitlines()[-80:],
    }
    if result.returncode != 0 and not allow_failure:
        raise RuntimeError(json.dumps(record, indent=2))
    return record


def read_candidate_table(path: Path, candidate_id_column: str, mesh_column: str, sort_column: str) -> pd.DataFrame:
    table = pd.read_csv(path)
    missing = [column for column in [candidate_id_column, mesh_column] if column not in table.columns]
    if missing:
        raise ValueError(f"candidate table {path} is missing required columns: {missing}")
    if sort_column in table.columns:
        table = table.sort_values(sort_column).reset_index(drop=True)
    return table


def resolve_mesh_path(repo: Path, value: Any) -> Path:
    mesh = Path(str(value))
    if not mesh.is_absolute():
        mesh = repo / mesh
    mesh = mesh.resolve()
    if not mesh.is_file():
        raise FileNotFoundError(f"candidate mesh not found: {mesh}")
    return mesh


def extract_result_row(
    source_row: pd.Series,
    source_candidate_id: str,
    run_id: str,
    run_dir: Path,
    summary_path: Path,
    summary: dict[str, Any],
    command_record: dict[str, Any],
) -> dict[str, Any]:
    combined = summary.get("combined_summary", {})
    permeability = summary.get("permeability_summary", {})
    state = summary.get("state_summary", {})
    run_input_audit = summary.get("run_input_audit", {})
    release_gate = summary.get("release_gate_audit", {})
    warning_checks = [
        check.get("name", "")
        for check in run_input_audit.get("checks", [])
        if check.get("severity") == "warning"
    ]
    return {
        "rank_by_search_objective": 0,
        "source_candidate_id": source_candidate_id,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "summary_json": str(summary_path),
        "command_returncode": command_record["returncode"],
        "active_component_count": combined.get("active_component_count", 0),
        "component_count": combined.get("component_count", 0),
        "total_active_objective_value": combined.get("total_active_objective_value", np.nan),
        "direct_permeability_objective": permeability.get("objective_value", np.nan),
        "direct_permeability_weighted_rmse_log10": permeability.get("weighted_rmse_log10", np.nan),
        "direct_permeability_rows": permeability.get("used_in_objective_rows", 0),
        "direct_permeability_effective_weight": permeability.get("effective_objective_weight", np.nan),
        "state_target_rows": state.get("target_rows", state.get("evaluation_rows", np.nan)),
        "state_active_objective_rows": state.get("active_objective_rows", state.get("used_in_objective_rows", 0)),
        "state_status_counts": json.dumps(
            state.get("evaluation_status", state.get("evaluation_status_counts", {})),
            sort_keys=True,
        ),
        "run_input_audit_status": run_input_audit.get("status", ""),
        "run_input_audit_warnings": ";".join(warning_checks),
        "release_gate_status": release_gate.get("status", ""),
        "release_gate_failures": release_gate.get("failure_count", 0),
        "release_gate_warnings": release_gate.get("warning_count", 0),
        "mesh_override": summary.get("mesh_override", ""),
        "ogs_mode": summary.get("ogs_mode", ""),
        "source_length_scale_m": source_row.get("length_scale_m", np.nan),
        "source_shift_scale": source_row.get("shift_scale", np.nan),
        "source_affected_cells": source_row.get("affected_cells", np.nan),
        "source_direct_objective": source_row.get("objective_value", np.nan),
        "source_weighted_rmse_log10": source_row.get("weighted_rmse_log10", np.nan),
    }


def write_markdown(path: Path, results: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Inversion Candidate Search",
        "",
        "This search runs multiple permeability-field meshes through the full",
        "candidate evaluation driver. In dry-run mode only the direct permeability",
        "component is active; after OGS execution the same table can rank candidates",
        "by the combined permeability plus state-observation objective.",
        "",
        f"- Candidate table: `{summary['candidate_table']}`",
        f"- Evaluated candidates: {summary['evaluated_candidate_count']}",
        f"- OGS mode: `{summary['ogs_mode']}`",
        f"- Results CSV: `{summary['results_csv']}`",
        "",
        "| Rank | Source candidate | Run id | Objective | Direct RMSE | State active rows | Run-input status | Release gate |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for _, row in results.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["rank_by_search_objective"])),
                    f"`{row['source_candidate_id']}`",
                    f"`{row['run_id']}`",
                    f"{float(row['total_active_objective_value']):.2f}",
                    f"{float(row['direct_permeability_weighted_rmse_log10']):.2f}",
                    str(int(row["state_active_objective_rows"])),
                    f"`{row['run_input_audit_status']}`",
                    f"`{row['release_gate_status']}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A dry-run ranking is a permeability-only ranking because no OGS output",
            "  VTU files exist yet.",
            "- With `--ogs-mode execute`, the same driver prepares each run, executes",
            "  OGS, samples state outputs, and ranks the combined objective components.",
            "- This is a deterministic search harness, not a Bayesian sampler. It is",
            "  the reproducible bridge between candidate-field generation and later",
            "  OGS-backed inversion.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = repo_root_from_script()
    output_dir = args.output_dir.resolve()
    scripts = repo / "inversion_workflow" / "scripts"

    if output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists, pass --overwrite to replace: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    table = read_candidate_table(
        args.candidate_table.resolve(),
        args.candidate_id_column,
        args.mesh_column,
        args.sort_column,
    )
    selected = table.head(args.max_candidates).copy()
    if selected.empty:
        raise SystemExit("no candidates selected")

    rows: list[dict[str, Any]] = []
    command_log: list[dict[str, Any]] = []
    for index, source_row in selected.reset_index(drop=True).iterrows():
        source_id = str(source_row[args.candidate_id_column])
        run_id = f"{args.run_id_prefix}_{index + 1:03d}_{slugify(source_id)}"
        mesh = resolve_mesh_path(repo, source_row[args.mesh_column])
        summary_path = output_dir / f"{run_id}_summary.json"
        command = [
            sys.executable,
            str(scripts / "evaluate_inversion_candidate.py"),
            "--config",
            str(args.config),
            "--run-id",
            run_id,
            "--mesh-override",
            str(mesh),
            "--ogs-mode",
            args.ogs_mode,
            "--summary-output",
            str(summary_path),
            "--output-variables",
            *args.output_variables,
        ]
        if args.overwrite:
            command.append("--overwrite")
        if args.ogs:
            command.extend(["--ogs", str(args.ogs)])
        if args.sif:
            command.extend(["--sif", str(args.sif)])
        if args.container_runtime:
            command.extend(["--container-runtime", args.container_runtime])
        if args.docker_apptainer_image:
            command.extend(["--docker-apptainer-image", args.docker_apptainer_image])
        if args.docker_workspace_root:
            command.extend(["--docker-workspace-root", str(args.docker_workspace_root)])
        if args.ogs_timeout_s:
            command.extend(["--ogs-timeout-s", str(args.ogs_timeout_s)])
        record = run_command(command, repo, allow_failure=args.ogs_mode == "execute")
        record["run_id"] = run_id
        record["source_candidate_id"] = source_id
        command_log.append(record)

        candidate_summary = read_json(summary_path)
        run_dir = Path(candidate_summary.get("run_dir", ""))
        rows.append(extract_result_row(source_row, source_id, run_id, run_dir, summary_path, candidate_summary, record))

    results = pd.DataFrame(rows).sort_values(
        ["total_active_objective_value", "direct_permeability_objective", "run_id"],
        na_position="last",
    ).reset_index(drop=True)
    results["rank_by_search_objective"] = range(1, len(results) + 1)
    results_path = output_dir / "inversion_candidate_search_results.csv"
    command_log_path = output_dir / "command_log.json"
    summary_path = output_dir / "INVERSION_SEARCH_SUMMARY.json"
    summary_md_path = output_dir / "INVERSION_SEARCH_SUMMARY.md"

    results.to_csv(results_path, index=False)
    command_log_path.write_text(json.dumps(command_log, indent=2, sort_keys=True), encoding="utf-8")
    best = results.iloc[0].to_dict()
    summary = {
        "candidate_table": str(args.candidate_table),
        "output_dir": str(output_dir),
        "ogs_mode": args.ogs_mode,
        "evaluated_candidate_count": int(results.shape[0]),
        "results_csv": str(results_path),
        "command_log": str(command_log_path),
        "summary_markdown": str(summary_md_path),
        "best_candidate": best,
        "notes": [
            "Dry-run searches rank only currently active objective components.",
            "State-observation rows become active only after OGS output VTU files exist.",
            "The search uses the same candidate driver as production OGS-backed evaluations.",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary_md_path, results, summary)

    print(f"wrote {results_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {summary_md_path}")
    print(f"best run id: {best['run_id']}")
    print(f"best objective: {best['total_active_objective_value']:.6g}")


if __name__ == "__main__":
    main()
