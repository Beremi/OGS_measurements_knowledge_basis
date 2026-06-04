# ERT Candidate Discrimination Audit

This audit evaluates the ERT log-resistivity diagnostic across existing executed runs with OGS output fields.
It is diagnostic only and is not assembled into the active objective.

## Status

- Status: `ert_candidate_discrimination_audit_generated_transform_support_unconfirmed`
- Runs audited: 66
- Runs with combined objective: 66
- Runs with full active combined objective: 66
- Support cells per compared output: 2035
- Compared rows per run: 162800
- Compared output times per run: 80
- Reference run: `direct_fit_observation_run`
- ERT MAE range across audited runs: 0.019636 log10 units
- Best ERT run: `broad_continuous_001_001_length_0p023m_shift_1p004` with MAE 0.254072
- Best active-objective run: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` with ERT MAE 0.254180
- Combined-objective/ERT-MAE correlation: 0.889440
- Activation gate: Use this only as cross-candidate diagnostic evidence. ERT remains outside the active likelihood until the ERT-to-OGS transform, exact support mask, and uncertainty/correlation model are accepted.

## Top Runs By ERT Log-Resistivity MAE

| Run | Kind | ERT MAE | Delta vs reference | Combined objective | NMR objective |
| --- | --- | ---: | ---: | ---: | ---: |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | 0.254072 | -0.000108 | 3159.059658 | 2889.177559 |
| `production_sampler_round5_005_length_0p004m_shift_1p031` | production_sampler_round | 0.254173 | -0.000007 | 3156.785440 | 2886.514169 |
| `lower_support_loop_002_002_length_0p004m_shift_1p020` | lower_support | 0.254176 | -0.000005 | 3156.534153 | 2886.524158 |
| `lower_support_loop_001_003_length_0p004m_shift_1p014` | lower_support | 0.254177 | -0.000003 | 3156.443974 | 2886.529692 |
| `lower_support_loop_001_001_length_0p003m_shift_1p006` | lower_support | 0.254179 | -0.000001 | 3156.373009 | 2886.537520 |
| `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | local_basis | 0.254179 | -0.000001 | 3156.354266 | 2886.536209 |
| `production_sampler_round2_005_basis_023_det_l_0p0075_s_0p750` | production_sampler_round | 0.254179 | -0.000001 | 3156.354758 | 2886.535612 |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | local_basis | 0.254180 | -0.000001 | 3156.353067 | 2886.535010 |
| `production_sampler_round2_004_basis_018_det_l_0p0050_s_0p750` | production_sampler_round | 0.254180 | -0.000000 | 3156.361079 | 2886.541932 |
| `production_sampler_round2_001_basis_003_det_l_0p0015_s_0p750` | production_sampler_round | 0.254180 | -0.000000 | 3156.361079 | 2886.541932 |
| `production_sampler_round2_002_basis_008_det_l_0p0025_s_0p750` | production_sampler_round | 0.254180 | -0.000000 | 3156.361079 | 2886.541932 |
| `production_sampler_round2_003_basis_013_det_l_0p0035_s_0p750` | production_sampler_round | 0.254180 | -0.000000 | 3156.361079 | 2886.541932 |
| `production_sampler_round3_006_basis_014_det_l_0p0035_s_1p000` | production_sampler_round | 0.254180 | -0.000000 | 3156.361470 | 2886.543413 |
| `production_sampler_round4_002_basis_009_det_l_0p0025_s_1p000` | production_sampler_round | 0.254180 | -0.000000 | 3156.361470 | 2886.543413 |
| `production_sampler_round3_005_basis_019_det_l_0p0050_s_1p000` | production_sampler_round | 0.254180 | -0.000000 | 3156.361470 | 2886.543413 |

## Interpretation

The ERT range measures how much the currently executed permeability-field family changes the provisional OGS-to-ERT log-resistivity diagnostic. A small range means the family barely changes ERT under the present support and transform assumptions; a larger range would justify using ERT as a stronger candidate-screening diagnostic after the geometry and uncertainty gates are accepted.

The audit deliberately keeps ERT outside the likelihood. The remaining activation requirements are collaborator acceptance of the ERT-to-OGS coordinate transform, the exact near-niche support mask, and an uncertainty/correlation model for the ERT inversion cells.
