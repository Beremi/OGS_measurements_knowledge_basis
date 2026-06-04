# Measurement Report Traceability Audit

This audit checks whether every manifest observation group is represented from
catalogued source files through the report chapter and workflow artifacts.

- Status: `measurement_report_traceability_audit_generated`
- Observations audited: 9
- Manifest validation checks: 28
- Manifest validation failures: 0
- Coverage rows: 9
- Traceability status counts: {'pass': 9}
- Data-content fact rows: 101
- Missing data-content summaries: 0
- Missing chapter sections: 0
- Missing inventory table references: 0
- Missing model-entry statements: 0
- Observations with missing expected artifacts: 0
- All observations traceable: `True`

## Observation Rows

| Observation | Folder | Status | Coverage | Source files | Content facts | Active rows | Missing items |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `ert_open_time_series` | `ert` | `pass` | `resistivity_diagnostic_generated_transform_support_unconfirmed` | 13 | 18 | 0 | none |
| `nmr_weekly_and_seasonal` | `nmr` | `pass` | `active_state_residual_from_sampled_ogs_outputs` | 54 | 9 | 192 | none |
| `permeability_pulse_tests` | `permeability_pulse_tests` | `pass` | `active_parameter_objective` | 5 | 21 | 75 | none |
| `taupe_tdr_edz_bands` | `taupe_tdr` | `pass` | `trend_operator_ready_absolute_calibration_pending` | 9 | 10 | 0 | none |
| `suction_relative_humidity_open_twin` | `suction_relative_humidity` | `pass` | `boundary_forcing_audited_not_point_residual` | 9 | 9 | 0 | none |
| `coordinates_and_geometry` | `coordinates_geometry_layout` | `pass` | `support_layer_ready` | 8 | 4 | 0 | none |
| `bedding_structure` | `bedding_geology_structure` | `pass` | `structural_prior_ready` | 4 | 4 | 0 | none |
| `model_projection_inputs` | `model_projection_inputs` | `pass` | `workflow_support_ready` | 87 | 14 | 0 | none |
| `other_hm_monitoring` | `other_hm_monitoring` | `pass` | `layout_and_qualitative_targets_ready_numeric_series_missing` | 10 | 12 | 0 | none |

## Interpretation

A passing traceability row is not the same as an active likelihood row. It means the
source catalogue, mined data-content summary, manifest validation, report coverage,
model-entry statement, and workflow artifacts are present. Activation gates remain governed by the likelihood,
stream-gate, external request, and response-intake audits.
