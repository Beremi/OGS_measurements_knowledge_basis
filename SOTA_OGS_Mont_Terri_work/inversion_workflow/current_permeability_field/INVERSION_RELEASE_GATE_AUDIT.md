# Inversion Release Gate Audit

This audit verifies that prepared OGS runs still obey the staged parameter-release plan.
The current allowed release is narrow: `k_i_rd` may vary as the active permeability
tensor-magnitude field, while `n_rd` porosity and all retention, mechanical, thermal,
boundary, and initialization parameters remain fixed until their gates are satisfied.

- Overall status: `pass`
- Runs audited: 1
- Checks: 20
- Failures: 0
- Warnings: 0

## Run Summary

| Run | Status | Failures | Warnings | Output variables |
| --- | --- | ---: | ---: | --- |
| `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` | `pass` | 0 | 0 | `pressure, saturation, temperature, displacement, porosity` |

## Non-Passing Checks

| Run | Check | Status | Detail |
| --- | --- | --- | --- |
| all | all checks | `pass` | no warnings or failures |

## Interpretation

- A passing audit means the candidate run varies the mesh permeability field while
  preserving the staged fixed-parameter assumptions recorded in the release plan.
- It does not mean OGS has executed or that the fit is physically accepted; state
  residuals still require actual OGS output VTU files.
- Any failure here should be treated as a hard stop before ranking the candidate,
  because it means the inverse problem no longer matches the documented stage.
