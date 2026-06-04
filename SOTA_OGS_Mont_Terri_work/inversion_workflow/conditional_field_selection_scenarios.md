# Conditional Field Selection Scenarios

This audit asks which executed field would be selected under each currently
defensible objective or diagnostic-gate scenario. It is a map of conditional
decisions, not a promotion of gated streams into the active likelihood.

- Status: `conditional_field_selection_scenarios_generated`
- Current packaged run: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Scenarios: 8
- Unique winners: 5
- Current field winning scenarios: 1
- Final decision: `single_field_not_stable_across_gate_scenarios`
- Required stream-gate failures: 7

## Scenario Winners

| Scenario | Gate status | Winner | Current rank | Current winner? | Winner ranks (active/NMR/ERT/Taupe) |
| --- | --- | --- | ---: | --- | --- |
| `S01_current_active_raw_nmr` Current active objective | `active_now` | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 1 | yes | 1/14/8/29 |
| `S02_promoted_nmr_trend_anomaly` Promoted NMR trend/anomaly | `internal_promotion_decision_required` | `broad_continuous_001_003_length_0p021m` | 14 | no | 56/1/60/62 |
| `S03_active_plus_ert_screen` Active objective plus ERT screen | `external_ert_gate_required` | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 3 | no | 2/13/6/18 |
| `S04_active_plus_taupe_screen` Active objective plus Taupe screen | `external_taupe_gate_required` | `local_bracketed_003_length_0p031m` | 21 | no | 62/41/63/3 |
| `S05_active_plus_ert_taupe_screen` Active objective plus ERT and Taupe | `external_ert_taupe_gates_required` | `production_sampler_round3_002_length_0p028m_shift_1p050` | 19 | no | 53/48/49/4 |
| `S06_active_plus_promoted_nmr_ert_taupe` Active plus promoted NMR, ERT, and Taupe | `internal_and_external_gates_required` | `production_sampler_round3_002_length_0p028m_shift_1p050` | 18 | no | 53/48/49/4 |
| `S07_diagnostics_only_nmr_ert_taupe` Diagnostics-only screen | `diagnostic_only_not_active_likelihood` | `local_bracketed_003_length_0p031m` | 19 | no | 62/41/63/3 |
| `S08_rank_consensus_all_streams` Rank consensus across all streams | `diagnostic_consensus_not_active_likelihood` | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 2 | no | 2/13/6/18 |

## Interpretation

- The current packaged field wins only the active raw-NMR objective scenario.
- Different defensible diagnostic or promoted-NMR scenarios select different fields.
- Use this as a conditional selection map; it does not promote ERT, Taupe/TDR, RH, or other-HM into the likelihood.

## Top Candidates By Scenario

### S01_current_active_raw_nmr - Current active objective

Current objective: direct gas-pulse permeability plus raw absolute NMR theta residual.

| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 0 | 1 | 14 | 8 | 29 |
| 2 | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 6.07113e-06 | 2 | 13 | 6 | 18 |
| 3 | `production_sampler_round2_005_basis_023_det_l_0p0075_s_0p750` | 8.56149e-06 | 3 | 19 | 7 | 23 |
| 4 | `production_sampler_round2_004_basis_018_det_l_0p0050_s_0p750` | 4.05594e-05 | 4 | 17 | 9 | 21 |
| 5 | `production_sampler_round2_002_basis_008_det_l_0p0025_s_0p750` | 4.05594e-05 | 5 | 16 | 11 | 22 |

### S02_promoted_nmr_trend_anomaly - Promoted NMR trend/anomaly

Conditional objective if the preferred within-label NMR trend/anomaly residual replaces raw NMR.

| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `broad_continuous_001_003_length_0p021m` | 0 | 56 | 1 | 60 | 62 |
| 2 | `local_refined_002_length_0p019m` | 3.65229e-07 | 47 | 2 | 55 | 64 |
| 3 | `local_refined_001_length_0p013m` | 6.35051e-05 | 40 | 3 | 46 | 56 |
| 4 | `broad_continuous_loop_001_001_length_0p015m` | 6.70588e-05 | 45 | 4 | 48 | 51 |
| 5 | `broad_continuous_001_002_length_0p022m_shift_0p998` | 0.000111711 | 55 | 5 | 61 | 65 |

### S03_active_plus_ert_screen - Active objective plus ERT screen

Equal-normalized screen using the current active objective and provisional ERT log-resistivity MAE.

| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 0.00273539 | 2 | 13 | 6 | 18 |
| 2 | `production_sampler_round2_005_basis_023_det_l_0p0075_s_0p750` | 0.00273694 | 3 | 19 | 7 | 23 |
| 3 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 0.00273805 | 1 | 14 | 8 | 29 |
| 4 | `production_sampler_round2_004_basis_018_det_l_0p0050_s_0p750` | 0.00276401 | 4 | 17 | 9 | 21 |
| 5 | `production_sampler_round2_002_basis_008_det_l_0p0025_s_0p750` | 0.00276401 | 5 | 16 | 11 | 22 |

### S04_active_plus_taupe_screen - Active objective plus Taupe screen

Equal-normalized screen using the current active objective and provisional Taupe/TDR trend MAE.

| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `local_bracketed_003_length_0p031m` | 0.189235 | 62 | 41 | 63 | 3 |
| 2 | `adaptive_combined_001_length_0p050m` | 0.304289 | 63 | 62 | 65 | 1 |
| 3 | `production_sampler_round3_002_length_0p028m_shift_1p050` | 0.310727 | 53 | 48 | 49 | 4 |
| 4 | `production_sampler_round3_001_length_0p028m` | 0.317476 | 52 | 39 | 51 | 7 |
| 5 | `production_sampler_round2_006_length_0p026m_shift_1p107` | 0.320991 | 57 | 56 | 50 | 5 |

### S05_active_plus_ert_taupe_screen - Active objective plus ERT and Taupe

Equal-normalized screen if ERT and Taupe/TDR diagnostics were both accepted as screening evidence.

| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `production_sampler_round3_002_length_0p028m_shift_1p050` | 0.218048 | 53 | 48 | 49 | 4 |
| 2 | `production_sampler_round3_001_length_0p028m` | 0.223288 | 52 | 39 | 51 | 7 |
| 3 | `production_sampler_round2_006_length_0p026m_shift_1p107` | 0.225586 | 57 | 56 | 50 | 5 |
| 4 | `broad_continuous_001_001_length_0p023m_shift_1p004` | 0.229511 | 38 | 25 | 1 | 10 |
| 5 | `optimizer_proposed_003_length_0p025m_shift_1p125` | 0.232509 | 60 | 57 | 52 | 6 |

### S06_active_plus_promoted_nmr_ert_taupe - Active plus promoted NMR, ERT, and Taupe

Equal-normalized all-available numeric screen without duplicating the NMR label-bias variant.

| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `production_sampler_round3_002_length_0p028m_shift_1p050` | 0.166099 | 53 | 48 | 49 | 4 |
| 2 | `production_sampler_round3_001_length_0p028m` | 0.168622 | 52 | 39 | 51 | 7 |
| 3 | `broad_continuous_001_001_length_0p023m_shift_1p004` | 0.172305 | 38 | 25 | 1 | 10 |
| 4 | `regularized_ogs_candidate_001_length_0p025m` | 0.177292 | 49 | 27 | 58 | 9 |
| 5 | `production_sampler_round4_001_length_0p029m_shift_0p954` | 0.179545 | 54 | 52 | 54 | 8 |

### S07_diagnostics_only_nmr_ert_taupe - Diagnostics-only screen

Equal-normalized screen using NMR trend/anomaly, ERT, and Taupe diagnostics only.

| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `local_bracketed_003_length_0p031m` | 0.181454 | 62 | 41 | 63 | 3 |
| 2 | `production_sampler_round3_002_length_0p028m_shift_1p050` | 0.202015 | 53 | 48 | 49 | 4 |
| 3 | `production_sampler_round3_001_length_0p028m` | 0.206258 | 52 | 39 | 51 | 7 |
| 4 | `production_sampler_round2_006_length_0p026m_shift_1p107` | 0.214549 | 57 | 56 | 50 | 5 |
| 5 | `production_sampler_round4_001_length_0p029m_shift_0p954` | 0.217675 | 54 | 52 | 54 | 8 |

### S08_rank_consensus_all_streams - Rank consensus across all streams

Mean-rank consensus from the cross-stream scorecard, including active objective and diagnostics.

| Rank | Run | Score | Active rank | NMR rank | ERT rank | Taupe rank |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000` | 10.4 | 2 | 13 | 6 | 18 |
| 2 | `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | 13.2 | 1 | 14 | 8 | 29 |
| 2 | `production_sampler_round4_002_basis_009_det_l_0p0025_s_1p000` | 13.2 | 12 | 8 | 14 | 24 |
| 4 | `production_sampler_round2_004_basis_018_det_l_0p0050_s_0p750` | 13.6 | 4 | 17 | 9 | 21 |
| 4 | `production_sampler_round2_003_basis_013_det_l_0p0035_s_0p750` | 13.6 | 6 | 15 | 12 | 20 |

## Source Artifacts

- `inversion_workflow/cross_stream_candidate_scorecard.csv`
- `inversion_workflow/current_permeability_field/CURRENT_PERMEABILITY_FIELD_SUMMARY.json`
- `inversion_workflow/measurement_stream_activation_gate_audit_summary.json`
