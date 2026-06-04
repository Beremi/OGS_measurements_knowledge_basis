# Measurement Catalogue Verification

Verification date: 2026-06-01.

This note records the current completeness checks for the measurement-oriented
catalogue in this folder.

## Source Coverage Check

Original source folders checked:

- `cda_knowledge_base/attachments`
- `cda_knowledge_base/attachments/thunderbird_recovered`
- `cda_knowledge_base/file_transfers/collected`

Result:

- 41 relevant original measurement/model-support files were checked by SHA1.
- 0 relevant original files are missing from `source_file_manifest.csv`.
- 11 files were excluded from the measurement-source check because they are calendar
  invites, catalogue notes, runtime/container artifacts, or model-environment helper
  files rather than measurement evidence.
- `source_file_manifest.csv` currently contains 206 copied or extracted source-file
  rows and 138 unique file hashes.

The excluded runtime/helper files are still retained in their original collection
locations when needed, especially under `file_transfers/collected`.

## Archive Coverage Check

Every ZIP archive currently known from the Gmail, Thunderbird, TeamBeam, and local
workspace scan is represented in `archive_member_catalog.csv`.

| Archive | ZIP file rows | Catalog rows | Status |
| --- | ---: | ---: | --- |
| `SOTA___OGS___Mont_Terri.zip` | 19 | 19 | complete |
| `cda_knowledge_base/file_transfers/collected/2025-04-03_ert_open_twin/ERT_meas_Niche_open.zip` | 1736 | 1736 | complete |
| `cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip` | 22 | 22 | complete |
| `cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip` | 14 | 14 | complete |
| `cda_knowledge_base/file_transfers/collected/2025-11-07_additional_measurements/003_Nov_2025.zip` | 10 | 10 | complete |
| `cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip` | 28 | 28 | complete |
| `cda_knowledge_base/attachments/thunderbird_recovered/2025-09-15_saisonally.zip` | 44 | 44 | complete |
| `cda_knowledge_base/attachments/thunderbird_recovered/2026-05-11_Presentations_CD-A_TD_260428.zip` | 7 | 7 | complete |

Total archive-member rows: 1880.

## Local Downloads Duplicate Check

I also checked `/home/ber0061/Downloads` for obvious CD-A/HERMES measurement-transfer
leftovers after rebuilding the catalogue.

- `/home/ber0061/Downloads/003_Nov_2025 (1).zip` has the same SHA1
  `20160256c51b62ee8e9dff056624eb6b8d822604` as
  `cda_knowledge_base/file_transfers/collected/2025-11-07_additional_measurements/003_Nov_2025.zip`.
- `/home/ber0061/Downloads/ERT_meas_Niche_open (1).zip` and
  `/home/ber0061/Downloads/ERT_meas_Niche_open (2).zip` have the same SHA1
  `812a36ef75364aabed2e688cfccaebc7374ba515` as
  `cda_knowledge_base/file_transfers/collected/2025-04-03_ert_open_twin/ERT_meas_Niche_open.zip`.
- `/home/ber0061/Downloads/CDA_N4_2D_250403` contains 261 loose OGS output/input
  files. The exchanged model-input ZIP itself is already catalogued as
  `cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip`
  and copied under `model_projection_inputs`; the loose Downloads directory was
  not treated as additional measurement evidence.

## Deep Source Pass Check

The 2026-06-01 deep source pass is recorded in
[deep_source_index.md](deep_source_index.md), with machine-readable tables in
[deep_source_index.csv](deep_source_index.csv) and
[workbook_sheet_deep_index.csv](workbook_sheet_deep_index.csv).

Result:

- 206 copied/extracted measurement source files were scanned.
- 34 workbook sheets were summarized, including data worksheets and chart sheets.
- Searchable text or outline extracts were generated for PDFs, PPTX files,
  workbooks, and raw text/data files under each measurement folder's
  `derived_files/deep_source_pass/` directory.
- 11 ZIP copies in the measurement folders were checked for office/data/image
  members. No such member is missing a same-name loose source copy somewhere in
  the measurement catalogue.
- Extraction warnings: 0.
- The pass was rerun with the bundled Codex workspace Python runtime after the
  default system Python lacked `openpyxl`.

## Measurement Content Deep-Dive Check

The 2026-06-01 content deep-dive pass is recorded in
[measurement_content_deep_dive.md](measurement_content_deep_dive.md), with
machine-readable fact rows in
[measurement_content_deep_dive.csv](measurement_content_deep_dive.csv).

Result:

- 101 mined fact rows were generated across 9 measurement folders.
- Each measurement folder now has a `DATA_CONTENT_SUMMARY.md` file and a
  `derived_files/content_deep_dive/content_summary.csv` file.
- The pass mines numeric/date ranges and source facts from the copied files
  themselves, including NMR weekly and seasonal `.dat` tables, RH/Taupe/
  permeability workbooks, the ERT TeamBeam ZIP member index, model/projection
  ZIPs, and searchable PDF/PPTX extracts.
- The measurement-info mirror includes these files under
  `cda_knowledge_base/measurements_info`, so the orientation tree contains both
  the copied raw files and a per-measurement data-content note.

## Current Conclusion

The measurement catalogue has a complete local reference for every known relevant
CD-A/HERMES email attachment, Thunderbird-recovered attachment, TeamBeam transfer
file, and inspected ZIP member from the scanned source set. The only large archive
intentionally retained as a raw ZIP instead of fully extracted into loose files is
`ERT_meas_Niche_open.zip`; its 1736 member files are indexed row-by-row in
`archive_member_catalog.csv`.
