# Cross-Stream Candidate Scorecard

This folder is a derived catalogue view, not a raw measurement stream.  It links the
current run-level diagnostics for the measurement streams that can already be
evaluated against executed OGS candidates:

- active direct permeability plus raw NMR theta objective,
- NMR bias/anomaly alternatives for the bound/interlayer-water caveat,
- provisional ERT log-resistivity residuals, and
- Taupe/TDR baseline-normalized trend residuals.

The source raw and processed files remain in the measurement-specific folders.  The
derived files here are copied from `SOTA_OGS_Mont_Terri_work/inversion_workflow/` by
`build_cross_stream_candidate_scorecard.py` so the measurement catalogue has a local
index of the candidate-level cross-stream evidence.

Current derived files:

- `derived_files/cross_stream_candidate_scorecard.csv`: run-level joined scorecard.
- `derived_files/cross_stream_candidate_scorecard_summary.json`: machine-readable
  stream winners, rank correlations, Pareto counts, and gate statement.
- `derived_files/cross_stream_candidate_scorecard.md`: human-readable summary and
  top/Pareto candidate tables.

Current interpretation:

- 66 executed runs are common to NMR, ERT, and Taupe diagnostics.
- No candidate is top-10 in every stream.
- The active incumbent is not the cross-stream mean-rank winner.
- The scorecard is diagnostic only and does not activate gated measurement streams
  in the likelihood.
