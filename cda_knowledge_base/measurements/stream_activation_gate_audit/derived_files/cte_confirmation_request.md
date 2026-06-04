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

## Draft

Subject: CD-A OGS CTE value/provenance confirmation needed before thermal-parameter interpretation
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: Tuanny.Cajuhi@bgr.de
Contact route: coordinator_with_model_setup_cc
Contact evidence: Gesa is the main CD-A coordination sender; Tuanny Cajuhi sent direct model-setup messages and discussed OGS support for distributed fields.

Dear Gesa, Tuanny,

While checking the recovered CD-A OGS XML against the report text, I found a thermal-expansivity provenance issue that should be confirmed before it is interpreted physically.

Request: Please confirm whether the XML parameter CTE=1254.74 in the CD-A OGS model is intended to be a solid linear thermal-expansivity value in 1/K, a mistaken copy of the solid heat capacity c_p_s, an inactive/irrelevant parameter in the intended run, or a value with another unit/convention.

Current local evidence/blocker: The active audit reads CTE=1254.74, c_p_s=1254.74, CTE equals c_p_s=True, bound property=Solid:thermal_expansivity:Parameter, expected unit=1/K, and CTE/reference-high ratio=48259230.769230776. The XML binds CTE to solid thermal_expansivity, but the value and comment look like a copied heat-capacity entry. The model must remain frozen, so this needs provenance confirmation rather than a local correction.

Minimum acceptance criteria: Written confirmation of the intended CTE meaning, unit, active/inactive status in the shared TRM setup, and the value that should be cited if the report discusses thermal expansivity or later releases thermal/retention/boundary parameters.

Why this matters: The current inversion keeps thermal parameters fixed, but the report must not physically interpret CTE or release thermal/retention/boundary parameters while this XML value is unconfirmed.

Local artifacts we can share if useful: inversion_workflow/thermal_expansivity_parameter_audit.md; inversion_workflow/runs/direct_fit_observation_run/03_parameters_TRM.xml; inversion_workflow/runs/direct_fit_observation_run/04_media_TRM.xml

Best,

## Tracking Row

| Field | Value |
| --- | --- |
| `request_id` | cte_value_confirmation |
| `priority` | high |
| `issue_type` | model_provenance_confirmation |
| `subject` | CD-A OGS CTE value/provenance confirmation needed before thermal-parameter interpretation |
| `suggested_to` | Gesa.Ziefle@bgr.de |
| `suggested_cc` | Tuanny.Cajuhi@bgr.de |
| `contact_route_status` | coordinator_with_model_setup_cc |
| `contact_evidence` | Gesa is the main CD-A coordination sender; Tuanny Cajuhi sent direct model-setup messages and discussed OGS support for distributed fields. |
| `request_status` | drafted_pending_send |
| `response_status` | no_response_recorded |
| `current_evidence` | The active audit reads CTE=1254.74, c_p_s=1254.74, CTE equals c_p_s=True, bound property=Solid:thermal_expansivity:Parameter, expected unit=1/K, and CTE/reference-high ratio=48259230.769230776. |
| `current_blocker` | The XML binds CTE to solid thermal_expansivity, but the value and comment look like a copied heat-capacity entry. The model must remain frozen, so this needs provenance confirmation rather than a local correction. |
| `exact_request` | Please confirm whether the XML parameter CTE=1254.74 in the CD-A OGS model is intended to be a solid linear thermal-expansivity value in 1/K, a mistaken copy of the solid heat capacity c_p_s, an inactive/irrelevant parameter in the intended run, or a value with another unit/convention. |
| `minimum_acceptance_criteria` | Written confirmation of the intended CTE meaning, unit, active/inactive status in the shared TRM setup, and the value that should be cited if the report discusses thermal expansivity or later releases thermal/retention/boundary parameters. |
| `why_needed_for_model` | The current inversion keeps thermal parameters fixed, but the report must not physically interpret CTE or release thermal/retention/boundary parameters while this XML value is unconfirmed. |
| `would_unlock` | A closed model-provenance note for the SOTA report and a clear release-gate decision for thermal expansivity. |
| `local_artifacts` | inversion_workflow/thermal_expansivity_parameter_audit.md; inversion_workflow/runs/direct_fit_observation_run/03_parameters_TRM.xml; inversion_workflow/runs/direct_fit_observation_run/04_media_TRM.xml |
| `acceptance_test` | The CTE row in the report open-comment audit can move from open_confirmation_required to confirmed_inactive, confirmed_typo_not_changed, or confirmed_value_recorded with the provider response cited. |
| `next_action` | send_confirmation_request_and_record_provider_response |