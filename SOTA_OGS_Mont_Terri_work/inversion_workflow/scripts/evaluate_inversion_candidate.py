#!/usr/bin/env python3
"""Evaluate one permeability-field candidate through all available observation layers."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_VARIABLES = ["pressure", "saturation", "temperature", "displacement", "porosity"]
STATE_OBJECTIVE_MODES = ["raw_absolute_theta", "nmr_within_label_trend_anomaly"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("inversion_workflow/run_config.example.json"),
        help="Run-preparation config used when no mesh override is supplied.",
    )
    parser.add_argument("--run-id", required=True, help="Candidate run id under inversion_workflow/runs.")
    parser.add_argument(
        "--mesh-override",
        type=Path,
        help="Existing bulk_w_projections.vtu candidate. If omitted, the field is generated from --config.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace the candidate run directory if it exists.")
    parser.add_argument(
        "--output-variables",
        nargs="*",
        default=DEFAULT_OUTPUT_VARIABLES,
        help="Output variables needed by state-observation operators.",
    )
    parser.add_argument(
        "--ogs-mode",
        choices=["skip", "dry-run", "execute"],
        default="dry-run",
        help="Whether to skip OGS, record a dry-run command, or execute OGS.",
    )
    parser.add_argument("--ogs", type=Path, help="Path to an OGS executable for --ogs-mode execute/dry-run.")
    parser.add_argument("--sif", type=Path, help="Apptainer/Singularity SIF image containing OGS.")
    parser.add_argument("--container-runtime", help="Container runtime for --sif.")
    parser.add_argument("--docker-apptainer-image", help="Docker image providing apptainer for running --sif.")
    parser.add_argument("--docker-workspace-root", type=Path, help="Host directory mounted at /work for Dockerized Apptainer.")
    parser.add_argument("--ogs-timeout-s", type=int, help="Optional OGS command timeout in seconds.")
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="Candidate summary path. Defaults to <run-dir>/CANDIDATE_EVALUATION_SUMMARY.json.",
    )
    parser.add_argument(
        "--release-plan",
        type=Path,
        default=Path("inversion_workflow/inversion_parameter_release_plan.csv"),
        help="Parameter-release plan used to gate candidate runs.",
    )
    parser.add_argument(
        "--skip-release-gate",
        action="store_true",
        help="Skip the parameter-release gate audit for this candidate.",
    )
    parser.add_argument(
        "--state-objective-mode",
        choices=STATE_OBJECTIVE_MODES,
        default="raw_absolute_theta",
        help=(
            "State-observation objective mode passed to assemble_inversion_objective.py. "
            "The default preserves the historical raw absolute-theta NMR residual."
        ),
    )
    return parser.parse_args()


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def load_run_dir(config_path: Path, run_id: str) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return (Path(config["run_root"]) / run_id).resolve()


def run_step(name: str, command: list[str], cwd: Path, allow_failure: bool = False) -> dict[str, Any]:
    started = time.time()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    finished = time.time()
    record = {
        "name": name,
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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    repo = repo_root_from_script()
    run_dir = load_run_dir(args.config, args.run_id)
    summary_path = args.summary_output or (run_dir / "CANDIDATE_EVALUATION_SUMMARY.json")
    scripts = repo / "inversion_workflow" / "scripts"

    steps: list[dict[str, Any]] = []
    prepare_cmd = [
        sys.executable,
        str(scripts / "prepare_ogs_run.py"),
        "--config",
        str(args.config),
        "--run-id",
        args.run_id,
        "--output-variables",
        *args.output_variables,
    ]
    if args.overwrite:
        prepare_cmd.append("--overwrite")
    if args.mesh_override:
        prepare_cmd.extend(["--mesh-override", str(args.mesh_override)])
    steps.append(run_step("prepare_ogs_run", prepare_cmd, repo))

    run_input_audit_json = run_dir / "OGS_RUN_INPUT_AUDIT.json"
    run_input_audit_md = run_dir / "OGS_RUN_INPUT_AUDIT.md"
    steps.append(
        run_step(
            "audit_ogs_run_inputs",
            [
                sys.executable,
                str(scripts / "audit_ogs_run_inputs.py"),
                "--run-dir",
                str(run_dir),
                "--output-json",
                str(run_input_audit_json),
                "--output-md",
                str(run_input_audit_md),
            ],
            repo,
        )
    )

    release_gate_json = run_dir / "INVERSION_RELEASE_GATE_AUDIT.json"
    release_gate_md = run_dir / "INVERSION_RELEASE_GATE_AUDIT.md"
    release_gate_csv = run_dir / "INVERSION_RELEASE_GATE_AUDIT.csv"
    if not args.skip_release_gate:
        steps.append(
            run_step(
                "audit_inversion_release_gates",
                [
                    sys.executable,
                    str(scripts / "audit_inversion_release_gates.py"),
                    "--run-dir",
                    str(run_dir),
                    "--release-plan",
                    str(args.release_plan),
                    "--output-json",
                    str(release_gate_json),
                    "--output-md",
                    str(release_gate_md),
                    "--output-csv",
                    str(release_gate_csv),
                ],
                repo,
            )
        )

    permeability_eval = run_dir / "permeability_fit_evaluation.csv"
    permeability_summary = run_dir / "permeability_fit_summary.json"
    steps.append(
        run_step(
            "evaluate_permeability_targets",
            [
                sys.executable,
                str(scripts / "evaluate_permeability_targets.py"),
                "--mesh",
                str(run_dir / "bulk_w_projections.vtu"),
                "--include-non-usable",
                "--output",
                str(permeability_eval),
                "--summary-output",
                str(permeability_summary),
            ],
            repo,
        )
    )

    if args.ogs_mode != "skip":
        ogs_cmd = [
            sys.executable,
            str(scripts / "run_ogs_model.py"),
            "--run-dir",
            str(run_dir),
        ]
        if args.ogs:
            ogs_cmd.extend(["--ogs", str(args.ogs)])
        if args.sif:
            ogs_cmd.extend(["--sif", str(args.sif)])
        if args.container_runtime:
            ogs_cmd.extend(["--container-runtime", args.container_runtime])
        if args.docker_apptainer_image:
            ogs_cmd.extend(["--docker-apptainer-image", args.docker_apptainer_image])
        if args.docker_workspace_root:
            ogs_cmd.extend(["--docker-workspace-root", str(args.docker_workspace_root)])
        if args.ogs_timeout_s:
            ogs_cmd.extend(["--timeout-s", str(args.ogs_timeout_s)])
        if args.ogs_mode == "dry-run":
            ogs_cmd.append("--dry-run")
        steps.append(run_step("run_ogs_model", ogs_cmd, repo, allow_failure=args.ogs_mode == "execute"))

    ogs_output_dir = run_dir / "ogs_output"
    state_samples = run_dir / "ogs_state_samples.csv"
    steps.append(
        run_step(
            "sample_ogs_state_outputs",
            [
                sys.executable,
                str(scripts / "sample_ogs_state_outputs.py"),
                "--output-dir",
                str(ogs_output_dir),
                "--inventory-output",
                str(run_dir / "ogs_output_inventory.csv"),
                "--samples-output",
                str(state_samples),
                "--summary-output",
                str(run_dir / "ogs_state_sampling_summary.json"),
            ],
            repo,
        )
    )

    steps.append(
        run_step(
            "audit_rh_boundary_curve",
            [
                sys.executable,
                str(scripts / "audit_rh_boundary_curve.py"),
                "--run-dir",
                str(run_dir),
            ],
            repo,
        )
    )

    state_eval = run_dir / "state_observation_evaluation.csv"
    state_summary = run_dir / "state_observation_evaluation_summary.json"
    steps.append(
        run_step(
            "evaluate_state_observation_targets",
            [
                sys.executable,
                str(scripts / "evaluate_state_observation_targets.py"),
                "--ogs-state-samples",
                str(state_samples),
                "--output",
                str(state_eval),
                "--summary-output",
                str(state_summary),
            ],
            repo,
        )
    )

    taupe_diagnostic = run_dir / "taupe_tdr_trend_diagnostic.csv"
    taupe_diagnostic_series = run_dir / "taupe_tdr_trend_diagnostic_series.csv"
    taupe_diagnostic_summary = run_dir / "taupe_tdr_trend_diagnostic_summary.json"
    taupe_diagnostic_markdown = run_dir / "taupe_tdr_trend_diagnostic.md"
    steps.append(
        run_step(
            "evaluate_taupe_tdr_trend_diagnostic",
            [
                sys.executable,
                str(scripts / "evaluate_taupe_tdr_trend_diagnostic.py"),
                "--ogs-state-samples",
                str(state_samples),
                "--output",
                str(taupe_diagnostic),
                "--series-output",
                str(taupe_diagnostic_series),
                "--summary-output",
                str(taupe_diagnostic_summary),
                "--markdown-output",
                str(taupe_diagnostic_markdown),
            ],
            repo,
        )
    )

    combined_components = run_dir / "combined_objective_components.csv"
    combined_summary = run_dir / "combined_objective_summary.json"
    steps.append(
        run_step(
            "assemble_inversion_objective",
            [
                sys.executable,
                str(scripts / "assemble_inversion_objective.py"),
                "--permeability-evaluation",
                str(permeability_eval),
                "--permeability-summary",
                str(permeability_summary),
                "--state-evaluation",
                str(state_eval),
                "--state-summary",
                str(state_summary),
                "--output",
                str(combined_components),
                "--summary-output",
                str(combined_summary),
                "--state-objective-mode",
                args.state_objective_mode,
            ],
            repo,
        )
    )

    summary = {
        "run_id": args.run_id,
        "run_dir": str(run_dir),
        "mesh_override": str(args.mesh_override.resolve()) if args.mesh_override else None,
        "ogs_mode": args.ogs_mode,
        "state_objective_mode": args.state_objective_mode,
        "steps": steps,
        "artifacts": {
            "run_manifest": str(run_dir / "RUN_MANIFEST.json"),
            "run_input_audit": str(run_input_audit_json),
            "run_input_audit_markdown": str(run_input_audit_md),
            "release_gate_audit": str(release_gate_json),
            "release_gate_audit_markdown": str(release_gate_md),
            "release_gate_audit_csv": str(release_gate_csv),
            "permeability_evaluation": str(permeability_eval),
            "permeability_summary": str(permeability_summary),
            "ogs_execution_status": str(run_dir / "OGS_EXECUTION_STATUS.json"),
            "ogs_output_inventory": str(run_dir / "ogs_output_inventory.csv"),
            "ogs_state_samples": str(state_samples),
            "rh_boundary_curve_audit": str(run_dir / "rh_boundary_curve_audit.csv"),
            "rh_boundary_curve_audit_summary": str(run_dir / "rh_boundary_curve_audit_summary.json"),
            "state_evaluation": str(state_eval),
            "state_summary": str(state_summary),
            "taupe_tdr_trend_diagnostic": str(taupe_diagnostic),
            "taupe_tdr_trend_diagnostic_series": str(taupe_diagnostic_series),
            "taupe_tdr_trend_diagnostic_summary": str(taupe_diagnostic_summary),
            "taupe_tdr_trend_diagnostic_markdown": str(taupe_diagnostic_markdown),
            "combined_components": str(combined_components),
            "combined_summary": str(combined_summary),
        },
        "run_input_audit": read_json(run_input_audit_json),
        "release_gate_audit": read_json(release_gate_json),
        "permeability_summary": read_json(permeability_summary),
        "state_summary": read_json(state_summary),
        "taupe_tdr_trend_diagnostic_summary": read_json(taupe_diagnostic_summary),
        "rh_boundary_summary": read_json(run_dir / "rh_boundary_curve_audit_summary.json"),
        "combined_summary": read_json(combined_summary),
        "notes": [
            "This driver evaluates a candidate permeability-field file without changing the OGS governing equations.",
            "The release-gate audit enforces the current staged inversion scope before objective evaluation.",
            "Direct permeability residuals are available immediately from the candidate mesh field.",
            "State residuals become active only after OGS output VTU files exist and are sampled.",
            "Taupe/TDR trend diagnostics are generated for mapped A3/A4 EDZ bands, but remain outside the active objective until the Taupe unit/calibration gate is resolved.",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {summary_path}")
    total = summary["combined_summary"].get("total_active_objective_value")
    print(f"total active objective: {total}")


if __name__ == "__main__":
    main()
