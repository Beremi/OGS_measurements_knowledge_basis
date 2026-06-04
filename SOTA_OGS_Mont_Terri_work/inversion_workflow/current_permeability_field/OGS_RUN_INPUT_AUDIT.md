# OGS Run Input Audit

- Run directory: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Project file: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/cd_a_open_niche_quad.prj`
- Status: `run_inputs_ogs_accepted_with_meshio_submesh_warnings`

## Checks

| Check | Severity | Result |
| --- | --- | --- |
| project_mesh_files_exist | ok | all project mesh files exist |
| process_variable_mesh_references | ok | all process-variable mesh references are in the project mesh list |
| required_output_variables | ok | required observation-output variables are requested |
| projected_bulk_mesh_fields | ok | bulk_w_projections.vtu contains required k_i_rd and n_rd cell fields |
| meshio_readability | warning | meshio cannot decode: bulk_all.vtu, cd-a_niche4.vtu, cd-a_left.vtu, cd-a_right.vtu, cd-a_top.vtu, cd-a_bottom.vtu |
| vtu_header_integrity | ok | all VTU XML headers expose point/cell counts and DataArray declarations |
| submesh_bulk_id_arrays | ok | all boundary/support submeshes expose bulk_node_ids and bulk_element_ids in their VTU headers |
| ogs_execution_acceptance | ok | recorded OGS execution accepted the project inputs with returncode 0 |

## Meshes

| Mesh | Header points | Header cells | Header arrays | meshio readable | Error |
| --- | ---: | ---: | --- | --- | --- |
| `bulk_w_projections.vtu` | 20873 | 10239 | Points, connectivity, offsets, types, MaterialIDs, k_i_rd, k_mag_rd, k_anisotropy_ratio_rd, k_theta_deg_rd, n_rd, k_smooth_requested_log10_multiplier_rd, k_smooth_applied_log10_multiplier_rd, k_smooth_kernel_weight_sum_rd, k_smooth_nearest_anchor_distance_m_rd, k_local_basis_requested_log10_increment_rd, k_local_basis_applied_log10_increment_rd, k_local_basis_weight_sum_rd, k_local_basis_nearest_anchor_distance_m_rd | True |  |
| `bulk_all.vtu` | 20873 | 10239 | bulk_node_ids, MaterialIDs, bulk_element_ids, Points, connectivity, offsets, types | False | Error: Incorrect padding |
| `cd-a_niche4.vtu` | 630 | 315 | bulk_node_ids, bulk_element_ids, Points, connectivity, offsets, types | False | Error: Incorrect padding |
| `cd-a_left.vtu` | 41 | 20 | bulk_node_ids, bulk_element_ids, Points, connectivity, offsets, types | False | Error: Invalid base64-encoded string: number of data characters (913) cannot be 1 more than a multiple of 4 |
| `cd-a_right.vtu` | 41 | 20 | bulk_node_ids, bulk_element_ids, Points, connectivity, offsets, types | False | Error: Invalid base64-encoded string: number of data characters (913) cannot be 1 more than a multiple of 4 |
| `cd-a_top.vtu` | 41 | 20 | bulk_node_ids, bulk_element_ids, Points, connectivity, offsets, types | False | Error: Invalid base64-encoded string: number of data characters (913) cannot be 1 more than a multiple of 4 |
| `cd-a_bottom.vtu` | 41 | 20 | bulk_node_ids, bulk_element_ids, Points, connectivity, offsets, types | False | Error: Invalid base64-encoded string: number of data characters (913) cannot be 1 more than a multiple of 4 |

## Interpretation

- The primary projected bulk mesh must be readable and contain `k_i_rd` and
  `n_rd` cell fields before a candidate can be evaluated.
- Boundary/support VTU files are present, referenced, and header-checked for
  point/cell counts plus OGS bulk id arrays. If those files fail `meshio`
  decoding, downstream Python tooling should regenerate them with
  `identifySubdomains` before relying on `meshio` reads.
- This audit does not execute OGS. When an `OGS_EXECUTION_STATUS.json` file
  exists, the audit records whether the target OGS run accepted these inputs.

## OGS Execution Evidence

- Execution status file: `/home/ber0061/Repositories/gesa_mails/SOTA_OGS_Mont_Terri_work/inversion_workflow/runs/local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000/OGS_EXECUTION_STATUS.json`
- Return code: `0`
- Backend: `docker_apptainer_sif`
- SIF image: `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif`
