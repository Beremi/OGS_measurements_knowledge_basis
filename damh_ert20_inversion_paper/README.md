# DAMH ERT20 inversion paper

This folder contains a compact paper-style report for campaign `damh_ert20_smu_until_20260612_0830_v1`.

Build:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

Main artifacts:

- `main.tex`: LaTeX source.
- `main.pdf`: compiled paper.
- `figures/`: paper-specific figures, written as both PDF and PNG.
- `tables/`: generated LaTeX tables.
- `reports/`: additional self-contained LaTeX report bundles with only PDFs,
  TeX sources, figures, and small LaTeX tables.

The report is generated from the saved campaign artifacts under:

`/home/beremi/repos/gesa_mails/inversion_atempt/results/damh_ert20_surrogate/damh_ert20_smu_until_20260612_0830_v1`

Additional report bundles:

- `reports/damh_ert20_t0_fixed_boundary_compact/`: fixed-boundary DAMH ERT20
  compact technical report with the aligned ERT/t0 boundary timing figure.
- `reports/domain_kl_100_3h_final_report/`: earlier 100-mode domain-KL
  three-hour campaign report.

Raw run products and report-generation scripts are intentionally not part of
this compact repository bundle.
