# GeneralBPC v5 frozen cross-layout result

Status: **partial transfer, not adopted**.

The candidate learned only from raw 9×9×6 binary observations, anonymous actions,
uniform-random interaction, and actual episode outcomes. The runtime contains no
Sokoban solver, route search, object label, neural network, or evaluation-time
learning. An offline solver was used only to reject unsolvable generated maps.

| Frozen holdout condition | Successes | Rate |
|---|---:|---:|
| GeneralBPC v5 | 448 / 2560 | 17.50% |
| No three-group joint support | 396 / 2560 | 15.47% |
| No loop effect-equivalence death | 154 / 2560 | 6.02% |
| Action channels rotated | 34 / 2560 | 1.33% |
| Untrained uniform field | 60 / 2560 | 2.34% |

The learned field clearly beats the zero and action-binding controls, and removing
observed zero-net-effect loops causes a large drop. However, three of ten frozen
maps remain at zero success, aggregate success misses the predeclared 40% gate,
and the independent gain from the three-group support is only 2.03 percentage
points instead of the required 3 points. Only the loop-death and zero-write gates
passed.

The strongest supported statement is therefore: v5 shows limited, causal,
same-generator cross-layout transfer, but does not yet provide reliable Sokoban
generalization and is not a completed universal BPC.

The exact protocol is in `protocol_v5.json`; raw per-level outcomes, hashes,
controls, and evidence boundaries are in `artifacts/v5/result.json`.
