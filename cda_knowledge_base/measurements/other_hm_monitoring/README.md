# Other HM Monitoring Information

This folder collects CD-A hydromechanical monitoring context that is not one of the main extracted measurement folders above, but still matters for model validation and interpretation. This includes deformation, pore pressure, crackmeters, laser scans, levelling, and general project measurement overview material.

## Copied Source Files

- [2026-05-11_TD517_CD-A_260507__Minutes.pdf](source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf) - May 2026 CD-A TD minutes.
- [2026-05-11_Presentations_CD-A_TD_260428.zip](source_files/2026-05-11_Presentations_CD-A_TD_260428.zip) - original TD presentation archive recovered from Thunderbird.
- [CD-A_TD_2026_sc.pdf](source_files/CD-A_TD_2026_sc.pdf) - BGR modelling / TD presentation.
- [Folien_Niv_TD_CDA_2026.pdf](source_files/Folien_Niv_TD_CDA_2026.pdf) - levelling presentation from the TD package.
- [CD-A_Slides_TD_260427x.pdf](source_files/CD-A_Slides_TD_260427x.pdf) - April 2026 TD slides.
- [2024-12-19_Input_HERMES_BGR_20241217.pdf](source_files/2024-12-19_Input_HERMES_BGR_20241217.pdf) - HERMES input document describing available CD-A measurements and modelling concept.
- [2025-09-05_CD-A_for_hermes_2D_Bologna_250904.pptx](source_files/2025-09-05_CD-A_for_hermes_2D_Bologna_250904.pptx), [2025-09-05_Hermes_T5_BGR_UGN_250904.pptx](source_files/2025-09-05_Hermes_T5_BGR_UGN_250904.pptx), [2025-09-05_Hermes_T5_BGR_UGN_250905x.pptx](source_files/2025-09-05_Hermes_T5_BGR_UGN_250905x.pptx) - short HERMES overview slides referencing the CD-A measurement-driven modelling concept.
- [VisualisationCDA.dat](source_files/VisualisationCDA.dat) - Tecplot layout file with labels for many HM monitoring objects.

Original locations:

- [Gmail attachments](../../attachments)
- [Thunderbird-recovered TD presentation package](../../attachments/thunderbird_recovered/2026-05-11_Presentations_CD-A_TD_260428.zip)
- [TeamBeam December CD-A data folder](../../file_transfers/collected/2025-12-03_cda_data)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including searchable text from the HM PDFs, PPTX outline extracts, Tecplot file
headers, and ZIP member checks.

The `2026-05-11_Presentations_CD-A_TD_260428.zip` archive was inspected and its
measurement-specific members are classified elsewhere in the measurement catalogue:

- `2604_TD_CD-A_ISU.pdf` -> [Taupe/TDR](../taupe_tdr/source_files/2604_TD_CD-A_ISU.pdf)
- `CD-A_Stand-ERT-2026-04.pdf` -> [ERT](../ert/source_files/CD-A_Stand-ERT-2026-04.pdf)
- `NMR2026.pdf` -> [NMR](../nmr/source_files/NMR2026.pdf)
- `RO_2013.4_3974_CD-A3 Phase 30_A21_TN-2025-12_signed.pdf` -> [Suction/RH](../suction_relative_humidity/source_files/RO_2013.4_3974_CD-A3%20Phase%2030_A21_TN-2025-12_signed.pdf)
- `Folien_Niv_TD_CDA_2026.pdf` -> this folder, as levelling/other-HM evidence.
- `CD-A_TD_2026_sc.pdf` -> this folder, as BGR modelling/other-HM evidence.
- `CD-A_Slides_TD_260427x.pdf` -> copied into the relevant water-content and HM
  folders as general TD context.

## Derived Structured Artifacts

The report working folder now contains a structured inventory of this secondary HM
material:

- [other_hm_monitoring.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_monitoring.md) - human-readable derived inventory.
- [other_hm_visualisation_zones.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_visualisation_zones.csv) - 84 Tecplot zones from `VisualisationCDA.dat`, classified by monitoring/support role with coordinate bounds.
- [other_hm_visualisation_text_labels.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_visualisation_text_labels.csv) - 11 legend/display labels from the Tecplot layout.
- [other_hm_levelling_displacements.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_levelling_displacements.csv) - 12 pointwise vertical displacement values from the precision-levelling slides.
- [other_hm_qualitative_targets.csv](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_qualitative_targets.csv) - 10 structured validation statements from the 2026 minutes, BGR modelling slides, and HERMES input note.
- [other_hm_monitoring_summary.json](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/other_hm_monitoring_summary.json) - machine-readable status and counts.
- [other_hm_missing_numeric_request.md](derived_files/other_hm_missing_numeric_request.md) - email-ready request for the missing numeric Geoscope, laser-scan, and full levelling exports.
- [other_hm_missing_numeric_request.csv](derived_files/other_hm_missing_numeric_request.csv) - six-row request table for the missing numeric streams.
- [other_hm_missing_numeric_evidence.csv](derived_files/other_hm_missing_numeric_evidence.csv) - source statements that justify those requests.
- [other_hm_missing_numeric_request_summary.json](derived_files/other_hm_missing_numeric_request_summary.json) - machine-readable summary and copy paths for the request package.
- [other_hm_numeric_source_audit.md](derived_files/other_hm_numeric_source_audit.md) - source-level audit proving which other-HM exports are locally present or missing.
- [other_hm_numeric_source_audit.csv](derived_files/other_hm_numeric_source_audit.csv) - six request classes checked against source files, ZIP members, text evidence, support geometry, and levelling rows.
- [other_hm_numeric_source_evidence.csv](derived_files/other_hm_numeric_source_evidence.csv) - retained text evidence hits for the request classes.
- [other_hm_numeric_source_audit_summary.json](derived_files/other_hm_numeric_source_audit_summary.json) - machine-readable source-scan summary.

## Measurement Streams Mentioned

The 2024 HERMES input document says BGR has access to long-term CD-A measurements including:

- Deformation.
- Humidity.
- Water content.
- Pore water pressures.
- Crack width.
- Pointwise measurements such as piezometers and extensometers.
- Two-dimensional measurements such as ERT, TDR, and laser scans.

The May 2026 TD minutes mention Geoscope updates including:

- RH.
- Temperature.
- Opening times.
- Extensometer.
- Mini-piezometer.
- Crackmeter.
- Suction.
- Laser scans.

The Tecplot `VisualisationCDA.dat` layout includes labels for:

- Minipiezometers.
- Extensometers.
- Taupe.
- Miniprismas.
- Permeability.
- Evapometer.
- LTM 1/2.
- AGI 1.
- NMR.
- RH.
- EXT 1-3.
- Open and closed twin.
- Fault/fracture labels.
- Convergence points.
- Laser scan objects.

The parsed Tecplot zones include 5 extensometer zones, 1 mini-piezometer zone, 22
fracture/crack-geometry zones, 12 miniprisma/geodetic zones, 2 laser-scan surface
zones, 6 RH/suction-support zones, and support zones for NMR, Taupe/TDR,
permeability, convergence points, evapometer, and niche geometry.

## Chapter 2 Alignment

The current report separates three uses that are easy to conflate:

- Direct pressure: mini-piezometer evidence is a high-value future residual, but it
  remains blocked until Geoscope exports provide values, timestamps, sensor support,
  units, absolute/gauge/head reference convention, quality flags, and uncertainty.
- Crackmeters, extensometers, laser scans, levelling, miniprisma, convergence, and
  auxiliary Geoscope streams: these are qualitative validation/support context now,
  not hard residuals, except for the extracted levelling slide-summary rows which
  are still diagnostic until the full survey table and reference frame are known.
- Fault/fracture geometry: the `Kluft`/layout zones are structural supports or
  scenario inputs. They should not be treated as measured pressure, saturation, or
  permeability unless a measured aperture, displacement, hydraulic effect, time,
  unit, and 3D-to-2D operator are supplied.

This wording matches
[chapter_02_measurements.tex](../../../mont_terri_questions_rewrite/paper/sections/chapter_02_measurements.tex)
and the current
[measurement_model_entry_matrix.md](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md).

## Extracted 2026 TD Notes

The May 2026 minutes report:

- RH/T: cold temperatures and low RH in winter 2025/2026.
- Horizontal and vertical extensometers BCD-A9/A10 in the closed niche had data failure since September 2025.
- Mini-piezometers BCD-A28 to BCD-A31 were working well.
- Crackmeter data show an ongoing trend in the closed niche and seasonal variation in the open niche.
- Open twin: an ongoing trend is observed by extensometer, suction, and Taupe.
- Closed twin: mostly static according to extensometer, pore pressure, and suction, except a crackmeter at one position showing ongoing closure.
- Proposed future work includes reinstallation of extensometer/fiber optics in the closed twin in 2027, drilling/geophysical characterization such as NMR, ERT, seismic, and permeability in early 2028, and climatization of the open twin at the end of 2028.

`CD-A_TD_2026_sc.pdf` frames BGR modelling comparison around:

- Displacements/strains from extensometers.
- Pore pressure from mini-piezometers.
- Pore pressure in the desaturated zone from suction.
- Stepwise benchmarking from simple 2D to complex 3D.
- A simplified perfect-ring 2D model whose simulated strain showed discrepancies
  against extensometer measurements.

`Folien_Niv_TD_CDA_2026.pdf` provides the current numeric levelling summary:

- Detectable displacement is 0.1 to 0.2 mm depending on point, at 95% confidence.
- The extracted height differences span from CDA-O1 = -2.1 mm settlement to
  CDA-C4 = +1.3 mm heave/uplift.
- Most points trend toward uplift except CDA-O1.

The HERMES overview PPTX files are short, but they state the goal of using CD-A measurements for numerical model improvement around the EDZ by combining physical and data-driven models.

## Modelling Relevance

These monitoring streams are likely secondary constraints compared with ERT/NMR/permeability/RH for the current HERMES modelling discussions, but they are important validation targets:

- Extensometers and displacement/strain data test the mechanical part of THM/TH2M simulations.
- Mini-piezometers test pore-pressure response in saturated or near-saturated regions.
- Crackmeters and laser scans help validate deformation/local closure and open/closed twin differences.
- Temperature/RH/opening-time records help interpret boundary forcing and disturbances.
- Levelling/miniprisma data can constrain longer-term deformation.
- The derived levelling table can become a deformation validation target after the
  survey reference frame is matched to OGS displacement output.

## Caveats

- Numeric time-series files for mini-piezometers, extensometers, crackmeters, and
  laser-scan statistical outputs were not present as separate spreadsheets in the
  scanned Gmail/TeamBeam material; the copied sources here are mainly reports,
  meeting minutes, presentations, and layout files. The derived missing-numeric
  request package now states exactly which exports and metadata are still needed.
  The numeric source audit checked 10 source files and 7 PDF ZIP members: all six
  request classes have local support evidence, but zero are hard-residual-ready.
- The precision-levelling slide summary has been extracted as 12 numeric rows, but a
  full survey table would still be better for weighting and reference-frame handling.
- The `VisualisationCDA.dat` file identifies many monitoring objects and their layout
  geometry but is not a clean monitoring time-series dataset.
- Data failures and maintenance states mentioned in the minutes should be considered before using any 2025/2026 HM monitoring signal.
