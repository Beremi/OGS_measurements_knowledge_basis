# Local Gate Recovery Audit

This audit re-scans the collected local measurement sources for evidence that could close the failed measurement-stream activation gates.
It excludes generated request drafts and provider-response templates, so matches are evidence from source files or source indexes rather than circular restatements of the blockers.

## Summary

- Status: `local_gate_recovery_audit_generated`
- Local source/index documents scanned: 2540
- Evidence rows: 4553
- Gates audited: 7
- Gates with possible local closure evidence requiring manual review: 0
- Gates still external after local rescan: 7

## Gate Results

| Gate | Local status | Evidence rows | Possible closure evidence | Top source hints |
| --- | --- | ---: | ---: | --- |
| `ert_transform_support` | `keyword_context_found_but_gate_still_external` | 2070 | 0 | measurements/archive_member_catalog.csv (row 10); measurements/archive_member_catalog.csv (row 100); measurements/archive_member_catalog.csv (row 1000) |
| `ert_uncertainty` | `keyword_context_found_but_gate_still_external` | 1889 | 0 | measurements/archive_member_catalog.csv (row 100); measurements/archive_member_catalog.csv (row 1000); measurements/archive_member_catalog.csv (row 1001) |
| `taupe_unit_calibration` | `keyword_context_found_but_gate_still_external` | 105 | 0 | measurements/archive_member_catalog.csv (row 1872); measurements/archive_member_catalog.csv (row 1873); measurements/archive_member_catalog.csv (row 1874) |
| `rh_active_curve_provenance` | `keyword_context_found_but_gate_still_external` | 166 | 0 | measurements/archive_member_catalog.csv (row 13); measurements/archive_member_catalog.csv (row 15); measurements/archive_member_catalog.csv (row 16) |
| `hm_numeric_exports` | `keyword_context_found_but_gate_still_external` | 138 | 0 | measurements/archive_member_catalog.csv (row 1872); measurements/archive_member_catalog.csv (row 1876); measurements/archive_member_catalog.csv (row 1878) |
| `hm_uncertainty` | `keyword_context_found_but_gate_still_external` | 58 | 0 | measurements/bedding_geology_structure/derived_files/deep_source_pass/extracted_text/2025-09-05_Ziefle_et_al_2023_Characterization_083fc8f3.pdf.txt (2025-09-05_Ziefle_et_al_2023_Characterization_083fc8f3.pdf.txt); measurements/bedding_geology_structure/derived_files/deep_source_pass/extracted_text/Perm_Sec_4-3_Ziefle_et_al_2023_Characterization_47842a2a.pdf.txt (Perm_Sec_4-3_Ziefle_et_al_2023_Characterization_47842a2a.pdf.txt); measurements/bedding_geology_structure/derived_files/deep_source_pass/extracted_text/bedding_page_4_Ziefle_GETE_2022_301223fe.pdf.txt (bedding_page_4_Ziefle_GETE_2022_301223fe.pdf.txt) |
| `perm_endpoint_geometry` | `keyword_context_found_but_gate_still_external` | 127 | 0 | measurements/archive_member_catalog.csv (row 1872); measurements/archive_member_catalog.csv (row 1873); measurements/archive_member_catalog.csv (row 1874) |

## Possible Closure Evidence Rows

No row satisfied the gate-specific hard closure checks.

## Interpretation

The audit is deliberately conservative.  A row with supporting context is useful provenance, but it is not sufficient to promote a stream to a hard residual.  A closure-candidate row should be inspected against the acceptance criteria before changing the stream activation gate.

The full row-level table is `local_gate_recovery_audit.csv`; the machine-readable summary is `local_gate_recovery_audit_summary.json`.
