# Report Open Comment Audit

This audit separates active LaTeX review markers from resolved formulation comments and
tracked provenance/calibration gates.

- Status: `report_open_comment_audit_generated`
- Active report unresolved marker count: 0
- Resolved formulation comments: 5
- Tracked external gate requests: 7
- Tracked internal/provenance/operational items: 4
- False-positive search hits classified: 4
- External request pack status: `external_gate_request_pack_generated_not_sent`
- External intake status: `external_gate_response_intake_generated_waiting_for_responses` with 7 missing responses
- CTE confirmation request status: `cte_confirmation_gmail_draft_created_waiting_user_send_and_response` (drafted_pending_send; no_response_recorded)

No TODO/FIXME/??/LaTeX todo/highlight/color review markers were found in main.tex or measurement_chapter.tex.

## Audit Rows

| Item | Class | Status | Location | Summary | Remaining action |
| --- | --- | --- | --- | --- | --- |
| `homogeneity_vs_heterogeneity` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex:97 | The report now distinguishes the homogeneous exchanged XML model from run-local heterogeneous permeability fields. | None for formulation; keep the distinction if report text is edited. |
| `relative_permeability_expression` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex:103 | The report now states the actual Van Genuchten relative-permeability function and fixed XML parameters. | None for formulation; keep the distinction if report text is edited. |
| `liquid_density_beta_storage` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex:174 | The report now explains the OGS liquid-density pressure/temperature dependence and composite storage term. | None for formulation; keep the distinction if report text is edited. |
| `momentum_bishop_thermal_strain` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex:200 | The report now states the configured Bishop law, Biot coefficient, and thermal strain placement. | None for formulation; keep the distinction if report text is edited. |
| `heat_balance_porosity_saturation` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex:221 | The report now explains where porosity and saturation enter thermal storage/conductivity mixing. | None for formulation; keep the distinction if report text is edited. |
| `ert_transform_support` | `tracked_external_gate_request` | `drafted_pending_send; no_response_recorded` | measurement_chapter.tex:355 | coordinate transform and exact support mask confirmed | send_request_and_record_response_artifacts |
| `ert_uncertainty` | `tracked_external_gate_request` | `drafted_pending_send; no_response_recorded` | measurement_chapter.tex:356 | inversion-field uncertainty/correlation model assigned | send_request_and_record_response_artifacts |
| `hm_numeric_exports` | `tracked_external_gate_request` | `drafted_pending_send; no_response_recorded` | measurement_chapter.tex:1307 | hard-residual-ready numeric time series located | send_request_and_record_response_artifacts |
| `hm_uncertainty` | `tracked_external_gate_request` | `drafted_pending_send; no_response_recorded` | measurement_chapter.tex:1307 | units, epochs, reference conventions, uncertainty, and quality flags available | send_request_and_record_response_artifacts |
| `rh_active_curve_provenance` | `tracked_external_gate_request` | `drafted_pending_send; no_response_recorded` | measurement_chapter.tex:1271 | active OGS pressure curve provenance confirmed | send_request_and_record_response_artifacts |
| `taupe_unit_calibration` | `tracked_external_gate_request` | `drafted_pending_send; no_response_recorded` | measurement_chapter.tex:1306 | Taupe workbook unit and absolute calibration confirmed | send_request_and_record_response_artifacts |
| `perm_endpoint_geometry` | `tracked_external_gate_request` | `drafted_pending_send; no_response_recorded` | measurement_chapter.tex:1324 | missing historical endpoint geometry for inactive permeability rows | send_request_and_record_response_artifacts |
| `cte_value_provenance` | `tracked_model_provenance_confirmation` | `drafted_pending_send; no_response_recorded` | main.tex:111 | The active CTE value is tracked as an implausible thermal-expansivity/provenance issue, not as a fit parameter. | Send the CTE confirmation request and record the provider response before releasing thermal or retention/boundary parameters. |
| `nmr_trend_anomaly_default_promotion` | `tracked_internal_policy` | `local_policy_recorded_not_promoted_default` | main.tex; measurement_chapter.tex; WORK_STATUS.md; inversion_workflow/README.md | The NMR trend/anomaly residual is implemented and preferred provisionally; local policy keeps it explicit/scenario-only for the current report state. | No current-report action; re-open only if the modelling team wants to change the default objective semantics. |
| `perm_likelihood_policy_default` | `tracked_internal_policy` | `local_policy_recorded_not_promoted_default` | measurement_chapter.tex:1667 | The direct-permeability robust/support-cell likelihood choice is explicit and not promoted as a silent default change. | Before more active-objective OGS spending, record whether the rowwise Gaussian policy remains accepted with a new parameterization or whether a robust/aggregated likelihood scenario should become the active selection policy. |
| `local_ogs_runtime_provenance` | `tracked_operational_caveat` | `container_execution_available_local_ogs_absent` | measurement_chapter.tex:1188 | The local host lacks a native ogs executable, while the collected SIF is executable through Dockerized Apptainer. | Keep the backend recorded for reproducibility; install native OGS only if the workflow requires it. |
| `latex_listing_commentstyle` | `false_positive_search_hit` | `not_active_report_comment` | main.tex:36 | The LaTeX listings style contains the word commentstyle; it is not a reviewer comment. | No report action. |
| `work_status_placeholder_scan_note` | `false_positive_search_hit` | `not_active_report_comment` | WORK_STATUS.md:492 | WORK_STATUS records that placeholder markers were checked; it is not itself an unresolved placeholder. | No report action. |
| `source_text_todos_external_content` | `false_positive_search_hit` | `not_active_report_comment` | inversion_workflow/processed_observations/other_hm_numeric_source_evidence.csv:81 | The remaining TODO-like text is source/extracted-content vocabulary outside the active report. | No report action. |
| `legacy_long_report_not_build_target` | `false_positive_search_hit` | `not_active_report_comment` | main.tex; WORK_STATUS.md; long_report.tex; inversion_workflow/processed_observations/other_hm_numeric_source_evidence.csv | long_report.tex is a legacy/source file; main.tex builds the active report and only inputs measurement_chapter.tex. | No report action. |

## Interpretation

The active report has no literal TODO/FIXME/??/todo/highlight/color review markers.
The earlier equation-formulation comments are resolved in the active text. The remaining
issues are tracked model-provenance, observation-operator, uncertainty, calibration, and
response-intake gates, so they should stay in the readiness audit instead of being treated
as unresolved LaTeX comments.
