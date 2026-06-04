# Inversion Workflow Prototype

This folder contains local workflow material for using the frozen CD-A OGS model with
heterogeneous permeability fields.  It does not change the governing equations or the
meaning of the exchanged model.  It only prepares mesh-cell parameter fields that can
be referenced by the existing OGS `MeshElement` parameter mechanism.

## Fast Paths

| Need | Use |
| --- | --- |
| Raw/source measurement files | [measurements/README.md](../../cda_knowledge_base/measurements/README.md) |
| Per-stream source provenance and mirror inventories | [measurements_info/README.md](../../cda_knowledge_base/measurements_info/README.md) |
| Normalized processed CSV observations | [processed_observations/README.md](processed_observations/README.md) |
| Current model-entry and allowed-use status | [measurement_model_entry_matrix.md](measurement_model_entry_matrix.md) |
| Strict activation blockers | [measurement_stream_activation_gate_audit.md](measurement_stream_activation_gate_audit.md) |
| Open questions across report/source/gate/final decisions | [open_questions_resolution_matrix.md](../../cda_knowledge_base/open_questions_resolution_matrix.md) |
| Current report wording | [chapter_02_measurements.tex](../../mont_terri_questions_rewrite/paper/sections/chapter_02_measurements.tex) |
| Literature/citation coverage | [Library README](../Library/README.md) and [citation_locator_audit.md](../Library/citation_locator_audit.md) |

It also contains a machine-checkable observation manifest and likelihood/activation
model for the local measurement catalogue.  Those files are the bridge between the
report's measurement discussion and future inversion code: they record which local
files are expected for each observation class, which model quantity they should
constrain, and which streams are defensible active residuals now.

The per-measurement model-entry matrix joins coverage, residual semantics,
activation gates, and final include/exclude status for the nine catalogue classes:

- `scripts/build_measurement_model_entry_matrix.py`
- `measurement_model_entry_matrix.csv`
- `measurement_model_entry_matrix_summary.json`
- `measurement_model_entry_matrix.md`

The stream activation-gate audit is the strict blocker list for turning diagnostics
into hard residuals:

- `scripts/build_measurement_stream_gate_audit.py`
- `measurement_stream_activation_gate_audit.csv`
- `measurement_stream_activation_gate_checks.csv`
- `measurement_stream_activation_gate_audit_summary.json`
- `measurement_stream_activation_gate_audit.md`

The follow-on closure package turns that blocker list into actionable collaborator
requests and internal modelling decisions:

- `scripts/build_measurement_gate_closure_request.py`
- `measurement_gate_closure_request.csv`
- `measurement_gate_closure_request_summary.json`
- `measurement_gate_closure_request.md`
- `measurement_gate_closure_email_draft.md`

The external request pack turns the external closure rows into recipient-specific
drafts, contact-routing fields, and a tracking table:

- `scripts/build_external_gate_request_pack.py`
- `external_gate_request_pack.csv`
- `external_gate_request_pack_summary.json`
- `external_gate_request_pack.md`
- `external_gate_requests/`

The response-intake tracker says where external replies/files should be filed and
which audits to refresh after each answer arrives:

- `scripts/build_external_gate_response_intake.py`
- `external_gate_response_intake.csv`
- `external_gate_response_intake_summary.json`
- `external_gate_response_intake.md`

The dispatch-readiness audit checks that the request-pack rows, recipient drafts,
response-intake rows, acceptance tests, refresh commands, and response-note
templates match before the emails are sent:

- `scripts/build_external_gate_dispatch_audit.py`
- `external_gate_dispatch_audit.csv`
- `external_gate_dispatch_audit_summary.json`
- `external_gate_dispatch_audit.md`

The Gmail live-state audit records point-in-time connector checks for the external
gate drafts and the CTE confirmation draft:

- `scripts/build_gmail_gate_live_state_audit.py`
- `gmail_gate_live_state_observations.csv`
- `gmail_gate_live_state_audit_summary.json`
- `gmail_gate_live_state_audit.md`

The external blocker dashboard joins the external request/intake/dispatch trackers,
the Gmail live-state audit, the local/Downloads recovery scans, and the separate CTE
confirmation request into one send/response worklist:

- `scripts/build_external_blocker_dashboard.py`
- `external_blocker_dashboard.csv`
- `external_blocker_dashboard_summary.json`
- `external_blocker_dashboard.md`

The local gate recovery audit rescans collected source files, ZIP/workbook/PDF
extracted text, and source indexes for local evidence that could close the failed
external gates before relying on provider requests:

- `scripts/build_local_gate_recovery_audit.py`
- `local_gate_recovery_audit.csv`
- `local_gate_recovery_audit_summary.json`
- `local_gate_recovery_audit.md`

The Downloads recovery audit applies the same gate checks to raw
`/home/ber0061/Downloads` files without promoting them into the curated catalogue.
It records verified duplicate TeamBeam/catalogue files, candidate raw-download
context, and extracted/run-output folders:

- `scripts/build_download_gate_recovery_audit.py`
- `download_gate_recovery_audit.csv`
- `download_gate_recovery_inventory.csv`
- `download_gate_recovery_audit_summary.json`
- `download_gate_recovery_audit.md`

The internal decision register records the local policies for seven internal or
internal-with-optional-confirmation items, including the separate NMR
not-promoted-default policy for the current report state:

- `scripts/build_internal_gate_decision_register.py`
- `internal_gate_decision_register.csv`
- `internal_gate_decision_register_summary.json`
- `internal_gate_decision_register.md`

The report open-comment audit separates active LaTeX review markers from resolved
formulation comments and tracked provenance/calibration gates:

- `scripts/build_report_open_comment_audit.py`
- `report_open_comment_audit.csv`
- `report_open_comment_audit_summary.json`
- `report_open_comment_audit.md`

The OGS formulation consistency audit parses the source XML and the representative
run-local XML so the report's formulation statements are machine-checkable:

- `scripts/build_ogs_formulation_consistency_audit.py`
- `ogs_formulation_consistency_audit.csv`
- `ogs_formulation_xml_inventory.csv`
- `ogs_formulation_consistency_audit_summary.json`
- `ogs_formulation_consistency_audit.md`

The citation locator audit in the report library checks that every active report
citation is directly checkable:

- `scripts/build_citation_locator_audit.py`
- `../Library/citation_locator_audit.csv`
- `../Library/citation_locator_audit_summary.json`
- `../Library/citation_locator_audit.md`

The measurement-report traceability audit checks that every manifest observation
group is represented from catalogue files through the report chapter and workflow
artifacts:

- `scripts/build_measurement_report_traceability_audit.py`
- `measurement_report_traceability_audit.csv`
- `measurement_report_traceability_audit_summary.json`
- `measurement_report_traceability_audit.md`

The permeability support lower-bound audit tests whether the remaining direct
pulse-test loss can still be reduced by any field that keeps the current
observation-to-support-cell map:

- `scripts/build_permeability_support_lower_bound_audit.py`
- `permeability_support_lower_bound_audit.csv`
- `permeability_support_lower_bound_row_audit.csv`
- `permeability_support_lower_bound_audit_summary.json`
- `permeability_support_lower_bound_audit.md`

Current result:

```text
streams audited: 8
gate checks: 20
active objective rows: 267
required failed gates: 7
closure requests: 13
external requests: 7
external recipient drafts: 5
external recipients with suggested To: 5/5
external recipients with suggested Cc: 1/5
external missing responses: 7
external dispatch-ready requests: 7/7
external dispatch failed checks: 0
Gmail live-state expected drafts observed: 6/6
Gmail live-state sent-subject hits: 0
Gmail live-state provider-reply hits: 0
external blocker dashboard blockers: 8
external blocker dashboard open blockers: 8
external blocker dashboard unsent blockers: 8
external blocker dashboard missing responses: 8
local gate recovery documents rescanned: 2540
local gate recovery possible gate-closing rows: 0
local gate recovery gates still external: 7
Downloads recovery documents scanned: 533
Downloads recovery possible gate-closing rows: 0
Downloads recovery verified duplicate/catalogue rows: 25
Downloads recovery uncatalogued extracted/run-output dirs: 1
CTE confirmation request: Gmail draft created, not sent
internal decisions: 7
internal policies recorded: 7
active report review markers: 0
resolved formulation comments: 5
OGS formulation consistency checks: 18, hard failures: 0
OGS formulation tracked caveats: 2
report-tracked external gates: 7
citation key instances: 63
missing or weak citation locators: 0
missing cited BibTeX entries: 0
unavailable cited fulltexts missing from log: 0
citation fulltext statuses: 56 local, 5 official web docs, 2 unavailable tracked
measurement-report traceable observations: 9/9
measurement-report missing chapter sections: 0
measurement-report missing model-entry statements: 0
measurement-report missing expected artifacts: 0
current field selection active decision: accept_as_current_active_objective_incumbent
current field selection final decision: do_not_promote_to_final_all_measurement_field
current field selection blocked/gated criteria: 4
permeability support lower-bound current objective: 269.818057
permeability support lower-bound objective: 269.818057
permeability same-support reducible gap: 0
permeability support groups with observed range >=2 log10: 16
conditional field scenarios: 8 scenarios, 5 unique winners, current field wins 1
conditional field candidate packages: 5 copied scenario-winning meshes
conditional field differences: 4 fields compared to current, max mean abs delta
  log10 k=0.0377448, max cells >0.10 log10=233
promotion decisions: active_with_tracked_caveats=2, diagnostic_only=2,
  boundary_audit_only=1, not_ready_for_hard_residual=1, support_layer_ready=2
```

Direct permeability and NMR are active with caveats.  ERT and Taupe/TDR remain
diagnostic-only, RH remains boundary-audit-only, and other HM monitoring remains
outside hard residual weighting until the missing numeric exports and metadata are
available.  The closure package is the current send/check list for those blockers:
ERT transform/support and covariance, Taupe unit calibration and grouping, RH active
curve provenance and uncertainty policy, other-HM numeric exports/metadata, NMR
bound-water handling, permeability gas-pulse error policy, and optional historical
permeability endpoint geometry.

The external request pack currently has status
`external_gate_request_pack_generated_not_sent`, and the dispatch layer has created
Gmail drafts for it.  The five Gmail drafts cover all seven external rows: ERT
transform/support plus covariance, other-HM numeric exports plus metadata, RH
boundary-curve provenance, Taupe/TDR calibration, and historical permeability
endpoint geometry. Suggested `To` routes are present for all five recipient drafts.
The ERT draft routes through `Gesa.Ziefle@bgr.de` with `Markus.Furche@bgr.de` as
suggested CC because the mailbox scan found Markus as the named ERT contact but
found no direct sender messages from him; the other four drafts route through Gesa
with explicit caveats asking her to forward to the appropriate provider if needed.

The response-intake tracker currently has status
`external_gate_response_intake_generated_waiting_for_responses`. It creates
provider-response directories under the affected stream catalogues
(`ert`, `other_hm_monitoring`, `suction_relative_humidity`, `taupe_tdr`, and
`permeability_pulse_tests`) and records the acceptance tests plus regeneration
commands needed after each answer arrives. It also creates one response-note
template per external request, without overwriting those notes after they are filled.

The dispatch-readiness audit currently has status
`external_gate_dispatch_gmail_drafts_created_waiting_user_send_and_responses`. It
verifies that all seven request rows are represented in the five drafts, that every
intake row has an acceptance test and refresh command, and that all seven
response-note templates exist. It records suggested `To` routes for all seven
request rows, suggested `Cc` routes for the two ERT rows, and zero failed dispatch
checks. The Gmail drafts are created but not sent, and all seven responses remain
missing.

The external blocker dashboard currently has status
`external_blocker_dashboard_generated_waiting_user_send_and_responses`. It records
eight open rows: seven external measurement-gate blockers plus the separate CTE
confirmation row. All eight are still unsent/missing-response blockers, all six
expected Gmail drafts were observed by the live-state audit, and local/Downloads
recovery scans found zero gate-closing evidence rows.

The internal register records these local policies: NMR should use the implemented
within-label trend/anomaly residual as the preferred provisional likelihood while
raw absolute-theta remains conditional; direct gas-pulse permeability stays active
as log10 intrinsic permeability with broad 0.5-log10 sigma and explicit gas/slip
caveats; RH remains boundary/provenance evidence only; Taupe/TDR grouping should use
grouped weights if later activated; and current Taupe/TDR support is limited to the
mapped A3/A4 Niche-4 support.  These policies do not close the external ERT, RH,
Taupe calibration, other-HM, or historical permeability source requests.

The report open-comment audit currently records zero active `TODO`/`FIXME`/`??` or
LaTeX todo/highlight/color review markers in `main.tex` and
`measurement_chapter.tex`. It classifies five earlier formulation comments as
resolved in the active report and keeps the remaining CTE, ERT, Taupe/TDR, RH,
other-HM, historical permeability, and NMR-default questions as tracked gates rather
than unresolved report comments.

The open-question resolution matrix in `open_question_resolution_matrix.md`
connects those tracked gates back to `cda_knowledge_base/open_questions.md`,
source/citation coverage, Gmail draft state, and the final-promotion trackers. It
currently records 23 rows: 6 locally resolved/current-scope rows, 9 external
send/response rows, 6 internal policy/final-decision rows, 1 tracked current-policy
caveat, and 1 deferred time-dependency row.  The added final-promotion row makes the
conservative no-new-evidence closeout decision explicit rather than treating the
draft packet as approval.

The measurement-report traceability audit currently passes all nine manifest
observation groups. It confirms that every group has a catalogue folder and README,
passes manifest validation, has a report inventory-table reference and subsection
coverage, has model-entry wording in the chapter, and has the expected workflow
artifacts. This is a traceability result, not activation: ERT, Taupe/TDR, RH, and
other-HM still remain gated by the likelihood and external-response audits.

The NMR bound/interlayer-water caveat now has a provisional decision package:

- `scripts/build_nmr_objective_decision.py`
- `nmr_objective_decision.csv`
- `nmr_objective_decision_summary.json`
- `nmr_objective_decision.md`

It recommends using within-label trend/anomaly NMR residuals as the first
provisional final NMR likelihood while keeping the current raw absolute-theta
objective conditional.  The executable path is now implemented as an explicit
assembler mode and separately ranked without overwriting the historical objective:

- `scripts/build_nmr_trend_anomaly_active_objective_ranking.py`
- `nmr_trend_anomaly_active_objective_ranking.csv`
- `nmr_trend_anomaly_active_objective_summary.json`
- `nmr_trend_anomaly_active_objective.md`
- `scripts/build_nmr_final_residual_policy_gate.py`
- `nmr_final_residual_policy_gate.csv`
- `nmr_final_residual_policy_gate_summary.json`
- `nmr_final_residual_policy_gate.md`
- `scripts/build_nmr_final_residual_policy_acceptance_template.py`
- `nmr_final_residual_policy_acceptance_record_template.csv`
- `nmr_final_residual_policy_acceptance_record_template_summary.json`
- `nmr_final_residual_policy_acceptance_record_template.md`

Use `--state-objective-mode nmr_within_label_trend_anomaly` with
`assemble_inversion_objective.py` or `evaluate_inversion_candidate.py` to exercise
that residual for future runs.  The internal decision register records the current
local policy: do not promote this mode to the default objective for the present
report state.  The default active objective therefore remains raw absolute-theta,
and trend/anomaly NMR is used only as explicit scenario/provisional likelihood
evidence unless the modelling team reopens that decision.

The final residual-policy gate in `nmr_final_residual_policy_gate.md` makes that
promotion boundary explicit.  It records that no final NMR policy has been selected,
keeps raw absolute theta as the current-report default with caveats, identifies
within-label trend/anomaly as the preferred provisional candidate policy, and
records the follow-up recommendation `pause_new_trend_anomaly_ogs_batch`.

The acceptance-record template in
`nmr_final_residual_policy_acceptance_record_template.md` is the fillable signoff
guardrail for that final NMR policy choice. It lists the four residual options from
the NMR objective decision package and currently records 0/1 primary approvals, is
not ready to apply, records no actual decision, changes no active objective,
promotes no field, and recommends no new OGS batch.

## Objective Readiness Audit

- `scripts/build_objective_readiness_audit.py`
- `objective_readiness_audit.csv`
- `objective_readiness_audit_summary.json`
- `objective_readiness_audit.md`
- `scripts/build_open_question_resolution_matrix.py`
- `open_question_resolution_matrix.csv`
- `open_question_resolution_matrix_summary.json`
- `open_question_resolution_matrix.md`

Run after refreshing report builds, observation tables, candidate runs, and release
gates:

```bash
python inversion_workflow/scripts/build_objective_readiness_audit.py
```

This audit maps the original report/model/inversion objective to current evidence.
It is stricter than a status note: each row records the requirement, current status,
authoritative artifacts, and remaining work.

Current objective state:

```text
completion_state: not_complete
requirements audited: 13
achieved: 4
achieved with tracked caveats: 6
partial: 3
blocking/incomplete: none
```

The audit confirms that the report, source model recovery with tracked caveats,
measurement inventory, processed measurement tables, source coverage, release plan,
release gates, and the frozen-model/measurement inclusion audit are in place. It
also prevents overclaiming: the final inversion is not complete while the workflow
is still a proposal/sampler-batch comparison, with ERT/Taupe/RH gates still open
and no converged posterior or optimizer trace over the combined objective.

Current loop state:

```text
executed combined candidates: 65
best candidate: basis_024_det_l_0p0075_s_1p000
best combined objective: 3156.353066948979
release gate: pass, 1300 checks
production sampler rounds best: basis_023_det_l_0p0075_s_0p750 at 3156.3547580979066
production sampler next proposal: length_0p007m_shift_1p020
production sampler decision: pause_active_production_sampling
permeability support lower-bound: current=269.818057, lower-bound=269.818057, gap=0
permeability next field-fit gate: 8 gates, same-support active-objective batch executable now false
permeability policy acceptance template: 0/1 primary approvals recorded, ready to apply false
NMR policy acceptance template: 0/1 primary approvals recorded, ready to apply false
current field package: generated
current field tensor cells: 10239 positive-definite triangle6 cells
current field deliverable status: best executed active-objective candidate, not final all-measurement inversion
current field selection active decision: accept_as_current_active_objective_incumbent
current field selection final decision: do_not_promote_to_final_all_measurement_field
conditional field selection: 8 scenarios, 5 unique winners, current field wins 1
conditional field candidate package: 5 copied scenario-winning meshes
conditional field difference audit: 4 non-current scenario winners compared
final promotion checklist: do_not_promote_current_field, 9 open criteria
final close-out playbook: 6 draft/response actions, 1 internal policy action, 2 scenario/final decision actions
final objective decision register: 9 decisions, 9 pending/not-ready, 7 explicit exclusion paths
final objective scenario matrix: 9 options, 2 current-field winning options, 5 unique winners
final objective include/exclude recommendations: 9 recommendations, promotion unblocked false
final objective no-new-evidence closeout draft: 9 draft decisions, records decisions false, promotion unblocked false
final objective no-new-evidence acceptance template: 0/9 approvals recorded, ready to apply false
open question resolution matrix: 23 rows, 6 resolved/current-scope, 9 external send/response, 6 internal policy/final-decision
Gmail send-review packet: 6 drafts, 8 requests, all unsent
```

## Current Permeability Field Package

- `scripts/build_current_permeability_field_package.py`
- `scripts/build_current_field_reproducibility_audit.py`
- `scripts/build_current_field_visual_inspection.py`
- `scripts/build_current_field_selection_audit.py`
- `scripts/build_conditional_field_selection_scenarios.py`
- `scripts/build_conditional_field_candidate_package.py`
- `scripts/build_conditional_field_difference_audit.py`
- `current_permeability_field/CURRENT_PERMEABILITY_FIELD.md`
- `current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json`
- `current_permeability_field/current_best_bulk_w_projections.vtu`
- `current_permeability_field/current_best_field_stats.csv`
- `current_permeability_field/ogs_run_inputs/`
- `current_permeability_field/packaged_file_manifest.csv`
- `current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.md`
- `current_permeability_field/CURRENT_FIELD_REPRODUCIBILITY_AUDIT.json`
- `current_permeability_field/visual_inspection/CURRENT_FIELD_VISUAL_INSPECTION.md`
- `current_permeability_field/visual_inspection/*.png`
- `current_field_selection_audit.md`
- `current_field_selection_audit_summary.json`
- `conditional_field_selection_scenarios.md`
- `conditional_field_selection_scenarios_summary.json`
- `conditional_field_candidates/CONDITIONAL_FIELD_CANDIDATES.md`
- `conditional_field_candidates/conditional_field_candidate_inventory.csv`
- `conditional_field_candidates/conditional_field_candidate_metric_evidence.csv`
- `conditional_field_candidates/CONDITIONAL_FIELD_DIFFERENCE_AUDIT.md`
- `conditional_field_candidates/conditional_field_difference_summary.csv`
- `conditional_field_candidates/conditional_field_difference_top_cells.csv`
- `final_inversion_promotion_checklist.md`
- `final_inversion_promotion_checklist_summary.json`
- `final_inversion_closeout_playbook.md`
- `final_inversion_closeout_playbook_summary.json`
- `final_objective_decision_register.md`
- `final_objective_decision_register_summary.json`
- `final_objective_scenario_matrix.md`
- `final_objective_scenario_matrix_summary.json`
- `final_objective_no_new_evidence_closeout_draft.md`
- `final_objective_no_new_evidence_closeout_draft_summary.json`
- `final_objective_no_new_evidence_acceptance_record_template.md`
- `final_objective_no_new_evidence_acceptance_record_template_summary.json`
- `permeability_configured_scalar_outlier_disposition.md`
- `permeability_configured_scalar_outlier_disposition_summary.json`
- `permeability_next_field_fit_gate.md`
- `permeability_next_field_fit_gate_summary.json`
- `permeability_likelihood_support_recommendations.md`
- `permeability_likelihood_support_recommendations_summary.json`
- `permeability_likelihood_policy_acceptance_record_template.md`
- `permeability_likelihood_policy_acceptance_record_template_summary.json`
- `gmail_draft_send_review_packet.md`
- `gmail_draft_send_review_packet_summary.json`

The package copies the current accepted run-local mesh and the run summaries needed
to inspect or rerun the field without digging through sampler directories.  It
records `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` as the packaged
run, with release gate `pass`, OGS return code 0, active objective
3156.353066948979, 75 direct permeability rows, and 192 active NMR state rows.

The packaged `k_i_rd` field has 10,239 `triangle6` cells, all positive-definite,
zero tensor asymmetry, fixed anisotropy ratio 2.5, bedding angle 144 degrees, and
fixed support porosity 0.105.  The ERT and Taupe/TDR summaries are included as
diagnostics only; their calibration/support gates remain open, so this is an
inspectable active-objective candidate rather than a final all-measurement field.
The visual inspection pass renders six PNG maps for log10 geometric-mean
permeability, minor and major eigen-permeability, local-basis increment, nearest
anchor distance, and local-basis weight support:

```bash
python inversion_workflow/scripts/build_current_field_visual_inspection.py
```

The selection audit then records the actual promotion decision.  It accepts the
packaged field as the current active-objective incumbent, but rejects promotion to a
final all-measurement field because the provisional NMR trend/anomaly residual
selects a different run, the cross-stream mean-rank winner is different, and four
criteria remain blocked or gated by ERT, Taupe/TDR, RH, other-HM, and external
response requirements.

The conditional scenario audit maps the candidate winner under eight gate/outcome
scenarios.  The current packaged field wins only the active raw-NMR objective; five
different fields win across the eight scenarios, so no single permeability field is
stable enough to report as the final all-measurement selection without resolving or
explicitly excluding the gated streams.

The conditional field-candidate package copies those five unique scenario-winning
meshes into `conditional_field_candidates/`, with per-field tensor statistics and
run summaries.  It now also extracts 25 NMR/ERT/Taupe metric-evidence rows from the
global diagnostic audits into per-candidate CSV files, with zero missing metric
rows.  This makes each gate-dependent field alternative inspectable without changing
the frozen source model or treating any gated diagnostic as accepted.

The conditional field-difference audit then compares each non-current
scenario-winning mesh against the current active-objective field cell by cell using
the geometric-mean log10 permeability of `k_i_rd`.  The nearest alternative,
`local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000`, is effectively identical
at this scale (mean absolute delta \(8.5\times10^{-6}\), no cells above 0.05
log10).  The other gate-dependent alternatives differ locally but materially:
the largest mean absolute delta is 0.0377448 log10, with at most 241 cells above
0.05 log10 and 233 cells above 0.10 log10 relative to the current field.

The final promotion checklist consolidates the close-out criteria in
`final_inversion_promotion_checklist.md`.  It records five passing criteria, one
source-model caveat, two active-objective-only passes, six external blockers, one
internal NMR policy blocker, and two failed final-promotion criteria.  The current
decision is `do_not_promote_current_field`; promotion requires closing those gates
or explicitly excluding the gated streams from the final objective.

The close-out playbook in `final_inversion_closeout_playbook.md` maps the nine open
criteria to action routes: six existing Gmail draft/response paths, one internal NMR
policy decision, and two scenario/final-field decision steps.  It also lists the
acceptance evidence and refresh commands to run after responses or exclusions are
recorded.

The final objective decision register in `final_objective_decision_register.md` is
the explicit include/exclude layer for those same open criteria.  It records nine
pending or not-ready decisions: six external stream/provenance decisions, one NMR
policy decision, and two scenario/final-field decisions.  Each row states the current
allowed use, include path, diagnostic/exclusion path, acceptance evidence, report
wording requirement, and refresh commands.  This keeps final promotion blocked until
every unresolved stream is closed, kept diagnostic-only, explicitly excluded, or
waived by a documented modelling decision.

The final objective scenario matrix in `final_objective_scenario_matrix.md` maps
those include/exclude choices to nine explicit selection options.  The current field
wins only the narrow raw-NMR active objective and the direct-only permeability tie
case; every currently scored option that promotes NMR trend/anomaly or accepts ERT
or Taupe/TDR chooses another run.  RH, other-HM, and endpoint-missing historical
permeability remain unscored future options until their missing provider evidence is
filed and the scenario audit is rebuilt.

The final objective include/exclude recommendation packet in
`final_objective_include_exclude_recommendations.md` makes the conservative
no-new-evidence position explicit.  It recommends keeping ERT, Taupe/TDR, RH,
other-HM, endpoint-missing historical permeability rows, and CTE out of final hard
likelihood weights unless provider evidence arrives or an explicit modelling
decision is recorded.  It also keeps NMR as a current-report policy caveat rather
than a final residual-policy decision, and it does not unblock final promotion.

The no-new-evidence closeout draft in
`final_objective_no_new_evidence_closeout_draft.md` turns those recommendations
into exact review text for a possible conservative closeout.  It contains nine
draft decision rows and a single-block acceptance text that would select
`F01_current_raw_nmr_exclude_gated_streams` only after user/modelling-team approval
and regenerated scenario/current-field/promotion audits.  The draft records no
actual decisions, sends no email, and does not promote the current field.

The acceptance-record template in
`final_objective_no_new_evidence_acceptance_record_template.md` is the fillable
signoff guardrail for that same path.  It has nine rows, records zero approvals,
is not ready to apply, and keeps final promotion blocked until every approval field
is filled from a real decision and the audits are regenerated.

The Gmail draft send-review packet in `gmail_draft_send_review_packet.md`
consolidates the outbound review list into six drafts covering eight request rows.
It records the subject, To/Cc route, Gmail draft id, response-note path, acceptance
evidence, and a short preview for each draft.  It does not send or modify mail.

## Continuous Inversion Loop

- `scripts/run_continuous_inversion_loop.py`
- `runs/continuous_inversion_loop/latest_loop_summary.md`
- `runs/continuous_inversion_loop/lower_support_cumulative_search_results.csv`

The loop driver wraps the existing deterministic pieces: rebuild adaptive evidence,
propose lower-support continuous fields, execute the top batch with
`run_inversion_candidate_search.py --ogs-mode execute`, merge the lower-support
evidence, refresh proposal/readiness artifacts, and rerun the release gate over all
executed candidate directories.

The first loop iteration executed `length_0p003m_shift_1p006`,
`length_0p005m_shift_0p985`, and `length_0p004m_shift_1p014`.  The best row is
`length_0p003m_shift_1p006` with combined objective 3156.37, a small improvement over
the previous lower-support best.  The second loop executed
`length_0p004m_shift_0p992`, `length_0p004m_shift_1p020`, and
`length_0p006m_shift_0p975`; the best row was 3156.40, so the incumbent did not
improve.  The current broad adaptive proposal is led by
`length_0p008m_shift_1p011`, `length_0p007m_shift_1p020`, and
`length_0p007m_shift_1p022`, while the focused lower-support plan now has
effectively zero probability of improvement for its top local candidate.

The first broad continuous evidence batch executed `length_0p023m_shift_1p004`,
`length_0p022m_shift_0p998`, and `length_0p021m`.  The best row was
`length_0p023m_shift_1p004` at 3159.06, so the incumbent stayed unchanged and the
previous broad uncertainty top was demoted in the refreshed proposal models.

The generalized loop driver then executed a broad continuous iteration over
`length_0p015m`, `length_0p016m_shift_0p968`, and `length_0p010m`.  The best row was
`length_0p010m` at 3157.70, so the incumbent still stayed unchanged.

## Anisotropy Sensitivity Plan

- `scripts/build_anisotropy_sensitivity_plan.py`
- `runs/anisotropy_sensitivity_plan/ANISOTROPY_SENSITIVITY_PLAN.md`
- `runs/anisotropy_sensitivity_plan/anisotropy_sensitivity_results.csv`
- `runs/anisotropy_sensitivity_plan/next_anisotropy_candidate_batch.csv`

The current smooth-field search changes local log-magnitude support while preserving
the global tensor orientation and anisotropy ratio.  The anisotropy sensitivity pass
tests the missing global degree of freedom directly: starting from the incumbent
`length_0p003m_shift_1p006` mesh, it preserves each cell's geometric-mean
permeability and sweeps tensor principal-direction angles and anisotropy ratios.

Current result:

```text
candidates: 35
baseline orientation: 144 deg
baseline anisotropy ratio: 2.5
best direct candidate: anis_theta_144p0_ratio_2p50
best direct objective: 269.83548846393245
delta versus baseline: 0.0
```

This means the direct pulse-test layer does not support spending an OGS batch on a
global angle/ratio-only perturbation.  Subsequent local-basis, local-anisotropy,
cross-stream hybrid, structural/EDZ, and support lower-bound audits now show that
more same-support active-objective sampling should wait for a support/likelihood
decision or for gated streams such as ERT/Taupe/RH to become active enough to justify
broader permeability-field degrees of freedom.

## Local-Basis Permeability Sampler

- `scripts/build_local_basis_sampler_plan.py`
- `runs/local_basis_sampler_plan/LOCAL_BASIS_SAMPLER_PLAN.md`
- `runs/local_basis_sampler_plan/local_basis_sampler_scores.csv`
- `runs/local_basis_sampler_plan/next_local_basis_candidate_batch.csv`

The local-basis sampler is the first richer field-basis diagnostic after the smooth
support and global anisotropy checks.  It starts from the incumbent
`length_0p003m_shift_1p006` mesh, builds 30 residual-derived anchor cells from the
active permeability pulse-test rows, perturbs only the run-local `k_i_rd` tensor
magnitude field, and scores the direct pulse-test layer before any OGS state outputs
are generated.

Current result:

```text
candidates scored: 131
basis anchor cells: 30
baseline direct objective: 269.83548846393245
best direct candidate: basis_004_det_l_0p0015_s_1p000
best direct objective: 269.8180571059851
direct objective delta: -0.01743135794737327
weighted RMSE log10: 1.61071549171474
proposed OGS batch size: 3
executed OGS batch best: basis_024_det_l_0p0075_s_1p000
executed combined objective: 3156.353066948979
```

The improvement is real but tiny on the direct permeability layer.  The selected
batch affects 30, 37, and 47 cells, respectively, and has now been executed with
`run_inversion_candidate_search.py --ogs-mode execute`.  All three runs returned code
0, passed the release gate, and sampled 192 active NMR state rows.  The best
combined candidate is `basis_024_det_l_0p0075_s_1p000` at 3156.35, a small
improvement over the previous `length_0p003m_shift_1p006` incumbent at 3156.37.

## Local Anisotropy Sampler

- `scripts/build_local_anisotropy_sampler_plan.py`
- `runs/local_anisotropy_sampler_plan/LOCAL_ANISOTROPY_SAMPLER_PLAN.md`
- `runs/local_anisotropy_sampler_plan/local_anisotropy_sampler_scores.csv`
- `runs/local_anisotropy_sampler_plan/next_local_anisotropy_candidate_batch.csv`

The local-basis sampler perturbs local tensor magnitude while preserving the active
orientation and anisotropy ratio.  The local anisotropy sampler tests the missing
local tensor freedom directly: it starts from the active incumbent
`local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`, preserves each cell's
geometric-mean permeability, and locally changes only the anisotropic split and
principal direction around the mapped pulse-test support cells.

Current result:

```text
candidates scored: 80
anchor rows: 75
unique anchor cells: 30
baseline direct objective: 269.8180571059851
best direct candidate: local_anis_isotropize_l0p015_s0p5_r1
best direct objective: 270.0079771623993
direct objective delta: +0.18992005641422338
```

Every tested local tensor-anisotropy candidate worsens the direct permeability
screen.  This argues against spending a release-gated OGS batch on local
orientation/ratio release for the active direct-permeability plus NMR objective
alone.

## Production Sampler And Convergence Audit

- `scripts/build_production_sampler_convergence_audit.py`
- `runs/production_sampler_convergence/PRODUCTION_SAMPLER_CONVERGENCE.md`
- `runs/production_sampler_convergence/executed_evidence_accepted.csv`
- `runs/production_sampler_convergence/convergence_by_stage.csv`
- `runs/production_sampler_convergence/cross_family_candidate_scores.csv`
- `runs/production_sampler_convergence/next_production_candidate_batch.csv`
- `runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.md`

This audit is the cross-family convergence and handoff record after the local-basis
batch and five production sampler rounds.  It standardizes the 54 accepted smooth-family OGS rows
and the 11 accepted local-basis OGS rows, checks the best-so-far history by execution
stage, scores the smooth and local-basis candidate pools with a random-forest
state-objective surrogate, and emits only candidates with materialized mesh files
into the next executable batch.  It also writes an explicit stop/continue decision
for the active direct-permeability plus NMR objective.

Current result:

```text
executed OGS evidence rows: 65
candidate pool rows: 394
unexecuted rows with materialized meshes: 210
best accepted field: basis_024_det_l_0p0075_s_1p000
best accepted objective: 3156.353066948979
local-basis improvement versus smooth incumbent: 0.019941698288221232
production sampler rounds best: basis_023_det_l_0p0075_s_0p750 at 3156.3547580979066
latest production round best: length_0p004m_shift_1p031 at 3156.785440
next executable production proposal: length_0p007m_shift_1p020
surrogate CV state-objective RMSE: 10.430369372008856
stop/continue decision: pause_active_production_sampling
```

Five production sampler rounds have now been executed and their best row is still
worse than the local-basis incumbent.  The decision audit recommends pausing this
active-objective production sampler because the next batch has low diagnostic
probability of improvement and all proposed lower-confidence bounds are above the
incumbent objective.  This is not a final inversion claim: it only says that more
smooth-family handoff OGS runs are not the best next use of compute until new
measurement streams or a new field family are ready.

## Cross-Stream Candidate Scorecard

- `scripts/build_cross_stream_candidate_scorecard.py`
- `cross_stream_candidate_scorecard.csv`
- `cross_stream_candidate_scorecard_summary.json`
- `cross_stream_candidate_scorecard.md`

This scorecard joins the active direct-permeability/raw-NMR objective with the
current NMR bias/anomaly, ERT log-resistivity, and Taupe/TDR trend diagnostics for
the same executed run ids.  It is diagnostic only: it does not promote ERT, Taupe,
or the offset-robust NMR alternatives into the likelihood.

Current result:

```text
joined executed runs: 66
top-10 in every stream: 0
Pareto candidates across active objective plus diagnostics: 23
active incumbent: local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000
active incumbent ranks: active=1, NMR-bias=14, ERT=8, Taupe=29
best mean-rank compromise: local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000
best compromise mean rank: 10.4
best compromise worst rank: 18
```

The scorecard is the current guard against overclaiming.  The active incumbent is a
good active-objective row, but it is not the consensus winner once the diagnostic
streams are viewed together; final field selection still depends on resolving or
explicitly excluding those stream gates.

## Cross-Stream Hybrid Field Screen

- `scripts/build_cross_stream_hybrid_field_plan.py`
- `runs/cross_stream_hybrid_field_plan/CROSS_STREAM_HYBRID_FIELD_PLAN.md`
- `runs/cross_stream_hybrid_field_plan/cross_stream_hybrid_candidate_scores.csv`
- `runs/cross_stream_hybrid_field_plan/next_cross_stream_hybrid_candidate_batch.csv`

This screen is the first new field-family check after the production sampler pause.
It takes the active incumbent
`local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`, derives permeability
magnitude from the actual `k_i_rd` tensors, and geometrically blends that magnitude
with the patterns from cross-stream winner runs while preserving the active tensor
orientation and anisotropy ratio.  The stored `k_mag_rd` metadata is not used as
the blend source because it is unchanged across several executed runs even when the
`k_i_rd` tensor components differ.

Current result:

```text
target winner runs: 5
hybrid fields screened: 15
active direct objective: 269.8180571059851
best hybrid: cross_hybrid_mean_rank_all_streams_plus2_a0p25
best hybrid direct objective: 269.8180571059851
best hybrid delta versus active: 0.0
```

No hybrid improves the direct permeability screen.  The emitted batch is therefore
only a deliberate diagnostic probe of cross-stream magnitude patterns; it does not
justify spending OGS runs on the active direct-permeability plus NMR objective
alone.

## Structural/EDZ Field-Family Screen

- `scripts/build_structural_edz_field_family_plan.py`
- `runs/structural_edz_field_family_plan/STRUCTURAL_EDZ_FIELD_FAMILY_PLAN.md`
- `runs/structural_edz_field_family_plan/structural_edz_candidate_scores.csv`
- `runs/structural_edz_field_family_plan/next_structural_edz_candidate_batch.csv`
- `../cda_knowledge_base/measurements/structural_edz_field_family_plan/derived_files/`

This screen checks a more explicitly geometric field family after the same sampler
pause.  It starts from the packaged active field and applies run-local log10
permeability multipliers shaped as central EDZ caps, central shells, bedding-parallel
bands using the documented \(144^\circ\) orientation, and broad open-twin corridors
around the mapped BCD-A32/BCD-A33 pulse-test lines.  The tensor orientation and
anisotropy ratio are preserved by scalar multiplication of `k_i_rd`, and no source
model file is modified.

Current result:

```text
structural/EDZ fields screened: 234
active direct objective: 269.8180571059851
active support cells in the permeability objective: 30
ERT ready-support cells catalogued for context: 1928
best structural/EDZ candidate: struct_bedding_parallel_band_bed_om0p75_w0p25_a0p5
best structural/EDZ family: bedding_parallel_band
best structural/EDZ direct objective: 269.8180571059851
improving candidates: 0
status: structural_edz_direct_screen_no_ogs_batch_recommended
```

No central EDZ, shell, bedding-band, or open-twin corridor candidate improves the
direct permeability screen.  The proposed batch therefore remains a documented
diagnostic probe only and should not be run for the current active objective without
a new modelling decision.

## Permeability Residual Conflict Audit

- `scripts/build_permeability_residual_conflict_audit.py`
- `permeability_residual_conflict_audit.md`
- `permeability_residual_conflict_audit.csv`
- `permeability_residual_segment_summary.csv`
- `permeability_residual_support_cell_audit.csv`
- `../cda_knowledge_base/measurements/permeability_residual_conflict_audit/derived_files/`

This audit explains what is still wrong in the active direct pulse-test layer for
the packaged field.  It re-evaluates the current `k_i_rd` tensor against all
permeability targets, then checks whether each active observation is inside the
configured scalar multiplier range implied by the current tensor shape and the
sampler eigenvalue bounds \(10^{-22}\)--\(10^{-12}\,\mathrm{m^2}\).

Current result:

```text
active direct rows: 75
weighted direct RMSE: 1.610715 log10(k)
rows with |residual| >= 1 log10: 48
rows with |residual| >= 2 log10: 21
rows outside configured scalar range: 2
support cells with repeated active rows: 24
support cells with observed range >= 1 log10: 16
```

Only two active rows are outside the configured scalar range, but many rows remain
large and many support cells carry repeated or conflicting active observations.  The
next direct-permeability step should therefore be a support/interpretation or
parameterization decision, not another smooth handoff batch by default.

## Permeability Likelihood Policy Audit

- `scripts/build_permeability_likelihood_policy_audit.py`
- `permeability_likelihood_policy_audit.md`
- `permeability_likelihood_policy_audit.csv`
- `permeability_likelihood_policy_row_audit.csv`
- `permeability_likelihood_policy_group_summary.csv`
- `permeability_likelihood_decision_request.md`
- `permeability_configured_scalar_outlier_disposition.md`
- `permeability_configured_scalar_outlier_disposition.csv`
- `permeability_likelihood_scenario_rerank.md`
- `permeability_likelihood_scenario_rerank.csv`
- `permeability_likelihood_scenario_rerank_policy_winners.csv`
- `permeability_likelihood_winner_cross_stream_audit.md`
- `permeability_likelihood_winner_cross_stream_audit.csv`
- `permeability_next_field_fit_gate.md`
- `permeability_next_field_fit_gate.csv`
- `permeability_likelihood_policy_acceptance_record_template.md`
- `../cda_knowledge_base/measurements/permeability_likelihood_policy_audit/derived_files/`

This audit keeps the active direct-permeability objective unchanged, then tests
whether the remaining mismatch is a field-search problem or a likelihood semantics
problem.  It compares the current duplicate-weighted Gaussian row policy with
diagnostic robust row losses and support-cell aggregation.

Current result:

```text
active row-Gaussian objective: 269.818057
weighted direct RMSE: 1.610715 log10(k)
top 10 row-loss share: 0.494
support-cell groups: 30
support-cell groups with observed range >= 1 log10: 16
support-cell weighted-mean objective: 1.77e-28
support-cell weighted-median objective: 134.727790
```

The near-zero support-cell mean diagnostic is the important warning: the packaged
field is already matching duplicate-weighted means of rows that map to the same
model support cell.  The active loss remains large because individual pulse-test
rows within those support cells disagree by several log units.  Any move to robust
tails, support-cell aggregation, or scalar-range outlier handling is therefore a
modelling-team likelihood decision, not a silent replacement of the recorded
rowwise Gaussian objective.

The no-OGS existing-field rerank in
`permeability_likelihood_scenario_rerank.md` scores 522 materialized VTU fields
under the same diagnostic likelihood policies.  Forty fields tie for the active
row-Gaussian best score, and the current accepted field is in that tie set.  The
Huber and Student-t row policies keep their winner inside that tie set, while the
capped row loss, support-cell median aggregation, and configured-scalar inside-only
diagnostic each select a winner outside it.  This confirms that likelihood
semantics can change candidate ranking, but it still does not approve a policy
change by itself.

The follow-up decision request in
`permeability_likelihood_decision_request.md` records the exact choices that must
be accepted before the next active-objective OGS batch: keep the rowwise Gaussian
default and change parameterization, promote a robust row likelihood, aggregate by
model support cell, gate scalar-range outliers, or define a new field family and
materiality threshold.  The current report policy is to keep the rowwise Gaussian
objective as the reproducible default until one of those choices is explicitly
approved; use the existing-field rerank as decision evidence and refresh it if the
accepted likelihood formula changes.

The configured-scalar outlier disposition in
`permeability_configured_scalar_outlier_disposition.md` resolves the local
bounds/tensor-shape bookkeeping for the two active rows outside the configured
scalar envelope.  They are one duplicated BCD-A32 0.87 m high-permeability value,
only 0.107 log10 above the current upper envelope, but mapped to support cell 4648
where active values span 6.949 log10.  The local disposition is therefore no
immediate eigenvalue-bound widening or tensor-shape release from these rows alone;
they remain visible under the current rowwise Gaussian default until the modelling
team accepts this disposition or chooses robust/capped/support-cell/outlier
likelihood semantics explicitly.

The winner cross-stream audit in
`permeability_likelihood_winner_cross_stream_audit.md` then joins the policy
winners to executed-run NMR/ERT/Taupe scorecard evidence.  Of the seven policy
winner rows, only four have cross-stream scorecard evidence, representing two
unique fields.  The three non-default winners outside the row-Gaussian best tie
set are direct-only materialized fields with no OGS/state/ERT/Taupe/NMR scorecard
evidence.  The row-Gaussian representative chosen by candidate-id sorting has
active-objective rank 45 and mean all-stream rank 30.4, while the current accepted
field has active-objective rank 1 and mean all-stream rank 13.2.  Therefore the
current field should not be replaced by a direct-only non-default winner without
OGS execution and stream diagnostics.

The next field-fit gate in `permeability_next_field_fit_gate.md` makes that pause
operational.  It records eight gates and the recommendation
`pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes`.
Under the current rowwise Gaussian policy, no same-support active-objective OGS
batch is executable now.  Reopening OGS spending requires an accepted likelihood,
support mapping, configured-bound/tensor-shape, or measurement-stream objective
change; any non-default direct policy winner also needs OGS/state/diagnostic
evidence before it can affect final promotion.

The consolidated recommendation packet in
`permeability_likelihood_support_recommendations.md` collects these direct
permeability policy checks into eight action rows.  It keeps
`keep_rowwise_gaussian_default` as the current-report policy, records that the
field is already at the single-support lower bound with zero same-support
reducible gap, rejects immediate bounds or tensor-shape release, and confirms that
the packet does not unblock final promotion.

The acceptance-record template in
`permeability_likelihood_policy_acceptance_record_template.md` is the fillable
signoff guardrail for that direct-permeability policy decision. It lists the five
exclusive policy options from the decision request and currently records 0/1
primary approvals, is not ready to apply, records no actual decision, changes no
active objective, and keeps same-support OGS spending blocked.

## Taupe/TDR Series-Weight Sensitivity

- `scripts/build_taupe_series_weight_sensitivity_audit.py`
- `taupe_series_weight_sensitivity_audit.csv`
- `taupe_series_weight_sensitivity_series.csv`
- `taupe_series_weight_sensitivity_summary.json`
- `taupe_series_weight_sensitivity.md`

This audit uses the existing Taupe/TDR series diagnostic to check whether the trend
screen depends on row, series, sensor, or EDZ-band weights.  The 12 mapped A3/A4
series are compared over 66 full active-objective runs; A7/A8 remain outside the
current local mesh support.

Current result:

```text
compared A3/A4 series: 12
uncompared A7/A8 series: 12
distinct per-series winner runs: 8
best aggregate/equal-series run: adaptive_combined_001_length_0p050m
A3-only winner: local_bracketed_003_length_0p031m
A4-only winner: adaptive_combined_002_length_0p050m_shift_0p750
```

This keeps Taupe/TDR as diagnostic evidence.  Sensor-specific uncertainty and
grouped weights still need a calibration decision before Taupe can become a hard
likelihood term.

## Relevant Source Model

The recovered projection example is kept in:

- `../GESA_model_original/projection_on_mesh_2025-09-05/`

That archive already switches `phi` and `k_i` to mesh-cell fields:

- `phi` reads `field_name` = `n_rd`
- `k_i` reads `field_name` = `k_i_rd`

The original example generated scalar random fields.  The script here replaces that
with a reproducible anisotropic 2D tensor field for `k_i_rd` while preserving all other
mesh data.

## Script

- `scripts/generate_anisotropic_permeability_field.py`

The script reads a VTU mesh, computes element centroids, generates a spatially
correlated log-permeability field, rotates a bedding-parallel tensor into model
coordinates, and writes the tensor components as a cell-data field.

The generated `k_i_rd` field has four components per element:

```text
k_xx k_xy k_yx k_yy
```

This matches the 2D tensor order used by the constant XML reference
`1.00E-19 0.00 0.00 0.40E-19`.

## Smoke-Test Command

Run from `SOTA_OGS_Mont_Terri_work`:

```bash
python inversion_workflow/scripts/generate_anisotropic_permeability_field.py \
  --input GESA_model_original/projection_on_mesh_2025-09-05/bulk.vtu \
  --output /tmp/cda_anisotropic_test.vtu \
  --seed 20260528 \
  --theta-deg 144 \
  --anisotropy-ratio 2.5 \
  --mean-k-ref 6.32e-20 \
  --log-sigma 0.5 \
  --corr-length 0.6
```

Then inspect that `/tmp/cda_anisotropic_test.vtu` contains cell arrays `k_i_rd`,
`k_mag_rd`, and `k_anisotropy_ratio_rd`.

## Use In An OGS Run

Use the run-preparation script to make a self-contained run directory:

```bash
python inversion_workflow/scripts/prepare_ogs_run.py \
  --config inversion_workflow/run_config.example.json \
  --run-id example_20260528 \
  --overwrite
```

The script copies the projection model files into `inversion_workflow/runs/<run-id>/`,
regenerates `bulk_w_projections.vtu`, and writes `RUN_MANIFEST.json`.

For the smoke-test run, the generated mesh contained:

```text
k_i_rd: (10239, 4)
n_rd: (10239, 1)
```

These are the two `MeshElement` fields read by the projection XML.  `k_i_rd` is the
anisotropic permeability tensor; `n_rd` is fixed porosity, currently `0.105`.

Before a production OGS run, re-run or verify subdomain identification for
`bulk_all.vtu` and the boundary meshes as noted in the recovered projection
`README.txt`.

The script currently generates a prior/proposal field.  It does not fit data by
itself; an inversion driver should call this script or its logic for each sample,
then evaluate the measurement observation operators described in the report.

## Observation Manifest

- `observation_manifest.json`
- `scripts/validate_observation_manifest.py`
- `observation_manifest_validation.json`

Run from `SOTA_OGS_Mont_Terri_work` with the bundled Codex Python runtime:

```bash
/home/ber0061/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  inversion_workflow/scripts/validate_observation_manifest.py
```

Current validation result:

```text
validated 28 checks across 9 observations
failures: 0
```

The manifest covers ERT, NMR, permeability pulse tests, Taupe/TDR, suction/RH,
coordinates/geometry, bedding/structure, model-projection inputs, and other HM
monitoring.  It checks file existence plus key ZIP counts, workbook sheets/columns,
CSV columns/row counts, text markers, and the OGS projection mesh cell data.

## Processed Observation Tables

- `scripts/build_processed_observations.py`
- `processed_observations/README.md`
- `processed_observations/*.csv`

Run from `SOTA_OGS_Mont_Terri_work` with the bundled Codex Python runtime:

```bash
/home/ber0061/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  inversion_workflow/scripts/build_processed_observations.py
```

The builder mines the measurement workbooks and ZIPs into normalized CSV tables for
model-facing observation operators.  Current outputs include weekly and seasonal NMR,
open-niche ERT archive/timestep inventories, ERT water-content/resistivity calibration
tables, interpreted permeability intervals, raw permeability pressure-decay series,
RH-to-Kelvin-pressure conversion, Taupe EDZ-band time series, and coordinate lookup
tables.  Separate operator builders then add the ERT calibration artifact, ERT spatial
lookup artifact, and Taupe/TDR trend artifact on top of those normalized tables.
The secondary HM monitoring layer is generated separately because it streams the
large Tecplot layout and records qualitative validation gates rather than direct
water-content or permeability observations.

The current generated summary is:

```text
16 processed observation tables
NMR weekly: 170 rows
NMR seasonal profiles: 294 rows
ERT timesteps: 1691 rows, including 16 timestep-list entries without a matching VTK
Permeability interpreted values: 204 rows
Permeability pressure decay: 6687 rows
RH Kelvin table: 4247 rows
Taupe/TDR EDZ bands: 5088 rows
```

These tables are derived products, not new raw data.  Every row keeps `source_file`
and, where applicable, `source_sheet` or `source_member` columns so the original email
or TeamBeam file can be traced before using a value in an inversion likelihood.

## NMR Bound-Water Sensitivity

- `scripts/build_nmr_bound_water_sensitivity.py`
- `processed_observations/nmr_bound_water_target_audit.csv`
- `processed_observations/nmr_bound_water_offset_scenarios.csv`
- `processed_observations/nmr_bound_water_group_offsets.csv`
- `processed_observations/nmr_bound_water_sensitivity_summary.json`
- `processed_observations/nmr_bound_water_sensitivity.md`
- `scripts/build_nmr_candidate_bias_sensitivity_audit.py`
- `nmr_candidate_bias_sensitivity_audit.csv`
- `nmr_candidate_bias_sensitivity_offsets.csv`
- `nmr_candidate_bias_sensitivity_label_biases.csv`
- `nmr_candidate_bias_sensitivity_summary.json`
- `nmr_candidate_bias_sensitivity.md`

Run after the state-observation targets exist:

```bash
python inversion_workflow/scripts/build_nmr_bound_water_sensitivity.py
```

This audit quantifies the NMR bound/interlayer-water caveat before NMR rows are used
as numerical OGS state residuals.  With the current fixed porosity of 0.105, 315 of
464 NMR target rows, and 162 of the 287 currently usable Niche-4 mapped rows, exceed
the maximum possible model-side `theta_model = porosity * liquid_saturation` if the
raw NMR values are interpreted as mobile water content without correction.  The
usable-row required positive offset has p95 = 0.0402 and max = 0.1231.  A tested
uniform subtraction of 0.05 gives the highest simple physical-row count for currently
usable rows, but still leaves 7 nonphysical usable rows, so the preferred first OGS
comparison is a within-label trend/anomaly residual or an absolute residual with
explicit label/campaign bias or model-error terms.

The candidate bias/anomaly audit applies those safer diagnostic forms to 66 executed
OGS runs with 192 active NMR rows each.  Under the current raw absolute-theta
objective, the best run is `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
with combined objective 3156.353066948979.  After fitting non-negative per-label NMR
bias terms, or equivalently comparing within-label anomalies for these all-positive
bias groups, the best diagnostic run becomes `broad_continuous_001_003_length_0p021m`
with diagnostic combined objective 505.614305828437.  The current-vs-label-bias rank
correlation is 0.6351529067946979, so the active permeability ranking is conditional
on the unresolved NMR free-water/bound-water interpretation.

The provisional executable package validates the assembler implementation of the same
within-label trend/anomaly residual against the diagnostic audit with maximum absolute
delta `5.684341886080802e-14`.  Among the 66 full active direct-permeability plus NMR
runs, `broad_continuous_001_003_length_0p021m` is still the trend/anomaly winner
with objective 505.614305828437; the raw-objective incumbent is rank 14 under this
mode, and the trend/anomaly winner is rank 56 under the raw objective.

The follow-up planner:

- `scripts/build_nmr_trend_anomaly_followup_plan.py`
- `runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.md`
- `runs/nmr_trend_anomaly_followup_plan/NMR_TREND_ANOMALY_FOLLOWUP_PLAN.json`
- `runs/nmr_trend_anomaly_followup_plan/nmr_trend_anomaly_followup_candidates.csv`

screens 489 unique candidate-pool rows and 305 unevaluated runnable mesh files
against that trend/anomaly incumbent.  It recommends
`pause_new_trend_anomaly_ogs_batch`: the best unevaluated direct-objective advantage
is only 0.011975, below the 0.739495 materiality threshold inferred from the observed
NMR trend/anomaly state-objective spread, and no unevaluated candidate beats the
incumbent under the median observed NMR state term.

The final NMR residual-policy gate records this as a policy and execution boundary:
raw absolute theta stays the current-report default, within-label trend/anomaly is
the preferred provisional final policy if accepted, and no additional OGS spending
is justified for that promoted-NMR mode until the final NMR semantics are selected.

## Other HM Monitoring Inventory

- `scripts/build_other_hm_monitoring_inventory.py`
- `scripts/build_other_hm_missing_numeric_request.py`
- `scripts/build_other_hm_numeric_source_audit.py`
- `processed_observations/other_hm_visualisation_zones.csv`
- `processed_observations/other_hm_visualisation_text_labels.csv`
- `processed_observations/other_hm_levelling_displacements.csv`
- `processed_observations/other_hm_qualitative_targets.csv`
- `processed_observations/other_hm_monitoring_summary.json`
- `processed_observations/other_hm_monitoring.md`
- `processed_observations/other_hm_missing_numeric_request.csv`
- `processed_observations/other_hm_missing_numeric_evidence.csv`
- `processed_observations/other_hm_missing_numeric_request_summary.json`
- `processed_observations/other_hm_missing_numeric_request.md`
- `processed_observations/other_hm_numeric_source_audit.csv`
- `processed_observations/other_hm_numeric_source_evidence.csv`
- `processed_observations/other_hm_numeric_source_audit_summary.json`
- `processed_observations/other_hm_numeric_source_audit.md`

Run after the collected TD minutes, levelling slides, modelling slides and Tecplot
layout are present:

```bash
/home/ber0061/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  inversion_workflow/scripts/build_other_hm_monitoring_inventory.py
```

Current result:

```text
Tecplot zones: 84
layout labels: 11
precision-levelling rows: 12
qualitative HM validation targets: 10
status: layout_and_qualitative_targets_ready_numeric_series_missing
```

This makes extensometer, mini-piezometer, crackmeter, laser-scan and levelling
evidence explicit in the workflow.  It does not make those streams active objective
terms yet: Geoscope time series and laser-scan statistical exports are still needed
before pressure/deformation residual weights can be assigned.

The missing-export follow-up is now a concrete request package:

```bash
python inversion_workflow/scripts/build_other_hm_missing_numeric_request.py
```

It writes six request rows for Geoscope mini-piezometer, extensometer, crackmeter,
boundary/context, laser-scan statistical interpretation, and full levelling survey
exports, plus eight source-evidence rows.  The package is copied into the
`other_hm_monitoring/derived_files` catalogue folder.  It still keeps active
objective rows at zero until numeric exports, units, support geometry, reference
conventions, and quality/status flags are present.

The numeric source audit verifies that status against the local bundle:

```bash
python inversion_workflow/scripts/build_other_hm_numeric_source_audit.py
```

It scans 10 source files and 7 ZIP members.  All 6 request classes have local
support evidence, but 0 are hard-residual-ready.  The ZIP contains only PDFs, and
the only numeric-extension source file in this folder is `VisualisationCDA.dat`,
which is support geometry rather than Geoscope time series.  The extracted 12-row
levelling table remains a sign/order-of-magnitude check until a full survey table,
reference frame, covariance, and all epochs are available.

## ERT Observation Operator

- `scripts/build_ert_observation_operator.py`
- `processed_observations/ert_water_content_resistivity_operator.csv`
- `processed_observations/ert_observation_operator_summary.json`
- `processed_observations/ert_observation_operator.md`
- `processed_observations/ert_measurement_semantics_timestep_audit.csv`
- `processed_observations/ert_measurement_semantics_relation_audit.csv`
- `processed_observations/ert_measurement_semantics_projection_groups.csv`
- `processed_observations/ert_measurement_semantics_summary.json`
- `processed_observations/ert_measurement_semantics.md`

Run after the processed observation tables exist:

```bash
/home/ber0061/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  inversion_workflow/scripts/build_ert_observation_operator.py
```

This builder makes the first ERT calibration component explicit.  It fits and records
power-law mappings of the form

```text
rho_ohm_m = a * theta_fraction ** b
theta_fraction = porosity * liquid_saturation
```

Current default first-test relation:

```text
relation id: kruschwitz_model_data2019
a: 1.108
b: -1.58
theta range: 0.01 to 0.18
ERT timestep rows: 1691, including 1675 with matching VTK member
```

The Niche-4 paired NMR/resistivity fit is also retained, but it is much more scattered
(RMSE 0.202 log10 resistivity units), so it is treated as a diagnostic rather than the
default conversion.  This ERT artifact does not yet make ERT an active objective term:
the spatial part is handled by the next lookup artifact.

Run the ERT semantics audit after the calibration and spatial lookup artifacts exist:

```bash
python inversion_workflow/scripts/build_ert_semantics_audit.py
```

The current audit records 1,691 ERT timestep rows, 1,675 with matching VTK members,
16 blocked by missing VTK matches, 5,966 projected ERT cells, and 2,035 cells that
satisfy both the OGS-cell and approximate central-support screens.  It explicitly
keeps ERT as an electrical-resistivity field residual; it is not measured saturation,
water content, pressure, or permeability.

## ERT Spatial Projection Operator

- `scripts/build_ert_spatial_projection_lookup.py`
- `processed_observations/ert_spatial_projection_lookup.csv`
- `processed_observations/ert_spatial_projection_summary.json`
- `processed_observations/ert_spatial_projection_operator.md`

Run after the ERT calibration exists:

```bash
python inversion_workflow/scripts/build_ert_spatial_projection_lookup.py
```

Use the Python environment that has `meshio`, because the script reads a reference
ERT VTK from the ZIP archive.  The current lookup records the provisional transform
`model_x = raw_x`, `model_y = raw_y + 500`, maps the 5,966 ERT triangular cells to
the OGS mesh, and adds an approximate 1.5 m central support flag from the local slide
notes.

Current ERT spatial result:

```text
ERT reference cells: 5966
OGS inside-cell rows: 4676
approximate 1.5 m support rows: 2194
rows ready after OGS output and support confirmation: 2035
ERT timesteps with matching VTK: 1675 of 1691
```

This lookup is not yet an active ERT objective term.  The remaining blockers are
confirmation of the ERT-to-OGS coordinate transform, reconstruction/agreement of the
exact near-niche 35 cm-in-rock support mask, and an ERT inversion
uncertainty/correlation model.

## ERT Resistivity Diagnostic

- `scripts/evaluate_ert_resistivity_diagnostic.py`
- `runs/direct_fit_observation_run/ert_resistivity_diagnostic.csv`
- `runs/direct_fit_observation_run/ert_resistivity_diagnostic_timesteps.csv`
- `runs/direct_fit_observation_run/ert_resistivity_diagnostic_summary.json`
- `runs/direct_fit_observation_run/ert_resistivity_diagnostic.md`
- `scripts/build_ert_candidate_discrimination_audit.py`
- `ert_candidate_discrimination_audit.csv`
- `ert_candidate_discrimination_timesteps.csv`
- `ert_candidate_discrimination_summary.json`
- `ert_candidate_discrimination.md`

Run after OGS outputs and the ERT spatial lookup exist:

```bash
python inversion_workflow/scripts/evaluate_ert_resistivity_diagnostic.py \
  --ogs-output-dir inversion_workflow/runs/direct_fit_observation_run/ogs_output \
  --support-mesh inversion_workflow/runs/direct_fit_observation_run/bulk_w_projections.vtu \
  --output inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic.csv \
  --timestep-output inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic_timesteps.csv \
  --summary-output inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic_summary.json \
  --markdown-output inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic.md
```

The direct-run diagnostic now samples OGS `theta = porosity * saturation` on the
2,035 currently supported ERT cells, converts it with the default Kruschwitz relation,
and compares it with the nearest open-niche ERT field within a 10-day tolerance.
It compares 162,800 cell-time rows across 80 OGS output times; 3 output times are
outside the time tolerance.  The area-weighted log10 residual summary is MAE
0.2541801957739222 and RMSE 0.29996586160456457.  This closes the local OGS-output
sampling part of the ERT operator, but the stream remains diagnostic until the
coordinate transform, near-niche support mask, and uncertainty/correlation model are
accepted.

The cross-run audit `scripts/build_ert_candidate_discrimination_audit.py` applies the
same log-resistivity diagnostic to 66 executed OGS runs with output fields.  Each run
compares 162,800 cell-time rows over 80 output times.  Across the current candidate
family, ERT MAE spans 0.019635573360798686 log10 units.  The ERT-only best run is
`broad_continuous_001_001_length_0p023m_shift_1p004` with MAE
0.25407209193077057; the best active-objective run is
`local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` with ERT MAE
0.2541796182834413.  The combined-objective/ERT-MAE correlation is
0.8894403368395667, so candidates that improve the active permeability+NMR objective
generally do not improve the provisional ERT score.  This is useful screening
evidence, but ERT remains outside the likelihood until transform, support, and
uncertainty gates are accepted.

## Taupe/TDR Observation Operator

- `scripts/build_taupe_observation_operator.py`
- `processed_observations/taupe_tdr_trend_operator.csv`
- `processed_observations/taupe_tdr_series_summary.csv`
- `processed_observations/taupe_tdr_observation_operator_summary.json`
- `processed_observations/taupe_tdr_observation_operator.md`
- `scripts/build_taupe_semantics_audit.py`
- `processed_observations/taupe_tdr_semantics_row_audit.csv`
- `processed_observations/taupe_tdr_semantics_series_audit.csv`
- `processed_observations/taupe_tdr_semantics_group_summary.csv`
- `processed_observations/taupe_tdr_semantics_summary.json`
- `processed_observations/taupe_tdr_semantics.md`
- `scripts/build_taupe_candidate_discrimination_audit.py`
- `taupe_candidate_discrimination_audit.csv`
- `taupe_candidate_discrimination_series.csv`
- `taupe_candidate_discrimination_summary.json`
- `taupe_candidate_discrimination.md`

Run after the processed observation tables and mesh lookup exist:

```bash
python inversion_workflow/scripts/build_taupe_observation_operator.py
```

Use the Python environment that has `meshio` installed, because the script reads the
OGS `n_rd` porosity field from the VTU mesh.

This builder makes the usable part of Taupe/TDR explicit without overclaiming the
absolute unit.  It creates baseline-normalized anomalies for each sensor/EDZ-band
series and links them to the mapped Taupe line-sample bands and OGS `n_rd` porosity
field.  The model-side comparison quantity is the change in band-averaged
`theta_model = porosity * liquid_saturation` relative to the same series baseline.

Current Taupe/TDR result:

```text
operator rows: 5088
sensor/EDZ-band series: 24
mapped trend rows: 2544
date range: 2019-12-01 to 2025-10-10
direct-run compared trend rows: 1860 across 12 A3/A4 series
direct-run standardized trend MAE: 1.8632
recommended role: trend diagnostic, not active absolute saturation likelihood
```

The operator also records candidate absolute conversions: value as volumetric
water-content percent, Topp-style dielectric water content, and the local linear
dielectric mixing expression.  Those columns are sanity checks only; absolute Taupe
residual weights remain blocked until the workbook unit or sensor-specific
calibration is confirmed.

The semantics audit adds the explicit activation split used by the likelihood
documentation: 2,544 A3/A4 rows are trend-diagnostic-ready after OGS state outputs
exist, 2,544 A7/A8 rows are outside the current local mesh support, and all 5,088
Taupe/TDR state-target rows remain inactive as absolute water-content/saturation
residuals until the Taupe unit/calibration is confirmed.

The run-local diagnostic script
`scripts/evaluate_taupe_tdr_trend_diagnostic.py` now compares the mapped A3/A4
Taupe trend rows with sampled OGS
`theta_model = porosity * liquid_saturation`.  For the direct reference run it
writes `runs/direct_fit_observation_run/taupe_tdr_trend_diagnostic.*`, compares
1,860 rows over 12 series, leaves 684 mapped rows outside the current OGS output
time horizon, and keeps all A7/A8 rows outside the current mesh support.  This is a
candidate screen only; it is not assembled into the active objective.

The cross-run audit
`scripts/build_taupe_candidate_discrimination_audit.py` reuses that diagnostic for
all existing runs with `ogs_state_samples.csv`.  It currently audits 74 runs, of
which 66 have the full active combined objective.  The Taupe standardized-trend MAE
varies only by 0.03687076560014302 across the executed candidate family.  The
Taupe-only best run is `adaptive_combined_001_length_0p050m` with MAE
1.829884354078035; the best active-objective run is
`local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` with Taupe MAE
1.863211058631399.  This is weak discrimination evidence for the current candidate
family, so Taupe remains a diagnostic screen until both the calibration gate and a
candidate family capable of moving the Taupe signal are available.

## RH Boundary-Curve Audit

- `scripts/audit_rh_boundary_curve.py`
- `runs/direct_fit_observation_run/rh_boundary_curve_audit.csv`
- `runs/direct_fit_observation_run/rh_boundary_curve_audit_summary.json`
- `scripts/build_rh_semantics_audit.py`
- `processed_observations/rh_measurement_semantics_row_audit.csv`
- `processed_observations/rh_measurement_semantics_sensor_summary.csv`
- `processed_observations/rh_boundary_curve_semantics.csv`
- `processed_observations/rh_measurement_semantics_summary.json`
- `processed_observations/rh_measurement_semantics.md`
- `scripts/build_rh_boundary_provenance_request.py`
- `processed_observations/rh_boundary_provenance_request.csv`
- `processed_observations/rh_boundary_provenance_evidence.csv`
- `processed_observations/rh_boundary_provenance_request_summary.json`
- `processed_observations/rh_boundary_provenance_request.md`
- `scripts/build_rh_boundary_candidate_curves.py`
- `processed_observations/rh_boundary_candidate_curves.csv`
- `processed_observations/rh_boundary_candidate_curve_summary.csv`
- `processed_observations/rh_boundary_candidate_curve_summary.json`
- `processed_observations/rh_boundary_candidate_curves.md`
- `processed_observations/rh_boundary_candidate_curve_xml/`
- `scripts/build_rh_boundary_uncertainty_audit.py`
- `processed_observations/rh_boundary_uncertainty_envelope.csv`
- `processed_observations/rh_boundary_uncertainty_audit.csv`
- `processed_observations/rh_boundary_uncertainty_summary.json`
- `processed_observations/rh_boundary_uncertainty.md`

The open-niche pressure boundary is already represented in the OGS model through the
active include in `08_curves.xml`:

```text
08_08_open_niche_seasonal.xml
```

Run the RH audit after the processed RH table exists:

```bash
python inversion_workflow/scripts/audit_rh_boundary_curve.py
```

The audit uses model time origin `2019-09-18T00:00:00`, matching the model timestep
comment in `05_1_fixed_timestepping.xml`, and interpolates the active OGS curve onto
the RH measurement dates.  Current result:

```text
RH Kelvin rows: 4247
active OGS curve rows: 845
RH rows compared inside active curve time range: 2280
rows after active curve time range: 1948
low-RH outlier rows excluded: 19
median absolute residual, RH Kelvin pressure minus OGS curve: 13.00 MPa
mean absolute residual: 16.32 MPa
```

The residual is large enough that the current OGS curve should be treated as an
existing model boundary condition requiring provenance/audit, not as a verified direct
reconstruction of the collected OT_RH5--8 workbooks.  RH5/RH6 are the cleaner sensors
for this check; RH7/RH8 contain low or suspicious values and keep their processed
quality flags.

The RH semantics audit adds the row-level activation gates and curve-implied RH
diagnostics:

```text
valid non-low-outlier RH rows: 4228
low-RH outliers: 19
open-twin >95% RH caution rows: 2492
preferred open-twin range rows: 1736
active-curve implied RH range: 70.23% to 96.59%
active-curve rows below clean RH5/RH6 minimum: 772 of 845
```

Therefore RH can be used as boundary-condition evidence and retention validation
context, but the active open-niche curve should not be locked as a verified forcing
until its generation or preprocessing is reconstructed.

The provenance request builder turns that caveat into an email-ready package:

```bash
python inversion_workflow/scripts/build_rh_boundary_provenance_request.py
```

It writes six request rows and ten evidence rows, with local catalogue copies under
`cda_knowledge_base/measurements/suction_relative_humidity/derived_files`.  The
requests cover active curve generation, time-range extension, sensor selection,
Kelvin conversion constants, open/closed curve mapping, and the retention-parameter
release gate.  The generated summary records that the active curve spans 2019-09-18
to 2023-12-26 in model time, while the copied RH workbooks continue to 2025-09-04.

The local candidate-curve builder creates reproducible RH-derived boundary histories
from the copied sensors:

```bash
python inversion_workflow/scripts/build_rh_boundary_candidate_curves.py
```

It writes six candidate policies and matching OGS-style XML snippets.  The
policy-preferred curve is `rh5_rh6_median`, because RH5/RH6 are the cleanest copied
open-twin thermo-hygrometer streams.  That candidate has 1,063 daily rows from
2021-12-16 to 2025-09-04, including 576 overlap rows against the active curve and
487 rows after the active curve ends.  Its overlap MAE against the active curve is
15.15 MPa.  These curves are candidate forcings and extension evidence only: they
must not replace `08_08_open_niche_seasonal.xml` until BGR/Gesa confirm the active
curve provenance, time axis, sensor-selection rule, Kelvin constants, and extension
policy.

The candidate-envelope audit compares those six local policies day by day:

```bash
python inversion_workflow/scripts/build_rh_boundary_uncertainty_audit.py
```

It writes 1,064 envelope dates: 577 overlap the active curve and 487 extend beyond
it.  In the overlap, the local RH-derived pressure-envelope width is 2.10 MPa at
p50 and 2.20 MPa at p90.  The active curve sits outside that local envelope on 575
of 577 overlap dates and differs from the envelope median by 15.22 MPa MAE.  This
quantifies the boundary uncertainty gate; it still does not make RH a likelihood
term.

## Mesh Observation Lookup

- `scripts/build_mesh_observation_lookup.py`
- `processed_observations/measurement_mesh_lookup.csv`
- `processed_observations/borehole_mesh_lookup.csv`
- `processed_observations/borehole_line_mesh_samples.csv`
- `processed_observations/ogs_bulk_mesh_cells.csv`
- `processed_observations/mesh_lookup_summary.json`

Run from `SOTA_OGS_Mont_Terri_work`:

```bash
/home/ber0061/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  inversion_workflow/scripts/build_mesh_observation_lookup.py
```

The lookup script parses the ASCII VTU bulk mesh directly, computes triangle
centroids, and maps catalogue points to either a containing triangle or a nearest-cell
fallback.  It also converts BGR model coordinates from the
`Coordinates_NMR_Taupe_characborehole.xlsx` workbook into the 2D model frame using the
same offset visible in `2025-09-05_Mess_Koord_XY.xlsx`:

```text
model x = BGR X + 4.63
model y = BGR Z - 1.28
```

Current lookup result:

```text
bulk mesh: 20,873 points, 10,239 triangle6 cells, x/y bounds -5 m to 5 m
measurement_mesh_lookup.csv: 107 rows
  inside_cell: 41
  inside mesh bounding box, nearest-cell fallback: 16
  outside mesh bounding box, nearest-cell fallback: 50
borehole_mesh_lookup.csv: 35 endpoint rows
borehole_line_mesh_samples.csv: 341 samples on 8 borehole/Taupe segments
```

The outside/fallback flags are important.  They identify measurements or intervals
that are outside the local OGS Niche-4 domain or inside geometric holes/openings, and
therefore require an explicit observation-operator decision before fitting.

## State Observation Targets

- `scripts/build_state_observation_targets.py`
- `processed_observations/state_observation_targets.csv`
- `processed_observations/state_observation_samples.csv`
- `processed_observations/state_observation_target_summary.json`

Run after the mesh lookup:

```bash
python inversion_workflow/scripts/build_state_observation_targets.py
```

This builder turns the non-permeability measurement tables into explicit target rows
for later OGS state comparison:

```text
state_observation_targets.csv: 11490 rows
state_observation_samples.csv: 11311 rows
NMR weekly targets: 170 rows, all mapped to NMR_4E or NMR_S lookup cells
NMR seasonal targets: 294 rows, 117 mapped in the current Niche-4 mesh
Suction/RH targets: 4247 Kelvin-pressure boundary-forcing rows
Taupe/TDR targets: 5088 EDZ-band rows, with a separate baseline-normalized trend operator
ERT targets: 1691 open-niche field-comparison rows, 1675 with matching ERT VTK
```

The target layer deliberately keeps the measurement semantics separate.  NMR compares
to model `porosity * saturation` only after the bound-water sensitivity audit is
applied; the current audit rules out a naive absolute mobile-water residual because
162 of 287 usable mapped NMR rows exceed fixed porosity before correction.  RH is a
time-dependent boundary or retention-validation target, not a cell sample; Taupe/TDR
is mapped to borehole line-sample bands and has a trend operator, but absolute unit
conversion is still pending; ERT is represented as an external field-projection
target with a run-local log-resistivity diagnostic, not a weighted objective term.
The Taupe trend artifact is explicit in `taupe_tdr_trend_operator.csv`; the ERT
calibration, projection, and diagnostic parts are explicit in
`ert_water_content_resistivity_operator.csv`, `ert_spatial_projection_lookup.csv`,
and `ert_resistivity_diagnostic.md`.

## State Observation Evaluation and Combined Objective

- `scripts/evaluate_state_observation_targets.py`
- `scripts/assemble_inversion_objective.py`
- `runs/direct_fit_observation_run/state_observation_evaluation.csv`
- `runs/direct_fit_observation_run/state_observation_evaluation_summary.json`
- `runs/direct_fit_observation_run/combined_objective_components.csv`
- `runs/direct_fit_observation_run/combined_objective_summary.json`

After OGS output files are sampled with `sample_ogs_state_outputs.py`, evaluate the
state-observation target layer with:

```bash
python inversion_workflow/scripts/evaluate_state_observation_targets.py
python inversion_workflow/scripts/assemble_inversion_objective.py
```

The current direct-fit observation run has completed through Dockerized Apptainer.
The sampler reads the fixed support-mesh porosity field `n_rd` when OGS output VTUs
omit porosity, so NMR water-content rows can be evaluated as
`theta_model = porosity * saturation` where output times and mapped support are
usable:

```text
state_observation_evaluation.csv: 11490 rows
evaluation status counts:
  boundary_forcing_target_no_state_residual: 4247
  evaluated: 192
  external_projection_required: 1691
  outside_time_tolerance: 95
  target_not_usable_for_current_state_fit: 5265
OGS output VTU files: 83
sampled state rows: 37184
state objective rows: 192
state objective value: 2886.54
```

For the direct cell-fit diagnostic run, the combined objective currently includes
both the direct permeability pulse-test component and the sampled NMR state component:

```text
active objective components: 2 of 2
direct permeability rows: 75, effective weight 52
direct permeability objective: 269.82
state-observation candidate rows: 11490, sampled OGS state rows 37184, active rows 192
state-observation objective: 2886.54
combined active objective: 3156.36
```

## Measurement Operator Coverage Audit

- `scripts/build_measurement_operator_coverage.py`
- `measurement_operator_coverage.csv`
- `measurement_operator_coverage_summary.json`
- `measurement_operator_coverage.md`

Run after the processed observation tables, mesh lookup, target builders, RH audit,
and candidate evaluation have been refreshed:

```bash
/home/ber0061/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  inversion_workflow/scripts/build_measurement_operator_coverage.py
```

The audit is a compact readiness map for the measurement streams.  It does not decide
scientific adequacy; it records whether each stream has entered the current frozen
OGS workflow as an active objective, a state residual waiting for OGS outputs, a
boundary-forcing audit, a diagnostic target, or support data.

Current coverage for the best executed lower-support loop OGS candidate
`lower_support_loop_001_001_length_0p003m_shift_1p006`:

```text
observation groups: 9
active objective groups now: 2
current active objective: 3156.37
active objective source: direct permeability pulse-test targets plus sampled NMR rows
NMR: active where complete OGS outputs cover usable observation times and support quantities
ERT: calibration, spatial lookup, direct-run diagnostic, and 66-run candidate audit ready under explicit transform/support assumptions; cross-run MAE range is 0.019635573360798686 log10 units, pending coordinate/support/uncertainty confirmation
Taupe/TDR: baseline-normalized trend operator ready; 74-run candidate audit gives MAE range 0.03687076560014302, so current candidate family weakly discriminates Taupe and absolute unit/calibration remains pending
RH: converted to Kelvin pressure and audited as boundary forcing, not a point residual
coordinates/geometry, bedding, and model projection: support layers ready
other HM: Tecplot layout, levelling summary, qualitative validation gates, and missing-export request package ready; Geoscope/laser-scan raw exports missing
```

## Measurement Model-Entry Matrix

- `scripts/build_measurement_model_entry_matrix.py`
- `measurement_model_entry_matrix.csv`
- `measurement_model_entry_matrix_summary.json`
- `measurement_model_entry_matrix.md`

Run after the coverage, likelihood, stream-gate, and final objective decision
tables have been refreshed:

```bash
python inversion_workflow/scripts/build_measurement_model_entry_matrix.py
```

This matrix is the compact per-measurement bridge from the source catalogue to the
current frozen OGS workflow. It keeps all nine measurement classes in view and records
the current entry class, residual or support role, active row count, allowed use,
blocker, include/exclude consequence, and link to the matching
`cda_knowledge_base/measurements_info/*/MEASUREMENT_INFO.md` note.

Current result:

```text
measurement classes: 9
active measurement classes: 2
active objective rows: 267
diagnostic/boundary classes: 3
support/prior classes: 3
not-ready hard-residual classes: 1
```

## Measurement Likelihood And Activation Model

- `scripts/build_measurement_likelihood_model.py`
- `measurement_likelihood_model.csv`
- `measurement_likelihood_model_summary.json`
- `measurement_likelihood_model.md`

Run after the target builders, operator builders, RH audit, and current candidate
evaluation:

```bash
python inversion_workflow/scripts/build_measurement_likelihood_model.py
```

This artifact is stricter than the coverage audit.  It records the residual form,
transform, current scale/weighting rule, bias or model-error terms, and activation
gate for each measurement stream.  The current result has 7 streams, with direct
permeability pulse tests and sampled NMR rows active now:

```text
measurement streams: 7
active streams now: 2
total current objective rows: 267
current active objective: 3156.37
```

The important scientific guardrails are explicit: direct permeability remains the
recorded broad log10 intrinsic-permeability likelihood, but the likelihood-policy
audit shows that repeated support-cell conflicts dominate the active Gaussian row
loss and the support lower-bound audit shows the current field already reaches the
single-support lower bound for the current support map. These conflicts must not be
silently hidden by a robust or aggregated policy; NMR needs
the generated bound-water sensitivity and 66-run candidate bias/anomaly audits, and
likely a trend/anomaly residual or label/campaign bias term, before absolute
water-content residuals are trusted; ERT and Taupe/TDR are forward
observation operators rather than direct saturation measurements; RH audits
boundary-condition provenance; and the other HM streams remain validation gates until
their numerical time series are located.

## Inversion Parameter Release Plan

- `scripts/build_inversion_parameter_release_plan.py`
- `scripts/audit_thermal_expansivity_parameter.py`
- `scripts/build_cte_confirmation_request.py`
- `thermal_expansivity_parameter_audit.csv`
- `thermal_expansivity_parameter_audit_summary.json`
- `thermal_expansivity_parameter_audit.md`
- `cte_confirmation_request.csv`
- `cte_confirmation_request_summary.json`
- `cte_confirmation_request.md`
- `inversion_parameter_release_plan.csv`
- `inversion_parameter_release_plan_summary.json`
- `inversion_parameter_release_plan.md`

Run after the measurement likelihood model and regularized candidate-set handoff have
been refreshed:

```bash
python inversion_workflow/scripts/build_inversion_parameter_release_plan.py
```

This audit cross-checks the base OGS XML, the projection XML, the selected
regularized run XML, the measurement likelihood model, and the current OGS candidate
set.  It records which parameters can be released now and which must remain fixed
until the residual-policy, support, stream, or provenance gates are approved.

Current decision:

```text
release-plan rows: 14
stage-1 active field: intrinsic permeability tensor magnitude field k_i_rd
active objective: direct permeability plus sampled NMR state residuals
current objective: 3156.353066948979 = 269.8180571059851 direct + 2886.535009842994 sampled state
state rows/times: 192 NMR rows from 83 OGS output times
stage-1 fixed support field: porosity n_rd, final NMR policy not selected
stage-2 scalar candidates: van Genuchten p_b and exponent, after NMR/RH gates
stage-3 mechanical candidates: elasticity and Biot, after numeric HM residuals
same-support active-objective batch executable now: false
provenance blockers: open-niche pressure curve and suspicious CTE value
```

The practical consequence is that the current inverse problem is not a free fit of
all XML constants.  The current executable OGS comparison varies only `k_i_rd`
magnitude fields.  Sampled NMR residuals are active in the objective, but porosity,
retention, tensor-shape, elasticity, swelling, thermal/fluid constants, and
initialization remain fixed until the gate conditions in
`inversion_parameter_release_plan.md` are met.  More same-support OGS sampling is
paused until support, likelihood, bounds, or stream-gate evidence changes.

The thermal-expansivity audit parses the active OGS XML binding and confirms that
`CTE = 1254.74` is bound to the solid `thermal_expansivity` property, while the same
numeric value is also used by `c_p_s`. The XML comment uses heat-capacity-like units,
whereas the OGS property role is a coefficient in `1/K`. Against the cited HE-D
solid thermal-expansion range of `1.0e-5` to `2.6e-5 1/K`, the active value is
`4.83e7` times too large at the high end. It remains a confirmation blocker, not a
calibration target.

The CTE confirmation request package turns that blocker into an outbound model-
provenance question. It has status
`cte_confirmation_gmail_draft_created_waiting_user_send_and_response`, routes the
draft to `Gesa.Ziefle@bgr.de` with `Tuanny.Cajuhi@bgr.de` as suggested CC, and asks
whether `CTE=1254.74` is an intended `1/K` thermal-expansivity value, a copy of
`c_p_s`, inactive in the intended run, or another unit/convention. Gmail draft
`r2947727639429158073` exists but is not sent. It does not modify the frozen model
and does not close the blocker until a provider response is recorded.

## Inversion Release Gate Audit

- `scripts/audit_inversion_release_gates.py`
- `inversion_release_gate_audit.csv`
- `inversion_release_gate_audit.json`
- `inversion_release_gate_audit.md`
- per-run `INVERSION_RELEASE_GATE_AUDIT.*` files written by `evaluate_inversion_candidate.py`

Run after prepared OGS candidate directories exist:

```bash
python inversion_workflow/scripts/audit_inversion_release_gates.py \
  --run-dir inversion_workflow/runs/regularized_ogs_candidate_001_length_0p025m \
  --run-dir inversion_workflow/runs/regularized_ogs_candidate_002_length_0p025m_shift_0p750 \
  --run-dir inversion_workflow/runs/regularized_ogs_candidate_003_length_0p025m_shift_0p500 \
  --run-dir inversion_workflow/runs/adaptive_combined_001_length_0p050m \
  --run-dir inversion_workflow/runs/adaptive_combined_002_length_0p050m_shift_0p750 \
  --run-dir inversion_workflow/runs/adaptive_combined_003_length_0p075m \
  --run-dir inversion_workflow/runs/local_refined_001_length_0p013m \
  --run-dir inversion_workflow/runs/local_refined_002_length_0p019m \
  --run-dir inversion_workflow/runs/local_bracketed_001_length_0p013m_shift_0p875 \
  --run-dir inversion_workflow/runs/local_bracketed_002_length_0p013m_shift_1p125 \
  --run-dir inversion_workflow/runs/local_bracketed_003_length_0p031m \
  --run-dir inversion_workflow/runs/optimizer_proposed_001_length_0p019m_shift_1p125 \
  --run-dir inversion_workflow/runs/optimizer_proposed_002_length_0p019m_shift_0p875 \
  --run-dir inversion_workflow/runs/optimizer_proposed_003_length_0p025m_shift_1p125 \
  --run-dir inversion_workflow/runs/continuous_proposed_001_length_0p006m_shift_0p992 \
  --run-dir inversion_workflow/runs/continuous_proposed_002_length_0p007m \
  --run-dir inversion_workflow/runs/continuous_proposed_003_length_0p007m_shift_0p972 \
  --run-dir inversion_workflow/runs/lower_support_continuous_001_length_0p004m_shift_0p995 \
  --run-dir inversion_workflow/runs/lower_support_continuous_002_length_0p003m_shift_0p986 \
  --run-dir inversion_workflow/runs/lower_support_continuous_003_length_0p004m_shift_0p994 \
  --run-dir inversion_workflow/runs/lower_support_loop_001_001_length_0p003m_shift_1p006 \
  --run-dir inversion_workflow/runs/lower_support_loop_001_002_length_0p005m_shift_0p985 \
  --run-dir inversion_workflow/runs/lower_support_loop_001_003_length_0p004m_shift_1p014 \
  --run-dir inversion_workflow/runs/lower_support_loop_002_001_length_0p004m_shift_0p992 \
  --run-dir inversion_workflow/runs/lower_support_loop_002_002_length_0p004m_shift_1p020 \
  --run-dir inversion_workflow/runs/lower_support_loop_002_003_length_0p006m_shift_0p975 \
  --run-dir inversion_workflow/runs/broad_continuous_001_001_length_0p023m_shift_1p004 \
  --run-dir inversion_workflow/runs/broad_continuous_001_002_length_0p022m_shift_0p998 \
  --run-dir inversion_workflow/runs/broad_continuous_001_003_length_0p021m \
  --run-dir inversion_workflow/runs/broad_continuous_loop_001_001_length_0p015m \
  --run-dir inversion_workflow/runs/broad_continuous_loop_001_002_length_0p016m_shift_0p968 \
  --run-dir inversion_workflow/runs/broad_continuous_loop_001_003_length_0p010m
```

The gate turns the release plan into an executable guard.  It checks that prepared
runs still use `k_i` as `MeshElement` field `k_i_rd`, keep `phi` as fixed support
field `n_rd = 0.105`, preserve the projection XML definitions for parameters and
media/retention properties, and only change output variables or candidate mesh fields
allowed by the current stage.

Current gate result for the three regularized OGS candidate runs, the first three
adaptive candidate runs, the two local-refinement candidate runs, the three
local-bracketing candidate runs, the three optimizer-proposed candidate runs, the
three continuous-proposed, three lower-support continuous, six lower-support loop,
six broad continuous candidate runs, the three local-basis candidate runs, and the
thirty production sampler candidate runs:

```text
runs audited: 65
checks: 1300
failures: 0
warnings: 0
status: pass
```

## Frozen Model and Measurement-Inclusion Audit

- `scripts/build_frozen_model_measurement_inclusion_audit.py`
- `frozen_model_measurement_inclusion_audit.csv`
- `frozen_model_measurement_inclusion_audit_summary.json`
- `frozen_model_measurement_inclusion_audit.md`

Run after refreshing the measurement-info mirror, release gates, current field
package, and promotion checklist:

```bash
python inversion_workflow/scripts/build_frozen_model_measurement_inclusion_audit.py
```

This audit is the compact evidence bridge between the frozen source model, the
run-local candidate meshes, and the measurement catalogue. It currently passes
13 checks with zero failures, verifies 75 `RUN_MANIFEST.json` files against the
recovered projection model, reads the 65-run release gate with 1300 passing
checks, confirms that the packaged current field has 10239/10239 positive-definite
cells, verifies the current-field reproducibility audit, and verifies the
measurement-info mirror indexes 206 source files, 1880 archive members, and 34
workbook sheets.

The audit is also an overclaiming guard. It passes because the workflow keeps the
current field labelled as an active-objective incumbent and preserves the final
promotion blockers for ERT, Taupe/TDR, RH, other-HM, permeability endpoint
geometry, and CTE provenance.

The current field package now also includes a reproducibility snapshot:
`current_permeability_field/ogs_run_inputs/` contains the run-local OGS project,
XML includes, meshes, and seasonal curves for the executed incumbent, while
`current_permeability_field/packaged_file_manifest.csv` records SHA256 checksums for
the packaged field, direct and sampled-NMR residual tables, audits, summaries, and
input snapshot.  `CURRENT_FIELD_REPRODUCIBILITY_AUDIT.md` verifies those package,
manifest, snapshot, objective, release-gate, execution, and field checks as a single
gate.  This makes the accepted active-objective field inspectable and rerunnable
without modifying the frozen source model.

## Direct Permeability Targets

- `scripts/build_permeability_observation_targets.py`
- `scripts/build_permeability_endpoint_geometry_request.py`
- `processed_observations/permeability_observation_targets.csv`
- `processed_observations/permeability_observation_cells.csv`
- `processed_observations/permeability_segment_geometry.csv`
- `processed_observations/permeability_missing_geometry_audit.csv`
- `processed_observations/permeability_missing_geometry_audit.md`
- `processed_observations/permeability_endpoint_geometry_request.csv`
- `processed_observations/permeability_endpoint_geometry_blocked_rows.csv`
- `processed_observations/permeability_endpoint_geometry_request_summary.json`
- `processed_observations/permeability_endpoint_geometry_request.md`
- `processed_observations/permeability_measurement_semantics_audit.csv`
- `processed_observations/permeability_measurement_semantics_group_summary.csv`
- `processed_observations/permeability_measurement_semantics_summary.json`
- `processed_observations/permeability_measurement_semantics.md`
- `processed_observations/permeability_target_summary.json`

Run after the mesh lookup:

```bash
/home/ber0061/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  inversion_workflow/scripts/build_permeability_observation_targets.py
```

The target builder maps interpreted pulse-test rows to 10 cm along-borehole intervals
where segment geometry is available.  It does not reinterpret the gas pulse-test
scalar as a tensor component.  It records the value as a noisy interval-scale
constraint on intrinsic permeability, with the borehole tangent and sampled cell IDs
available for a later sensitivity/averaging operator.

Current status:

```text
permeability_observation_targets.csv: 204 rows
usable for current local OGS fit: 75 rows
mapped outside current mesh and excluded from first fit: 27 rows
missing segment geometry: 98 rows
missing-geometry audit groups: 5
missing-geometry rows with source-backed orientation evidence: 98
missing/non-positive interpreted permeability: 4 rows
```

The 75 initial direct constraints come from the in-mesh BCD-A32 and BCD-A33 rows.
The BCD-A34/35 rows are retained but excluded because their closed-twin geometry maps
outside the current local mesh.  Older BCD-A24/25/26/27 and BFM-D19 rows are now
catalogued in `permeability_missing_geometry_audit.md`: their vertical/horizontal
orientation evidence is retained from the characterization paper, but they still
need matching endpoint geometry or an explicitly approved digitized trace before
they can become interval cell targets.

Run the endpoint request builder after rebuilding targets when this external
geometry gap needs to be followed up:

```bash
python inversion_workflow/scripts/build_permeability_endpoint_geometry_request.py
```

It writes a five-row request table and a 98-row blocked-observation table.  The
request asks for labelled start/end coordinates for BCD-A24, BCD-A25, BCD-A26,
BCD-A27, and BFM-D19 in the same local/model frame as the coordinate workbook and
OGS projection, plus the depth-zero and interval-position convention.  It also
copies the request package into the permeability catalogue derived-files folder.
No historical row is activated by this package; it only makes the external geometry
request explicit.

Run the semantics audit after rebuilding targets:

```bash
python inversion_workflow/scripts/build_permeability_semantics_audit.py
```

The audit records the physical interpretation gate for each row.  Current counts are
204 interpreted rows, 200 positive rows, 75 active direct candidates, 27 outside-mesh
rows, and 98 rows blocked by missing endpoint geometry.  The usable direct rows are
only BCD-A32 and BCD-A33 in the current mesh.  The audit also records the modelling
rule used by the likelihood: a nitrogen pulse-decay row is a noisy scalar interval
observation of intrinsic permeability and must be compared in log space to an
interval-weighted directional tensor response, not to hydraulic conductivity,
saturation, liquid relative permeability, or a single tensor component.

## Permeability Target Evaluation

- `scripts/evaluate_permeability_targets.py`
- `runs/<run-id>/permeability_fit_evaluation.csv`
- `runs/<run-id>/permeability_fit_summary.json`

Run after preparing a mesh-field run directory and building permeability targets:

```bash
python inversion_workflow/scripts/evaluate_permeability_targets.py \
  --mesh inversion_workflow/runs/smoke_test/bulk_w_projections.vtu \
  --include-non-usable
```

The evaluator reads the generated `k_i_rd` cell-data field and computes the
directional effective permeability \(e^T K e\) for each mapped pulse-test interval.
It compares predicted and observed values in log10 space and uses duplicate-aware
objective weights so the September workbook and the consolidated workbook do not
double-weight identical 2024 interval values.

Current smoke-test result for the prior/proposal field generated by
`run_config.example.json`:

```text
used objective rows: 75
effective objective weight after duplicate handling: 52
weighted RMSE: 2.70 log10(k) units
objective value with sigma=0.5 log10 units: 756.95
best single global log10 shift: +1.2285
best single global permeability multiplier: 16.92
weighted RMSE after that global shift: 2.40 log10(k) units
```

This is a baseline diagnostic, not a calibrated inversion.  The result shows that a
single global multiplier is insufficient; the direct permeability data require a
heterogeneous field with strong local high-permeability intervals.

## Direct Permeability Field Fit Diagnostic

- `scripts/fit_permeability_field_from_targets.py`
- `runs/direct_permeability_fit/bulk_w_projections.vtu`
- `runs/direct_permeability_fit/permeability_direct_fit_targets.csv`
- `runs/direct_permeability_fit/permeability_direct_fit_cells.csv`
- `runs/direct_permeability_fit/permeability_direct_fit_summary.json`

Run from `SOTA_OGS_Mont_Terri_work` after the smoke-test field and permeability
target layer exist:

```bash
python inversion_workflow/scripts/fit_permeability_field_from_targets.py
python inversion_workflow/scripts/evaluate_permeability_targets.py \
  --mesh inversion_workflow/runs/direct_permeability_fit/bulk_w_projections.vtu \
  --include-non-usable \
  --output inversion_workflow/runs/direct_permeability_fit/permeability_fit_evaluation.csv \
  --summary-output inversion_workflow/runs/direct_permeability_fit/permeability_fit_summary.json
```

The direct-fit script is deliberately limited.  It computes a duplicate-aware
log10 permeability multiplier for each selected target cell, scales the existing
tensor by that scalar, preserves the tensor orientation/anisotropy, and writes
diagnostic cell fields:

```text
k_fit_requested_log10_multiplier_rd
k_fit_applied_log10_multiplier_rd
k_fit_anchor_weight_rd
k_fit_anchor_count_rd
```

Current direct-fit result:

```text
usable target rows: 75
adjusted cells: 30
effective objective weight: 52
weighted RMSE before fit: 2.70 log10(k) units
weighted RMSE after direct cell fit: 1.61 log10(k) units
objective value after fit with sigma=0.5 log10 units: 269.82
applied log10 multiplier range: -1.48 to +5.80
```

This is not yet a production inversion field.  It is a traceable diagnostic showing
where the mapped pulse-test data force strong local permeability corrections.  The
remaining residual is expected because several interpreted values collapse onto the
same finite-element cell, some rows are duplicate measurements from different source
workbooks, and only the direct pulse-test target layer is included.

## Smooth Interval-Anchored Permeability Fit

- `scripts/fit_smooth_permeability_field_from_targets.py`
- `runs/smooth_permeability_fit/smooth_fit_results.csv`
- `runs/smooth_permeability_fit/SMOOTH_FIT_SUMMARY.json`
- `runs/smooth_permeability_fit/SMOOTH_FIT_SUMMARY.md`
- `runs/smooth_permeability_candidate_search/smooth_fit_results.csv`
- `runs/smooth_permeability_candidate_search/SMOOTH_FIT_SUMMARY.md`
- `runs/candidate_smooth_0p025m_search_driver/CANDIDATE_EVALUATION_SUMMARY.json`

The smooth fit is an intermediate parameterization between the random prior sweep and
the direct per-cell diagnostic.  It estimates duplicate-aware log10 multipliers at the
30 measured anchor cells, spreads them with a finite-cutoff Gaussian kernel, and
multiplies the existing tensor field by a scalar factor.  Tensor orientation and
anisotropy are preserved locally; only the tensor magnitude changes.

Current length-scale sweep:

```text
length scale  affected cells  weighted RMSE  objective
0.05 m        471             1.67           291.29
0.10 m        1052            1.88           368.82
0.20 m        2343            2.01           419.52
0.40 m        4738            2.06           441.83
0.80 m        8354            2.13           470.95
```

The extended candidate search also varies a shift-damping factor.  Its best direct
candidate uses a 0.025 m smoothing length with full target-derived shifts:

```text
candidate: length_0p025m
affected cells: 208
weighted RMSE: 1.61 log10(k)
direct objective: 269.97
applied log10 multiplier range: -1.48 to +5.80
```

This field is smoother than the direct 30-cell diagnostic but substantially more
localized than the earlier 0.05 m field.  It has been passed through the full
candidate driver as `candidate_smooth_0p025m_search_driver`, where the active
objective is 269.97 until OGS state outputs become available.  The damped-shift rows
in `smooth_permeability_candidate_search` are intentionally under-fit proposal
fields for later OGS/state-observation comparison, not the current direct best.

## Regularized Permeability Candidate Ranking

- `scripts/rank_regularized_permeability_candidates.py`
- `runs/regularized_permeability_candidate_ranking/REGULARIZED_CANDIDATE_RANKING.md`
- `runs/regularized_permeability_candidate_ranking/regularized_candidate_tradeoffs.csv`
- `runs/regularized_permeability_candidate_ranking/regularized_candidate_scenario_scores.csv`

Run after `smooth_permeability_candidate_search` has been regenerated:

```bash
python inversion_workflow/scripts/rank_regularized_permeability_candidates.py
```

This ranking separates direct pulse-test misfit from field-update complexity before
OGS state residuals are available.  It marks the Pareto tradeoff between direct
objective value and the sum of squared cell-wise log10 permeability updates, then
adds transparent weak/moderate/strong update-penalty scenarios.  The penalty is a
mesh-resolution-dependent selection aid, not a calibrated geological prior.

Current result:

```text
candidates ranked: 18
Pareto tradeoff candidates: length_0p025m, length_0p025m_shift_0p750, length_0p025m_shift_0p500
data-only winner: length_0p025m, objective 269.97, RMSE 1.61 log10(k)
moderate update-penalty winner: length_0p025m_shift_0p750, objective 301.16, RMSE 1.70 log10(k)
strong update-penalty winner: length_0p025m_shift_0p500, objective 392.72, RMSE 1.94 log10(k)
```

The practical recommendation is to carry at least the data-only winner and one damped
regularized winner into OGS-backed state-observation comparison.  That prevents the
first executable OGS pass from testing only the most aggressively fitted direct
permeability field.

## Regularized OGS Candidate Set

- `scripts/run_regularized_ogs_candidate_set.py`
- `runs/regularized_ogs_candidate_set/REGULARIZED_OGS_CANDIDATE_SET.md`
- `runs/regularized_ogs_candidate_set/regularized_ogs_candidate_set_results.csv`
- `runs/regularized_ogs_candidate_001_length_0p025m/`
- `runs/regularized_ogs_candidate_002_length_0p025m_shift_0p750/`
- `runs/regularized_ogs_candidate_003_length_0p025m_shift_0p500/`

Run after the regularized ranking exists:

```bash
python inversion_workflow/scripts/run_regularized_ogs_candidate_set.py --overwrite --ogs-mode execute ...
```

This script reads the Pareto/scenario winners from
`REGULARIZED_CANDIDATE_RANKING.json` and sends each selected field through the full
candidate harness: run-directory preparation, run-input audit, direct permeability
evaluation, OGS execution or command recording, state-output sampling, RH boundary audit,
state target evaluation, and combined objective assembly.

Current executed candidate comparison:

```text
length_0p025m: combined objective 3166.61, direct objective 269.97, state objective 2896.64, state active rows 192
length_0p025m_shift_0p750: combined objective 3198.49, direct objective 301.16, state objective 2897.33, state active rows 192
length_0p025m_shift_0p500: combined objective 3289.65, direct objective 392.72, state objective 2896.93, state active rows 192
release gate for all three: pass
run-input caveat for all three: copied boundary/support submeshes retain the same local meshio warning tracked by the direct-run audit
OGS output files for each candidate: 83
```

The NMR state objective is similar for the three selected fields, so this first
combined ranking is still driven mostly by the direct permeability term.  It is a
reproducible OGS-backed comparison, not yet a final inversion sampler.

## Adaptive Combined Candidate Plan

- `scripts/build_adaptive_combined_candidate_plan.py`
- `runs/adaptive_combined_candidate_plan/ADAPTIVE_COMBINED_CANDIDATE_PLAN.md`
- `runs/adaptive_combined_candidate_plan/ADAPTIVE_COMBINED_CANDIDATE_PLAN.json`
- `runs/adaptive_combined_candidate_plan/executed_candidate_evidence.csv`
- `runs/adaptive_combined_candidate_plan/next_candidate_batch.csv`
- `runs/adaptive_combined_candidate_plan/all_candidate_scores.csv`
- `runs/adaptive_combined_candidate_search/INVERSION_SEARCH_SUMMARY.md`
- `runs/adaptive_combined_candidate_search/inversion_candidate_search_results.csv`
- `runs/local_refinement_permeability_candidate_search/SMOOTH_FIT_SUMMARY.md`
- `runs/local_refinement_candidate_search/INVERSION_SEARCH_SUMMARY.md`
- `runs/local_refinement_candidate_search/inversion_candidate_search_results.csv`
- `runs/local_bracketing_candidate_search/INVERSION_SEARCH_SUMMARY.md`
- `runs/local_bracketing_candidate_search/inversion_candidate_search_results.csv`
- `runs/bayesian_candidate_proposal/OPTIMIZER_CANDIDATE_PROPOSAL.md`
- `runs/bayesian_candidate_proposal/next_optimizer_candidate_batch.csv`

Run after refreshing the regularized, adaptive, or local-refinement OGS candidate
sets:

```bash
python inversion_workflow/scripts/build_adaptive_combined_candidate_plan.py
```

This planner is not an optimizer.  It uses executed combined-objective evidence from
the regularized candidate set, adaptive candidate-search batches, and local-refinement
batches, plus the direct smooth-search tables, to select the next batch for the
existing candidate-search harness.

The first adaptive batch executed the top three broader-support proposals through
Dockerized Apptainer:

```text
length_0p050m: combined 3276.57, direct 291.29, state 2985.27, active NMR rows 192
length_0p050m_shift_0p750: combined 3300.91, direct 329.40, state 2971.51, active NMR rows 192
length_0p075m: combined 3353.88, direct 334.00, state 3019.88, active NMR rows 192
```

None of these beat the earlier `length_0p025m` combined objective of 3166.61.  The
state objective was no longer flat over that six-candidate set: it ranges from
2896.64 to 3019.88, so broader 0.05--0.075 m support appears to worsen the sampled
NMR residual layer for the current observation model.

The local-refinement grid around the 0.025 m support field then executed the top two
finer-support proposals:

```text
length_0p013m: combined 3159.66, direct 269.82, state 2889.85, active NMR rows 192
length_0p019m: combined 3164.96, direct 269.82, state 2895.14, active NMR rows 192
```

Both improve on the 0.025 m regularized result, and `length_0p013m` is the current
best executed smooth-field candidate.

The first local-bracketing batch then executed both shift directions around the 0.013 m
support and one wider full-shift support:

```text
length_0p013m_shift_1p125: combined 3167.21, direct 277.43, state 2889.78, active NMR rows 192
length_0p013m_shift_0p875: combined 3167.34, direct 277.43, state 2889.92, active NMR rows 192
length_0p031m: combined 3219.35, direct 271.39, state 2947.96, active NMR rows 192
```

None improves on `length_0p013m`.

The finite-candidate Bayesian proposal batch then executed three additional
candidate fields:

```text
length_0p019m_shift_0p875: combined 3172.37, direct 277.43, active NMR rows 192
length_0p019m_shift_1p125: combined 3172.69, direct 277.43, active NMR rows 192
length_0p025m_shift_1p125: combined 3173.39, direct 277.02, active NMR rows 192
```

These also fail to improve on `length_0p013m`.

The first continuous-proposal batch then executed the first three continuously
sampled smooth-field proposals:

```text
length_0p006m_shift_0p992: combined 3156.78, direct 269.85, active NMR rows 192
length_0p007m: combined 3157.74, direct 269.82, active NMR rows 192
length_0p007m_shift_0p972: combined 3158.16, direct 270.21, active NMR rows 192
```

The first continuous row improves on the previous `length_0p013m` best by about
2.88 active-objective units.

A lower-support continuous batch then tested the region below the original
continuous support lower bound:

```text
length_0p004m_shift_0p995: combined 3156.38, direct 269.83, active NMR rows 192
length_0p004m_shift_0p994: combined 3156.38, direct 269.84, active NMR rows 192
length_0p003m_shift_0p986: combined 3156.47, direct 269.91, active NMR rows 192
```

A repeatable lower-support loop then refreshed the local proposal, executed the next
three candidates, merged them into cumulative lower-support evidence, and refreshed
the planner:

```text
length_0p003m_shift_1p006: combined 3156.37, direct 269.84, active NMR rows 192
length_0p004m_shift_1p014: combined 3156.44, direct 269.91, active NMR rows 192
length_0p005m_shift_0p985: combined 3156.49, direct 269.93, active NMR rows 192
```

The second loop executed the next focused batch:

```text
length_0p004m_shift_0p992: combined 3156.40, direct 269.85, active NMR rows 192
length_0p004m_shift_1p020: combined 3156.53, direct 270.00, active NMR rows 192
length_0p006m_shift_0p975: combined 3156.70, direct 270.18, active NMR rows 192
```

It did not improve the incumbent.

The broad continuous evidence batch then tested the previous broad top proposals:

```text
length_0p023m_shift_1p004: combined 3159.06, direct 269.88, active NMR rows 192
length_0p022m_shift_0p998: combined 3169.30, direct 269.84, active NMR rows 192
length_0p021m: combined 3169.31, direct 269.83, active NMR rows 192
```

It did not improve the incumbent.

The repeatable broad continuous loop then executed the next broad proposal batch:

```text
length_0p010m: combined 3157.70, direct 269.82, active NMR rows 192
length_0p015m: combined 3161.36, direct 269.82, active NMR rows 192
length_0p016m_shift_0p968: combined 3165.33, direct 270.30, active NMR rows 192
```

It also did not improve the incumbent.

The current best executed smooth-family field is `length_0p003m_shift_1p006`; the
current best executed field overall is `basis_024_det_l_0p0075_s_1p000`. The
smooth-family planner still treats 32 executed smooth-family candidates as evidence.

Current proposed next batch:

```text
1. length_0p008m_shift_1p011, expected combined planning score 3159.70
2. length_0p007m_shift_1p020, expected combined planning score 3159.83
3. length_0p007m_shift_1p022, expected combined planning score 3159.87
4. length_0p004m_shift_1p031, expected combined planning score 3160.08
5. length_0p008m_shift_1p024, expected combined planning score 3159.92
6. length_0p010m_shift_1p011, expected combined planning score 3159.69
```

The expected combined score is only a surrogate, computed as direct objective plus
the median executed state objective.  The next evidence-producing step is either a
targeted batch that answers a specific remaining bracket question, or replacement of
the deterministic batch-selection logic with an optimizer/sampler.

## Finite-Candidate Bayesian Proposal

- `scripts/build_bayesian_candidate_proposal.py`
- `runs/bayesian_candidate_proposal/OPTIMIZER_CANDIDATE_PROPOSAL.md`
- `runs/bayesian_candidate_proposal/OPTIMIZER_CANDIDATE_PROPOSAL.json`
- `runs/bayesian_candidate_proposal/optimizer_candidate_scores.csv`
- `runs/bayesian_candidate_proposal/next_optimizer_candidate_batch.csv`

Run after regenerating the adaptive plan, because it uses
`all_candidate_scores.csv` and `executed_candidate_evidence.csv`:

```bash
python inversion_workflow/scripts/build_bayesian_candidate_proposal.py
```

This proposal layer now ranks the generated finite-grid and continuous-candidate
pool; it is still not a continuous inversion sampler. It fits a Gaussian-process
surrogate to the sampled NMR state objective for the 32 executed smooth-family OGS candidates
represented in the generated-candidate score table. Three historical lower-support
rows are reconstructed from executed search results because their original proposal
directories were overwritten. The known direct permeability objective is added for
each generated candidate field, and unexecuted candidates are ranked by lower
confidence bound. Current top remaining proposal:

```text
1. length_0p003m_shift_0p972, predicted combined 3156.77, LCB 3156.69
2. length_0p004m_shift_1p031, predicted combined 3156.79, LCB 3156.73
3. length_0p006m_shift_0p970, predicted combined 3156.84, LCB 3156.79
```

The probability-of-improvement values are effectively zero for these rows. The artifact is most useful as a transparent proposal; a production
inversion still needs a continuous optimizer/sampler loop and broader measurement
activation.

## Continuous Bayesian Candidate Plan

- `scripts/build_continuous_bayesian_candidate_plan.py`
- `runs/continuous_bayesian_candidate_plan/CONTINUOUS_CANDIDATE_PLAN.md`
- `runs/continuous_bayesian_candidate_plan/CONTINUOUS_CANDIDATE_PLAN.json`
- `runs/continuous_bayesian_candidate_plan/continuous_direct_candidate_scores.csv`
- `runs/continuous_bayesian_candidate_plan/continuous_optimizer_candidate_scores.csv`
- `runs/continuous_bayesian_candidate_plan/next_continuous_candidate_batch.csv`

Run after the adaptive plan and finite-candidate proposal are current:

```bash
python inversion_workflow/scripts/build_continuous_bayesian_candidate_plan.py --overwrite
```

This is the first proposal layer that leaves the pre-generated finite grid. It
samples continuous smooth-field support lengths and shift scales, writes run-local
`bulk_w_projections.vtu` meshes, evaluates the direct permeability objective for
each new field, and uses the current generated-table evidence intersection to
predict the sampled NMR state-objective term.
After each continuous batch, the same script excludes already executed continuous
candidates from its next batch.

Current output:

```text
continuous candidates generated: 136
training OGS candidates: 32
best executed candidate: length_0p003m_shift_1p006, combined 3156.37
top proposal: length_0p009m_shift_0p979, predicted combined 3158.11, LCB 3157.76
next batch: length_0p009m_shift_0p979, length_0p008m_shift_1p040, length_0p010m_shift_1p050
```

The already executed continuous and lower-support continuous batches are evidence. The
regenerated top continuous proposals are not evidence until they are executed through
OGS. Use the emitted batch table with the existing candidate-search driver:

```bash
python inversion_workflow/scripts/run_inversion_candidate_search.py \
  --candidate-table inversion_workflow/runs/continuous_bayesian_candidate_plan/next_continuous_candidate_batch.csv \
  --sort-column proposal_rank \
  --max-candidates 3 \
  --run-id-prefix continuous_proposed \
  --output-dir inversion_workflow/runs/continuous_candidate_search \
  --ogs-mode execute \
  --sif /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif \
  --docker-apptainer-image ghcr.io/apptainer/apptainer:latest \
  --docker-workspace-root /home/ber0061/Repositories/gesa_mails \
  --ogs-timeout-s 7200 \
  --overwrite
```

This continuous plan remains a smooth-family proposal bridge. The cross-family
production handoff is now tracked separately in
`runs/production_sampler_convergence/PRODUCTION_SAMPLER_CONVERGENCE.md`.

The lower-support continuous plan records the focused local search around the current
best:

```text
lower-support continuous candidates generated: 99
training OGS candidates: 32
best executed candidate: length_0p003m_shift_1p006, combined 3156.37
top local proposal: length_0p003m_shift_0p972, predicted combined 3156.76, LCB 3156.69
next local batch: length_0p003m_shift_0p972, length_0p004m_shift_1p031, length_0p006m_shift_0p970
```

The best focused lower-support probability of improvement is now about
`1.3e-08`, so this local family looks near a plateau.

## Direct Permeability Prior Sweep

- `scripts/run_direct_permeability_prior_sweep.py`
- `runs/direct_permeability_prior_sweep/sweep_results.csv`
- `runs/direct_permeability_prior_sweep/SWEEP_SUMMARY.json`

The sweep script generates heterogeneous anisotropic prior/proposal fields and ranks
them by the direct pulse-test objective before any OGS run is attempted.  It is useful
for separating two questions:

```text
Does a random heterogeneous prior already explain the direct permeability data?
Does the candidate mainly need a uniform scale shift, or is the spatial pattern wrong?
```

The verified 12-candidate sweep used the two usable pulse-test segment orientations
and the bedding-prior angle as tensor-angle candidates, with anisotropy ratios 1 and
2.5 and two geometric-mean permeability scales.  Current best generated prior:

```text
candidate: candidate_0009
theta: 144 deg
anisotropy ratio: 1.0
mean k_ref: 1.0e-18 m2
weighted RMSE: 2.41 log10(k) units
objective value: 605.00
best uniform-scale multiplier: 1.15
RMSE after uniform scale shift: 2.41 log10(k) units
```

This is better than the original smoke-test prior but still much worse than the
direct cell-fit diagnostic, which reaches RMSE 1.61 and objective 269.82.  The sweep
therefore supports the modelling interpretation: the pulse-test data require local
high-permeability structure tied to the measured intervals, not just a random
heterogeneous field or a global permeability multiplier.

## OGS-Ready Observation Run

- `scripts/prepare_ogs_run.py`
- `scripts/audit_ogs_run_inputs.py`
- `scripts/audit_ogs_environment.py`
- `scripts/run_ogs_model.py`
- `scripts/sample_ogs_state_outputs.py`
- `OGS_ENVIRONMENT_AUDIT.md`
- `runs/direct_fit_observation_run/`
- `runs/direct_fit_observation_run/RUN_MANIFEST.json`
- `runs/direct_fit_observation_run/OGS_RUN_INPUT_AUDIT.md`
- `runs/direct_fit_observation_run/OGS_EXECUTION_STATUS.json`
- `runs/direct_fit_observation_run/ogs_output_inventory.csv`
- `runs/direct_fit_observation_run/ogs_state_samples.csv`
- `runs/direct_fit_observation_run/ogs_state_sampling_summary.json`

The run-preparation script can now either generate a prior field from
`run_config.example.json` or use an existing fitted mesh as `bulk_w_projections.vtu`.
For the current direct-fit diagnostic field, the prepared OGS run directory was made
with:

```bash
python inversion_workflow/scripts/prepare_ogs_run.py \
  --run-id direct_fit_observation_run \
  --mesh-override inversion_workflow/runs/direct_permeability_fit/bulk_w_projections.vtu \
  --output-variables pressure saturation temperature displacement porosity
```

The output-variable edit is applied only inside the run copy of
`05_time_loop_TRM.xml`; it does not change the GESA source model or governing
equations.  These variables are the minimum practical set for later state-observation
operators:

```text
pressure      -> RH/suction and hydraulic-state checks
saturation    -> ERT/NMR/Taupe water-content observation operators
temperature   -> RH/Kelvin conversion and thermal boundary checks
displacement  -> HM/deformation validation
porosity      -> saturation-to-water-content conversion checks
```

The prepared run contains all required project files and the fitted mesh fields:

```text
k_i_rd: (10239, 4)
n_rd: (10239, 1)
k_fit_applied_log10_multiplier_rd: (10239, 1)
```

Run-input consistency is checked with:

```bash
python inversion_workflow/scripts/audit_ogs_run_inputs.py \
  --run-dir inversion_workflow/runs/direct_fit_observation_run
```

Current audit status is `run_inputs_ogs_accepted_with_meshio_submesh_warnings`.  The
project mesh files exist, process-variable mesh references resolve, required output
variables are requested, and `bulk_w_projections.vtu` contains `k_i_rd` and `n_rd`.
The enhanced audit also verifies VTU header integrity, confirms that the copied
boundary/support submeshes expose `bulk_node_ids` and `bulk_element_ids`, and records
that the Dockerized-Apptainer OGS execution accepted the inputs with return code 0.
However, `bulk_all.vtu` and the copied boundary/support VTUs still cannot be decoded
by `meshio` because their appended base64 data are not padded in a way that the local
tooling accepts.  Regenerate these submeshes with `identifySubdomains` if downstream
Python tooling must read them through `meshio`.

The local environment currently has no host `ogs` executable, but the file-transfer
catalogue contains a BGR/Gesa Apptainer image:

```text
cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif
```

The image metadata identifies `ogs/ogs@6.5.4
(cb5b3235101edecf3ba55e1039fe3c19bc13c636)` and places
`/usr/local/ogs/build/bin` on the container `PATH`.  Record and refresh host and
container execution status with:

```bash
python inversion_workflow/scripts/audit_ogs_environment.py
```

Current audit result:

```text
status: ogs_container_found_runtime_available
PATH lookup: not found
executable candidates: 0
selected container: apptainer_ogs6.5.4.sif
container version label: ogs/ogs@6.5.4 (cb5b3235101edecf3ba55e1039fe3c19bc13c636)
preferred backend: docker_apptainer_sif
runtime command: /usr/bin/docker
Dockerized Apptainer image: ghcr.io/apptainer/apptainer:latest
```

If a host OGS is installed outside those locations, re-run the audit with
`--candidate /path/to/ogs`.  If using the collected SIF directly, install Apptainer,
Singularity, or a `run-singularity` wrapper.  The current local backend uses Dockerized
Apptainer, so the collected SIF can be run by recording a command like:

```bash
python inversion_workflow/scripts/run_ogs_model.py \
  --run-dir inversion_workflow/runs/direct_fit_observation_run \
  --sif /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif \
  --docker-apptainer-image ghcr.io/apptainer/apptainer:latest \
  --docker-workspace-root /home/ber0061/Repositories/gesa_mails \
  --timeout-s 7200
```

Recorded command:

```bash
/usr/bin/timeout 7200 docker run --rm --privileged --user 1000:1000 \
  -v /etc/passwd:/etc/passwd:ro -v /etc/group:/etc/group:ro \
  -v /home/ber0061/Repositories/gesa_mails:/work \
  ghcr.io/apptainer/apptainer:latest apptainer exec --bind /work:/work \
  --pwd /work/SOTA_OGS_Mont_Terri_work/inversion_workflow/runs/direct_fit_observation_run \
  /work/cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif \
  ogs -o ogs_output cd_a_open_niche_quad.prj
```

The same backend has completed the recovered OGS 6.5.4 model for the direct
observation run and for the three selected regularized candidates.  The direct run
recorded return code 0, backend `docker_apptainer_sif`, and 83 VTU outputs.  For a
host executable, pass `--ogs /path/to/ogs` instead.  The execution status and the
last stdout/stderr lines are written to `OGS_EXECUTION_STATUS.json`.

After OGS writes `.vtu` files into `ogs_output`, sample the state fields at the
measurement lookup cells with:

```bash
python inversion_workflow/scripts/sample_ogs_state_outputs.py
```

The sampler inventories output files and samples the 107 catalogue measurement points
plus 341 borehole/Taupe line-sample points for each output timestep.  Cell-data fields
are read directly by `lookup_cell_id`; point-data fields are averaged over the lookup
cell vertices.  It also writes
`theta_from_porosity_times_saturation = porosity * saturation` as a model-side water
content proxy, with the same bound/interlayer-water caveat documented for NMR.

Current sampled status:

```text
OGS output files found: 83
sampled model time range: 0 to 140,000,000 s after 2019-09-18
lookup rows ready per output timestep: 448
sample rows written: 37184
state target rows ready for evaluation: 11490
state objective rows currently active: 192
```

## Candidate Evaluation Driver

- `scripts/evaluate_inversion_candidate.py`
- `runs/candidate_direct_fit_driver/CANDIDATE_EVALUATION_SUMMARY.json`

The candidate driver is the current end-to-end evaluation harness for fitting
heterogeneous anisotropic fields while leaving the GESA OGS process files unchanged.
For one candidate field it:

```text
1. prepares a run directory from the recovered projection model,
2. copies or generates `bulk_w_projections.vtu`,
3. audits run-input mesh fields, output variables, and submesh readability,
4. runs the inversion release-gate audit against the staged parameter plan,
5. evaluates direct pulse-test permeability residuals,
6. records or executes the OGS command,
7. samples OGS state outputs if they exist,
8. audits the RH boundary curve,
9. evaluates state-observation targets, and
10. assembles the active objective components.
```

The verified direct-fit diagnostic candidate can be run with:

```bash
python inversion_workflow/scripts/evaluate_inversion_candidate.py \
  --run-id candidate_direct_fit_driver \
  --mesh-override inversion_workflow/runs/direct_permeability_fit/bulk_w_projections.vtu \
  --ogs-mode dry-run
```

Current driver result:

```text
active objective components after OGS execution: 2 of 2
direct permeability objective: 269.82
direct permeability rows/effective weight: 75 / 52
release gate: pass
state target rows evaluated: 11490
state objective rows: 192
state objective: 2886.54
combined objective: 3156.36
RH boundary overlap rows audited: 2280
```

The current best smooth search candidate was run with:

```bash
python inversion_workflow/scripts/evaluate_inversion_candidate.py \
  --run-id candidate_smooth_0p025m_search_driver \
  --mesh-override inversion_workflow/runs/smooth_permeability_candidate_search/length_0p025m/bulk_w_projections.vtu \
  --ogs-mode dry-run
```

Its direct-only dry-run objective is 269.97.  The executed regularized candidate set
provides the OGS-backed comparison for this field: combined objective 3166.61 with
192 active NMR state rows.  The later local-refinement execute-mode batch improves the
smooth-field best to `length_0p013m`, with direct objective 269.82, 192 active NMR
state rows, and combined objective 3159.66.  The first continuous-proposal
execute-mode batch improves the active objective further to
`length_0p006m_shift_0p992`, with direct objective 269.85, 192 active NMR state rows,
and combined objective 3156.78.  The lower-support continuous execute-mode batch now
sets the current best to `length_0p004m_shift_0p995`, with direct objective 269.83,
192 active NMR state rows, and combined objective 3156.38.  The first repeatable
lower-support loop improves it again to `length_0p003m_shift_1p006`, with direct
objective 269.84, 192 active NMR state rows, and combined objective 3156.37.

Use `--ogs-mode execute` with either `--ogs /path/to/ogs` or
`--sif /path/to/apptainer_ogs6.5.4.sif` when execution is available.  The same driver
will then sample state outputs and activate any numerical state residuals supported
by the current observation operators.

## Inversion Candidate Search Driver

- `scripts/run_inversion_candidate_search.py`
- `runs/inversion_candidate_search/inversion_candidate_search_results.csv`
- `runs/inversion_candidate_search/INVERSION_SEARCH_SUMMARY.md`

The search driver is the deterministic loop around `evaluate_inversion_candidate.py`.
It reads a candidate-mesh table, prepares one OGS run directory per selected row,
evaluates all currently available objective components, and ranks the resulting
candidate summaries.  The default input is the smooth permeability candidate-search
table:

```bash
python inversion_workflow/scripts/run_inversion_candidate_search.py \
  --max-candidates 4 \
  --overwrite
```

Current dry-run ranking:

```text
rank  source candidate              objective  state rows active  release gate
1     length_0p025m                 269.97     0                  pass
2     length_0p050m                 291.29     0                  pass
3     length_0p025m_shift_0p750     301.16     0                  pass
4     length_0p050m_shift_0p750     329.40     0                  pass
```

Because this was run in dry mode, it is still a permeability-only ranking.  With
`--ogs-mode execute` plus either a host `--ogs` path or the collected `--sif` path
through Dockerized Apptainer, the same driver executes OGS for every candidate,
samples state outputs, and ranks by the combined active objective.  The first
adaptive execute-mode search used this path for three broader-support candidates and
ranked them at 3276.57, 3300.91, and 3353.88; all were worse than the then-best
0.025 m regularized field.
The local-refinement execute-mode search then ranked `length_0p013m` and
`length_0p019m` at 3159.66 and 3164.96.  The first local-bracketing execute-mode search then
ranked `length_0p013m_shift_1p125`, `length_0p013m_shift_0p875`, and `length_0p031m`
at 3167.21, 3167.34, and 3219.35, so that bracket did not improve the best field.
The first continuous-proposal execute-mode search then ranked
`length_0p006m_shift_0p992`, `length_0p007m`, and `length_0p007m_shift_0p972` at
3156.78, 3157.74, and 3158.16.  The lower-support continuous execute-mode search then
ranked `length_0p004m_shift_0p995`, `length_0p004m_shift_0p994`, and
`length_0p003m_shift_0p986` at 3156.38, 3156.38, and 3156.47.  The first repeatable
lower-support loop then ranked `length_0p003m_shift_1p006`,
`length_0p004m_shift_1p014`, and `length_0p005m_shift_0p985` at 3156.37, 3156.44,
and 3156.49, giving the current best active candidate.  The second repeatable
lower-support loop ranked `length_0p004m_shift_0p992`,
`length_0p004m_shift_1p020`, and `length_0p006m_shift_0p975` at 3156.40, 3156.53,
and 3156.70, so the incumbent remained unchanged.  The broad continuous execute-mode
search then ranked `length_0p023m_shift_1p004`, `length_0p022m_shift_0p998`, and
`length_0p021m` at 3159.06, 3169.30, and 3169.31, again leaving the incumbent
unchanged.  The broad continuous loop then ranked `length_0p010m`,
`length_0p015m`, and `length_0p016m_shift_0p968` at 3157.70, 3161.36, and 3165.33,
also leaving the incumbent unchanged.
A full inversion still requires replacing deterministic batch selection with an
optimizer or ensemble sampler.
