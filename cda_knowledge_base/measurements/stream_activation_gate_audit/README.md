# Stream Activation Gate Audit

This folder stores catalogue copies of the workflow artifacts that decide which
measurement streams can be used as hard residuals in the frozen OGS model.

## Files

- [measurement_stream_activation_gate_audit.md](derived_files/measurement_stream_activation_gate_audit.md) - stream-level activation decisions and gate failures.
- [measurement_stream_activation_gate_checks.csv](derived_files/measurement_stream_activation_gate_checks.csv) - row-level gate checks.
- [measurement_model_entry_matrix.md](derived_files/measurement_model_entry_matrix.md) - per-measurement join of coverage, likelihood semantics, activation gates, final allowed use, blockers, and measurement-info links.
- [measurement_gate_closure_request.md](derived_files/measurement_gate_closure_request.md) - actionable closure package for failed and warning gates.
- [measurement_gate_closure_request.csv](derived_files/measurement_gate_closure_request.csv) - machine-readable closure request table.
- [measurement_gate_closure_email_draft.md](derived_files/measurement_gate_closure_email_draft.md) - draft request text grouped by external source.
- [external_gate_request_pack.md](derived_files/external_gate_request_pack.md) - recipient-specific external request pack for the provider-facing gates.
- [external_gate_dispatch_audit.md](derived_files/external_gate_dispatch_audit.md) - dispatch-readiness and Gmail-draft audit for the seven external requests.
- [external_gate_gmail_drafts.csv](derived_files/external_gate_gmail_drafts.csv) - Gmail draft ids for the five unsent external request drafts.
- [external_gate_response_intake.md](derived_files/external_gate_response_intake.md) - response-filing checklist, acceptance tests, and refresh commands for expected answers.
- [cte_confirmation_request.md](derived_files/cte_confirmation_request.md) - separate CTE provenance request for the suspicious active thermal-expansivity value.
- [cte_confirmation_gmail_draft.csv](derived_files/cte_confirmation_gmail_draft.csv) - Gmail draft id for the unsent CTE request.
- [final_inversion_promotion_checklist.md](derived_files/final_inversion_promotion_checklist.md) - final all-measurement field promotion checklist.
- [final_inversion_closeout_playbook.md](derived_files/final_inversion_closeout_playbook.md) - action routing for the open final-promotion criteria.
- [final_objective_decision_register.md](derived_files/final_objective_decision_register.md) - include, diagnostic-only, exclusion, or waiver decision register for the final objective.
- [final_objective_scenario_matrix.md](derived_files/final_objective_scenario_matrix.md) - explicit final-objective option matrix and current winner consequences.
- [final_objective_include_exclude_recommendations.md](derived_files/final_objective_include_exclude_recommendations.md) - conservative no-new-evidence recommendations for each open include/exclude row.
- [final_objective_no_new_evidence_closeout_draft.md](derived_files/final_objective_no_new_evidence_closeout_draft.md) - exact draft decision text for a possible conservative no-new-evidence closeout; review only, not an approval record.
- [final_objective_no_new_evidence_acceptance_record_template.md](derived_files/final_objective_no_new_evidence_acceptance_record_template.md) - fillable signoff guardrail for the conservative closeout; currently 0/9 approvals and not ready to apply.
- [gmail_draft_send_review_packet.md](derived_files/gmail_draft_send_review_packet.md) - consolidated review packet for the unsent Gmail drafts.
- [report_open_comment_audit.md](derived_files/report_open_comment_audit.md) - active-report marker/comment audit.
- [open_question_resolution_matrix.md](derived_files/open_question_resolution_matrix.md) - consolidated map from the open-question list to local resolutions, external provider gates, and internal modelling decisions.
- [objective_readiness_audit.md](derived_files/objective_readiness_audit.md) - objective-level completion audit that distinguishes achieved report/catalogue work from the still incomplete final all-measurement inversion.

Current status: direct permeability and NMR are active with caveats; ERT, Taupe/TDR,
RH/suction, and other HM monitoring remain diagnostic, boundary-audit, or qualitative
until their support, calibration, uncertainty, provenance, and numeric-export gates
are closed.  Five Gmail drafts cover the seven external stream requests and one
separate Gmail draft covers the CTE provenance request; none is recorded as sent, and
no provider responses are recorded yet.  The final objective decision register now
requires each open stream to be explicitly included, kept diagnostic-only, excluded,
or waived before the current active permeability field can be promoted.  The final
objective scenario matrix records nine possible final-objective choices; the current
field wins only the raw-NMR active objective and the direct-only tie case, while
promoted-NMR, ERT, or Taupe/TDR options select different fields.
The include/exclude recommendation packet records the current conservative position:
without new provider evidence, keep the unresolved external/provenance streams
diagnostic-only, inactive, or scoped out, and keep the current permeability field
labelled as active-objective incumbent rather than final.
The no-new-evidence closeout draft turns that position into exact decision text for
review: nine draft rows, a single-block acceptance text, and a conditional F01
scenario path that still requires approval and regenerated audits before any field
label changes.
The matching acceptance-record template records 0/9 approvals and is not ready to
apply, so the draft cannot be mistaken for an accepted final-objective decision.
The open-question resolution matrix records 23 rows and separates the remaining
questions into 6 locally resolved/current-scope rows, 9 external send/response rows,
6 internal policy/final-decision rows, 1 tracked current-policy caveat, 1 deferred
time-dependency row, and an explicit no-new-evidence closeout decision row.
