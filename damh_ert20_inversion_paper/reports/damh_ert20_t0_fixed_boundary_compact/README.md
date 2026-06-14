# DAMH ERT20 compact technical report

Self-contained LaTeX report bundle for the fixed open-niche-boundary DAMH ERT20 run `damh_ert20_t0_fixed_boundary_deep_su_until_20260614_0800_v1`.

Included files:

- `DAMH_ERT20_COMPACT_TECHNICAL_REPORT.tex`: LaTeX source.
- `DAMH_ERT20_COMPACT_TECHNICAL_REPORT.pdf`: compiled report.
- `figures/`: image assets referenced by the LaTeX source.

Build from this folder with:

```bash
pdflatex -interaction=nonstopmode -halt-on-error DAMH_ERT20_COMPACT_TECHNICAL_REPORT.tex
pdflatex -interaction=nonstopmode -halt-on-error DAMH_ERT20_COMPACT_TECHNICAL_REPORT.tex
```

Raw sampler, residual, and posterior data products are intentionally not included in this repository bundle.
