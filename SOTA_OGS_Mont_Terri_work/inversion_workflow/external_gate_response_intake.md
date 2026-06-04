# External Gate Response Intake

This tracker says where each external response should be filed, what minimum metadata is needed, and which generated artifacts need refreshing after a response arrives.
It does not indicate that the requests have been sent or answered.

## Summary

- Status: `external_gate_response_intake_generated_waiting_for_responses`
- External request rows tracked: 7
- Missing responses: 7
- Intake directories created: 5

## Intake Table

| Request | Gate | Status | Intake directory | Acceptance test |
| --- | --- | --- | --- | --- |
| `ert_transform_support` | `ERT_TRANSFORM_SUPPORT` | `missing_response` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses` | A reproducible ERT-to-OGS transform and accepted support mask can be encoded without freehand interpretation; the ERT spatial projection and support-sensitivity audits can be regenerated with no provisional-transform caveat. |
| `ert_uncertainty` | `ERT_UNCERTAINTY` | `missing_response` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses` | The ERT likelihood can assign defensible row/group weights without treating dense VTK cells as independent observations. |
| `hm_numeric_exports` | `HM_NUMERIC_EXPORTS` | `missing_response` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses` | The other-HM source audit finds at least one hard-residual-ready numeric request class with time/epoch and model-facing support. |
| `hm_uncertainty` | `HM_UNCERTAINTY` | `missing_response` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses` | Each candidate other-HM residual has enough metadata to state which OGS quantity/support it measures and what residual weight it receives. |
| `rh_active_curve_provenance` | `RH_ACTIVE_CURVE_PROVENANCE` | `missing_response` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses` | The active XML pressure curve can be regenerated or explained well enough that replacement curves/retention targets are no longer based on unknown provenance. |
| `taupe_unit_calibration` | `TAUPE_UNIT_CALIBRATION` | `missing_response` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses` | The Taupe semantics audit can decide whether absolute Taupe values are water content, permittivity/proxy, or trend-only evidence. |
| `perm_endpoint_geometry` | `PERM_SUPPORT` | `missing_response` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses` | Inactive historical rows can be projected to OGS cells with a trace/support definition rather than excluded for missing geometry. |

## Details

### `ert_transform_support`

- Audience: BGR ERT provider / Markus Furche via Gesa Ziefle
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `Markus.Furche@bgr.de`
- Contact route: `coordinator_with_named_provider_cc`
- Recipient draft: `inversion_workflow/external_gate_requests/bgr_ert_markus_furche_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses`
- Expected response artifacts: Coordinate-frame note or transform script; electrode/inversion coordinate reference; accepted tunnel/niche support polygon or mask; decision on 35 cm rock-depth handling and the current radial support variants.
- Minimum intake metadata: source contact, response date, coordinate origin/axes, unit convention, support-mask definition, and whether the current local transform model_x=raw_x/model_y=raw_y+500 is accepted.
- Acceptance test: A reproducible ERT-to-OGS transform and accepted support mask can be encoded without freehand interpretation; the ERT spatial projection and support-sensitivity audits can be regenerated with no provisional-transform caveat.
- Refresh commands after intake: `python inversion_workflow/scripts/build_ert_spatial_projection_lookup.py; python inversion_workflow/scripts/build_ert_support_sensitivity_audit.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_measurement_gate_closure_request.py; python inversion_workflow/scripts/build_external_gate_request_pack.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`
- Gate-closure effect: May close ERT_TRANSFORM_SUPPORT and make ERT support ready for weighted residual design.
- Current blocker/caveat: ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.
- Response notes file to create/update: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md`

### `ert_uncertainty`

- Audience: BGR ERT provider / Markus Furche via Gesa Ziefle
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `Markus.Furche@bgr.de`
- Contact route: `coordinator_with_named_provider_cc`
- Recipient draft: `inversion_workflow/external_gate_requests/bgr_ert_markus_furche_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses`
- Expected response artifacts: Per-cell, region, or time-level ERT uncertainty/covariance export, or written simplified weighting rule with log base, filtering, spatial correlation, and effective degrees of freedom.
- Minimum intake metadata: sigma units/log base, temporal grouping, spatial correlation assumptions, filtering rules, unstable-cell handling, and whether cells may be aggregated before comparison.
- Acceptance test: The ERT likelihood can assign defensible row/group weights without treating dense VTK cells as independent observations.
- Refresh commands after intake: `python inversion_workflow/scripts/build_measurement_likelihood_model.py; python inversion_workflow/scripts/build_ert_candidate_discrimination_audit.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_measurement_gate_closure_request.py; python inversion_workflow/scripts/build_external_gate_request_pack.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`
- Gate-closure effect: May close ERT_UNCERTAINTY and allow ERT to move from diagnostic screen toward a hard residual.
- Current blocker/caveat: No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.
- Response notes file to create/update: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md`

### `hm_numeric_exports`

- Audience: Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_specific_provider_unresolved`
- Recipient draft: `inversion_workflow/external_gate_requests/bgr_other_hm_exports_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses`
- Expected response artifacts: Machine-readable Geoscope mini-piezometer, extensometer, crackmeter, laser-scan statistical interpretation, and precision-levelling tables.
- Minimum intake metadata: instrument id, timestamp or survey epoch, measured value, unit, coordinate/support id, reference/zero convention, processing provenance, and quality/status flag.
- Acceptance test: The other-HM source audit finds at least one hard-residual-ready numeric request class with time/epoch and model-facing support.
- Refresh commands after intake: `python inversion_workflow/scripts/build_other_hm_monitoring_inventory.py; python inversion_workflow/scripts/build_other_hm_missing_numeric_request.py; python inversion_workflow/scripts/build_measurement_operator_coverage.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_measurement_gate_closure_request.py; python inversion_workflow/scripts/build_external_gate_request_pack.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`
- Gate-closure effect: May close HM_NUMERIC_EXPORTS and create candidate pressure/deformation/laser/levelling validation residuals.
- Current blocker/caveat: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.
- Response notes file to create/update: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md`

### `hm_uncertainty`

- Audience: Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_specific_provider_unresolved`
- Recipient draft: `inversion_workflow/external_gate_requests/bgr_other_hm_exports_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses`
- Expected response artifacts: Uncertainty/covariance or accepted simplified weighting notes for every supplied other-HM numeric export, including failed-sensor and maintenance intervals.
- Minimum intake metadata: unit/reference convention, uncertainty model, covariance or independence assumptions, quality flags, failure periods, laser registration uncertainty/masks, and levelling covariance frame.
- Acceptance test: Each candidate other-HM residual has enough metadata to state which OGS quantity/support it measures and what residual weight it receives.
- Refresh commands after intake: `python inversion_workflow/scripts/build_other_hm_missing_numeric_request.py; python inversion_workflow/scripts/build_measurement_likelihood_model.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_measurement_gate_closure_request.py; python inversion_workflow/scripts/build_external_gate_request_pack.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`
- Gate-closure effect: May close HM_UNCERTAINTY after numeric exports exist and residual weights are defensible.
- Current blocker/caveat: Required metadata for hard HM residual weights are absent from the current local bundle.
- Response notes file to create/update: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md`

### `rh_active_curve_provenance`

- Audience: Gesa Ziefle / BGR RH or OGS boundary-curve source
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_processing_owner_unresolved`
- Recipient draft: `inversion_workflow/external_gate_requests/bgr_rh_boundary_curve_provenance_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses`
- Expected response artifacts: Active open-niche pressure-curve source table, script/notebook, sensor selection note, Kelvin conversion constants, time-axis origin/timezone, smoothing/manual-edit policy, sign convention, and open/closed curve mapping.
- Minimum intake metadata: source sensors/sheets, model-time zero, RH percent/fraction convention, temperature/density constants, pressure unit/sign, extension/extrapolation policy, and post-active-curve decision.
- Acceptance test: The active XML pressure curve can be regenerated or explained well enough that replacement curves/retention targets are no longer based on unknown provenance.
- Refresh commands after intake: `python inversion_workflow/scripts/audit_rh_boundary_curve.py; python inversion_workflow/scripts/build_rh_semantics_audit.py; python inversion_workflow/scripts/build_rh_boundary_candidate_curves.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_measurement_gate_closure_request.py; python inversion_workflow/scripts/build_external_gate_request_pack.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`
- Gate-closure effect: May close RH_ACTIVE_CURVE_PROVENANCE and make RH boundary forcing reproducible.
- Current blocker/caveat: Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.
- Response notes file to create/update: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md`

### `taupe_unit_calibration`

- Audience: Taupe/TDR provider via Gesa Ziefle
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_provider_unresolved`
- Recipient draft: `inversion_workflow/external_gate_requests/taupe_tdr_calibration_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses`
- Expected response artifacts: Taupe_WC unit definition, sensor/band calibration equations, uncertainty by sensor/band, baseline/reference date, and ARDP/dielectric/water-content conversion notes.
- Minimum intake metadata: workbook sheet/column unit, whether values are volumetric water-content percent or a proxy, matrix/porosity correction status, calibration constants, and uncertainty model.
- Acceptance test: The Taupe semantics audit can decide whether absolute Taupe values are water content, permittivity/proxy, or trend-only evidence.
- Refresh commands after intake: `python inversion_workflow/scripts/build_taupe_semantics_audit.py; python inversion_workflow/scripts/build_taupe_observation_operator.py; python inversion_workflow/scripts/build_taupe_candidate_discrimination_audit.py; python inversion_workflow/scripts/build_taupe_series_weight_sensitivity_audit.py; python inversion_workflow/scripts/build_measurement_likelihood_model.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_measurement_gate_closure_request.py; python inversion_workflow/scripts/build_external_gate_request_pack.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`
- Gate-closure effect: May close TAUPE_UNIT_CALIBRATION and allow Taupe to become trend-only or absolute residual evidence.
- Current blocker/caveat: Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.
- Response notes file to create/update: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md`

### `perm_endpoint_geometry`

- Audience: Gesa Ziefle / BGR permeability source
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_source_owner_unresolved`
- Recipient draft: `inversion_workflow/external_gate_requests/bgr_historical_permeability_geometry_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses`
- Expected response artifacts: Endpoint coordinates, labelled digitized traces, or interval geometry tables for historical BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 permeability intervals.
- Minimum intake metadata: borehole id, open/closed assignment, start/end coordinates or depths, orientation convention, interval length/support, date/source table, permeability value, and uncertainty/evaluation note.
- Acceptance test: Inactive historical rows can be projected to OGS cells with a trace/support definition rather than excluded for missing geometry.
- Refresh commands after intake: `python inversion_workflow/scripts/build_permeability_observation_targets.py; python inversion_workflow/scripts/build_permeability_semantics_audit.py; python inversion_workflow/scripts/evaluate_permeability_targets.py; python inversion_workflow/scripts/build_measurement_operator_coverage.py; python inversion_workflow/scripts/build_measurement_likelihood_model.py; python inversion_workflow/scripts/build_measurement_stream_gate_audit.py; python inversion_workflow/scripts/build_measurement_gate_closure_request.py; python inversion_workflow/scripts/build_external_gate_request_pack.py; python inversion_workflow/scripts/build_objective_readiness_audit.py`
- Gate-closure effect: May close the tracked PERM_SUPPORT caveat and add historical pulse-test rows to the direct parameter objective.
- Current blocker/caveat: Historical permeability endpoints are needed only if these older rows should enter the fit.
- Response notes file to create/update: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md`
