# DAMH ERT20 Free-t0 Global-Archie Run Report

This directory is a lightweight report bundle copied from the nested
`inversion_atempt` run report. It intentionally contains only the report PDF,
LaTeX source, rendered figures, and small summary CSVs.

Raw candidate directories, rank likelihood histories, launch logs, model
checkpoints, datasets, and surrogate outputs are not included.

## Files

- `free_t0_global_archie_run_report.pdf`: final report generated from LaTeX.
- `free_t0_global_archie_run_report.tex`: report source.
- `RUN_SYNTHESIS_REPORT.md`: markdown synthesis of the run.
- `figures/`: rendered report figures.
- `archie_global_vs_previous_per_support_summary.csv`: comparison table for the
  global Archie pair against previous per-support Archie estimates.
- `archie_radial_by_depth_values.csv`: values used by the radial Archie plot.

## Important Diagnostic Note

The radial Archie plot and numbered mesh support map are the key figures in
this bundle:

- `figures/10_archie_radial_by_depth.png`
- `figures/11_ert20_supports_numbered_on_mesh.png`

The strongest departure from the current global Archie pair is localized in the
shallower `15 cm` measurements, especially supports `3-5` at `108`, `144`, and
`180` degrees. In the mesh-aligned coordinates these are in the left/upper-left
sector of the mesh, not the bottom of the page.

This could indicate a shallow or surface electrical-current effect, contact
effect, or near-boundary current leakage locally breaking the simple
OGS-theta-plus-Archie ERT model. That hypothesis is not proven by the plot, but
it should be carried forward before interpreting the failed global-Archie run
as only a hydraulic or porosity field problem.
