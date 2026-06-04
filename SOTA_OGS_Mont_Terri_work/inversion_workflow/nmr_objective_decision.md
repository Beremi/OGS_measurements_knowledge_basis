# NMR Objective Decision

This package turns the existing NMR bound-water and candidate-bias audits into a
provisional objective decision. It does not change the default raw-theta active objective.

## Recommendation

- Recommended option: `within_label_trend_anomaly`.
- Active objective changed: `False`.
- Active NMR rows per run: 192.
- Active NMR label groups: 17.
- Fixed model porosity used in audits: 0.105.
- Usable mapped NMR rows above fixed porosity before correction: 162 of 287.
- Current-vs-recommended rank correlation: 0.6351529067946979.
- Executable mode status: `nmr_trend_anomaly_active_objective_mode_implemented_provisional`.
- Executable best run: `broad_continuous_001_003_length_0p021m` with objective 505.614306.
- Executable-vs-diagnostic validation max abs delta: 0.000000000000.

Use within-label trend/anomaly NMR residuals as the first provisional final NMR likelihood; keep raw absolute NMR conditional.

The recommended first final NMR likelihood is a within-label trend/anomaly
residual. It compares temporal/spatial changes after centering each
`observation_family + measurement_label` group. This removes constant
bound/interlayer-water and campaign offsets to first order and avoids treating
total NMR-visible water as mobile transport water.

## Decision Table

| Option | Decision | Final? | Selected run | Combined objective | Caveat |
| --- | --- | --- | --- | ---: | --- |
| `raw_absolute_current` | `current_active_but_conditional` | `no` | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 3156.353067 | This is the implemented active residual, but it compares total NMR-visible water content to mobile OGS theta without a bound/interlayer-water term. |
| `global_uniform_offset` | `stress_test_only_not_recommended` | `no` | `regularized_ogs_candidate_001_length_0p025m` | 665.711367 | A single subtraction improves physical-row counts but still leaves nonphysical rows and overcorrects low-water labels; it is useful only as a sensitivity check. |
| `absolute_with_label_bias` | `acceptable_if_absolute_nmr_is_required` | `conditional` | `broad_continuous_001_003_length_0p021m` | 505.614306 | This preserves absolute information while explicitly absorbing constant bound/interlayer-water and campaign offsets. |
| `within_label_trend_anomaly` | `recommended_provisional_nmr_residual` | `yes_after_acceptance` | `broad_continuous_001_003_length_0p021m` | 505.614306 | This is the safest first OGS-backed NMR residual because constant bound/interlayer-water offsets cancel to first order and no porosity release is needed. |

## Option Details

### `raw_absolute_current`

- Residual definition: theta_model - raw theta_NMR_obs
- Nuisance terms: none
- Selected candidate: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Current-objective rank of selected candidate: 1.0
- Bias/anomaly-safe rank of selected candidate: 14.0
- NMR objective: 2886.535009842994
- Normalized residual RMSE: 5.483436241919646
- Nonphysical/caveated rows or offsets: 120
- Acceptance criteria: Do not call this final unless a bound/interlayer-water model-error term is accepted and the report states that the residual is conditional.

### `global_uniform_offset`

- Residual definition: theta_model - (theta_NMR_obs - global_offset)
- Nuisance terms: single global offset, best physical-count offset=0.05
- Selected candidate: `regularized_ogs_candidate_001_length_0p025m`
- Current-objective rank of selected candidate: 
- Bias/anomaly-safe rank of selected candidate: 
- NMR objective: 395.73740717235034
- Normalized residual RMSE: 2.0303360948486624
- Nonphysical/caveated rows or offsets: 3
- Acceptance criteria: Reject as final unless collaborators provide one physically justified global offset.

### `absolute_with_label_bias`

- Residual definition: theta_model + b_label - theta_NMR_obs
- Nuisance terms: non-negative label/campaign bias per observation_family + measurement_label
- Selected candidate: `broad_continuous_001_003_length_0p021m`
- Current-objective rank of selected candidate: 56.0
- Bias/anomaly-safe rank of selected candidate: 1.0
- NMR objective: 235.78427385061542
- Normalized residual RMSE: 1.5671905391317007
- Nonphysical/caveated rows or offsets: bias_mean=0.053584; bias_p90=0.072046; bias_max=0.075639
- Acceptance criteria: Requires an approved prior/penalty or reporting policy for bias terms; biases must not be silently interpreted as transport water.

### `within_label_trend_anomaly`

- Residual definition: (theta_model - mean_label(theta_model)) - (theta_NMR_obs - mean_label(theta_NMR_obs))
- Nuisance terms: constant label/campaign offsets cancel by centering
- Selected candidate: `broad_continuous_001_003_length_0p021m`
- Current-objective rank of selected candidate: 56.0
- Bias/anomaly-safe rank of selected candidate: 1.0
- NMR objective: 235.78427385061542
- Normalized residual RMSE: 1.5671905391317007
- Nonphysical/caveated rows or offsets: absolute offsets removed; absolute water content not fitted
- Acceptance criteria: The executable assembler mode and ranking package now exist; accepting this option means promoting it to the reporting/search default and stating that NMR contributes trends/anomalies, not absolute mobile water content.

## Implication

The present permeability-field incumbent remains the best raw absolute-theta candidate, but it is only rank 14 under the recommended NMR trend/anomaly treatment. The best trend/anomaly candidate is rank 56 under the raw active objective, so the NMR residual definition materially affects candidate selection.

Do not change the default active objective silently. The centered-label anomaly assembler mode and regenerated ranking package now exist; promotion to the default reporting/search objective still requires an explicit modelling decision.
