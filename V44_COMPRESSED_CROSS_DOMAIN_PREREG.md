# BPC v0.44 compressed cross-domain preregistration

This protocol is committed before any v0.44 formal result is observed. Old
v0.42/v0.43 data were used only to diagnose the mechanism; every formal initial
world is excluded from those data.

## Frozen core

v0.44 removes the high-cardinality exact 3x3 projection and retains the same
center, horizontal and vertical translation-shared stencils, parallel action
posteriors, Beta writeback, `2^20` capacity and action equivariance. It does not
add a selector, threshold, semantic field or domain-specific branch.

Expected hashes:

- `bpc_compressed_medium_v44.py`: `db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6`
- `bpc_parallel_medium_v42.py`: `68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef`
- `bpc_pure_medium_v41.py`: `e1893081144c47f97191b4b82c9e5d7959774951e3f7bc05860c8d06fe1122cf`

## Fresh tracks

Track A uses Sokoban physics: training seed `245010`, holdout seed `245110`,
the same 360 separate-regime training worlds and 24 joint-physics holdout worlds
with four streams. All initials must be disjoint from v0.41, v0.42 and its
frozen reproduction.

Track B uses causal terrain/particle physics: training seed `245020`, holdout
seed `245120`, the same 360 training lattices and 24 four-stream holdout
lattices. All initials must be disjoint from the generator pilot and v0.43.

## Fixed gates

Both tracks retain their prior probability and causal gates. Track A requires
at least 10% novel full contexts, overall Brier at most 0.020, changed Brier
below 0.25/copy/half, unseen-changed Brier at most 0.25, and at least 10%
improvement over action removal and rotation. Track B requires at least 25%
novel contexts, overall Brier at most 0.030, the same changed-bit limits and
action controls, plus at least 10% improvement over phase-flipped input on both
changed subsets.

For each track, raw-state count must exceed active cells divided by 64. Track A
may activate at most 33,343 cells, one quarter of the v0.42 frozen predecessor;
Track B may activate at most 162,362 cells, one quarter of v0.43. Evaluation
must make zero writes and preserve digests. All hashes and the complete unit
suite must pass.

The combined result passes only if every gate in both tracks passes on the
first execution. This would establish a compact same-core, fresh-weight
physical predictor in two domains. It would not establish goal behavior,
cross-domain weight transfer or AGI.
