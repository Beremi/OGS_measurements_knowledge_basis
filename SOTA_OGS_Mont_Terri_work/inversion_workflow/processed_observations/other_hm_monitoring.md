# Other HM Monitoring Inventory

This inventory structures the secondary CD-A hydromechanical monitoring material
that is present as meeting reports, presentations and the Tecplot layout.

## Generated Tables

| File | Rows | Contents |
| --- | ---: | --- |
| `other_hm_visualisation_zones.csv` | 84 | Tecplot zones from `VisualisationCDA.dat`, classified by measurement/support role and coordinate bounds. |
| `other_hm_visualisation_text_labels.csv` | 11 | Display labels from the Tecplot layout legend. |
| `other_hm_levelling_displacements.csv` | 12 | Pointwise vertical displacement values from the precision-levelling slides. |
| `other_hm_qualitative_targets.csv` | 10 | Structured HM validation statements from the 2026 minutes, modelling slides and HERMES input note. |
| `other_hm_monitoring_summary.json` | 1 | Machine-readable counts and readiness status. |

## Layout Content

- Tecplot zones parsed: 84.
- Layout labels parsed: 11.
- Largest zone by nodes: `open_twin_LS` with 1,499,860 nodes.

| Classified role | Zones |
| --- | ---: |
| `convergence_points` | 2 |
| `evapometer` | 1 |
| `extensometer` | 5 |
| `fracture_or_crack_geometry` | 22 |
| `laser_scan_geodetic_support` | 3 |
| `laser_scan_surface` | 2 |
| `mini_piezometer` | 1 |
| `miniprisma_geodesy` | 12 |
| `niche_geometry` | 8 |
| `nmr_support` | 19 |
| `permeability_support` | 2 |
| `rh_suction_support` | 6 |
| `taupe_tdr_support` | 1 |

## Numeric Levelling Summary

The levelling slides provide the only pointwise numeric deformation values in
this secondary-HM bundle. Values are height differences from the first
measurement on 2022-08-29/30 to the 2026-03 campaign.

| Point | Location | Height difference [mm] |
| --- | --- | ---: |
| `CDA-O1` | Open Twin | -2.1 |
| `57` | Galerie 18 | -0.1 |
| `CDA-O2` | Open Twin | 0.2 |
| `58` | Galerie 18 | 0.3 |
| `CDA-O3` | Open Twin | 0.4 |
| `CDA-O4` | Open Twin | 0.4 |
| `CDA-C5` | Closed Twin | 0.5 |
| `CDA-C3` | Closed Twin | 0.6 |
| `CDA-C1` | Closed Twin | 0.6 |
| `CDA-C2` | Closed Twin | 0.8 |
| `CDA-O5` | Open Twin | 0.9 |
| `CDA-C4` | Closed Twin | 1.3 |

## Model-Entry Status

- Mini-piezometers are the cleanest future pressure residual candidates, but
  the Geoscope numeric series are not in the currently collected files.
- Extensometer and crackmeter information is currently trend/status evidence;
  the closed-niche BCD-A9/A10 extensometer failure since September 2025 must
  be respected before using those records.
- Levelling values can become displacement-validation targets after the survey
  reference frame and OGS displacement output support are aligned.
- Laser-scan objects are present in the Tecplot layout, but the statistical
  laser-scan update mentioned in the minutes is not present as a raw data
  export in this catalogue.

## Immediate Missing Raw Exports

- Geoscope time series for mini-piezometers BCD-A28 to BCD-A31.
- Geoscope extensometer and crackmeter time series, including instrument-status
  metadata around the September 2025 closed-niche failure.
- Laser-scan statistical interpretation files from the 2026-04-20 update.
- A table/spreadsheet version of the levelling survey if residual weighting
  beyond the slide-summary values is needed.

Run `build_other_hm_missing_numeric_request.py` to turn this list into an
email-ready request package with requested fields, source evidence, and
catalogue copies.
