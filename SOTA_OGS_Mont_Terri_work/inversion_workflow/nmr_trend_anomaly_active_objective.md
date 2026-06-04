# NMR Trend/Anomaly Active Objective Ranking

This package exercises `assemble_inversion_objective.py --state-objective-mode nmr_within_label_trend_anomaly` across the existing executed candidate runs.
It is a provisional active-objective implementation path; it does not overwrite the historical raw-theta `combined_objective_*` files.

## Status

- Status: `nmr_trend_anomaly_active_objective_mode_implemented_provisional`
- Runs evaluated: 74 / 74
- Runs with direct permeability plus NMR trend/anomaly objective: 66
- Best trend/anomaly objective run: `broad_continuous_001_003_length_0p021m` with objective 505.614306
- Raw-objective incumbent: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` with raw objective 3156.353067
- Raw incumbent rank under trend/anomaly: 14
- Trend/anomaly winner raw rank: 56
- Diagnostic validation max abs delta: 0.000000000000
- Activation gate: Executable but still provisional: this mode can be passed to evaluate_inversion_candidate.py, but promotion to the default reporting objective still needs explicit modelling acceptance because it changes the winner relative to the raw absolute NMR objective.

## Top Candidate Runs

| Rank | Run | Trend/anomaly combined | Direct permeability | NMR trend/anomaly | Raw combined | Raw rank | Rows | Groups |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `broad_continuous_001_003_length_0p021m` | 505.614306 | 269.830032 | 235.784274 | 3169.309599 | 56 | 192 | 17 |
| 2 | `local_refined_002_length_0p019m` | 505.614351 | 269.818057 | 235.796294 | 3164.958854 | 47 | 192 | 17 |
| 3 | `local_refined_001_length_0p013m` | 505.622107 | 269.818057 | 235.804050 | 3159.664381 | 40 | 192 | 17 |
| 4 | `broad_continuous_loop_001_001_length_0p015m` | 505.622543 | 269.818057 | 235.804486 | 3161.360042 | 45 | 192 | 17 |
| 5 | `broad_continuous_001_002_length_0p022m_shift_0p998` | 505.628029 | 269.842723 | 235.785305 | 3169.300620 | 55 | 192 | 17 |
| 6 | `continuous_proposed_002_length_0p007m` | 505.631136 | 269.818057 | 235.813078 | 3157.741296 | 33 | 192 | 17 |
| 7 | `broad_continuous_loop_001_003_length_0p010m` | 505.633510 | 269.818057 | 235.815453 | 3157.702129 | 32 | 192 | 17 |
| 8 | `production_sampler_round4_002_basis_009_det_l_0p0025_s_1p000` | 505.637404 | 269.818057 | 235.819347 | 3156.361470 | 12 | 192 | 17 |
| 9 | `local_basis_sampler_001_basis_004_det_l_0p0015_s_1p000` | 505.637404 | 269.818057 | 235.819347 | 3156.361470 | 10 | 192 | 17 |
| 10 | `production_sampler_round3_005_basis_019_det_l_0p0050_s_1p000` | 505.637404 | 269.818057 | 235.819347 | 3156.361470 | 9 | 192 | 17 |
| 11 | `production_sampler_round3_006_basis_014_det_l_0p0035_s_1p000` | 505.637404 | 269.818057 | 235.819347 | 3156.361470 | 8 | 192 | 17 |
| 12 | `direct_fit_observation_run` | 505.637404 | 269.818057 | 235.819347 | 3156.361470 | 11 | 192 | 17 |
| 13 | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 505.637437 | 269.818057 | 235.819380 | 3156.354266 | 2 | 192 | 17 |
| 14 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 505.637442 | 269.818057 | 235.819385 | 3156.353067 | 1 | 192 | 17 |
| 15 | `production_sampler_round2_003_basis_013_det_l_0p0035_s_0p750` | 505.638503 | 269.819147 | 235.819357 | 3156.361079 | 6 | 192 | 17 |

## Implementation Note

The executable residual is formed within each `observation_family` plus `measurement_label` NMR group as `(theta_model - weighted_group_mean(theta_model)) - (theta_NMR_obs - weighted_group_mean(theta_NMR_obs))`, using the existing NMR sigma values. Constant bound/interlayer-water and campaign offsets therefore cancel to first order, while the frozen OGS model state remains `theta = porosity * liquid_saturation`.

This ranking is the practical next step after the NMR objective decision package: the code path now exists for future candidate evaluations, but the report should still call it provisional until the modelling team accepts this residual as the promoted/default NMR likelihood.
