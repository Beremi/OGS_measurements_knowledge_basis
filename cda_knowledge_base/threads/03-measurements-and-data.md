# Measurements And Data

## ERT

ERT is the densest spatial data stream discussed. It measures resistance between sensor pairs, with around 2500 measurements per niche. Markus Furche explained, via Gesa, that raw values are difficult to use directly and BGR can instead provide evaluated values with coverage/accuracy at each point.

Available or referenced ERT data:

- `ERT_meas_Niche_open.zip` from TeamBeam.
- Daily VTK-style evaluated ERT data mentioned in the slides.
- Raw example from 1 September 2022:
  - `2022-09-01_02-00_open.ohm`
  - `2022-09-01_02-00_closed.ohm`
  - `2022-09-01_02-00-00.tx0`
  - `elecs_open.txt`
  - `elecs_closed.txt`

The `.tx0` file combines both niches. Gesa noted:

- #1-#2592: open niche;
- #2593-#5184: closed niche.

ERT caveats:

- reliability decreases with distance;
- reliable region is about 1.5 m radius and 35 cm into the rock;
- ERT mesh differs from FEM mesh;
- raw resistance values need post-processing before model comparison.

## ERT-Water Content Relation

Gesa sent `WC_vs_RHO_2025-02.xlsx` and `WC_vs_RHO_open-closed.pdf` in April 2025. The September 2025 slides later mention an open-twin Archie-style relation:

```text
y = 1.44 x^-1.51
```

The conversion from volumetric water content to saturation was written as:

```text
S = WC_vol / n
```

Use the relation cautiously. Gesa's later messages and 2026 minutes imply the evaluated ERT/water-content relation was still being refined.

## NMR

Stephan Costabel supplied direct NMR water-content data:

- `Weekly_2021-2022_at_4S.dat`
- `Weekly_2022-2025_at_4E.dat`
- `4S-4E-NMRmonitoring_until_Sep2025.png`
- `thunderbird_recovered/2025-09-15_saisonally.zip`

Weekly columns:

1. Time.
2. Water content in vol%.
3. 95% confidence interval for water content.
4. T2 relaxation time in ms.
5. 95% confidence interval for T2.

For modelling water content, Stephan said columns 4 and 5 can be ignored.

Known NMR issues:

- technical failures cause gaps;
- February-April 2025 detuned frequency caused about 1 vol% overestimation;
- seasonal files are date-coded by filename;
- seasonal columns are position, water content, and 95% confidence interval;
- before autumn 2021 only floor/ceiling measured;
- September 2020 only floor measured;
- winter 2024 is missing.

## Taupe / TDR

Gesa described Taupe measurements as post-processed apparent relative dielectric permittivity interpreted as water content or saturation.

Formula from the modelling slides:

```text
epsilon_r = epsilon_rock * (1 - phi) + epsilon_w * phi * S_w
```

where `epsilon_w` is approximately 80.

Gesa said BGR can provide mean amplitude of saturation change by distance intervals from the wall. Additional Taupe files are likely in `003_Nov_2025.zip`.

## Suction / Relative Humidity

Suction and relative-humidity data can be linked to saturation with:

- Kelvin equation;
- van Genuchten retention curve.

Measurements discussed:

- depths 40 cm and 70 cm;
- horizontal and vertical directions;
- open and closed niche comparisons.

The 2026 technical discussion minutes note ongoing sensor and logger/software issues. Thermo-hygrometers appear better for the open niche; psychrometers appear better for the closed niche.

## Permeability

Gmail attachments include:

- `CD-A_Permeability.xlsx`

TeamBeam later included:

- `Permeability_CDA_all_2025.xlsx`
- `Perm_Sec_4-3_Ziefle_et_al_2023_Characterization.pdf`

The February 2025 slides describe modified COMDRILL double-piston packer pulse tests:

- 10 cm interval;
- nitrogen;
- pressure up to 1 bar;
- intrinsic permeability estimated for a 3D volume around a 10 cm borehole interval;
- maximum error roughly half an order of magnitude;
- two measurements per direction every 10 cm interval;
- measurements repeated about 3 years apart.

The modelling conclusion from Gesa:

- anisotropy follows bedding-plane orientation;
- EDZ affects the near-field;
- heterogeneous permeability should generally be higher along bedding;
- permeability evolves/self-heals over time;
- start without time dependence and revisit later.

## Coordinates

Coordinate files:

- `Mess_Koord_XY.xlsx`
- `Mess_Koord_XY.jpg`

Use:

- `2D_Model (x/y)` columns for relevant 2D modelling.
- Ignore closed-twin coordinates for the current open-niche work unless the modelling scope changes.

Geometry caveat:

- ERT positions and NMR positions use different profiles, so positions may not lie on the exact same model surface.
