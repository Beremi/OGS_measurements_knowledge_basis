# Permeability Likelihood And Support Recommendations

This generated packet consolidates the direct-permeability likelihood, support,
outlier, rerank, cross-stream, and next-field-fit audits into one decision-support
record.  It does not change the active objective, alter OGS inputs, approve a
non-default likelihood, or promote a field.

- Status: `permeability_likelihood_support_recommendations_generated`
- Recommendations: 8
- Current-report policy: `keep_rowwise_gaussian_default`
- Current Gaussian objective: 269.8180571059851
- Active direct rows: 75
- Support groups: 30
- Groups with observed range >= 1 log10: 16
- Spatial support cells active/repeated/range>=2 log10: 30/24/16
- Current at single-support lower bound: `True`
- Same-support reducible objective gap: 0.0
- Same-support active-objective batch executable now: `False`
- Bounds release recommended now: `False`
- Tensor-shape release recommended now: `False`
- Alternate policy winners outside row-Gaussian best tie set: 3
- Outside-tie direct-only policy winners: 3
- Final promotion unblocked by this packet: `False`

## Recommendation Table

| Decision | Topic | Recommendation | Effect on OGS spending |
| --- | --- | --- | --- |
| `D01_current_report_policy` | Recorded direct-permeability policy | Keep the duplicate-weighted rowwise Gaussian direct-permeability policy as the current-report default for reproducibility. | No new same-support OGS batch is justified by this row alone. |
| `D02_same_support_lower_bound` | Same-support field-search limit | Treat the remaining direct permeability loss as irreducible by another one-value-per-support-cell field in the current support map. | Pause same-support active-objective OGS batches now. |
| `D03_support_aggregation` | Support-cell aggregation option | Use support-cell aggregation only as an explicit alternative likelihood, not as an automatic correction. | Existing-field rerank can be used first; new OGS is needed only after a non-default policy selects a candidate lacking state diagnostics. |
| `D04_robust_row_policy` | Robust row likelihood option | Keep robust row policies as candidate final-policy options, especially if the modelling team wants to reduce dominance by a few conflicting rows. | Huber and Student-t winners currently remain inside the row-Gaussian tie set; no immediate same-support OGS batch follows from these diagnostics alone. |
| `D05_configured_scalar_outliers` | Configured scalar envelope rows | Record the two active envelope rows as one duplicated BCD-A32 high-value case embedded in a larger same-support conflict; do not widen bounds or release tensor shape from these rows alone. | This disposition does not reopen same-support active-objective OGS sampling. |
| `D06_existing_field_rerank` | No-OGS existing-field policy rerank | Use the existing-field rerank as decision evidence before proposing new field families. | Only non-default winners that are not already executed/scored need targeted OGS execution after policy acceptance. |
| `D07_cross_stream_requirement` | Non-default direct-policy winners | Require OGS state sampling and cross-stream diagnostics before any direct-only non-default winner can replace the current active field. | Targeted OGS execution is conditional on policy acceptance and candidate selection. |
| `D08_next_field_fit_gate` | Next OGS field-fit action | Pause same-support active-objective production sampling. Reopen only after a likelihood/support/bounds/tensor-shape decision or accepted measurement-stream objective changes the problem. | No same-support active-objective batch is executable now. |

## Detailed Rows

### `D01_current_report_policy` Recorded direct-permeability policy

- Current evidence: current Gaussian objective=269.8180571059851; active rows=75; effective objective weight=52.0; recommended current-report policy=keep_rowwise_gaussian_default
- Recommendation: Keep the duplicate-weighted rowwise Gaussian direct-permeability policy as the current-report default for reproducibility.
- What not to do: Do not silently replace the recorded active objective with a robust, support-aggregated, capped, or outlier-filtered policy.
- Decision required before change: The modelling team must explicitly approve any non-default likelihood formula and rerun the scenario/current-field/readiness audits.
- Effect on OGS spending: No new same-support OGS batch is justified by this row alone.

### `D02_same_support_lower_bound` Same-support field-search limit

- Current evidence: current objective=269.8180571059851; single-support lower bound=269.8180571059851; reducible gap=0.0; support groups at lower bound=30/30; spatial active/repeated/range>=2 support cells=30/24/16
- Recommendation: Treat the remaining direct permeability loss as irreducible by another one-value-per-support-cell field in the current support map.
- What not to do: Do not spend more OGS runs on the same support and same row-Gaussian objective expecting the dominant direct loss to drop.
- Decision required before change: Change support mapping, likelihood semantics, measurement interpretation, bounds, tensor shape, or accepted stream objective before reopening routine runs.
- Effect on OGS spending: Pause same-support active-objective OGS batches now.

### `D03_support_aggregation` Support-cell aggregation option

- Current evidence: support groups=30; repeated groups=24; groups range>=1 log10=16; support mean objective=1.7670484276950664e-28; support median objective=134.72779043641356
- Recommendation: Use support-cell aggregation only as an explicit alternative likelihood, not as an automatic correction.
- What not to do: Do not interpret the near-zero support-mean diagnostic as proof that the pulse-test dataset is physically resolved; it mostly proves the field matches duplicate-weighted support means.
- Decision required before change: Choose mean, median, robust group, or another group statistic and state how repeated pulse-test rows should be weighted.
- Effect on OGS spending: Existing-field rerank can be used first; new OGS is needed only after a non-default policy selects a candidate lacking state diagnostics.

### `D04_robust_row_policy` Robust row likelihood option

- Current evidence: row top-10 loss share=0.49400403343820803; Huber delta objective=183.67124740833367; Student-t nu4 objective=121.16896116540622; row-Gaussian best ties=40
- Recommendation: Keep robust row policies as candidate final-policy options, especially if the modelling team wants to reduce dominance by a few conflicting rows.
- What not to do: Do not call a robust result final until the residual scale, tail policy, and treatment of duplicate support rows are documented.
- Decision required before change: Choose Huber, Student-t, capped Gaussian, or another robust form with explicit sigma, tail parameters, and normalization/weighting convention.
- Effect on OGS spending: Huber and Student-t winners currently remain inside the row-Gaussian tie set; no immediate same-support OGS batch follows from these diagnostics alone.

### `D05_configured_scalar_outliers` Configured scalar envelope rows

- Current evidence: outlier rows=2; physical groups=1; max envelope excess=0.10719186674877967 log10; same-support range=6.948847477552619 log10; bounds release=False; tensor release=False
- Recommendation: Record the two active envelope rows as one duplicated BCD-A32 high-value case embedded in a larger same-support conflict; do not widen bounds or release tensor shape from these rows alone.
- What not to do: Do not treat the small envelope excess as sufficient evidence for a broader tensor-shape release.
- Decision required before change: Accept this local disposition or choose an explicit outlier, capped, inside-only, bound-widening, or tensor-shape-release policy.
- Effect on OGS spending: This disposition does not reopen same-support active-objective OGS sampling.

### `D06_existing_field_rerank` No-OGS existing-field policy rerank

- Current evidence: candidate fields scored=522; current accepted in row-Gaussian best tie set=True; alternate policy winners outside tie set=3
- Recommendation: Use the existing-field rerank as decision evidence before proposing new field families.
- What not to do: Do not promote an alternate-policy winner solely from direct-permeability reranking.
- Decision required before change: If the accepted formula differs from these audited policies, rerun the rerank under the exact accepted formula.
- Effect on OGS spending: Only non-default winners that are not already executed/scored need targeted OGS execution after policy acceptance.

### `D07_cross_stream_requirement` Non-default direct-policy winners

- Current evidence: policy winner rows=7; with cross-stream scorecard=4; outside-tie direct-only winners=3; current accepted mean rank=13.2; row-Gaussian representative mean rank=30.4
- Recommendation: Require OGS state sampling and cross-stream diagnostics before any direct-only non-default winner can replace the current active field.
- What not to do: Do not treat direct-only materialized VTU candidates as final all-measurement candidates.
- Decision required before change: After a non-default direct policy is approved, execute or audit the selected winner through OGS/state/NMR/ERT/Taupe diagnostics before promotion.
- Effect on OGS spending: Targeted OGS execution is conditional on policy acceptance and candidate selection.

### `D08_next_field_fit_gate` Next OGS field-fit action

- Current evidence: gate status=permeability_next_field_fit_gate_generated; recommendation=pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes; executable same-support batch now=False; open blockers=8
- Recommendation: Pause same-support active-objective production sampling. Reopen only after a likelihood/support/bounds/tensor-shape decision or accepted measurement-stream objective changes the problem.
- What not to do: Do not present the current direct-permeability field as final or continue the same production sampler by inertia.
- Decision required before change: Choose a direct-permeability policy and close or explicitly exclude external stream gates before final promotion.
- Effect on OGS spending: No same-support active-objective batch is executable now.

## Policy Winner Snapshot

- capped_gaussian_abs1_log10: winner=local_anisotropy_sampler_plan/local_anis_residual_sign_l0p0015_s0p5_r2p5, value=64.81233623477108, winner_in_current_gaussian_best_tie_set=False, current_rank=183.0
- configured_scalar_inside_only_gaussian: winner=lower_support_continuous_candidate_plan/length_0p007m_shift_0p946, value=244.31792014948041, winner_in_current_gaussian_best_tie_set=False, current_rank=110.0
- current_duplicate_weighted_gaussian: winner=broad_continuous_loop_001_001_length_0p015m, value=269.8180571059851, winner_in_current_gaussian_best_tie_set=True, current_rank=1.0
- huber_delta_2sigma: winner=broad_continuous_loop_001_001_length_0p015m, value=183.6712474083337, winner_in_current_gaussian_best_tie_set=True, current_rank=1.0
- student_t_nu4: winner=broad_continuous_loop_001_001_length_0p015m, value=121.16896116540623, winner_in_current_gaussian_best_tie_set=True, current_rank=1.0
- support_cell_weighted_mean_unit_gaussian: winner=current_permeability_field/current_best, value=1.072850831100576e-28, winner_in_current_gaussian_best_tie_set=True, current_rank=1.0
- support_cell_weighted_median_unit_gaussian: winner=local_anisotropy_sampler_plan/local_anis_perpendicular_all_l0p0015_s1_r12, value=81.82840410875852, winner_in_current_gaussian_best_tie_set=False, current_rank=228.0

## Interpretation

- The active field is already at the single-support lower bound for the current one-value-per-support-cell mapping.
- The support-conflict spatial audit maps those conflicts onto the current mesh, so support or likelihood changes can be reviewed against concrete cells rather than only aggregate counts.
- The remaining direct pulse-test mismatch is therefore a likelihood/support/measurement-interpretation question before it is another same-family field-search question.
- Robust tails, support-cell aggregation, capped row loss, configured-scalar inside-only scoring, and bounds/tensor-shape release are all policy choices, not automatic corrections.
- The current report should keep the rowwise Gaussian policy for reproducibility unless the modelling team records a different policy and regenerates the downstream audits.
- Use `permeability_likelihood_policy_acceptance_record_template.md` as the separate signoff guardrail before treating any policy option as approved.
- This packet does not unblock final promotion.

## Source Artifacts

- `inversion_workflow/permeability_likelihood_policy_audit_summary.json`
- `inversion_workflow/permeability_likelihood_decision_request_summary.json`
- `inversion_workflow/permeability_support_lower_bound_audit_summary.json`
- `inversion_workflow/permeability_support_conflict_spatial_audit_summary.json`
- `inversion_workflow/permeability_configured_scalar_outlier_disposition_summary.json`
- `inversion_workflow/permeability_likelihood_scenario_rerank_summary.json`
- `inversion_workflow/permeability_likelihood_winner_cross_stream_audit_summary.json`
- `inversion_workflow/permeability_next_field_fit_gate_summary.json`
