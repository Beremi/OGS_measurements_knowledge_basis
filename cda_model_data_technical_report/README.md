# CD-A OGS Model/Data Technical Report

This folder contains a standalone LaTeX technical report on the CD-A OGS TRM
model, available measurement streams, stochastic input choices, heterogeneity
feasibility, and the main audit findings.

- Source: `main.tex`
- Bibliography: `references.bib`
- Figures: `figures/`
- Figure generator: `scripts/build_measurement_setup_figures.py`
- Built PDF: `main.pdf`

Regenerate measurement setup figures:

```bash
python scripts/build_measurement_setup_figures.py
```

Build:

```bash
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```
