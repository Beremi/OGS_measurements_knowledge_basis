# Draft: CD-A Measurement Gate Closure Requests

Subject: CD-A modelling: files and confirmations needed for measurement-stream activation

Dear Gesa,

We have now catalogued the CD-A measurement files and built preliminary OGS comparison
operators. Before we can describe ERT, Taupe/TDR, RH/suction, and other HM monitoring
as hard residuals in the inversion objective, we need a few source confirmations and
numeric exports. The current inversion can only be described as direct permeability plus
conditional NMR, with the other streams used as diagnostics.

## BGR ERT provider / Markus Furche via Gesa Ziefle

- `ert_transform_support` (high): Confirm the coordinate frame of the ERT inversion VTK fields and electrode files, the exact transform into the local OGS 2D x/y frame, and the accepted near-niche support mask for model comparison. The current local operator assumes model_x = raw_x and model_y = raw_y + 500 and uses a provisional central support mask.
  Acceptance criteria: A written transform definition or script; coordinate-frame origin and axes; tunnel/niche contour or support polygon; accepted handling of the 35 cm rock-depth recommendation; and a decision on whether the current 1.5 m/radial support variants are acceptable or must be replaced.
  Why: ERT can only become a weighted log-resistivity residual if each inversion cell is placed on the same physical support as the OGS cells. The support-sensitivity audit shows that changing support can change candidate rankings.
- `ert_uncertainty` (high): Provide or approve an ERT inversion-field uncertainty and correlation model for log10 resistivity residuals: per-cell or region-level sigma, time correlation, spatial correlation/effective degrees of freedom, and any recommended filtering or aggregation before comparison to OGS theta-derived resistivity.
  Acceptance criteria: Either a covariance/error export or an agreed simplified weighting rule, including units/log base, independence assumptions, date grouping, and rules for unstable or fracture-dominated cells.
  Why: The archive has dense ERT fields, but VTK pixels cannot be treated as independent observations without over-weighting ERT relative to sparse NMR/permeability data.

## Gesa Ziefle / BGR Geoscope, laser-scan, and levelling source

- `hm_numeric_exports` (high): Provide hard-residual-ready numeric exports for Geoscope mini-piezometers, extensometers, crackmeters, the 2026-04-20 laser-scan statistical interpretation, and the full precision-levelling survey table.
  Acceptance criteria: Machine-readable tables with timestamps or survey epochs, instrument ids, measured values, units, coordinates/support ids, reference/zero conventions, calibration or processing provenance, quality/status flags, and uncertainty/covariance where available.
  Why: The local catalogue has layout geometry and qualitative HM statements, but no numeric time series or statistical exports that can be sampled against OGS pressure/displacement states.
- `hm_uncertainty` (high): For every provided other-HM export, include the metadata required for residual weights: units, epochs, coordinate/support geometry, reference conventions, uncertainty/covariance, quality flags, and failure/maintenance intervals.
  Acceptance criteria: Each table has self-contained units and reference conventions; failed sensors such as BCD-A9/B10 are flagged; laser registration uncertainty and masks are included; and levelling covariance/reference frame are documented.
  Why: Even if numeric values are found, they cannot become hard residuals without metadata that states what OGS quantity and support they measure.

## Gesa Ziefle / BGR RH or OGS boundary-curve source

- `rh_active_curve_provenance` (high): Provide the provenance for the active open-niche pressure curve in 08_08_open_niche_seasonal.xml: source sensors, input sheets, scripts/notebooks, time-axis origin, smoothing/filtering, manual edits, Kelvin constants, sign convention, and open/closed curve mapping.
  Acceptance criteria: Original or intermediate table/script, sensor selection rule, model-time zero and timezone, RH percent/fraction convention, temperature/density constants, pressure unit/sign, extrapolation policy, and decision for post-active-curve dates.
  Why: RH/suction affects the OGS boundary forcing. The local RH-derived candidate envelope does not reproduce the active curve, so replacing or trusting the curve requires provenance.

## Gesa Ziefle / BGR permeability source

- `perm_endpoint_geometry` (medium): Provide labelled endpoint geometry or approved digitized traces for the historical BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 permeability intervals that are currently retained but inactive.
  Acceptance criteria: For each interval: borehole id, open/closed assignment, start/end coordinates or depths with convention, orientation, interval length/support, date/source table, permeability value, and uncertainty/evaluation note.
  Why: These older rows cannot be projected to OGS cells until the measured 3D interval volume is known. They are useful because they broaden the permeability evidence outside the currently active mapped rows.

## Taupe/TDR provider via Gesa Ziefle

- `taupe_unit_calibration` (high): Confirm what the values in Taupe_WC.xlsx physically represent: calibrated volumetric water-content percent, relative dielectric permittivity, ARDP-derived proxy, or another quantity. Provide the sensor-specific calibration equations and uncertainty.
  Acceptance criteria: Workbook unit for every sheet/column; calibration equation and constants; whether values are already corrected for rock porosity/mineral matrix; uncertainty by sensor/band; baseline/reference date; and ARDP-to-water or dielectric conversion details.
  Why: The current workbook values pass some sanity checks if interpreted as water-content percent but fail if interpreted through a generic Topp permittivity conversion. Absolute Taupe residuals would be misleading without calibration.

I can send the current local audit tables if useful. The main point is to avoid
overstating a final all-measurement inversion before the support, calibration,
uncertainty, and provenance gates are closed.

Best,
