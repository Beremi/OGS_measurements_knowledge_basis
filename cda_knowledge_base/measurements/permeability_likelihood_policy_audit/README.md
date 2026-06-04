# Permeability Likelihood Policy Audit

This folder stores catalogue copies of the workflow artifacts that decide whether
the direct permeability pulse-test residual is a field-search problem, a support
mapping problem, or a likelihood-policy decision.

## Files

- [permeability_residual_conflict_audit.md](derived_files/permeability_residual_conflict_audit.md) - row, segment, configured-scalar-range, and support-cell residual conflict audit for the current field.
- [permeability_support_lower_bound_audit.md](derived_files/permeability_support_lower_bound_audit.md) - one-value-per-support-cell lower-bound proof for the current direct permeability support map.
- [permeability_likelihood_decision_request.md](derived_files/permeability_likelihood_decision_request.md) - modelling-team decision request for rowwise Gaussian, robust, support-cell, outlier, or new-parameterization policies.
- [permeability_configured_scalar_outlier_disposition.md](derived_files/permeability_configured_scalar_outlier_disposition.md) - local disposition for the two active configured-scalar-envelope outlier rows.
- [permeability_likelihood_scenario_rerank.md](derived_files/permeability_likelihood_scenario_rerank.md) - no-OGS rerank of materialized VTU fields under alternative direct-permeability likelihood policies.
- [permeability_likelihood_winner_cross_stream_audit.md](derived_files/permeability_likelihood_winner_cross_stream_audit.md) - cross-stream evidence audit for the direct-policy winner fields.
- [permeability_next_field_fit_gate.md](derived_files/permeability_next_field_fit_gate.md) - next-action gate for deciding whether another OGS batch is justified.
- [permeability_likelihood_support_recommendations.md](derived_files/permeability_likelihood_support_recommendations.md) - consolidated direct-permeability likelihood/support recommendation packet.
- [permeability_likelihood_policy_acceptance_record_template.md](derived_files/permeability_likelihood_policy_acceptance_record_template.md) - fillable signoff guardrail for selecting exactly one direct-permeability likelihood/support/outlier policy.

Current status: the rowwise Gaussian direct permeability objective remains the
current-report default for reproducibility, but the current field is already at the
single-support lower bound for the current support map.  The configured-scalar
outlier disposition records the two envelope rows as one duplicated BCD-A32 0.87 m
value that is only slightly above the configured upper envelope and does not by
itself justify eigenvalue-bound widening or tensor-shape release.  The next
field-fit gate therefore records that no same-support active-objective OGS batch is
executable now; reopening OGS spending requires an explicit likelihood, support
mapping, configured-bound/tensor-shape, or measurement-stream objective change.
The consolidated recommendation packet keeps the same decision in one place:
`keep_rowwise_gaussian_default` remains the current-report policy, the same-support
reducible gap is zero, bounds and tensor-shape release are not recommended now, and
the packet does not unblock final promotion.  The acceptance-record template lists
the five policy options from the decision request and currently records 0/1 primary
approvals, ready-to-apply false, no actual decision, no active-objective change, no
field promotion, and no same-support OGS spending unblocked.
