# Draft: CD-A historical permeability endpoint geometry needed for inactive intervals

Subject: CD-A historical permeability endpoint geometry needed for inactive intervals
Suggested To: Gesa.Ziefle@bgr.de
Suggested Cc: none
Contact route: coordinator_only_source_owner_unresolved
Contact evidence: Gesa sent permeability spreadsheets, characterization material, and the later updated permeability transfer; the local scan does not identify a direct historical pulse-test geometry owner address.
Contact caveat: Ask Gesa to forward to the BGR permeability data owner if labelled interval endpoints come from another source.

Dear Gesa,

The current direct permeability objective uses only rows with mapped interval support. The older retained rows need endpoint geometry before they can be projected to OGS cells.

Could you please help with the items below? These are the minimum pieces we need before we can describe the corresponding stream as a defensible hard residual in the CD-A OGS inversion workflow.

## `perm_endpoint_geometry`

Request: Provide labelled endpoint geometry or approved digitized traces for the historical BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 permeability intervals that are currently retained but inactive.

Minimum acceptance criteria: For each interval: borehole id, open/closed assignment, start/end coordinates or depths with convention, orientation, interval length/support, date/source table, permeability value, and uncertainty/evaluation note.

Why this matters: These older rows cannot be projected to OGS cells until the measured 3D interval volume is known. They are useful because they broaden the permeability evidence outside the currently active mapped rows.

Current local evidence/blocker: 98 older permeability rows are retained but inactive because labelled endpoint geometry is missing. Historical permeability endpoints are needed only if these older rows should enter the fit.

Local artifacts we can share if useful: inversion_workflow/processed_observations/permeability_missing_geometry_audit.md

Best,
