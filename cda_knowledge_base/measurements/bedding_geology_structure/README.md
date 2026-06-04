# Bedding / Geology / Structure Information

This folder collects bedding and geological-structure context relevant to CD-A measurement interpretation and modelling. These files are especially important for permeability anisotropy, ERT paths, and EDZ heterogeneity.

## Copied Source Files

- [bedding_angle_ERT.png](source_files/bedding_angle_ERT.png) - bedding-angle reference image sent in the December 2025 ERT/geometry discussion.
- [bedding_page_4_Ziefle_GETE_2022.pdf](source_files/bedding_page_4_Ziefle_GETE_2022.pdf) - extracted bedding/fault context from Ziefle/GETE 2022 material.
- [2025-09-05_Ziefle_et_al_2023_Characterization.pdf](source_files/2025-09-05_Ziefle_et_al_2023_Characterization.pdf) - characterization paper shared by email.
- [Perm_Sec_4-3_Ziefle_et_al_2023_Characterization.pdf](source_files/Perm_Sec_4-3_Ziefle_et_al_2023_Characterization.pdf) - characterization paper from the December TeamBeam transfer.

Original locations:

- [Gmail characterization attachment](../../attachments/2025-09-05_Ziefle_et_al_2023_Characterization.pdf)
- [TeamBeam December CD-A data folder](../../file_transfers/collected/2025-12-03_cda_data)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including searchable text from the bedding/characterization PDFs and provenance
links back to Gmail/TeamBeam sources.

## Extracted Geological Details

Gesa's December 2025 bedding-angle note states that the relevant bedding angle is approximately 144 degrees.

The `bedding_page_4_Ziefle_GETE_2022.pdf` material describes the open twin as including a major bedding-parallel structure / fault zone:

- Orientation reported as approximately `(145/59)`.
- The structure includes scaly clay and visible shear bands.
- It is located around NM 4.5 in the open twin context.
- The surrounding structural setting includes flat SW/NW-dipping faults.

The characterization paper material is important because it gives a measurement-method overview for the CD-A experiment. It lists or discusses:

- ERT for water-content evolution.
- NMR/CCM for water-content information.
- Taupe/TDR for water-content-related information, with limitations.
- Permeability pulse tests and fault-zone information.
- Suction and pore-pressure monitoring.
- Deformation and other HM monitoring.
- Numerical modelling as part of the comparative interpretation.

## Modelling Relevance

Bedding and structure matter in several ways:

- Permeability anisotropy should follow bedding orientation.
- Fault zones and bedding-parallel structures can create local hydraulic or electrical pathways.
- ERT inversion anomalies may reflect structural features, not only smooth saturation changes.
- Permeability pulse-test data near structural features should not be interpreted as homogeneous EDZ behaviour without checking position.
- The open/closed twin contrast may be partly controlled by geological structure, boundary conditions, and EDZ evolution together.

For the first modelling iteration, Gesa advised starting with a simpler permeability setup without time dependency, but bedding should remain part of the interpretation of anisotropy and subdomain design.

In the current OGS workflow this folder is a support/prior layer, not an active
measurement residual.  Faults and fracture geometry can define anisotropy context,
EDZ/fault masks, local permeability-basis supports, or scenario fields.  They become
hard quantitative inputs only after the 3D feature, projection into the current 2D
slice, effective width/support, target field, uncertainty, and independent aperture,
displacement, or hydraulic-effect evidence are explicit.  See the report-side
fault/fracture semantics in
[chapter_02_measurements.tex](../../../mont_terri_questions_rewrite/paper/sections/chapter_02_measurements.tex)
and the current allowed-use row in
[measurement_model_entry_matrix.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md).

## Caveats

- The bedding angle is a geometric/structural constraint, not a directly measured saturation/permeability value.
- The `(145/59)` structure and the approximately 144 degree bedding angle should be checked against the exact coordinate convention used in the model before applying as a tensor orientation.
- Structure can explain local deviations in ERT/permeability/NMR/Taupe data; it should not be ignored when selecting calibration points.
