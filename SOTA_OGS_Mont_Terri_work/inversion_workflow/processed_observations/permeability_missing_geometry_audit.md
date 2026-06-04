# Permeability Missing Geometry Audit

This audit keeps interpreted permeability rows that cannot yet be projected
onto the local OGS mesh visible, without converting them into unsupported cell
targets.

- Missing-geometry groups: 5
- Missing-geometry interpreted rows: 98
- Groups with source-backed orientation only: 5

| Segment | Block label | Rows | Depth range [m] | Direction evidence | Geometry status |
| --- | --- | ---: | --- | --- | --- |
| `BCD-A24` | BCDA_24 (vertical, 2021) | 30 | 0.15-3.30 | vertical | orientation_only_endpoint_geometry_missing |
| `BCD-A25` | BCDA_25 (horizontal, 2021) | 30 | 0.15-3.30 | horizontal | orientation_only_endpoint_geometry_missing |
| `BCD-A26` | BCDA_26 | 15 | 0.15-3.30 | vertical | orientation_only_endpoint_geometry_missing |
| `BCD-A27` | BCDA_27 Closed twin | 15 | 0.15-3.30 | horizontal | orientation_only_endpoint_geometry_missing |
| `BFM-D19` | BFM-D19 Open twin | 8 | 0.70-1.70 | nearly horizontal | orientation_only_endpoint_geometry_missing |

## Source Evidence

- The characterization paper states that BCD-A24 and BCD-A26 are vertical,
  BCD-A25 and BCD-A27 are horizontal, and BFM-D19 is nearly horizontal.
- The current coordinate workbook provides labelled endpoint geometry for
  BCD-A32 to BCD-A35, but not for BCD-A24 to BCD-A27 or BFM-D19.
- `VisualisationCDA.dat` contains permeability layout geometry, but the
  recovered Tecplot zones do not attach unambiguous BCD-A24/25/26/27 or
  BFM-D19 endpoint labels to the points, so they are not used for OGS
  residual mapping.

## Required To Activate These Rows

- Labelled start/end coordinates for BCD-A24, BCD-A25, BCD-A26, BCD-A27 and
  BFM-D19 in the same local frame as the OGS mesh, or
- an explicitly approved digitization of Figure 3 / Figure 7 geometry from
  the characterization paper with uncertainty assigned to the projected
  interval locations.
