# Model Formulation Audit

This folder stores generated model-facing guardrail artifacts for the recovered CD-A
OGS workflow. These files connect the measurement catalogue to the frozen source
model and staged inversion setup.

- [ogs_formulation_consistency_audit.md](derived_files/ogs_formulation_consistency_audit.md) checks the report's formulation statements against the active source XML and representative run-local XML.
- [frozen_model_measurement_inclusion_audit.md](derived_files/frozen_model_measurement_inclusion_audit.md) checks that the GESA model remains frozen, prepared runs source the recovered projection model, staged release gates pass, the current field package is positive-definite, and all measurement groups are represented while final-promotion blockers remain explicit.

Current generated status:

- OGS formulation consistency audit: 18 checks, 0 hard failures.
- Frozen-model measurement-inclusion audit: 13 checks, 0 failures, 75 run manifests checked, 65 release-gated runs, 206 measurement-info source rows, 1,880 archive-member rows, and 34 workbook-sheet summaries.
