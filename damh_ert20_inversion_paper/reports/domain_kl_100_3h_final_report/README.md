# Domain-KL 100-mode 3h final report

Self-contained LaTeX report bundle for `ert10_support_365d_domain_kl_100_3h_native_s1_v1`.

Included files:

- `domain_kl_100_3h_final_report.tex`: LaTeX source.
- `domain_kl_100_3h_final_report.pdf`: compiled report.
- `figures/`: image assets referenced by the LaTeX source.
- `tables/domain_kl_100_3h_scalar_parameter_posterior_summary.tex`: small LaTeX table used by the report.

Build from this folder with:

```bash
pdflatex -interaction=nonstopmode -halt-on-error domain_kl_100_3h_final_report.tex
pdflatex -interaction=nonstopmode -halt-on-error domain_kl_100_3h_final_report.tex
```

Raw campaign CSV and JSON outputs are intentionally not included in this repository bundle.
