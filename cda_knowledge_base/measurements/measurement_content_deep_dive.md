# Measurement Content Deep Dive

Generated: 2026-06-01.

This is the top-level index for the second-pass content mining of the measurement folders. It complements `deep_source_index.md`, which is file-oriented, by adding measurement-oriented facts from the actual copied tables, archives, and extracted document text.

## Scope

- Measurement folders covered: 9.
- Mined fact rows: 101.
- Source file kinds in the underlying deep index: `bib`=1, `fig`=11, `jpg`=1, `pdf`=25, `png`=22, `pptx`=4, `pvsm`=1, `py`=1, `tex`=2, `text/data`=100, `vtu`=15, `xlsx`=12, `zip`=11.

## Per-Measurement Content Files

| Measurement | Fact rows | Content summary | Source folder |
| --- | ---: | --- | --- |
| ERT / Electrical Resistivity | 18 | [DATA_CONTENT_SUMMARY.md](ert/DATA_CONTENT_SUMMARY.md) | [source_files/](ert/source_files) |
| NMR Water Content | 9 | [DATA_CONTENT_SUMMARY.md](nmr/DATA_CONTENT_SUMMARY.md) | [source_files/](nmr/source_files) |
| Taupe / TDR | 10 | [DATA_CONTENT_SUMMARY.md](taupe_tdr/DATA_CONTENT_SUMMARY.md) | [source_files/](taupe_tdr/source_files) |
| Suction / Relative Humidity | 9 | [DATA_CONTENT_SUMMARY.md](suction_relative_humidity/DATA_CONTENT_SUMMARY.md) | [source_files/](suction_relative_humidity/source_files) |
| Permeability Pulse Tests | 21 | [DATA_CONTENT_SUMMARY.md](permeability_pulse_tests/DATA_CONTENT_SUMMARY.md) | [source_files/](permeability_pulse_tests/source_files) |
| Other HM Monitoring | 12 | [DATA_CONTENT_SUMMARY.md](other_hm_monitoring/DATA_CONTENT_SUMMARY.md) | [source_files/](other_hm_monitoring/source_files) |
| Coordinates / Geometry / Layout | 4 | [DATA_CONTENT_SUMMARY.md](coordinates_geometry_layout/DATA_CONTENT_SUMMARY.md) | [source_files/](coordinates_geometry_layout/source_files) |
| Bedding / Geology / Structure | 4 | [DATA_CONTENT_SUMMARY.md](bedding_geology_structure/DATA_CONTENT_SUMMARY.md) | [source_files/](bedding_geology_structure/source_files) |
| Model Projection Inputs | 14 | [DATA_CONTENT_SUMMARY.md](model_projection_inputs/DATA_CONTENT_SUMMARY.md) | [source_files/](model_projection_inputs/source_files) |

## Machine-Readable Files

- [measurement_content_deep_dive.csv](measurement_content_deep_dive.csv): all mined fact rows.
- [measurement_content_deep_dive_summary.json](measurement_content_deep_dive_summary.json): counts and generated-file list.
