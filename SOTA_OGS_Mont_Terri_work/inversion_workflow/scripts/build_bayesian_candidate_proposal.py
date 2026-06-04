#!/usr/bin/env python3
"""Rank unexecuted candidate fields with a finite-candidate Bayesian surrogate."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


BASE_FEATURE_COLUMNS = [
    "length_scale_m",
    "shift_scale",
    "cutoff_factor",
    "affected_cells",
    "objective_value",
    "weighted_rmse_log10",
    "sum_squared_applied_log10_shift_all_cells",
    "mean_abs_applied_log10_shift_affected",
    "rms_applied_log10_shift_affected",
    "applied_log10_shift_min",
    "applied_log10_shift_max",
    "optimal_global_permeability_multiplier",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-scores",
        type=Path,
        default=Path("inversion_workflow/runs/adaptive_combined_candidate_plan/all_candidate_scores.csv"),
        help="Scored finite candidate table produced by build_adaptive_combined_candidate_plan.py.",
    )
    parser.add_argument(
        "--executed-evidence",
        type=Path,
        default=Path("inversion_workflow/runs/adaptive_combined_candidate_plan/executed_candidate_evidence.csv"),
        help="Executed-candidate combined objective evidence.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/bayesian_candidate_proposal"),
    )
    parser.add_argument("--max-proposals", type=int, default=6)
    parser.add_argument(
        "--execution-batch-size",
        type=int,
        default=3,
        help="Number of top candidates to copy into next_optimizer_candidate_batch.csv.",
    )
    parser.add_argument(
        "--xi",
        type=float,
        default=0.0,
        help="Expected-improvement exploration offset for a minimization objective.",
    )
    parser.add_argument(
        "--lcb-kappa",
        type=float,
        default=1.0,
        help="Lower-confidence-bound multiplier for secondary ranking.",
    )
    parser.add_argument(
        "--acquisition",
        choices=["lcb", "ei"],
        default="lcb",
        help="Primary acquisition rule: lower confidence bound or expected improvement.",
    )
    return parser.parse_args()


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
        number = float(value)
        return None if not np.isfinite(number) else number
    if value is pd.NA or value is None:
        return None
    return value


def read_inputs(candidate_scores: Path, executed_evidence: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not candidate_scores.exists():
        raise SystemExit(f"candidate score table not found: {candidate_scores}")
    if not executed_evidence.exists():
        raise SystemExit(f"executed evidence table not found: {executed_evidence}")
    candidates = pd.read_csv(candidate_scores)
    executed = pd.read_csv(executed_evidence)
    if candidates.empty:
        raise SystemExit(f"candidate score table is empty: {candidate_scores}")
    if executed.empty:
        raise SystemExit(f"executed evidence table is empty: {executed_evidence}")
    for frame, path in [(candidates, candidate_scores), (executed, executed_evidence)]:
        if "candidate_id" not in frame.columns:
            raise SystemExit(f"`candidate_id` column missing from {path}")
    candidates = candidates.drop_duplicates("candidate_id", keep="first").copy()
    executed = executed.drop_duplicates("candidate_id", keep="first").copy()
    if "state_objective_value" not in executed.columns:
        executed["state_objective_value"] = (
            pd.to_numeric(executed["total_active_objective_value"], errors="coerce")
            - pd.to_numeric(executed["direct_permeability_objective"], errors="coerce")
        )
    return candidates, executed


def build_feature_matrix(candidates: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    features = candidates.copy()
    numeric_columns = [column for column in BASE_FEATURE_COLUMNS if column in features.columns]
    for column in numeric_columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")
    if "length_scale_m" in features.columns:
        features["log_length_scale_m"] = np.log(pd.to_numeric(features["length_scale_m"], errors="coerce"))
        numeric_columns.append("log_length_scale_m")
    if "affected_cells" in features.columns:
        features["log1p_affected_cells"] = np.log1p(
            pd.to_numeric(features["affected_cells"], errors="coerce")
        )
        numeric_columns.append("log1p_affected_cells")
    if "sum_squared_applied_log10_shift_all_cells" in features.columns:
        features["log1p_update_sse"] = np.log1p(
            pd.to_numeric(features["sum_squared_applied_log10_shift_all_cells"], errors="coerce")
        )
        numeric_columns.append("log1p_update_sse")
    feature_frame = features[numeric_columns].replace([np.inf, -np.inf], np.nan)
    medians = feature_frame.median(numeric_only=True)
    feature_frame = feature_frame.fillna(medians).fillna(0.0)
    return feature_frame, numeric_columns


def expected_improvement(best: float, mean: np.ndarray, std: np.ndarray, xi: float) -> np.ndarray:
    std = np.asarray(std, dtype=float)
    mean = np.asarray(mean, dtype=float)
    improvement = best - mean - xi
    output = np.zeros_like(mean, dtype=float)
    positive_std = std > 0.0
    if positive_std.any():
        z = improvement[positive_std] / std[positive_std]
        output[positive_std] = improvement[positive_std] * norm.cdf(z) + std[positive_std] * norm.pdf(z)
    output[~positive_std] = np.maximum(improvement[~positive_std], 0.0)
    return np.maximum(output, 0.0)


def fit_predict(
    candidates: pd.DataFrame,
    executed: pd.DataFrame,
    feature_frame: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged = candidates.merge(
        executed[
            [
                "candidate_id",
                "total_active_objective_value",
                "direct_permeability_objective",
                "state_objective_value",
                "executed_source",
            ]
        ],
        on="candidate_id",
        how="left",
        suffixes=("", "_executed"),
    )
    training_mask = merged["state_objective_value"].notna()
    if int(training_mask.sum()) < 3:
        raise SystemExit("at least three executed candidates are required for the surrogate proposal")
    x_train = feature_frame.loc[training_mask].to_numpy(dtype=float)
    y_train = pd.to_numeric(merged.loc[training_mask, "state_objective_value"], errors="coerce").to_numpy(dtype=float)
    kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(
        length_scale=np.ones(len(feature_columns)),
        length_scale_bounds=(1e-2, 1e2),
        nu=1.5,
    ) + WhiteKernel(noise_level=1.0, noise_level_bounds=(1e-6, 1e4))
    model = make_pipeline(
        StandardScaler(),
        GaussianProcessRegressor(
            kernel=kernel,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=0,
        ),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ConvergenceWarning)
        model.fit(x_train, y_train)
    state_mean, state_std = model.predict(feature_frame.to_numpy(dtype=float), return_std=True)
    scored = merged.copy()
    scored["gp_state_objective_mean"] = state_mean
    scored["gp_state_objective_std"] = state_std
    scored["direct_objective_for_prediction"] = pd.to_numeric(scored["objective_value"], errors="coerce")
    scored["gp_combined_objective_mean"] = scored["direct_objective_for_prediction"] + scored[
        "gp_state_objective_mean"
    ]
    scored["gp_combined_objective_std"] = scored["gp_state_objective_std"]
    executed_combined = pd.to_numeric(
        scored.loc[training_mask, "total_active_objective_value"], errors="coerce"
    )
    best_objective = float(executed_combined.min())
    best_row = scored.loc[training_mask].sort_values("total_active_objective_value").iloc[0]
    metadata = {
        "training_candidate_count": int(training_mask.sum()),
        "feature_columns": feature_columns,
        "best_executed_candidate": str(best_row["candidate_id"]),
        "best_executed_combined_objective": best_objective,
        "best_executed_state_objective": float(best_row["state_objective_value"]),
        "model": "GaussianProcessRegressor(Matern nu=1.5) over finite candidate table, target=state objective",
        "learned_kernel": str(model.named_steps["gaussianprocessregressor"].kernel_),
    }
    return scored, metadata


def add_acquisition_columns(scored: pd.DataFrame, best_objective: float, xi: float, lcb_kappa: float) -> pd.DataFrame:
    output = scored.copy()
    output["expected_improvement"] = expected_improvement(
        best_objective,
        output["gp_combined_objective_mean"].to_numpy(dtype=float),
        output["gp_combined_objective_std"].to_numpy(dtype=float),
        xi,
    )
    output["probability_of_improvement"] = norm.cdf(
        (best_objective - output["gp_combined_objective_mean"]) / output["gp_combined_objective_std"].clip(lower=1e-12)
    )
    output["lower_confidence_bound"] = (
        output["gp_combined_objective_mean"] - lcb_kappa * output["gp_combined_objective_std"]
    )
    output["is_executed_ogs_candidate"] = output["total_active_objective_value"].notna()
    return output


def rank_candidates(scored: pd.DataFrame, acquisition: str) -> pd.DataFrame:
    unexecuted = scored[~scored["is_executed_ogs_candidate"]].copy()
    if unexecuted.empty:
        raise SystemExit("all candidates are already executed")
    if acquisition == "ei":
        unexecuted = unexecuted.sort_values(
            ["expected_improvement", "lower_confidence_bound", "gp_combined_objective_mean", "candidate_id"],
            ascending=[False, True, True, True],
        ).reset_index(drop=True)
    else:
        unexecuted = unexecuted.sort_values(
            ["lower_confidence_bound", "gp_combined_objective_mean", "expected_improvement", "candidate_id"],
            ascending=[True, True, False, True],
        ).reset_index(drop=True)
    unexecuted["proposal_rank"] = range(1, unexecuted.shape[0] + 1)
    return unexecuted


def write_markdown(path: Path, proposals: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Bayesian Candidate Proposal",
        "",
        "This artifact is a finite-candidate optimizer proposal over already generated",
        "smooth permeability fields. It fits the sampled NMR state-objective component",
        "for executed OGS candidates and combines that surrogate with the known direct",
        "permeability objective for each unexecuted candidate.",
        "",
        "It is not a final inversion sampler: it ranks a fixed candidate table and should",
        "be replaced by a continuous optimizer or ensemble sampler if this finite search",
        "no longer answers useful bracketing questions.",
        "",
        "## Evidence",
        "",
        f"- Candidate count: {summary['candidate_count']}",
        f"- Executed training candidates: {summary['training_candidate_count']}",
        f"- Best executed candidate: `{summary['best_executed_candidate']}`",
        f"- Best executed combined objective: {summary['best_executed_combined_objective']:.2f}",
        f"- Model: `{summary['model']}`",
        f"- Acquisition rule: `{summary['acquisition']}`",
        "",
        "## Proposed Execution Batch",
        "",
        "| Rank | Candidate | Predicted combined | Std | Expected improvement | P(improve) | LCB | Direct objective | Reason |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in proposals.head(int(summary["execution_batch_size"])).iterrows():
        reason = "lowest predicted lower confidence bound"
        if summary["acquisition"] == "ei":
            reason = "highest expected improvement over current best"
        if float(row["expected_improvement"]) <= 0.0:
            reason = "low expected improvement; retained only as finite-candidate surrogate exploration"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["proposal_rank"])),
                    f"`{row['candidate_id']}`",
                    f"{float(row['gp_combined_objective_mean']):.2f}",
                    f"{float(row['gp_combined_objective_std']):.2f}",
                    f"{float(row['expected_improvement']):.4g}",
                    f"{float(row['probability_of_improvement']):.3f}",
                    f"{float(row['lower_confidence_bound']):.2f}",
                    f"{float(row['objective_value']):.2f}",
                    reason,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Execution Command",
            "",
            "```bash",
            "python inversion_workflow/scripts/run_inversion_candidate_search.py \\",
            "  --candidate-table inversion_workflow/runs/bayesian_candidate_proposal/next_optimizer_candidate_batch.csv \\",
            "  --sort-column proposal_rank \\",
            "  --max-candidates 3 \\",
            "  --run-id-prefix optimizer_proposed \\",
            "  --ogs-mode execute \\",
            "  --sif /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif \\",
            "  --docker-apptainer-image ghcr.io/apptainer/apptainer:latest \\",
            "  --docker-workspace-root /home/ber0061/Repositories/gesa_mails \\",
            "  --ogs-timeout-s 7200 \\",
            "  --overwrite",
            "```",
            "",
            "## Caveats",
            "",
            "- The Gaussian-process target is the sampled NMR state objective, not all measurement streams.",
            "- Direct permeability misfit is known for each candidate and is added outside the surrogate.",
            "- ERT, Taupe/TDR, RH, and later parameter fields remain gated by the likelihood model.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    candidates, executed = read_inputs(args.candidate_scores, args.executed_evidence)
    feature_frame, feature_columns = build_feature_matrix(candidates)
    scored, metadata = fit_predict(candidates, executed, feature_frame, feature_columns)
    scored = add_acquisition_columns(
        scored,
        float(metadata["best_executed_combined_objective"]),
        xi=args.xi,
        lcb_kappa=args.lcb_kappa,
    )
    proposals = rank_candidates(scored, acquisition=args.acquisition)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    score_path = output_dir / "optimizer_candidate_scores.csv"
    batch_path = output_dir / "next_optimizer_candidate_batch.csv"
    summary_path = output_dir / "OPTIMIZER_CANDIDATE_PROPOSAL.json"
    markdown_path = output_dir / "OPTIMIZER_CANDIDATE_PROPOSAL.md"
    scored.to_csv(score_path, index=False)
    selected = proposals.head(args.execution_batch_size).copy()
    selected.to_csv(batch_path, index=False)
    summary = {
        **metadata,
        "candidate_scores": str(args.candidate_scores),
        "executed_evidence": str(args.executed_evidence),
        "output_dir": str(output_dir),
        "optimizer_candidate_scores_csv": str(score_path),
        "next_optimizer_candidate_batch_csv": str(batch_path),
        "summary_markdown": str(markdown_path),
        "candidate_count": int(candidates.shape[0]),
        "unexecuted_candidate_count": int(proposals.shape[0]),
        "proposal_count": int(min(args.max_proposals, proposals.shape[0])),
        "execution_batch_size": int(selected.shape[0]),
        "xi": float(args.xi),
        "lcb_kappa": float(args.lcb_kappa),
        "acquisition": args.acquisition,
        "top_proposals": json_ready(proposals.head(args.max_proposals).to_dict(orient="records")),
        "notes": [
            "Finite-candidate Bayesian optimizer proposal; it does not execute OGS.",
            "The surrogate fits state objective only and adds known direct objective to rank combined objective.",
            "Execute next_optimizer_candidate_batch.csv before treating proposals as evidence.",
        ],
    }
    summary_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(markdown_path, proposals, summary)
    print(f"wrote {score_path}")
    print(f"wrote {batch_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {markdown_path}")
    print(f"top proposal: {selected.iloc[0]['candidate_id']}")


if __name__ == "__main__":
    main()
