# Gmail Draft Send Review Packet

This packet consolidates the local review state for the six Gmail drafts that
block final inversion promotion. It does not send, archive, delete, or label
email.

- Status: `gmail_draft_send_review_packet_generated_not_sent`
- Drafts: 6
- Unsent drafts: 6
- Ready for user review: 6
- External measurement drafts: 5
- CTE confirmation drafts: 1
- Gmail live-state checked at: `2026-06-01T03:55:46+02:00`
- Sent-subject hits: 0
- Provider-reply hits: 0

## Drafts

| Draft | Type | Requests | To | Cc | Subject | Ready | Response notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `r6776618065355728003` | `external_measurement_gate` | `ert_transform_support,ert_uncertainty` | Gesa.Ziefle@bgr.de | Markus.Furche@bgr.de | CD-A ERT transform, support, and uncertainty needed for OGS comparison | `True` | /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md |
| `r1284411814726937591` | `external_measurement_gate` | `hm_numeric_exports,hm_uncertainty` | Gesa.Ziefle@bgr.de | none | CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation | `True` | /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md |
| `r-8461584324877432346` | `external_measurement_gate` | `rh_active_curve_provenance` | Gesa.Ziefle@bgr.de | none | CD-A RH/suction boundary-curve provenance needed for OGS forcing | `True` | /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md |
| `r-4809950961900799564` | `external_measurement_gate` | `taupe_unit_calibration` | Gesa.Ziefle@bgr.de | none | CD-A Taupe/TDR workbook units and calibration needed before objective activation | `True` | /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md |
| `r-4984596174110032107` | `external_measurement_gate` | `perm_endpoint_geometry` | Gesa.Ziefle@bgr.de | none | CD-A historical permeability endpoint geometry needed for inactive intervals | `True` | /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md |
| `r2947727639429158073` | `model_provenance_confirmation` | `cte_value_confirmation` | Gesa.Ziefle@bgr.de | Tuanny.Cajuhi@bgr.de | CD-A OGS CTE value/provenance confirmation needed before thermal-parameter interpretation | `True` | inversion_workflow/cte_confirmation_request.md |

## Review Notes

### `r6776618065355728003`

- Subject: CD-A ERT transform, support, and uncertainty needed for OGS comparison
- To: Gesa.Ziefle@bgr.de
- Cc: Markus.Furche@bgr.de
- Local draft file(s): inversion_workflow/external_gate_requests/bgr_ert_markus_furche_via_gesa_ziefle.md
- Request ids: ert_transform_support,ert_uncertainty
- Current blocker: ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.; No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.
- Acceptance evidence: A reproducible ERT-to-OGS transform and accepted support mask can be encoded without freehand interpretation; the ERT spatial projection and support-sensitivity audits can be regenerated with no provisional-transform caveat.; The ERT likelihood can assign defensible row/group weights without treating dense VTK cells as independent observations.
- Response/intake location: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_transform_support_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/ert/source_files/provider_responses/ert_uncertainty_response_notes.md
- Next action: review_send_gmail_draft_then_file_provider_response_in_intake_dir

Preview:

```text
# Draft: CD-A ERT transform, support, and uncertainty needed for OGS comparison

Subject: CD-A ERT transform, support, and uncertainty needed for OGS comparison
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: Markus.Furche@bgr.de
Contact route: coordinator_with_named_provider_cc
Contact evidence: Gesa is the main CD-A sender; Markus.Furche@bgr.de is found in ERT and meeting-related messages and Gesa relayed Markus' ERT explanation in Gmail message 1994cb5d2bcefa24.
Contact caveat: No direct Gmail sender messages from Markus were found in the scan, so the request is routed through Gesa with Markus as suggested CC.

Dear Gesa, Markus,

We can already run a provisional ERT diagnostic against sampled OGS water-content outputs, but it should not become an inversion residual until the coordinate support and uncertainty model are confirmed.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `ert_transform_support`
```

### `r1284411814726937591`

- Subject: CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation
- To: Gesa.Ziefle@bgr.de
- Cc: none
- Local draft file(s): inversion_workflow/external_gate_requests/bgr_other_hm_exports_via_gesa_ziefle.md
- Request ids: hm_numeric_exports,hm_uncertainty
- Current blocker: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.; Required metadata for hard HM residual weights are absent from the current local bundle.
- Acceptance evidence: The other-HM source audit finds at least one hard-residual-ready numeric request class with time/epoch and model-facing support.; Each candidate other-HM residual has enough metadata to state which OGS quantity/support it measures and what residual weight it receives.
- Response/intake location: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_numeric_exports_response_notes.md; /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/other_hm_monitoring/source_files/provider_responses/hm_uncertainty_response_notes.md
- Next action: review_send_gmail_draft_then_file_provider_response_in_intake_dir

Preview:

```text
# Draft: CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation

Subject: CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: none
Contact route: coordinator_only_specific_provider_unresolved
Contact evidence: Gesa is the main CD-A sender and sent the April 2026 technical-discussion minutes/presentations in Gmail message 19e1688564149e24; the current local scan does not identify a direct Geoscope, laser-scan, or levelling data owner address.
Contact caveat: Ask Gesa to forward to the appropriate BGR Geoscope, laser-scan, and levelling data owners if she is not the source.

Dear Gesa,

The local catalogue contains HM layout geometry and qualitative evidence, but no hard-residual-ready numeric time series or statistical exports for these streams.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `hm_numeric_exports`
```

### `r-8461584324877432346`

- Subject: CD-A RH/suction boundary-curve provenance needed for OGS forcing
- To: Gesa.Ziefle@bgr.de
- Cc: none
- Local draft file(s): inversion_workflow/external_gate_requests/bgr_rh_boundary_curve_provenance_via_gesa_ziefle.md
- Request ids: rh_active_curve_provenance
- Current blocker: Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.
- Acceptance evidence: The active XML pressure curve can be regenerated or explained well enough that replacement curves/retention targets are no longer based on unknown provenance.
- Response/intake location: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/provider_responses/rh_active_curve_provenance_response_notes.md
- Next action: review_send_gmail_draft_then_file_provider_response_in_intake_dir

Preview:

```text
# Draft: CD-A RH/suction boundary-curve provenance needed for OGS forcing

Subject: CD-A RH/suction boundary-curve provenance needed for OGS forcing
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: none
Contact route: coordinator_only_processing_owner_unresolved
Contact evidence: Gesa sent the CD-A modelling slides, RH/suction material, and model-transfer threads that define the active boundary-curve context.
Contact caveat: The scan does not identify a separate RH/OGS pressure-curve processing owner, so Gesa remains the routing contact.

Dear Gesa,

The local RH-derived pressure curves do not reproduce the active XML pressure boundary, so we need the source/provenance before using RH as anything stronger than a boundary audit.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `rh_active_curve_provenance`
```

### `r-4809950961900799564`

- Subject: CD-A Taupe/TDR workbook units and calibration needed before objective activation
- To: Gesa.Ziefle@bgr.de
- Cc: none
- Local draft file(s): inversion_workflow/external_gate_requests/taupe_tdr_calibration_via_gesa_ziefle.md
- Request ids: taupe_unit_calibration
- Current blocker: Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.
- Acceptance evidence: The Taupe semantics audit can decide whether absolute Taupe values are water content, permittivity/proxy, or trend-only evidence.
- Response/intake location: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/taupe_tdr/source_files/provider_responses/taupe_unit_calibration_response_notes.md
- Next action: review_send_gmail_draft_then_file_provider_response_in_intake_dir

Preview:

```text
# Draft: CD-A Taupe/TDR workbook units and calibration needed before objective activation

Subject: CD-A Taupe/TDR workbook units and calibration needed before objective activation
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: none
Contact route: coordinator_only_provider_unresolved
Contact evidence: Gesa's 2025-11-07 measurement overview says the TeamBeam transfer includes Taupe data and context, but the current scan does not identify a direct Taupe/TDR provider address.
Contact caveat: Ask Gesa to forward to the Taupe/TDR provider or confirm the unit/calibration source directly.

Dear Gesa,

We can compare Taupe/TDR temporal trends diagnostically, but the workbook values need unit and calibration confirmation before any absolute water-content or saturation residual.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `taupe_unit_calibration`
```

### `r-4984596174110032107`

- Subject: CD-A historical permeability endpoint geometry needed for inactive intervals
- To: Gesa.Ziefle@bgr.de
- Cc: none
- Local draft file(s): inversion_workflow/external_gate_requests/bgr_historical_permeability_geometry_via_gesa_ziefle.md
- Request ids: perm_endpoint_geometry
- Current blocker: Historical permeability endpoints are needed only if these older rows should enter the fit.
- Acceptance evidence: Inactive historical rows can be projected to OGS cells with a trace/support definition rather than excluded for missing geometry.
- Response/intake location: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/provider_responses/perm_endpoint_geometry_response_notes.md
- Next action: review_send_gmail_draft_then_file_provider_response_in_intake_dir

Preview:

```text
# Draft: CD-A historical permeability endpoint geometry needed for inactive intervals

Subject: CD-A historical permeability endpoint geometry needed for inactive intervals
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: none
Contact route: coordinator_only_source_owner_unresolved
Contact evidence: Gesa sent permeability spreadsheets, characterization material, and the later updated permeability transfer; the local scan does not identify a direct historical pulse-test geometry owner address.
Contact caveat: Ask Gesa to forward to the BGR permeability data owner if labelled interval endpoints come from another source.

Dear Gesa,

The current direct permeability objective uses only rows with mapped interval support. The older retained rows need endpoint geometry before they can be projected to OGS cells.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `perm_endpoint_geometry`
```

### `r2947727639429158073`

- Subject: CD-A OGS CTE value/provenance confirmation needed before thermal-parameter interpretation
- To: Gesa.Ziefle@bgr.de
- Cc: Tuanny.Cajuhi@bgr.de
- Local draft file(s): inversion_workflow/cte_confirmation_request.md
- Request ids: cte_value_confirmation
- Current blocker: The XML binds CTE to solid thermal_expansivity, but the value and comment look like a copied heat-capacity entry. The model must remain frozen, so this needs provenance confirmation rather than a local correction.
- Acceptance evidence: The CTE row in the report open-comment audit can move from open_confirmation_required to confirmed_inactive, confirmed_typo_not_changed, or confirmed_value_recorded with the provider response cited.
- Response/intake location: inversion_workflow/cte_confirmation_request.md
- Next action: review_send_cte_confirmation_draft_then_record_provider_response

Preview:

```text
# CTE Confirmation Request

This request packages the suspicious CD-A OGS `CTE` value as a model-provenance confirmation item.
It does not modify the frozen GESA model and does not claim that the value has been confirmed.

## Summary

- Status: `cte_confirmation_gmail_draft_created_waiting_user_send_and_response`
- Request id: `cte_value_confirmation`
- Suggested To: `Gesa.Ziefle@bgr.de`
- Suggested Cc: `Tuanny.Cajuhi@bgr.de`
- Contact route: `coordinator_with_model_setup_cc`
- Request status: `drafted_pending_send`
- Response status: `no_response_recorded`
- Gmail draft id: `r2947727639429158073`
- Gmail send status: `gmail_draft_created_not_sent`
```

## Source Artifacts

- `inversion_workflow/external_gate_gmail_drafts.csv`
- `inversion_workflow/cte_confirmation_gmail_draft.csv`
- `inversion_workflow/external_blocker_dashboard.csv`
- `inversion_workflow/external_gate_dispatch_audit.csv`
- `inversion_workflow/gmail_gate_live_state_audit_summary.json`
- `inversion_workflow/final_inversion_closeout_playbook.md`
