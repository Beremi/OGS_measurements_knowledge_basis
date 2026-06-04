# OGS Model Audit

This note records how the editable report folder relates to the OGS files received
from Gesa.

## Source Copies

- `GESA_model_original/2025-04-03_CDA_N4_2D_250403/CDA_N4_2D_250403/`
  contains the April 2025 model package, including the project file and mesh files.
- `GESA_model_original/2025-05-09_CDA_N4_2D_250509/` contains the May 2025 XML
  update package.
- `GESA_model_original/projection_on_mesh_2025-09-05/` contains the projection-on-mesh
  workflow recovered from the September 2025 exchange, including
  `generate_projections.py`, `bulk_w_projections.vtu`, and the XML/project variant
  that reads mesh-cell fields.
- `ogs_settings/` is the report-local copy used for the XML listings in the PDF.

## Provenance

- The report-local `ogs_settings` XML files were checked against the May 2025 Gesa
  XML package before editing the report.
- The report-local `cd_a_open_niche_quad.prj` is retained from the April 2025 model
  package, because the May 2025 package does not include the project file or meshes.
- The April-to-May model change is limited to the time-loop and fixed-timestep
  schedule files. The May package aligns monthly outputs with the ERT campaign
  schedule, with the first output at the end of September 2019.
- The original extracted model folders under `GESA_model_original/` are kept as
  source copies. The report-local XML files in `ogs_settings/` were converted to
  UTF-8 only so LaTeX can include their comments safely in listings.
- The projection workflow is kept separately from the frozen base model because it is
  a prototype for parameter-field injection, not the base model itself.

## Active Model Features Read From XML

- Process: `THERMO_RICHARDS_MECHANICS`.
- Primary variables: displacement, liquid pressure, and temperature.
- Time integration / nonlinear solve: Backward Euler with Newton iteration.
- Gravity / body force: inactive, because `specific_body_force` is `0 0`.
- Mechanical loading: `load_top` and initial stress parameters are defined in XML
  support files but are not bound as active process load terms in the current setup.
- Pressure boundary conditions: active top pressure and open-niche seasonal pressure.
  The outside pressure value exists as a parameter but is not active in the process
  boundary-condition block.
- Temperature boundary condition: outside temperature Dirichlet on `bulk_all`.
- Intrinsic permeability tensor: `k_i = (1.00e-19, 0, 0, 0.40e-19) m2`.
- Porosity and Biot coefficient: `phi = 0.105`, `biot = 1`.
- van Genuchten retention / relative permeability: residual liquid saturation `0.1`,
  residual gas saturation `0`, exponent `0.45`, air-entry pressure `10 MPa`, and
  minimum relative permeability `1e-25`.
- Liquid density model: linear pressure/temperature dependence around
  `rho0 = 1095 kg/m3`, `T0 = 298.15 K`, and `p0 = 7.5 MPa`.

## Caveats For The Report

- The active XML value `CTE = 1254.74` is physically implausible for a thermal
  expansivity in `1/K`; it is preserved as an XML fact but flagged in the report as
  requiring confirmation.
- The XML process is an OGS no-vapor TRM setup. This removes vapor transport, but it
  does not remove all thermal-hydraulic coupling: liquid density and viscosity still
  depend on temperature/pressure, and heat advection uses the Darcy velocity.
- The measurement chapter treats the model as frozen. Measurements enter through
  observation operators, boundary-condition reconstruction, validation targets, or
  externally generated inversion parameter fields, not by silently changing the
  governing equations.
- The copied projection workflow demonstrates one acceptable implementation route for
  those parameter fields: create cell-data arrays on the VTU mesh and reference them
  through OGS `MeshElement` parameters. Its included random fields are examples only
  and should be replaced by reproducible log-space anisotropic permeability fields for
  the actual inversion.
- `inversion_workflow/scripts/generate_anisotropic_permeability_field.py` is a first
  reproducible replacement for that example. It preserves the frozen OGS process and
  writes a four-component `k_i_rd` cell-data tensor in the same component order as the
  current 2D XML permeability tensor.
- `inversion_workflow/scripts/prepare_ogs_run.py` now creates a self-contained run
  directory from the projection model and writes `RUN_MANIFEST.json`. The smoke-test
  run confirmed that the generated `bulk_w_projections.vtu` contains both fields read
  by the projection XML: four-component `k_i_rd` and fixed-porosity `n_rd`.
