# CD-A Email Knowledge Base

This folder collects the CD-A modelling information found in Gmail messages from Gesa Ziefle, the BGR/ENSI collaborators named by Michal, and BGR TeamBeam file-transfer notices.

The focus is the Mont Terri CD-A experiment as used for HERMES modelling: OGS numerical models, ERT/NMR/Taupe/suction/permeability measurements, heterogeneous parameter fields, Bayesian/ML inversion, and related meetings.

## Start Here

- [Repository root README](../README.md) - fastest entry point for agents; explains
  the difference between source knowledge, measurement catalogues, processed
  observations, OGS/inversion audits, and report notes.
- [Modelling knowledge base](./modelling_knowledge_base.md) - consolidated technical notes extracted from the emails.
- [Timeline](./timeline.md) - chronological view of the collaboration and data/model exchanges.
- [Collaborators](./people/collaborators.md) - people, organizations, and inferred roles.
- [Attachment catalog](./attachments/attachment_catalog.md) - all Gmail attachments, including raw/archive files recovered from Thunderbird.
- [TeamBeam file transfers](./file_transfers/teambeam_files.md) - exact file names, sizes, hashes, expiry dates, context, and local collection status for files sent via file transfer.
- [Measurement information](./measurements/README.md) - measurement-type folders with copied source files, extracted ZIP contents, and detailed notes for ERT, NMR, permeability, Taupe/TDR, suction/RH, coordinates, geology, projection inputs, and other HM monitoring.
- [Measurement info mirror](./measurements_info/README.md) - generated navigation copy with per-measurement `MEASUREMENT_INFO.md` and `DATA_CONTENT_SUMMARY.md` files, copied `source_files/`, copied `derived_files/`, workbook sheet summaries, searchable extracts, raw provenance links, and current model-entry/gate status.
- [Measurement model-entry matrix](../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md) - joined per-measurement view of coverage, residual semantics, activation gates, final allowed use, blockers, and links back to the measurement-info notes.
- [Model formulation audit](./measurements/model_formulation_audit/README.md) - generated guardrails for the frozen OGS source model, run-local candidate fields, release gates, and measurement-inclusion status.
- [Stream activation and final-objective gates](./measurements/stream_activation_gate_audit/README.md) - activation blockers, Gmail/request tracking, final include/exclude recommendations, and the no-new-evidence closeout draft.
- [Permeability likelihood policy audit](./measurements/permeability_likelihood_policy_audit/README.md) - direct pulse-test likelihood/support decision records, next field-fit gate, and the policy acceptance template.
- [Measurement archive inventory](./measurements/archive_inventory.md) - ZIP-by-ZIP record of archive contents, copied/extracted measurement files, the full archive-member CSV index, and the source-file checksum manifest.
- [Source email index](./emails/source_email_index.md) - message-by-message index with Gmail message IDs.
- [Search scope](./source_exports/search_scope.md) - Gmail search queries and limitations.

## Fast Lookup

| Need | Use |
| --- | --- |
| Copied measurement source files | [measurements/README.md](./measurements/README.md), then the stream `source_files/` folder |
| Per-file measurement inventories and raw provenance | [measurements_info/README.md](./measurements_info/README.md), then each `MEASUREMENT_INFO.md` |
| Processed observation CSVs | [processed_observations/README.md](../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/README.md) |
| Stream activation and missing gates | [measurement_stream_activation_gate_audit.md](../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_stream_activation_gate_audit.md) and [open-question resolution matrix](./open_questions_resolution_matrix.md) |
| OGS/model input archives and projection files | [model projection inputs](./measurements/model_projection_inputs/README.md) and [GESA model originals](../SOTA_OGS_Mont_Terri_work/GESA_model_original) |
| Current report wording | [Chapter 2 measurements](../mont_terri_questions_rewrite/paper/sections/chapter_02_measurements.tex) |
| Citation/source status | [Library README](../SOTA_OGS_Mont_Terri_work/Library/README.md) and [citation locator audit](../SOTA_OGS_Mont_Terri_work/Library/citation_locator_audit.md) |
| Maintenance state | [knowledge_base_maintenance_audit.md](./knowledge_base_maintenance_audit.md) |

## Topic Notes

- [Workplan and collaboration](./threads/01-workplan-and-collaboration.md)
- [OGS models and model setup](./threads/02-model-ogs-trm-th2m.md)
- [Measurements and data](./threads/03-measurements-and-data.md)
- [Inversion and heterogeneity](./threads/04-inversion-and-heterogeneity.md)
- [Meetings and next steps](./threads/05-meetings-and-next-steps.md)
- [Open questions](./open_questions.md)
- [Open-question resolution matrix](./open_questions_resolution_matrix.md) - generated map from each remaining question to local resolution, external request, internal policy decision, or no-new-evidence closeout decision.

## Coverage

Included sources:

- Gmail messages from `Gesa.Ziefle@bgr.de`.
- Gmail messages from Tuanny Cajuhi and Stephan Costabel.
- Gmail messages mentioning Kristof Kessler, Markus Furche, Herbert Kunz, Jobst Massmann, and Bastian Graupner.
- BGR TeamBeam notices from `no-reply@teambeam.bgr.de` related to Gesa, CD-A, HERMES, or Ziefle.
- TeamBeam transfer files collected from local and remote Downloads folders, stored under `file_transfers/collected`, and verified against the SHA1 hashes from the notification emails.

Not included:

- Private mailbox material unrelated to CD-A modelling.

## Local Attachment Folder

Downloaded files are in:

`/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/attachments`

Connector-supported Gmail attachments are stored directly in the attachment folder. Raw/archive Gmail attachments recovered from Thunderbird are stored in `attachments/thunderbird_recovered`. File-transfer items are listed in the catalogs with their source message IDs.

Collected TeamBeam files are in:

`/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected`
