# Draft: CD-A ERT transform, support, and uncertainty needed for OGS comparison

Subject: CD-A ERT transform, support, and uncertainty needed for OGS comparison
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: Markus.Furche@bgr.de
Contact route: coordinator_with_named_provider_cc
Contact evidence: Gesa is the main CD-A sender; Markus.Furche@bgr.de is found in ERT and meeting-related messages and Gesa relayed Markus' ERT explanation in Gmail message 1994cb5d2bcefa24.
Contact caveat: No direct Gmail sender messages from Markus were found in the scan, so the request is routed through Gesa with Markus as suggested CC.

Dear Gesa, Markus,

We can already run a provisional ERT diagnostic against sampled OGS water-content outputs, but it should not become an inversion residual until the coordinate support and uncertainty model are confirmed.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `ert_transform_support`

Request: Confirm the coordinate frame of the ERT inversion VTK fields and electrode files, the exact transform into the local OGS 2D x/y frame, and the accepted near-niche support mask for model comparison. The current local operator assumes model_x = raw_x and model_y = raw_y + 500 and uses a provisional central support mask.

Minimum acceptance criteria: A written transform definition or script; coordinate-frame origin and axes; tunnel/niche contour or support polygon; accepted handling of the 35 cm rock-depth recommendation; and a decision on whether the current 1.5 m/radial support variants are acceptable or must be replaced.

Why this matters: ERT can only become a weighted log-resistivity residual if each inversion cell is placed on the same physical support as the OGS cells. The support-sensitivity audit shows that changing support can change candidate rankings.

Current local evidence/blocker: support variants=9; best mean support-rank run=broad_continuous_001_001_length_0p023m_shift_1p004; rank correlations vs default={'inner_annulus_1p15_1p30m': 0.4285714285714286, 'outer_annulus_1p30_1p50m': 0.6571428571428573, 'radius_le_1p25m': 0.4285714285714286, 'radius_le_1p2m': 0.6571428571428573, 'radius_le_1p35m': 0.48571428571428577, 'radius_le_1p3m': 0.4285714285714286, 'radius_le_1p45m': 1.0, 'radius_le_1p4m': 0.942857142857143} ERT-to-OGS transform and exact near-niche support mask remain assumed, not confirmed.

Local artifacts we can share if useful: inversion_workflow/processed_observations/ert_spatial_projection_operator.md; inversion_workflow/ert_support_sensitivity.md; cda_knowledge_base/measurements/ert/source_files/ERT_meas_Niche_open.zip

## `ert_uncertainty`

Request: Provide or approve an ERT inversion-field uncertainty and correlation model for log10 resistivity residuals: per-cell or region-level sigma, time correlation, spatial correlation/effective degrees of freedom, and any recommended filtering or aggregation before comparison to OGS theta-derived resistivity.

Minimum acceptance criteria: Either a covariance/error export or an agreed simplified weighting rule, including units/log base, independence assumptions, date grouping, and rules for unstable or fracture-dominated cells.

Why this matters: The archive has dense ERT fields, but VTK pixels cannot be treated as independent observations without over-weighting ERT relative to sparse NMR/permeability data.

Current local evidence/blocker: cross-run ERT MAE range=0.019635573360798686; no pixel/time covariance model is recorded No defensible ERT residual sigma/correlation model is available; pixels cannot be treated as independent rows.

Local artifacts we can share if useful: inversion_workflow/ert_candidate_discrimination.md; inversion_workflow/measurement_likelihood_model.md

Best,
