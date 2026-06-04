# Suction/RH Measurement Semantics Audit

This audit separates the raw relative-humidity measurements, Kelvin-equation pressure conversion, active OGS boundary-curve comparison, and likelihood activation gates.

## Source Files

- RH workbooks: [OT_RH5.xlsx](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH5.xlsx), [OT_RH6.xlsx](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH6.xlsx), [OT_RH7.xlsx](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH7.xlsx), [OT_RH8.xlsx](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/OT_RH8.xlsx)
- Suction/RH location figure: [Location_suc.png](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/Location_suc.png)
- Phase 30 report: [RO_2013.4_3974_CD-A3 Phase 30_A21_TN-2025-12_signed.pdf](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/RO_2013.4_3974_CD-A3 Phase 30_A21_TN-2025-12_signed.pdf)
- TD minutes: [2026-05-11_TD517_CD-A_260507__Minutes.pdf](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf)
- TD modelling slides: [CD-A_Slides_TD_260427x.pdf](/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/suction_relative_humidity/source_files/CD-A_Slides_TD_260427x.pdf)

## Current Status

- Status: `boundary_forcing_semantics_ready_curve_provenance_unverified`
- RH rows: 4247
- Date range: 2021-12-16 to 2025-09-04
- Sensors: RH5, RH6, RH7, RH8
- Valid non-low-outlier rows: 4228
- Low-RH outlier rows: 19
- Open-twin >95% RH caution rows: 2492
- State-target rows: 4247 (4228 boundary-forcing rows marked usable in the target table).

The data should be used as boundary-condition evidence and retention-curve validation context, not as a mesh-cell point residual.  The active OGS open-niche pressure curve remains a provenance item until its preprocessing can be reproduced from RH/T data or documented by BGR/Gesa.

## Kelvin Conversion

- Formula used: `p_l_gauge = rho_l * R * T / M_w * ln(RH_fraction)`
- Assumed temperature: 298.15 K
- Assumed liquid density: 1095.0 kg/m3
- Kelvin coefficient: 150675312.70202932 Pa

| Quantity | Min | P50 | Max |
| --- | ---: | ---: | ---: |
| RH (%) | 13.188 | 95.3084 | 97.2722 |
| Kelvin gauge liquid pressure (MPa) | -305.248 | -7.24036 | -4.16728 |

## Active OGS Boundary Curve

- Active curve path: `inversion_workflow/runs/direct_fit_observation_run/08_08_open_niche_seasonal.xml`
- Curve rows: 845
- Curve pressure range: -53.2383 to -5.22589 MPa
- Curve-implied RH range at the same assumed T/rho: 70.2345% to 96.5911%
- Curve rows below the clean RH5/RH6 collected RH minimum: 772
- Compared RH rows inside the active curve time range: 2280
- Median absolute RH-minus-OGS pressure mismatch: 12.99802291936514 MPa
- Mean absolute RH-minus-OGS pressure mismatch: 16.318672497526755 MPa

The active curve spans much drier implied RH than the cleaner RH5/RH6 workbook evidence for much of its duration.  This supports the current interpretation: it is an existing model boundary condition, not yet a verified direct reconstruction of the collected RH workbooks.

## Sensor Summary

| Sensor | Rows | Date min | Date max | Low outliers | >95% caution | Preferred range | Compared | Outside curve | RH min | RH median | RH max | Median abs mismatch MPa | Recommended use |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| RH5 | 1042 | 2022-01-11 | 2025-09-04 | 0 | 387 | 655 | 555 | 487 | 94.0807 | 94.7497 | 95.9927 | 11.758 | preferred RH boundary evidence |
| RH6 | 1064 | 2021-12-16 | 2025-09-04 | 0 | 0 | 1064 | 577 | 487 | 93.3225 | 93.804 | 94.9883 | 11.359 | preferred RH boundary evidence |
| RH7 | 1071 | 2021-12-16 | 2025-09-04 | 7 | 1055 | 9 | 577 | 487 | 13.188 | 96.4184 | 97.2722 | 15.070 | retain with stronger quality screening because low/suspicious values occur |
| RH8 | 1070 | 2021-12-16 | 2025-09-04 | 12 | 1050 | 8 | 571 | 487 | 13.2027 | 95.4777 | 96.2194 | 13.257 | retain with stronger quality screening because low/suspicious values occur |

## Activation Rules

- Treat RH as vapour relative humidity converted to a boundary-pressure candidate; it is not measured permeability, saturation, or OGS cell pressure.
- Exclude the RH7/RH8 values below 50% RH unless the logger/sensor provenance is confirmed.
- Retain open-twin values above 95% RH with a reliability caution; they are not a clean calibration subset for thermo-hygrometers.
- Use RH5/RH6 preferentially for open-twin boundary reconstruction checks, because they do not contain the low-RH outlier episodes.
- Do not treat `08_08_open_niche_seasonal.xml` as a verified RH-derived forcing until the curve-generation workflow is reconstructed.

## Remaining Blocker

Reconstruct or document the provenance/preprocessing of 08_08_open_niche_seasonal.xml before treating the active OGS open-niche curve as a verified RH-derived forcing.

## Generated Audit Files

- `row_audit`: `inversion_workflow/processed_observations/rh_measurement_semantics_row_audit.csv`
- `sensor_summary`: `inversion_workflow/processed_observations/rh_measurement_semantics_sensor_summary.csv`
- `curve_semantics`: `inversion_workflow/processed_observations/rh_boundary_curve_semantics.csv`
- `summary`: `inversion_workflow/processed_observations/rh_measurement_semantics_summary.json`
- `markdown`: `inversion_workflow/processed_observations/rh_measurement_semantics.md`
