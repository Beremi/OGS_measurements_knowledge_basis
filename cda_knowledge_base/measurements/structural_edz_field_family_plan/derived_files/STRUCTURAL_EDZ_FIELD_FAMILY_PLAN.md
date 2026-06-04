# Structural/EDZ Field-Family Screen

This artifact screens a different permeability-field family after the active production sampler pause.
It applies geometry-shaped log10 permeability multipliers to the current run-local tensor field,
preserving tensor orientation and anisotropy ratio while testing central EDZ, bedding-band,
and open-twin corridor magnitude patterns.

The score is the direct permeability pulse-test layer only. No OGS run is executed here,
and the frozen source model is not modified.

## Evidence

- Active/current run: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Input mesh: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/current_permeability_field/current_best_bulk_w_projections.vtu`
- Candidate fields screened: 234
- Shape families: bedding_parallel_band, central_edz_cap_decay, central_edz_shell, open_twin_broad_corridor, open_twin_depth_decay_corridor
- Active direct objective: 269.818057
- Active weighted RMSE log10: 1.610715
- Improving direct-screen candidates: 0
- Activation gate: Run-local direct screen only. Execute the batch with the OGS candidate harness only if best_direct_delta_vs_active is below the materiality threshold and the modelling decision explicitly accepts structural/EDZ probing as the next family.

## Best Direct Structural Candidate

- Candidate: `struct_bedding_parallel_band_bed_om0p75_w0p25_a0p5`
- Family: `bedding_parallel_band`
- Shape: `bed_om0p75_w0p25`
- Log10 amplitude: 0.500
- Direct objective: 269.818057
- Delta versus active: +0.000000
- Weighted RMSE log10: 1.610715

## Top Screened Fields

| Rank | Candidate | Family | Amplitude | Objective | Delta | RMSE | Target cells |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `struct_bedding_parallel_band_bed_om0p75_w0p25_a0p5` | `bedding_parallel_band` | 0.50 | 269.818 | +0.000 | 1.611 | 1 |
| 2 | `struct_bedding_parallel_band_bed_om0p75_w0p25_a1` | `bedding_parallel_band` | 1.00 | 269.818 | +0.000 | 1.611 | 1 |
| 3 | `struct_bedding_parallel_band_bed_om0p75_w0p25_a1p5` | `bedding_parallel_band` | 1.50 | 269.818 | +0.000 | 1.611 | 1 |
| 4 | `struct_bedding_parallel_band_bed_om0p75_w0p25_a2` | `bedding_parallel_band` | 2.00 | 269.818 | +0.000 | 1.611 | 1 |
| 5 | `struct_bedding_parallel_band_bed_om0p75_w0p25_am0p5` | `bedding_parallel_band` | -0.50 | 269.818 | +0.000 | 1.611 | 1 |
| 6 | `struct_bedding_parallel_band_bed_om0p75_w0p25_am1` | `bedding_parallel_band` | -1.00 | 269.818 | +0.000 | 1.611 | 1 |
| 7 | `struct_bedding_parallel_band_bed_o0_w0p25_a0p5` | `bedding_parallel_band` | 0.50 | 269.818 | +0.000 | 1.611 | 17 |
| 8 | `struct_bedding_parallel_band_bed_o0_w0p25_am0p5` | `bedding_parallel_band` | -0.50 | 269.818 | +0.000 | 1.611 | 17 |
| 9 | `struct_bedding_parallel_band_bed_om0p75_w0p5_a0p5` | `bedding_parallel_band` | 0.50 | 269.818 | +0.000 | 1.611 | 26 |
| 10 | `struct_bedding_parallel_band_bed_om0p75_w0p5_am0p5` | `bedding_parallel_band` | -0.50 | 269.818 | +0.000 | 1.611 | 26 |
| 11 | `struct_bedding_parallel_band_bed_o0_w0p25_am1` | `bedding_parallel_band` | -1.00 | 269.818 | +0.000 | 1.611 | 17 |
| 12 | `struct_bedding_parallel_band_bed_o0_w0p25_a1` | `bedding_parallel_band` | 1.00 | 269.818 | +0.000 | 1.611 | 17 |

## Proposed Diagnostic Batch

The proposed screened batch is `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/runs/structural_edz_field_family_plan/next_structural_edz_candidate_batch.csv`.

| Batch rank | Candidate | Family | Objective | Delta | Recommended action |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `struct_central_edz_shell_shell_r0p85_w0p15_a0p5` | `central_edz_shell` | 269.821 | +0.003 | do_not_run_for_active_objective_without_new_modelling_decision |
| 2 | `struct_bedding_parallel_band_bed_o0_w0p25_a0p5` | `bedding_parallel_band` | 269.818 | +0.000 | do_not_run_for_active_objective_without_new_modelling_decision |
| 3 | `struct_central_edz_cap_decay_cap_r1p15_d0p2_a0p5` | `central_edz_cap_decay` | 270.312 | +0.494 | do_not_run_for_active_objective_without_new_modelling_decision |

## Interpretation

No structural/EDZ candidate improves the direct permeability screen. The generated top meshes are useful as documented diagnostic probes, but they do not justify more active-objective OGS runs before measurement-stream gates or a different parameterization are addressed.

## Notes

- Central EDZ shapes use the same approximate 1.5 m centre-support convention already documented for the ERT support screen.
- Bedding-band shapes use the current report's bedding/anisotropy angle of 144 degrees.
- Open-twin corridor shapes use mapped BCD-A32 and BCD-A33 borehole line samples, not individual residual-derived anchor coefficients.
- Full direct-objective rankings include neutral geometry perturbations when they do not intersect active pulse-test support cells; the proposed batch prefers rows that perturb active target cells.
- Candidate meshes are run-local VTU files under this plan directory and should only be passed to OGS after the activation gate is accepted.
