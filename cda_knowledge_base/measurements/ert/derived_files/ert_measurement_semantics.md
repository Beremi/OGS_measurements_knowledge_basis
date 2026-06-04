# ERT Measurement Semantics Audit

This audit keeps the electrical-resistivity measurement stream separate from
water content, saturation, and permeability.  ERT can become a strong spatial
state residual only after the calibration, projection support, and OGS output
sampling gates are all satisfied.

## Key Counts

- ERT archive folders: 61
- VTK files in archive inventory: 1675
- Timestep rows: 1691
- Timesteps with matching VTK: 1675
- Timesteps missing matching VTK: 16
- State-target ERT rows: 1691
- Paired NMR/resistivity calibration rows: 72
- ERT projection lookup rows: 5966
- ERT cells inside an OGS cell: 4676
- ERT cells inside approximate 1.5 m support: 2194
- Rows ready after OGS output and current support screen: 2035

## What ERT Observes

ERT observes an electrical response that has already been inverted to a bulk
resistivity field on the ERT inversion mesh.  It is not a direct measurement
of saturation, volumetric water content, pressure, or permeability.  In the
current workflow it enters only through a forward observation path:

```text
OGS S_l and porosity -> theta_model = porosity * S_l
theta_model -> rho_pred using a local empirical theta-resistivity relation
rho_pred -> ERT/common support -> log10-resistivity residual
```

## Calibration Relation

- Recommended relation: `kruschwitz_model_data2019`
- Equation: `rho_ohm_m = 1.108 * theta_fraction ** -1.58`
- Calibrated theta range: 0.01 to 0.18
- Recommended-relation resistivity range: 16.642 to 1601.5 ohm m
- Niche-4 paired NMR/resistivity diagnostic RMSE: 0.2021 log10 resistivity units

| Relation | Role | Points | a | b | RMSE log10 rho | Theta range | Gate |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `nmr_pairs_all` | diagnostic_or_rejected_calibration_relation | 72 | 1.0876 | -1.6803 | 0.1813 | 0.0752-0.172 | retain_for_sensitivity_or_diagnostics_only |
| `nmr_pairs_N3` | diagnostic_or_rejected_calibration_relation | 37 | 6.6662 | -0.66675 | 0.07042 | 0.101-0.172 | retain_for_sensitivity_or_diagnostics_only |
| `nmr_pairs_N4` | diagnostic_or_rejected_calibration_relation | 35 | 10.699 | -0.74299 | 0.2021 | 0.0752-0.15 | retain_for_sensitivity_or_diagnostics_only |
| `kruschwitz_resistivity` | diagnostic_or_rejected_calibration_relation | 18 | 0.7293 | -0.82971 | 0.04763 | 0.01-0.18 | retain_for_sensitivity_or_diagnostics_only |
| `kruschwitz_model_data2019` | default_first_test_theta_to_resistivity_relation | 18 | 1.108 | -1.58 | 4.41e-16 | 0.01-0.18 | usable_after_ogs_theta_sampling_and_spatial_support_confirmation |
| `kruschwitz_old_fit` | diagnostic_or_rejected_calibration_relation | 18 | 1.6866 | -1.325 | 6.103e-16 | 0.01-0.18 | retain_for_sensitivity_or_diagnostics_only |

## Spatial Support

The current projection is a centroid lookup from a reference ERT VTK mesh to
the OGS bulk mesh.  It uses the explicit provisional transform
`model_x = raw_x`, `model_y = raw_y + 500`.  This is a reproducible support
bridge, not a full ERT forward solver.

- Sample log10 resistivity range in the reference VTK: min=0.47776, p50=1.3493, max=2.5248

| Projection group | Rows | Inside OGS cell | Approx. support | Ready after OGS output | Median nearest OGS distance m |
| --- | ---: | ---: | ---: | ---: | ---: |
| `False | False` | 3772 | 2641 | 0 | 0 | 0.059609 |
| `True | False` | 159 | 0 | 159 | 0 | 0.026325 |
| `True | True` | 2035 | 2035 | 2035 | 2035 | 0.0093087 |

## Activation Decision

- Do not use ERT as measured saturation or measured permeability.
- Do not activate field residuals for the 16 timestep rows without matching VTK members.
- Do not activate numerical ERT residuals until OGS outputs are sampled and the coordinate transform plus exact 35 cm-in-rock/near-niche support mask are confirmed.
- When activated, use log10-resistivity residuals with aggregation or support weights; neighbouring ERT inversion cells are correlated and should not be counted as independent point measurements.

## Generated Files

- `timestep_audit`: `inversion_workflow/processed_observations/ert_measurement_semantics_timestep_audit.csv`
- `relation_audit`: `inversion_workflow/processed_observations/ert_measurement_semantics_relation_audit.csv`
- `projection_group_summary`: `inversion_workflow/processed_observations/ert_measurement_semantics_projection_groups.csv`
- `summary`: `inversion_workflow/processed_observations/ert_measurement_semantics_summary.json`
- `markdown`: `inversion_workflow/processed_observations/ert_measurement_semantics.md`
