#!/usr/bin/env python3
"""Prepare ranked regularized permeability candidates through the OGS candidate harness."""

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
        "--ranking",
        type=Path,
        default=Path(
            "inversion_workflow/runs/regularized_permeability_candidate_ranking/"
            "REGULARIZED_CANDIDATE_RANKING.json"
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("inversion_workflow/run_config.example.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/regularized_ogs_candidate_set"),
    )
    parser.add_argument("--run-id-prefix", default="regularized_ogs_candidate")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--ogs-mode",
        choices=["skip", "dry-run", "execute"],
        default="dry-run",
    )
    parser.add_argument("--ogs", type=Path)
    parser.add_argument("--sif", type=Path)
    parser.add_argument("--container-runtime")
    parser.add_argument("--docker-apptainer-image", help="Docker image providing apptainer for running --sif.")
    parser.add_argument("--docker-workspace-root", type=Path, help="Host directory mounted at /work for Dockerized Apptainer.")
    parser.add_argument("--ogs-timeout-s", type=int, help="Optional OGS command timeout in seconds.")
    parser.add_argument(
        "--output-variables",
        nargs="*",
        default=DEFAULT_OUTPUT_VARIABLES,
    )
    return parser.parse_args()


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def slugify(value: Any) -> str:
    text = str(value).strip()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text.strip("._-") or "candidate"


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


def finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def json_number(value: Any) -> float | None:
    if not finite(value):
        return None
    return float(value)


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return json_number(value)
    if value is pd.NA or value is None:
        return None
    return value


def selected_candidates(ranking: dict[str, Any]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    roles: dict[str, set[str]] = {}

    for row in ranking.get("pareto_candidates", []):
        candidate_id = str(row["candidate_id"])
        by_id.setdefault(candidate_id, dict(row))
        roles.setdefault(candidate_id, set()).add("pareto_tradeoff")

    for row in ranking.get("scenario_winners", []):
        candidate_id = str(row["candidate_id"])
        by_id.setdefault(candidate_id, dict(row))
        roles.setdefault(candidate_id, set()).add(str(row.get("scenario_id", "scenario_winner")))

    def sort_key(item: dict[str, Any]) -> tuple[float, str]:
        objective = item.get("objective_value", item.get("data_objective_value", np.inf))
        return (float(objective) if finite(objective) else float("inf"), str(item.get("candidate_id", "")))

    output = []
    for candidate_id, row in by_id.items():
        item = dict(row)
        item["candidate_id"] = candidate_id
        item["selection_roles"] = ";".join(sorted(roles.get(candidate_id, set())))
        output.append(item)
    return sorted(output, key=sort_key)


def extract_result_row(
    selection_index: int,
    candidate: dict[str, Any],
    run_id: str,
    summary_path: Path,
    command_record: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    combined = summary.get("combined_summary", {})
    permeability = summary.get("permeability_summary", {})
    state = summary.get("state_summary", {})
    run_input = summary.get("run_input_audit", {})
    release_gate = summary.get("release_gate_audit", {})
    warning_checks = [
        check.get("name", "")
        for check in run_input.get("checks", [])
        if check.get("severity") == "warning"
    ]
    return {
        "selection_order": selection_index,
        "candidate_id": candidate["candidate_id"],
        "selection_roles": candidate.get("selection_roles", ""),
        "run_id": run_id,
        "run_dir": summary.get("run_dir", ""),
        "summary_json": str(summary_path),
        "command_returncode": command_record["returncode"],
        "ogs_mode": summary.get("ogs_mode", ""),
        "active_component_count": combined.get("active_component_count", 0),
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
        "run_input_audit_status": run_input.get("status", ""),
        "run_input_audit_warnings": ";".join(warning_checks),
        "release_gate_status": release_gate.get("status", ""),
        "release_gate_failures": release_gate.get("failure_count", 0),
        "release_gate_warnings": release_gate.get("warning_count", 0),
        "mesh_override": summary.get("mesh_override", ""),
        "source_length_scale_m": candidate.get("length_scale_m", np.nan),
        "source_shift_scale": candidate.get("shift_scale", np.nan),
        "source_affected_cells": candidate.get("affected_cells", np.nan),
        "source_objective_value": candidate.get("objective_value", candidate.get("data_objective_value", np.nan)),
        "source_weighted_rmse_log10": candidate.get("weighted_rmse_log10", np.nan),
        "source_sum_squared_update": candidate.get("sum_squared_applied_log10_shift_all_cells", np.nan),
    }


def write_markdown(path: Path, results: pd.DataFrame, summary: dict[str, Any]) -> None:
    ogs_mode = summary["ogs_mode"]
    if ogs_mode == "execute":
        intro = [
            "This file records executed OGS results for the Pareto/scenario-winner",
            "permeability candidates selected by the regularized ranking.  Each field",
            "was prepared through the candidate harness, run with OGS, sampled against",
            "state targets, and assembled into the active combined objective.",
        ]
        interpretation = [
            "- In execute mode, the selected fields are ranked by the active combined",
            "  objective: direct permeability pulse-test residuals plus sampled NMR",
            "  state residuals where OGS output times and quantities are usable.",
            "- The selected set is deliberately small: it includes the direct-misfit",
            "  winner and damped update candidates that trade direct fit for lower field",
            "  complexity.",
            "- ERT, Taupe/TDR, and RH/suction are still represented as diagnostics,",
            "  projection/operator layers, or boundary-forcing audits until their",
            "  support, calibration, and provenance gates are resolved.",
        ]
    else:
        intro = [
            "This file records the OGS-ready dry-run handoff for the Pareto/scenario-winner",
            "permeability candidates selected by the regularized ranking.  It prepares each",
            "field through the same candidate harness used for production OGS execution.",
        ]
        interpretation = [
            "- In dry-run/skip mode this remains a direct-permeability ranking because no OGS",
            "  state output VTU files are produced by this script invocation.",
            "- The selected set is deliberately small: it includes the direct-misfit",
            "  winner and damped update candidates that trade direct fit for lower field",
            "  complexity.",
            "- When a host OGS executable or an Apptainer/Singularity runtime for the",
            "  collected SIF is available, rerun this script with `--ogs-mode execute`",
            "  plus either `--ogs /path/to/ogs` or `--sif /path/to/apptainer_ogs6.5.4.sif`;",
            "  the same run directories will then be sampled for NMR, ERT/Taupe",
            "  diagnostics, RH audit, and combined objective assembly.",
        ]
    lines = [
        "# Regularized OGS Candidate Set",
        "",
        *intro,
        "",
        f"- Ranking source: `{summary['ranking']}`",
        f"- Selected candidates: {summary['selected_candidate_count']}",
        f"- OGS mode: `{ogs_mode}`",
        f"- Results CSV: `{summary['results_csv']}`",
        "",
        "| Candidate | Roles | Run id | Objective | RMSE log10(k) | State active rows | Run-input status | Release gate |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for _, row in results.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['candidate_id']}`",
                    str(row["selection_roles"]).replace("|", "/"),
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
            *interpretation,
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = repo_root_from_script()
    scripts = repo / "inversion_workflow" / "scripts"
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists, pass --overwrite to replace: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    ranking = read_json(args.ranking)
    candidates = selected_candidates(ranking)
    if not candidates:
        raise SystemExit(f"no selected candidates in {args.ranking}")

    rows: list[dict[str, Any]] = []
    command_log: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = str(candidate["candidate_id"])
        mesh = Path(str(candidate["mesh"]))
        if not mesh.is_absolute():
            mesh = repo / mesh
        mesh = mesh.resolve()
        if not mesh.is_file():
            raise FileNotFoundError(f"candidate mesh not found: {mesh}")

        run_id = f"{args.run_id_prefix}_{index:03d}_{slugify(candidate_id)}"
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
        record["candidate_id"] = candidate_id
        command_log.append(record)
        candidate_summary = read_json(summary_path)
        rows.append(extract_result_row(index, candidate, run_id, summary_path, record, candidate_summary))

    results = pd.DataFrame(rows).sort_values(
        ["total_active_objective_value", "direct_permeability_objective", "selection_order"],
        na_position="last",
    ).reset_index(drop=True)
    results["rank_by_current_objective"] = range(1, len(results) + 1)

    results_path = output_dir / "regularized_ogs_candidate_set_results.csv"
    command_log_path = output_dir / "command_log.json"
    summary_path = output_dir / "REGULARIZED_OGS_CANDIDATE_SET.json"
    md_path = output_dir / "REGULARIZED_OGS_CANDIDATE_SET.md"
    results.to_csv(results_path, index=False)
    command_log_path.write_text(json.dumps(json_ready(command_log), indent=2, sort_keys=True), encoding="utf-8")
    if args.ogs_mode == "execute":
        notes = [
            "This set is selected from the regularized ranking Pareto/scenario winners.",
            "Execute-mode results include direct permeability objectives and sampled NMR state residuals.",
            "ERT, Taupe/TDR, and RH/suction remain diagnostic or boundary/provenance-gated streams until their activation gates pass.",
        ]
    else:
        notes = [
            "This set is selected from the regularized ranking Pareto/scenario winners.",
            "Dry-run/skip results include direct permeability objectives and prepared state targets, but no OGS state residuals from this invocation.",
            "Rerun with OGS execution to compare the same field set against sampled state observations.",
        ]
    summary = {
        "ranking": str(args.ranking),
        "output_dir": str(output_dir),
        "ogs_mode": args.ogs_mode,
        "selected_candidate_count": int(len(candidates)),
        "results_csv": str(results_path),
        "command_log": str(command_log_path),
        "summary_markdown": str(md_path),
        "selected_candidates": json_ready(candidates),
        "best_current_candidate": json_ready(results.iloc[0].to_dict()),
        "notes": notes,
    }
    summary_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(md_path, results, summary)

    print(f"wrote {results_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {md_path}")
    print(f"selected candidates: {len(candidates)}")
    print(f"best current candidate: {summary['best_current_candidate']['candidate_id']}")
    print(f"best current objective: {summary['best_current_candidate']['total_active_objective_value']:.6g}")


if __name__ == "__main__":
    main()
