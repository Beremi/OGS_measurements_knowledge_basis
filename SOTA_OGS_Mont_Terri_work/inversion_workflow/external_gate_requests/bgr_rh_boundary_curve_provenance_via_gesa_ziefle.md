# Draft: CD-A RH/suction boundary-curve provenance needed for OGS forcing

Subject: CD-A RH/suction boundary-curve provenance needed for OGS forcing
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: none
Contact route: coordinator_only_processing_owner_unresolved
Contact evidence: Gesa sent the CD-A modelling slides, RH/suction material, and model-transfer threads that define the active boundary-curve context.
Contact caveat: The scan does not identify a separate RH/OGS pressure-curve processing owner, so Gesa remains the routing contact.

Dear Gesa,

The local RH-derived pressure curves do not reproduce the active XML pressure boundary, so we need the source/provenance before using RH as anything stronger than a boundary audit.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `rh_active_curve_provenance`

Request: Provide the provenance for the active open-niche pressure curve in 08_08_open_niche_seasonal.xml: source sensors, input sheets, scripts/notebooks, time-axis origin, smoothing/filtering, manual edits, Kelvin constants, sign convention, and open/closed curve mapping.

Minimum acceptance criteria: Original or intermediate table/script, sensor selection rule, model-time zero and timezone, RH percent/fraction convention, temperature/density constants, pressure unit/sign, extrapolation policy, and decision for post-active-curve dates.

Why this matters: RH/suction affects the OGS boundary forcing. The local RH-derived candidate envelope does not reproduce the active curve, so replacing or trusting the curve requires provenance.

Current local evidence/blocker: provenance request rows=6; active outside candidate envelope=575 Active boundary curve generation, sensor screening, time axis, constants, and extension policy are not confirmed.

Local artifacts we can share if useful: inversion_workflow/processed_observations/rh_boundary_candidate_curves.md; inversion_workflow/processed_observations/rh_boundary_uncertainty.md

Best,
