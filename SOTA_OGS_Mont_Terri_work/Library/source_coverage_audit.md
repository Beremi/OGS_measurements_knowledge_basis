# Source Coverage Audit

This audit records the source-tracking state for the current `main.tex` and
`measurement_chapter.tex` report sources.  It is a complement to `opalinus_clay.bib`
and `unavailable_fulltexts.md`; the bibliography remains authoritative for citation
metadata.

## Current Result

- Cited keys in the report: 29.
- Cited keys missing from `opalinus_clay.bib`: 0.
- Cited blocked/fulltext-unavailable keys missing from `unavailable_fulltexts.md`: 0.
- Local measurement-source PDFs cited by the report are copied into `Library/fulltexts`.
- Citation key instances audited for locators: 63.
- Citation instances missing page/section/equation/table or equivalent locator: 0.
- Citation fulltext classes from the locator audit: 56 local fulltexts, 5 official
  OGS web-documentation citations, and 2 unavailable-but-tracked fulltexts.

## Local Measurement Sources Added To The Bibliography

| Citation key | Local source | Library copy | Report use |
| --- | --- | --- | --- |
| `CDAModellingSlides2025` | `../cda_knowledge_base/measurements/ert/source_files/2025-09-05_CD-A_for_hermes_2D_250904x.pdf` | `fulltexts/Local_CD_A_for_HERMES_2D_250904x.pdf` | ERT inverse-problem questions, permeability pulse-test description, Taupe mixing expression, and projection workflow. |
| `NMR2026Local` | `../cda_knowledge_base/measurements/nmr/source_files/NMR2026.pdf` | `fulltexts/Local_NMR2026_CD_A.pdf` | NMR interlayer/bound-water caveat. |
| `TaupeISU2026Local` | `../cda_knowledge_base/measurements/taupe_tdr/source_files/2604_TD_CD-A_ISU.pdf` | `fulltexts/Local_Taupe_TD_CD_A_ISU_2026.pdf` | Differential TDR / TAUPE sensor-cable method identification. |
| `TDMinutes2026Local` | `../cda_knowledge_base/measurements/suction_relative_humidity/source_files/2026-05-11_TD517_CD-A_260507__Minutes.pdf` | `fulltexts/Local_TD517_CD_A_260507_Minutes.pdf` | RH/suction sensor-reliability split. |
| `BGRModellingTD2026Local` | `../cda_knowledge_base/measurements/other_hm_monitoring/source_files/CD-A_TD_2026_sc.pdf` | `fulltexts/Local_BGR_Modelling_TD_CDA_2026.pdf` | Other-HM future observation-operator priority and extensometer discrepancy caveat. |
| `LevellingTD2026Local` | `../cda_knowledge_base/measurements/other_hm_monitoring/source_files/Folien_Niv_TD_CDA_2026.pdf` | `fulltexts/Local_Precision_Levelling_TD_CDA_2026.pdf` | Other-HM numeric levelling displacement summary. |
| `InputHERMES2024Local` | `../cda_knowledge_base/measurements/other_hm_monitoring/source_files/2024-12-19_Input_HERMES_BGR_20241217.pdf` | `fulltexts/Input_HERMES_BGR_20241217.pdf` | Other HM monitoring inventory and validation-gate context. |

## Blocked Cited Fulltexts

The cited keys `Topp1980TDR` and `Kleinberg1996NMR` remain
intentionally tracked in `unavailable_fulltexts.md`.  The report cites them with
page locators where used.  Fresh publisher and metadata searches on 2026-05-31
verified the Wiley/AGU route for `Topp1980TDR` through DOI/CiNii metadata and the
ScienceDirect record for `Kleinberg1996NMR`, but fresh direct publisher-PDF
attempts still returned HTML blocker/landing pages, which are preserved in
`Library/fulltexts`.
The active NMR discussion now also cites the open-access `Cui2022DualScaleNMR`
fulltext for the clay/micro-porosity forward-modelling caveat.  The active
Taupe/TDR discussion now also cites the USDA-hosted `Robinson2003TDRReview`
fulltext for the dielectric-water-content calibration caveat.  `VanLoon2003`
remains listed there as a related
publisher-blocked journal article, but the active report now cites the locally
downloaded Nagra NTB 03-07 report (`VanLoon2004Nagra`) for that Mont Terri
diffusion/porosity context.  `Thomson1871Kelvin` and `ThermalEffectsOPA2010` were
previously blocked, but clean PDFs have now been downloaded from Zenodo and the UPC
open-access repository respectively.

The inactive tracked `Elsayed2020ClayNMR` source was also rechecked on
2026-05-31.  The ACS article page identifies it as open access, but automated PDF
retrieval still returned a Cloudflare blocker; the HTML blocker and a BibBase
metadata response are retained under `Library/fulltexts` for provenance.

## Recovered Fulltexts

| Citation key | Download source | Library copy |
| --- | --- | --- |
| `ThermalEffectsOPA2010` | UPC open-access repository record `https://upcommons.upc.edu/entities/publication/70c9bb30-f441-4652-8074-7de5aa282bf8` | `fulltexts/Gens_Vaunat_Garitte_Wileveau_2007_In_situ_behaviour_OPA.pdf` |
| `Cui2022DualScaleNMR` | Springer open-access article `https://link.springer.com/article/10.1007/s11242-022-01752-0` | `fulltexts/Cui_Shikhov_Arns_2022_NMR_Relaxation_Dual_Scale.pdf` |
| `Revil1998ShalySands` | Cornell-hosted JGR PDF `https://cpb-us-w2.wpmucdn.com/sites.coecis.cornell.edu/dist/f/396/files/2020/11/61-1998-Revil-et-al.-Electrical-conductivity-in-shaly-sands-with-geophy.pdf` | `fulltexts/Revil_et_al_1998_Electrical_Conductivity_Shaly_Sands.pdf` |
| `Robinson2003TDRReview` | USDA-ARS publication PDF `https://www.ars.usda.gov/arsuserfiles/20361500/pdf_pubs/P1889.pdf` | `fulltexts/Robinson_et_al_2003_TDR_Dielectric_EC_Review_USDA.pdf` |
| `Thomson1871Kelvin` | Zenodo record `https://zenodo.org/records/1742066` | `fulltexts/Thomson_1871_Equilibrium_Vapour_Curved_Surface.pdf` |
| `VanLoon2004Nagra` | Nagra open report PDF `https://nagra.ch/wp-content/uploads/2022/08/e_ntb03-007.pdf` | `fulltexts/Van_Loon_2004_Nagra_NTB_03_07_Diffusion_OPA.pdf` |

## Citation Locator Audit

The active report citations are audited in `citation_locator_audit.md`, with machine
tables in `citation_locator_audit.csv` and `citation_locator_audit_summary.json`.
The audit checks every `\cite` key instance in `main.tex` and
`measurement_chapter.tex` for a page range, PDF page, section, equation, table, or
named official-documentation section.  Current result: 63 citation key instances,
29 unique cited keys, zero missing or weak locators, zero missing BibTeX entries,
and zero unavailable fulltexts missing from `unavailable_fulltexts.md`; the fulltext
status counts are 56 local fulltexts, 5 official web-documentation citations, and 2
unavailable-but-tracked citation instances.

## Recheck Command

Run this from `SOTA_OGS_Mont_Terri_work` to verify the basic citation-key coverage:

```bash
/home/ber0061/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 - <<'PY'
from pathlib import Path
import re
tex = '\n'.join(Path(p).read_text(encoding='utf-8') for p in ['main.tex', 'measurement_chapter.tex'])
cited = sorted({key.strip() for match in re.finditer(r'\\cite(?:\[[^\]]*\])*\{([^}]+)\}', tex) for key in match.group(1).split(',')})
bib = Path('opalinus_clay.bib').read_text(encoding='utf-8')
bibkeys = set(re.findall(r'@\w+\{([^,]+),', bib))
missing = sorted(set(cited) - bibkeys)
print(f'cited keys: {len(cited)}')
print(f'missing bib entries: {missing}')
PY
```
