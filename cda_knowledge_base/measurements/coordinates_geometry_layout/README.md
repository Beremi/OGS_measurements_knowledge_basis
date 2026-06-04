# Coordinates / Geometry / Layout Information

This folder collects coordinate, layout, and geometry files needed to place CD-A measurements into the modelling frame. These files are not state measurements by themselves, but they are essential for using ERT, NMR, Taupe, suction, and permeability data correctly.

## Copied Source Files

- [2025-09-05_Mess_Koord_XY.xlsx](source_files/2025-09-05_Mess_Koord_XY.xlsx) - coordinate workbook shared in the September 2025 HERMES thread.
- [2025-09-05_Mess_Koord_XY.jpg](source_files/2025-09-05_Mess_Koord_XY.jpg) - coordinate/measurement-location image.
- [003_Nov_2025.zip](source_files/003_Nov_2025.zip) - original multi-measurement TeamBeam archive containing NMR/Taupe/characterization borehole coordinates and figures.
- [Coordinates_NMR_Taupe_characborehole.xlsx](source_files/Coordinates_NMR_Taupe_characborehole.xlsx) - NMR/Taupe/characterization borehole coordinate workbook extracted from `003_Nov_2025.zip`.
- [NMR_Taupe_Char_brg_1.png](source_files/NMR_Taupe_Char_brg_1.png), [NMR_Taupe_Char_brg_2.png](source_files/NMR_Taupe_Char_brg_2.png), [NMR_Taupe_Char_brg_3.png](source_files/NMR_Taupe_Char_brg_3.png) - borehole/location figures from `003_Nov_2025.zip`.
- [VisualisationCDA.dat](source_files/VisualisationCDA.dat) - Tecplot layout/visualization file from TeamBeam.

Original locations:

- [Gmail coordinate attachments](../../attachments)
- [TeamBeam additional measurements archive](../../file_transfers/collected/2025-11-07_additional_measurements/003_Nov_2025.zip)
- [TeamBeam December CD-A data folder](../../file_transfers/collected/2025-12-03_cda_data)

Detailed file-level extraction from this pass is in
[derived_files/deep_source_pass/source_file_deep_summary.md](derived_files/deep_source_pass/source_file_deep_summary.md),
including coordinate workbook summaries, Tecplot file headers, and ZIP member
checks.

## Coordinate Workbook: Mess_Koord_XY

`2025-09-05_Mess_Koord_XY.xlsx` contains one main sheet, `Tabelle1`, with 109 rows. It groups measurement points by type:

- NMR: 19 entries.
- Suction: 8 entries.
- Taupe: 8 entries.
- Permeability: 72 entries. The category text in the file is spelled `Permeablilty`.

The sheet contains coordinate blocks for:

- Original/3D model coordinates.
- `2D_Model (x/z)` coordinates.
- `2D_Model (x/y)` coordinates.

Email context says the relevant modelling coordinates for the requested use are the `2D_Model (x/y)` columns. Gesa also indicated that closed-twin coordinates can be ignored for the current modelling focus.

## Coordinate Workbook: NMR/Taupe/Characterization Boreholes

`Coordinates_NMR_Taupe_characborehole.xlsx` contains 37 labels with original coordinates and BGR model coordinates. Early labels include:

- `NMR_4R`
- `NMR_4Q`
- `NMR_4P`
- `NMR_O1`
- `NMR_O2`
- `NMR_4N`
- `NMR_4D`
- `NMR_5D`
- `NMR_4E`
- `NMR_4G`

The workbook is the main bridge between NMR/Taupe/characterization borehole labels and model coordinates.

## Tecplot Layout File

`VisualisationCDA.dat` is a Tecplot-style CD-A layout file. It is large and contains both geometry and labels. Parsed metadata:

- 84 zones.
- 95 text labels.
- Labels include Minipiezometer, Extensometer, Taupe, Miniprisma 1-12, Permeability, Evapometer, LTM 1/2, AGI 1, NMR, RH, EXT 1-3, open twin, closed twin, faults/fractures (`Kluft_0` through `Kluft_21`), convergence points, laser scan objects, permeability boreholes, permeability measurement points, Taupe positions, and NMR positions.

## Modelling Relevance

These files should be used before importing any measurement into OGS or an inversion workflow:

- Map point measurements to the same coordinate system as the mesh.
- Decide whether a coordinate belongs to the open or closed twin.
- Place NMR, Taupe, suction/RH, and permeability data at the correct borehole intervals or positions.
- Connect bedding/fault/structure labels to local anomalies in ERT, permeability, or water-content data.
- Check whether a plotted measurement is in 3D, `2D_Model (x/z)`, or `2D_Model (x/y)` coordinates before comparing with a 2D model.

The current workflow treats coordinates/layout as a support layer, not a likelihood
stream.  The processed lookup files under
[processed_observations](../../../SOTA_OGS_Mont_Terri_work/inversion_workflow/processed_observations/README.md)
carry the model-facing products: `measurement_coordinates_xy.csv`,
`borehole_coordinates.csv`, `measurement_mesh_lookup.csv`,
`borehole_mesh_lookup.csv`, and `borehole_line_mesh_samples.csv`.  Mapping status
must be propagated to downstream streams before a row becomes an active residual.

## Caveats

- Coordinate-system naming must be checked carefully; the workbook contains several coordinate blocks.
- For the HERMES 2D work discussed by email, use `2D_Model (x/y)` unless a later modelling decision overrides that.
- The Tecplot file is broad CD-A visualization material, not a clean measurement import table. It should be parsed deliberately before automated use.
