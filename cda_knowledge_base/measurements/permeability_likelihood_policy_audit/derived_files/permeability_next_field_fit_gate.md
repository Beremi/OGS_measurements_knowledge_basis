# Permeability Next Field-Fit Gate

This gate turns the current residual, likelihood-policy, rerank, and promotion
audits into explicit next-action rules. It does not change the active
objective, run OGS, or modify the frozen GESA model.

- Status: `permeability_next_field_fit_gate_generated`
- Gates: 8
- Overall recommendation: `pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes`
- Same-support active-objective batch executable now: False
- Current report default policy: `keep_rowwise_gaussian_default`
- Current field final decision: `do_not_promote_to_final_all_measurement_field`
- Same-support reducible gap: 0.0
- Spatial support cells active/repeated/range>=2 log10: 30/24/16
- Outside-tie direct-only policy winners: 3

## Gate Table

| Gate | Type | Status | Decision | Evidence | Reopen prerequisite |
| --- | --- | --- | --- | --- | --- |
| `G01_same_support_active_objective_sampling` | `stop_gate` | `do_not_run_more_same_support_sampling_now` | Pause routine same-support smooth/local-basis active-objective OGS batches. | support lower-bound gap=0.0; reducible fraction=0.0; current at lower bound=True; support-conflict spatial audit=permeability_support_conflict_spatial_audit_generated; active/repeated/range>=2 support cells=30/24/16; production sampler recommendation=pause_active_production_sampling | Approve a changed support mapping, likelihood semantics, configured bound/tensor-shape release, or a new accepted measurement-stream objective. |
| `G02_likelihood_policy_decision` | `internal_policy_gate` | `rowwise_gaussian_default_retained_for_current_report` | keep_rowwise_gaussian_default | decision options=5; top-10 row-loss share=0.49400403343820803; support mean objective=1.7670484276950664e-28; support median objective=134.72779043641356 | Record the exact robust kernel, support aggregation, outlier disposition, or new parameterization rule. |
| `G03_nondefault_policy_winner_execution` | `execution_gate` | `blocked_until_policy_approved_and_ogs_executed` | Do not replace the current accepted field with a direct-only non-default winner. | rerank scored fields=522; outside-tie direct-only winners=3; winner rows with cross-stream evidence=4; unique winners with cross-stream evidence=2 | Approve a non-default likelihood policy, execute targeted OGS/state sampling for its winner, and join the run to NMR/ERT/Taupe diagnostics before any promotion. |
| `G04_configured_scalar_outliers` | `bounds_or_tensor_shape_gate` | `local_outlier_disposition_recorded_policy_still_required` | Do not widen eigenvalue bounds or release tensor shape from the scalar-envelope rows alone; keep them visible under the current default until the modelling team accepts or changes the policy. | active rows outside configured scalar range=2; \|residual\|>=2 log10 rows=21; max abs residual=3.4744237387763093; outlier disposition status=permeability_configured_scalar_outlier_disposition_generated; unique outlier groups=1; max envelope excess=0.10719186674877967 log10; bounds release now=False; tensor-shape release now=False | Modelling team accepts this local disposition or chooses a capped/robust row policy, support-cell aggregation, explicit outlier exclusion, wider eigenvalue bounds, or tensor-shape/anisotropy release. |
| `G05_support_geometry_and_endpoint_update` | `support_mapping_gate` | `blocked_by_support_conflicts_and_endpoint_geometry` | Keep endpoint-missing historical permeability rows inactive unless geometry is accepted. | support groups=30; groups with observed range >=2 log10=16; spatial top conflict cell=4648 (BCD-A32 at 0.85-0.87 m, observed range=6.948847477552619); open promotion criteria include P13=True | Accept missing endpoint traces/geometry or a new support aggregation policy, then rebuild targets. |
| `G06_measurement_stream_final_objective` | `external_stream_gate` | `blocked_by_external_stream_gates` | Do not promote the active field as the final all-measurement result. | final-objective options=9; current-field winning options=2; unique winners=5; open blockers=8 | Close or explicitly exclude ERT, Taupe/TDR, RH, other-HM, endpoint, CTE, and NMR-policy gates, then choose one final-objective scenario. |
| `G07_current_field_package` | `deliverable_gate` | `available_for_inspection_active_only` | Keep the packaged field as the active-objective incumbent, not a final field. | current run=local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000; triangle6 cells=10239; positive-definite cells=10239; final decision=do_not_promote_to_final_all_measurement_field | Pass the final promotion checklist and final-objective scenario decision. |
| `G08_posterior_or_optimizer_trace` | `completion_gate` | `not_ready_until_objective_finalized` | Do not treat deterministic sampler batches as a converged posterior or optimizer trace. | Current evidence is a deterministic candidate/sampler comparison; promotion decision=do_not_promote_current_field; open criteria=9 | Finalize the likelihood/objective gates, then run the chosen optimizer/posterior workflow against that objective. |

## Next Decision Sequence

- Keep the current field active-only while final objective gates remain open.
- Do not run another same-support active-objective OGS batch under the current row-Gaussian policy.
- Use the spatial support-conflict audit to inspect where the repeated-row support conflicts sit on the mesh before changing support or likelihood semantics.
- Choose whether direct permeability needs robust rows, support-cell aggregation, scalar outlier handling, or a new parameterization.
- Use the configured-scalar outlier disposition: current local evidence does not justify bounds widening or tensor-shape release from the two duplicate envelope rows alone.
- If a non-default direct policy is approved and selects a direct-only winner, execute OGS/state/diagnostic evidence before any promotion.
- After external stream gates are closed or explicitly excluded, rebuild final-objective scenarios and the promotion checklist.

## Source Artifacts

- `inversion_workflow/permeability_residual_conflict_audit_summary.json`
- `inversion_workflow/permeability_support_lower_bound_audit_summary.json`
- `inversion_workflow/permeability_support_conflict_spatial_audit_summary.json`
- `inversion_workflow/permeability_likelihood_decision_request_summary.json`
- `inversion_workflow/permeability_configured_scalar_outlier_disposition_summary.json`
- `inversion_workflow/permeability_likelihood_scenario_rerank_summary.json`
- `inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json`
- `inversion_workflow/final_objective_scenario_matrix_summary.json`
- `inversion_workflow/final_inversion_promotion_checklist_summary.json`
- `inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json`
- `inversion_workflow/runs/production_sampler_convergence/PRODUCTION_SAMPLER_DECISION.json`
