# GESA CD-A / Mont Terri Knowledge Base

This repository is a local, provenance-preserving workspace for the Mont Terri
CD-A / HERMES modelling effort.  It combines email-derived source knowledge,
curated measurement catalogues, processed observation tables, OGS/inversion
audits, and paper/report notes.  Do not treat every file here as a model-ready
dataset: raw sources, copied catalogue files, generated audits, processed CSVs,
and report text have different authority.

## Fast Paths

| Need | Start here |
| --- | --- |
| What this repo is | [cda_knowledge_base/README.md](cda_knowledge_base/README.md) and [modelling_knowledge_base.md](cda_knowledge_base/modelling_knowledge_base.md) |
| Raw/source measurement files | [measurements/README.md](cda_knowledge_base/measurements/README.md), then each stream's `source_files/` |
| Searchable measurement inventories | [measurements_info/README.md](cda_knowledge_base/measurements_info/README.md) and per-stream `MEASUREMENT_INFO.md` |
| Processed CSV observations | [processed_observations/README.md](SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/README.md) |
| Model inputs and OGS archives | [model_projection_inputs/README.md](cda_knowledge_base/measurements/model_projection_inputs/README.md) and [GESA_model_original](SOTA_OGS_Mont_Terri_work/GESA_model_original) |
| Observation-to-model semantics | [measurement_model_entry_matrix.md](SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md) |
| Open gates and blockers | [measurement_stream_activation_gate_audit.md](SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_stream_activation_gate_audit.md) and [open_questions_resolution_matrix.md](cda_knowledge_base/open_questions_resolution_matrix.md) |
| Citations and source coverage | [Library README](SOTA_OGS_Mont_Terri_work/Library/README.md), [citation_locator_audit.md](SOTA_OGS_Mont_Terri_work/Library/citation_locator_audit.md), and [source_coverage_audit.md](SOTA_OGS_Mont_Terri_work/Library/source_coverage_audit.md) |
| Current report text | [chapter_02_measurements.tex](mont_terri_questions_rewrite/paper/sections/chapter_02_measurements.tex) |
| Knowledge-base maintenance notes | [knowledge_base_maintenance_audit.md](cda_knowledge_base/knowledge_base_maintenance_audit.md) |

## Main Areas

- `cda_knowledge_base/` is the email/source knowledge base.  It records Gmail,
  Thunderbird-recovered attachments, TeamBeam notices and collected transfer files,
  collaborator context, timeline, open questions, and source-derived technical
  notes.
- `cda_knowledge_base/measurements/` and
  `cda_knowledge_base/measurements_info/` are the measurement source catalogues.
  `measurements/` is the curated source-oriented tree.  `measurements_info/` is a
  generated navigation mirror with per-stream inventories, copied source files,
  derived files, workbook summaries, and current gate/model-entry status.
- `SOTA_OGS_Mont_Terri_work/inversion_workflow/` is the processed-observation and
  modelling-workflow layer.  It contains normalized CSVs, observation operators,
  likelihood policies, OGS run/input audits, candidate-field scorecards, activation
  gates, and final-objective decision trackers.
- `mont_terri_questions_rewrite/` is the paper/report workspace.  Chapter 2 is the
  current report-side synthesis of what each stream measures, how it ties to OGS,
  and why some streams remain active, diagnostic, gated, or blocked.

## Current Stream Status

Use
[SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md](SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md)
as the authoritative joined status layer.  The current high-level state is:

| Stream | Current use |
| --- | --- |
| Permeability pulse tests | Active material-field likelihood for mapped BCD-A32/A33 rows, with gas/slip/support caveats and historical endpoint geometry still gated. |
| NMR water content | Active state objective in the current report default, but final residual policy is unsettled; within-label trend/anomaly is the preferred provisional policy. |
| ERT | Diagnostic log-resistivity field only until coordinate transform, support mask, and uncertainty/correlation are accepted. |
| Taupe/TDR | Diagnostic trend stream only until workbook unit/calibration and grouped uncertainty are accepted; A7/A8 are outside current support. |
| RH/suction | Boundary-condition provenance/audit only; local Kelvin curves are reproducible candidates, not verified replacements for the active OGS curve. |
| Direct pressure | Future pressure residual; mini-piezometer plots exist, but machine-readable Geoscope exports, support, units, and reference convention are missing. |
| Faults/fractures | Structural prior/scenario context, not a residual without aperture/displacement/hydraulic-effect data and 3D-to-2D projection policy. |
| Geoscope/crackometer/other HM | Qualitative validation/support context only until numeric exports, timestamps, units, reference zeros, signs, and uncertainty are available. |
| Coordinates/projection inputs | Support layers for all observation operators and run-local mesh-field injection; not likelihood streams themselves. |

## Provenance Rules

- Raw files stay under the original attachment/transfer folders and copied
  catalogue `source_files/`; do not delete, rename, or overwrite them.
- Processed CSVs under `inversion_workflow/processed_observations/` are generated
  products with row-level source columns.  Check the source files before changing
  interpretation.
- Generated audits record the current workflow state.  If new provider responses
  or new files are added, rerun the documented builders before updating conclusions.
- Mark unconfirmed transforms, units, reference conventions, and final objective
  decisions as gated or uncertain.
