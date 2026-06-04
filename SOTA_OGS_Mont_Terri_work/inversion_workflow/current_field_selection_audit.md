# Current Field Selection Audit

This audit is the selection record for the packaged permeability field. It
separates acceptance as the current active-objective incumbent from rejection
as a final all-measurement field.

- Status: `current_field_selection_audit_generated`
- Packaged run: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Active-objective decision: `accept_as_current_active_objective_incumbent`
- Final all-measurement decision: `do_not_promote_to_final_all_measurement_field`
- Criteria passed: 2
- Criteria with caveats: 2
- Criteria blocked/gated: 4
- Criteria failing final promotion: 2

## Decision Rationale

- The packaged field is complete, release-gated, and first under the current active objective.
- The active objective still contains only direct permeability and raw NMR state residuals.
- The preferred provisional NMR trend/anomaly residual selects a different run.
- The cross-stream scorecard's best mean-rank run differs from the packaged field.
- ERT, Taupe/TDR, RH, and other-HM streams remain gated by support, calibration, provenance, or numeric-export gaps.

## Criteria

| Criterion | Status | Evidence | Implication |
| --- | --- | --- | --- |
| `C01_field_package_integrity` Packaged field is complete, positive-definite, and traceable to a release-gated OGS run. | `pass` | package status=current_permeability_field_package_generated; mesh=inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu; triangle6 cells=10239; positive-definite cells=10239; non-positive-definite cells=0; release gate=pass; OGS returncode=0. | The field is suitable for inspection, reruns, and active-objective comparison. |
| `C02_active_objective_incumbent` Field is the current winner under the active direct-permeability plus raw-NMR objective. | `pass` | active rank=1.0; active objective=3156.353066948979; direct objective=269.8180571059851; raw NMR/state objective=2886.5350098429944; active components=2. | Accept as the active-objective incumbent, with the active objective's known caveats. |
| `C03_direct_permeability_fit` Direct gas-pulse permeability rows are represented as tensor-direction interval targets. | `pass_with_caveat` | usable direct rows=75; weighted RMSE log10=1.61071549171474; field=k_i_rd; log10 sigma=0.5. | This supports the field as a direct pulse-test fit, not as a liquid effective-permeability proof. |
| `C04_raw_nmr_active_fit` Raw NMR theta rows are sampled from OGS outputs and active in the current objective. | `pass_with_caveat` | NMR/state rows used=192; raw normalized RMSE=5.483436241919646; state sample rows=37184; raw active field rank=1.0. | The raw-theta state fit is usable but remains conditional because bound/interlayer water can change the preferred residual. |
| `C05_nmr_trend_anomaly_robustness` Field remains acceptable if the preferred provisional NMR trend/anomaly residual is promoted. | `fails_final_promotion` | trend/anomaly winner=broad_continuous_001_003_length_0p021m; current field trend/anomaly rank=14.0; trend/anomaly winner raw-objective rank=56.0; promotion gate=Executable but still provisional: this mode can be passed to evaluate_inversion_candidate.py, but promotion to the default reporting objective still needs explicit modelling acceptance because it changes the winner relative to the raw absolute NMR objective.. | Do not call the packaged field final if NMR is promoted to the offset-robust residual without reranking field selection. |
| `C06_ert_diagnostic_consistency` Field is compatible with the provisional ERT log-resistivity diagnostic. | `blocked_or_gated` | active-incumbent ERT rank=8.0; ERT MAE log10=0.2541796182834413; ERT winner=broad_continuous_001_001_length_0p023m_shift_1p004; required gate failures=7. | ERT can screen the field, but cannot select a final field until transform/support/covariance gates are accepted. |
| `C07_taupe_diagnostic_consistency` Field is compatible with the provisional Taupe/TDR trend diagnostic. | `blocked_or_gated` | active-incumbent Taupe rank=29.0; Taupe MAE=1.863211058631399; Taupe winner=adaptive_combined_001_length_0p050m; required gate failures=7. | Taupe/TDR cannot select a final field until workbook unit/calibration and grouped uncertainty are accepted. |
| `C08_cross_stream_consensus` Same field is supported by active objective plus NMR, ERT, and Taupe diagnostics. | `fails_final_promotion` | best mean-rank run=local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000; active field mean rank=13.2; active field worst rank=29.0; active field top-10 stream count=2; top-10-all-stream candidates=0. | The packaged field is not the cross-stream consensus field under the current diagnostic scorecard. |
| `C09_rh_other_hm_gate` RH and other-HM information can be used as hard residuals in final field selection. | `blocked_or_gated` | promotion decisions={'active_with_tracked_caveats': 2, 'boundary_audit_only': 1, 'diagnostic_only': 2, 'not_ready_for_hard_residual': 1, 'support_layer_ready': 2}; diagnostic/boundary-only streams=3; not-ready hard-residual streams=1. | RH remains boundary/provenance evidence and other-HM remains outside hard residual weighting. |
| `C10_external_gate_closure` External calibration/provenance responses needed for final all-measurement selection are closed. | `blocked_or_gated` | external intake status=external_gate_response_intake_generated_waiting_for_responses; tracked requests=7; missing responses=7; main remaining gates=['ERT transform/support and uncertainty', 'Taupe unit/calibration and uncertainty', 'RH active boundary-curve provenance', 'other-HM numeric exports', 'CTE confirmation', 'NMR trend/anomaly default-promotion decision']. | Final selection must wait for response filing or an explicit decision to exclude those gated streams. |

## Source Artifacts

- `inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json`
- `inversion_workflow/cross_stream_candidate_scorecard_summary.json`
- `inversion_workflow/nmr_trend_anomaly_active_objective_summary.json`
- `inversion_workflow/measurement_stream_activation_gate_audit_summary.json`
- `inversion_workflow/external_gate_response_intake_summary.json`
