# Report Open Comment Audit

This audit separates active LaTeX review markers from resolved formulation comments and
tracked provenance/calibration gates.

- Status: `report_open_comment_audit_generated`
- Active report unresolved marker count: 0
- Resolved formulation comments: 5
- Tracked external gate requests: 0
- Tracked internal/provenance/operational items: 4
- False-positive search hits classified: 4
- External request pack status: `None`
- External intake status: `None` with None missing responses
- CTE confirmation request status: `None` (None; None)

No TODO/FIXME/??/LaTeX todo/highlight/color review markers were found in main.tex or measurement_chapter.tex.

## Audit Rows

| Item | Class | Status | Location | Summary | Remaining action |
| --- | --- | --- | --- | --- | --- |
| `homogeneity_vs_heterogeneity` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex | The report now distinguishes the homogeneous exchanged XML model from run-local heterogeneous permeability fields. | None for formulation; keep the distinction if report text is edited. |
| `relative_permeability_expression` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex | The report now states the actual Van Genuchten relative-permeability function and fixed XML parameters. | None for formulation; keep the distinction if report text is edited. |
| `liquid_density_beta_storage` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex | The report now explains the OGS liquid-density pressure/temperature dependence and composite storage term. | None for formulation; keep the distinction if report text is edited. |
| `momentum_bishop_thermal_strain` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex | The report now states the configured Bishop law, Biot coefficient, and thermal strain placement. | None for formulation; keep the distinction if report text is edited. |
| `heat_balance_porosity_saturation` | `resolved_formulation_comment` | `resolved_in_active_report` | main.tex | The report now explains where porosity and saturation enter thermal storage/conductivity mixing. | None for formulation; keep the distinction if report text is edited. |
| `cte_value_provenance` | `tracked_model_provenance_confirmation` | `open_confirmation_required` | main.tex; measurement_chapter.tex; WORK_STATUS.md; inversion_workflow/README.md | The active CTE value is tracked as an implausible thermal-expansivity/provenance issue, not as a fit parameter. | Send the CTE confirmation request and record the provider response before releasing thermal or retention/boundary parameters. |
| `nmr_trend_anomaly_default_promotion` | `tracked_internal_policy` | `local_policy_recorded_not_promoted_default` | main.tex; measurement_chapter.tex; WORK_STATUS.md; inversion_workflow/README.md | The NMR trend/anomaly residual is implemented and preferred provisionally; local policy keeps it explicit/scenario-only for the current report state. | No current-report action; re-open only if the modelling team wants to change the default objective semantics. |
| `perm_likelihood_policy_default` | `tracked_internal_policy` | `local_policy_recorded_not_promoted_default` | main.tex; measurement_chapter.tex; WORK_STATUS.md; inversion_workflow/README.md | The direct-permeability robust/support-cell likelihood choice is explicit and not promoted as a silent default change. | Before more active-objective OGS spending, record whether the rowwise Gaussian policy remains accepted with a new parameterization or whether a robust/aggregated likelihood scenario should become the active selection policy. |
| `local_ogs_runtime_provenance` | `tracked_operational_caveat` | `container_execution_available_local_ogs_absent` | main.tex; measurement_chapter.tex; WORK_STATUS.md; inversion_workflow/README.md | The local host lacks a native ogs executable, while the collected SIF is executable through Dockerized Apptainer. | Keep the backend recorded for reproducibility; install native OGS only if the workflow requires it. |
| `latex_listing_commentstyle` | `false_positive_search_hit` | `not_active_report_comment` | main.tex; WORK_STATUS.md; long_report.tex; inversion_workflow/processed_observations/other_hm_numeric_source_evidence.csv | The LaTeX listings style contains the word commentstyle; it is not a reviewer comment. | No report action. |
| `work_status_placeholder_scan_note` | `false_positive_search_hit` | `not_active_report_comment` | main.tex; WORK_STATUS.md; long_report.tex; inversion_workflow/processed_observations/other_hm_numeric_source_evidence.csv | WORK_STATUS records that placeholder markers were checked; it is not itself an unresolved placeholder. | No report action. |
| `source_text_todos_external_content` | `false_positive_search_hit` | `not_active_report_comment` | main.tex; WORK_STATUS.md; long_report.tex; inversion_workflow/processed_observations/other_hm_numeric_source_evidence.csv | The remaining TODO-like text is source/extracted-content vocabulary outside the active report. | No report action. |
| `legacy_long_report_not_build_target` | `false_positive_search_hit` | `not_active_report_comment` | main.tex; WORK_STATUS.md; long_report.tex; inversion_workflow/processed_observations/other_hm_numeric_source_evidence.csv | long_report.tex is a legacy/source file; main.tex builds the active report and only inputs measurement_chapter.tex. | No report action. |

## Interpretation

The active report has no literal TODO/FIXME/??/todo/highlight/color review markers.
The earlier equation-formulation comments are resolved in the active text. The remaining
issues are tracked model-provenance, observation-operator, uncertainty, calibration, and
response-intake gates, so they should stay in the readiness audit instead of being treated
as unresolved LaTeX comments.
