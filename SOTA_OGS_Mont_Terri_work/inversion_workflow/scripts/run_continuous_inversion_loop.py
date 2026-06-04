#!/usr/bin/env python3
"""Run one repeatable continuous-candidate OGS inversion-loop iteration."""

from __future__ import annotations

import argparse
import json
import math
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loop-name", default="lower_support_loop_001")
    parser.add_argument(
        "--loop-output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/continuous_inversion_loop/lower_support_loop_001"),
        help="Directory for this loop iteration's logs and summaries.",
    )
    parser.add_argument(
        "--proposal-output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/lower_support_continuous_candidate_plan"),
        help="Continuous proposal directory to build before and after the OGS batch.",
    )
    parser.add_argument(
        "--search-output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/lower_support_continuous_loop_001_search"),
        help="Output directory for run_inversion_candidate_search.py.",
    )
    parser.add_argument(
        "--cumulative-lower-support-results",
        type=Path,
        default=Path("inversion_workflow/runs/continuous_inversion_loop/lower_support_cumulative_search_results.csv"),
        help="Merged lower-support executed-result table consumed by refreshed planning artifacts.",
    )
    parser.add_argument(
        "--lower-support-base-results",
        type=Path,
        default=Path("inversion_workflow/runs/lower_support_continuous_candidate_search/inversion_candidate_search_results.csv"),
    )
    parser.add_argument(
        "--extra-lower-support-results",
        type=Path,
        action="append",
        default=[],
        help="Additional lower-support search result CSV to include in the cumulative table.",
    )
    parser.add_argument("--loop-search-glob", default="lower_support_continuous_loop_*_search/inversion_candidate_search_results.csv")
    parser.add_argument(
        "--cumulative-results-role",
        choices=["lower-support", "additional"],
        default="lower-support",
        help=(
            "How to pass the merged cumulative result table into the adaptive planner. "
            "Use 'additional' for broad/non-lower-support continuous loops."
        ),
    )
    parser.add_argument(
        "--adaptive-additional-results",
        type=Path,
        action="append",
        default=[],
        help="Additional executed result table to pass to the adaptive planner. May be repeated.",
    )
    parser.add_argument("--skip-proposal-build", action="store_true")
    parser.add_argument("--skip-secondary-plan-refresh", action="store_true")
    parser.add_argument("--skip-release-audit", action="store_true")
    parser.add_argument("--skip-readiness-audit", action="store_true")
    parser.add_argument("--overwrite", action="store_true")

    parser.add_argument("--length-min-m", type=float, default=0.003125)
    parser.add_argument("--length-max-m", type=float, default=0.012)
    parser.add_argument("--shift-min", type=float, default=0.85)
    parser.add_argument("--shift-max", type=float, default=1.08)
    parser.add_argument("--sample-count", type=int, default=96)
    parser.add_argument("--seed", type=int, default=20260529)
    parser.add_argument("--cutoff-factor", type=float, default=3.0)
    parser.add_argument("--max-candidates", type=int, default=3)
    parser.add_argument("--max-proposals", type=int, default=12)
    parser.add_argument("--run-id-prefix", help="Prefix for prepared OGS run directories. Defaults to --loop-name.")

    parser.add_argument(
        "--ogs-mode",
        choices=["skip", "dry-run", "execute"],
        default="execute",
        help="Passed through to run_inversion_candidate_search.py.",
    )
    parser.add_argument("--ogs", type=Path, help="Optional OGS executable path.")
    parser.add_argument("--sif", type=Path, help="Optional Apptainer/Singularity SIF image containing OGS.")
    parser.add_argument("--container-runtime", help="Container runtime for --sif.")
    parser.add_argument("--docker-apptainer-image", help="Docker image providing apptainer for running --sif.")
    parser.add_argument("--docker-workspace-root", type=Path, help="Host directory mounted at /work for Dockerized Apptainer.")
    parser.add_argument("--ogs-timeout-s", type=int, help="Optional OGS command timeout in seconds.")
    return parser.parse_args()


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if pd.isna(value) if not isinstance(value, (list, tuple, dict, str, bytes)) else False:
        return None
    if hasattr(value, "item"):
        try:
            return json_ready(value.item())
        except Exception:
            pass
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(command: list[str], cwd: Path, log_dir: Path, label: str) -> dict[str, Any]:
    started = time.time()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    finished = time.time()
    stdout_path = log_dir / f"{label}.stdout.log"
    stderr_path = log_dir / f"{label}.stderr.log"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    record = {
        "label": label,
        "command": command,
        "command_display": shlex.join(command),
        "returncode": result.returncode,
        "started_at_unix": started,
        "finished_at_unix": finished,
        "duration_s": finished - started,
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "stdout_tail": result.stdout.splitlines()[-40:],
        "stderr_tail": result.stderr.splitlines()[-40:],
    }
    if result.returncode != 0:
        raise RuntimeError(json.dumps(record, indent=2))
    return record


def build_adaptive_command(
    scripts: Path,
    lower_support_results: Path | None = None,
    additional_results: list[Path] | None = None,
) -> list[str]:
    command = [sys.executable, str(scripts / "build_adaptive_combined_candidate_plan.py")]
    if lower_support_results is not None:
        command.extend(["--lower-support-continuous-search-results", str(lower_support_results)])
    for path in additional_results or []:
        command.extend(["--additional-executed-results", str(path)])
    return command


def build_lower_support_plan_command(args: argparse.Namespace, scripts: Path) -> list[str]:
    command = [
        sys.executable,
        str(scripts / "build_continuous_bayesian_candidate_plan.py"),
        "--finite-candidate-scores",
        "inversion_workflow/runs/adaptive_combined_candidate_plan/all_candidate_scores.csv",
        "--executed-evidence",
        "inversion_workflow/runs/adaptive_combined_candidate_plan/executed_candidate_evidence.csv",
        "--output-dir",
        str(args.proposal_output_dir),
        "--length-min-m",
        str(args.length_min_m),
        "--length-max-m",
        str(args.length_max_m),
        "--shift-min",
        str(args.shift_min),
        "--shift-max",
        str(args.shift_max),
        "--sample-count",
        str(args.sample_count),
        "--seed",
        str(args.seed),
        "--cutoff-factor",
        str(args.cutoff_factor),
        "--max-proposals",
        str(args.max_proposals),
        "--execution-batch-size",
        str(args.max_candidates),
    ]
    if args.overwrite:
        command.append("--overwrite")
    return command


def build_focused_lower_support_refresh_command(args: argparse.Namespace, scripts: Path) -> list[str]:
    command = [
        sys.executable,
        str(scripts / "build_continuous_bayesian_candidate_plan.py"),
        "--finite-candidate-scores",
        "inversion_workflow/runs/adaptive_combined_candidate_plan/all_candidate_scores.csv",
        "--executed-evidence",
        "inversion_workflow/runs/adaptive_combined_candidate_plan/executed_candidate_evidence.csv",
        "--output-dir",
        "inversion_workflow/runs/lower_support_continuous_candidate_plan",
        "--length-min-m",
        "0.003125",
        "--length-max-m",
        "0.012",
        "--shift-min",
        "0.85",
        "--shift-max",
        "1.08",
        "--sample-count",
        str(args.sample_count),
        "--seed",
        str(args.seed),
        "--cutoff-factor",
        str(args.cutoff_factor),
        "--max-proposals",
        str(args.max_proposals),
        "--execution-batch-size",
        str(args.max_candidates),
        "--overwrite",
    ]
    return command


def build_search_command(args: argparse.Namespace, scripts: Path, candidate_table: Path) -> list[str]:
    command = [
        sys.executable,
        str(scripts / "run_inversion_candidate_search.py"),
        "--candidate-table",
        str(candidate_table),
        "--sort-column",
        "proposal_rank",
        "--max-candidates",
        str(args.max_candidates),
        "--run-id-prefix",
        args.run_id_prefix or args.loop_name,
        "--output-dir",
        str(args.search_output_dir),
        "--ogs-mode",
        args.ogs_mode,
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
    return command


def copy_plan_snapshot(proposal_dir: Path, loop_output: Path, prefix: str) -> dict[str, str]:
    copied: dict[str, str] = {}
    for name in [
        "CONTINUOUS_CANDIDATE_PLAN.json",
        "CONTINUOUS_CANDIDATE_PLAN.md",
        "continuous_optimizer_candidate_scores.csv",
        "next_continuous_candidate_batch.csv",
    ]:
        source = proposal_dir / name
        if source.exists():
            target = loop_output / f"{prefix}_{name}"
            shutil.copy2(source, target)
            copied[name] = str(target)
    return copied


def result_identity_columns(frame: pd.DataFrame) -> list[str]:
    for column in ["source_candidate_id", "candidate_id", "run_id"]:
        if column in frame.columns:
            return [column]
    return []


def merge_lower_support_results(args: argparse.Namespace, repo: Path) -> dict[str, Any]:
    run_root = repo / "inversion_workflow" / "runs"
    paths = [args.lower_support_base_results]
    paths.extend(sorted(run_root.glob(args.loop_search_glob)))
    paths.extend(args.extra_lower_support_results or [])
    if args.search_output_dir not in [path.parent for path in paths]:
        current = args.search_output_dir / "inversion_candidate_search_results.csv"
        paths.append(current)

    frames: list[pd.DataFrame] = []
    used_paths: list[str] = []
    for path in paths:
        resolved = (repo / path).resolve() if not path.is_absolute() else path.resolve()
        if not resolved.exists():
            continue
        frame = pd.read_csv(resolved)
        if frame.empty:
            continue
        frame = frame.copy()
        frame["search_results_path"] = str(resolved)
        frames.append(frame)
        used_paths.append(str(resolved))
    if not frames:
        raise SystemExit("no lower-support search result tables found to merge")

    cumulative = pd.concat(frames, ignore_index=True, sort=False)
    if "total_active_objective_value" in cumulative.columns:
        cumulative["total_active_objective_value"] = pd.to_numeric(
            cumulative["total_active_objective_value"], errors="coerce"
        )
        cumulative = cumulative.sort_values(
            ["total_active_objective_value", "direct_permeability_objective", "run_id"],
            na_position="last",
        )
    identity = result_identity_columns(cumulative)
    if identity:
        cumulative = cumulative.drop_duplicates(identity, keep="first")
    cumulative = cumulative.reset_index(drop=True)
    if "rank_by_search_objective" in cumulative.columns and "total_active_objective_value" in cumulative.columns:
        cumulative = cumulative.sort_values(
            ["total_active_objective_value", "direct_permeability_objective", "run_id"],
            na_position="last",
        ).reset_index(drop=True)
        cumulative["rank_by_search_objective"] = range(1, cumulative.shape[0] + 1)

    output = (repo / args.cumulative_lower_support_results).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    cumulative.to_csv(output, index=False)
    best = cumulative.iloc[0].to_dict() if not cumulative.empty else {}
    merge_summary = {
        "cumulative_results_csv": str(output),
        "input_result_tables": used_paths,
        "result_count": int(cumulative.shape[0]),
        "best_candidate": json_ready(best),
    }
    summary_path = output.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(merge_summary, indent=2, sort_keys=True), encoding="utf-8")
    merge_summary["summary_json"] = str(summary_path)
    return merge_summary


def adaptive_additional_paths(args: argparse.Namespace, include_cumulative: bool = False) -> list[Path]:
    paths = list(args.adaptive_additional_results or [])
    if include_cumulative and args.cumulative_results_role == "additional" and args.cumulative_lower_support_results.exists():
        paths.append(args.cumulative_lower_support_results)
    return paths


def read_best_from_evidence(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if frame.empty or "total_active_objective_value" not in frame.columns:
        return {}
    frame["total_active_objective_value"] = pd.to_numeric(frame["total_active_objective_value"], errors="coerce")
    return json_ready(frame.sort_values("total_active_objective_value", na_position="last").iloc[0].to_dict())


def executed_run_dirs(evidence_path: Path) -> list[str]:
    if not evidence_path.exists():
        return []
    frame = pd.read_csv(evidence_path)
    if "run_dir" not in frame.columns:
        return []
    seen: list[str] = []
    for value in frame["run_dir"].dropna().astype(str):
        if value and value not in seen and Path(value).is_dir():
            seen.append(value)
    return seen


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    pre_best = summary.get("pre_loop_best_candidate", {})
    post_best = summary.get("post_loop_best_candidate", {})
    search_best = summary.get("search_best_candidate", {})
    release = summary.get("release_gate_summary", {})
    readiness = summary.get("readiness_summary", {})
    lines = [
        "# Continuous Inversion Loop Iteration",
        "",
        "This artifact records one repeatable continuous candidate loop:",
        "refresh evidence, propose continuous fields, execute the proposed OGS batch,",
        "merge the new executed evidence, refresh plans, and rerun release/readiness",
        "audits.",
        "",
        f"- Loop name: `{summary['loop_name']}`",
        f"- OGS mode: `{summary['ogs_mode']}`",
        f"- Proposal directory: `{summary['proposal_output_dir']}`",
        f"- Search directory: `{summary['search_output_dir']}`",
        f"- Cumulative loop results: `{summary['cumulative_results']}`",
        "",
        "## Result",
        "",
        f"- Best before loop: `{pre_best.get('candidate_id')}` / {pre_best.get('total_active_objective_value')}",
        f"- Best in executed loop batch: `{search_best.get('source_candidate_id')}` / {search_best.get('total_active_objective_value')}",
        f"- Best after refreshed evidence: `{post_best.get('candidate_id')}` / {post_best.get('total_active_objective_value')}",
        f"- Improvement this loop: {summary.get('improvement_this_loop')}",
        "",
        "## Verification",
        "",
        f"- Release gate status: `{release.get('status')}` across {release.get('run_count')} runs and {release.get('check_count')} checks",
        f"- Objective readiness state: `{readiness.get('completion_state')}`",
        "",
        "## Files",
        "",
        f"- Executed batch snapshot: `{summary.get('plan_snapshots', {}).get('next_continuous_candidate_batch.csv')}`",
        f"- Search summary: `{summary.get('search_summary_json')}`",
        f"- Command log: `{summary.get('command_log_json')}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = repo_root_from_script()
    scripts = repo / "inversion_workflow" / "scripts"
    args.loop_output_dir = (repo / args.loop_output_dir).resolve() if not args.loop_output_dir.is_absolute() else args.loop_output_dir.resolve()
    args.proposal_output_dir = (
        repo / args.proposal_output_dir
        if not args.proposal_output_dir.is_absolute()
        else args.proposal_output_dir
    ).resolve()
    args.search_output_dir = (
        repo / args.search_output_dir if not args.search_output_dir.is_absolute() else args.search_output_dir
    ).resolve()
    args.cumulative_lower_support_results = (
        repo / args.cumulative_lower_support_results
        if not args.cumulative_lower_support_results.is_absolute()
        else args.cumulative_lower_support_results
    ).resolve()

    if args.loop_output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"loop output directory exists, pass --overwrite to replace: {args.loop_output_dir}")
        shutil.rmtree(args.loop_output_dir)
    args.loop_output_dir.mkdir(parents=True)
    log_dir = args.loop_output_dir / "logs"
    log_dir.mkdir()

    command_log: list[dict[str, Any]] = []
    pre_adaptive = run_command(
        build_adaptive_command(scripts, additional_results=adaptive_additional_paths(args, include_cumulative=True)),
        repo,
        log_dir,
        "01_pre_adaptive_plan",
    )
    command_log.append(pre_adaptive)
    evidence_path = repo / "inversion_workflow/runs/adaptive_combined_candidate_plan/executed_candidate_evidence.csv"
    pre_best = read_best_from_evidence(evidence_path)

    if not args.skip_proposal_build:
        command_log.append(
            run_command(build_lower_support_plan_command(args, scripts), repo, log_dir, "02_lower_support_proposal_plan")
        )
    candidate_table = args.proposal_output_dir / "next_continuous_candidate_batch.csv"
    if not candidate_table.exists():
        raise SystemExit(f"candidate batch table not found: {candidate_table}")
    plan_snapshots = copy_plan_snapshot(args.proposal_output_dir, args.loop_output_dir, "pre_execution")

    command_log.append(
        run_command(build_search_command(args, scripts, candidate_table), repo, log_dir, "03_execute_candidate_batch")
    )
    search_summary_json = args.search_output_dir / "INVERSION_SEARCH_SUMMARY.json"
    search_summary = read_json(search_summary_json)
    search_best = search_summary.get("best_candidate", {})

    merge_summary = merge_lower_support_results(args, repo)
    cumulative_results_path = Path(merge_summary["cumulative_results_csv"])

    lower_support_results = cumulative_results_path if args.cumulative_results_role == "lower-support" else None
    additional_results = adaptive_additional_paths(args)
    if args.cumulative_results_role == "additional":
        additional_results.append(cumulative_results_path)
    command_log.append(
        run_command(
            build_adaptive_command(scripts, lower_support_results, additional_results),
            repo,
            log_dir,
            "04_post_adaptive_plan",
        )
    )

    if not args.skip_secondary_plan_refresh:
        command_log.append(
            run_command([sys.executable, str(scripts / "build_bayesian_candidate_proposal.py")], repo, log_dir, "05_finite_bayesian_proposal")
        )
        broad_command = [
            sys.executable,
            str(scripts / "build_continuous_bayesian_candidate_plan.py"),
            "--overwrite",
        ]
        command_log.append(run_command(broad_command, repo, log_dir, "06_broad_continuous_plan"))
        command_log.append(
            run_command(
                build_focused_lower_support_refresh_command(args, scripts),
                repo,
                log_dir,
                "07_refreshed_lower_support_plan",
            )
        )

    release_summary: dict[str, Any] = {}
    if not args.skip_release_audit:
        run_dirs = executed_run_dirs(evidence_path)
        audit_command = [sys.executable, str(scripts / "audit_inversion_release_gates.py")]
        for run_dir in run_dirs:
            audit_command.extend(["--run-dir", run_dir])
        command_log.append(run_command(audit_command, repo, log_dir, "08_release_gate_audit"))
        release_summary = read_json(repo / "inversion_workflow/inversion_release_gate_audit.json")

    post_best = read_best_from_evidence(evidence_path)
    pre_value = pre_best.get("total_active_objective_value")
    post_value = post_best.get("total_active_objective_value")
    improvement = None
    if isinstance(pre_value, (int, float)) and isinstance(post_value, (int, float)):
        improvement = float(pre_value) - float(post_value)

    latest_json = args.loop_output_dir.parent / "latest_loop_summary.json"
    latest_json.write_text(
        json.dumps(
            json_ready(
                {
                    "loop_name": args.loop_name,
                    "search_best_candidate": search_best,
                    "post_loop_best_candidate": post_best,
                    "improvement_this_loop": improvement,
                    "search_summary_json": str(search_summary_json),
                }
            ),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    readiness_summary: dict[str, Any] = {}
    if not args.skip_readiness_audit:
        command_log.append(
            run_command([sys.executable, str(scripts / "build_objective_readiness_audit.py")], repo, log_dir, "09_objective_readiness_audit")
        )
        readiness_summary = read_json(repo / "inversion_workflow/objective_readiness_audit_summary.json")

    command_log_json = args.loop_output_dir / "command_log.json"
    command_log_json.write_text(json.dumps(json_ready(command_log), indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "loop_name": args.loop_name,
        "ogs_mode": args.ogs_mode,
        "loop_output_dir": str(args.loop_output_dir),
        "proposal_output_dir": str(args.proposal_output_dir),
        "search_output_dir": str(args.search_output_dir),
        "cumulative_lower_support_results": str(cumulative_results_path),
        "cumulative_results": str(cumulative_results_path),
        "pre_loop_best_candidate": pre_best,
        "search_best_candidate": json_ready(search_best),
        "post_loop_best_candidate": post_best,
        "improvement_this_loop": improvement,
        "merged_lower_support_results": merge_summary,
        "plan_snapshots": plan_snapshots,
        "search_summary_json": str(search_summary_json),
        "release_gate_summary": release_summary,
        "readiness_summary": readiness_summary,
        "command_log_json": str(command_log_json),
        "notes": [
            "The source GESA model remains frozen; this loop varies only run-local k_i_rd mesh fields.",
            "The loop is still a proposal-batch workflow, not a production optimizer or ensemble sampler.",
            "Regenerate the report after accepting the refreshed summaries.",
        ],
    }
    summary_json = args.loop_output_dir / "LOOP_ITERATION_SUMMARY.json"
    summary_md = args.loop_output_dir / "LOOP_ITERATION_SUMMARY.md"
    summary_json.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary_md, summary)
    latest_md = args.loop_output_dir.parent / "latest_loop_summary.md"
    shutil.copy2(summary_json, latest_json)
    shutil.copy2(summary_md, latest_md)

    print(f"wrote {summary_json}")
    print(f"wrote {summary_md}")
    print(f"best after loop: {post_best.get('candidate_id')} {post_best.get('total_active_objective_value')}")


if __name__ == "__main__":
    main()
