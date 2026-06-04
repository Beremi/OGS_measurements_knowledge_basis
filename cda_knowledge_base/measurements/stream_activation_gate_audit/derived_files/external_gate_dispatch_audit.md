# External Gate Dispatch Audit

This audit checks that the external measurement-gate request drafts, request-pack rows, and response-intake templates match before any request is sent.
It is not evidence that the emails were sent or that any external gate was answered.

## Summary

- Status: `external_gate_dispatch_gmail_drafts_created_waiting_user_send_and_responses`
- Requests audited: 7
- Recipient drafts: 5
- Ready requests: 7
- Failed per-request checks: 0
- Request rows with suggested To: 7
- Request rows with suggested Cc: 2
- Not-yet-sent requests: 7
- Gmail draft rows: 7
- Unique Gmail drafts: 5
- Missing responses: 7

## Cross-Checks

- `request_ids_match_intake`: `true`
- `request_id_counts_match_intake`: `true`
- `request_ids_unique`: `true`
- `intake_request_ids_unique`: `true`
- `all_recipient_drafts_exist`: `true`
- `all_suggested_to_present`: `true`
- `all_response_notes_exist`: `true`
- `all_acceptance_tests_present`: `true`
- `all_refresh_commands_present`: `true`
- `all_request_rows_have_gmail_draft`: `true`

## Dispatch Table

| Request | Draft | Gmail draft | Intake notes | Ready | Failures |
| --- | --- | --- | --- | --- | --- |
| `ert_transform_support` | `inversion_workflow/external_gate_requests/bgr_ert_markus_furche_via_gesa_ziefle.md` | `r6776618065355728003` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md` | `true` | none |
| `ert_uncertainty` | `inversion_workflow/external_gate_requests/bgr_ert_markus_furche_via_gesa_ziefle.md` | `r6776618065355728003` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md` | `true` | none |
| `hm_numeric_exports` | `inversion_workflow/external_gate_requests/bgr_other_hm_exports_via_gesa_ziefle.md` | `r1284411814726937591` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md` | `true` | none |
| `hm_uncertainty` | `inversion_workflow/external_gate_requests/bgr_other_hm_exports_via_gesa_ziefle.md` | `r1284411814726937591` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md` | `true` | none |
| `rh_active_curve_provenance` | `inversion_workflow/external_gate_requests/bgr_rh_boundary_curve_provenance_via_gesa_ziefle.md` | `r-8461584324877432346` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md` | `true` | none |
| `taupe_unit_calibration` | `inversion_workflow/external_gate_requests/taupe_tdr_calibration_via_gesa_ziefle.md` | `r-4809950961900799564` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md` | `true` | none |
| `perm_endpoint_geometry` | `inversion_workflow/external_gate_requests/bgr_historical_permeability_geometry_via_gesa_ziefle.md` | `r-4984596174110032107` | `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md` | `true` | none |

## Details

### `ert_transform_support`

- Audience: BGR ERT provider / Markus Furche via Gesa Ziefle
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `Markus.Furche@bgr.de`
- Contact route: `coordinator_with_named_provider_cc`
- Contact caveat: No direct Gmail sender messages from Markus were found in the scan, so the request is routed through Gesa with Markus as suggested CC.
- Gate: `ERT_TRANSFORM_SUPPORT`
- Draft: `inversion_workflow/external_gate_requests/bgr_ert_markus_furche_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md`
- Gmail draft id: `r6776618065355728003`
- Gmail message/thread: `19e7f5b474a8b331` / `19e7f5b474a8b331`
- Gmail send status: `gmail_draft_created_not_sent`
- Dispatch status: `gmail_draft_created_not_sent_waiting_response`
- Request status: `drafted_pending_send`
- Pack response status: `no_response_recorded`
- Intake response status: `missing_response`
- Failed checks: none
- Next action: `review_or_send_gmail_draft_then_file_response_in_intake_tracker`

### `ert_uncertainty`

- Audience: BGR ERT provider / Markus Furche via Gesa Ziefle
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `Markus.Furche@bgr.de`
- Contact route: `coordinator_with_named_provider_cc`
- Contact caveat: No direct Gmail sender messages from Markus were found in the scan, so the request is routed through Gesa with Markus as suggested CC.
- Gate: `ERT_UNCERTAINTY`
- Draft: `inversion_workflow/external_gate_requests/bgr_ert_markus_furche_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md`
- Gmail draft id: `r6776618065355728003`
- Gmail message/thread: `19e7f5b474a8b331` / `19e7f5b474a8b331`
- Gmail send status: `gmail_draft_created_not_sent`
- Dispatch status: `gmail_draft_created_not_sent_waiting_response`
- Request status: `drafted_pending_send`
- Pack response status: `no_response_recorded`
- Intake response status: `missing_response`
- Failed checks: none
- Next action: `review_or_send_gmail_draft_then_file_response_in_intake_tracker`

### `hm_numeric_exports`

- Audience: Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_specific_provider_unresolved`
- Contact caveat: Ask Gesa to forward to the appropriate BGR Geoscope, laser-scan, and levelling data owners if she is not the source.
- Gate: `HM_NUMERIC_EXPORTS`
- Draft: `inversion_workflow/external_gate_requests/bgr_other_hm_exports_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md`
- Gmail draft id: `r1284411814726937591`
- Gmail message/thread: `19e7f5b8191fa466` / `19e7f5b8191fa466`
- Gmail send status: `gmail_draft_created_not_sent`
- Dispatch status: `gmail_draft_created_not_sent_waiting_response`
- Request status: `drafted_pending_send`
- Pack response status: `no_response_recorded`
- Intake response status: `missing_response`
- Failed checks: none
- Next action: `review_or_send_gmail_draft_then_file_response_in_intake_tracker`

### `hm_uncertainty`

- Audience: Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_specific_provider_unresolved`
- Contact caveat: Ask Gesa to forward to the appropriate BGR Geoscope, laser-scan, and levelling data owners if she is not the source.
- Gate: `HM_UNCERTAINTY`
- Draft: `inversion_workflow/external_gate_requests/bgr_other_hm_exports_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md`
- Gmail draft id: `r1284411814726937591`
- Gmail message/thread: `19e7f5b8191fa466` / `19e7f5b8191fa466`
- Gmail send status: `gmail_draft_created_not_sent`
- Dispatch status: `gmail_draft_created_not_sent_waiting_response`
- Request status: `drafted_pending_send`
- Pack response status: `no_response_recorded`
- Intake response status: `missing_response`
- Failed checks: none
- Next action: `review_or_send_gmail_draft_then_file_response_in_intake_tracker`

### `rh_active_curve_provenance`

- Audience: Gesa Ziefle / BGR RH or OGS boundary-curve source
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_processing_owner_unresolved`
- Contact caveat: The scan does not identify a separate RH/OGS pressure-curve processing owner, so Gesa remains the routing contact.
- Gate: `RH_ACTIVE_CURVE_PROVENANCE`
- Draft: `inversion_workflow/external_gate_requests/bgr_rh_boundary_curve_provenance_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md`
- Gmail draft id: `r-8461584324877432346`
- Gmail message/thread: `19e7f5ba6f82e787` / `19e7f5ba6f82e787`
- Gmail send status: `gmail_draft_created_not_sent`
- Dispatch status: `gmail_draft_created_not_sent_waiting_response`
- Request status: `drafted_pending_send`
- Pack response status: `no_response_recorded`
- Intake response status: `missing_response`
- Failed checks: none
- Next action: `review_or_send_gmail_draft_then_file_response_in_intake_tracker`

### `taupe_unit_calibration`

- Audience: Taupe/TDR provider via Gesa Ziefle
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_provider_unresolved`
- Contact caveat: Ask Gesa to forward to the Taupe/TDR provider or confirm the unit/calibration source directly.
- Gate: `TAUPE_UNIT_CALIBRATION`
- Draft: `inversion_workflow/external_gate_requests/taupe_tdr_calibration_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md`
- Gmail draft id: `r-4809950961900799564`
- Gmail message/thread: `19e7f5bcbd697dcf` / `19e7f5bcbd697dcf`
- Gmail send status: `gmail_draft_created_not_sent`
- Dispatch status: `gmail_draft_created_not_sent_waiting_response`
- Request status: `drafted_pending_send`
- Pack response status: `no_response_recorded`
- Intake response status: `missing_response`
- Failed checks: none
- Next action: `review_or_send_gmail_draft_then_file_response_in_intake_tracker`

### `perm_endpoint_geometry`

- Audience: Gesa Ziefle / BGR permeability source
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `none`
- Contact route: `coordinator_only_source_owner_unresolved`
- Contact caveat: Ask Gesa to forward to the BGR permeability data owner if labelled interval endpoints come from another source.
- Gate: `PERM_SUPPORT`
- Draft: `inversion_workflow/external_gate_requests/bgr_historical_permeability_geometry_via_gesa_ziefle.md`
- Intake directory: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses`
- Response notes: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md`
- Gmail draft id: `r-4984596174110032107`
- Gmail message/thread: `19e7f5beff237940` / `19e7f5beff237940`
- Gmail send status: `gmail_draft_created_not_sent`
- Dispatch status: `gmail_draft_created_not_sent_waiting_response`
- Request status: `drafted_pending_send`
- Pack response status: `no_response_recorded`
- Intake response status: `missing_response`
- Failed checks: none
- Next action: `review_or_send_gmail_draft_then_file_response_in_intake_tracker`
