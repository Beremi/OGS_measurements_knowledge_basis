# OGS Models And Model Setup

## Model Formulation

Gesa described the current benchmark model as TRM in OGS6: Thermo-Richards-Mechanics. TH2M, involving two-phase flow, is available in OGS but was not the initial benchmark model.

The model work discussed in the emails starts from a 2D open-niche model, but BGR also maintains or plans broader CD-A model variants including 3D and larger-domain 2D setups.

## Transferred Model Packages

Two TeamBeam model transfers are central:

- `CDA_N4_2D_250403.zip`: initial 2D model package.
- `CDA_N4_2D_250509.zip`: updated model with less output and faster runtime.

The April 2025 transfer also included:

- `apptainer_ogs6.5.4.sif`
- `docker_ogs6.5.4.tar.gz`
- `Dockerfile`
- `ReadMe.md`

Kristof Kessler was named as the contact for the container; Gesa was the contact for the 2D model.

## Runtime And Output

Tuanny reported that the updated CD-A setup improved runtime and output volume:

- runtime roughly 10 minutes;
- larger time steps;
- more compact output.

This makes the 2D model more suitable for repeated calibration or inversion loops than the original package.

## Existing EDZ Approach

The existing simplified EDZ approach uses:

- reduced strength;
- increased permeability;
- circular region around the opening.

Gesa noted that this is not realistic enough to represent the full near-field physics, but it is the current modelling simplification and a useful baseline.

## Heterogeneous Parameters

Tuanny confirmed that OGS can represent spatial heterogeneity with:

- functions;
- mesh fields / spatially distributed mesh values.

The September 2025 slides describe a projection workflow:

```text
main mesh (bulk.vtu)
  -> generate_projections.py
  -> bulk_w_projections.vtu
  -> identifySubdomains -m bulk_w_projections.vtu bulk_all.vtu *.prj
  -> parameters_TRM.xml reads projected values
```

The Thunderbird-recovered attachment `attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip` is the concrete example for this workflow.

## Model/Data Comparison

The model output of most interest is saturation or water content. The data side includes:

- ERT-derived water content/saturation;
- NMR direct water-content measurements;
- Taupe/TDR water-content or saturation proxy;
- suction/relative humidity converted through Kelvin and retention relations;
- direct permeability pulse-test measurements.

The ERT mesh and FEM mesh mismatch remains a practical implementation issue. BGR can provide evaluated measurement values and coverage/accuracy; the modelling side needs to decide whether to interpolate, project, or request data on a specific model mesh/surface.
