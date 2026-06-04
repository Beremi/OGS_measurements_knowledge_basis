# Taupe/TDR Series Weight Sensitivity Audit

This audit checks whether the Taupe/TDR trend diagnostic ranking changes when compared A3/A4 series, sensors, or EDZ bands are grouped differently.
It is diagnostic only and does not activate Taupe/TDR in the likelihood.

## Status

- Status: `taupe_series_weight_sensitivity_generated_not_active_likelihood`
- Runs evaluated: 66
- Compared series: 12
- Uncompared series: 12
- Distinct per-series winner runs: 8
- Best mean weighting-rank run: `adaptive_combined_001_length_0p050m` with mean rank 1.25
- Activation gate: Diagnostic only: this audit quantifies local sensitivity to Taupe/TDR trend grouping and weights. It does not confirm workbook units, sensor calibration, absolute saturation mapping, or residual uncertainty.

## Weighting Mode Winners

| Weighting mode | Winner | Aggregate rank | Mode rank | Aggregate MAE | Mode MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| `aggregate_row_weighted` | `adaptive_combined_001_length_0p050m` | 1.00 | 1.00 | 1.829884 | 1.829884 |
| `equal_series` | `adaptive_combined_001_length_0p050m` | 1.00 | 1.00 | 1.829884 | 1.829884 |
| `equal_sensor` | `adaptive_combined_001_length_0p050m` | 1.00 | 1.00 | 1.829884 | 1.829884 |
| `equal_edz_band` | `adaptive_combined_001_length_0p050m` | 1.00 | 1.00 | 1.829884 | 1.829884 |
| `a3_only_equal_series` | `local_bracketed_003_length_0p031m` | 3.00 | 1.00 | 1.832081 | 1.832425 |
| `a4_only_equal_series` | `adaptive_combined_002_length_0p050m_shift_0p750` | 2.00 | 1.00 | 1.830476 | 1.825056 |
| `drop_worst_series` | `adaptive_combined_001_length_0p050m` | 1.00 | 1.00 | 1.829884 | 1.656278 |
| `trim_best_worst_series` | `adaptive_combined_001_length_0p050m` | 1.00 | 1.00 | 1.829884 | 1.718737 |

## Top Runs By Mean Rank Across Weighting Modes

| Run | Kind | Aggregate MAE | Equal-series MAE | A3-only | A4-only | Drop-worst | Mean rank | Worst rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `adaptive_combined_001_length_0p050m` | adaptive_combined | 1.829884 | 1.829884 | 1.832770 | 1.826998 | 1.656278 | 1.25 | 2.00 |
| `adaptive_combined_002_length_0p050m_shift_0p750` | adaptive_combined | 1.830476 | 1.830476 | 1.835896 | 1.825056 | 1.657905 | 2.00 | 3.00 |
| `local_bracketed_003_length_0p031m` | local_smooth | 1.832081 | 1.832081 | 1.832425 | 1.831737 | 1.661512 | 7.88 | 44.00 |
| `production_sampler_round3_002_length_0p028m_shift_1p050` | production_sampler_round | 1.850646 | 1.850646 | 1.867682 | 1.833610 | 1.684112 | 10.38 | 50.00 |
| `production_sampler_round2_006_length_0p026m_shift_1p107` | production_sampler_round | 1.850755 | 1.850755 | 1.867203 | 1.834307 | 1.684104 | 10.88 | 52.00 |
| `optimizer_proposed_003_length_0p025m_shift_1p125` | optimizer_proposed | 1.851080 | 1.851080 | 1.867306 | 1.834855 | 1.684444 | 12.25 | 55.00 |
| `production_sampler_round3_001_length_0p028m` | production_sampler_round | 1.851241 | 1.851241 | 1.868395 | 1.834087 | 1.684586 | 12.75 | 51.00 |
| `production_sampler_round5_005_length_0p004m_shift_1p031` | production_sampler_round | 1.863067 | 1.863067 | 1.897637 | 1.828497 | 1.691816 | 13.50 | 23.00 |
| `production_sampler_round4_001_length_0p029m_shift_0p954` | production_sampler_round | 1.851897 | 1.851897 | 1.869071 | 1.834723 | 1.685112 | 13.88 | 53.00 |
| `lower_support_loop_002_002_length_0p004m_shift_1p020` | lower_support | 1.863117 | 1.863117 | 1.897657 | 1.828577 | 1.691864 | 14.88 | 24.00 |
| `regularized_ogs_candidate_001_length_0p025m` | regularized_ogs | 1.852588 | 1.852588 | 1.869105 | 1.836070 | 1.685739 | 15.38 | 58.00 |
| `broad_continuous_001_001_length_0p023m_shift_1p004` | broad_continuous | 1.854766 | 1.854766 | 1.874346 | 1.835185 | 1.688064 | 16.00 | 56.00 |
| `lower_support_loop_001_003_length_0p004m_shift_1p014` | lower_support | 1.863144 | 1.863144 | 1.897668 | 1.828620 | 1.691890 | 16.12 | 25.00 |
| `lower_support_loop_001_001_length_0p003m_shift_1p006` | lower_support | 1.863182 | 1.863182 | 1.897684 | 1.828681 | 1.691927 | 17.12 | 26.00 |
| `regularized_ogs_candidate_002_length_0p025m_shift_0p750` | regularized_ogs | 1.856246 | 1.856246 | 1.875812 | 1.836680 | 1.688317 | 17.25 | 59.00 |

## Most Discriminating Series

| Series | Sensor | EDZ band | MAE range | Best run | Best series MAE | Aggregate rank of best | Series/aggregate rank corr |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| `A3_10-20cm` | A3 | 10-20 | 0.196132 | `adaptive_combined_001_length_0p050m` | 1.054710 | 1.00 | 0.773 |
| `A3_40-50cm` | A3 | 40-50 | 0.165601 | `production_sampler_round3_002_length_0p028m_shift_1p050` | 3.682526 | 4.00 | 0.819 |
| `A4_20-30cm` | A4 | 20-30 | 0.152795 | `adaptive_combined_003_length_0p075m` | 3.495833 | 13.00 | 0.538 |
| `A4_40-50cm` | A4 | 40-50 | 0.135787 | `broad_continuous_loop_001_002_length_0p016m_shift_0p968` | 1.720360 | 63.00 | -0.927 |
| `A3_20-30cm` | A3 | 20-30 | 0.132221 | `local_bracketed_003_length_0p031m` | 1.075789 | 3.00 | 0.121 |
| `A4_0-50cm` | A4 | 0-50 | 0.121504 | `adaptive_combined_001_length_0p050m` | 2.042848 | 1.00 | 0.333 |
| `A3_0-50cm` | A3 | 0-50 | 0.111360 | `adaptive_combined_003_length_0p075m` | 1.126353 | 13.00 | -0.219 |
| `A3_0-10cm` | A3 | 0-10 | 0.098095 | `adaptive_combined_003_length_0p075m` | 2.839370 | 13.00 | -0.073 |
| `A4_10-20cm` | A4 | 10-20 | 0.086875 | `adaptive_combined_003_length_0p075m` | 1.081379 | 13.00 | 0.944 |
| `A4_30-40cm` | A4 | 30-40 | 0.080253 | `broad_continuous_loop_001_003_length_0p010m` | 1.351676 | 57.00 | -0.059 |
| `A3_30-40cm` | A3 | 30-40 | 0.043339 | `adaptive_combined_002_length_0p050m_shift_0p750` | 1.031292 | 2.00 | 0.148 |
| `A4_0-10cm` | A4 | 0-10 | 0.024485 | `broad_continuous_loop_001_001_length_0p015m` | 1.009974 | 51.00 | -0.316 |

## Interpretation

A stable winner across weighting modes would support using Taupe/TDR as a simple trend screen once calibration is accepted. A changing winner means grouped weights and uncertainty are part of the scientific gate, not an implementation detail.
A7/A8 remain unmapped in the current local OGS mesh support, so this audit is limited to the compared A3/A4 series.
