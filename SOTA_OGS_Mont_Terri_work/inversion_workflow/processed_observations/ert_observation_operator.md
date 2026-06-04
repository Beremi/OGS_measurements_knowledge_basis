# ERT Observation Operator

This file documents the current first-pass operator for using OGS water-content output in ERT comparisons.

## Recommended Relation

- Relation id: `kruschwitz_model_data2019`
- Model input: `theta = porosity * liquid_saturation` from sampled OGS output.
- Prediction: `rho_ohm_m = a * theta_fraction ** b`.
- `a = 1.108`
- `b = -1.58`
- Fit rows: 18
- Fit RMSE: 0.0000 log10(ohm m)
- Calibrated theta range: 0.0100 to 0.1800

The recommended relation is the smooth local workbook conversion column.  The Niche-4 paired NMR/resistivity fit is retained in the table as a diagnostic, but it has larger scatter and should not be treated as a finished ERT forward model.

## Spatial Projection Status

Confirm the ERT-to-OGS coordinate transform and exact near-niche support mask, then sample OGS theta outputs and form log-resistivity residuals.

ERT residuals should be formed in log-resistivity space and should retain explicit uncertainty for ERT inversion smoothing, electrode coverage, fractures, and mesh mismatch.

## Fitted Relations

| Relation id | Source subset | n | a | b | RMSE log10 rho | Recommended |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `nmr_pairs_all` | all N3+N4 paired NMR/resistivity rows | 72 | 1.08756 | -1.68032 | 0.1813 | no |
| `nmr_pairs_N3` | N3 paired NMR/resistivity rows | 37 | 6.66623 | -0.666747 | 0.0704 | no |
| `nmr_pairs_N4` | N4 paired NMR/resistivity rows | 35 | 10.6986 | -0.742988 | 0.2021 | no |
| `kruschwitz_resistivity` | Kruschwitz2004 workbook column resistivity | 18 | 0.729295 | -0.829714 | 0.0476 | no |
| `kruschwitz_model_data2019` | Kruschwitz2004 workbook column model_data2019 | 18 | 1.108 | -1.58 | 0.0000 | yes |
| `kruschwitz_old_fit` | Kruschwitz2004 workbook column old_fit | 18 | 1.6866 | -1.325 | 0.0000 | no |

## Coverage

- ERT timestep rows: 1691
- Rows with matching VTK member: 1675
- Rows missing matching VTK member: 16
- Spatial lookup rows: 5966
- Spatial projection-ready rows: 2035
- Reference VTK: `Niche open/2019/11-2019/dcinv.result_01.vtk`
