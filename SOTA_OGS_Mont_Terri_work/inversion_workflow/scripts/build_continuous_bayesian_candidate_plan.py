#!/usr/bin/env python3
"""Propose continuous smooth-field candidates beyond the fixed finite grid."""

from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any

import meshio
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bayesian_candidate_proposal import BASE_FEATURE_COLUMNS  # noqa: E402
from fit_smooth_permeability_field_from_targets import (  # noqa: E402
    build_anchor_table,
    cell_centroids,
    read_cell_field,
    run_candidate,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mesh",
        type=Path,
        default=Path("inversion_workflow/runs/smoke_test/bulk_w_projections.vtu"),
    )
    parser.add_argument(
        "--targets",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_observation_targets.csv"),
    )
    parser.add_argument(
        "--target-cells",
        type=Path,
        default=Path("inversion_workflow/processed_observations/permeability_observation_cells.csv"),
    )
    parser.add_argument(
        "--finite-candidate-scores",
        type=Path,
        default=Path("inversion_workflow/runs/adaptive_combined_candidate_plan/all_candidate_scores.csv"),
        help="Finite-grid direct scores used to train the state-objective surrogate.",
    )
    parser.add_argument(
        "--executed-evidence",
        type=Path,
        default=Path("inversion_workflow/runs/adaptive_combined_candidate_plan/executed_candidate_evidence.csv"),
        help="Executed OGS candidate evidence with combined and direct objective values.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("inversion_workflow/runs/continuous_bayesian_candidate_plan"),
    )
    parser.add_argument("--field-name", default="k_i_rd")
    parser.add_argument("--length-min-m", type=float, default=0.00625)
    parser.add_argument("--length-max-m", type=float, default=0.075)
    parser.add_argument("--shift-min", type=float, default=0.70)
    parser.add_argument("--shift-max", type=float, default=1.25)
    parser.add_argument("--sample-count", type=int, default=96)
    parser.add_argument("--seed", type=int, default=20260529)
    parser.add_argument("--cutoff-factor", type=float, default=3.0)
    parser.add_argument("--max-abs-log10-shift", type=float, default=8.0)
    parser.add_argument("--min-k-eigenvalue", type=float, default=1.0e-22)
    parser.add_argument("--max-k-eigenvalue", type=float, default=1.0e-12)
    parser.add_argument("--log10-sigma", type=float, default=0.5)
    parser.add_argument("--lcb-kappa", type=float, default=1.0)
    parser.add_argument("--xi", type=float, default=0.0)
    parser.add_argument("--max-proposals", type=int, default=12)
    parser.add_argument("--execution-batch-size", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true")
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


def candidate_label(length_scale: float, shift_scale: float) -> str:
    label = f"length_{length_scale:.3f}m"
    if not math.isclose(shift_scale, 1.0):
        label = f"{label}_shift_{shift_scale:.3f}"
    return label.replace(".", "p")


def continuous_hyperparameter_samples(args: argparse.Namespace) -> pd.DataFrame:
    if args.length_min_m <= 0.0 or args.length_max_m <= args.length_min_m:
        raise SystemExit("length bounds must be positive and increasing")
    if args.shift_max <= args.shift_min:
        raise SystemExit("shift bounds must be increasing")
    rng = np.random.default_rng(args.seed)

    log_l_min = math.log(args.length_min_m)
    log_l_max = math.log(args.length_max_m)
    random_rows = []
    for _ in range(args.sample_count):
        length = math.exp(float(rng.uniform(log_l_min, log_l_max)))
        shift = float(rng.uniform(args.shift_min, args.shift_max))
        random_rows.append((length, shift, "log_uniform_random"))

    # Deterministic local probes around the current 0.013 m best and the nearby
    # bracket. These keep the proposal stable even if the random seed changes.
    local_lengths = [0.0075, 0.0100, 0.0125, 0.0150, 0.0175, 0.0210, 0.0280, 0.0420]
    local_shifts = [0.80, 0.95, 1.00, 1.05, 1.20]
    local_rows = [
        (length, shift, "deterministic_local_probe")
        for length in local_lengths
        for shift in local_shifts
        if args.length_min_m <= length <= args.length_max_m and args.shift_min <= shift <= args.shift_max
    ]

    rows = []
    seen: set[str] = set()
    for length, shift, source in local_rows + random_rows:
        label = candidate_label(length, shift)
        if label in seen:
            continue
        seen.add(label)
        rows.append(
            {
                "candidate_id": label,
                "length_scale_m": float(length),
                "shift_scale": float(shift),
                "cutoff_factor": args.cutoff_factor,
                "proposal_sample_source": source,
            }
        )
    if not rows:
        raise SystemExit("no continuous samples generated")
    return pd.DataFrame(rows)


def build_feature_matrix(candidates: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    features = candidates.copy()
    numeric_columns = [column for column in BASE_FEATURE_COLUMNS if column in features.columns]
    for column in numeric_columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")
    if "length_scale_m" in features.columns:
        features["log_length_scale_m"] = np.log(pd.to_numeric(features["length_scale_m"], errors="coerce"))
        numeric_columns.append("log_length_scale_m")
    if "affected_cells" in features.columns:
        features["log1p_affected_cells"] = np.log1p(pd.to_numeric(features["affected_cells"], errors="coerce"))
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


def train_state_surrogate(
    finite_scores: pd.DataFrame,
    executed: pd.DataFrame,
    proposal_scores: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    evidence = executed.copy()
    if "state_objective_value" not in evidence.columns:
        evidence["state_objective_value"] = (
            pd.to_numeric(evidence["total_active_objective_value"], errors="coerce")
            - pd.to_numeric(evidence["direct_permeability_objective"], errors="coerce")
        )
    training = finite_scores.merge(
        evidence[["candidate_id", "total_active_objective_value", "state_objective_value"]],
        on="candidate_id",
        how="inner",
    )
    training = training[training["state_objective_value"].notna()].copy()
    if training.shape[0] < 3:
        raise SystemExit("at least three executed candidates with finite candidate scores are required")

    training["row_role"] = "training"
    proposals = proposal_scores.copy()
    proposals["row_role"] = "proposal"
    combined = pd.concat([training, proposals], ignore_index=True, sort=False)
    feature_frame, feature_columns = build_feature_matrix(combined)
    train_mask = combined["row_role"] == "training"

    x_train = feature_frame.loc[train_mask].to_numpy(dtype=float)
    y_train = pd.to_numeric(combined.loc[train_mask, "state_objective_value"], errors="coerce").to_numpy(dtype=float)
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
    mean, std = model.predict(feature_frame.to_numpy(dtype=float), return_std=True)
    combined["gp_state_objective_mean"] = mean
    combined["gp_state_objective_std"] = std
    best_row = training.sort_values("total_active_objective_value").iloc[0]
    metadata = {
        "training_candidate_count": int(training.shape[0]),
        "best_executed_candidate": str(best_row["candidate_id"]),
        "best_executed_combined_objective": float(best_row["total_active_objective_value"]),
        "best_executed_state_objective": float(best_row["state_objective_value"]),
        "feature_columns": feature_columns,
        "model": "GaussianProcessRegressor(Matern nu=1.5) continuous proposal, target=state objective",
        "learned_kernel": str(model.named_steps["gaussianprocessregressor"].kernel_),
    }
    proposal_prediction = combined[combined["row_role"] == "proposal"].copy()
    executed_ids = set(evidence["candidate_id"].astype(str))
    proposal_prediction["is_executed_ogs_candidate"] = proposal_prediction["candidate_id"].astype(str).isin(
        executed_ids
    )
    return proposal_prediction, metadata


def score_acquisition(scored: pd.DataFrame, best_objective: float, args: argparse.Namespace) -> pd.DataFrame:
    output = scored.copy()
    output["direct_objective_for_prediction"] = pd.to_numeric(output["objective_value"], errors="coerce")
    output["gp_combined_objective_mean"] = output["direct_objective_for_prediction"] + output[
        "gp_state_objective_mean"
    ]
    output["gp_combined_objective_std"] = output["gp_state_objective_std"]
    output["expected_improvement"] = expected_improvement(
        best_objective,
        output["gp_combined_objective_mean"].to_numpy(dtype=float),
        output["gp_combined_objective_std"].to_numpy(dtype=float),
        args.xi,
    )
    output["probability_of_improvement"] = norm.cdf(
        (best_objective - output["gp_combined_objective_mean"]) / output["gp_combined_objective_std"].clip(lower=1e-12)
    )
    output["lower_confidence_bound"] = (
        output["gp_combined_objective_mean"] - args.lcb_kappa * output["gp_combined_objective_std"]
    )
    output = output[~output["is_executed_ogs_candidate"].fillna(False)].copy()
    if output.empty:
        raise SystemExit("all continuous proposal candidates are already executed")
    output = output.sort_values(
        ["lower_confidence_bound", "gp_combined_objective_mean", "objective_value", "candidate_id"]
    ).reset_index(drop=True)
    output["proposal_rank"] = range(1, output.shape[0] + 1)
    return output


def write_markdown(path: Path, proposals: pd.DataFrame, summary: dict[str, Any]) -> None:
    lines = [
        "# Continuous Bayesian Candidate Plan",
        "",
        "This artifact proposes new smooth permeability fields outside the fixed",
        "pre-generated finite grid. It samples continuous support length and shift",
        "scale values, evaluates the direct pulse-test objective for each generated",
        "mesh, and uses the executed OGS candidates to predict the sampled NMR state",
        "objective.",
        "",
        "It does not execute OGS. The emitted batch is a handoff to",
        "`run_inversion_candidate_search.py --ogs-mode execute`.",
        "",
        "## Evidence",
        "",
        f"- Training OGS candidates: {summary['training_candidate_count']}",
        f"- Best executed candidate: `{summary['best_executed_candidate']}`",
        f"- Best executed combined objective: {summary['best_executed_combined_objective']:.2f}",
        f"- Continuous candidates generated: {summary['continuous_candidate_count']}",
        f"- Length range: {summary['length_min_m']:.5f} to {summary['length_max_m']:.5f} m",
        f"- Shift range: {summary['shift_min']:.2f} to {summary['shift_max']:.2f}",
        "",
        "## Proposed Execution Batch",
        "",
        "| Rank | Candidate | Length [m] | Shift | Direct objective | Predicted combined | Std | LCB | P(improve) |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in proposals.head(int(summary["execution_batch_size"])).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["proposal_rank"])),
                    f"`{row['candidate_id']}`",
                    f"{float(row['length_scale_m']):.5f}",
                    f"{float(row['shift_scale']):.3f}",
                    f"{float(row['objective_value']):.2f}",
                    f"{float(row['gp_combined_objective_mean']):.2f}",
                    f"{float(row['gp_combined_objective_std']):.2f}",
                    f"{float(row['lower_confidence_bound']):.2f}",
                    f"{float(row['probability_of_improvement']):.3f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is the first continuous proposal layer over the smooth-field",
            "  parameterization; it is not yet a production sampler.",
            "- The state surrogate is trained only on the currently executed OGS/NMR",
            "  evidence, while the direct permeability objective is evaluated exactly",
            "  for each proposed mesh.",
            "- Execute the proposed batch, regenerate the adaptive/Bayesian summaries,",
            "  and only then decide whether the local smooth-field family is exhausted.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir = args.output_dir.resolve()
    if args.output_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"output directory exists, pass --overwrite to replace: {args.output_dir}")
        import shutil

        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True)

    finite_scores = pd.read_csv(args.finite_candidate_scores)
    executed = pd.read_csv(args.executed_evidence)
    samples = continuous_hyperparameter_samples(args)

    mesh = meshio.read(args.input_mesh)
    field = read_cell_field(mesh, args.field_name)
    centroids = cell_centroids(mesh)
    _, anchors = build_anchor_table(field, args.targets, args.target_cells)
    if anchors.empty:
        raise SystemExit("no anchor cells available for continuous proposal")

    rows: list[dict[str, Any]] = []
    for _, sample in samples.iterrows():
        row = run_candidate(
            mesh=mesh,
            field=field,
            centroids=centroids,
            anchors=anchors,
            length_scale=float(sample["length_scale_m"]),
            shift_scale=float(sample["shift_scale"]),
            args=args,
        )
        row["proposal_sample_source"] = sample["proposal_sample_source"]
        rows.append(row)
    direct_scores = pd.DataFrame(rows).sort_values(["objective_value", "length_scale_m"]).reset_index(drop=True)
    direct_scores["rank_by_objective"] = range(1, direct_scores.shape[0] + 1)

    predicted, metadata = train_state_surrogate(finite_scores, executed, direct_scores)
    proposals = score_acquisition(predicted, metadata["best_executed_combined_objective"], args)
    top = proposals.head(args.max_proposals).copy()
    batch = proposals.head(args.execution_batch_size).copy()

    direct_scores_path = args.output_dir / "continuous_direct_candidate_scores.csv"
    proposal_scores_path = args.output_dir / "continuous_optimizer_candidate_scores.csv"
    batch_path = args.output_dir / "next_continuous_candidate_batch.csv"
    summary_json_path = args.output_dir / "CONTINUOUS_CANDIDATE_PLAN.json"
    summary_md_path = args.output_dir / "CONTINUOUS_CANDIDATE_PLAN.md"

    direct_scores.to_csv(direct_scores_path, index=False)
    proposals.to_csv(proposal_scores_path, index=False)
    batch.to_csv(batch_path, index=False)

    summary = {
        **metadata,
        "continuous_candidate_count": int(direct_scores.shape[0]),
        "proposal_count": int(top.shape[0]),
        "execution_batch_size": int(args.execution_batch_size),
        "length_min_m": float(args.length_min_m),
        "length_max_m": float(args.length_max_m),
        "shift_min": float(args.shift_min),
        "shift_max": float(args.shift_max),
        "cutoff_factor": float(args.cutoff_factor),
        "seed": int(args.seed),
        "sample_count": int(args.sample_count),
        "input_mesh": str(args.input_mesh),
        "finite_candidate_scores": str(args.finite_candidate_scores),
        "executed_evidence": str(args.executed_evidence),
        "direct_candidate_scores_csv": str(direct_scores_path),
        "optimizer_candidate_scores_csv": str(proposal_scores_path),
        "next_continuous_candidate_batch_csv": str(batch_path),
        "summary_markdown": str(summary_md_path),
        "top_proposals": [json_ready(row) for row in top.to_dict(orient="records")],
        "notes": [
            "Continuous smooth-field proposal; it does not execute OGS.",
            "The GESA source model remains frozen; generated meshes are run-local parameter-field candidates.",
            "The state surrogate is trained on executed OGS candidates and direct permeability is evaluated for each new candidate.",
        ],
    }
    summary_json_path.write_text(json.dumps(json_ready(summary), indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(summary_md_path, top, summary)
    print(f"wrote {direct_scores_path}")
    print(f"wrote {proposal_scores_path}")
    print(f"wrote {batch_path}")
    print(f"wrote {summary_json_path}")
    print(f"wrote {summary_md_path}")
    print(f"top proposal: {top.iloc[0]['candidate_id']}")


if __name__ == "__main__":
    main()
