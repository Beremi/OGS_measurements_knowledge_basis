# CD-A Modelling Knowledge Base

## Collaboration Objective

The collaboration around CD-A is framed as a HERMES Task 5 effort to combine BGR's Mont Terri CD-A measurements and modelling experience with IGN/UGN data-driven methods. The recurring goal in the emails is to use measured geophysical and hydromechanical data to improve numerical models of the CD-A niches, especially the near-field excavation disturbed zone (EDZ), water-content evolution, and permeability field.

The practical modelling target discussed most often is:

- start from a 2D OGS model of the open CD-A niche;
- use ERT-derived water-content/saturation information and supporting measurements;
- infer or parameterize a heterogeneous permeability field around the niche;
- compare modelled saturation/water-content evolution against ERT, NMR, Taupe, suction, and permeability measurements;
- later revisit time dependency and self-healing of permeability.

## Numerical Model Context

The numerical modelling stack is OGS6. BGR describes the current benchmark model as TRM, meaning Thermo-Richards-Mechanics. TH2M, a two-phase-flow formulation, was mentioned as possible but not the current default for the initial benchmark.

Model levels mentioned in the emails and slides:

- 3D CD-A model: excavation, gallery/niches, long-term excavation/desaturation, and field-scale validation.
- 2D 100 m x 100 m model: desaturation with homogeneous EDZ and host rock.
- 2D 10 m x 10 m model: desaturation with ERT/NMR data and more precise geometry.
- 2D idealized quarter/ring model: simplified EDZ geometry and controlled parameter studies.

The April 2025 model transfer supplied:

- `CDA_N4_2D_250403.zip`
- OGS 6.5.4 container files for Docker and Apptainer
- `ReadMe.md`
- `Dockerfile`

The May 2025 update supplied:

- `CDA_N4_2D_250509.zip`
- described as faster and producing less output

Tuanny later reported the updated setup had roughly 10 minute runtime, larger time steps, and more compact output.

## Existing EDZ Representation

The model currently uses a simplified EDZ approach: reduced strength and increased permeability in a circular area around the opening. Gesa described this as not fully realistic, but useful as a starting point.

The collaboration could test how far that simplified approach can go and where it fails when constrained by measured water-content and permeability information.

## Target Parameters

The main parameter of interest is the permeability field around the niches. The emails also discuss related parameters that may be part of a broader inversion or calibration:

- permeability;
- pressure boundary condition derived from relative humidity via the Kelvin equation;
- retention curve, especially `pc-S`;
- relative permeability curve, `krel-S`;
- porosity;
- storativity;
- stress boundary condition;
- EDZ geometry or near-field spatial domains.

BGR's permeability measurements show strong contrasts between open and closed niches and between directions. The CD-A presentation from February 2025 notes approximate permeability differences:

- open twin: around `1e-15 m2`;
- closed twin: around `1e-19 m2`;
- clearer differences in vertical direction and over time;
- significant differences up to about 1.5 m from the opening.

## Heterogeneous Field Support in OGS

Tuanny confirmed that OGS can support heterogeneous properties through functions and spatially distributed mesh values. The September 2025 modelling slides also describe a projection workflow:

1. Generate spatial fields/projections, using `generate_projections.py`.
2. Start from the main mesh, noted as `bulk.vtu`.
3. Produce a mesh containing projected values, noted as `bulk_w_projections.vtu`.
4. Use `identifySubdomains` with the mesh and projection files.
5. Update `parameters_TRM.xml` so parameters are read from projected values instead of hard-coded constants.

This is the clearest workflow mentioned for inserting heterogeneous permeability or other parameter distributions into the OGS model.

## Coordinates And Geometry

Gesa sent `Mess_Koord_XY.xlsx` and `Mess_Koord_XY.jpg` with measurement coordinates. For the relevant 2D model, use the columns labelled `2D_Model (x/y)`. Gesa noted that closed-twin coordinates can be disregarded for the current open-niche modelling task.

The measurement locations are not perfectly on a common surface:

- ERT uses a laser-scan profile at the ERT position.
- NMR positions use another profile closer to the gallery.
- Measurement points therefore do not all sit exactly on the same model boundary.

This needs a modelling decision: either project measurements to the model boundary/surface, or keep track of measurement-specific geometry offsets.

## ERT Data

ERT is central because it provides the richest spatial and temporal water-content proxy. Markus Furche's explanation, relayed by Gesa, says ERT measures resistance between sensor pairs, with roughly 2500 measurements per niche. Raw ERT values are difficult to use directly; BGR can provide evaluated data and coverage/accuracy information at each point.

Important ERT modelling points:

- Reference day in the February 2025 slides: 31 October 2019.
- Electrodes #17 and #18 were not used in the shown evaluation.
- BGR can provide daily VTK-style ERT data.
- ERT fields mentioned: resistivity, delta resistivity, log resistivity, and phase angle.
- Reliability decreases with distance from sensors.
- Reliable ERT region is about 1.5 m radius but only around 35 cm into the rock.
- The ERT mesh is not identical to the FEM mesh.
- The FEM mesh was based on laser-scan geometry; the ERT mesh was based on sensor positions.
- Gesa asked whether ERT mesh data are acceptable directly, or whether BGR needs to transform them to match the FEM mesh or surface boundary.

Raw ERT examples were later sent for 1 September 2022:

- `.tx0` file: data from both niches, with open niche records #1-#2592 and closed niche records #2593-#5184.
- `.ohm` files: inversion inputs.
- `elecs_open.txt` and `elecs_closed.txt`: electrode positions.

## ERT To Water Content Or Saturation

The April 2025 email supplied the `WC_vs_RHO_2025-02.xlsx` and `WC_vs_RHO_open-closed.pdf` relation between resistivity and water content.

The September 2025 modelling discussion later referred to the open-twin relation:

`y = 1.44 x^-1.51`

The slides also note the conversion:

`S = WC_vol / n`

where `S` is saturation, `WC_vol` is volumetric water content, and `n` is porosity.

This relation should be treated carefully because Gesa and BGR were still discussing which evaluated ERT-water-content relation to use. Updated ERT/water-content modelling was still expected around June 2026.

## NMR Data

NMR provides direct water-content measurements and is used as a possible independent constraint in the Bayesian inverse problem. Stephan Costabel supplied NMR water-content data in September 2025.

The weekly NMR data files are:

- `Weekly_2021-2022_at_4S.dat`
- `Weekly_2022-2025_at_4E.dat`

Column meanings:

- time;
- water content in vol%;
- 95% confidence interval for water content;
- T2 relaxation time in ms;
- 95% confidence interval for T2.

For the current modelling purpose, Stephan noted that columns 4 and 5 can be ignored.

Known NMR caveats:

- Gaps exist because of technical failures.
- From February to April 2025, a detuned wrong frequency caused slight overestimation of about 1 vol%.
- Seasonal data include figures and ASCII files; filenames encode dates.
- Seasonal columns are position, water content in vol%, and 95% confidence interval.
- Before autumn 2021, only floor and ceiling were measured.
- September 2020 only has floor measurements.
- Winter 2024 is missing.

The NMR slide material distinguishes sparse seasonal measurements from ongoing measurements at selected positions. Gesa proposed using ERT first because it is denser, with NMR as an additional constraint.

## Taupe/TDR Data

Gesa described Taupe measurements as post-processed apparent relative dielectric permittivity, interpreted in terms of water content or saturation. The conceptual relation in the slides is:

`epsilon_r = epsilon_rock * (1 - phi) + epsilon_w * phi * S_w`

where:

- `epsilon_w` is approximately 80;
- `phi` is porosity;
- `S_w` is water saturation.

Gesa said BGR can provide the mean amplitude of saturation change by distance intervals from the niche wall. Taupe data were not fully attached in Gmail; a TeamBeam transfer named `003_Nov_2025.zip` likely contains additional November 2025 measurements.

## Suction And Relative Humidity

Suction measurements are relevant for pressure boundary conditions and saturation conversion. The September 2025 slides mention using the Kelvin equation and van Genuchten retention curve to compute saturation from relative humidity.

The April/May 2026 technical discussion minutes report:

- thermo-hygrometers appear best for the open niche;
- psychrometers appear better for the closed niche;
- some sensor readings are affected by data logger/software problems;
- suction measurement work continues and was part of the April 2026 technical discussion.

Measurements are discussed at depths of 40 cm and 70 cm in horizontal and vertical directions.

## Permeability Anisotropy And Bedding

Gesa answered that permeability anisotropy should be tied to the orientation of bedding planes. The near-field can be modified by the EDZ, but the general expectation is higher permeability along bedding.

The December 2025 TeamBeam transfer supplied bedding-angle context:

- approximate bedding angle: 144 degrees;
- included `bedding_angle_ERT.png`;
- included `bedding_page_4_Ziefle_GETE_2022.pdf`;
- included permeability update material.

The modelling implication is that heterogeneous permeability should not be treated as arbitrary spatial noise only. It should respect bedding orientation where the data support that.

## Time Dependency And Self-Healing

Gesa stated that permeability differs by location and evolves over time due to self-healing processes. However, she suggested starting without time dependency and later revisiting it.

Recommended modelling sequence from the email evidence:

1. Begin with a static heterogeneous permeability field.
2. Fit or constrain it using available ERT/water-content data and direct permeability measurements.
3. Add other measurement types as validation or additional constraints.
4. Consider time-dependent permeability/self-healing only after the static inversion workflow is stable.

## Inversion Strategy

The intended inversion problem was not fully specified in the emails, but the direction is clear:

- use ERT-derived saturation/water content as the primary spatial data source;
- use NMR as a direct water-content anchor;
- use Taupe/TDR and suction data as secondary constraints;
- use direct permeability measurements to guide plausible permeability magnitude, anisotropy, and location dependence;
- infer a heterogeneous permeability field around the open niche;
- compare model saturation against measured water-content/saturation products.

User-side progress mentioned in April 2026:

- random-field modelling was progressing;
- Simona was working on the topic;
- Tomáš planned a stay at BGR in June 2026.

## Data And File Locations

Downloaded Gmail attachments are cataloged in [attachment_catalog.md](./attachments/attachment_catalog.md).

TeamBeam file-transfer metadata, including exact file names and hashes, is cataloged in [teambeam_files.md](./file_transfers/teambeam_files.md). The TeamBeam files are now collected locally under `file_transfers/collected`. Raw/archive Gmail attachments that the connector could not download are recovered under `attachments/thunderbird_recovered`.

For agent navigation, use the root [repository README](../README.md) first, then
the source-oriented [measurement catalogue](./measurements/README.md), the
generated [measurement-info mirror](./measurements_info/README.md), and the
model-facing [processed observation tables](../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/README.md).
The joined current-use and gate status is in
[measurement_model_entry_matrix.md](../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_model_entry_matrix.md);
the strict activation blockers are in
[measurement_stream_activation_gate_audit.md](../SOTA_OGS_Mont_Terri_work/inversion_workflow/measurement_stream_activation_gate_audit.md);
the report-side semantics are in
[chapter_02_measurements.tex](../mont_terri_questions_rewrite/paper/sections/chapter_02_measurements.tex).
