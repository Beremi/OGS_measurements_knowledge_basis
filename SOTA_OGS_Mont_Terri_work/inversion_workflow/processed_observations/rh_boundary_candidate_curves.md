# RH Boundary Candidate Curves

This file records local RH-derived open-niche pressure-boundary curve candidates from the copied OT_RH5-8 workbooks.
The curves are reproducible candidate forcings and extension evidence, not verified replacements for the active OGS curve.

## Status

- Status: `rh_boundary_candidate_curves_generated_provenance_still_unverified`
- Candidate curves: 6
- Candidate curve rows: 6348
- Preferred policy candidate: `rh5_rh6_median`
- Lowest overlap-MAE candidate: `rh6_only`
- Activation gate: Do not replace the active OGS boundary curve or release RH/retention likelihoods until BGR/Gesa confirm curve provenance, sensor selection, time axis, conversion constants, and extension policy.

## Candidate Summary

| Candidate | Rows | Date range | Compared | After active curve | P50 RH % | P50 pressure MPa | Median abs mismatch MPa | MAE MPa | RMSE MPa |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `all_valid_median` | 1064 | 2021-12-16 to 2025-09-04 | 577 | 487 | 95.105 | -7.564 | 12.617 | 16.425 | 19.281 |
| `rh5_only` | 1037 | 2022-01-11 to 2025-09-04 | 550 | 487 | 94.744 | -8.135 | 11.425 | 15.244 | 18.023 |
| `rh5_rh6_below95_median` | 1062 | 2021-12-16 to 2025-09-04 | 575 | 487 | 94.103 | -9.160 | 12.164 | 14.720 | 17.565 |
| `rh5_rh6_mean` | 1063 | 2021-12-16 to 2025-09-04 | 576 | 487 | 94.289 | -8.862 | 12.215 | 15.146 | 18.094 |
| `rh5_rh6_median` | 1063 | 2021-12-16 to 2025-09-04 | 576 | 487 | 94.289 | -8.862 | 12.215 | 15.146 | 18.094 |
| `rh6_only` | 1059 | 2021-12-16 to 2025-09-04 | 572 | 487 | 93.803 | -9.639 | 11.212 | 14.352 | 17.438 |

## Interpretation

The policy-preferred local curve is the RH5/RH6 median because RH5/RH6 are the cleanest copied open-twin thermo-hygrometer streams. Matching the active OGS curve is not used as the selection rule: the current evidence already shows that the active curve is not a direct reconstruction of these copied workbooks.

The generated XML files start only where local RH data exist. They therefore cannot replace the full active OGS boundary without an explicit pre-2021 policy and a post-2023 extension policy.

## Generated Files

- `candidate_curves_csv`: `inversion_workflow/processed_observations/rh_boundary_candidate_curves.csv`
- `summary_csv`: `inversion_workflow/processed_observations/rh_boundary_candidate_curve_summary.csv`
- `summary_json`: `inversion_workflow/processed_observations/rh_boundary_candidate_curve_summary.json`
- `markdown`: `inversion_workflow/processed_observations/rh_boundary_candidate_curves.md`
