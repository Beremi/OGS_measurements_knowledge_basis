# Draft: CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation

Subject: CD-A Geoscope, laser-scan, and levelling numeric exports needed for model validation
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: none
Contact route: coordinator_only_specific_provider_unresolved
Contact evidence: Gesa is the main CD-A sender and sent the April 2026 technical-discussion minutes/presentations in Gmail message 19e1688564149e24; the current local scan does not identify a direct Geoscope, laser-scan, or levelling data owner address.
Contact caveat: Ask Gesa to forward to the appropriate BGR Geoscope, laser-scan, and levelling data owners if she is not the source.

Dear Gesa,

The local catalogue contains HM layout geometry and qualitative evidence, but no hard-residual-ready numeric time series or statistical exports for these streams.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `hm_numeric_exports`

Request: Provide hard-residual-ready numeric exports for Geoscope mini-piezometers, extensometers, crackmeters, the 2026-04-20 laser-scan statistical interpretation, and the full precision-levelling survey table.

Minimum acceptance criteria: Machine-readable tables with timestamps or survey epochs, instrument ids, measured values, units, coordinates/support ids, reference/zero conventions, calibration or processing provenance, quality/status flags, and uncertainty/covariance where available.

Why this matters: The local catalogue has layout geometry and qualitative HM statements, but no numeric time series or statistical exports that can be sampled against OGS pressure/displacement states.

Current local evidence/blocker: hard-ready request classes=0; zip numeric-candidate members=0 Local source scan found layout geometry, laser surface geometry, extracted levelling slide rows, and report/minute evidence, but no hard-residual-ready Geoscope time series, laser statistical interpretation product, or full levelling survey table.

Local artifacts we can share if useful: inversion_workflow/processed_observations/other_hm_numeric_source_audit.md; cda_knowledge_base/measurements/other_hm_monitoring/source_files/

## `hm_uncertainty`

Request: For every provided other-HM export, include the metadata required for residual weights: units, epochs, coordinate/support geometry, reference conventions, uncertainty/covariance, quality flags, and failure/maintenance intervals.

Minimum acceptance criteria: Each table has self-contained units and reference conventions; failed sensors such as BCD-A9/B10 are flagged; laser registration uncertainty and masks are included; and levelling covariance/reference frame are documented.

Why this matters: Even if numeric values are found, they cannot become hard residuals without metadata that states what OGS quantity and support they measure.

Current local evidence/blocker: Do not assign hard HM residual weights until numeric exports include timestamps or survey epochs, units, support geometry, reference conventions, uncertainty/covariance, and quality/status flags. Required metadata for hard HM residual weights are absent from the current local bundle.

Local artifacts we can share if useful: inversion_workflow/processed_observations/other_hm_missing_numeric_request.md; inversion_workflow/processed_observations/other_hm_numeric_source_audit.md

Best,
