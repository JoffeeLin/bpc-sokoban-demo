# BPC v0.43 causal-lattice result

Status: **FAIL / NON-ADOPTED**. The first execution used preregistration commit
`7b2d570` and the unchanged v0.42 core hash
`68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef`.

## Strong but insufficient evidence

| Brier residual | Candidate | No action | Rotated action | Phase flipped | Copy | 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| all physical bits | 0.027824 | 0.024797 | 0.042070 | 0.358544 | 0.010435 | 0.250000 |
| changed bits | 0.042229 | 0.303081 | 0.799612 | 0.894178 | 1.000000 | 0.250000 |
| unseen-context changed bits | 0.042315 | 0.305401 | 0.798577 | 0.894153 | 1.000000 | 0.250000 |

The formal novelty rate was 57.68%, above the strengthened 25% gate. On
unseen-context changed bits the candidate improved over action removal by
86.14%, action rotation by 94.70%, and phase-flipped input by 95.27%. Thus the
terrain is causally used rather than serving as a random uniqueness channel.
Evaluation made zero writes and all digests were unchanged.

## Failed compression boundary

Eleven of twelve gates passed. The fixed-capacity compression gate failed:

- unique training raw states: 3,900;
- active medium cells: 649,450;
- active cells divided by 64: 10,147.66.

The full 3x3 context phase activates too many addresses even though the
parallel posterior resolver later gives many of those contexts little
influence. This is high-quality prediction backed by excessive context-table
occupancy, not the required compressed reusable physical law.

## Decision

Do not adopt or publish as a breakthrough. Do not add more transitions merely
to make the raw-state count exceed the existing table occupancy, and do not
weaken the gate. A next core must reduce high-cardinality memorization and then
repeat both physical domains with fresh preregistered evidence.
