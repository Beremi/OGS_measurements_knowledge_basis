# Permeability Measurement Semantics Audit

This audit records how the CD-A permeability pulse-test rows should be interpreted
before they are used as inverse-problem observations.  It is deliberately stricter
than a workbook inventory because the measurements are gas pulse tests on finite
borehole intervals, while the OGS unknown is an intrinsic permeability tensor field.

## Key Counts

- Interpreted target rows: 204
- Positive interpreted permeability rows: 200
- Rows usable in the current OGS direct objective: 75
- Missing-geometry groups: 5
- Pressure-decay rows retained separately: 6687
- Pressure-decay interval count: 32

Target status counts:

| Status | Rows |
| --- | ---: |
| `mapped_inside_mesh` | 75 |
| `mapped_outside_mesh` | 27 |
| `missing_segment_geometry` | 98 |
| `not_usable_missing_or_nonpositive_permeability` | 4 |

Semantic activation gates:

| Gate | Rows |
| --- | ---: |
| `active_direct_log_intrinsic_permeability_candidate` | 75 |
| `excluded_current_mesh_outside_domain` | 27 |
| `excluded_missing_or_nonpositive_interpreted_value` | 4 |
| `excluded_pending_endpoint_geometry_or_digitized_trace` | 98 |

## What The Test Observes

- Source workbooks report interpreted permeability/transmissibility values and raw pressure-decay traces.
- The local HERMES slides describe a modified COMDRILL double-piston packer, 10 cm static interval, nitrogen injection up to 1 bar, and pressure monitoring after injection.
- The CD-A characterization paper states that the pulse tests determine intrinsic permeability of a 3D volume around the 10 cm borehole interval, with about half an order of magnitude experimental/evaluation error.
- Klinkenberg's gas-permeability result means the apparent gas permeability is pressure dependent; a liquid-equivalent/intrinsic value requires slippage/test-condition interpretation.

Therefore the active row is a noisy scalar interval observation of intrinsic
permeability.  It is not hydraulic conductivity, not liquid relative
permeability, not saturation, and not a direct cell-wise tensor component.

## Model-Side Operator

Current active comparison:

```text
residual = log10(k_pred_m2) - log10(k_obs_m2)
k_pred  = interval-weighted directional response e^T K e from k_i_rd
sigma   = 0.5 log10 units for the first-pass likelihood
```

The directional response is a pragmatic first observation operator.  A stricter
future operator would replace the nominal 10 cm along-borehole window with a
test-specific pressure-transient sensitivity kernel, but the current data do not
contain enough test-geometry and interpretation metadata to justify that level.

## Value Ranges

- All positive rows log10(k/m2): min=-21.301, p50=-19.097, max=-12.002
- Currently usable rows log10(k/m2): min=-21, p50=-17.222, max=-12.097

Lowest positive interpreted rows:

| Observation | Segment | Twin | Direction | Depth m | k m2 | log10 k | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| perm_0131 | BCD-A25 | missing | horizontal | 1.25 | 5.000e-22 | -21.3 | missing_segment_geometry |
| perm_0043 | BCD-A35 | closed | horizontal | 0.59 | 1.000e-21 | -21 | mapped_outside_mesh |
| perm_0141 | BCD-A25 | missing | horizontal | 0.75 | 1.000e-21 | -21 | missing_segment_geometry |
| perm_0073 | BCD-A27 | closed | horizontal | 0.75 | 1.000e-21 | -21 | missing_segment_geometry |
| perm_0195 | BCD-A33 | open | vertical | 0.59 | 1.000e-21 | -21 | mapped_inside_mesh |
| perm_0134 | BCD-A25 | missing | horizontal | 3.3 | 2.000e-21 | -20.7 | missing_segment_geometry |
| perm_0036 | BCD-A34 | closed | vertical | 1.25 | 2.000e-21 | -20.7 | mapped_outside_mesh |
| perm_0173 | BCD-A32 | open | horizontal | 1.25 | 2.000e-21 | -20.7 | mapped_inside_mesh |

Highest positive interpreted rows:

| Observation | Segment | Twin | Direction | Depth m | k m2 | log10 k | Status |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| perm_0086 | BFM-D19 | open | nearly horizontal | 1.2 | 9.950e-13 | -12 | missing_segment_geometry |
| perm_0087 | BFM-D19 | open | nearly horizontal | 1.7 | 9.300e-13 | -12.03 | missing_segment_geometry |
| perm_0088 | BFM-D19 | open | nearly horizontal | 1.7 | 8.270e-13 | -12.08 | missing_segment_geometry |
| perm_0005 | BCD-A32 | open | horizontal | 0.87 | 8.000e-13 | -12.1 | mapped_inside_mesh |
| perm_0155 | BCD-A32 | open | horizontal | 0.87 | 8.000e-13 | -12.1 | mapped_inside_mesh |
| perm_0085 | BFM-D19 | open | nearly horizontal | 1.2 | 6.800e-13 | -12.17 | missing_segment_geometry |
| perm_0089 | BFM-D19 | open | nearly horizontal | 0.7 | 2.080e-13 | -12.68 | missing_segment_geometry |
| perm_0029 | BCD-A34 | closed | vertical | 0.55 | 1.000e-13 | -13 | mapped_outside_mesh |

## Coverage By Segment

| Segment | Rows | Usable | Missing geometry | Outside mesh | log10 k min | log10 k median | log10 k max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `BCD-A32` | 38 | 38 | 0 | 0 | -20.699 | -16.849 | -12.097 |
| `BCD-A33` | 41 | 37 | 0 | 0 | -21 | -17.222 | -14.097 |
| `BCD-A24` | 30 | 0 | 30 | 0 | -20.301 | -17.872 | -13 |
| `BCD-A25` | 30 | 0 | 30 | 0 | -21.301 | -19.398 | -13 |
| `BCD-A26` | 15 | 0 | 15 | 0 | -20.222 | -19.699 | -14.222 |
| `BCD-A27` | 15 | 0 | 15 | 0 | -21 | -19.398 | -16.097 |
| `BCD-A34` | 15 | 0 | 0 | 15 | -20.699 | -19.301 | -13 |
| `BCD-A35` | 12 | 0 | 0 | 12 | -21 | -19.398 | -19.046 |
| `BFM-D19` | 8 | 0 | 8 | 0 | -13.996 | -12.425 | -12.002 |

## Activation Rules

- Use only positive, in-mesh rows with labelled endpoint geometry for the current direct objective.
- Keep missing-geometry BCD-A24/25/26/27 and BFM-D19 rows visible, but inactive until endpoint geometry or an approved digitized trace exists.
- Keep mapped-outside rows inactive for the current Niche-4 mesh unless the model domain is expanded or a deliberate support mapping is approved.
- Keep the residual in log10 permeability space because values span many orders of magnitude and the stated measurement/evaluation error is multiplicative.
- Treat horizontal/vertical contrasts as evidence for anisotropy and EDZ heterogeneity, not as proof of a single tensor component at a single cell.

## Source Basis

- Local HERMES modelling slides: permeability method details on PDF p. 5.
- Ziefle et al. characterization paper: pulse-test setup/results in Section 4.3 and permeability interpretation in later discussion sections.
- Klinkenberg 1941: gas apparent permeability depends on reciprocal mean pressure; extrapolated infinite-pressure value is the medium permeability constant.
- Marschall et al. 2005: Opalinus Clay gas transport depends on intrinsic permeability, capillary threshold, saturation, and possible dilatancy at high gas pressure; this supports keeping gas-test interpretation separate from OGS liquid relative permeability.

## Generated Files

- `row_audit`: `inversion_workflow/processed_observations/permeability_measurement_semantics_audit.csv`
- `group_summary`: `inversion_workflow/processed_observations/permeability_measurement_semantics_group_summary.csv`
- `summary`: `inversion_workflow/processed_observations/permeability_measurement_semantics_summary.json`
- `markdown`: `inversion_workflow/processed_observations/permeability_measurement_semantics.md`
