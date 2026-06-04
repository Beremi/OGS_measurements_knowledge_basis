# Historical Permeability Endpoint Geometry Request

This package converts the remaining historical permeability geometry gap into a
specific external-data request.  It does not infer or digitize endpoints by
itself, because the collected files only prove orientation and measurement
values for these rows, not label-resolved start/end coordinates.

## Current State

- Blocked segments: 5
- Blocked interpreted rows: 98
- Positive blocked rows: 98
- Activation status: `blocked_missing_labelled_endpoint_geometry` for every row listed here.

## Endpoint Request Table

| Segment | Block label | Rows | Depth range m | Direction | Twin | k range m2 | log10 k range | Requested endpoints |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| `BCD-A24` | BCDA_24 (vertical, 2021) | 30 | 0.15-3.3 | vertical |  | 5.000e-21-1.000e-13 | -20.301--13 | `BCD-A24 Anfang` / `BCD-A24 Ende` |
| `BCD-A25` | BCDA_25 (horizontal, 2021) | 30 | 0.15-3.3 | horizontal |  | 5.000e-22-1.000e-13 | -21.301--13 | `BCD-A25 Anfang` / `BCD-A25 Ende` |
| `BCD-A26` | BCDA_26 | 15 | 0.15-3.3 | vertical |  | 6.000e-21-6.000e-15 | -20.222--14.222 | `BCD-A26 Anfang` / `BCD-A26 Ende` |
| `BCD-A27` | BCDA_27 Closed twin | 15 | 0.15-3.3 | horizontal | closed | 1.000e-21-8.000e-17 | -21--16.097 | `BCD-A27 Anfang` / `BCD-A27 Ende` |
| `BFM-D19` | BFM-D19 Open twin | 8 | 0.7-1.7 | nearly horizontal | open | 1.010e-14-9.950e-13 | -13.996--12.002 | `BFM-D19 Anfang` / `BFM-D19 Ende` |

## What To Ask BGR/Gesa For

For each row in the table, request the following geometry metadata:

- For each borehole/trace: start/collar point x,y,z; end/tip point x,y,z; coordinate frame; depth-zero reference; positive along-borehole direction; whether workbook depth is interval centre or interval start; borehole diameter or packer interval length if it differs from 0.10 m; and coordinate uncertainty.
- If labelled coordinates are unavailable, provide an explicitly approved digitized trace from the original layout/figure, the source figure/file used, the digitization transform, and an uncertainty to apply to mapped interval locations.
- Confirm whether the listed workbook depth is measured from the borehole collar along the borehole trace.
- Confirm whether the 10 cm interval should be treated as centred on the reported depth, starting at the reported depth, or using another packer convention.
- For BFM-D19, confirm how the evapometer values/depths map to the BFM-D19 borehole trace and whether the `Evapometer` zone in `VisualisationCDA.dat` is the correct spatial support.

Email-ready text:

```text
Could you please provide labelled endpoint geometry for BCD-A24, BCD-A25, BCD-A26, BCD-A27, and BFM-D19 in the same local coordinate frame as the CD-A coordinate workbook / OGS projection?

For each trace we need start/collar and end/tip x,y,z coordinates, the depth-zero reference, the positive along-borehole direction, the convention for the reported permeability depth values, and an uncertainty estimate. If original coordinates are unavailable, an approved digitized trace with source figure/file and uncertainty would be sufficient for a gated model test.

The reason is that 98 interpreted permeability/evapometer rows are already extracted and orientation-classified, but they cannot be projected into OGS cells until these endpoints are labelled.
```

## Source Evidence Used

- `characterization_pdf`: Ziefle et al. characterization paper, Section 4.3 / PDF text around p. 7: pulse tests in BCD-A24 to BCD-A27; BCD-A24 and BCD-A26 vertical, BCD-A25 and BCD-A27 horizontal, and BFM-D19 nearly horizontal; pulse tests in March 2021 and evapometer measurements in June/July 2020.
- `workbook_probe`: Permeability_CDA_all_2025.xlsx sheet 2021 contains block labels for BCDA_24/25/26/27; 2025-09-05_CD-A_Permeability.xlsx sheet 2021_BCDA27_19 contains labels for BCDA_26, BCDA_27 Closed twin, and BFM-D19 Open twin. These workbook labels are measurement-table headings, not start/end coordinates.
- `visualisation_probe`: VisualisationCDA.dat contains generic zones Permeability_bhrg and Permeability_Meas_points, but the recovered zones do not attach unambiguous BCD-A24/25/26/27 or BFM-D19 start/end labels to the points.
- `available_geometry_reference`: The current coordinate/mesh line-sample layer has labelled endpoints for BCD-A32 to BCD-A35 and Taupe BCD-A3/A4/A7/A8, which proves the expected format, but not for BCD-A24/25/26/27 or BFM-D19.

## Why These Rows Stay Inactive

The active direct permeability operator samples a finite interval on a labelled
borehole trace and compares the workbook value to a log-space directional
intrinsic-permeability response.  Without labelled endpoints, the interval
centre and direction cannot be mapped to OGS cells.  Using the generic
`Permeability_bhrg` or `Permeability_Meas_points` Tecplot zones without a
label mapping would silently assign measurements to unsupported locations.

## Raw Value Files

- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/Permeability_CDA_all_2025.xlsx`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/2025-09-05_CD-A_Permeability.xlsx`
- `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements/permeability_pulse_tests/source_files/2025-09-05_Ziefle_et_al_2023_Characterization.pdf`

## Generated Files

- Request table: `inversion_workflow/processed_observations/permeability_endpoint_geometry_request.csv`
- Blocked-row table: `inversion_workflow/processed_observations/permeability_endpoint_geometry_blocked_rows.csv`
- Summary JSON: `inversion_workflow/processed_observations/permeability_endpoint_geometry_request_summary.json`
- This note: `inversion_workflow/processed_observations/permeability_endpoint_geometry_request.md`
