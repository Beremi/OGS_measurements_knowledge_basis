# Model Projection Inputs

This folder collects files that are not measurements themselves, but are needed to project measurement information, define OGS model inputs, or reproduce the model-data comparison workflow discussed in the emails.

## Copied Source Files

- [2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip](source_files/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip) - Thunderbird-recovered projection-on-mesh archive.
- [projection_example/](source_files/projection_example) - extracted copy of the projection archive.
- [CDA_N4_2D_250403.zip](source_files/CDA_N4_2D_250403.zip) - TeamBeam 2D model/container archive from April 2025.
- [CDA_N4_2D_250403/](source_files/CDA_N4_2D_250403) - extracted browsing copy of the April 2025 2D model archive.
- [CDA_N4_2D_250509.zip](source_files/CDA_N4_2D_250509.zip) - TeamBeam updated 2D model archive from May 2025.
- [CDA_N4_2D_250509/](source_files/CDA_N4_2D_250509) - extracted browsing copy of the May 2025 updated model archive.
- [SOTA___OGS___Mont_Terri.zip](source_files/SOTA___OGS___Mont_Terri.zip) - workspace-level OGS/report archive, catalogued for completeness.
- [SOTA_OGS_Mont_Terri_zip/](source_files/SOTA_OGS_Mont_Terri_zip) - extracted browsing copy of that workspace-level archive.

Original locations:

- [Thunderbird-recovered projection archive](../../attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip)
- [TeamBeam April model/container transfer](../../file_transfers/collected/2025-04-04_2d_model_container)
- [TeamBeam May updated model transfer](../../file_transfers/collected/2025-05-09_updated_model)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including searchable outlines for `specifications.pptx`, OGS XML/project-file
headers, TeX/report files, and ZIP member checks.

## Projection Archive Contents

The projection archive contains 28 files and approx. 5.18 MB uncompressed. Important contents include:

- `generate_projections.py`
- `bulk.vtu`
- `bulk_all.vtu`
- `bulk_w_projections.vtu`
- `03_parameters_TRM.xml`
- `03_parameters_TRM_orig.xml`
- `cd_a_open_niche_quad.prj`
- `comparison.pvsm`
- `specifications.pptx`
- OGS XML/project input files.

The archive `README.txt` states important changes:

- `*prj`: mesh call.
- `03_param*`: function/projection specification.
- `bulk_all.vtu` domain identification needs to be re-done with `bulk.vtu`.
- Suggested command: `/home/ogs_auto_jenkins/release_versions/native/master/ogs6_v6.5.4/bin/identifySubdomains -m bulk_w_projections.vtu bulk_all.vtu`.

`generate_projections.py`:

- Imports `meshio`, `numpy`, `pandas`, and `matplotlib`.
- Reads `bulk.vtu`.
- Writes `bulk_w_projections.vtu`.
- Creates point-data/cell-data arrays.
- Works with `triangle6` elements and material IDs.

`specifications.pptx` contains timestep/projection notes:

- `ts_0000`: 18.09.2019.
- `ts_0001`: 18.09.2019 + 10 days, interpreted as end of September 2019.
- `ts_0003`: `ts_001` + 1 month, interpreted as end of October 2019.
- Later timesteps continue monthly.
- A quick convergence check is described at point ID 127.
- Time-step examples include 1 day, 10 days, and 15.2187 days.
- 365.25 days/year divided by 12 months gives 30.4375 days/month; half of that is about 2 weeks.

## Transferred OGS Model Archives

The April 2025 TeamBeam model archive `CDA_N4_2D_250403.zip` contains 22 files:

- 14 OGS XML/project-include files.
- 7 VTU mesh/boundary files.
- `cd_a_open_niche_quad.prj`.
- Seasonal open/closed niche curve XML files.

The extracted browsing copy is [source_files/CDA_N4_2D_250403](source_files/CDA_N4_2D_250403). The archive itself contains a top-level `CDA_N4_2D_250403/` directory, so the extracted files sit one level below that folder.

The May 2025 update `CDA_N4_2D_250509.zip` contains 14 XML files and no VTU meshes. It is a lighter update of the OGS configuration and curve files, consistent with the email description that Tuanny provided a faster/lower-output model setup. The extracted browsing copy is [source_files/CDA_N4_2D_250509](source_files/CDA_N4_2D_250509).

The workspace-level `SOTA___OGS___Mont_Terri.zip` contains 19 files: `main.tex`,
`long_report.tex`, `opalinus_clay.bib`, OGS settings, `cd_a_open_niche_quad.prj`,
and one THM reference PDF. It does not contain additional measurement workbooks or
presentation slides, but it is kept here because it documents the OGS/report context
around the measurement-driven modelling task.

For row-level archive provenance, see [../archive_member_catalog.csv](../archive_member_catalog.csv).

## Modelling Relevance

These files are central to connecting measurements to the OGS mesh:

- The projection script shows how point/cell data were added to the mesh.
- The XML files show where projected functions enter the OGS model.
- The VTU files provide concrete mesh/projection examples.
- The timestep notes matter for aligning monthly ERT/NMR/Taupe/RH data to simulation outputs.
- The 2D model archives preserve the model versions exchanged in April and May 2025.

Use this folder when:

- Rebuilding the OGS model from the shared archives.
- Checking how measurement fields should be projected to the simulation mesh.
- Verifying whether current mesh files include the projected domains/subdomains.
- Aligning measurement dates with OGS output timesteps.

In the current workflow this folder is a support layer for run-local field
injection, not a source of measurement residuals.  The active pattern is to keep the
transferred OGS model frozen and introduce heterogeneous candidate fields through
mesh-cell values such as `n_rd` and `k_i_rd`; source XML interpretation issues, such
as the tracked CTE provenance question, remain gated until provider confirmation or
explicit scope-out.  See
[measurement_model_entry_matrix.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md)
and
[OGS_RUN_INPUT_AUDIT.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/current_permeability_field/OGS_RUN_INPUT_AUDIT.md)
for the current model-facing status.

## Caveats

- The projection archive is an example/workflow archive, not a final processed measurement dataset.
- `bulk_all.vtu` domain identification was explicitly marked as needing to be re-done.
- The exact OGS version in the notes is `ogs6_v6.5.4`; reproducibility may depend on matching or adapting that version.
