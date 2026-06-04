# ERT Measurement Information

ERT here means electrical resistivity tomography / resistivity monitoring around the CD-A niches, with an emphasis on the open twin and the relationship between resistivity, water content, and saturation.

## Copied Source Files

- [ERT_meas_Niche_open.zip](source_files/ERT_meas_Niche_open.zip) - TeamBeam archive of open-niche ERT time series and VTK results.
- [2025-12-12_2022-09-01_02-00-00.tx0](source_files/2025-12-12_2022-09-01_02-00-00.tx0) - raw ERT measurement file recovered from Thunderbird.
- [2025-12-12_2022-09-01_02-00_closed.ohm](source_files/2025-12-12_2022-09-01_02-00_closed.ohm) - inversion/input data for closed niche, recovered from Thunderbird.
- [2025-12-12_2022-09-01_02-00_open.ohm](source_files/2025-12-12_2022-09-01_02-00_open.ohm) - inversion/input data for open niche, recovered from Thunderbird.
- [2025-12-12_elecs_closed.txt](source_files/2025-12-12_elecs_closed.txt) and [2025-12-12_elecs_open.txt](source_files/2025-12-12_elecs_open.txt) - electrode positions.
- [2025-04-04_WC_vs_RHO_2025-02.xlsx](source_files/2025-04-04_WC_vs_RHO_2025-02.xlsx) - water-content/resistivity relationship data.
- [2025-04-04_WC_vs_RHO_open-closed.pdf](source_files/2025-04-04_WC_vs_RHO_open-closed.pdf) - visual comparison of water-content/resistivity relation.
- [2025-02-27_CD-A_for_hermes_2D_250227x.pdf](source_files/2025-02-27_CD-A_for_hermes_2D_250227x.pdf) - February 2025 CD-A/HERMES 2D modelling slides with ERT overview.
- [2025-09-05_CD-A_for_hermes_2D_250904x.pdf](source_files/2025-09-05_CD-A_for_hermes_2D_250904x.pdf) - September 2025 CD-A/HERMES slides with ERT inverse-problem questions.
- [CD-A_Stand-ERT-2026-04.pdf](source_files/CD-A_Stand-ERT-2026-04.pdf) - 2026 ERT status slides from the TD presentation package.
- [CD-A_Slides_TD_260427x.pdf](source_files/CD-A_Slides_TD_260427x.pdf) - April 2026 technical discussion slides with cross-measurement modelling context.
- [bedding_angle_ERT.png](source_files/bedding_angle_ERT.png) - bedding-angle reference image sent with the ERT discussion.

Original locations:

- [TeamBeam ERT archive](../../file_transfers/collected/2025-04-03_ert_open_twin/ERT_meas_Niche_open.zip)
- [Gmail ERT/water-content attachments](../../attachments)
- [Thunderbird-recovered raw ERT files](../../attachments/thunderbird_recovered)
- [TeamBeam bedding image](../../file_transfers/collected/2025-12-03_cda_data/bedding_angle_ERT.png)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including searchable text for the ERT PDFs, workbook outline summaries, raw
`.tx0`/`.ohm`/electrode-file headers, and ZIP member checks.

## What Is In The Data

The `ERT_meas_Niche_open.zip` archive contains a large open-niche ERT time series:

- 1,736 files total.
- 1,675 `.vtk` files and 61 timestep/list files.
- Approx. 925 MB uncompressed.
- Time span represented by folder and file names: November 2019 through December 2024.
- The folder structure is organized as `Niche open/YYYY/MM-YYYY`.
- The extracted VTK files are unstructured-grid outputs. A sample VTK header reports `POINTS 3126 double`, with `DATASET UNSTRUCTURED_GRID`.
- Timestep list files reference daily data files such as `2019-11-01_02-00_open.data`.
- The full member list is indexed in [../archive_member_catalog.csv](../archive_member_catalog.csv). The ERT VTK archive is intentionally retained as a single raw ZIP rather than duplicated as 925 MB of loose VTK files.

The Thunderbird-recovered raw example from 2022-09-01 contains:

- `.tx0` raw measurement file: 1,055,029 bytes, 6,128 lines.
- `.ohm` open inversion/input file: 85,076 bytes, 2,656 lines.
- `.ohm` closed inversion/input file: 80,726 bytes, 2,524 lines.
- The `.tx0` header references `C:\Mont Terri\CD-A\Originaldaten\2022-09-01_02-00-00.tx0`, date `01.09.2022`, GeoTest.EXE version 2.51a, Device_LGM.DLL version 1.29, and LGM 4-Point Light 10W.
- The `.ohm` files begin with `72 # Number of electrodes` and electrode coordinate blocks.

Gesa's explanation for the raw ERT files:

- The `.tx0` file contains both niches.
- Measurements `#1` to `#2592` correspond to the open niche.
- Measurements `#2593` to `#5184` correspond to the closed niche.
- The `.ohm` files are the inversion input files.
- `elecs_open.txt` and `elecs_closed.txt` contain the electrode positions.

## Information Extracted From Slides And Emails

The February 2025 HERMES slides describe ERT as long-term monitoring of electrical resistivity. The modelling problem is framed as:

- Use ERT/NMR data in a precise 2D geometry model.
- Relate electrical resistivity to water content.
- Connect ERT-derived water content to saturation and permeability.
- Compare process variables such as pressure, deformation, and saturation with material parameters such as permeability and porosity.
- A known practical issue is that the ERT evaluation mesh is not identical to the FEM/OGS mesh.

The September 2025 slides list open questions for ERT-based inversion:

- How is the resistivity field computed from discrete resistivity measurements?
- If an OGS saturation field is available, which parameters should be fitted to reproduce the discrete measurements?
- Candidate fitted terms include permeability, pressure boundary conditions at the surface, the retention curve, and saturation/resistivity relation.
- Pressure boundary conditions may be derived from RH measurements and the Kelvin equation.
- Noise and fracture-related electric paths may not be represented in the OGS model.
- Some physical points show instability over time, so measurement cleaning or filtering may be needed.
- The ERT computational domain and OGS simulation domain differ and need an explicit handling strategy.

The April 2026 TD material confirms that ERT remains a current measurement stream for CD-A model comparison and inversion. The ERT status slides should be treated as the most recent ERT-specific presentation in this local archive.

## Model-Facing Operator Status

The SOTA/OGS workflow now has explicit ERT operator and diagnostic artifacts:

- [ert_observation_operator.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/ert_observation_operator.md) - theta-to-resistivity calibration.
- [ert_spatial_projection_operator.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/ert_spatial_projection_operator.md) - ERT-cell to OGS-cell spatial lookup.
- [ert_spatial_projection_lookup.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/ert_spatial_projection_lookup.csv) - row-level projection lookup.
- [ert_measurement_semantics.md](derived_files/ert_measurement_semantics.md) - ERT measurement semantics and activation-gate audit.
- [ert_measurement_semantics_summary.json](derived_files/ert_measurement_semantics_summary.json) - machine-readable ERT audit summary.
- [ert_measurement_semantics_timestep_audit.csv](derived_files/ert_measurement_semantics_timestep_audit.csv) - row-level timestep activation gates.
- [ert_measurement_semantics_relation_audit.csv](derived_files/ert_measurement_semantics_relation_audit.csv) - calibration relation roles.
- [ert_measurement_semantics_projection_groups.csv](derived_files/ert_measurement_semantics_projection_groups.csv) - grouped projection/support counts.
- [ert_resistivity_diagnostic.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/runs/direct_fit_observation_run/ert_resistivity_diagnostic.md) - direct-run OGS-to-ERT log-resistivity diagnostic.
- [ert_candidate_discrimination.md](derived_files/ert_candidate_discrimination.md) - cross-run ERT log-resistivity discrimination audit.
- [ert_candidate_discrimination_summary.json](derived_files/ert_candidate_discrimination_summary.json) - machine-readable cross-run ERT audit summary.
- [ert_candidate_discrimination_audit.csv](derived_files/ert_candidate_discrimination_audit.csv) - run-level cross-run ERT diagnostic table.
- [ert_candidate_discrimination_timesteps.csv](derived_files/ert_candidate_discrimination_timesteps.csv) - timestep-level cross-run ERT diagnostic table.
- [ert_support_sensitivity.md](derived_files/ert_support_sensitivity.md) - support-mask sensitivity audit over selected stream-winner runs.
- [ert_support_sensitivity_summary.json](derived_files/ert_support_sensitivity_summary.json) - machine-readable support-sensitivity summary.

Current status:

- The default calibration is `rho_ohm_m = 1.108 * theta_fraction^-1.58`, with `theta_fraction = porosity * liquid_saturation`.
- The reference ERT VTK mesh has 3,126 points and 5,966 triangular cells.
- The current spatial lookup applies the explicit provisional transform `model_x = raw_x`, `model_y = raw_y + 500` to place the ERT x/z coordinates into the local OGS x/y frame.
- 4,676 ERT cells map inside an OGS cell.
- 2,035 cells are both inside an OGS cell and inside the approximate 1.5 m central support flag.
- The direct-run diagnostic compares 162,800 cell-time rows across 80 OGS output times, with area-weighted log10 MAE 0.2541801957739222 and RMSE 0.29996586160456457.
- The cross-run candidate audit compares 66 executed OGS runs, each with 162,800 ERT cell-time rows over 80 output times.
- Across the current candidate family, ERT MAE spans 0.019635573360798686 log10 units.
- The ERT-only best run is `broad_continuous_001_001_length_0p023m_shift_1p004` with MAE 0.25407209193077057; the best active-objective run is `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000` with ERT MAE 0.2541796182834413.
- The combined-objective/ERT-MAE correlation is 0.8894403368395667, so improving the current active permeability+NMR objective generally does not improve the provisional ERT residual.
- The support-sensitivity audit checks 6 representative runs and 9 radial support variants inside the current provisional 1.5 m mask. The ERT-only broad-continuous run has the best mean support rank (1.67; worst rank 4.0), but tighter/outer subsets can swap the winner with `local_basis_sampler_003_basis_029_det_l_0p0100_s_1p000`.

This is a reproducible geometry bridge plus a run-local field-consistency diagnostic, not yet an active residual. Before assigning ERT numerical weights, the ERT-to-OGS coordinate transform, exact near-niche support mask including the "35 cm in rock" recommendation from the local slides, and ERT uncertainty/correlation model still need confirmation.

The semantics audit currently records 1,691 ERT timestep rows, 1,675 with matching
VTK files, 16 blocked by missing VTK matches, 5,966 projected ERT cells, and 2,035
cells that satisfy both current support screens.  It keeps ERT as an electrical
resistivity field residual after theta-to-rho conversion.  It is not measured
saturation, measured water content, pressure, or permeability.

## Modelling Relevance

ERT is the main spatially dense water-content/saturation-related measurement in the archive. It is valuable because it covers the near-field around the niche over many years, but it is indirect:

- ERT measures resistivity, not saturation directly.
- Conversion to water content requires an empirical or physics-informed relationship such as Archie-type fitting.
- The conversion needs calibration/validation against NMR, Taupe/TDR, RH/suction, and possibly laboratory data.
- Structural features and bedding/fault zones can create electric paths that are not naturally represented in a smooth OGS model.
- Projection between the ERT inversion mesh and OGS mesh must be made explicit.

For inversion, the useful observables are likely:

- Resistivity fields or resistivity changes relative to the initial state around October 2019.
- ERT-derived water-content/saturation fields after applying a selected resistivity-to-water-content relationship.
- Selected filtered/cleaned points or regions if full-field inversion is too noisy.

## Caveats

- The open-niche archive is large and was not fully extracted into this folder; the ZIP copy is preserved as the source archive.
- The raw `.tx0`/`.ohm` example is one timestamp only, but it is important because it documents the raw format and split between open and closed measurement indices.
- The low quality of any Archie fit or water-content conversion should be checked against NMR/Taupe/RH evidence before using it as a hard inverse-problem target.
- ERT geometry, electrode positions, and bedding/structure should be checked before any model-data comparison.
