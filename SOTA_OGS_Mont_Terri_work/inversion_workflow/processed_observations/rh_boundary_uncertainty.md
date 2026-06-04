# RH Boundary Uncertainty Envelope Audit

This audit treats the six locally generated RH-derived boundary curves as a policy ensemble.
It quantifies sensor-policy spread and active-curve mismatch; it does not activate RH/suction in the likelihood.

## Status

- Status: `rh_boundary_uncertainty_envelope_generated_provenance_still_unverified`
- Candidate curves: 6
- Envelope dates: 1064
- Preferred policy candidate: `rh5_rh6_median`
- Lowest overlap-MAE candidate: `rh6_only`
- Activation gate: Diagnostic only: the local RH candidate envelope quantifies sensor-policy spread and active-curve mismatch. RH boundary forcing and any retention/suction likelihood remain gated until BGR/Gesa confirm the active curve provenance, sensor screening, time axis, Kelvin constants, and extension policy.

## Envelope Statistics

| Regime | Dates | Date range | Candidate count p50 | Pressure range p50 MPa | Pressure range p90 MPa | Active outside envelope | Active abs mismatch MAE MPa |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Overlap with active curve | 577 | 2021-12-16 to 2023-12-26 | 6.0 | 2.104 | 2.205 | 575 | 15.224 |
| After active curve | 487 | 2023-12-27 to 2025-09-04 | 6.0 | 2.143 | 2.233 | n/a | n/a |

## Candidate Policies

| Candidate | Rows | Date range | Compared | After active | Pressure p50 MPa | Overlap MAE MPa | Delta to preferred MAE MPa | Delta p90 MPa |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `all_valid_median` | 1064 | 2021-12-16 to 2025-09-04 | 577 | 487 | -7.564 | 16.425 | 1.395 | 1.557 |
| `rh5_only` | 1037 | 2022-01-11 to 2025-09-04 | 550 | 487 | -8.135 | 15.244 | 0.793 | 0.950 |
| `rh5_rh6_below95_median` | 1062 | 2021-12-16 to 2025-09-04 | 575 | 487 | -9.160 | 14.720 | 0.335 | 0.950 |
| `rh5_rh6_mean` | 1063 | 2021-12-16 to 2025-09-04 | 576 | 487 | -8.862 | 15.146 | 0.000 | 0.000 |
| `rh5_rh6_median` | 1063 | 2021-12-16 to 2025-09-04 | 576 | 487 | -8.862 | 15.146 | 0.000 | 0.000 |
| `rh6_only` | 1059 | 2021-12-16 to 2025-09-04 | 572 | 487 | -9.639 | 14.352 | 0.777 | 0.950 |

## Largest Daily Candidate Spread

| Date | Regime | Candidates | Pressure range MPa | Pressure min | Pressure median | Pressure max | Active pressure | Active inside envelope |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2022-03-16 | compared_to_active_curve | 6 | 17.878 | -25.539 | -8.818 | -7.662 | -23.456 | True |
| 2022-03-20 | compared_to_active_curve | 6 | 17.787 | -25.561 | -8.528 | -7.774 | -22.554 | True |
| 2022-03-17 | compared_to_active_curve | 6 | 9.512 | -17.204 | -8.847 | -7.692 | -23.227 | False |
| 2022-03-07 | compared_to_active_curve | 6 | 8.130 | -15.537 | -8.632 | -7.407 | -25.631 | False |
| 2022-03-19 | compared_to_active_curve | 6 | 7.987 | -15.733 | -8.514 | -7.747 | -22.775 | False |
| 2022-03-05 | compared_to_active_curve | 6 | 6.340 | -13.699 | -8.607 | -7.358 | -26.136 | False |
| 2022-01-10 | compared_to_active_curve | 5 | 2.340 | -8.188 | -8.188 | -5.848 | -38.203 | False |
| 2022-01-31 | compared_to_active_curve | 6 | 2.333 | -8.564 | -7.517 | -6.230 | -34.507 | False |
| 2022-01-28 | compared_to_active_curve | 6 | 2.324 | -8.502 | -7.448 | -6.178 | -35.165 | False |
| 2022-01-27 | compared_to_active_curve | 6 | 2.320 | -8.488 | -7.433 | -6.168 | -35.377 | False |

## Interpretation

The preferred RH5/RH6-median curve is a policy choice based on the cleanest copied open-twin sensors, not a fit to the active OGS curve.
Over the overlap, the active curve is outside the local candidate pressure envelope on 575 daily envelope rows.
That mismatch is larger than an implementation detail: it means the active OGS boundary curve likely used different source data, filtering, constants, or time handling than the copied RH workbooks.

The post-active rows show that the copied RH workbooks can extend the boundary candidate beyond the current 2023-12-26 active curve end, but no extension should be accepted until the provenance and sensor-screening questions are answered.

## Generated Files

- `envelope_csv`: `inversion_workflow/processed_observations/rh_boundary_uncertainty_envelope.csv`
- `candidate_audit_csv`: `inversion_workflow/processed_observations/rh_boundary_uncertainty_audit.csv`
- `summary_json`: `inversion_workflow/processed_observations/rh_boundary_uncertainty_summary.json`
- `markdown`: `inversion_workflow/processed_observations/rh_boundary_uncertainty.md`
