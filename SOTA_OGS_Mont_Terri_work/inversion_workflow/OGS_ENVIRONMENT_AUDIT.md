# OGS Environment Audit

This file records whether the local environment can execute the recovered
CD-A OGS model. It is an execution-readiness artifact; it does not modify
the GESA model or run OGS.

- Audit status: `ogs_container_found_runtime_available`
- `PATH` lookup: `not found`
- Executable candidates: 0
- Selected executable: `none`


## Container Candidates

| Path | Version label | Runnable now | Runtime blocker |
| --- | --- | --- | --- |
| `/home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/apptainer_ogs6.5.4.sif` | ogs/ogs@6.5.4 (cb5b3235101edecf3ba55e1039fe3c19bc13c636) | True |  |

Container runtime status:

- Preferred container backend: `docker_apptainer_sif`
- Preferred SIF runtime command: `/usr/bin/docker`
- Available native SIF runtimes: `{}`
- Docker path: `/usr/bin/docker`
- Dockerized Apptainer image: `ghcr.io/apptainer/apptainer:latest`

## Execution Backend

- Preferred backend: `docker_apptainer_sif`
- Runtime command: `/usr/bin/docker`
- Dockerized Apptainer image: `ghcr.io/apptainer/apptainer:latest`
- Run OGS through `run_ogs_model.py --sif ... --docker-apptainer-image ... --docker-workspace-root ...`.

## Search Scope

- Search directories: /usr/bin, /usr/local/bin, /opt, /home/ber0061
- Maximum search depth: 5
- Container search directories: /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/file_transfers/collected, /home/ber0061/Repositories/gesa_mails/cda_knowledge_base/measurements
- Container maximum search depth: 7

## Notes

- State-observation residuals remain inactive until OGS produces output
  VTU files that can be sampled at observation times and fields.
- Direct permeability residuals can still be evaluated from candidate
  mesh fields without executing OGS.
