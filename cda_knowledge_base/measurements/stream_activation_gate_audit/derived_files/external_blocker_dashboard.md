# External Blocker Dashboard

This dashboard consolidates the external measurement-gate requests and the separate CTE confirmation request.
It does not send, archive, delete, or label email; it only joins the local trackers and point-in-time Gmail live-state audit.

## Summary

- Status: `external_blocker_dashboard_generated_waiting_user_send_and_responses`
- Blockers: 8 total, 7 external measurement gates, 1 CTE confirmation row
- Open blockers: 8
- Unsent blockers: 8
- Missing-response blockers: 8
- Gmail live-state check: `2026-06-01T03:55:46+02:00`
- Expected drafts observed: 6/6
- Sent-subject hits: 0
- Provider-reply hits: 0
- Recent CD-A/HERMES/TeamBeam non-draft hits: 0
- Local gate recovery possible gate-closing rows: 0
- Downloads recovery possible gate-closing rows: 0

## Blocker Table

| Request | Type | Priority | Stream | Gate | Status | Draft | Observed | Response | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ert_transform_support` | `external_measurement_gate` | high | `ert_resistivity` | `ERT_TRANSFORM_SUPPORT` | `blocked_waiting_user_send_and_provider_response` | `r6776618065355728003` | `true` | `missing_response` | review_send_gmail_draft_then_file_provider_response_in_intake_dir |
| `ert_uncertainty` | `external_measurement_gate` | high | `ert_resistivity` | `ERT_UNCERTAINTY` | `blocked_waiting_user_send_and_provider_response` | `r6776618065355728003` | `true` | `missing_response` | review_send_gmail_draft_then_file_provider_response_in_intake_dir |
| `hm_numeric_exports` | `external_measurement_gate` | high | `other_hm_monitoring` | `HM_NUMERIC_EXPORTS` | `blocked_waiting_user_send_and_provider_response` | `r1284411814726937591` | `true` | `missing_response` | review_send_gmail_draft_then_file_provider_response_in_intake_dir |
| `hm_uncertainty` | `external_measurement_gate` | high | `other_hm_monitoring` | `HM_UNCERTAINTY` | `blocked_waiting_user_send_and_provider_response` | `r1284411814726937591` | `true` | `missing_response` | review_send_gmail_draft_then_file_provider_response_in_intake_dir |
| `rh_active_curve_provenance` | `external_measurement_gate` | high | `relative_humidity_suction` | `RH_ACTIVE_CURVE_PROVENANCE` | `blocked_waiting_user_send_and_provider_response` | `r-8461584324877432346` | `true` | `missing_response` | review_send_gmail_draft_then_file_provider_response_in_intake_dir |
| `taupe_unit_calibration` | `external_measurement_gate` | high | `taupe_tdr` | `TAUPE_UNIT_CALIBRATION` | `blocked_waiting_user_send_and_provider_response` | `r-4809950961900799564` | `true` | `missing_response` | review_send_gmail_draft_then_file_provider_response_in_intake_dir |
| `perm_endpoint_geometry` | `external_measurement_gate` | medium | `permeability_pulse_tests` | `PERM_SUPPORT` | `blocked_waiting_user_send_and_provider_response` | `r-4984596174110032107` | `true` | `missing_response` | review_send_gmail_draft_then_file_provider_response_in_intake_dir |
| `cte_value_confirmation` | `model_provenance_confirmation` | high | `model_provenance` | `CTE_VALUE_CONFIRMATION` | `blocked_waiting_user_send_and_provider_response` | `r2947727639429158073` | `true` | `no_response_recorded` | review_send_cte_confirmation_draft_then_record_provider_response |

## Details

### `ert_transform_support`

- Blocker type: `external_measurement_gate`
- Priority: `high`
- Stream/gate: `ert_resistivity` / `ERT_TRANSFORM_SUPPORT`
- Subject: CD-A ERT transform, support, and uncertainty needed for OGS comparison
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `Markus.Furche@bgr.de`
- Contact route: `coordinator_with_named_provider_cc`
- Gmail draft/message/thread: `r6776618065355728003` / `19e7f5b474a8b331` / `19e7f5b474a8b331`
- Gmail send status: `gmail_draft_created_not_sent`
- Observed in Gmail live-state audit: `true`
- Request/response status: `drafted_pending_send` / `missing_response`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md`
- Local recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Downloads recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Acceptance test: A reproducible ERT-to-OGS transform and accepted support mask can be encoded without freehand interpretation; the ERT spatial projection and support-sensitivity audits can be regenerated with no provisional-transform caveat.
- Current blocker/caveat: ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.
- Next action: `review_send_gmail_draft_then_file_provider_response_in_intake_dir`

### `ert_uncertainty`

- Blocker type: `external_measurement_gate`
- Priority: `high`
- Stream/gate: `ert_resistivity` / `ERT_UNCERTAINTY`
- Subject: CD-A ERT transform, support, and uncertainty needed for OGS comparison
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `Markus.Furche@bgr.de`
- Contact route: `coordinator_with_named_provider_cc`
- Gmail draft/message/thread: `r6776618065355728003` / `19e7f5b474a8b331` / `19e7f5b474a8b331`
- Gmail send status: `gmail_draft_created_not_sent`
- Observed in Gmail live-state audit: `true`
- Request/response status: `drafted_pending_send` / `missing_response`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md`
- Local recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Downloads recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Acceptance test: The ERT likelihood can assign defensible row/group weights without treating dense VTK cells as independent observations.
- Current blocker/caveat: No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.
- Next action: `review_send_gmail_draft_then_file_provider_response_in_intake_dir`

### `hm_numeric_exports`

- Blocker type: `external_measurement_gate`
- Priority: `high`
- Stream/gate: `other_hm_monitoring` / `HM_NUMERIC_EXPORTS`
- Subject: CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_specific_provider_unresolved`
- Gmail draft/message/thread: `r1284411814726937591` / `19e7f5b8191fa466` / `19e7f5b8191fa466`
- Gmail send status: `gmail_draft_created_not_sent`
- Observed in Gmail live-state audit: `true`
- Request/response status: `drafted_pending_send` / `missing_response`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md`
- Local recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Downloads recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Acceptance test: The other-HM source audit finds at least one hard-residual-ready numeric request class with time/epoch and model-facing support.
- Current blocker/caveat: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.
- Next action: `review_send_gmail_draft_then_file_provider_response_in_intake_dir`

### `hm_uncertainty`

- Blocker type: `external_measurement_gate`
- Priority: `high`
- Stream/gate: `other_hm_monitoring` / `HM_UNCERTAINTY`
- Subject: CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_specific_provider_unresolved`
- Gmail draft/message/thread: `r1284411814726937591` / `19e7f5b8191fa466` / `19e7f5b8191fa466`
- Gmail send status: `gmail_draft_created_not_sent`
- Observed in Gmail live-state audit: `true`
- Request/response status: `drafted_pending_send` / `missing_response`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md`
- Local recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Downloads recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Acceptance test: Each candidate other-HM residual has enough metadata to state which OGS quantity/support it measures and what residual weight it receives.
- Current blocker/caveat: Required metadata for hard HM residual weights are absent from the current local bundle.
- Next action: `review_send_gmail_draft_then_file_provider_response_in_intake_dir`

### `rh_active_curve_provenance`

- Blocker type: `external_measurement_gate`
- Priority: `high`
- Stream/gate: `relative_humidity_suction` / `RH_ACTIVE_CURVE_PROVENANCE`
- Subject: CD-A RH/suction boundary-curve provenance needed for OGS forcing
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_processing_owner_unresolved`
- Gmail draft/message/thread: `r-8461584324877432346` / `19e7f5ba6f82e787` / `19e7f5ba6f82e787`
- Gmail send status: `gmail_draft_created_not_sent`
- Observed in Gmail live-state audit: `true`
- Request/response status: `drafted_pending_send` / `missing_response`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md`
- Local recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Downloads recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Acceptance test: The active XML pressure curve can be regenerated or explained well enough that replacement curves/retention targets are no longer based on unknown provenance.
- Current blocker/caveat: Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.
- Next action: `review_send_gmail_draft_then_file_provider_response_in_intake_dir`

### `taupe_unit_calibration`

- Blocker type: `external_measurement_gate`
- Priority: `high`
- Stream/gate: `taupe_tdr` / `TAUPE_UNIT_CALIBRATION`
- Subject: CD-A Taupe/TDR workbook units and calibration needed before objective activation
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_provider_unresolved`
- Gmail draft/message/thread: `r-4809950961900799564` / `19e7f5bcbd697dcf` / `19e7f5bcbd697dcf`
- Gmail send status: `gmail_draft_created_not_sent`
- Observed in Gmail live-state audit: `true`
- Request/response status: `drafted_pending_send` / `missing_response`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md`
- Local recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Downloads recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Acceptance test: The Taupe semantics audit can decide whether absolute Taupe values are water content, permittivity/proxy, or trend-only evidence.
- Current blocker/caveat: Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.
- Next action: `review_send_gmail_draft_then_file_provider_response_in_intake_dir`

### `perm_endpoint_geometry`

- Blocker type: `external_measurement_gate`
- Priority: `medium`
- Stream/gate: `permeability_pulse_tests` / `PERM_SUPPORT`
- Subject: CD-A historical permeability endpoint geometry needed for inactive intervals
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_source_owner_unresolved`
- Gmail draft/message/thread: `r-4984596174110032107` / `19e7f5beff237940` / `19e7f5beff237940`
- Gmail send status: `gmail_draft_created_not_sent`
- Observed in Gmail live-state audit: `true`
- Request/response status: `drafted_pending_send` / `missing_response`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md`
- Local recovery: `keyword_context_found_but_gate_still_external`, possible closure rows `0`
- Downloads recovery: `supporting_local_context_only_gate_still_external`, possible closure rows `0`
- Acceptance test: Inactive historical rows can be projected to OGS cells with a trace/support definition rather than excluded for missing geometry.
- Current blocker/caveat: Historical permeability endpoints are needed only if these older rows should enter the fit.
- Next action: `review_send_gmail_draft_then_file_provider_response_in_intake_dir`

### `cte_value_confirmation`

- Blocker type: `model_provenance_confirmation`
- Priority: `high`
- Stream/gate: `model_provenance` / `CTE_VALUE_CONFIRMATION`
- Subject: CD-A OGS CTE value/provenance confirmation needed before thermal-parameter interpretation
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `Tuanny.Cajuhi@bgr.de`
- Contact route: `coordinator_with_model_setup_cc`
- Gmail draft/message/thread: `r2947727639429158073` / `19e7f61a36cb3470` / `19e7f61a36cb3470`
- Gmail send status: `gmail_draft_created_not_sent`
- Observed in Gmail live-state audit: `true`
- Request/response status: `drafted_pending_send` / `no_response_recorded`
- Intake directory: `not_applicable`
- Response notes: `inversion_workflow/cte_confirmation_request.md`
- Local recovery: `not_applicable_model_provenance_confirmation`, possible closure rows `not_applicable`
- Downloads recovery: `not_applicable_model_provenance_confirmation`, possible closure rows `not_applicable`
- Acceptance test: The CTE row in the report open-comment audit can move from open_confirmation_required to confirmed_inactive, confirmed_typo_not_changed, or confirmed_value_recorded with the provider response cited.
- Current blocker/caveat: The XML binds CTE to solid thermal_expansivity, but the value and comment look like a copied heat-capacity entry. The model must remain frozen, so this needs provenance confirmation rather than a local correction.
- Next action: `review_send_cte_confirmation_draft_then_record_provider_response`

## Source Artifacts

- `inversion_workflow/external_gate_response_intake.csv`
- `inversion_workflow/external_gate_gmail_drafts.csv`
- `inversion_workflow/external_gate_dispatch_audit_summary.json`
- `inversion_workflow/gmail_gate_live_state_audit_summary.json`
- `inversion_workflow/local_gate_recovery_audit_summary.json`
- `inversion_workflow/download_gate_recovery_audit_summary.json`
- `inversion_workflow/cte_confirmation_request.csv`
- `inversion_workflow/cte_confirmation_gmail_draft.csv`
- `inversion_workflow/cte_confirmation_request_summary.json`
