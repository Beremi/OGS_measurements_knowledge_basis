# DAMH ERT20 Free-t0 Global-Archie Run Synthesis

Generated: `2026-06-15T09:04:46+02:00`  
Campaign: `damh_ert20_t0_free_global_archie_su_until_20260615_0830_v1`

## Verdict

This run is a **failed sampler run with useful pre-crash exact OGS diagnostics**.

The requested parametrisation was applied: the ERT time shift was a free parameter, Archie parameters were fitted globally, and the open-niche boundary parameters were fixed. The run did not reach the planned stop at `2026-06-15 08:30 CEST`. It exited at `2026-06-14 22:59:45 CEST` with launcher `exit_code.txt = 139`.

The immediate Python error was:

```text
ValueError: cannot reshape array of size 640 into shape (20,33)
```

MPI then reported a segmentation fault during teardown. The failed evaluation appears to be `solver14_eval000003`: OGS itself finished with return code `0`, but post-processing produced only `640` ERT outputs, i.e. `20 x 32`, while the likelihood expected `660`, i.e. `20 x 33`.

## Main Artifacts

| Artifact | Path |
| --- | --- |
| Result directory | `/home/beremi/repos/gesa_mails/inversion_atempt/results/damh_ert20_t0_free_global_archie_surrogate/damh_ert20_t0_free_global_archie_su_until_20260615_0830_v1` |
| Launch directory | `/home/beremi/repos/gesa_mails/inversion_atempt/results/damh_ert20_t0_free_global_archie_surrogate_launch_logs/damh_ert20_t0_free_global_archie_su_until_20260615_0830_v1` |
| Manifest | `damh_manifest.json` |
| MPI stdout | `damh_mpi_stdout.log` |
| MPI stderr | `damh_mpi_stderr.log` |
| Exit code | `exit_code.txt` |
| Failed run directory | `/home/beremi/repos/gesa_mails/inversion_atempt/runs/damh_ert20_t0_free_global_archie_surrogate/damh_ert20_t0_free_global_archie_su_until_20260615_0830_v1/solver14_eval000003` |

## Configuration

| Item | Value |
| --- | ---: |
| MPI size | `16` |
| Feature count | `208` |
| Observation count expected by likelihood | `660` |
| ERT supports | `20` |
| ERT time points expected | `33` |
| Archie mode | `global` |
| Free t0 shift | `true` |
| t0 prior mean | `96.08167195600231` days |
| t0 prior std | `10.0` days |
| t0 prior bounds | `[66.08167195600231, 106.08167195600231]` days |
| t0 proposal sd | `2.0` days before multiplier, `1.8` after multiplier |
| Open-niche boundary fixed | `true` |
| Open-niche shift | `0.0` days |
| Open-niche suction scale | `1.0` |
| Open-niche suction offset | `0.0` MPa |
| DAMH requested evaluations | `1000000` |
| DAMH requested time limit | `35073` s |

Dataset: `/home/beremi/repos/gesa_mails/inversion_atempt/data/nn_pretraining/ert20_t0_free_global_archie_current/dataset_arrays.npz`  
Warm checkpoint: `/home/beremi/repos/gesa_mails/inversion_atempt/models/ert20_damh_t0_free_global_archie_seed/ert20_theta_mlp_warm.pt`

## Run Outcome

| Metric | Value |
| --- | ---: |
| Planned launch time | `2026-06-14T22:45:27+02:00` |
| Result manifest written | `2026-06-14T22:45:32+02:00` |
| First exact candidate summary | `2026-06-14T22:49:51+02:00` |
| Last exact candidate summary | `2026-06-14T22:59:38+02:00` |
| Launcher exit timestamp | `2026-06-14T22:59:45+02:00` |
| Launcher exit code | `139` |
| Clean `damh_finished` marker | absent |
| Exact candidate summaries | `44` |
| Candidate statuses | `44 evaluated` |
| OGS return codes for summarized candidates | `44 returncode 0` |
| OGS timeouts for summarized candidates | `0` |
| Failed candidate with OGS success but no summary | `solver14_eval000003` |
| surrDAMH raw/sample/accepted rows flushed | `1 / 1 / 1` |

Because only one surrDAMH sampling row was flushed, this run does **not** provide a meaningful posterior trace or accepted-sample ensemble. The reliable data products are the 44 exact OGS candidate summaries and their residual/Archie/theta files.

## Exact Candidate Diagnostics

All 44 summarized exact candidates used `archie_mode = global`, had `theta_output_count = 660`, and kept the fixed open-niche boundary values:

```text
open_niche_curve_shift_days = 0.0
open_niche_curve_suction_scale = 1.0
open_niche_curve_suction_offset_mpa = 0.0
```

| Quantity | Min | Median | Mean | Max |
| --- | ---: | ---: | ---: | ---: |
| Local Archie log likelihood | `49.1736` | `49.7161` | `49.7104` | `50.1971` |
| Local Archie MAE | `0.08243` | `0.08368` | `0.08376` | `0.08546` |
| Local Archie objective | `0.33679` | `0.34882` | `0.34896` | `0.36238` |
| Global Archie `log10(a)` | `1.05834` | `1.07766` | `1.07875` | `1.11161` |
| Global Archie exponent `b` | `-0.48113` | `-0.46530` | `-0.46284` | `-0.42675` |
| ERT t0 shift days | `89.6880` | `95.4619` | `95.4769` | `100.3196` |
| `k0_log10_k_m2` | `-21.2935` | `-20.9788` | `-20.9960` | `-20.5290` |
| Homogeneous porosity | `0.14018` | `0.14854` | `0.14798` | `0.15305` |
| Bedding angle deg | `138.7395` | `139.4510` | `139.4174` | `140.0752` |
| `q_22_over_11` | `0.43484` | `0.44953` | `0.45104` | `0.47322` |
| OGS duration s | `252.44` | `260.71` | `267.91` | `285.79` |
| Candidate wall time s | `253.36` | `261.62` | `268.86` | `286.80` |

The t0 shift was visibly active in the valid candidates: the exact candidates span roughly `89.69` to `100.32` days, centered near `95.48` days.

## Top Exact Candidates

Top candidates by exact-candidate local Archie log likelihood:

| Rank | Candidate | Log likelihood | MAE | t0 shift days | Global `log10(a)` | Global `b` |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `solver13_eval000003` | `50.197105` | `0.082541` | `91.463850` | `1.060321` | `-0.481130` |
| 2 | `solver09_eval000003` | `50.047850` | `0.082492` | `95.456776` | `1.067875` | `-0.470627` |
| 3 | `solver01_eval000003` | `50.043519` | `0.083309` | `89.687973` | `1.081020` | `-0.460855` |
| 4 | `solver01_eval000002` | `49.964777` | `0.083288` | `92.909363` | `1.073765` | `-0.467137` |
| 5 | `solver13_eval000002` | `49.964145` | `0.082861` | `93.989998` | `1.065788` | `-0.472344` |

For context, these best likelihood values are much lower than the completed fixed-boundary deep run's best value near `62.21`, so the pre-crash global-Archie/free-t0 run should be treated as a diagnostic failure run, not as an improved fit.

## Rank And Likelihood History

The rank-level Archie likelihood histories contain `4,140` rows, corresponding to `207` likelihood calls at 20 support rows per call. Every history row has `archie_mode = global`, confirming that the global-Archie code path was active throughout the recorded run.

Per-rank likelihood-call counts:

| Rank | Calls |
| ---: | ---: |
| 0 | `12` |
| 1 | `12` |
| 2 | `12` |
| 3 | `16` |
| 4 | `12` |
| 5 | `14` |
| 6 | `13` |
| 7 | `14` |
| 8 | `12` |
| 9 | `16` |
| 10 | `16` |
| 11 | `16` |
| 12 | `12` |
| 13 | `18` |
| 14 | `12` |

Rank 15 did not leave a likelihood-history file before the crash.

## Important Archie Spatial Note

The mesh-aligned radial Archie comparison is a key diagnostic artifact:

- Numbered mesh support map: `figures/11_ert20_supports_numbered_on_mesh.png`
- Figure: `figures/10_archie_radial_by_depth.png`
- Values: `archie_radial_by_depth_values.csv`

The strongest departure from the current global Archie pair is localized rather than domain-wide.
It is dominated by the shallower `15 cm` support trace, especially supports `3-5` in the previous
per-support fit. In the mesh-aligned coordinates these are supports `3`, `4`, and `5` at `108`,
`144`, and `180` degrees, i.e. the left/upper-left sector, not the bottom of the page. If a
field-view niche drawing is rotated relative to the mesh, translate this feature by support IDs
and angles rather than by page position. A plausible hypothesis is that shallow/surface electrical
current paths, contact effects, or near-boundary current leakage are locally breaking the simple
OGS-theta-plus-Archie ERT model. This is not proven by the plot alone, but future analysis should
test this explicitly before interpreting the global-Archie failure as only a hydraulic or porosity
field problem.

## Failure Analysis

The core failure was a mismatch between the expected ERT observation vector length and the vector returned by one candidate:

```text
expected: 20 supports x 33 times = 660
actual:   20 supports x 32 times = 640
```

The failed OGS run itself completed successfully (`solver14_eval000003`, OGS return code `0`). Therefore the problem is very likely in the ERT extraction/alignment step after OGS, probably when a free t0 perturbation moves one ERT measurement time outside the matched OGS output-time window or below the matching tolerance. The likelihood then tries to reshape the returned vector to the fixed observed-data shape `(20, 33)` and aborts.

## Scientific Use

Usable:

- The 44 evaluated exact candidate summaries.
- Confirmation that free t0 was sampled and recorded.
- Confirmation that global Archie fitting was applied.
- Confirmation that fixed open-niche boundary parameters remained fixed.
- Rough diagnostic distributions for t0, Archie parameters, and early candidate fit quality.

Not usable:

- Posterior samples from this run.
- Acceptance-rate diagnostics from this run.
- Long-run convergence diagnostics.
- A final surrogate-updated ensemble.
- Any morning-completion claim.

## Recommended Fix Before Relaunch

Before relaunching the overnight run, make the solver/likelihood contract robust to free t0 shifts:

1. Enforce that every candidate returns exactly `20 x 33 = 660` ERT values.
2. If a shifted ERT date cannot be matched, either interpolate to the nearest valid OGS interval or reject the candidate with `-inf` likelihood before calling `ArchieLSLikelihood.fit`.
3. Add an explicit guard in `get_observations` that checks `theta_flat.size == observed.size` and writes a failure summary instead of letting MPI crash.
4. Add a smoke test using t0 shifts near the prior bounds, especially around the upper/lower tails, to confirm no 32-time extraction can reach the likelihood.
