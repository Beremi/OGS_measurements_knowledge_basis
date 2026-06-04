# OGS Formulation Consistency Audit

This audit checks the report's formulation statements against the active source XML and the representative run-local XML used by the workflow.

## Summary

- Status: `ogs_formulation_consistency_audit_generated`
- Check count: 18
- Pass count: 17
- Tracked caveat count: 2
- Fail count: 0
- Source process type: `THERMO_RICHARDS_MECHANICS`
- Primary variables: displacement, pressure, temperature
- Run-local output variables: pressure, saturation, temperature, displacement, porosity
- Run-local optimized/field parameters: {'phi': 'n_rd', 'k_i': 'k_i_rd'}

## Checks

| Check | Status | XML evidence | Implication |
| --- | --- | --- | --- |
| `process_type_and_primary_variables` | `pass` | type=THERMO_RICHARDS_MECHANICS; variables=['displacement', 'pressure', 'temperature'] | The report's primary variable list matches the process XML. |
| `gravity_specific_body_force_off` | `pass` | specific_body_force=0 0 | The no-gravity Darcy expression in the report is consistent with the XML. |
| `process_variable_orders_and_bcs` | `pass` | displacement={'components': '2', 'order': '2', 'initial_condition': 'ic_displacement', 'boundary_conditions': [{'mesh': 'cd-a_left', 'type': 'Dirichlet', 'component': '0', 'parameter': 'bc_displacement'}, {'mesh': 'cd-a_right', 'type': 'Dirichlet', 'component': '0', 'parameter': 'bc_displacement'}, {'mesh': 'cd-a_top', 'type': 'Dirichlet', 'component': '1', 'parameter': 'bc_displacement'}, {'mesh': 'cd-a_bottom', 'type': 'Dirichlet', 'component': '1', 'parameter': 'bc_displacement'}]}; pressure={'components': '1', 'order': '1', 'initial_condition': 'ic_pressure', 'boundary_conditions': [{'mesh': 'cd-a_top', 'type': 'Dirichlet', 'component': '', 'parameter': 'bc_top_pressure'}, {'mesh': 'cd-a_niche4', 'type': 'Dirichlet', 'component': '', 'parameter': 'open_niche_seasonal'}]}; temperature={'components': '1', 'order': '1', 'initial_condition': 'ic_temperature', 'boundary_conditions': [{'mesh': 'bulk_all', 'type': 'Dirichlet', 'component': '0', 'parameter': 'bc_temperature_outside'}]} | The active finite-element variable orders and boundary-condition assignment are traceable. |
| `liquid_density_linear_temperature_pressure` | `pass` | {"independent_variables": {"liquid_phase_pressure": {"reference_condition": "7.5e6", "slope": "3.2e-10"}, "temperature": {"reference_condition": "298.15", "slope": "-5E-4"}}, "reference_value": "1095", "type": "Linear"} | The report's storage and thermal-coupling discussion should retain density derivatives. |
| `vapor_terms_absent_from_active_phase` | `pass` | active vapor-like properties=[] | Vapor-density, vapor-diffusion, and latent-heat terms must not be included as active equations. |
| `relative_permeability_van_genuchten` | `pass` | {'type': 'RelativePermeabilityVanGenuchten', 'parameter_name': '', 'residual_liquid_saturation': '0.1', 'residual_gas_saturation': '0', 'exponent': '0.45', 'minimum_relative_permeability_liquid': '1e-25', 'p_b': '', 'reference_value': ''} | The permeability fitting should alter intrinsic permeability, not the relative-permeability function. |
| `saturation_van_genuchten_retention` | `pass` | {'type': 'SaturationVanGenuchten', 'parameter_name': '', 'residual_liquid_saturation': '0.1', 'residual_gas_saturation': '0', 'exponent': '0.45', 'minimum_relative_permeability_liquid': '', 'p_b': '10e6', 'reference_value': ''} | Retention parameters should stay gated unless an explicit release decision is recorded. |
| `bishop_power_law_saturation` | `pass` | {'type': 'BishopsPowerLaw', 'parameter_name': '', 'residual_liquid_saturation': '', 'residual_gas_saturation': '', 'exponent': '1', 'minimum_relative_permeability_liquid': '', 'p_b': '', 'reference_value': ''} | The compact pore-stress term b(S) alpha p I becomes S p I only after XML substitutions. |
| `linear_elastic_orthotropic` | `pass` | constitutive_relation_types=['LinearElasticOrthotropic', 'LinearElasticOrthotropic'] | Report equations should keep the generalized Hooke-law representation. |
| `swelling_stress_active` | `pass` | {'type': 'SaturationDependentSwelling', 'parameter_name': '', 'residual_liquid_saturation': '', 'residual_gas_saturation': '', 'exponent': '', 'minimum_relative_permeability_liquid': '', 'p_b': '', 'reference_value': ''} | The mechanical equation should not be presented as purely thermoelastic. |
| `thermal_conductivity_effective_porosity_mixing` | `pass` | {'type': 'EffectiveThermalConductivityPorosityMixing', 'parameter_name': '', 'residual_liquid_saturation': '', 'residual_gas_saturation': '', 'exponent': '', 'minimum_relative_permeability_liquid': '', 'p_b': '', 'reference_value': ''} | The heat-balance section should keep porosity/saturation in effective storage and conduction. |
| `biot_coefficient_one` | `pass` | media={'type': 'Parameter', 'parameter_name': 'biot', 'residual_liquid_saturation': '', 'residual_gas_saturation': '', 'exponent': '', 'minimum_relative_permeability_liquid': '', 'p_b': '', 'reference_value': ''}; parameter={'type': 'Constant', 'value': '', 'values': '1', 'field_name': '', 'curve': '', 'parameter': '', 'expression': ''} | The report's alpha_B=1 substitution is valid for this model. |
| `intrinsic_permeability_source_constant_run_mesh_field` | `pass` | source k_i={'type': 'Constant', 'value': '', 'values': '1.00E-19 0.00 0.00 0.40E-19', 'field_name': '', 'curve': '', 'parameter': '', 'expression': ''}; run k_i={'type': 'MeshElement', 'value': '', 'values': '', 'field_name': 'k_i_rd', 'curve': '', 'parameter': '', 'expression': ''} | This is a parameter-field substitution, not a change to the OGS process equations. |
| `porosity_run_mesh_field_fixed_support` | `pass_with_caveat` | source phi={'type': 'Constant', 'value': '', 'values': '0.105', 'field_name': '', 'curve': '', 'parameter': '', 'expression': ''}; run phi={'type': 'MeshElement', 'value': '', 'values': '', 'field_name': 'n_rd', 'curve': '', 'parameter': '', 'expression': ''}; n_rd stats={'metric': 'n_rd', 'finite_count': 10239, 'min': 0.105, 'p01': 0.105, 'p05': 0.105, 'p10': 0.105, 'p50': 0.105, 'p90': 0.105, 'p95': 0.105, 'p99': 0.105, 'max': 0.105, 'mean': 0.105, 'std': 0.0, 'area_weighted_mean': 0.105} | Report wording should distinguish mesh-element representation from released/optimized porosity. |
| `cte_value_tracked_provenance_caveat` | `tracked_caveat` | CTE={'type': 'Constant', 'value': '', 'values': '1254.74', 'field_name': '', 'curve': '', 'parameter': '', 'expression': ''}; c_p_s={'type': 'Constant', 'value': '', 'values': '1254.74', 'field_name': '', 'curve': '', 'parameter': '', 'expression': ''} | The report should not infer a physically accepted thermal-expansivity calibration from this XML value. |
| `run_local_output_variables_for_observation_operators` | `pass` | source output variables=[]; run output variables=['pressure', 'saturation', 'temperature', 'displacement', 'porosity'] | State, ERT, Taupe/TDR, and NMR operators can sample the needed run-local VTU quantities. |
| `run_local_process_and_media_semantics_unchanged` | `pass` | changed core XML files=[] | The workflow changes field values and output selection, not the governing process definition. |
| `active_boundary_conditions_and_inactive_defined_parameters` | `pass` | active BC parameters=['bc_displacement', 'bc_temperature_outside', 'bc_top_pressure', 'open_niche_seasonal']; defined inactive examples=bc_pressure_outside, load_top, ic_sigma0 | Inactive XML parameters should not be described as active forcing terms. |

## Interpretation

- The exchanged source XML is a THERMO_RICHARDS_MECHANICS model with displacement, pressure, and temperature as primary variables; gravity is disabled.
- The active run-local workflow changes parameter representation for permeability and porosity to mesh-element fields, while preserving the OGS process, phase laws, boundary-condition structure, and constitutive relation semantics.
- The permeability field is the actual heterogeneous tensor field used for fitting; the porosity mesh field is fixed support in the current field package (`n_rd` is spatially constant at 0.105).
- The CTE value remains a tracked provenance caveat, not a formulation blocker and not a released fit parameter.

## Source Artifacts

- `ogs_settings/01_processes_TRM.xml`
- `ogs_settings/02_process_variables_TRM.xml`
- `ogs_settings/03_parameters_TRM.xml`
- `ogs_settings/04_media_TRM.xml`
- `ogs_settings/04_1_media_aqu_liq.xml`
- `ogs_settings/04_2_media_twophase.xml`
- `ogs_settings/05_time_loop_TRM.xml`
- `inversion_workflow/runs/direct_fit_observation_run/03_parameters_TRM.xml`
- `inversion_workflow/runs/direct_fit_observation_run/05_time_loop_TRM.xml`
- `inversion_workflow/current_permeability_field/current_best_field_stats.csv`
