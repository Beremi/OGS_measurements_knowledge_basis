# External Gate Request Pack

This pack splits the external rows from the measurement gate-closure request package into recipient-specific drafts.
It is a request/tracking artifact only; it does not record that any request has been sent or answered.

## Summary

- Status: `external_gate_request_pack_generated_not_sent`
- External request rows: 7
- Recipient drafts: 5
- High-priority external requests: 6
- Medium-priority external requests: 1

## Recipient Drafts

| Recipient/audience | Requests | Draft |
| --- | --- | --- |
| BGR ERT provider / Markus Furche via Gesa Ziefle | `ert_transform_support`, `ert_uncertainty` | `inversion_workflow/external_gate_requests/bgr_ert_markus_furche_via_gesa_ziefle.md` |
| Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source | `hm_numeric_exports`, `hm_uncertainty` | `inversion_workflow/external_gate_requests/bgr_other_hm_exports_via_gesa_ziefle.md` |
| Gesa Ziefle / BGR RH or OGS boundary-curve source | `rh_active_curve_provenance` | `inversion_workflow/external_gate_requests/bgr_rh_boundary_curve_provenance_via_gesa_ziefle.md` |
| Taupe/TDR provider via Gesa Ziefle | `taupe_unit_calibration` | `inversion_workflow/external_gate_requests/taupe_tdr_calibration_via_gesa_ziefle.md` |
| Gesa Ziefle / BGR permeability source | `perm_endpoint_geometry` | `inversion_workflow/external_gate_requests/bgr_historical_permeability_geometry_via_gesa_ziefle.md` |

## Contact Routing

| Recipient/audience | Suggested To | Suggested Cc | Route status | Evidence/caveat |
| --- | --- | --- | --- | --- |
| BGR ERT provider / Markus Furche via Gesa Ziefle | `Gesa.Ziefle@bgr.de` | `Markus.Furche@bgr.de` | `coordinator_with_named_provider_cc` | Gesa is the main CD-A sender; Markus.Furche@bgr.de is found in ERT and meeting-related messages and Gesa relayed Markus' ERT explanation in Gmail message 1994cb5d2bcefa24. Caveat: No direct Gmail sender messages from Markus were found in the scan, so the request is routed through Gesa with Markus as suggested CC. |
| Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source | `Gesa.Ziefle@bgr.de` | none | `coordinator_only_specific_provider_unresolved` | Gesa is the main CD-A sender and sent the April 2026 technical-discussion minutes/presentations in Gmail message 19e1688564149e24; the current local scan does not identify a direct Geoscope, laser-scan, or levelling data owner address. Caveat: Ask Gesa to forward to the appropriate BGR Geoscope, laser-scan, and levelling data owners if she is not the source. |
| Gesa Ziefle / BGR RH or OGS boundary-curve source | `Gesa.Ziefle@bgr.de` | none | `coordinator_only_processing_owner_unresolved` | Gesa sent the CD-A modelling slides, RH/suction material, and model-transfer threads that define the active boundary-curve context. Caveat: The scan does not identify a separate RH/OGS pressure-curve processing owner, so Gesa remains the routing contact. |
| Taupe/TDR provider via Gesa Ziefle | `Gesa.Ziefle@bgr.de` | none | `coordinator_only_provider_unresolved` | Gesa's 2025-11-07 measurement overview says the TeamBeam transfer includes Taupe data and context, but the current scan does not identify a direct Taupe/TDR provider address. Caveat: Ask Gesa to forward to the Taupe/TDR provider or confirm the unit/calibration source directly. |
| Gesa Ziefle / BGR permeability source | `Gesa.Ziefle@bgr.de` | none | `coordinator_only_source_owner_unresolved` | Gesa sent permeability spreadsheets, characterization material, and the later updated permeability transfer; the local scan does not identify a direct historical pulse-test geometry owner address. Caveat: Ask Gesa to forward to the BGR permeability data owner if labelled interval endpoints come from another source. |

## Request Details

### `ert_transform_support`

- Priority: `high`
- Stream/gate: `ert_resistivity` / `ERT_TRANSFORM_SUPPORT` (`fail`)
- Request type: `support_geometry_and_transform`
- Requested answer or file: Confirm the coordinate frame of the ERT inversion VTK fields and electrode files, the exact transform into the local OGS 2D x/y frame, and the accepted near-niche support mask for model comparison. The current local operator assumes model_x = raw_x and model_y = raw_y + 500 and uses a provisional central support mask.
- Minimum acceptance criteria: A written transform definition or script; coordinate-frame origin and axes; tunnel/niche contour or support polygon; accepted handling of the 35 cm rock-depth recommendation; and a decision on whether the current 1.5 m/radial support variants are acceptable or must be replaced.
- Current evidence: support variants=9; best mean support-rank run=broad_continuous_001_001_length_0p023m_shift_1p004; rank correlations vs default={'inner_annulus_1p15_1p30m': 0.4285714285714286, 'outer_annulus_1p30_1p50m': 0.6571428571428573, 'radius_le_1p25m': 0.4285714285714286, 'radius_le_1p2m': 0.6571428571428573, 'radius_le_1p35m': 0.48571428571428577, 'radius_le_1p3m': 0.4285714285714286, 'radius_le_1p45m': 1.0, 'radius_le_1p4m': 0.942857142857143}
- Current blocker: ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.
- Why needed for the model: ERT can only become a weighted log-resistivity residual if each inversion cell is placed on the same physical support as the OGS cells. The support-sensitivity audit shows that changing support can change candidate rankings.
- Would unlock: Promote ERT from diagnostic field check to candidate active residual support.
- Local artifacts to share if useful: inversion_workflow/processed_observations/ert_spatial_projection_operator.md; inversion_workflow/ert_support_sensitivity.md; cda_knowledge_base/measurements/ert/source_files/ERT_meas_Niche_open.zip
- Related local request package: none

### `ert_uncertainty`

- Priority: `high`
- Stream/gate: `ert_resistivity` / `ERT_UNCERTAINTY` (`fail`)
- Request type: `uncertainty_model`
- Requested answer or file: Provide or approve an ERT inversion-field uncertainty and correlation model for log10 resistivity residuals: per-cell or region-level sigma, time correlation, spatial correlation/effective degrees of freedom, and any recommended filtering or aggregation before comparison to OGS theta-derived resistivity.
- Minimum acceptance criteria: Either a covariance/error export or an agreed simplified weighting rule, including units/log base, independence assumptions, date grouping, and rules for unstable or fracture-dominated cells.
- Current evidence: cross-run ERT MAE range=0.019635573360798686; no pixel/time covariance model is recorded
- Current blocker: No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.
- Why needed for the model: The archive has dense ERT fields, but VTK pixels cannot be treated as independent observations without over-weighting ERT relative to sparse NMR/permeability data.
- Would unlock: Defensible ERT likelihood weight or downweighted diagnostic residual.
- Local artifacts to share if useful: inversion_workflow/ert_candidate_discrimination.md; inversion_workflow/measurement_likelihood_model.md
- Related local request package: none

### `hm_numeric_exports`

- Priority: `high`
- Stream/gate: `other_hm_monitoring` / `HM_NUMERIC_EXPORTS` (`fail`)
- Request type: `source_file_request`
- Requested answer or file: Provide hard-residual-ready numeric exports for Geoscope mini-piezometers, extensometers, crackmeters, the 2026-04-20 laser-scan statistical interpretation, and the full precision-levelling survey table.
- Minimum acceptance criteria: Machine-readable tables with timestamps or survey epochs, instrument ids, measured values, units, coordinates/support ids, reference/zero conventions, calibration or processing provenance, quality/status flags, and uncertainty/covariance where available.
- Current evidence: hard-ready request classes=0; zip numeric-candidate members=0
- Current blocker: Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.
- Why needed for the model: The local catalogue has layout geometry and qualitative HM statements, but no numeric time series or statistical exports that can be sampled against OGS pressure/displacement states.
- Would unlock: Potential pressure/deformation/laser/levelling validation residuals.
- Local artifacts to share if useful: inversion_workflow/processed_observations/other_hm_numeric_source_audit.md; cda_knowledge_base/measurements/other_hm_monitoring/source_files/
- Related local request package: inversion_workflow/processed_observations/other_hm_missing_numeric_request.md

### `hm_uncertainty`

- Priority: `high`
- Stream/gate: `other_hm_monitoring` / `HM_UNCERTAINTY` (`fail`)
- Request type: `metadata_and_uncertainty_model`
- Requested answer or file: For every provided other-HM export, include the metadata required for residual weights: units, epochs, coordinate/support geometry, reference conventions, uncertainty/covariance, quality flags, and failure/maintenance intervals.
- Minimum acceptance criteria: Each table has self-contained units and reference conventions; failed sensors such as BCD-A9/B10 are flagged; laser registration uncertainty and masks are included; and levelling covariance/reference frame are documented.
- Current evidence: Do not assign hard HM residual weights until numeric exports include timestamps or survey epochs, units, support geometry, reference conventions, uncertainty/covariance, and quality/status flags.
- Current blocker: Required metadata for hard HM residual weights are absent from the current local bundle.
- Why needed for the model: Even if numeric values are found, they cannot become hard residuals without metadata that states what OGS quantity and support they measure.
- Would unlock: Defensible weights and activation gates for other-HM residuals.
- Local artifacts to share if useful: inversion_workflow/processed_observations/other_hm_missing_numeric_request.md; inversion_workflow/processed_observations/other_hm_numeric_source_audit.md
- Related local request package: inversion_workflow/processed_observations/other_hm_missing_numeric_request.md

### `rh_active_curve_provenance`

- Priority: `high`
- Stream/gate: `relative_humidity_suction` / `RH_ACTIVE_CURVE_PROVENANCE` (`fail`)
- Request type: `provenance_and_processing_files`
- Requested answer or file: Provide the provenance for the active open-niche pressure curve in 08_08_open_niche_seasonal.xml: source sensors, input sheets, scripts/notebooks, time-axis origin, smoothing/filtering, manual edits, Kelvin constants, sign convention, and open/closed curve mapping.
- Minimum acceptance criteria: Original or intermediate table/script, sensor selection rule, model-time zero and timezone, RH percent/fraction convention, temperature/density constants, pressure unit/sign, extrapolation policy, and decision for post-active-curve dates.
- Current evidence: provenance request rows=6; active outside candidate envelope=575
- Current blocker: Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.
- Why needed for the model: RH/suction affects the OGS boundary forcing. The local RH-derived candidate envelope does not reproduce the active curve, so replacing or trusting the curve requires provenance.
- Would unlock: Verified boundary forcing or a reproducible replacement curve.
- Local artifacts to share if useful: inversion_workflow/processed_observations/rh_boundary_candidate_curves.md; inversion_workflow/processed_observations/rh_boundary_uncertainty.md
- Related local request package: inversion_workflow/processed_observations/rh_boundary_provenance_request.md

### `taupe_unit_calibration`

- Priority: `high`
- Stream/gate: `taupe_tdr` / `TAUPE_UNIT_CALIBRATION` (`fail`)
- Request type: `calibration_confirmation`
- Requested answer or file: Confirm what the values in Taupe_WC.xlsx physically represent: calibrated volumetric water-content percent, relative dielectric permittivity, ARDP-derived proxy, or another quantity. Provide the sensor-specific calibration equations and uncertainty.
- Minimum acceptance criteria: Workbook unit for every sheet/column; calibration equation and constants; whether values are already corrected for rock porosity/mineral matrix; uncertainty by sensor/band; baseline/reference date; and ARDP-to-water or dielectric conversion details.
- Current evidence: absolute candidate conversions remain sanity checks; Topp physical rows are zero in current audit
- Current blocker: Taupe values are not confirmed as volumetric water-content percent, permittivity, or another ARDP-derived proxy.
- Why needed for the model: The current workbook values pass some sanity checks if interpreted as water-content percent but fail if interpreted through a generic Topp permittivity conversion. Absolute Taupe residuals would be misleading without calibration.
- Would unlock: Possible absolute Taupe water-content/saturation residual, or confirmed trend-only use.
- Local artifacts to share if useful: inversion_workflow/processed_observations/taupe_tdr_semantics.md; cda_knowledge_base/measurements/taupe_tdr/source_files/Taupe_WC.xlsx
- Related local request package: none

### `perm_endpoint_geometry`

- Priority: `medium`
- Stream/gate: `permeability_pulse_tests` / `PERM_SUPPORT` (`tracked_caveat`)
- Request type: `source_file_request`
- Requested answer or file: Provide labelled endpoint geometry or approved digitized traces for the historical BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 permeability intervals that are currently retained but inactive.
- Minimum acceptance criteria: For each interval: borehole id, open/closed assignment, start/end coordinates or depths with convention, orientation, interval length/support, date/source table, permeability value, and uncertainty/evaluation note.
- Current evidence: 98 older permeability rows are retained but inactive because labelled endpoint geometry is missing.
- Current blocker: Historical permeability endpoints are needed only if these older rows should enter the fit.
- Why needed for the model: These older rows cannot be projected to OGS cells until the measured 3D interval volume is known. They are useful because they broaden the permeability evidence outside the currently active mapped rows.
- Would unlock: Additional permeability pulse-test rows for direct parameter fitting.
- Local artifacts to share if useful: inversion_workflow/processed_observations/permeability_missing_geometry_audit.md
- Related local request package: inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md
