# Knowledge Base Maintenance Audit

Generated/updated: 2026-06-04.

This audit records the documentation maintenance pass requested for the CD-A /
Mont Terri agent-facing knowledge base.  It preserves the distinction between
source files, copied catalogues, generated audits, processed observations, report
text, and cited literature.

## Checked Entry Points

- `README.md`
- `cda_knowledge_base/README.md`
- `cda_knowledge_base/modelling_knowledge_base.md`
- `cda_knowledge_base/measurements/README.md`
- `cda_knowledge_base/measurements_info/README.md`
- `cda_knowledge_base/open_questions_resolution_matrix.md`
- `SOTA_OGS_Mont_Terri_work/inversion_workflow/README.md`
- `SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md`
- `SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_stream_activation_gate_audit.md`
- `mont_terri_questions_rewrite/paper/sections/chapter_02_measurements.tex`

## What Was Updated

- Added a root `README.md` as the fast entry point for future agents.  It explains
  the role of `cda_knowledge_base/`, `cda_knowledge_base/measurements*/`,
  `SOTA_OGS_Mont_Terri_work/inversion_workflow/`, and
  `mont_terri_questions_rewrite/`, and gives fast paths for raw/source data,
  processed CSVs, OGS model inputs, open gates, citations, and report text.
- Added fast lookup tables and cross-links in the main CD-A and inversion workflow
  READMEs so agents can jump directly to source catalogues, processed observations,
  stream gates, model-entry matrices, citation audits, and Chapter 2 wording.
- Added a stream-status map to `cda_knowledge_base/measurements/README.md` covering
  permeability, NMR, ERT, Taupe/TDR, RH/suction, direct pressure,
  faults/fractures, Geoscope/crackometer/other HM, and coordinates/projection
  inputs.
- Updated support-layer READMEs for other HM, bedding/geology, coordinates, and
  model projection inputs so they align with the current Chapter 2 semantics:
  direct pressure is a blocked future residual; faults/fractures are structural
  priors/scenarios; coordinates and projection files are support layers; Geoscope,
  crackmeter, laser, levelling, and other HM streams remain non-hard-residual until
  numeric exports and metadata arrive.
- Added this maintenance audit for future refreshes.

## Current Stream Interpretation Snapshot

| Stream | Current use | Remaining gate |
| --- | --- | --- |
| Permeability pulse tests | Active material likelihood for mapped BCD-A32/A33 intervals. | Gas/slip/support policy and historical endpoint geometry if older rows enter. |
| NMR water content | Active current-report state objective with caveats. | Final residual policy for bound/interlayer water or trend/anomaly use. |
| ERT | Diagnostic log-resistivity field. | ERT-to-OGS transform, exact support mask, and uncertainty/correlation model. |
| Taupe/TDR | Diagnostic EDZ-band trend stream. | Workbook unit/calibration and grouped uncertainty/support policy. |
| RH/suction | Boundary-condition provenance/audit. | Active OGS pressure-curve provenance, screening, time axis, constants, and uncertainty policy. |
| Direct pressure | Blocked future pressure residual. | Mini-piezometer numeric exports with support, units, reference convention, flags, and uncertainty. |
| Faults/fractures | Structural prior/scenario context. | 3D-to-2D projection policy plus measured aperture/displacement/hydraulic-effect evidence for hard use. |
| Geoscope/crackometer/other HM | Qualitative validation/support context. | Numeric exports, epochs, units, reference zeros, sign conventions, quality flags, and covariance. |
| Coordinates/projection inputs | Support and run-local mesh-field injection layers. | Historical endpoint geometry, projected subdomain verification, and CTE provenance if broader THM claims are made. |

## Remaining Gaps

- The external gate request package remains unsent/missing responses according to
  the current generated audits.  ERT, Taupe/TDR, RH/suction, other HM, historical
  permeability endpoints, and CTE provenance still depend on provider responses or
  explicit exclusion/waiver decisions.
- NMR and direct permeability are active but not final all-measurement proof.  NMR
  needs a final residual-policy approval; direct permeability has support-conflict
  and likelihood-policy caveats.
- Direct pressure, crackmeter, extensometer, laser scan, and Geoscope streams are
  documented from reports/slides/layouts, but hard residuals require
  machine-readable exports and metadata.
- The checkout's `.git` directory is present but invalid/empty in this workspace,
  so Git status/diff commands may fail until repository metadata is restored.

## Recommended Refresh Commands

Run from `/home/ber0061/Repositories/gesa_mails` unless noted otherwise.

```bash
# Find navigation references and obvious gate wording.
rg -n "processed_observations|measurement_model_entry_matrix|measurement_stream_activation_gate_audit|chapter_02_measurements|open_questions_resolution_matrix|provider_responses|not_ready|diagnostic_only|boundary_audit_only|active_with_tracked_caveats" README.md cda_knowledge_base SOTA_OGS_Mont_Terri_work/inversion_workflow mont_terri_questions_rewrite/paper/sections/chapter_02_measurements.tex

# Rebuild normalized observation tables.
cd SOTA_OGS_Mont_Terri_work
python inversion_workflow/scripts/build_processed_observations.py
python inversion_workflow/scripts/build_mesh_observation_lookup.py
python inversion_workflow/scripts/build_permeability_observation_targets.py
python inversion_workflow/scripts/build_state_observation_targets.py
python inversion_workflow/scripts/build_other_hm_monitoring_inventory.py

# Rebuild stream semantics and gate/status layers after new evidence.
python inversion_workflow/scripts/build_measurement_model_entry_matrix.py
python inversion_workflow/scripts/build_measurement_stream_gate_audit.py
python inversion_workflow/scripts/build_measurement_report_traceability_audit.py
python inversion_workflow/scripts/build_objective_readiness_audit.py
python inversion_workflow/scripts/build_open_question_resolution_matrix.py

# Check documentation cleanliness.
cd /home/ber0061/Repositories/gesa_mails
git diff --check
```

If Git metadata is unavailable, run practical path/link checks with a Markdown link
checker or a local script that resolves relative file links from each edited
document, and record the failed Git command in the final maintenance note.
