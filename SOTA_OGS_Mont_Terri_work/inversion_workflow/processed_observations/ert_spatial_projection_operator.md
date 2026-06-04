# ERT Spatial Projection Operator

This file documents the current spatial support lookup between the ERT inversion mesh and the OGS bulk mesh.

## Current Status

- Status: `projection_lookup_ready_transform_assumed_ogs_outputs_pending`
- Reference VTK: `Niche open/2019/11-2019/dcinv.result_01.vtk`
- ERT cells: 5966
- ERT timesteps with matching VTK: 1675 of 1691
- OGS inside-cell rows: 4676
- Approximate 1.5 m centre-support rows: 2194
- Rows ready for residual after OGS output and support confirmation: 2035
- Calibration relation: `kruschwitz_model_data2019`

## Coordinate Transform

- `model_x = raw_x * 1 + 0`
- `model_y = raw_y * 1 + 500`

Raw ERT bounds: `{'min': [-10.0, -510.0, 0.0], 'max': [10.0, -490.0, 0.0]}`

Transformed ERT centroid bounds: `{'min': [-9.769414469845334, -9.814676013259998], 'max': [9.819158254042334, 9.782842292063341]}`

OGS mesh bounds: `{'min': [-5.0, -5.0], 'max': [5.0, 5.0]}`

The +500 m shift in the second ERT coordinate is recorded as an explicit assumption.  It places the ERT inversion domain around the local OGS coordinate frame, but it still needs confirmation against the agreed ERT/FEM coordinate convention.

## Residual Path

1. Sample OGS `theta_model = porosity * liquid_saturation` at `ogs_lookup_cell_id` for the ERT lookup rows.
2. Convert sampled theta to resistivity with `ert_water_content_resistivity_operator.csv`.
3. Compare in log10 resistivity space against the ERT VTK `Resistivity(log10)` field.
4. Use the support flags to restrict residuals to the agreed near-niche ERT support.

## Remaining Blocker

Confirm the ERT-to-OGS coordinate transform and exact near-niche support mask, then sample OGS theta outputs and form log-resistivity residuals.

The lookup is intentionally not an active objective term yet: it is a reproducible geometry bridge for later OGS state-output evaluation.
