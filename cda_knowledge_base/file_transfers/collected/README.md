# Collected TeamBeam Files

This directory contains the TeamBeam transfer files collected from local and remote Downloads folders and verified against the SHA1 hashes from the TeamBeam notification emails.

## Folder Classification

| Folder | Transfer date | Contents | Source used for collection |
| --- | --- | --- | --- |
| `2025-04-03_ert_open_twin` | 2025-04-03 | Open-niche ERT measurement archive. | Local `/home/ber0061/Downloads`. |
| `2025-04-04_2d_model_container` | 2025-04-04 / 2025-04-11 | CD-A 2D model archive, OGS 6.5.4 Docker/Apptainer containers, README, Dockerfile. | Local `/home/ber0061/Downloads`. |
| `2025-05-09_updated_model` | 2025-05-09 | Faster/lower-output updated 2D CD-A model. | Local `/home/ber0061/Downloads`. |
| `2025-11-07_additional_measurements` | 2025-11-07 / 2025-11-14 | Additional measurements archive, likely Taupe, characterization boreholes, NMR positions, suction, and permeability context. | Local `/home/ber0061/Downloads`. |
| `2025-12-03_cda_data` | 2025-12-03 | Tecplot visualization data, updated permeability file, bedding-angle material, and characterization PDFs. | `ber0061@10.10.10.243:/home/ber0061/Downloads`. |

## Verification

Each collected file was checked with `sha1sum` against the SHA1 hash listed in `../teambeam_files.md`.

The remote machine also contained duplicates of earlier transfers. They were not copied again because the local copies already matched the expected SHA1 hashes. The remote ERT archive was named `ERT_meas_Niche_open (1).zip`, but matched the expected `ERT_meas_Niche_open.zip` hash.
