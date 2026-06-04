# ERT Support Sensitivity Audit

This audit quantifies how selected executed OGS candidates rank under tighter radial subsets of the current provisional ERT support.
It does not activate ERT in the likelihood.

## Status

- Status: `ert_support_sensitivity_generated_transform_still_unconfirmed`
- Runs evaluated: 6
- Support variants: 9
- Best mean support-rank run: `broad_continuous_001_001_length_0p023m_shift_1p004` with mean rank 1.67
- Activation gate: Diagnostic only: this audit quantifies sensitivity inside the current approximate ERT support. It does not confirm the ERT-to-OGS transform, exact tunnel-contour support mask, or ERT inversion uncertainty/correlation model.

## Winners By Support Variant

| Support variant | Winner | Cells/output | MAE log10 | RMSE log10 | Rank correlation to default |
| --- | --- | ---: | ---: | ---: | ---: |
| `inner_annulus_1p15_1p30m` | `broad_continuous_001_001_length_0p023m_shift_1p004` | 886 | 0.289829 | 0.355837 | 0.429 |
| `outer_annulus_1p30_1p50m` | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 1141 | 0.238767 | 0.272850 | 0.657 |
| `radius_le_1p25m` | `broad_continuous_001_001_length_0p023m_shift_1p004` | 484 | 0.314781 | 0.386674 | 0.429 |
| `radius_le_1p2m` | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 115 | 0.355177 | 0.418807 | 0.657 |
| `radius_le_1p35m` | `broad_continuous_001_001_length_0p023m_shift_1p004` | 1289 | 0.272639 | 0.331462 | 0.486 |
| `radius_le_1p3m` | `broad_continuous_001_001_length_0p023m_shift_1p004` | 894 | 0.291745 | 0.357901 | 0.429 |
| `radius_le_1p45m` | `broad_continuous_001_001_length_0p023m_shift_1p004` | 1834 | 0.257263 | 0.305310 | 1.000 |
| `radius_le_1p4m` | `broad_continuous_001_001_length_0p023m_shift_1p004` | 1587 | 0.261822 | 0.314704 | 0.943 |
| `radius_le_1p5m` | `broad_continuous_001_001_length_0p023m_shift_1p004` | 2035 | 0.254072 | 0.299644 | 1.000 |

## Selected Run Scores

| Run | Kind | Support | Cells/output | MAE log10 | RMSE log10 | Rank | Rank delta vs default |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `inner_annulus_1p15_1p30m` | 886 | 0.289829 | 0.355837 | 1.00 | 0.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `inner_annulus_1p15_1p30m` | 886 | 0.290562 | 0.356381 | 2.00 | -3.00 |
| `direct_fit_observation_run` | direct_reference | `inner_annulus_1p15_1p30m` | 886 | 0.291091 | 0.357256 | 3.00 | -1.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `inner_annulus_1p15_1p30m` | 886 | 0.291091 | 0.357257 | 4.00 | 1.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `inner_annulus_1p15_1p30m` | 886 | 0.291091 | 0.357257 | 5.00 | 3.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `inner_annulus_1p15_1p30m` | 886 | 0.302553 | 0.369803 | 6.00 | 0.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `outer_annulus_1p30_1p50m` | 1141 | 0.238767 | 0.272850 | 1.00 | -1.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `outer_annulus_1p30_1p50m` | 1141 | 0.238767 | 0.272850 | 2.00 | -1.00 |
| `direct_fit_observation_run` | direct_reference | `outer_annulus_1p30_1p50m` | 1141 | 0.238768 | 0.272851 | 3.00 | -1.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `outer_annulus_1p30_1p50m` | 1141 | 0.239113 | 0.273085 | 4.00 | 3.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `outer_annulus_1p30_1p50m` | 1141 | 0.240319 | 0.274137 | 5.00 | 0.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `outer_annulus_1p30_1p50m` | 1141 | 0.254584 | 0.292621 | 6.00 | 0.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `radius_le_1p25m` | 484 | 0.314781 | 0.386674 | 1.00 | 0.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `radius_le_1p25m` | 484 | 0.315174 | 0.386982 | 2.00 | -3.00 |
| `direct_fit_observation_run` | direct_reference | `radius_le_1p25m` | 484 | 0.315610 | 0.387686 | 3.00 | -1.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `radius_le_1p25m` | 484 | 0.315610 | 0.387686 | 4.00 | 1.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `radius_le_1p25m` | 484 | 0.315610 | 0.387686 | 5.00 | 3.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `radius_le_1p25m` | 484 | 0.322854 | 0.395404 | 6.00 | 0.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `radius_le_1p2m` | 115 | 0.355177 | 0.418807 | 1.00 | -1.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `radius_le_1p2m` | 115 | 0.355177 | 0.418807 | 2.00 | -1.00 |
| `direct_fit_observation_run` | direct_reference | `radius_le_1p2m` | 115 | 0.355177 | 0.418807 | 3.00 | -1.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `radius_le_1p2m` | 115 | 0.355263 | 0.418843 | 4.00 | 3.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `radius_le_1p2m` | 115 | 0.355303 | 0.418865 | 5.00 | 0.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `radius_le_1p2m` | 115 | 0.356986 | 0.420400 | 6.00 | 0.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `radius_le_1p35m` | 1289 | 0.272639 | 0.331462 | 1.00 | 0.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `radius_le_1p35m` | 1289 | 0.273498 | 0.332108 | 2.00 | -3.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `radius_le_1p35m` | 1289 | 0.273605 | 0.332626 | 3.00 | 0.00 |
| `direct_fit_observation_run` | direct_reference | `radius_le_1p35m` | 1289 | 0.273605 | 0.332626 | 4.00 | 0.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `radius_le_1p35m` | 1289 | 0.273605 | 0.332626 | 5.00 | 3.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `radius_le_1p35m` | 1289 | 0.287146 | 0.347981 | 6.00 | 0.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `radius_le_1p3m` | 894 | 0.291745 | 0.357901 | 1.00 | 0.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `radius_le_1p3m` | 894 | 0.292471 | 0.358436 | 2.00 | -3.00 |
| `direct_fit_observation_run` | direct_reference | `radius_le_1p3m` | 894 | 0.292994 | 0.359297 | 3.00 | -1.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `radius_le_1p3m` | 894 | 0.292994 | 0.359298 | 4.00 | 1.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `radius_le_1p3m` | 894 | 0.292994 | 0.359298 | 5.00 | 3.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `radius_le_1p3m` | 894 | 0.304348 | 0.371662 | 6.00 | 0.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `radius_le_1p45m` | 1834 | 0.257263 | 0.305310 | 1.00 | 0.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `radius_le_1p45m` | 1834 | 0.257814 | 0.306022 | 2.00 | 0.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `radius_le_1p45m` | 1834 | 0.257814 | 0.306023 | 3.00 | 0.00 |
| `direct_fit_observation_run` | direct_reference | `radius_le_1p45m` | 1834 | 0.257814 | 0.306023 | 4.00 | 0.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `radius_le_1p45m` | 1834 | 0.258326 | 0.306169 | 5.00 | 0.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `radius_le_1p45m` | 1834 | 0.271882 | 0.322967 | 6.00 | 0.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `radius_le_1p4m` | 1587 | 0.261822 | 0.314704 | 1.00 | 0.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `radius_le_1p4m` | 1587 | 0.262694 | 0.315718 | 2.00 | -1.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `radius_le_1p4m` | 1587 | 0.262694 | 0.315718 | 3.00 | 1.00 |
| `direct_fit_observation_run` | direct_reference | `radius_le_1p4m` | 1587 | 0.262694 | 0.315718 | 4.00 | 0.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `radius_le_1p4m` | 1587 | 0.262853 | 0.315508 | 5.00 | 0.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `radius_le_1p4m` | 1587 | 0.276883 | 0.332642 | 6.00 | 0.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | `radius_le_1p5m` | 2035 | 0.254072 | 0.299644 | 1.00 | 0.00 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | `radius_le_1p5m` | 2035 | 0.254179 | 0.299965 | 2.00 | 0.00 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | `radius_le_1p5m` | 2035 | 0.254180 | 0.299966 | 3.00 | 0.00 |
| `direct_fit_observation_run` | direct_reference | `radius_le_1p5m` | 2035 | 0.254180 | 0.299966 | 4.00 | 0.00 |
| `broad_continuous_001_003_length_0p021m` | broad_continuous | `radius_le_1p5m` | 2035 | 0.255141 | 0.300512 | 5.00 | 0.00 |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | `radius_le_1p5m` | 2035 | 0.268728 | 0.317097 | 6.00 | 0.00 |

## Interpretation

The radial caps are a local sensitivity proxy inside the already documented `ready_for_residual_after_ogs_output` mask. They are not a substitute for the missing agreed ERT/FEM tunnel-contour support definition.
If the ERT winner or ranking changes strongly across these variants, the ERT stream should remain a diagnostic screen until the exact support and covariance model are fixed.
