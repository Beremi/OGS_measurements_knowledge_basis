# NMR Candidate Bias Sensitivity Audit

This audit checks whether the executed candidate ranking is robust to the documented NMR bound/interlayer-water caveat.
It does not change the active objective.

## Status

- Status: `nmr_candidate_bias_sensitivity_generated_current_objective_unchanged`
- Runs audited: 66
- Runs with full active combined objective: 66
- Active NMR rows per run: 192
- Current best combined run: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` with objective 3156.353067
- Best per-label-bias run: `broad_continuous_001_003_length_0p021m` with diagnostic combined objective 505.614306
- Best within-label anomaly run: `broad_continuous_001_003_length_0p021m` with diagnostic combined objective 505.614306
- Current-vs-label-bias rank correlation: 0.635153
- Current-vs-trend-anomaly rank correlation: 0.635153
- Activation gate: Diagnostic only: current NMR objective is unchanged. Use label-bias or trend/anomaly forms only after accepting a bound/interlayer-water treatment and updating the likelihood model.

## Top Runs By Diagnostic NMR Treatments

### Per-Label Bias

| Run | Kind | Bias combined | Bias NMR objective | Bias max | Current combined |
| --- | --- | ---: | ---: | ---: | ---: |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | 505.614306 | 235.784274 | 0.075639 | 3169.309599 |
| `local_refined_002_length_0p019m` | local_smooth | 505.614351 | 235.796294 | 0.075688 | 3164.958854 |
| `local_refined_001_length_0p013m` | local_smooth | 505.622107 | 235.804050 | 0.075757 | 3159.664381 |
| `broad_continuous_loop_001_001_length_0p015m` | broad_continuous | 505.622543 | 235.804486 | 0.075638 | 3161.360042 |
| `broad_continuous_001_002_length_0p022m_shift_0p998` | broad_continuous | 505.628029 | 235.785305 | 0.075639 | 3169.300620 |
| `continuous_proposed_002_length_0p007m` | continuous_proposed | 505.631136 | 235.813078 | 0.075776 | 3157.741296 |
| `broad_continuous_loop_001_003_length_0p010m` | broad_continuous | 505.633510 | 235.815453 | 0.075770 | 3157.702129 |
| `production_sampler_round4_002_basis_009_det_l_0p0025_s_1p000` | production_sampler_round | 505.637404 | 235.819347 | 0.075761 | 3156.361470 |
| `local_basis_sampler_001_basis_004_det_l_0p0015_s_1p000` | local_basis | 505.637404 | 235.819347 | 0.075761 | 3156.361470 |
| `production_sampler_round3_005_basis_019_det_l_0p0050_s_1p000` | production_sampler_round | 505.637404 | 235.819347 | 0.075761 | 3156.361470 |
| `production_sampler_round3_006_basis_014_det_l_0p0035_s_1p000` | production_sampler_round | 505.637404 | 235.819347 | 0.075761 | 3156.361470 |
| `direct_fit_observation_run` | direct_reference | 505.637404 | 235.819347 | 0.075761 | 3156.361470 |

### Within-Label Anomaly

| Run | Kind | Anomaly combined | Anomaly NMR objective | Rows | Groups | Current combined |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | 505.614306 | 235.784274 | 192 | 17 | 3169.309599 |
| `local_refined_002_length_0p019m` | local_smooth | 505.614351 | 235.796294 | 192 | 17 | 3164.958854 |
| `local_refined_001_length_0p013m` | local_smooth | 505.622107 | 235.804050 | 192 | 17 | 3159.664381 |
| `broad_continuous_loop_001_001_length_0p015m` | broad_continuous | 505.622543 | 235.804486 | 192 | 17 | 3161.360042 |
| `broad_continuous_001_002_length_0p022m_shift_0p998` | broad_continuous | 505.628029 | 235.785305 | 192 | 17 | 3169.300620 |
| `continuous_proposed_002_length_0p007m` | continuous_proposed | 505.631136 | 235.813078 | 192 | 17 | 3157.741296 |
| `broad_continuous_loop_001_003_length_0p010m` | broad_continuous | 505.633510 | 235.815453 | 192 | 17 | 3157.702129 |
| `production_sampler_round4_002_basis_009_det_l_0p0025_s_1p000` | production_sampler_round | 505.637404 | 235.819347 | 192 | 17 | 3156.361470 |
| `local_basis_sampler_001_basis_004_det_l_0p0015_s_1p000` | local_basis | 505.637404 | 235.819347 | 192 | 17 | 3156.361470 |
| `production_sampler_round3_005_basis_019_det_l_0p0050_s_1p000` | production_sampler_round | 505.637404 | 235.819347 | 192 | 17 | 3156.361470 |
| `production_sampler_round3_006_basis_014_det_l_0p0035_s_1p000` | production_sampler_round | 505.637404 | 235.819347 | 192 | 17 | 3156.361470 |
| `direct_fit_observation_run` | direct_reference | 505.637404 | 235.819347 | 192 | 17 | 3156.361470 |

## Uniform Offset Winners

| Offset | Best run | Combined objective | NMR objective | Nonphysical corrected rows |
| ---: | --- | ---: | ---: | ---: |
| 0 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 3156.353067 | 2886.535010 | 120 |
| 0.005 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 2698.401476 | 2428.583419 | 84 |
| 0.01 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 2286.886695 | 2017.068638 | 55 |
| 0.015 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 1921.808724 | 1651.990667 | 39 |
| 0.02 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 1603.167563 | 1333.349505 | 35 |
| 0.03 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 1105.195670 | 835.377613 | 13 |
| 0.04 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 792.971018 | 523.152961 | 11 |
| 0.05 | `regularized_ogs_candidate_001_length_0p025m` | 665.711367 | 395.737407 | 3 |
| 0.075 | `local_bracketed_003_length_0p031m` | 1133.000797 | 861.614620 | 13 |
| 0.1 | `adaptive_combined_001_length_0p050m` | 2746.489156 | 2455.198414 | 47 |

## Interpretation

The per-label-bias and within-label anomaly diagnostics remove constant NMR offsets that could plausibly arise from bound/interlayer water. If their top-ranked candidates differ from the current raw absolute-theta objective, the current permeability-field ranking should be treated as conditional on the unresolved NMR interpretation.

Uniform subtraction is included only as a simple stress test. The generated bound-water audit already shows that one global offset cannot make every usable NMR row physical without overcorrecting others.
