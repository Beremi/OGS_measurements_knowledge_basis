# Current Field Reproducibility Audit

This audit verifies that the packaged current permeability-field deliverable
contains enough local evidence to inspect and rerun the active-objective
incumbent without modifying the frozen source model.

- Status: `current_field_reproducibility_verified`
- Required failures: `0`
- Warning failures: `0`
- Package directory: `inversion_workflow/current_permeability_field`
- Run id: `local_basis_sampler_002_basis_024_det_l_0p0075_s_1p000`
- Manifest rows: `46`
- Run-input snapshot files: `25`

## Checks

| Check | Group | Severity | Status | Details |
| --- | --- | --- | --- | --- |
| `summary_exists` | `package` | `required` | `pass` | summary path exists=True |
| `package_status` | `package` | `required` | `pass` | status=current_permeability_field_package_generated |
| `markdown_exists` | `package` | `required` | `pass` | current field package markdown exists |
| `manifest_exists` | `manifest` | `required` | `pass` | manifest rows=46 |
| `manifest_row_count_matches_summary` | `manifest` | `required` | `pass` | csv rows=46, summary rows=46 |
| `manifest_hashes_verify` | `manifest` | `required` | `pass` | all manifest sizes and SHA256 values verify |
| `required_packaged_files_present` | `manifest` | `required` | `pass` | all required packaged evidence files are present |
| `run_input_snapshot_required_files` | `run_input_snapshot` | `required` | `pass` | snapshot files=25 |
| `project_references_resolve` | `run_input_snapshot` | `required` | `pass` | project refs=15 |
| `nested_includes_resolve` | `run_input_snapshot` | `required` | `pass` | all nested include files resolve |
| `combined_objective_components_sum` | `objective` | `required` | `pass` | component sum=3156.353066948979; total=3156.353066948979 |
| `expected_active_components` | `objective` | `required` | `pass` | active_component_count=2 |
| `direct_residual_rows_match_summary` | `objective` | `required` | `pass` | csv used rows=75; component used rows=75 |
| `state_residual_rows_match_summary` | `objective` | `required` | `pass` | csv used rows=192; component used rows=192 |
| `release_gate_passed` | `release_gate` | `required` | `pass` | status=pass; failures=0 |
| `ogs_execution_returncode_zero` | `ogs_execution` | `required` | `pass` | returncode=0 |
| `ogs_run_input_audit_accepts_inputs` | `run_input_snapshot` | `required` | `pass` | status=run_inputs_ogs_accepted_with_meshio_submesh_warnings; error checks=[] |
| `field_positive_definite` | `field` | `required` | `pass` | cells=10239; positive=10239; non_positive=0 |
| `fixed_porosity_support` | `field` | `required` | `pass` | n_rd min/max=0.105/0.105 |

## Interpretation

- A pass means the package can be treated as a reproducible active-objective
  incumbent: the field mesh, residual tables, OGS run inputs, execution status,
  and checksum manifest are internally consistent.
- This audit does not promote the field to a final all-measurement inversion
  result.  Stream gates and modelling-policy approvals remain separate.

## Key Evidence

- Active objective: `3156.353066948979`
- Direct rows: `75`
- State rows: `192`
- OGS return code: `0`
- Field cells: `10239`
- Positive-definite cells: `10239`
- Project file: `inversion_workflow/current_permeability_field/ogs_run_inputs/cd_a_open_niche_quad.prj`
- Project references checked: `15`
