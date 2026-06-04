# CD-A Measurement Information

This folder reorganizes the measurement information from the CD-A email and TeamBeam material by measurement type. Each subfolder contains:

- `source_files/`: copied local working copies of the files that contain data, raw measurements, figures, presentations, reports, or geometry information for that measurement type.
- `derived_files/`: generated summaries, row-level audits, or normalized extracts where a measurement type has additional mined products.
- `README.md`: extracted notes from the files themselves, with modelling relevance and links back to the copied files and original source locations.

The source copies here are for orientation and modelling work. The original collected archive remains in:

- [Gmail attachments](../attachments)
- [Thunderbird-recovered Gmail attachments](../attachments/thunderbird_recovered)
- [Collected TeamBeam transfers](../file_transfers/collected)

The ZIP/archive pass is documented separately in [archive_inventory.md](archive_inventory.md).
For row-level lookup inside every inspected archive, use
[archive_member_catalog.csv](archive_member_catalog.csv), which lists 1,880 archive
members and their copied or retained local catalogue paths.
For a generated navigation copy with per-measurement `MEASUREMENT_INFO.md` files,
copied `source_files/`, copied `derived_files/`, workbook sheet summaries,
searchable extracts, raw provenance links, and current model-entry/gate status, use
[../measurements_info](../measurements_info/README.md).
For a flat checksum inventory of the files copied or extracted into measurement
`source_files/` folders, use [source_file_manifest.csv](source_file_manifest.csv).
For the deeper pass through the files themselves, use
[deep_source_index.md](deep_source_index.md), [deep_source_index.csv](deep_source_index.csv),
and [workbook_sheet_deep_index.csv](workbook_sheet_deep_index.csv). These index
searchable text/outline extracts from PDFs, PPTX decks, Excel workbooks, raw text
files, and ZIP members under each measurement folder's `derived_files/deep_source_pass/`.
For a measurement-oriented second pass with the concrete row counts, date ranges,
numeric ranges, and ZIP/archive facts mined from those copied files, use
[measurement_content_deep_dive.md](measurement_content_deep_dive.md) and the per-folder
`DATA_CONTENT_SUMMARY.md` files. The same files are copied into
[../measurements_info](../measurements_info/README.md) for navigation.
For the latest completeness check against the collected Gmail, Thunderbird, and
TeamBeam sources, see [catalog_verification.md](catalog_verification.md).

For model-facing normalized tables generated from the workbooks and ZIP archives, see
[processed observation tables](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/README.md).
Those CSVs preserve row-level links back to the source files in this measurement
catalogue.
The report-facing traceability check is generated in
[measurement_report_traceability_audit.md](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_report_traceability_audit.md)
and copied under [stream_activation_gate_audit/derived_files](stream_activation_gate_audit/derived_files);
it currently verifies that all nine manifest observation groups are represented by
catalogue folders, report inventory references, report subsections, model-entry
wording, and workflow artifacts.
The joined model-entry matrix is generated in
[measurement_model_entry_matrix.md](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md)
and copied under [stream_activation_gate_audit/derived_files](stream_activation_gate_audit/derived_files);
it records the current active, diagnostic, boundary-audit, support/prior, and
not-ready status for the same nine measurement classes.
The same gate-audit folder now also contains
[final_objective_no_new_evidence_closeout_draft.md](stream_activation_gate_audit/derived_files/final_objective_no_new_evidence_closeout_draft.md),
which gives exact draft text for a conservative no-new-evidence final-objective
closeout without recording approval or promoting the current field.
Its companion
[final_objective_no_new_evidence_acceptance_record_template.md](stream_activation_gate_audit/derived_files/final_objective_no_new_evidence_acceptance_record_template.md)
is the signoff template for that path and currently records 0/9 approvals.

## Measurement Type Folders

- [Archive inventory](archive_inventory.md) - row-level catalogue of the inspected ZIPs, including the ERT VTK archive, seasonal NMR archive, TD presentation package, November 2025 measurement archive, and OGS/model projection archives.
- [ERT](ert/README.md) - electrical resistivity monitoring, ERT-derived water content, raw inversion examples, electrode positions, and open-niche VTK time series.
- [NMR](nmr/README.md) - nuclear magnetic resonance water-content monitoring, weekly open-niche data, seasonal NMR campaigns, positions, interpretation caveats, and the final residual-policy acceptance template.
- [Permeability Pulse Tests](permeability_pulse_tests/README.md) - pulse-test permeability data from 2021/2024/2025 sheets, method notes, and modelling domain implications.
- [Taupe / TDR](taupe_tdr/README.md) - Taupe differential TDR water-content/proxy data, coordinates, borehole figures, and interpretation from the 2026 technical discussion.
- [Suction / Relative Humidity](suction_relative_humidity/README.md) - open-twin RH sheets, suction/RH sensor location information, annual report notes, and Kelvin/retention-curve modelling links.
- [Coordinates / Geometry / Layout](coordinates_geometry_layout/README.md) - measurement coordinates, BGR model coordinates, 2D model coordinate tables, and Tecplot layout data.
- [Bedding / Geology / Structure](bedding_geology_structure/README.md) - bedding angle, bedding-parallel fault/structure context, and geological constraints relevant to anisotropy and EDZ interpretation.
- [Model Projection Inputs](model_projection_inputs/README.md) - projection scripts, OGS/VTU project material, mesh projection archive, and 2D model container archives.
- [Other HM Monitoring](other_hm_monitoring/README.md) - deformation, pore pressure, crackmeter, laser scan, levelling, and general monitoring context from CD-A reports and meeting material.
- [Stream Activation Gate Audit](stream_activation_gate_audit/README.md) - strict activation blockers plus the consolidated request package for closing support, calibration, uncertainty, provenance, and numeric-export gates.
- [Model Formulation Audit](model_formulation_audit/README.md) - frozen OGS source-model, run-local field, release-gate, and measurement-inclusion guardrails.
- [Cross-Stream Candidate Scorecard](cross_stream_candidate_scorecard/README.md) - derived run-level comparison of the active objective with NMR bias/anomaly, ERT, and Taupe/TDR diagnostics.
- [Permeability Likelihood Policy Audit](permeability_likelihood_policy_audit/README.md) - direct permeability residual conflict, support lower-bound, likelihood-policy, rerank, next field-fit gate, and policy acceptance-template outputs.

## Stream Status Map

This table is the quickest source-catalogue view of what each stream means, where
its data live, how it connects to OGS, and what still gates hard use.  For the
machine-joined current status, use
[measurement_model_entry_matrix.md](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md).

| Stream | Sources, coverage, support | Meaning and units | Processed/model-facing files | Current OGS tie, activation, and missing grounding |
| --- | --- | --- | --- | --- |
| Permeability | Source files in [permeability_pulse_tests/source_files](permeability_pulse_tests/source_files): 2021/2024/2025 workbooks and method slides. Current active support is mapped open-twin BCD-A32/A33 intervals; older BCD-A24/A25/A26/A27/BFM-D19 rows lack accepted endpoints. | Nitrogen pulse-test interpreted intrinsic permeability or transmissibility over nominal 10 cm 3D borehole intervals; fit value is `m2` in log10 space, not hydraulic conductivity, liquid relative permeability, saturation, or a tensor component. | [permeability_interpreted_values.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/permeability_interpreted_values.csv), [permeability_observation_targets.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/permeability_observation_targets.csv), and [permeability_measurement_semantics.md](permeability_pulse_tests/derived_files/permeability_measurement_semantics.md). | Active material likelihood for 75 mapped positive rows with broad log-space error and duplicate-aware weights. Missing: gas/slip correction provenance, accepted support/outlier policy, and endpoint geometry if historical rows are to enter. |
| NMR | Source files in [nmr/source_files](nmr/source_files): weekly 4S/4E `.dat` tables, seasonal NMR ZIP/extracts, NMR slides, and coordinates. Weekly coverage is 2021-10-06 to 2025-09-09; seasonal campaigns span 2019-2025 with Niche 3/4 context. | NMR-derived volumetric water content in vol.% plus confidence intervals and T2; OGS comparison uses fraction water content, but NMR-visible water may include bound/interlayer water. | [nmr_weekly.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/nmr_weekly.csv), [nmr_seasonal_profiles.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/nmr_seasonal_profiles.csv), [nmr_bound_water_sensitivity.md](nmr/derived_files/nmr_bound_water_sensitivity.md), and [nmr_final_residual_policy_gate.md](nmr/derived_files/nmr_final_residual_policy_gate.md). | Active current-report state objective with caveats. OGS samples `theta = porosity * liquid_saturation`; final residual policy is unsettled because many rows exceed fixed porosity. Missing: accepted free-water/bound-water or trend/anomaly policy and final approval. |
| ERT | Source files in [ert/source_files](ert/source_files): open-niche VTK ZIP, raw `.tx0`/`.ohm` example, electrode files, water-content/resistivity workbook, and ERT slides. Inventory covers 1691 timestep entries from 2019-11-01 to 2024-12-31; ERT support is a provisional projected mesh/support mask. | Electrical resistivity or resistivity change in ohm m; not measured saturation, water content, pressure, or permeability. Default diagnostic comparison is log10 resistivity after an empirical theta-to-rho conversion. | [ert_timesteps.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/ert_timesteps.csv), [ert_spatial_projection_operator.md](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/ert_spatial_projection_operator.md), [ert_observation_operator.md](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/ert_observation_operator.md), and [ert_measurement_semantics.md](ert/derived_files/ert_measurement_semantics.md). | Diagnostic only. OGS tie is `S_l -> theta -> rho -> ERT support -> log10 residual`. Missing: accepted coordinate transform, exact near-niche/35 cm support mask, bad-data handling, and uncertainty/correlation model. |
| Taupe/TDR | Source files in [taupe_tdr/source_files](taupe_tdr/source_files): `Taupe_WC.xlsx`, coordinates, borehole figures, TD slides, and layout. Workbook rows span 2019-12-01 to 2025-10-10 for A3/A4/A7/A8; A3/A4 map to current support and A7/A8 are outside it. | Taupe/TDR ARDP-derived water-content or dielectric proxy by EDZ distance band. Source unit is not confirmed as volumetric water content, permittivity, or another proxy. | [taupe_tdr_bands.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/taupe_tdr_bands.csv), [taupe_tdr_trend_operator.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/taupe_tdr_trend_operator.csv), and [taupe_tdr_semantics.md](taupe_tdr/derived_files/taupe_tdr_semantics.md). | Diagnostic trend stream only. OGS tie is band-averaged `theta = porosity * liquid_saturation` trend by sensor/EDZ band. Missing: unit/calibration, baseline convention, sensor-band uncertainty/covariance, and grouped weighting approval. |
| RH/suction | Source files in [suction_relative_humidity/source_files](suction_relative_humidity/source_files): OT_RH5-8 workbooks, suction location image, annual report, minutes, and TD slides. Daily copied RH coverage is 2021-12-16 to 2025-09-04; supports are boundary-audit points near the open niche. | Relative humidity in percent; converted through Kelvin equation to gauge liquid-pressure or suction candidates with stated constants and sign convention. | [rh_open_twin_kelvin.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/rh_open_twin_kelvin.csv), [rh_measurement_semantics.md](suction_relative_humidity/derived_files/rh_measurement_semantics.md), [rh_boundary_candidate_curves.md](suction_relative_humidity/derived_files/rh_boundary_candidate_curves.md), and [rh_boundary_uncertainty.md](suction_relative_humidity/derived_files/rh_boundary_uncertainty.md). | Boundary-audit only. OGS tie is candidate provenance for open-niche pressure curve `p_E(t)`, not an interior residual. Missing: active XML curve source/script, sensor screening, time origin, constants, extension policy, and accepted boundary/retention uncertainty policy. |
| Direct pressure | Source evidence is in [other_hm_monitoring/source_files](other_hm_monitoring/source_files), especially 2026 TD minutes/slides and Geoscope-context files; mini-piezometer BCD-A28-A31 trends are described, with source plots around 2024-03 to 2026-01. | Candidate pore pressure in Pa/kPa or hydraulic head, but the local catalogue lacks the machine-readable export and reference convention. | [other_hm_missing_numeric_request.md](other_hm_monitoring/derived_files/other_hm_missing_numeric_request.md) and [other_hm_numeric_source_audit.md](other_hm_monitoring/derived_files/other_hm_numeric_source_audit.md). | Blocked future residual. OGS tie would be `liquid_pressure` or head at sensor support. Missing: Geoscope time series, coordinates/support, absolute/gauge/head convention, units, quality flags, calibration, uncertainty, and 3D-to-2D mapping. |
| Faults/fractures | Source files in [bedding_geology_structure/source_files](bedding_geology_structure/source_files) and [other_hm_monitoring/source_files/VisualisationCDA.dat](other_hm_monitoring/source_files/VisualisationCDA.dat). Structural evidence includes bedding angle about 144 degrees and Tecplot `Kluft` zones; geometry is static/contextual unless dated aperture or displacement data arrive. | Structural geometry, bedding/fault orientation, scaly clay/shear-band context, and fracture/crack layout; not a pressure/saturation/permeability residual by itself. | [other_hm_visualisation_zones.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_visualisation_zones.csv) and [measurement_model_entry_matrix.md](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md). | Support/prior or scenario layer. OGS tie is possible anisotropy angle, EDZ/fault mask, permeability/porosity prior, or covariance modifier. Missing: 3D-to-2D projection policy, width/support, target field, aperture/hydraulic effect or displacement data, and uncertainty. |
| Geoscope/crackometer/other HM | Source files in [other_hm_monitoring/source_files](other_hm_monitoring/source_files): minutes, TD slides, levelling slides, HERMES input, PPTX overview, and `VisualisationCDA.dat`. Current local numeric data include 12 levelling slide-summary rows; full time-series exports are absent. | Extensometer displacement/strain, crack aperture/relative displacement, laser scan surface difference, levelling vertical displacement, miniprisma/convergence, climate/context streams. Units and sign/reference conventions are stream-specific and mostly missing locally. | [other_hm_monitoring.md](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_monitoring.md), [other_hm_levelling_displacements.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_levelling_displacements.csv), and [other_hm_numeric_source_audit.md](other_hm_monitoring/derived_files/other_hm_numeric_source_audit.md). | Not ready for hard residuals. OGS tie would be displacement, strain, pressure, crack opening, surface difference, or boundary-context filters. Missing: machine-readable values, timestamps/epochs, support geometry, units, reference zeros, sign conventions, quality flags, and uncertainty/covariance. |
| Coordinates/projection inputs | Source files in [coordinates_geometry_layout/source_files](coordinates_geometry_layout/source_files) and [model_projection_inputs/source_files](model_projection_inputs/source_files): coordinate workbooks, layout file, projection scripts, VTU meshes, OGS XML/project files, and model ZIPs. Coordinate support uses `2D_Model (x/y)` unless scope changes. | Not state measurements. They define point, line, interval, mesh, timestep, and run-local projection support. | [measurement_coordinates_xy.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/measurement_coordinates_xy.csv), [measurement_mesh_lookup.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/measurement_mesh_lookup.csv), [borehole_line_mesh_samples.csv](../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/borehole_line_mesh_samples.csv), and [model_projection_inputs/README.md](model_projection_inputs/README.md). | Support layer ready. OGS tie is measurement-to-mesh lookup and run-local mesh-field injection (`n_rd`, `k_i_rd`). Missing: historical permeability endpoint geometry if those rows enter, production verification of projected boundary subdomains, and CTE provenance confirmation for broad thermo-mechanical claims. |

## Cross-Measurement Modelling Themes

- The central modelling target is the EDZ and water-content evolution around the open and closed CD-A niches in Opalinus Clay.
- ERT, NMR, Taupe/TDR, suction/RH, and permeability are all discussed as possible constraints for HERMES modelling, but they connect to OGS variables differently.
- ERT provides spatial resistivity fields that can be linked to water content/saturation through an Archie-type relationship, but it is indirect and sensitive to geometry, inversion mesh, fractures, and filtering choices. The generated ERT semantics audit keeps it as a log-resistivity field residual after theta-to-rho conversion, not measured saturation, water content, pressure, or permeability.
- NMR gives more direct point/line water-content information and can anchor or validate ERT-derived water content, but it is sparse and has several documented campaign and instrument caveats. The generated NMR bound-water audit shows that 162 of 287 currently usable mapped NMR rows exceed fixed model porosity before correction, so raw absolute NMR water content should not be used as a naive `porosity * saturation` residual.
- Taupe/TDR is treated as saturation/water-content related, with strong open-twin seasonal behaviour and weaker closed-twin changes. The generated Taupe semantics audit keeps it as a baseline-normalized trend diagnostic: 2,544 A3/A4 rows are mapped to the current mesh support, 2,544 A7/A8 rows are outside support, and 0 rows are active absolute saturation residuals until unit/calibration evidence is available.
- Suction/RH data can help define pressure boundary conditions through Kelvin-equation conversion and saturation through retention curves, but the reliable instrument differs by RH range. The generated RH semantics audit keeps RH as boundary-condition evidence, not a mesh-cell pressure residual: 4,228 rows are valid non-low-outlier candidates, 19 RH7/RH8 low outliers are excluded, and the active OGS curve remains provenance-blocked because 772 of 845 curve rows imply RH below the clean RH5/RH6 workbook minimum.
- Permeability pulse tests provide EDZ/near-field material-parameter constraints and show large open/closed twin contrasts. The generated permeability semantics audit keeps these as gas-pulse scalar interval observations of intrinsic permeability, not hydraulic conductivity, liquid relative permeability, saturation, or direct tensor components.
- Coordinates and bedding geometry are not measurements of state variables themselves, but they are necessary for placing all point, borehole, and 2D fields into the OGS/CD-A modelling frame.

## Data Status

The files in this folder come from the already-collected Gmail, Thunderbird, local Downloads, and remote TeamBeam material. No known CD-A/HERMES email attachment from the scanned scope is still missing in the existing knowledge base. Multi-measurement ZIPs were inspected and their contents copied into the relevant measurement folders.

Archive status:

- 8 ZIP archives were inspected, including the workspace-level OGS/report ZIP.
- 1,880 archive members are indexed in [archive_member_catalog.csv](archive_member_catalog.csv).
- 206 files are listed in [source_file_manifest.csv](source_file_manifest.csv) across the measurement `source_files/` folders.
- The deep source pass scanned all 206 copied/extracted source files, summarized 34 workbook sheets, extracted searchable text from 25 PDFs and 4 PPTX files, and found no ZIP-contained office/data/image member that lacks a same-name loose source copy somewhere in the measurement catalogue.
- The content deep-dive pass generated 101 measurement-oriented fact rows and one `DATA_CONTENT_SUMMARY.md` file per measurement folder.
- The November 2025 measurement archive and the 2026 TD presentation archive were split into measurement-specific source copies.
- The seasonal NMR archive and the projection/model archives were extracted into browseable source folders.
- The ERT VTK time-series archive is retained as a raw ZIP to avoid duplicating 925 MB of loose VTK data, but every member is indexed in the archive catalog.
