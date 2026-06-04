# Permeability Residual Conflict Audit

This audit explains the remaining direct pulse-test residuals for the current accepted field.
It is not a new OGS run and it does not promote additional measurement streams into the likelihood.

## Current Direct Fit

- Mesh: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu`
- Active direct rows: 75
- Direct objective: 269.818057
- Weighted RMSE: 1.610715 log10(k)
- Weighted mean absolute residual: 1.229550 log10(k)
- Max absolute residual: 3.474424 log10(k)

## Residual Counts

- Residual bands: `{'abs_1_to_2_log10': 27, 'abs_lt_0p5_log10': 27, 'abs_2_to_3_log10': 15, 'abs_ge_3_log10': 6}`
- Residual signs: `{'underpredicts_observation': 40, 'overpredicts_observation': 25, 'zero_residual': 10}`
- Configured scalar feasibility: `{'observed_inside_configured_scalar_range': 73, 'observed_above_configured_scalar_range': 2}`
- Recommended next actions: `{'review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs': 46, 'locally_consistent_under_current_log10_sigma': 27, 'review_sampler_bounds_tensor_shape_or_measurement_interpretation_before_more_spatial_sampling': 2}`
- Active rows with |residual| >= 1 log10: 48
- Active rows with |residual| >= 2 log10: 21
- Active rows outside configured scalar range: 2

## Segment Summary

| Segment | Rows | Mean residual | Mean abs | Max abs | Depth range [m] | Observed log10 range |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `BCD-A32` | 38 | -0.440 | 1.382 | 3.474 | 0.15-3.30 | -20.70 to -12.10 |
| `BCD-A33` | 37 | -0.390 | 1.169 | 3.452 | 0.17-3.30 | -21.00 to -14.10 |

## Largest Active Residuals

| Observation | Segment | Depth [m] | Observed | Predicted | Residual | Feasibility | Next action |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `perm_0005` | `BCD-A32` | 0.87 | -12.097 | -15.571 | -3.474 | observed_above_configured_scalar_range | review_sampler_bounds_tensor_shape_or_measurement_interpretation_before_more_spatial_sampling |
| `perm_0155` | `BCD-A32` | 0.87 | -12.097 | -15.571 | -3.474 | observed_above_configured_scalar_range | review_sampler_bounds_tensor_shape_or_measurement_interpretation_before_more_spatial_sampling |
| `perm_0169` | `BCD-A32` | 0.85 | -19.046 | -15.571 | +3.474 | observed_inside_configured_scalar_range | review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs |
| `perm_0181` | `BCD-A33` | 0.55 | -14.097 | -17.548 | -3.452 | observed_inside_configured_scalar_range | review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs |
| `perm_0015` | `BCD-A33` | 0.55 | -14.097 | -17.548 | -3.452 | observed_inside_configured_scalar_range | review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs |
| `perm_0195` | `BCD-A33` | 0.59 | -21.000 | -17.548 | +3.452 | observed_inside_configured_scalar_range | review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs |
| `perm_0156` | `BCD-A32` | 1.01 | -14.523 | -16.810 | -2.287 | observed_inside_configured_scalar_range | review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs |
| `perm_0006` | `BCD-A32` | 1.01 | -14.523 | -16.810 | -2.287 | observed_inside_configured_scalar_range | review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs |
| `perm_0170` | `BCD-A32` | 0.95 | -19.097 | -16.810 | +2.287 | observed_inside_configured_scalar_range | review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs |
| `perm_0157` | `BCD-A32` | 1.15 | -15.097 | -17.247 | -2.151 | observed_inside_configured_scalar_range | review support_geometry_gas_to_water_conversion_or_uncertainty_before_more_ogs |

## Interpretation

2 active rows are outside the configured scalar multiplier range; more spatial sampling within the same scalar-bounded family cannot close those rows without revisiting bounds, tensor-shape release, or measurement interpretation.

## Outputs

- Row audit: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_residual_conflict_audit.csv`
- Segment summary: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_residual_segment_summary.csv`
- Support-cell audit: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/permeability_residual_support_cell_audit.csv`
