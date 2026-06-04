# Current Permeability Field Package

This is the current best executed field under the active objective. It is a
deliverable candidate field, not a final all-measurement inversion result.

- Run id: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Packaged mesh: `inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu`
- Source run directory: `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Run-local OGS input snapshot: `inversion_workflow/current_permeability_field/ogs_run_inputs`
- Packaged file manifest: `inversion_workflow/current_permeability_field/packaged_file_manifest.csv`
- Release gate: `pass` with 0 failures
- OGS execution return code: `0`
- Active objective value: 3156.353066948979
- Active components: 2
- Direct permeability rows used: 75 with weighted RMSE 1.61071549171474 log10 units
- NMR state rows used: 192 with normalized RMSE 5.483436241919646
- ERT diagnostic MAE: 0.2541796182834413 log10 units (`ert_resistivity_diagnostic_generated_transform_support_unconfirmed`)
- Taupe/TDR diagnostic MAE: 1.863211058631399 (`taupe_trend_diagnostic_generated_not_active_likelihood`)

## Field Geometry

- Mesh points: 20873
- Triangle6 cells: 10239
- Tensor field: `k_i_rd`, component order row-major [k_xx, k_xy, k_yx, k_yy]
- Positive-definite cells: 10239
- Max tensor asymmetry: 0.0
- Total triangle area: 95.63080986225386 m2

## Key Field Statistics

| Metric | p05 | p50 | p95 | max |
| --- | ---: | ---: | ---: | ---: |
| `k_eigen_min_m2` | 1.7039353236787076e-20 | 4.118296807900794e-20 | 7.906639561937955e-20 | 2.862047708646117e-14 |
| `k_eigen_max_m2` | 4.259838309196769e-20 | 1.0295742019751984e-19 | 1.9766598904844885e-19 | 7.155119271615293e-14 |
| `k_eigen_ratio` | 2.499999999999999 | 2.4999999999999996 | 2.5000000000000004 | 2.5000000000000013 |
| `log10_k_eigen_min` | -19.768546893809017 | -19.385282356749467 | -19.10200806067943 | -13.543323131083211 |
| `log10_k_eigen_max` | -19.37060688513698 | -18.98734234807743 | -18.704068052007393 | -13.145383122411173 |
| `n_rd` | 0.105 | 0.105 | 0.105 | 0.105 |

## Visual Inspection

- `visual_inspection/CURRENT_FIELD_VISUAL_INSPECTION.md`
- `visual_inspection/log10_k_geom_map.png`
- `visual_inspection/log10_k_eigen_min_map.png`
- `visual_inspection/log10_k_eigen_max_map.png`
- `visual_inspection/local_basis_increment_map.png`
- `visual_inspection/nearest_anchor_distance_map.png`
- `visual_inspection/local_basis_weight_sum_map.png`

The visual inspection maps are generated from the packaged VTU by
`inversion_workflow/scripts/build_current_field_visual_inspection.py`. They are
QA plots for the active-objective incumbent and do not promote this package to a
final all-measurement inversion result.

## Reproducible OGS Input Snapshot

The frozen source model is not edited by this package.  The folder
`ogs_run_inputs/` is a run-local snapshot of the exact project, XML includes,
bulk meshes, boundary meshes, and seasonal curve files used by the accepted
active-objective incumbent.

- Snapshot directory: `inversion_workflow/current_permeability_field/ogs_run_inputs`
- Snapshot file count: 25
- Snapshot total size: 4644736 bytes
- Project file: `ogs_run_inputs/cd_a_open_niche_quad.prj`
- Project mesh field file: `ogs_run_inputs/bulk_w_projections.vtu`
- The root-level `current_best_bulk_w_projections.vtu` is a convenience copy of that run-local field mesh.
- SHA256 manifest: `inversion_workflow/current_permeability_field/packaged_file_manifest.csv`

A rerun should be launched from `ogs_run_inputs/` with the project file
`cd_a_open_niche_quad.prj` and a fresh output directory.  The generated
`OGS_EXECUTION_STATUS.json` records the verified execution used for the current
objective scores.

## Caveats

- This package preserves the frozen OGS equations and releases only the `k_i_rd` mesh-cell tensor field.
- The active objective currently contains direct permeability pulse-test rows and conditional raw NMR state rows.
- ERT and Taupe/TDR diagnostics are packaged as screening evidence only; their support/calibration/uncertainty gates remain open.
- RH remains boundary/provenance evidence, not an active residual.
- Other-HM monitoring remains inactive until hard-residual-ready numeric exports are supplied.
- The NMR trend/anomaly mode is implemented but not promoted to the default active objective.

## Packaged Files

- `current_best_bulk_w_projections.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/bulk_w_projections.vtu`
- `RUN_MANIFEST.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/RUN_MANIFEST.json`
- `combined_objective_summary.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/combined_objective_summary.json`
- `combined_objective_components.csv` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/combined_objective_components.csv`
- `permeability_fit_summary.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/permeability_fit_summary.json`
- `permeability_fit_evaluation.csv` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/permeability_fit_evaluation.csv`
- `state_observation_evaluation_summary.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/state_observation_evaluation_summary.json`
- `state_observation_evaluation.csv` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/state_observation_evaluation.csv`
- `ogs_state_samples.csv` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/ogs_state_samples.csv`
- `ogs_output_inventory.csv` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/ogs_output_inventory.csv`
- `ert_resistivity_diagnostic_summary.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/ert_resistivity_diagnostic_summary.json`
- `taupe_tdr_trend_diagnostic_summary.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/taupe_tdr_trend_diagnostic_summary.json`
- `rh_boundary_curve_audit_summary.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/rh_boundary_curve_audit_summary.json`
- `INVERSION_RELEASE_GATE_AUDIT.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/INVERSION_RELEASE_GATE_AUDIT.json`
- `INVERSION_RELEASE_GATE_AUDIT.csv` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/INVERSION_RELEASE_GATE_AUDIT.csv`
- `INVERSION_RELEASE_GATE_AUDIT.md` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/INVERSION_RELEASE_GATE_AUDIT.md`
- `OGS_RUN_INPUT_AUDIT.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/OGS_RUN_INPUT_AUDIT.json`
- `OGS_RUN_INPUT_AUDIT.md` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/OGS_RUN_INPUT_AUDIT.md`
- `OGS_EXECUTION_STATUS.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/OGS_EXECUTION_STATUS.json`
- `ogs_state_sampling_summary.json` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/ogs_state_sampling_summary.json`

## Run-Input Snapshot Files

- `01_processes_TRM.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/01_processes_TRM.xml`
- `02_process_variables_TRM.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/02_process_variables_TRM.xml`
- `03_parameters_TRM.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/03_parameters_TRM.xml`
- `03_parameters_TRM_orig.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/03_parameters_TRM_orig.xml`
- `04_1_media_aqu_liq.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/04_1_media_aqu_liq.xml`
- `04_2_media_twophase.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/04_2_media_twophase.xml`
- `04_media_TRM.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/04_media_TRM.xml`
- `05_1_fixed_timestepping.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/05_1_fixed_timestepping.xml`
- `05_time_loop_TRM.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/05_time_loop_TRM.xml`
- `06_nonlinear_solver_T.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/06_nonlinear_solver_T.xml`
- `07_linear_solver_T.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/07_linear_solver_T.xml`
- `08_08_open_niche_seasonal.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/08_08_open_niche_seasonal.xml`
- `08_curves.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/08_curves.xml`
- `README.txt` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/README.txt`
- `bulk.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/bulk.vtu`
- `bulk_all.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/bulk_all.vtu`
- `bulk_w_projections.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/bulk_w_projections.vtu`
- `cd-a_bottom.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/cd-a_bottom.vtu`
- `cd-a_left.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/cd-a_left.vtu`
- `cd-a_niche4.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/cd-a_niche4.vtu`
- `cd-a_right.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/cd-a_right.vtu`
- `cd-a_top.vtu` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/cd-a_top.vtu`
- `cd_a_open_niche_quad.prj` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/cd_a_open_niche_quad.prj`
- `closed_niche_seasonal_curve_shifted.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/closed_niche_seasonal_curve_shifted.xml`
- `open_niche_seasonal_curve_shifted.xml` copied from `inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/open_niche_seasonal_curve_shifted.xml`
