# Measurement Gate Closure Request

This package converts the stream activation-gate audit into concrete requests and
internal decisions needed before diagnostic measurement streams are promoted to
hard residuals in the frozen OGS workflow.

## Summary

- Requests: 13
- Failed-gate requests: 7
- Warning-gate requests: 4
- External requests: 7
- Internal or internal-with-confirmation decisions: 6
- High-priority request ids: ert_transform_support, ert_uncertainty, hm_numeric_exports, hm_uncertainty, rh_active_curve_provenance, taupe_unit_calibration, nmr_bound_water, perm_likelihood_policy, rh_uncertainty

Only direct permeability and NMR currently provide active objective rows. ERT,
Taupe/TDR, RH/suction, and other-HM monitoring must remain diagnostic,
boundary-audit, or qualitative streams until the requests below are closed.

## Priority Table

| Priority | Request | Stream | Gate | Audience | Unlocks |
| --- | --- | --- | --- | --- | --- |
| `high` | `ert_transform_support` | `ert_resistivity` | `ERT_TRANSFORM_SUPPORT` (fail) | BGR ERT provider / Markus Furche via Gesa Ziefle | Promote ERT from diagnostic field check to candidate active residual support. |
| `high` | `ert_uncertainty` | `ert_resistivity` | `ERT_UNCERTAINTY` (fail) | BGR ERT provider / Markus Furche via Gesa Ziefle | Defensible ERT likelihood weight or downweighted diagnostic residual. |
| `high` | `hm_numeric_exports` | `other_hm_monitoring` | `HM_NUMERIC_EXPORTS` (fail) | Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source | Potential pressure/deformation/laser/levelling validation residuals. |
| `high` | `hm_uncertainty` | `other_hm_monitoring` | `HM_UNCERTAINTY` (fail) | Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source | Defensible weights and activation gates for other-HM residuals. |
| `high` | `rh_active_curve_provenance` | `relative_humidity_suction` | `RH_ACTIVE_CURVE_PROVENANCE` (fail) | Gesa Ziefle / BGR RH or OGS boundary-curve source | Verified boundary forcing or a reproducible replacement curve. |
| `high` | `taupe_unit_calibration` | `taupe_tdr` | `TAUPE_UNIT_CALIBRATION` (fail) | Taupe/TDR provider via Gesa Ziefle | Possible absolute Taupe water-content/saturation residual, or confirmed trend-only use. |
| `high` | `nmr_bound_water` | `nmr_water_content` | `NMR_BOUND_WATER` (warn) | internal modelling decision, optionally checked with Stephan Costabel | A final NMR likelihood definition instead of a conditional active state residual. |
| `high` | `perm_likelihood_policy` | `permeability_pulse_tests` | `PERM_LIKELIHOOD_POLICY` (internal_policy) | internal modelling decision, optionally checked with Gesa Ziefle/BGR | A defensible direct-permeability objective policy for the next search or scenario reranking. |
| `high` | `rh_uncertainty` | `relative_humidity_suction` | `RH_UNCERTAINTY` (fail) | internal modelling decision with BGR confirmation if possible | Boundary-forcing replacement decision and possible retention-parameter gate. |
| `medium` | `perm_endpoint_geometry` | `permeability_pulse_tests` | `PERM_SUPPORT` (tracked_caveat) | Gesa Ziefle / BGR permeability source | Additional permeability pulse-test rows for direct parameter fitting. |
| `medium` | `perm_error_model` | `permeability_pulse_tests` | `PERM_ERROR_MODEL` (warn) | internal modelling decision, optionally checked with Gesa Ziefle/BGR | Cleaner wording for active permeability residuals and defensible sigma/caveat handling. |
| `medium` | `taupe_group_weights` | `taupe_tdr` | `TAUPE_GROUP_WEIGHTS` (warn) | internal modelling decision with Taupe/TDR provider confirmation if possible | Taupe trend likelihood weights or a clearly scoped diagnostic score. |
| `medium` | `taupe_support` | `taupe_tdr` | `TAUPE_SUPPORT` (warn) | internal modelling decision with Taupe/TDR provider confirmation if possible | A clean Taupe activation mask and report wording for excluded sensors. |

## Requests By Stream

### `ert_resistivity`

#### `ert_transform_support`

- Priority: `high`
- Gate: `ERT_TRANSFORM_SUPPORT` / coordinate transform and exact support mask confirmed (`fail`)
- Request type: `support_geometry_and_transform`
- Audience: BGR ERT provider / Markus Furche via Gesa Ziefle
- Owner/source: BGR ERT processing source
- External/internal: `external`
- Exact request: Confirm the coordinate frame of the ERT inversion VTK fields and electrode files, the exact transform into the local OGS 2D x/y frame, and the accepted near-niche support mask for model comparison. The current local operator assumes model_x = raw_x and model_y = raw_y + 500 and uses a provisional central support mask.
- Minimum acceptance criteria: A written transform definition or script; coordinate-frame origin and axes; tunnel/niche contour or support polygon; accepted handling of the 35 cm rock-depth recommendation; and a decision on whether the current 1.5 m/radial support variants are acceptable or must be replaced.
- Current evidence: support variants=9; best mean support-rank run=broad_continuous_001_001_length_0p023m_shift_1p004; rank correlations vs default={'inner_annulus_1p15_1p30m': 0.4285714285714286, 'outer_annulus_1p30_1p50m': 0.6571428571428573, 'radius_le_1p25m': 0.4285714285714286, 'radius_le_1p2m': 0.6571428571428573, 'radius_le_1p35m': 0.48571428571428577, 'radius_le_1p3m': 0.4285714285714286, 'radius_le_1p45m': 1.0, 'radius_le_1p4m': 0.942857142857143}
- Current blocker/caveat: ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.
- Why needed for model: ERT can only become a weighted log-resistivity residual if each inversion cell is placed on the same physical support as the OGS cells. The support-sensitivity audit shows that changing support can change candidate rankings.
- Would unlock: Promote ERT from diagnostic field check to candidate active residual support.
- Existing local artifacts: inversion_workflow/processed_observations/ert_spatial_projection_operator.md; inversion_workflow/ert_support_sensitivity.md; cda_knowledge_base/measurements/ert/source_files/ERT_meas_Niche_open.zip
- Related request package: none
- Source gate artifacts: ert_support_sensitivity_summary.json; ert_spatial_projection_operator.md

#### `ert_uncertainty`

- Priority: `high`
- Gate: `ERT_UNCERTAINTY` / inversion-field uncertainty/correlation model assigned (`fail`)
- Request type: `uncertainty_model`
- Audience: BGR ERT provider / Markus Furche via Gesa Ziefle
- Owner/source: BGR ERT inversion/evaluation source
- External/internal: `external`
- Exact request: Provide or approve an ERT inversion-field uncertainty and correlation model for log10 resistivity residuals: per-cell or region-level sigma, time correlation, spatial correlation/effective degrees of freedom, and any recommended filtering or aggregation before comparison to OGS theta-derived resistivity.
- Minimum acceptance criteria: Either a covariance/error export or an agreed simplified weighting rule, including units/log base, independence assumptions, date grouping, and rules for unstable or fracture-dominated cells.
- Current evidence: cross-run ERT MAE range=0.019635573360798686; no pixel/time covariance model is recorded
- Current blocker/caveat: No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.
- Why needed for model: The archive has dense ERT fields, but VTK pixels cannot be treated as independent observations without over-weighting ERT relative to sparse NMR/permeability data.
- Would unlock: Defensible ERT likelihood weight or downweighted diagnostic residual.
- Existing local artifacts: inversion_workflow/ert_candidate_discrimination.md; inversion_workflow/measurement_likelihood_model.md
- Related request package: none
- Source gate artifacts: ert_candidate_discrimination_summary.json; measurement_likelihood_model.md

### `nmr_water_content`

#### `nmr_bound_water`

- Priority: `high`
- Gate: `NMR_BOUND_WATER` / bound/interlayer-water bias quantified (`warn`)
- Request type: `internal_method_decision`
- Audience: internal modelling decision, optionally checked with Stephan Costabel
- Owner/source: IGN/UGN modelling team plus BGR NMR source if needed
- External/internal: `internal_with_optional_external_confirmation`
- Exact request: Choose the final NMR residual definition before reporting an all-measurement fit: raw absolute theta with an added model-error floor, label/campaign bias residual, within-position trend/anomaly residual, or a free-water correction based on bound/interlayer-water evidence.
- Minimum acceptance criteria: A documented objective formula, bias/offset parameter handling, sigma/error floor, which weekly/seasonal rows are active, and whether the known February-April 2025 4E detuning issue is excluded, corrected, or downweighted.
- Current evidence: bound-water usable-row required-offset p95=0.04017850052068304; bias audit runs=66; rank correlation=0.6351529067946979
- Current blocker/caveat: Raw absolute theta residuals remain conditional until a free-water/bound-water correction or anomaly residual is accepted.
- Why needed for model: NMR measures total NMR-visible water content, while the OGS state proxy is mobile theta = porosity * liquid_saturation. Many NMR rows exceed fixed model porosity unless a bound/interlayer-water or bias term is included.
- Would unlock: A final NMR likelihood definition instead of a conditional active state residual.
- Existing local artifacts: inversion_workflow/processed_observations/nmr_bound_water_sensitivity.md; inversion_workflow/nmr_candidate_bias_sensitivity.md
- Related request package: none
- Source gate artifacts: nmr_bound_water_sensitivity_summary.json; nmr_candidate_bias_sensitivity_summary.json

### `other_hm_monitoring`

#### `hm_numeric_exports`

- Priority: `high`
- Gate: `HM_NUMERIC_EXPORTS` / hard-residual-ready numeric time series located (`fail`)
- Request type: `source_file_request`
- Audience: Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source
- Owner/source: BGR other-HM monitoring source
- External/internal: `external`
- Exact request: Provide hard-residual-ready numeric exports for Geoscope mini-piezometers, extensometers, crackmeters, the 2026-04-20 laser-scan statistical interpretation, and the full precision-levelling survey table.
- Minimum acceptance criteria: Machine-readable tables with timestamps or survey epochs, instrument ids, measured values, units, coordinates/support ids, reference/zero conventions, calibration or processing provenance, quality/status flags, and uncertainty/covariance where available.
- Current evidence: hard-ready request classes=0; zip numeric-candidate members=0
- Current blocker/caveat: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.
- Why needed for model: The local catalogue has layout geometry and qualitative HM statements, but no numeric time series or statistical exports that can be sampled against OGS pressure/displacement states.
- Would unlock: Potential pressure/deformation/laser/levelling validation residuals.
- Existing local artifacts: inversion_workflow/processed_observations/other_hm_numeric_source_audit.md; cda_knowledge_base/measurements/other_hm_monitoring/source_files/
- Related request package: inversion_workflow/processed_observations/other_hm_missing_numeric_request.md
- Source gate artifacts: other_hm_numeric_source_audit_summary.json; other_hm_missing_numeric_request.md

#### `hm_uncertainty`

- Priority: `high`
- Gate: `HM_UNCERTAINTY` / units, epochs, reference conventions, uncertainty, and quality flags available (`fail`)
- Request type: `metadata_and_uncertainty_model`
- Audience: Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source
- Owner/source: BGR other-HM monitoring source
- External/internal: `external`
- Exact request: For every provided other-HM export, include the metadata required for residual weights: units, epochs, coordinate/support geometry, reference conventions, uncertainty/covariance, quality flags, and failure/maintenance intervals.
- Minimum acceptance criteria: Each table has self-contained units and reference conventions; failed sensors such as BCD-A9/B10 are flagged; laser registration uncertainty and masks are included; and levelling covariance/reference frame are documented.
- Current evidence: Do not assign hard HM residual weights until numeric exports include timestamps or survey epochs, units, support geometry, reference conventions, uncertainty/covariance, and quality/status flags.
- Current blocker/caveat: Required metadata for hard HM residual weights are absent from the current local bundle.
- Why needed for model: Even if numeric values are found, they cannot become hard residuals without metadata that states what OGS quantity and support they measure.
- Would unlock: Defensible weights and activation gates for other-HM residuals.
- Existing local artifacts: inversion_workflow/processed_observations/other_hm_missing_numeric_request.md; inversion_workflow/processed_observations/other_hm_numeric_source_audit.md
- Related request package: inversion_workflow/processed_observations/other_hm_missing_numeric_request.md
- Source gate artifacts: other_hm_numeric_source_audit.md

### `permeability_pulse_tests`

#### `perm_likelihood_policy`

- Priority: `high`
- Gate: `PERM_LIKELIHOOD_POLICY` / direct permeability robust/support-cell likelihood policy before more OGS (`internal_policy`)
- Request type: `likelihood_policy_decision`
- Audience: internal modelling decision, optionally checked with Gesa Ziefle/BGR
- Owner/source: IGN/UGN modelling team plus BGR permeability source if needed
- External/internal: `internal_with_optional_external_confirmation`
- Exact request: Choose the direct-permeability likelihood policy before more active-objective OGS spending: keep the current duplicate-weighted rowwise Gaussian default, promote a robust row likelihood, aggregate rows by model support cell, gate configured-scalar-range outliers, or require a new parameterization before running more candidates.
- Minimum acceptance criteria: A written policy choice, residual formula, row/group weights, outlier handling, reranking rule for existing candidates, and the condition under which the current rowwise Gaussian objective remains the report default.
- Current evidence: The likelihood-policy audit finds 75 active direct rows, current Gaussian objective 269.818057, top-10 row-loss share 0.494, 16 support-cell groups with observed range >=1 log10, and a support-cell weighted-mean diagnostic objective near zero.
- Current blocker/caveat: The active rowwise Gaussian policy is retained for reproducibility, but robust tails, support-cell aggregation, and scalar-range outlier handling are explicit modelling decisions before more active-objective OGS spending.
- Why needed for model: The current field fits duplicate-weighted means of repeated rows sharing the same support cell, while individual pulse-test rows within those cells conflict by several log units. More smooth field sampling is not the same thing as resolving the likelihood semantics.
- Would unlock: A defensible direct-permeability objective policy for the next search or scenario reranking.
- Existing local artifacts: inversion_workflow/permeability_likelihood_policy_audit.md; inversion_workflow/permeability_likelihood_decision_request.md
- Related request package: inversion_workflow/permeability_likelihood_decision_request.md
- Source gate artifacts: permeability_likelihood_policy_audit.md; permeability_likelihood_decision_request.md

#### `perm_endpoint_geometry`

- Priority: `medium`
- Gate: `PERM_SUPPORT` / missing historical endpoint geometry for inactive permeability rows (`tracked_caveat`)
- Request type: `source_file_request`
- Audience: Gesa Ziefle / BGR permeability source
- Owner/source: BGR permeability measurement source
- External/internal: `external`
- Exact request: Provide labelled endpoint geometry or approved digitized traces for the historical BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 permeability intervals that are currently retained but inactive.
- Minimum acceptance criteria: For each interval: borehole id, open/closed assignment, start/end coordinates or depths with convention, orientation, interval length/support, date/source table, permeability value, and uncertainty/evaluation note.
- Current evidence: 98 older permeability rows are retained but inactive because labelled endpoint geometry is missing.
- Current blocker/caveat: Historical permeability endpoints are needed only if these older rows should enter the fit.
- Why needed for model: These older rows cannot be projected to OGS cells until the measured 3D interval volume is known. They are useful because they broaden the permeability evidence outside the currently active mapped rows.
- Would unlock: Additional permeability pulse-test rows for direct parameter fitting.
- Existing local artifacts: inversion_workflow/processed_observations/permeability_missing_geometry_audit.md
- Related request package: inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md
- Source gate artifacts: permeability_missing_geometry_audit.md; permeability_endpoint_geometry_request.md

#### `perm_error_model`

- Priority: `medium`
- Gate: `PERM_ERROR_MODEL` / broad gas-pulse model-error scale (`warn`)
- Request type: `method_decision_and_optional_source_confirmation`
- Audience: internal modelling decision, optionally checked with Gesa Ziefle/BGR
- Owner/source: IGN/UGN modelling team plus BGR permeability source if needed
- External/internal: `internal_with_optional_external_confirmation`
- Exact request: Approve the gas-pulse permeability residual model: log10 intrinsic permeability space, duplicate-aware interval weights, current sigma = 0.5 log10 units, and the policy for gas/slip/liquid-equivalent caveats.
- Minimum acceptance criteria: A written statement of whether the nitrogen pulse-test values are used as intrinsic permeability constraints on the OGS base permeability tensor magnitude, whether any Klinkenberg/slip correction is needed, and how scalar interval measurements are mapped to the anisotropic tensor field.
- Current evidence: current evaluator uses sigma=0.5 log10 units and duplicate-aware weights
- Current blocker/caveat: Gas/slip/liquid-equivalent interpretation remains a tracked model-error caveat.
- Why needed for model: The active field is a tensor-valued intrinsic permeability. The measurements are gas pulse-test interval estimates with directional/support effects, so the residual must not be described as direct water hydraulic conductivity or as all tensor components.
- Would unlock: Cleaner wording for active permeability residuals and defensible sigma/caveat handling.
- Existing local artifacts: inversion_workflow/processed_observations/permeability_measurement_semantics.md; inversion_workflow/processed_observations/permeability_observation_targets.csv
- Related request package: inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md
- Source gate artifacts: evaluate_permeability_targets.py; permeability_measurement_semantics.md

### `relative_humidity_suction`

#### `rh_active_curve_provenance`

- Priority: `high`
- Gate: `RH_ACTIVE_CURVE_PROVENANCE` / active OGS pressure curve provenance confirmed (`fail`)
- Request type: `provenance_and_processing_files`
- Audience: Gesa Ziefle / BGR RH or OGS boundary-curve source
- Owner/source: BGR OGS/RH processing source
- External/internal: `external`
- Exact request: Provide the provenance for the active open-niche pressure curve in 08_08_open_niche_seasonal.xml: source sensors, input sheets, scripts/notebooks, time-axis origin, smoothing/filtering, manual edits, Kelvin constants, sign convention, and open/closed curve mapping.
- Minimum acceptance criteria: Original or intermediate table/script, sensor selection rule, model-time zero and timezone, RH percent/fraction convention, temperature/density constants, pressure unit/sign, extrapolation policy, and decision for post-active-curve dates.
- Current evidence: provenance request rows=6; active outside candidate envelope=575
- Current blocker/caveat: Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.
- Why needed for model: RH/suction affects the OGS boundary forcing. The local RH-derived candidate envelope does not reproduce the active curve, so replacing or trusting the curve requires provenance.
- Would unlock: Verified boundary forcing or a reproducible replacement curve.
- Existing local artifacts: inversion_workflow/processed_observations/rh_boundary_candidate_curves.md; inversion_workflow/processed_observations/rh_boundary_uncertainty.md
- Related request package: inversion_workflow/processed_observations/rh_boundary_provenance_request.md
- Source gate artifacts: rh_boundary_provenance_request_summary.json; rh_boundary_uncertainty_summary.json

#### `rh_uncertainty`

- Priority: `high`
- Gate: `RH_UNCERTAINTY` / boundary/retention uncertainty model accepted (`fail`)
- Request type: `uncertainty_model_and_policy`
- Audience: internal modelling decision with BGR confirmation if possible
- Owner/source: IGN/UGN modelling team plus BGR RH source if needed
- External/internal: `internal_with_optional_external_confirmation`
- Exact request: Decide whether RH/suction enters only as boundary forcing, as a retention validation target, or as a future calibration target; approve the boundary/retention uncertainty model and replacement policy for RH-derived curves.
- Minimum acceptance criteria: Accepted sensor subset; uncertainty bands for RH-to-pressure conversion; treatment of RH7/RH8 low outliers and high-RH values; whether candidate curves replace or only audit the active XML curve; and release gates for retention parameters.
- Current evidence: envelope dates=1064; overlap pressure-range p50=2.103967930926996
- Current blocker/caveat: Local RH-derived envelope is quantified but not accepted as replacement forcing or retention likelihood.
- Why needed for model: A pressure boundary can move the entire desaturation response. It should not be fitted or replaced without a clear uncertainty and provenance policy.
- Would unlock: Boundary-forcing replacement decision and possible retention-parameter gate.
- Existing local artifacts: inversion_workflow/processed_observations/rh_boundary_uncertainty.md; inversion_workflow/processed_observations/rh_boundary_candidate_curves.md
- Related request package: inversion_workflow/processed_observations/rh_boundary_provenance_request.md
- Source gate artifacts: rh_boundary_uncertainty_summary.json; rh_boundary_uncertainty.md

### `taupe_tdr`

#### `taupe_unit_calibration`

- Priority: `high`
- Gate: `TAUPE_UNIT_CALIBRATION` / Taupe workbook unit and absolute calibration confirmed (`fail`)
- Request type: `calibration_confirmation`
- Audience: Taupe/TDR provider via Gesa Ziefle
- Owner/source: BGR/ISU Taupe processing source
- External/internal: `external`
- Exact request: Confirm what the values in Taupe_WC.xlsx physically represent: calibrated volumetric water-content percent, relative dielectric permittivity, ARDP-derived proxy, or another quantity. Provide the sensor-specific calibration equations and uncertainty.
- Minimum acceptance criteria: Workbook unit for every sheet/column; calibration equation and constants; whether values are already corrected for rock porosity/mineral matrix; uncertainty by sensor/band; baseline/reference date; and ARDP-to-water or dielectric conversion details.
- Current evidence: absolute candidate conversions remain sanity checks; Topp physical rows are zero in current audit
- Current blocker/caveat: Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.
- Why needed for model: The current workbook values pass some sanity checks if interpreted as water-content percent but fail if interpreted through a generic Topp permittivity conversion. Absolute Taupe residuals would be misleading without calibration.
- Would unlock: Possible absolute Taupe water-content/saturation residual, or confirmed trend-only use.
- Existing local artifacts: inversion_workflow/processed_observations/taupe_tdr_semantics.md; cda_knowledge_base/measurements/taupe_tdr/source_files/Taupe_WC.xlsx
- Related request package: none
- Source gate artifacts: taupe_tdr_semantics.md; measurement_likelihood_model.md

#### `taupe_group_weights`

- Priority: `medium`
- Gate: `TAUPE_GROUP_WEIGHTS` / series/group weighting and uncertainty model accepted (`warn`)
- Request type: `uncertainty_model`
- Audience: internal modelling decision with Taupe/TDR provider confirmation if possible
- Owner/source: IGN/UGN modelling team plus BGR/ISU Taupe source if needed
- External/internal: `internal_with_optional_external_confirmation`
- Exact request: Approve Taupe/TDR grouped weighting before objective activation: aggregate weighting, equal-series, equal-sensor, equal-EDZ-band, robust/trimmed score, or a provider-supplied series uncertainty model.
- Minimum acceptance criteria: Series grouping rule, sigma/error model, handling of strongly correlated EDZ bands, sensor-specific downweighting, and whether A3/A4 only or all sensors should contribute.
- Current evidence: series-weight runs=66; compared series=12; distinct per-series winners=8
- Current blocker/caveat: Series-specific uncertainty and grouped weighting remain part of the calibration gate.
- Why needed for model: The series-weight audit shows different Taupe subseries prefer different permeability candidates. A naive row count would over-weight dense correlated bands.
- Would unlock: Taupe trend likelihood weights or a clearly scoped diagnostic score.
- Existing local artifacts: inversion_workflow/taupe_series_weight_sensitivity.md; inversion_workflow/taupe_candidate_discrimination.md
- Related request package: none
- Source gate artifacts: taupe_series_weight_sensitivity_summary.json

#### `taupe_support`

- Priority: `medium`
- Gate: `TAUPE_SUPPORT` / all relevant Taupe sensors inside current mesh support (`warn`)
- Request type: `support_geometry_decision`
- Audience: internal modelling decision with Taupe/TDR provider confirmation if possible
- Owner/source: IGN/UGN modelling team plus BGR/ISU Taupe source if needed
- External/internal: `internal_with_optional_external_confirmation`
- Exact request: Decide how to handle A7/A8 Taupe sensors that are outside the current Niche-4 OGS support: exclude them, use them only qualitatively, expand the geometry/model scope, or map them to a separate support if justified.
- Minimum acceptance criteria: Sensor/borehole support decision for A3, A4, A7, and A8; explicit inclusion/exclusion flags; and a statement that excluded sensors must not be counted as active residuals.
- Current evidence: uncompared/outside-support series=12
- Current blocker/caveat: A7/A8 remain outside the current Niche-4 mesh support.
- Why needed for model: Half of the Taupe workbook series are outside the current local mesh support. Including them without matching OGS support would create nonphysical residuals.
- Would unlock: A clean Taupe activation mask and report wording for excluded sensors.
- Existing local artifacts: inversion_workflow/processed_observations/taupe_tdr_semantics.md; inversion_workflow/taupe_series_weight_sensitivity.md
- Related request package: none
- Source gate artifacts: taupe_series_weight_sensitivity_summary.json; taupe_tdr_semantics.md

## Email-Ready Grouping

### External BGR / Provider Requests

- `ert_transform_support` to BGR ERT provider / Markus Furche via Gesa Ziefle: Confirm the coordinate frame of the ERT inversion VTK fields and electrode files, the exact transform into the local OGS 2D x/y frame, and the accepted near-niche support mask for model comparison. The current local operator assumes model_x = raw_x and model_y = raw_y + 500 and uses a provisional central support mask. Minimum acceptance: A written transform definition or script; coordinate-frame origin and axes; tunnel/niche contour or support polygon; accepted handling of the 35 cm rock-depth recommendation; and a decision on whether the current 1.5 m/radial support variants are acceptable or must be replaced.
- `ert_uncertainty` to BGR ERT provider / Markus Furche via Gesa Ziefle: Provide or approve an ERT inversion-field uncertainty and correlation model for log10 resistivity residuals: per-cell or region-level sigma, time correlation, spatial correlation/effective degrees of freedom, and any recommended filtering or aggregation before comparison to OGS theta-derived resistivity. Minimum acceptance: Either a covariance/error export or an agreed simplified weighting rule, including units/log base, independence assumptions, date grouping, and rules for unstable or fracture-dominated cells.
- `hm_numeric_exports` to Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source: Provide hard-residual-ready numeric exports for Geoscope mini-piezometers, extensometers, crackmeters, the 2026-04-20 laser-scan statistical interpretation, and the full precision-levelling survey table. Minimum acceptance: Machine-readable tables with timestamps or survey epochs, instrument ids, measured values, units, coordinates/support ids, reference/zero conventions, calibration or processing provenance, quality/status flags, and uncertainty/covariance where available.
- `hm_uncertainty` to Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source: For every provided other-HM export, include the metadata required for residual weights: units, epochs, coordinate/support geometry, reference conventions, uncertainty/covariance, quality flags, and failure/maintenance intervals. Minimum acceptance: Each table has self-contained units and reference conventions; failed sensors such as BCD-A9/B10 are flagged; laser registration uncertainty and masks are included; and levelling covariance/reference frame are documented.
- `rh_active_curve_provenance` to Gesa Ziefle / BGR RH or OGS boundary-curve source: Provide the provenance for the active open-niche pressure curve in 08_08_open_niche_seasonal.xml: source sensors, input sheets, scripts/notebooks, time-axis origin, smoothing/filtering, manual edits, Kelvin constants, sign convention, and open/closed curve mapping. Minimum acceptance: Original or intermediate table/script, sensor selection rule, model-time zero and timezone, RH percent/fraction convention, temperature/density constants, pressure unit/sign, extrapolation policy, and decision for post-active-curve dates.
- `taupe_unit_calibration` to Taupe/TDR provider via Gesa Ziefle: Confirm what the values in Taupe_WC.xlsx physically represent: calibrated volumetric water-content percent, relative dielectric permittivity, ARDP-derived proxy, or another quantity. Provide the sensor-specific calibration equations and uncertainty. Minimum acceptance: Workbook unit for every sheet/column; calibration equation and constants; whether values are already corrected for rock porosity/mineral matrix; uncertainty by sensor/band; baseline/reference date; and ARDP-to-water or dielectric conversion details.
- `perm_endpoint_geometry` to Gesa Ziefle / BGR permeability source: Provide labelled endpoint geometry or approved digitized traces for the historical BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 permeability intervals that are currently retained but inactive. Minimum acceptance: For each interval: borehole id, open/closed assignment, start/end coordinates or depths with convention, orientation, interval length/support, date/source table, permeability value, and uncertainty/evaluation note.

### Internal Decisions

- `nmr_bound_water`: Choose the final NMR residual definition before reporting an all-measurement fit: raw absolute theta with an added model-error floor, label/campaign bias residual, within-position trend/anomaly residual, or a free-water correction based on bound/interlayer-water evidence. Minimum acceptance: A documented objective formula, bias/offset parameter handling, sigma/error floor, which weekly/seasonal rows are active, and whether the known February-April 2025 4E detuning issue is excluded, corrected, or downweighted.
- `perm_likelihood_policy`: Choose the direct-permeability likelihood policy before more active-objective OGS spending: keep the current duplicate-weighted rowwise Gaussian default, promote a robust row likelihood, aggregate rows by model support cell, gate configured-scalar-range outliers, or require a new parameterization before running more candidates. Minimum acceptance: A written policy choice, residual formula, row/group weights, outlier handling, reranking rule for existing candidates, and the condition under which the current rowwise Gaussian objective remains the report default.
- `rh_uncertainty`: Decide whether RH/suction enters only as boundary forcing, as a retention validation target, or as a future calibration target; approve the boundary/retention uncertainty model and replacement policy for RH-derived curves. Minimum acceptance: Accepted sensor subset; uncertainty bands for RH-to-pressure conversion; treatment of RH7/RH8 low outliers and high-RH values; whether candidate curves replace or only audit the active XML curve; and release gates for retention parameters.
- `perm_error_model`: Approve the gas-pulse permeability residual model: log10 intrinsic permeability space, duplicate-aware interval weights, current sigma = 0.5 log10 units, and the policy for gas/slip/liquid-equivalent caveats. Minimum acceptance: A written statement of whether the nitrogen pulse-test values are used as intrinsic permeability constraints on the OGS base permeability tensor magnitude, whether any Klinkenberg/slip correction is needed, and how scalar interval measurements are mapped to the anisotropic tensor field.
- `taupe_group_weights`: Approve Taupe/TDR grouped weighting before objective activation: aggregate weighting, equal-series, equal-sensor, equal-EDZ-band, robust/trimmed score, or a provider-supplied series uncertainty model. Minimum acceptance: Series grouping rule, sigma/error model, handling of strongly correlated EDZ bands, sensor-specific downweighting, and whether A3/A4 only or all sensors should contribute.
- `taupe_support`: Decide how to handle A7/A8 Taupe sensors that are outside the current Niche-4 OGS support: exclude them, use them only qualitatively, expand the geometry/model scope, or map them to a separate support if justified. Minimum acceptance: Sensor/borehole support decision for A3, A4, A7, and A8; explicit inclusion/exclusion flags; and a statement that excluded sensors must not be counted as active residuals.
