# Taupe/TDR Observation Operator

This file documents the current model-facing use of the Taupe/TDR workbook.

## Current Status

- Status: `trend_operator_ready_absolute_calibration_pending`
- Operator rows: 5088
- Sensor/band series: 24
- Date range: 2019-12-01 to 2025-10-10
- Rows with mapped trend operator: 2544
- Recommended numerical role: trend diagnostic; not an active absolute saturation likelihood.

The robust operator is a within-series temporal anomaly.  For each sensor and EDZ band, the first finite workbook values define a baseline, and later values are stored as raw, relative, and robustly standardized anomalies.  The model-side quantity is the same band average of `theta_model = porosity * liquid_saturation`; its change from the matching baseline output should be compared to the Taupe trend.  This supports trend diagnostics without assuming that the workbook value is already an absolute saturation.

## Absolute Candidate Conversions

The CSV also records three candidate absolute interpretations for every row:

- `theta_fraction_if_taupe_value_is_vol_percent`: treats the workbook value as volumetric water-content percent.
- `theta_fraction_if_taupe_value_is_topp_epsilon`: treats the value as dielectric permittivity in the Topp et al. empirical soil relation.
- `theta_fraction_if_linear_mixing_epsilon_rock_6`: treats the value as dielectric permittivity in the local linear mixing formula with `epsilon_rock = 6` and `epsilon_water = 80`.

These are diagnostics, not default likelihoods.  The workbook name suggests water-content processing, but the presentation material describes TAUPE as differential TDR / ARDP, so the absolute unit must be confirmed before assigning residual weights.

## Series Summary

| Series | Rows | Baseline | Scale | First | Final | Net standardized change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A3_0-10cm | 212 | 10.1725 | 0.015973 | 10.1931 | 10.1331 | -3.756 |
| A3_0-50cm | 212 | 10.2415 | 0.0118847 | 10.2588 | 10.2069 | -4.366 |
| A3_10-20cm | 212 | 10.1965 | 0.0202854 | 10.2138 | 10.1282 | -4.220 |
| A3_20-30cm | 212 | 10.239 | 0.019986 | 10.2486 | 10.1756 | -3.655 |
| A3_30-40cm | 212 | 10.2608 | 0.0140617 | 10.2864 | 10.2241 | -4.430 |
| A3_40-50cm | 212 | 10.3421 | 0.0173421 | 10.3554 | 10.3818 | 1.524 |
| A4_0-10cm | 212 | 10.2024 | 0.0286862 | 10.1932 | 10.239 | 1.599 |
| A4_0-50cm | 212 | 10.2409 | 0.00906439 | 10.2198 | 10.2285 | 0.959 |
| A4_10-20cm | 212 | 10.2559 | 0.0104129 | 10.2746 | 10.2055 | -6.640 |
| A4_20-30cm | 212 | 10.2625 | 0.0176038 | 10.1942 | 10.2381 | 2.495 |
| A4_30-40cm | 212 | 10.3454 | 0.0150993 | 10.3307 | 10.2617 | -4.570 |
| A4_40-50cm | 212 | 10.3896 | 0.0229423 | 10.407 | 10.2544 | -6.649 |
| A7_0-10cm | 212 | 10.189 | 0.159096 | 10.1938 | 10.533 | 2.132 |
| A7_0-50cm | 212 | 10.3043 | 0.126816 | 10.3094 | 10.6782 | 2.908 |
| A7_10-20cm | 212 | 10.3295 | 0.113298 | 10.3414 | 10.687 | 3.051 |
| A7_20-30cm | 212 | 10.4058 | 0.090901 | 10.4034 | 10.8255 | 4.644 |
| A7_30-40cm | 212 | 10.4203 | 0.0937399 | 10.4395 | 10.8612 | 4.499 |
| A7_40-50cm | 212 | 10.4714 | 0.0799219 | 10.4865 | 10.9698 | 6.048 |
| A8_0-10cm | 212 | 9.91933 | 0.108016 | 9.87127 | 10.114 | 2.247 |
| A8_0-50cm | 212 | 10.0063 | 0.0847028 | 9.97487 | 10.1389 | 1.936 |
| A8_10-20cm | 212 | 10.0388 | 0.0884125 | 10.0123 | 10.1563 | 1.630 |
| A8_20-30cm | 212 | 10.0725 | 0.0683313 | 10.0533 | 10.1522 | 1.447 |
| A8_30-40cm | 212 | 10.0876 | 0.0714612 | 10.07 | 10.166 | 1.344 |
| A8_40-50cm | 212 | 10.0415 | 0.067734 | 10.0205 | 10.1267 | 1.569 |

## Candidate Sanity Counts

- Value as water-content percent gives saturation within [0, 1] for 2120 of 5088 rows.
- Topp epsilon interpretation gives saturation within [0, 1] for 0 of 5088 rows.
- Linear-mixing epsilon interpretation with `epsilon_rock = 6` gives saturation within [0, 1] for 2544 of 5088 rows.

These counts are only physical-range diagnostics.  They do not prove the correct calibration.

## Remaining Blocker

Confirm whether Taupe_WC workbook values are calibrated volumetric water-content percent, apparent relative dielectric permittivity, or another ARDP-derived proxy before assigning absolute residual weights.

After OGS state outputs exist, this operator can be used immediately for Taupe trend diagnostics.  Promoting it to an active numerical objective needs a documented Taupe unit/calibration choice or a defensible trend-only likelihood.
