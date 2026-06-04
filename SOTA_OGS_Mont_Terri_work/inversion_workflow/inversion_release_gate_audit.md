# Inversion Release Gate Audit

This audit verifies that prepared OGS runs still obey the staged parameter-release plan.
The current allowed release is narrow: `k_i_rd` may vary as the active permeability
tensor-magnitude field, while `n_rd` porosity and all retention, mechanical, thermal,
boundary, and initialization parameters remain fixed until their gates are satisfied.

- Overall status: `pass`
- Runs audited: 65
- Checks: 1300
- Failures: 0
- Warnings: 0

## Run Summary

| Run | Status | Failures | Warnings | Output variables |
| --- | --- | ---: | ---: | --- |
| `regularized_ogs_candidate_001_length_0p025m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `regularized_ogs_candidate_002_length_0p025m_shift_0p750` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `regularized_ogs_candidate_003_length_0p025m_shift_0p500` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `adaptive_combined_001_length_0p050m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `adaptive_combined_002_length_0p050m_shift_0p750` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `adaptive_combined_003_length_0p075m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `local_refined_001_length_0p013m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `local_refined_002_length_0p019m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `local_bracketed_001_length_0p013m_shift_0p875` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `local_bracketed_002_length_0p013m_shift_1p125` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `local_bracketed_003_length_0p031m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `optimizer_proposed_001_length_0p019m_shift_1p125` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `optimizer_proposed_002_length_0p019m_shift_0p875` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `optimizer_proposed_003_length_0p025m_shift_1p125` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `continuous_proposed_001_length_0p006m_shift_0p992` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `continuous_proposed_002_length_0p007m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `continuous_proposed_003_length_0p007m_shift_0p972` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_continuous_001_length_0p004m_shift_0p995` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_continuous_002_length_0p003m_shift_0p986` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_continuous_003_length_0p004m_shift_0p994` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_loop_001_001_length_0p003m_shift_1p006` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_loop_001_002_length_0p005m_shift_0p985` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_loop_001_003_length_0p004m_shift_1p014` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_loop_002_001_length_0p004m_shift_0p992` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_loop_002_002_length_0p004m_shift_1p020` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `lower_support_loop_002_003_length_0p006m_shift_0p975` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `broad_continuous_001_002_length_0p022m_shift_0p998` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `broad_continuous_001_003_length_0p021m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `broad_continuous_loop_001_001_length_0p015m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `broad_continuous_loop_001_002_length_0p016m_shift_0p968` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `broad_continuous_loop_001_003_length_0p010m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `local_basis_sampler_001_basis_004_det_l_0p0015_s_1p000` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_001_length_0p004m_shift_0p954` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_002_length_0p005m_shift_0p952` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_003_length_0p003m_shift_0p950` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_004_length_0p007m_shift_0p951` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_005_length_0p007m_shift_0p950` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_006_length_0p008m_shift_0p948` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round2_001_basis_003_det_l_0p0015_s_0p750` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round2_002_basis_008_det_l_0p0025_s_0p750` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round2_003_basis_013_det_l_0p0035_s_0p750` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round2_004_basis_018_det_l_0p0050_s_0p750` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round2_005_basis_023_det_l_0p0075_s_0p750` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round2_006_length_0p026m_shift_1p107` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round3_001_length_0p028m` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round3_002_length_0p028m_shift_1p050` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round3_003_length_0p008m_shift_0p934` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round3_004_length_0p010m_shift_0p950` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round3_005_basis_019_det_l_0p0050_s_1p000` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round3_006_basis_014_det_l_0p0035_s_1p000` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round4_001_length_0p029m_shift_0p954` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round4_002_basis_009_det_l_0p0025_s_1p000` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round4_003_length_0p006m_shift_0p977` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round4_004_length_0p003m_shift_0p972` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round4_005_length_0p006m_shift_0p970` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round4_006_length_0p004m_shift_0p967` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round5_001_length_0p009m_shift_0p933` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round5_002_length_0p009m_shift_0p929` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round5_003_length_0p010m_shift_0p926` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round5_004_length_0p009m_shift_0p913` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round5_005_length_0p004m_shift_1p031` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |
| `production_sampler_round5_006_length_0p003m_shift_0p964` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |

## Non-Passing Checks

| Run | Check | Status | Detail |
| --- | --- | --- | --- |
| all | all checks | `pass` | no warnings or failures |

## Interpretation

- A passing audit means the candidate run varies the mesh permeability field while
  preserving the staged fixed-parameter assumptions recorded in the release plan.
- It does not mean OGS has executed or that the fit is physically accepted; state
  residuals still require actual OGS output VTU files.
- Any failure here should be treated as a hard stop before ranking the candidate,
  because it means the inverse problem no longer matches the documented stage.
