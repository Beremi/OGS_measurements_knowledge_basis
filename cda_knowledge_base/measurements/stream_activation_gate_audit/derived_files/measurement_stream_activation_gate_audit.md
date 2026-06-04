# Measurement Stream Activation Gate Audit

This audit is stricter than the measurement inventory. It records whether each
stream is active, conditional, diagnostic-only, or blocked from hard residual
weights by missing support, calibration, uncertainty, provenance, or numeric
source data.

## Summary

- Streams audited: 8
- Streams active now: 2
- Active objective rows: 267
- Streams not ready for hard residuals: 1
- Diagnostic/boundary-only streams: 3

## Stream Decisions

| Stream | Decision | Active rows | Gate counts | Blockers / caveats | Next action |
| --- | --- | ---: | --- | --- | --- |
| `nmr_water_content` | `active_with_tracked_caveats` | 192 | pass=1, warn=1, fail=0, missing=0 | Raw absolute theta residuals remain conditional until a free-water/bound-water correction or anomaly residual is accepted. | Keep active but conditional; decide whether final objective uses label-bias or trend/anomaly residual. |
| `permeability_pulse_tests` | `active_with_tracked_caveats` | 75 | pass=2, warn=1, fail=0, missing=0 | Gas/slip/liquid-equivalent interpretation remains a tracked model-error caveat. | Keep active; obtain endpoint geometry if older permeability rows should enter. |
| `geometry_support` | `support_layer_ready` | 0 | pass=1, warn=0, fail=0, missing=0 | none | Continue propagating mapping status; add missing historical endpoint geometry where needed. |
| `model_projection_inputs` | `support_layer_ready` | 0 | pass=1, warn=0, fail=0, missing=0 | none | Keep using release-gated run preparation; do not release later parameters until stream gates pass. |
| `ert_resistivity` | `diagnostic_only` | 0 | pass=1, warn=0, fail=2, missing=0 | ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.; No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows. | Confirm ERT-to-OGS transform, exact support mask, and inversion uncertainty/correlation before assigning weights. |
| `taupe_tdr` | `diagnostic_only` | 0 | pass=1, warn=2, fail=1, missing=0 | Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy. | Confirm Taupe workbook units/calibration and adopt a grouped uncertainty model; A7/A8 remain outside support. |
| `relative_humidity_suction` | `boundary_audit_only` | 0 | pass=1, warn=0, fail=2, missing=0 | Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.; Local RH-derived envelope is quantified but not accepted as replacement forcing or retention likelihood. | Get BGR/Gesa provenance for active open-niche pressure curve before replacement forcing or retention likelihood. |
| `other_hm_monitoring` | `not_ready_for_hard_residual` | 0 | pass=1, warn=0, fail=2, missing=0 | Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.; Required metadata for hard HM residual weights are absent from the current local bundle. | Locate Geoscope, laser-scan, and levelling numeric exports with epochs, units, support, and uncertainty. |

## Failed Or Warning Gates

| Stream | Gate | Status | Evidence | Blocker / caveat |
| --- | --- | --- | --- | --- |
| `ert_resistivity` | coordinate transform and exact support mask confirmed | `fail` | support variants=9; best mean support-rank run=broad_continuous_001_001_length_0p023m_shift_1p004; rank correlations vs default={'inner_annulus_1p15_1p30m': 0.4285714285714286, 'outer_annulus_1p30_1p50m': 0.6571428571428573, 'radius_le_1p25m': 0.4285714285714286, 'radius_le_1p2m': 0.6571428571428573, 'radius_le_1p35m': 0.48571428571428577, 'radius_le_1p3m': 0.4285714285714286, 'radius_le_1p45m': 1.0, 'radius_le_1p4m': 0.942857142857143} | ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed. |
| `ert_resistivity` | inversion-field uncertainty/correlation model assigned | `fail` | cross-run ERT MAE range=0.019635573360798686; no pixel/time covariance model is recorded | No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows. |
| `nmr_water_content` | bound/interlayer-water bias quantified | `warn` | bound-water usable-row required-offset p95=0.04017850052068304; bias audit runs=66; rank correlation=0.6351529067946979 | Raw absolute theta residuals remain conditional until a free-water/bound-water correction or anomaly residual is accepted. |
| `other_hm_monitoring` | hard-residual-ready numeric time series located | `fail` | hard-ready request classes=0; zip numeric-candidate members=0 | Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table. |
| `other_hm_monitoring` | units, epochs, reference conventions, uncertainty, and quality flags available | `fail` | Do not assign hard HM residual weights until numeric exports include timestamps or survey epochs, units, support geometry, reference conventions, uncertainty/covariance, and quality/status flags. | Required metadata for hard HM residual weights are absent from the current local bundle. |
| `permeability_pulse_tests` | broad gas-pulse model-error scale | `warn` | current evaluator uses sigma=0.5 log10 units and duplicate-aware weights | Gas/slip/liquid-equivalent interpretation remains a tracked model-error caveat. |
| `relative_humidity_suction` | active OGS pressure curve provenance confirmed | `fail` | provenance request rows=6; active outside candidate envelope=575 | Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed. |
| `relative_humidity_suction` | boundary/retention uncertainty model accepted | `fail` | envelope dates=1064; overlap pressure-range p50=2.103967930926996 | Local RH-derived envelope is quantified but not accepted as replacement forcing or retention likelihood. |
| `taupe_tdr` | series/group weighting and uncertainty model accepted | `warn` | series-weight runs=66; compared series=12; distinct per-series winners=8 | Series-specific uncertainty and grouped weighting remain part of the calibration gate. |
| `taupe_tdr` | all relevant Taupe sensors inside current mesh support | `warn` | uncompared/outside-support series=12 | A7/A8 remain outside the current Niche-4 mesh support. |
| `taupe_tdr` | Taupe workbook unit and absolute calibration confirmed | `fail` | absolute candidate conversions remain sanity checks; Topp physical rows are zero in current audit | Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy. |

## Interpretation

Only direct permeability and NMR currently provide active objective rows,
and NMR remains conditional on the bound/interlayer-water bias treatment.
ERT, Taupe/TDR, and RH have useful forward diagnostics, but their hard
likelihood promotion is blocked by transform/support/uncertainty,
unit/calibration/weighting, and boundary-provenance gates, respectively.
Other HM monitoring has support geometry and qualitative constraints but no
hard-residual-ready numeric exports.  This is why the current inversion
should not be described as a final all-measurement fit.
