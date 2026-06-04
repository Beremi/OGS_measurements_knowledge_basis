# Processed Observation Tables

This folder contains normalized CSV tables built from the collected CD-A measurement
sources.  The tables are derived products: keep the raw files in
`../../../cda_knowledge_base/measurements/` as the authority, and use the
`source_file`, `source_sheet`, and `source_member` columns here to trace every row
back to its original source.

## Generated Tables

| File | Rows | Columns |
| --- | ---: | ---: |
| `borehole_coordinates.csv` | 35 | 11 |
| `ert_archive_inventory.csv` | 61 | 12 |
| `ert_kruschwitz2004_relation.csv` | 24 | 9 |
| `ert_nmr_resistivity_pairs.csv` | 72 | 9 |
| `ert_timesteps.csv` | 1691 | 8 |
| `ert_vtk_sample_metadata.csv` | 61 | 7 |
| `manifest_summary.csv` | 9 | 8 |
| `measurement_coordinates_xy.csv` | 107 | 13 |
| `nmr_seasonal_profiles.csv` | 294 | 7 |
| `nmr_seasonal_zip_inventory.csv` | 44 | 4 |
| `nmr_weekly.csv` | 170 | 9 |
| `permeability_interpreted_values.csv` | 204 | 14 |
| `permeability_pressure_decay.csv` | 6687 | 7 |
| `permeability_workbook_inventory.csv` | 7 | 10 |
| `rh_open_twin_kelvin.csv` | 4247 | 13 |
| `rh_measurement_semantics_row_audit.csv` | 4247 | 34 |
| `rh_measurement_semantics_sensor_summary.csv` | 4 | 19 |
| `rh_boundary_curve_semantics.csv` | 845 | 10 |
| `rh_boundary_provenance_request.csv` | 6 | 10 |
| `rh_boundary_provenance_evidence.csv` | 10 | 7 |
| `taupe_tdr_bands.csv` | 5088 | 10 |
| `taupe_tdr_trend_operator.csv` | 5088 | 41 |
| `taupe_tdr_series_summary.csv` | 24 | 17 |
| `taupe_tdr_semantics_row_audit.csv` | 5088 | 43 |
| `taupe_tdr_semantics_series_audit.csv` | 24 | 39 |
| `taupe_tdr_semantics_group_summary.csv` | 44 | 23 |

## Measurement-Specific Notes

- `nmr_weekly.csv` combines the weekly 4S and 4E NMR monitoring files.  It parses the
  German month names into ISO-like timestamps and flags the February-April 2025 4E
  detuning caveat from the email discussion.
- `nmr_seasonal_profiles.csv` mines the seasonal NMR ZIP directly, without requiring
  a separate extracted folder.  Each row is a campaign-date/position water-content
  value from one `.dat` member in the ZIP.
- `ert_archive_inventory.csv` and `ert_timesteps.csv` mine the open-niche ERT ZIP
  structure.  They do not unpack all VTK files; they map monthly folders, timestep
  lists, timestamps, and matching VTK members for later targeted extraction.
- `ert_nmr_resistivity_pairs.csv` and `ert_kruschwitz2004_relation.csv` normalize the
  water-content/resistivity workbook used for the Archie-type local conversion.
- `permeability_interpreted_values.csv` extracts the interpreted permeability and
  transmissibility interval tables from both permeability workbooks.  It preserves
  zeros and missing values as found; use `positive_permeability` and
  `log10_permeability_m2` for fitting.
- `permeability_pressure_decay.csv` converts the raw pressure-decay sheets
  `Messdaten_BCDA26` and `Messdaten_BCDA27` into a long table of time and normalized
  interval pressure.  No additional test interpretation is applied.
- `rh_open_twin_kelvin.csv` converts RH to Kelvin-equation liquid pressure using
  rho_l = 1095 kg/m3, T = 298.15 K, and
  M_w = 0.0180153 kg/mol.  The pressure column
  `liquid_pressure_gauge_pa_kelvin` is relative to gas pressure; the absolute column
  adds 101325 Pa as a documented convention.  Use
  `../scripts/audit_rh_boundary_curve.py` to compare this table with the active OGS
  open-niche pressure curve in a prepared run directory.
- `rh_measurement_semantics_row_audit.csv`, `rh_measurement_semantics_sensor_summary.csv`,
  and `rh_boundary_curve_semantics.csv` keep the RH measurement meaning separate from
  the active OGS curve provenance.  The audit records 4,228 valid non-low-outlier RH
  rows, 19 low-RH outliers, 2,492 open-twin rows above the 95 percent
  thermo-hygrometer caution threshold, and 772 of 845 active-curve rows with implied
  RH below the clean RH5/RH6 workbook minimum.
- `rh_boundary_provenance_request.csv`, `rh_boundary_provenance_evidence.csv`,
  `rh_boundary_provenance_request_summary.json`, and
  `rh_boundary_provenance_request.md` turn that mismatch into six concrete BGR/Gesa
  requests: active curve generation, time-axis extension, sensor screening, Kelvin
  conversion constants, open/closed curve mapping, and the retention-parameter
  release gate.  The package records ten evidence rows and is copied to the
  suction/RH catalogue `derived_files/` folder.
- `taupe_tdr_bands.csv` reshapes the Taupe workbook into one row per
  sensor/date/EDZ-band value.  The physical unit/conversion is still flagged as
  unresolved because the workbook itself does not document it; use the separate
  Taupe observation-operator builder for baseline-normalized trend diagnostics and
  candidate absolute conversions.
- `measurement_coordinates_xy.csv` and `borehole_coordinates.csv` preserve the
  coordinate-workbook rows used for model lookup.
- Secondary HM monitoring sources are intentionally parsed by the separate
  `../scripts/build_other_hm_monitoring_inventory.py` companion script because it
  streams a large Tecplot layout file and writes qualitative validation gates rather
  than the main water-content/permeability observation tables.

## Intended Use

These CSVs are the first model-facing layer for observation operators.  They are not
yet an inversion driver and they do not execute OGS.  The next step is to connect
these rows to mesh lookup/sampling code and to define likelihood/error models for
each measurement stream.

## Mesh Lookup Layer

After rebuilding the processed tables, run
`../scripts/build_mesh_observation_lookup.py` from `SOTA_OGS_Mont_Terri_work` to map
coordinate rows and borehole intervals onto the OGS bulk mesh.  That second script
currently writes:

| File | Purpose |
| --- | --- |
| `measurement_mesh_lookup.csv` | Point lookup for rows in `measurement_coordinates_xy.csv`. |
| `borehole_mesh_lookup.csv` | Point lookup for labelled NMR, characterization-borehole, and Taupe endpoints. |
| `borehole_line_mesh_samples.csv` | Line samples for borehole/Taupe segments, for interval-style observation operators. |
| `ogs_bulk_mesh_cells.csv` | Cell centroids and material IDs for the bulk mesh. |
| `mesh_lookup_summary.json` | Mesh bounds, transform convention, and lookup status counts. |

The mesh domain is local.  Rows outside the mesh bounding box are intentionally
retained and flagged as `outside_mesh_bbox_nearest_cell`; rows inside the bounding
box but not inside a triangle are flagged as `inside_mesh_bbox_nearest_cell`.

## Permeability Observation Target Layer

After the mesh lookup exists, run
`../scripts/build_permeability_observation_targets.py` from
`SOTA_OGS_Mont_Terri_work`.  It writes:

| File | Purpose |
| --- | --- |
| `permeability_observation_targets.csv` | One row per interpreted permeability workbook row, with fit usability status. |
| `permeability_observation_cells.csv` | Cell weights for mapped interval targets. |
| `permeability_segment_geometry.csv` | Segment lengths, tangents, and in/out-of-mesh sample counts. |
| `permeability_missing_geometry_audit.csv` | Grouped audit of interpreted rows with source-backed orientation but missing endpoint geometry. |
| `permeability_missing_geometry_audit.md` | Human-readable missing-geometry audit and activation requirements. |
| `permeability_endpoint_geometry_request.csv` | Five-row external request table for the missing BCD-A24/25/26/27 and BFM-D19 endpoint geometry. |
| `permeability_endpoint_geometry_blocked_rows.csv` | The 98 interpreted rows blocked by that endpoint geometry gap, with requested endpoint labels. |
| `permeability_endpoint_geometry_request_summary.json` | Machine-readable counts, evidence notes, and catalogue-copy paths for the endpoint request package. |
| `permeability_endpoint_geometry_request.md` | Human-readable/email-ready endpoint geometry request. |
| `permeability_measurement_semantics_audit.csv` | Row-level semantics and activation-gate audit for every interpreted permeability target. |
| `permeability_measurement_semantics_group_summary.csv` | Target-status, campaign/orientation, segment, and source-sheet summaries. |
| `permeability_measurement_semantics_summary.json` | Machine-readable counts, ranges, and activation rules. |
| `permeability_measurement_semantics.md` | Human-readable gas-pulse/scalar-to-tensor semantics audit. |
| `permeability_target_summary.json` | Status counts and assumptions. |

The scalar gas pulse-test value is not treated as a tensor component.  The target
rows describe a noisy interval-scale constraint on intrinsic permeability; a later
likelihood should compare it to an interval average of the model tensor field using
an explicitly chosen sensitivity approximation.  Older BCD-A24/25/26/27 and BFM-D19
rows retain direction/orientation evidence from the characterization paper, but stay
outside the active objective until labelled endpoints or an explicitly approved
digitized trace exists.

Run `../scripts/build_permeability_endpoint_geometry_request.py` after the target
builder to regenerate the follow-up package for those inactive historical rows.  It
writes a five-segment request table for BCD-A24, BCD-A25, BCD-A26, BCD-A27, and
BFM-D19, a 98-row blocked-observation table, a JSON summary, and a Markdown note
with email-ready wording.  The package documents that the collected workbooks and
characterization paper prove measurement values and orientation, but not labelled
start/end coordinates, so the rows remain inactive.

Run `../scripts/build_permeability_semantics_audit.py` after the target builder to
regenerate the semantic audit.  The current audit records 204 interpreted rows, 200
positive rows, 75 active direct candidates, 27 rows outside the current mesh, and 98
rows blocked by missing endpoint geometry.  It also makes the modelling rule explicit:
the nitrogen pulse-test result is a noisy scalar interval observation of intrinsic
permeability, not hydraulic conductivity, liquid relative permeability, saturation, or
a direct cell-wise tensor component.

## State Observation Target Layer

After the mesh lookup exists, run
`../scripts/build_state_observation_targets.py` from `SOTA_OGS_Mont_Terri_work`.  It
writes:

| File | Purpose |
| --- | --- |
| `state_observation_targets.csv` | NMR, RH, Taupe/TDR, and ERT target rows with operator semantics and usability flags. |
| `state_observation_samples.csv` | Mapping from state target rows to OGS lookup cells or line-sample cells where applicable. |
| `state_observation_target_summary.json` | Target counts by measurement family, status, and sample layer. |

This layer keeps different measurement semantics separate: NMR compares to model
`porosity * saturation` with the bound/interlayer-water caveat, RH is boundary
forcing through Kelvin pressure, Taupe/TDR is a trend diagnostic until absolute
calibration is documented, and ERT remains an external field-projection target even
though first-pass Taupe trend, ERT theta-to-resistivity calibration, and ERT spatial
lookup artifacts are now explicit.

## Other HM Monitoring Inventory

After the collected TD minutes, levelling slides, modelling slides and Tecplot layout
exist, run `../scripts/build_other_hm_monitoring_inventory.py` from
`SOTA_OGS_Mont_Terri_work`.  It writes:

| File | Purpose |
| --- | --- |
| `other_hm_visualisation_zones.csv` | Tecplot zones from `VisualisationCDA.dat`, classified by monitoring/support role with coordinate bounds. |
| `other_hm_visualisation_text_labels.csv` | Legend/display labels from the Tecplot layout. |
| `other_hm_levelling_displacements.csv` | Pointwise vertical displacement values from the 2026 precision-levelling slides. |
| `other_hm_qualitative_targets.csv` | Structured validation statements from the 2026 minutes, BGR modelling slides and HERMES input note. |
| `other_hm_monitoring_summary.json` | Status, counts and remaining raw-export blocker. |
| `other_hm_monitoring.md` | Human-readable inventory and missing-export list. |
| `other_hm_missing_numeric_request.csv` | Six-row request table for the missing numeric Geoscope, laser-scan and full levelling exports. |
| `other_hm_missing_numeric_evidence.csv` | Source statements that justify the missing-export requests. |
| `other_hm_missing_numeric_request_summary.json` | Machine-readable request counts, activation status and catalogue-copy paths. |
| `other_hm_missing_numeric_request.md` | Human-readable/email-ready request for numeric other-HM monitoring exports. |

These artifacts make mini-piezometer, extensometer, crackmeter, laser-scan and
levelling evidence visible to the workflow, but they do not make the stream an active
objective term.  Hard pressure/deformation residuals still need the underlying
Geoscope time-series exports and laser-scan statistical files.

Run `../scripts/build_other_hm_missing_numeric_request.py` after the inventory to
regenerate the missing-export request package.  It lists the Geoscope
mini-piezometer, extensometer, crackmeter, boundary/context, laser-scan statistical
interpretation, and full levelling survey exports needed before hard pressure or
deformation residuals can be assigned.

## Taupe/TDR Observation Operator

After the processed tables and mesh lookup exist, run
`../scripts/build_taupe_observation_operator.py` from `SOTA_OGS_Mont_Terri_work`.
It writes:

| File | Purpose |
| --- | --- |
| `taupe_tdr_trend_operator.csv` | Baseline-normalized Taupe anomalies, mapped EDZ-band porosity diagnostics, and candidate absolute conversions. |
| `taupe_tdr_series_summary.csv` | One row per sensor/EDZ-band series with baseline, scale, and net change. |
| `taupe_tdr_observation_operator_summary.json` | Operator status, mapped row counts, physical-range sanity checks, and remaining blocker. |
| `taupe_tdr_observation_operator.md` | Human-readable operator description. |
| `taupe_tdr_semantics_row_audit.csv` | Row-level measured-quantity, model-quantity, residual, and activation-gate interpretation. |
| `taupe_tdr_semantics_series_audit.csv` | Series-level support, calibration, and physical-range counts for each sensor/EDZ band. |
| `taupe_tdr_semantics_group_summary.csv` | Counts by sensor, EDZ band, mapping status, and activation gate. |
| `taupe_tdr_semantics_summary.json` | Machine-readable semantics summary used by the likelihood documentation. |
| `taupe_tdr_semantics.md` | Human-readable Taupe/TDR measurement semantics audit. |

The current recommended Taupe role is a trend diagnostic against band-averaged
`theta_model = porosity * liquid_saturation`.  Absolute saturation residuals remain
blocked until the Taupe workbook unit or sensor-specific dielectric/water-content
calibration is confirmed.  Run the builder with a Python environment that has
`meshio`, because it reads the OGS `n_rd` porosity field from the VTU mesh.
The semantics audit records 2,544 A3/A4 trend-diagnostic rows, 2,544 A7/A8 rows
outside the current local OGS mesh support, and 0 Taupe/TDR rows active as absolute
state residuals in the current candidate objective.

## ERT Observation Operator

After the processed tables exist, run
`../scripts/build_ert_observation_operator.py` from `SOTA_OGS_Mont_Terri_work`.  It
writes:

| File | Purpose |
| --- | --- |
| `ert_water_content_resistivity_operator.csv` | Power-law theta-to-resistivity fits from paired NMR/resistivity and workbook relation columns. |
| `ert_observation_operator_summary.json` | Recommended first-test relation, ERT timestep coverage, and remaining blocker. |
| `ert_observation_operator.md` | Human-readable operator description. |
| `ert_measurement_semantics_timestep_audit.csv` | Row-level timestep activation gates and residual semantics. |
| `ert_measurement_semantics_relation_audit.csv` | Calibration-relation roles, recommended relation, and diagnostic alternatives. |
| `ert_measurement_semantics_projection_groups.csv` | Grouped projection/support counts for ERT cells. |
| `ert_measurement_semantics_summary.json` | Machine-readable ERT semantics and activation summary. |
| `ert_measurement_semantics.md` | Human-readable ERT measurement-semantics audit. |

The current default first-test relation is `kruschwitz_model_data2019`:
`rho_ohm_m = 1.108 * theta_fraction ** -1.58`, where
`theta_fraction = porosity * liquid_saturation`.
Run `../scripts/build_ert_semantics_audit.py` after the ERT calibration and spatial
lookup builders to refresh the ERT activation audit.  The current audit records 1,691
timestep rows, 1,675 matching VTK members, 16 missing VTK matches, 5,966 projected ERT
cells, and 2,035 cells that satisfy both the OGS-cell and approximate central-support
screens.  It keeps ERT as a log-resistivity field residual, not measured saturation,
water content, pressure, or permeability.

## ERT Spatial Projection Operator

After the ERT calibration exists, run
`../scripts/build_ert_spatial_projection_lookup.py` from
`SOTA_OGS_Mont_Terri_work`.  Use a Python environment with `meshio`, because the
script reads a reference ERT VTK from the ZIP archive.  It writes:

| File | Purpose |
| --- | --- |
| `ert_spatial_projection_lookup.csv` | ERT-cell centroid lookup to OGS cells, with transformed coordinates, sample ERT resistivity, and support flags. |
| `ert_spatial_projection_summary.json` | Transform assumption, lookup counts, ERT timestep coverage, and remaining blocker. |
| `ert_spatial_projection_operator.md` | Human-readable spatial operator description. |

The current lookup uses `model_x = raw_x` and `model_y = raw_y + 500` to place the
ERT x/z mesh in the local OGS x/y frame.  It maps 5,966 ERT cells, with 4,676 inside
an OGS cell and 2,035 also inside the approximate 1.5 m central support mask.  ERT
residuals still need OGS output sampling, transform confirmation, and the exact
near-niche support mask before they should carry numerical weights.

## State Observation Evaluation

After OGS output files are sampled with
`../scripts/sample_ogs_state_outputs.py`, run
`../scripts/evaluate_state_observation_targets.py`.  It writes
`state_observation_evaluation.csv` and `state_observation_evaluation_summary.json`
inside the selected run directory.  NMR rows can become numerical residuals against
model `porosity * saturation`; RH remains boundary forcing, Taupe/TDR has a
baseline-normalized trend diagnostic but remains pending absolute calibration, and
ERT has calibration and spatial lookup artifacts but remains pending OGS outputs and
support confirmation.

## Permeability Target Evaluation

After preparing a run directory with a generated `k_i_rd` field, run
`../scripts/evaluate_permeability_targets.py`.  It writes
`permeability_fit_evaluation.csv` and `permeability_fit_summary.json` into the run
directory.  The evaluator computes directional `e^T K e` predictions for the direct
pulse-test targets and reports duplicate-aware log-space residuals.

Use `../scripts/assemble_inversion_objective.py` after the direct permeability and
state evaluations exist.  It writes a component table and strict JSON summary of the
currently active objective terms.

Use `../scripts/build_measurement_operator_coverage.py` after the candidate
evaluation is refreshed to write `../measurement_operator_coverage.csv`,
`../measurement_operator_coverage_summary.json`, and
`../measurement_operator_coverage.md`.  That audit gives one row per measurement
stream and records whether the stream is an active objective term, a state residual
waiting for OGS outputs, boundary-forcing evidence, diagnostic support, or workflow
support data.

For a full per-candidate pass, use `../scripts/evaluate_inversion_candidate.py`.
It runs the preparation, direct permeability evaluation, optional OGS execution,
state-output sampling, RH boundary audit, state-target evaluation, and combined
objective assembly for one candidate run directory.

Use `../scripts/run_direct_permeability_prior_sweep.py` to rank generated
heterogeneous anisotropic prior/proposal fields by the direct pulse-test objective
before spending OGS runtime on a candidate.

Use `../scripts/fit_smooth_permeability_field_from_targets.py` to build smooth
interval-anchored candidate fields from the direct pulse-test multipliers.  The
script writes length-scale-ranked fields that preserve tensor orientation/anisotropy
while spreading local permeability corrections over nearby cells.
