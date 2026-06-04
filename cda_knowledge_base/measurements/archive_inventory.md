# Measurement Archive Inventory

This file records the detailed ZIP/archive pass for the CD-A measurement catalogue. It complements the per-measurement README files by showing which archive members were inspected, copied out, extracted, or retained inside the raw archive.

The full row-level index is:

- [archive_member_catalog.csv](archive_member_catalog.csv) - 1,880 archive-member rows with archive path, member path, measurement class, size, copied measurement folders, local copied/extracted paths, and a short classification note.
- [source_file_manifest.csv](source_file_manifest.csv) - 206 copied/extracted source-file rows with measurement folder, relative path, size, extension, and SHA1 checksum.

## Coverage Summary

| Archive | Source location | Members inspected | Measurement classification | Local catalogue status |
| --- | --- | ---: | --- | --- |
| [SOTA___OGS___Mont_Terri.zip](../../SOTA___OGS___Mont_Terri.zip) | Workspace root | 19 files | Model projection inputs and report context | Archive copied to [model_projection_inputs/source_files](model_projection_inputs/source_files/SOTA___OGS___Mont_Terri.zip) and extracted to [model_projection_inputs/source_files/SOTA_OGS_Mont_Terri_zip](model_projection_inputs/source_files/SOTA_OGS_Mont_Terri_zip). It contains OGS XML/project files, report TeX/BibTeX, and one THM reference PDF, not measurement workbooks. |
| [ERT_meas_Niche_open.zip](../file_transfers/collected/2025-04-03_ert_open_twin/ERT_meas_Niche_open.zip) | TeamBeam, 2025-04-03 | 1,736 files | ERT | Raw archive copied to [ert/source_files](ert/source_files/ERT_meas_Niche_open.zip). Members are indexed in [archive_member_catalog.csv](archive_member_catalog.csv), but the 925 MB uncompressed VTK series is not exploded into duplicate loose files. |
| [CDA_N4_2D_250403.zip](../file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip) | TeamBeam, 2025-04-04 / 2025-04-11 | 22 files | Model projection inputs | Archive copied to [model_projection_inputs/source_files](model_projection_inputs/source_files/CDA_N4_2D_250403.zip) and extracted to [model_projection_inputs/source_files/CDA_N4_2D_250403](model_projection_inputs/source_files/CDA_N4_2D_250403). |
| [CDA_N4_2D_250509.zip](../file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip) | TeamBeam, 2025-05-09 | 14 files | Model projection inputs | Archive copied to [model_projection_inputs/source_files](model_projection_inputs/source_files/CDA_N4_2D_250509.zip) and extracted to [model_projection_inputs/source_files/CDA_N4_2D_250509](model_projection_inputs/source_files/CDA_N4_2D_250509). |
| [003_Nov_2025.zip](../file_transfers/collected/2025-11-07_additional_measurements/003_Nov_2025.zip) | TeamBeam, 2025-11-07 / 2025-11-14 | 10 files | Coordinates, Taupe/TDR, suction/RH, NMR context | Archive copied into the relevant measurement folders. Each workbook/image member is copied out as a standalone source file in the relevant measurement folder(s). |
| [2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip](../attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip) | Thunderbird-recovered attachment | 28 files | Model projection inputs | Archive copied to [model_projection_inputs/source_files](model_projection_inputs/source_files/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip) and extracted to [model_projection_inputs/source_files/projection_example](model_projection_inputs/source_files/projection_example). |
| [2025-09-15_saisonally.zip](../attachments/thunderbird_recovered/2025-09-15_saisonally.zip) | Thunderbird-recovered attachment | 44 files | NMR | Archive copied to [nmr/source_files](nmr/source_files/2025-09-15_saisonally.zip) and extracted to [nmr/source_files/seasonal_nmr](nmr/source_files/seasonal_nmr). |
| [2026-05-11_Presentations_CD-A_TD_260428.zip](../attachments/thunderbird_recovered/2026-05-11_Presentations_CD-A_TD_260428.zip) | Thunderbird-recovered attachment | 7 files | ERT, NMR, Taupe/TDR, suction/RH, other HM monitoring | Archive copied to [other_hm_monitoring/source_files](other_hm_monitoring/source_files/2026-05-11_Presentations_CD-A_TD_260428.zip). Each PDF member is copied to the relevant measurement folder(s). |

No inspected archive member is currently without a local catalogue reference. For the large ERT time series, the reference is intentionally the retained raw ZIP plus the archive-member CSV, not a duplicated extraction of all VTK files.

## Multi-Measurement Archive: 003_Nov_2025.zip

The November 2025 TeamBeam archive is the main source for Taupe/TDR, suction/RH, and shared coordinate material.

| Archive member | Copied measurement folders | Extracted meaning |
| --- | --- | --- |
| `001_Location_Taupe_NMR_CharacBorehole/Coordinates_NMR_Taupe_characborehole.xlsx` | [coordinates_geometry_layout](coordinates_geometry_layout/source_files/Coordinates_NMR_Taupe_characborehole.xlsx), [nmr](nmr/source_files/Coordinates_NMR_Taupe_characborehole.xlsx), [taupe_tdr](taupe_tdr/source_files/Coordinates_NMR_Taupe_characborehole.xlsx) | Coordinate bridge for NMR, Taupe, and characterization boreholes. |
| `001_Location_Taupe_NMR_CharacBorehole/NMR_Taupe_Char_brg_1.png` | [coordinates_geometry_layout](coordinates_geometry_layout/source_files/NMR_Taupe_Char_brg_1.png), [taupe_tdr](taupe_tdr/source_files/NMR_Taupe_Char_brg_1.png) | Location/borehole figure for NMR/Taupe/characterization interpretation. |
| `001_Location_Taupe_NMR_CharacBorehole/NMR_Taupe_Char_brg_2.png` | [coordinates_geometry_layout](coordinates_geometry_layout/source_files/NMR_Taupe_Char_brg_2.png), [taupe_tdr](taupe_tdr/source_files/NMR_Taupe_Char_brg_2.png) | Location/borehole figure for NMR/Taupe/characterization interpretation. |
| `001_Location_Taupe_NMR_CharacBorehole/NMR_Taupe_Char_brg_3.png` | [coordinates_geometry_layout](coordinates_geometry_layout/source_files/NMR_Taupe_Char_brg_3.png), [taupe_tdr](taupe_tdr/source_files/NMR_Taupe_Char_brg_3.png) | Location/borehole figure for NMR/Taupe/characterization interpretation. |
| `002_Taupe_Measurements/Taupe_WC.xlsx` | [taupe_tdr](taupe_tdr/source_files/Taupe_WC.xlsx) | Taupe/TDR workbook with A3, A4, A7, and A8 time series over EDZ distance bands. |
| `003_Suction_Measurements/Location_suc.png` | [suction_relative_humidity](suction_relative_humidity/source_files/Location_suc.png) | Suction/RH sensor location figure. |
| `003_Suction_Measurements/OT_RH5.xlsx` | [suction_relative_humidity](suction_relative_humidity/source_files/OT_RH5.xlsx) | Open-twin RH5 time series. |
| `003_Suction_Measurements/OT_RH6.xlsx` | [suction_relative_humidity](suction_relative_humidity/source_files/OT_RH6.xlsx) | Open-twin RH6 time series. |
| `003_Suction_Measurements/OT_RH7.xlsx` | [suction_relative_humidity](suction_relative_humidity/source_files/OT_RH7.xlsx) | Open-twin RH7 time series, with low-RH outlier periods flagged in the RH README and derived audit. |
| `003_Suction_Measurements/OT_RH8.xlsx` | [suction_relative_humidity](suction_relative_humidity/source_files/OT_RH8.xlsx) | Open-twin RH8 time series, with low-RH outlier periods flagged in the RH README and derived audit. |

## TD Presentation Archive: 2026-05-11_Presentations_CD-A_TD_260428.zip

The April/May 2026 technical-discussion package contains the most recent local presentation material in this archive set.

| Archive member | Copied measurement folders | Extracted meaning |
| --- | --- | --- |
| `2604_TD_CD-A_ISU.pdf` | [taupe_tdr](taupe_tdr/source_files/2604_TD_CD-A_ISU.pdf) | Taupe/TDR technical interpretation, including ARDP behaviour and open/closed twin contrasts. |
| `CD-A_Slides_TD_260427x.pdf` | [ert](ert/source_files/CD-A_Slides_TD_260427x.pdf), [nmr](nmr/source_files/CD-A_Slides_TD_260427x.pdf), [taupe_tdr](taupe_tdr/source_files/CD-A_Slides_TD_260427x.pdf), [suction_relative_humidity](suction_relative_humidity/source_files/CD-A_Slides_TD_260427x.pdf), [other_hm_monitoring](other_hm_monitoring/source_files/CD-A_Slides_TD_260427x.pdf) | Cross-measurement technical-discussion slides for ERT, NMR, RH/suction, Taupe, and modelling status. |
| `CD-A_Stand-ERT-2026-04.pdf` | [ert](ert/source_files/CD-A_Stand-ERT-2026-04.pdf) | ERT status presentation. |
| `CD-A_TD_2026_sc.pdf` | [other_hm_monitoring](other_hm_monitoring/source_files/CD-A_TD_2026_sc.pdf) | BGR modelling and HM comparison context. |
| `Folien_Niv_TD_CDA_2026.pdf` | [other_hm_monitoring](other_hm_monitoring/source_files/Folien_Niv_TD_CDA_2026.pdf) | Precision levelling summary and displacement context. |
| `NMR2026.pdf` | [nmr](nmr/source_files/NMR2026.pdf) | NMR 2026 presentation, including interlayer-water and seasonal comparison points. |
| `RO_2013.4_3974_CD-A3 Phase 30_A21_TN-2025-12_signed.pdf` | [suction_relative_humidity](suction_relative_humidity/source_files/RO_2013.4_3974_CD-A3%20Phase%2030_A21_TN-2025-12_signed.pdf) | Annual/report material for suction/RH instrumentation and data flow. |

## ERT Open-Niche Archive

`ERT_meas_Niche_open.zip` is the only archive that is intentionally not exploded into loose working copies because it contains a large VTK time series:

- 1,736 files total.
- 1,675 `.vtk` files.
- 61 timestep/list `.txt` files.
- Approximately 925 MB uncompressed.
- Folder naming covers 61 months from `2019-11` through `2024-12`.
- Yearly member counts: 2019 = 46, 2020 = 316, 2021 = 364, 2022 = 371, 2023 = 352, 2024 = 287.

The ERT README describes the measurement semantics and the model-facing operator status. Use [archive_member_catalog.csv](archive_member_catalog.csv) when a specific VTK or timestep file must be located inside the raw ZIP.

## NMR Seasonal Archive

`2025-09-15_saisonally.zip` was extracted because it contains a manageable set of data tables and figures:

- 22 seasonal `.dat` tables.
- 11 `.png` figures.
- 11 `.fig` figure files.
- Niche 3 and Niche 4 campaigns from 2019 through 2025.

The extracted browsing copy is [nmr/source_files/seasonal_nmr](nmr/source_files/seasonal_nmr). The NMR README records the weekly and seasonal table interpretation, time coverage, water-content ranges, and caveats from Stephan Costabel's email.

## Model And Projection Archives

Four archives are classified as model/projection inputs or report/model context rather than direct measurement streams:

- `SOTA___OGS___Mont_Terri.zip`: workspace-level OGS/report archive with `main.tex`, `long_report.tex`, `opalinus_clay.bib`, OGS settings, and `wang_kosakoeski_kolditz_thm_2009.pdf`. It is catalogued for completeness, but it does not contain additional measurement spreadsheets or presentations.
- `2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip`: projection example with `generate_projections.py`, VTU meshes, OGS XML files, `bulk_w_projections.vtu`, `comparison.pvsm`, and `specifications.pptx`.
- `CDA_N4_2D_250403.zip`: initial transferred 2D CD-A OGS setup, now extracted under [model_projection_inputs/source_files/CDA_N4_2D_250403](model_projection_inputs/source_files/CDA_N4_2D_250403).
- `CDA_N4_2D_250509.zip`: updated faster/lower-output 2D CD-A OGS setup, now extracted under [model_projection_inputs/source_files/CDA_N4_2D_250509](model_projection_inputs/source_files/CDA_N4_2D_250509).

These files are included in the measurement catalogue because they define how measurement information is placed on the OGS mesh and how simulation time should be aligned with monthly/seasonal observations.
