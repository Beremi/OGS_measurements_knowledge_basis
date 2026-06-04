# NMR Bound-Water Sensitivity

This audit quantifies the NMR caveat before NMR water-content rows are promoted
to numerical OGS state residuals.  The fixed current porosity is used as the
maximum model water content for saturated cells, because the model-side proxy is
`theta_model = porosity * liquid_saturation` and `S_l <= 1`.

- Fixed porosity used for the audit: `0.105`
- NMR target rows: 464
- Usable current-mesh rows: 287
- Rows whose uncorrected NMR water content exceeds fixed porosity: 315
- Usable rows whose uncorrected NMR water content exceeds fixed porosity: 162
- Usable-row required positive offset quantiles: p50=0.0019, p75=0.0108, p90=0.0259, p95=0.0402, max=0.1231

## Offset Scenarios

| Offset | Scope | Physical rows | Still above phi | Negative free-water rows | Physical fraction |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0.000 | `all_nmr_targets` | 149 | 315 | 0 | 0.321 |
| 0.000 | `usable_current_mesh_targets` | 125 | 162 | 0 | 0.436 |
| 0.005 | `all_nmr_targets` | 204 | 260 | 0 | 0.440 |
| 0.005 | `usable_current_mesh_targets` | 172 | 115 | 0 | 0.599 |
| 0.010 | `all_nmr_targets` | 252 | 212 | 0 | 0.543 |
| 0.010 | `usable_current_mesh_targets` | 210 | 77 | 0 | 0.732 |
| 0.015 | `all_nmr_targets` | 283 | 181 | 0 | 0.610 |
| 0.015 | `usable_current_mesh_targets` | 232 | 55 | 0 | 0.808 |
| 0.020 | `all_nmr_targets` | 303 | 161 | 0 | 0.653 |
| 0.020 | `usable_current_mesh_targets` | 241 | 46 | 0 | 0.840 |
| 0.030 | `all_nmr_targets` | 342 | 121 | 1 | 0.737 |
| 0.030 | `usable_current_mesh_targets` | 267 | 19 | 1 | 0.930 |
| 0.040 | `all_nmr_targets` | 367 | 96 | 1 | 0.791 |
| 0.040 | `usable_current_mesh_targets` | 270 | 16 | 1 | 0.941 |
| 0.050 | `all_nmr_targets` | 414 | 49 | 1 | 0.892 |
| 0.050 | `usable_current_mesh_targets` | 280 | 6 | 1 | 0.976 |
| 0.075 | `all_nmr_targets` | 442 | 5 | 17 | 0.953 |
| 0.075 | `usable_current_mesh_targets` | 271 | 1 | 15 | 0.944 |
| 0.100 | `all_nmr_targets` | 373 | 1 | 90 | 0.804 |
| 0.100 | `usable_current_mesh_targets` | 216 | 1 | 70 | 0.753 |

## High-Offset Mapping Labels

| Label | Rows | Required offset p95 | Required offset max | Observed theta max |
| --- | ---: | ---: | ---: | ---: |
| `NMR_4I` | 7 | 0.0984 | 0.1231 | 0.2281 |
| `NMR_4F` | 7 | 0.0655 | 0.0724 | 0.1774 |
| `NMR_4K` | 10 | 0.0604 | 0.0633 | 0.1683 |
| `NMR_4L` | 10 | 0.0558 | 0.0728 | 0.1778 |
| `NMR_4Q` | 7 | 0.0436 | 0.0448 | 0.1498 |
| `NMR_4G` | 7 | 0.0424 | 0.0427 | 0.1477 |
| `NMR_S` | 28 | 0.0404 | 0.0522 | 0.1572 |
| `NMR_4H` | 7 | 0.0399 | 0.0402 | 0.1452 |
| `NMR_4M` | 10 | 0.0319 | 0.0455 | 0.1505 |

## Activation Recommendation

- Do not activate absolute NMR theta residuals as theta_obs = phi*S_l without a bound/interlayer-water bias or error term.
- Use trend/anomaly residuals within each station/position as the first OGS-backed NMR comparison because constant bound-water offsets cancel to first order.
- If absolute NMR residuals are used, compare theta_obs = phi*S_l + b_label + epsilon with a non-negative label/campaign bias term or a group-specific model-error floor.
- Do not infer porosity from NMR alone; porosity remains fixed in the current stage because theta observations trade off directly with saturation and bound water.

## Interpretation

A single global bound-water subtraction is not a clean solution: large offsets
are needed for some seasonal labels, while the low seasonal values would become
negative free-water contents.  The safer first residual is therefore a
within-label trend/anomaly comparison, or an absolute comparison with explicit
label/campaign bias terms and an additional model-error floor.
