# Taupe/TDR Candidate Discrimination Audit

This audit evaluates the Taupe/TDR trend diagnostic across existing executed runs with sampled OGS state outputs.
It is diagnostic only and is not assembled into the active objective.

## Status

- Status: `taupe_candidate_discrimination_audit_generated_not_active_likelihood`
- Runs audited: 74
- Runs with combined objective: 74
- Compared rows per run: 1860
- Compared series per run: 12
- Reference run: `direct_fit_observation_run`
- Taupe MAE range across audited runs: 0.036871
- Best Taupe run: `adaptive_combined_001_length_0p050m` with MAE 1.829884
- Best active-objective run: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` with Taupe MAE 1.863211
- Combined-objective/Taupe-MAE correlation: -0.537840
- Activation gate: Use this only as cross-candidate diagnostic evidence. Taupe/TDR remains outside the active likelihood until workbook units, sensor calibration, trend uncertainty, and grouped weights are confirmed.

## Top Runs By Taupe Trend MAE

| Run | Kind | Taupe MAE | Delta vs reference | Combined objective | NMR objective |
| --- | --- | ---: | ---: | ---: | ---: |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | 1.829884 | -0.033327 | 3276.565238 | 2985.274497 |
| `adaptive_combined_002_length_0p050m_shift_0p750` | adaptive_combined | 1.830476 | -0.032735 | 3300.912191 | 2971.512711 |
| `local_bracketed_003_length_0p031m` | local_smooth | 1.832081 | -0.031130 | 3219.345219 | 2947.959041 |
| `production_sampler_round3_002_length_0p028m_shift_1p050` | production_sampler_round | 1.850646 | -0.012565 | 3167.879480 | 2896.788219 |
| `production_sampler_round2_006_length_0p026m_shift_1p107` | production_sampler_round | 1.850755 | -0.012456 | 3171.354419 | 2896.246864 |
| `optimizer_proposed_003_length_0p025m_shift_1p125` | optimizer_proposed | 1.851080 | -0.012130 | 3173.394559 | 2896.375020 |
| `production_sampler_round3_001_length_0p028m` | production_sampler_round | 1.851241 | -0.011970 | 3167.358208 | 2896.954006 |
| `production_sampler_round4_001_length_0p029m_shift_0p954` | production_sampler_round | 1.851897 | -0.011314 | 3169.222932 | 2897.117201 |
| `regularized_ogs_candidate_001_length_0p025m` | regularized_ogs | 1.852588 | -0.010623 | 3166.611452 | 2896.637493 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | 1.854766 | -0.008445 | 3159.059658 | 2889.177559 |
| `regularized_ogs_candidate_002_length_0p025m_shift_0p750` | regularized_ogs | 1.856246 | -0.006965 | 3198.487212 | 2897.326180 |
| `regularized_ogs_candidate_003_length_0p025m_shift_0p500` | regularized_ogs | 1.861598 | -0.001613 | 3289.645364 | 2896.926283 |
| `adaptive_combined_003_length_0p075m` | adaptive_combined | 1.862538 | -0.000673 | 3353.882859 | 3019.880738 |
| `production_sampler_round5_005_length_0p004m_shift_1p031` | production_sampler_round | 1.863067 | -0.000144 | 3156.785440 | 2886.514169 |
| `lower_support_loop_002_002_length_0p004m_shift_1p020` | lower_support | 1.863117 | -0.000094 | 3156.534153 | 2886.524158 |

## Interpretation

A small Taupe-MAE range means the currently executed permeability-field family barely changes the mapped A3/A4 Taupe trend diagnostic. That would make Taupe a weak discriminator for this candidate family even if the unit/calibration gate were later resolved.

The audit deliberately keeps Taupe outside the likelihood. The remaining activation requirements are the Taupe workbook unit, sensor-specific calibration or accepted trend-only scale, grouped series weights, and collaborator acceptance of the A3/A4 support mapping.
