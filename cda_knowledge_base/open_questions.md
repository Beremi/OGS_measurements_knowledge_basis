# Open Questions

Resolution/status map: `open_questions_resolution_matrix.md` consolidates this
list with the report-comment audit, measurement gates, citation/source checks,
Gmail draft state, and final-promotion trackers.

## Data Location

- TeamBeam transfer inventory is complete locally and SHA1 verified.
- Previously unsupported Gmail raw/archive attachments were recovered from local Thunderbird on 2026-05-26.

TeamBeam files collected from local `/home/ber0061/Downloads` on 2026-05-26:

```text
ERT_meas_Niche_open.zip
CDA_N4_2D_250403.zip
apptainer_ogs6.5.4.sif
ReadMe.md
docker_ogs6.5.4.tar.gz
Dockerfile
CDA_N4_2D_250509.zip
003_Nov_2025.zip
```

TeamBeam files collected from `ber0061@10.10.10.243:/home/ber0061/Downloads` on 2026-05-26:

```text
VisualisationCDA.dat
Perm_Sec_4-3_Ziefle_et_al_2023_Characterization.pdf
Permeability_CDA_all_2025.xlsx
bedding_angle_ERT.png
bedding_page_4_Ziefle_GETE_2022.pdf
```

Gmail raw/archive attachments recovered from Thunderbird on 2026-05-26:

```text
Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip
saisonally.zip
2022-09-01_02-00_open.ohm
2022-09-01_02-00_closed.ohm
2022-09-01_02-00-00.tx0
Presentations_CD-A_TD_260428.zip
```

Known missing CD-A/HERMES attachments from the scanned Gmail/TeamBeam scope: none.

## Current Working Answers From The SOTA/OGS Report Pass

These answers reflect the current state of
`/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work` and should be treated
as modelling decisions for the first executable workflow, not as final scientific
closure.

- First inversion parameter set: permeability only. The active workflow fits or
  proposes a heterogeneous intrinsic-permeability tensor field through run-local mesh
  data. Porosity and van Genuchten retention parameters are documented as later scalar
  release options after OGS state outputs and identifiability checks exist.
- Direct permeability measurements: active log-permeability likelihood terms, not hard
  cell constraints. The current smooth 0.05 m candidate uses 75 usable interval rows
  with duplicate-aware effective weight 52.
- Bedding angle: use as a structural prior for anisotropy direction. The current
  workflow includes the approximately 144 degree bedding context as a candidate angle,
  while allowing diagnostic comparison against axis-aligned alternatives.
- Projection workflow: inspected and incorporated. The projection archive is copied
  under `SOTA_OGS_Mont_Terri_work/GESA_model_original/projection_on_mesh_2025-09-05`
  and proves that OGS can read `k_i_rd` and `n_rd` as mesh-cell fields.
- Base model status: the April/May transferred model is still treated as the
  authoritative baseline in the scanned scope. The May 2025 XML update is used for the
  current report audit, with April mesh/project files retained where required. No
  newer baseline model was found in the scanned Gmail/TeamBeam/Thunderbird scope.
- Current model-entry coverage: 9 measurement groups are represented. Only
  permeability pulse tests have active objective rows before OGS execution; NMR is
  residual-ready pending OGS state outputs; ERT needs a resistivity projection; Taupe
  needs unit/calibration confirmation; RH is a boundary-forcing/provenance audit.

## ERT Processing

- Which ERT-water-content relation should be treated as current?
- Should the open-twin relation `y = 1.44 x^-1.51` be used for first tests?
- Should model comparison use evaluated ERT on the ERT mesh, interpolated data on the FEM mesh, or projected surface/boundary values?
- What coverage/accuracy threshold should be used to filter ERT points?

## Measurement Geometry

- How should different measurement profiles be reconciled?
- Should NMR/Taupe/suction points be projected to the model boundary or represented at their actual measured offsets?
- Is the `2D_Model (x/y)` coordinate system in `Mess_Koord_XY.xlsx` sufficient for all first-stage model-data comparisons?

## Inversion Setup

- What is the first inversion parameter set: permeability only, or permeability plus porosity/storativity/retention parameters? Current working answer: permeability only first; porosity/retention later if state residuals prove permeability alone is insufficient.
- Should bedding angle be hard-coded as anisotropy direction from the start? Current working answer: use bedding as a prior/candidate direction, not an unquestioned hard constraint.
- What prior ranges should be used for permeability in EDZ and host rock?
- Should direct permeability measurements be used as hard constraints, likelihood terms, or validation only? Current working answer: active likelihood terms with large log-space errors and gas-test caveats.

## OGS Implementation

- What exactly is inside `Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip`? Current working answer: a projection workflow with `bulk.vtu`, generated projected fields, `bulk_w_projections.vtu`, and XML/project material showing mesh-field parameters.
- Does the current 2D model already read projected mesh properties, or does `parameters_TRM.xml` still need to be changed? Current working answer: the transferred April/May base XML uses constants; the projection variant and the report workflow use run-local mesh-field replacements without modifying the authoritative base model.
- Is `CDA_N4_2D_250509.zip` the best baseline model, or was a newer model shared outside the scanned emails? Current working answer: May 2025 is the best baseline in the scanned scope; newer outside-scope sharing is still possible and would need confirmation from Gesa/BGR.

## Time Dependency

- When should self-healing/time-dependent permeability be introduced?
- Which data can identify temporal permeability change rather than just spatial heterogeneity?
- Can the current data separate EDZ damage, bedding anisotropy, and time-dependent healing?
