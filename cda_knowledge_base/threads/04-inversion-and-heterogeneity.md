# Inversion And Heterogeneity

## Main Inversion Target

The strongest repeated modelling target is estimating a heterogeneous permeability field around the CD-A niches, especially the open niche, using ERT-derived water content/saturation and additional measurements.

Gesa suggested the first modelling stage should focus on ERT data converted to water content or saturation, because ERT provides better spatial/temporal coverage than NMR.

## Candidate Data Constraints

Primary:

- ERT-derived water content/saturation.

Secondary or validation constraints:

- NMR water content;
- Taupe/TDR saturation or water-content proxy;
- suction/relative humidity converted to saturation;
- direct permeability pulse-test values;
- bedding-angle and geological/structural characterization.

## Candidate Parameters

Parameters mentioned as possible fitting/comparison elements:

- permeability;
- pressure boundary condition from RH/Kelvin equation;
- retention curve `pc-S`;
- relative permeability `krel-S`;
- porosity;
- storativity;
- stress boundary condition;
- EDZ spatial extent and/or segmented domains.

## Static First, Time-Dependent Later

Gesa explicitly said permeability can change over time because of self-healing processes, and the change differs by location. She recommended starting without time dependency and adding it later if needed.

This suggests the practical modelling workflow:

1. Build static heterogeneous fields.
2. Insert fields into OGS through mesh values or functions.
3. Compare saturation/water-content output to ERT and NMR.
4. Check consistency with permeability measurements and bedding direction.
5. Add time-dependent permeability only after the static inversion is reliable.

## Bedding And Anisotropy

Permeability anisotropy should be linked to bedding orientation. The December 2025 TeamBeam transfer includes bedding material and Gesa mentioned a bedding angle of approximately 144 degrees.

This matters for random fields:

- use bedding direction as a preferred correlation direction;
- avoid treating anisotropy as unstructured noise;
- expect EDZ effects near the opening to modify the bedding-controlled background.

## Mesh Projection

The September 2025 slides and Tuanny's comments support using mesh-based heterogeneous parameters in OGS.

The likely workflow is:

```text
generate random field or projected parameter values
project values onto OGS mesh
write mesh fields / projection files
run identifySubdomains if needed
modify parameters_TRM.xml to read projected values
run OGS and compare output to measurement-derived fields
```

The recovered attachment `attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip` contains a concrete BGR example of this workflow, including `generate_projections.py`, projected meshes, OGS XML files, and specifications.

## Bayesian / ML Context

By April 2026, Michal reported progress on random-field modelling and said Simona was working on the topic too. Gesa asked for the citation:

`Beresova S, Beres M, Luber T. 2025. Bayesian inversion with neural network surrogates for TSX parameter estimation.`

This suggests the CD-A work may reuse or adapt a surrogate-assisted Bayesian inversion workflow from the TSX context.

## Recommended Working Data Order

1. Use the collected TeamBeam model packages and ERT zip.
2. Use the Thunderbird-recovered heterogeneous projection zip.
3. Load `Mess_Koord_XY.xlsx` and define measurement-to-model coordinate mapping.
4. Decide on the ERT water-content/saturation relation to use for first tests.
5. Create a baseline static heterogeneous permeability field.
6. Validate against NMR and direct permeability.
7. Add Taupe/suction only after the baseline pipeline is stable.
