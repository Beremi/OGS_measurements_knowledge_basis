# Inversion Parameter Release Plan

This audit records which OGS parameters are allowed to vary in the current
measurement-driven workflow and which ones must remain fixed until the
corresponding observation operators, state outputs, or provenance checks exist.
It is generated from the local OGS XML, the projection parameter files, the
measurement likelihood model, and the regularized OGS candidate-set handoff.

## Current Decision

- Fit only the intrinsic permeability tensor magnitude field `k_i_rd` as the active released field in stage 1.
- Use sampled NMR state residuals in the current active objective, but do not release porosity `n_rd` because the final NMR policy is unapproved and porosity, saturation, and bound/interlayer water remain non-identifiable.
- Keep tensor shape, van Genuchten, relative-permeability, elastic, swelling, Biot, thermal, and initialization values fixed until their gates are approved.
- Do not spend more same-support active-objective OGS batches until support, likelihood, bounds, or stream-gate evidence changes.
- Treat the open-niche pressure curve and suspicious `CTE` value as provenance/confirmation blockers, not as ordinary fit parameters.

## Current Evidence Snapshot

- Active objective components: `2`.
- Current total active objective: `3156.353066948979`.
- Direct permeability objective: `269.8180571059851` over `75` rows.
- Sampled-state objective: `2886.535009842994` over `192` NMR rows from `83` OGS output times.
- NMR final policy selected: `False`; current report policy: `retain_raw_absolute_theta_current_report_default_with_caveats`.
- Same-support active-objective batch executable now: `False`; recommendation: `pause_same_support_active_objective_ogs_until_likelihood_support_bounds_or_stream_gate_changes`.
- Support-conflict cells: active `30`, repeated `24`, range >=2 log10 `16`.
- Open external/provenance blockers: `8`.
- Candidate-set OGS mode: `execute` with `3` selected candidates.

## Stage Counts

| Stage | Rows |
| --- | ---: |
| `blocked_or_confirm_provenance` | 1 |
| `blocked_or_confirm_value` | 1 |
| `fixed_for_current_experiment` | 1 |
| `fixed_model_setup_confirm_before_mechanics` | 1 |
| `fixed_numerical_control` | 1 |
| `stage_1_active_field` | 1 |
| `stage_1_fixed_support_field` | 1 |
| `stage_2_candidate_scalar` | 2 |
| `stage_2_candidate_tensor_shape` | 1 |
| `stage_2_fixed_until_retention_data` | 1 |
| `stage_3_candidate_mechanical` | 2 |
| `stage_3_validation_only` | 1 |

## Release Table

| Order | Parameter group | OGS entry | Stage | Recommendation | Gate |
| ---: | --- | --- | --- | --- | --- |
| 1 | intrinsic permeability tensor magnitude field | `medium property permeability -> parameter k_i / MeshElement field k_i_rd` | `stage_1_active_field` | Fit now as a run-local MeshElement tensor field. The current deterministic candidates multiply the existing four-component tensor by scalar cell factors, preserving tensor symmetry, orientation, and anisotropy ratio while changing magnitude. | Already active for inside-mesh positive-k intervals; next gate is OGS-backed state-output plausibility. |
| 2 | permeability tensor shape: anisotropy ratio, orientation, off-diagonal terms | `same k_i_rd tensor components k_xx k_xy k_yx k_yy` | `stage_2_candidate_tensor_shape` | Do not release tensor shape in the first fit. Keep the current bedding-parallel tensor geometry and test scalar magnitude fields first; release anisotropy ratio or orientation only after directional permeability/support evidence and OGS state diagnostics justify the extra degrees of freedom. | Activate only after the direct support/likelihood policy is approved, repeated-support conflicts are resolved or explicitly retained, and OGS-backed state diagnostics show material benefit from tensor-shape degrees of freedom. |
| 3 | porosity support field | `medium property porosity -> parameter phi / MeshElement field n_rd` | `stage_1_fixed_support_field` | Keep fixed in the first permeability inversion. The projection machinery can read n_rd, but the current field is a fixed porosity support, not an active unknown. | Release as scalar or field only after the final NMR residual policy is approved, ERT/Taupe uncertainty gates are closed or excluded, and a sensitivity audit separates porosity from saturation and bound/interlayer-water effects. |
| 4 | van Genuchten air-entry pressure | `property saturation / p_b` | `stage_2_candidate_scalar` | Treat as a later scalar retention parameter, not as an active first-stage unknown. It should be released only after RH boundary provenance and state-output sampling are settled. | Confirm or reconstruct 08_08_open_niche_seasonal.xml, select the NMR residual policy, and close or explicitly exclude ERT/Taupe/RH gates before fitting. |
| 5 | van Genuchten exponent | `properties saturation and relative_permeability / exponent` | `stage_2_candidate_scalar` | Keep fixed in the first OGS comparison set. Consider a scalar release together with p_b only after retention-sensitive state residuals are active. | Release only as a paired retention calibration after the p_b, NMR-policy, and RH-provenance gates are satisfied. |
| 6 | residual saturations | `relative_permeability and saturation / residual_liquid_saturation, residual_gas_saturation` | `stage_2_fixed_until_retention_data` | Keep fixed for current and near-term runs. Residual saturations should not be inferred from the present field data unless independent retention/hysteresis constraints are added. | Require dedicated retention information or a sensitivity study proving state residuals can distinguish residual saturation. |
| 7 | relative-permeability numerical floor | `relative_permeability / minimum_relative_permeability_liquid` | `fixed_numerical_control` | Keep fixed. Treat this as a numerical floor, not a physical calibration parameter. | Only revisit in a numerical robustness study if very dry cells appear in OGS outputs. |
| 8 | open-niche pressure boundary curve | `parameter open_niche_seasonal / pressure_scaling_factor / open_niche_seasonal_curve` | `blocked_or_confirm_provenance` | Do not treat as an ordinary material parameter. Reconstruct the curve from RH/T data or obtain its preprocessing provenance before fitting or scaling it. | Confirm how 08_08_open_niche_seasonal.xml was generated; then decide whether to fit only a documented scaling/bias term. |
| 9 | orthotropic elasticity | `parameters E, G, nu / LinearElasticOrthotropic` | `stage_3_candidate_mechanical` | Keep fixed for hydraulic calibration. Consider scalar or facies-level mechanical release only after numerical displacement/pressure outputs are compared with levelling, extensometer, piezometer, and scan data. | Locate numeric HM time series, sample displacement/pressure OGS outputs, then run sensitivity checks before release. |
| 10 | Biot coupling coefficient | `medium property biot_coefficient -> parameter biot` | `stage_3_candidate_mechanical` | Keep fixed at 1.0 unless a dedicated poromechanical identifiability study supports release. | Require active pressure/displacement residuals and mechanical calibration data before fitting. |
| 11 | saturation-dependent swelling | `solid property swelling_stress_rate / SaturationDependentSwelling` | `stage_3_validation_only` | Keep fixed and use as a mechanical plausibility check first. Releasing swelling parameters needs calibrated saturation/displacement evidence, not only hydraulic pulse-test misfit. | Activate only after displacement outputs and numeric HM series support a mechanical likelihood. |
| 12 | thermal and liquid transport constants | `rho_s, kappa_th_s, c_p_s, c_p_l, kappa_l, eta, liquid density, thermal mixing` | `fixed_for_current_experiment` | Keep fixed. The current measurement catalogue is hydraulic/water-content dominated and does not support fitting thermal constants or water viscosity/density law. | Revisit only if a real thermal experiment or temperature-gradient likelihood is added. |
| 13 | solid thermal expansivity | `solid property thermal_expansivity -> parameter CTE` | `blocked_or_confirm_value` | Confirm the XML value and units before any physical interpretation. The generated thermal-expansivity audit shows that CTE equals c_p_s in the base file, has a heat-capacity-like XML comment, and is 4.826e+07 times the high end of the cited HE-D solid thermal-expansion range. | Do not release or physically interpret CTE until Gesa/BGR confirms whether the XML value should be near 1e-5 1/K, a different value, or inactive in the intended run. |
| 14 | initial pressure and stress setup | `ic_pressure, ic_sigma0, bc_top_pressure, load_top` | `fixed_model_setup_confirm_before_mechanics` | Keep fixed for permeability fitting. Treat initial pressure/stress expressions as provenance items to audit before any mechanical or pressure-boundary calibration. | Audit active process-variable references and numeric HM/pressure data before release. |

## Parameter Details

### 1. intrinsic permeability tensor magnitude field

- OGS entry: `medium property permeability -> parameter k_i / MeshElement field k_i_rd`
- Base definition: `Constant; 1.00E-19 0.00 0.00 0.40E-19`
- Projection/run definition: `projection: MeshElement; field_name=k_i_rd; selected run: MeshElement; field_name=k_i_rd`
- Release stage: `stage_1_active_field`
- Model quantity affected: Darcy mobility through intrinsic permeability K in v = -(k_rel K / mu) grad p; also controls saturation, theta, RH-response, ERT, Taupe/TDR, and HM state outputs after OGS runs.
- Measurement evidence: Direct pulse-test likelihood is active with 75 objective rows from 204 candidate rows; the current active objective has 2 components and totals 3156.353066948979, with direct objective 269.8180571059851 plus sampled-state objective 2886.535009842994.
- Identifiability risk: Pulse tests are scalar interval-scale constraints on e^T K e, not full tensor observations. Gas/slip interpretation, 3D-to-2D support, and duplicate intervals remain explicit model-error terms.
- Activation gate: Already active for inside-mesh positive-k intervals; next gate is OGS-backed state-output plausibility.
- Source files: `ogs_settings/03_parameters_TRM.xml; GESA_model_original/projection_on_mesh_2025-09-05/03_parameters_TRM.xml; inversion_workflow/runs/regularized_ogs_candidate_001_length_0p025m/03_parameters_TRM.xml; inversion_workflow/measurement_likelihood_model.csv`

### 2. permeability tensor shape: anisotropy ratio, orientation, off-diagonal terms

- OGS entry: `same k_i_rd tensor components k_xx k_xy k_yx k_yy`
- Base definition: `Constant; 1.00E-19 0.00 0.00 0.40E-19`
- Projection/run definition: `MeshElement; field_name=k_i_rd`
- Release stage: `stage_2_candidate_tensor_shape`
- Model quantity affected: Directional Darcy response and lateral redistribution of pressure/saturation around the niche.
- Measurement evidence: Bedding/geometry layers constrain orientation qualitatively; direct pulse-test residuals currently constrain only interval-projected directional permeability. The global anisotropy screen selected anis_theta_144p0_ratio_2p50 with direct delta 0.0, while the local tensor-anisotropy screen best candidate local_anis_isotropize_l0p015_s0p5_r1 has direct delta 0.18992005641422338; this is not enough to release tensor shape before support/likelihood and stream-gate decisions.
- Identifiability risk: A scalar interval value can be fit by many tensor combinations. Releasing angle and anisotropy too early would trade off against support mapping and local magnitude updates.
- Activation gate: Activate only after the direct support/likelihood policy is approved, repeated-support conflicts are resolved or explicitly retained, and OGS-backed state diagnostics show material benefit from tensor-shape degrees of freedom.
- Source files: `GESA_model_original/projection_on_mesh_2025-09-05/03_parameters_TRM.xml; inversion_workflow/runs/regularized_ogs_candidate_001_length_0p025m/03_parameters_TRM.xml; inversion_workflow/processed_observations/borehole_line_mesh_samples.csv`

### 3. porosity support field

- OGS entry: `medium property porosity -> parameter phi / MeshElement field n_rd`
- Base definition: `Constant; 0.105`
- Projection/run definition: `projection: MeshElement; field_name=n_rd; selected run: MeshElement; field_name=n_rd`
- Release stage: `stage_1_fixed_support_field`
- Model quantity affected: Storage, theta = porosity * liquid_saturation, and effective thermal conductivity.
- Measurement evidence: NMR has 464 candidate water-content rows; the current field samples 83 OGS output times and uses 192 NMR rows in the state objective.  The default NMR policy remains retain_raw_absolute_theta_current_report_default_with_caveats, final policy selected=False, so porosity is still support, not an active unknown.
- Identifiability risk: Porosity trades directly against saturation in theta observations and against permeability in hydraulic response. NMR measures hydrogen-bearing water, not only mobile free water in the Richards saturation variable.
- Activation gate: Release as scalar or field only after the final NMR residual policy is approved, ERT/Taupe uncertainty gates are closed or excluded, and a sensitivity audit separates porosity from saturation and bound/interlayer-water effects.
- Source files: `ogs_settings/03_parameters_TRM.xml; GESA_model_original/projection_on_mesh_2025-09-05/03_parameters_TRM.xml; inversion_workflow/runs/regularized_ogs_candidate_001_length_0p025m/03_parameters_TRM.xml; inversion_workflow/measurement_likelihood_model.csv`

### 4. van Genuchten air-entry pressure

- OGS entry: `property saturation / p_b`
- Base definition: `SaturationVanGenuchten; p_b=10e6; residual_liquid_saturation=0.1; residual_gas_saturation=0; exponent=0.45`
- Projection/run definition: `fixed XML property in all prepared runs`
- Release stage: `stage_2_candidate_scalar`
- Model quantity affected: Capillary pressure-saturation relation, storage derivative dS/dp_c, and liquid saturation state.
- Measurement evidence: RH/Kelvin table has 4247 rows and NMR/ERT/Taupe provide theta diagnostics, but RH currently exposes a boundary-curve provenance mismatch rather than a clean retention likelihood; 8 external/provenance blockers remain open.
- Identifiability risk: Strongly correlated with open-niche pressure boundary, permeability, exponent, residual saturation, and porosity.
- Activation gate: Confirm or reconstruct 08_08_open_niche_seasonal.xml, select the NMR residual policy, and close or explicitly exclude ERT/Taupe/RH gates before fitting.
- Source files: `ogs_settings/04_2_media_twophase.xml; inversion_workflow/measurement_likelihood_model.csv`

### 5. van Genuchten exponent

- OGS entry: `properties saturation and relative_permeability / exponent`
- Base definition: `saturation: SaturationVanGenuchten; exponent=0.45; relative_permeability: RelativePermeabilityVanGenuchten; exponent=0.45`
- Projection/run definition: `fixed XML property in all prepared runs`
- Release stage: `stage_2_candidate_scalar`
- Model quantity affected: Shape of S(p_c) and k_rel(S), hence drying/wetting response around the open niche.
- Measurement evidence: NMR, ERT, Taupe/TDR, and RH are retention-sensitive, but they are still gated by NMR policy, ERT support/uncertainty, Taupe absolute calibration, and RH boundary-curve provenance.
- Identifiability risk: The exponent is poorly separated from p_b and residual saturation without independent retention or suction data.
- Activation gate: Release only as a paired retention calibration after the p_b, NMR-policy, and RH-provenance gates are satisfied.
- Source files: `ogs_settings/04_2_media_twophase.xml`

### 6. residual saturations

- OGS entry: `relative_permeability and saturation / residual_liquid_saturation, residual_gas_saturation`
- Base definition: `saturation: SaturationVanGenuchten; residual_liquid_saturation=0.1; residual_gas_saturation=0; relative_permeability: RelativePermeabilityVanGenuchten; residual_liquid_saturation=0.1; residual_gas_saturation=0`
- Projection/run definition: `fixed XML property in all prepared runs`
- Release stage: `stage_2_fixed_until_retention_data`
- Model quantity affected: Effective saturation, retention curve limits, and relative permeability endpoints.
- Measurement evidence: No active observation currently isolates residual saturation.
- Identifiability risk: Highly nonlinear and confounded with p_b, exponent, boundary pressure, NMR bound water, and sensor calibration.
- Activation gate: Require dedicated retention information or a sensitivity study proving state residuals can distinguish residual saturation.
- Source files: `ogs_settings/04_2_media_twophase.xml`

### 7. relative-permeability numerical floor

- OGS entry: `relative_permeability / minimum_relative_permeability_liquid`
- Base definition: `RelativePermeabilityVanGenuchten; minimum_relative_permeability_liquid=1e-25`
- Projection/run definition: `fixed XML property in all prepared runs`
- Release stage: `fixed_numerical_control`
- Model quantity affected: Minimum liquid mobility under very low liquid saturation.
- Measurement evidence: Current experiment evidence does not constrain the numerical lower bound.
- Identifiability risk: Changing it can alter solver behavior and dry-end mobility without clear observability.
- Activation gate: Only revisit in a numerical robustness study if very dry cells appear in OGS outputs.
- Source files: `ogs_settings/04_2_media_twophase.xml`

### 8. open-niche pressure boundary curve

- OGS entry: `parameter open_niche_seasonal / pressure_scaling_factor / open_niche_seasonal_curve`
- Base definition: `open_niche_seasonal: CurveScaled; curve=open_niche_seasonal_curve; base_parameter=pressure_scaling_factor; pressure_scaling_factor: Constant; 1.0`
- Projection/run definition: `same boundary parameter copied into prepared runs`
- Release stage: `blocked_or_confirm_provenance`
- Model quantity affected: Dirichlet pressure boundary on the open niche; drives pressure and saturation transients.
- Measurement evidence: RH audit compares RH-derived Kelvin pressures against the active OGS curve and finds a large mismatch over the overlapping time range.
- Identifiability risk: Boundary pressure can mimic permeability and retention changes, so fitting it blindly would contaminate material inference.
- Activation gate: Confirm how 08_08_open_niche_seasonal.xml was generated; then decide whether to fit only a documented scaling/bias term.
- Source files: `ogs_settings/03_parameters_TRM.xml; ogs_settings/08_08_open_niche_seasonal.xml; inversion_workflow/measurement_likelihood_model.csv`

### 9. orthotropic elasticity

- OGS entry: `parameters E, G, nu / LinearElasticOrthotropic`
- Base definition: `E: Constant; 13.80e+9 6.00e+9 13.80e+9; G: Constant; 4.79e+9 2.46e+9 4.79e+9; nu: Constant; 0.44 0.22 0.44`
- Projection/run definition: `fixed XML parameters in all prepared permeability runs`
- Release stage: `stage_3_candidate_mechanical`
- Model quantity affected: Stress-displacement response, pore-pressure coupling through volumetric strain, and swelling constraint.
- Measurement evidence: Other HM monitoring is structured as qualitative/secondary validation; key Geoscope and laser-scan numeric exports are still missing.
- Identifiability risk: The 2D model cannot uniquely explain full 3D deformation, crack, and scan observations; hydraulic changes can also alter pore-pressure-driven strain.
- Activation gate: Locate numeric HM time series, sample displacement/pressure OGS outputs, then run sensitivity checks before release.
- Source files: `ogs_settings/03_parameters_TRM.xml; inversion_workflow/processed_observations/other_hm_monitoring.md`

### 10. Biot coupling coefficient

- OGS entry: `medium property biot_coefficient -> parameter biot`
- Base definition: `Constant; 1`
- Projection/run definition: `fixed XML parameter in all prepared permeability runs`
- Release stage: `stage_3_candidate_mechanical`
- Model quantity affected: Effective stress coupling and pressure-strain coupling in the TRM process.
- Measurement evidence: No active numerical mechanical likelihood is available yet.
- Identifiability risk: Biot trades against elasticity, storage, initial stress, pressure boundary, and saturation state.
- Activation gate: Require active pressure/displacement residuals and mechanical calibration data before fitting.
- Source files: `ogs_settings/03_parameters_TRM.xml; ogs_settings/04_media_TRM.xml`

### 11. saturation-dependent swelling

- OGS entry: `solid property swelling_stress_rate / SaturationDependentSwelling`
- Base definition: `SaturationDependentSwelling; swelling_pressures=1.0E+06 1.0E+06 1.0E+06; exponents=1 1 1; lower_saturation_limit=0.1; upper_saturation_limit=1`
- Projection/run definition: `fixed XML property in all prepared permeability runs`
- Release stage: `stage_3_validation_only`
- Model quantity affected: Moisture-induced stress/strain source term and mechanical response to wetting.
- Measurement evidence: Levelling and qualitative HM evidence can screen implausible swelling response after OGS outputs exist.
- Identifiability risk: Swelling is entangled with saturation, elasticity, boundary constraints, and 2D geometry simplifications.
- Activation gate: Activate only after displacement outputs and numeric HM series support a mechanical likelihood.
- Source files: `ogs_settings/04_media_TRM.xml`

### 12. thermal and liquid transport constants

- OGS entry: `rho_s, kappa_th_s, c_p_s, c_p_l, kappa_l, eta, liquid density, thermal mixing`
- Base definition: `rho_s: Constant; 2.52e+3; kappa_th_s: Constant; 2.156; c_p_s: Constant; 1254.74; c_p_l: Constant; 4160; kappa_l: Constant; 0.6; eta: Constant; 1.0e-3; liquid density: Linear; reference_value=1095`
- Projection/run definition: `fixed XML parameters/properties in all prepared permeability runs`
- Release stage: `fixed_for_current_experiment`
- Model quantity affected: Heat storage/conduction, density/storage terms, and Darcy mobility through viscosity.
- Measurement evidence: No thermal perturbation likelihood or viscosity/density-specific measurement stream is active.
- Identifiability risk: Changes would be poorly observed and could compensate hydraulic parameters without physical support.
- Activation gate: Revisit only if a real thermal experiment or temperature-gradient likelihood is added.
- Source files: `ogs_settings/03_parameters_TRM.xml; ogs_settings/04_media_TRM.xml; ogs_settings/04_1_media_aqu_liq.xml; ogs_settings/04_2_media_twophase.xml`

### 13. solid thermal expansivity

- OGS entry: `solid property thermal_expansivity -> parameter CTE`
- Base definition: `Constant; 1254.74`
- Projection/run definition: `fixed XML parameter in all prepared permeability runs`
- Release stage: `blocked_or_confirm_value`
- Model quantity affected: Thermal strain and thermal pressurization terms if temperature changes occur.
- Measurement evidence: Current runs are near-isothermal; this is a model-provenance caveat rather than an active likelihood term.
- Identifiability risk: If thermal gradients appear, the current value could dominate THM coupling nonphysically.
- Activation gate: Do not release or physically interpret CTE until Gesa/BGR confirms whether the XML value should be near 1e-5 1/K, a different value, or inactive in the intended run.
- Source files: `ogs_settings/03_parameters_TRM.xml; ogs_settings/04_media_TRM.xml; inversion_workflow/thermal_expansivity_parameter_audit_summary.json`

### 14. initial pressure and stress setup

- OGS entry: `ic_pressure, ic_sigma0, bc_top_pressure, load_top`
- Base definition: `ic_pressure: Function; expression=1.5e6 - ((1095*(1 + 3.2e-10*(1.5e6 - 7.5e6))))*0*y; ic_sigma0: Function; expression=(-1.21e6) + 1*((1095*(1 + 3.2e-10*(1.5e6 - 7.5e6))))*0*y | (-7e6 + 1*1.5e6) + 1*((1095*(1 + 3.2e-10*(1.5e6 - 7.5e6))))*0*y | 0 | 0; bc_top_pressure: Function; expression=1.5e6 - ((1095*(1 + 3.2e-10*(1.5e6 - 7.5e6))))*0*50; load_top: Function; expression=(-7e6) + 1*((1095*(1 + 3.2e-10*(1.5e6 - 7.5e6))))*0*50`
- Projection/run definition: `same setup copied into prepared runs; load_top and initial stress remain model-provenance checks`
- Release stage: `fixed_model_setup_confirm_before_mechanics`
- Model quantity affected: Initial pore pressure, possible initial stress if activated, and top pressure/load boundary assumptions.
- Measurement evidence: Pressure/deformation monitoring can eventually test the initialization, but those residuals are not active now.
- Identifiability risk: Changing initial and boundary states can imitate permeability and storage effects over early times.
- Activation gate: Audit active process-variable references and numeric HM/pressure data before release.
- Source files: `ogs_settings/03_parameters_TRM.xml; ogs_settings/01_processes_TRM.xml; ogs_settings/02_process_variables_TRM.xml`

## Gate Checklist

- Stage 1 releases only k_i_rd magnitude fields against active direct permeability rows and sampled NMR state residuals.
- Porosity n_rd is field-capable but fixed until the final NMR residual policy and a porosity/saturation/bound-water separation audit are approved.
- Do not run more same-support active-objective OGS batches until support, likelihood, bounds, or stream gates change.
- Retention parameters require final NMR policy selection plus RH boundary-curve provenance before release.
- Mechanical, swelling, Biot, and initial-stress parameters require numeric HM/pressure residuals before release.
- CTE and open-niche pressure curve remain confirmation/provenance blockers, not calibration targets.

## Practical Consequence

The current inverse problem is not a free calibration of all XML constants.
It is a staged workflow: first fit a heterogeneous anisotropic permeability
field in `k_i_rd`; then use OGS state outputs to decide whether porosity,
retention, boundary, or mechanical parameters are identifiable enough to release.
