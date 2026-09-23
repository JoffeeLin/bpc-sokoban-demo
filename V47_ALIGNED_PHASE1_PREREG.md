# BPC v0.47 aligned phase-one preregistration

This protocol is committed before the first v0.47 result. v0.47 preserves the
historical camera unchanged for auditability and introduces a new camera that
maps board coordinate `(x,y)` to byte `y*8+x`. Column 7 and row 7 are explicit
carrier padding; byte 63 remains the one-bit physical closure port.

## Fixed development run

- core: unchanged v0.44 compressed probability medium;
- training seed `247010`: 120 fresh worlds from each of the three separate
  physical regimes, 24 random transitions each;
- holdout seed `247110`: 24 fresh joint-physics worlds, four independent
  24-step streams each;
- all initial worlds exclude the v0.41, v0.42, its frozen reproduction, and
  v0.44 Sokoban runs;
- complete unit suite, including coordinate, padding, physical-neighbor and
  rotation tests, must pass before execution.

Frozen source hashes:

- `bpc_aligned_canvas_v47.py`: `49a3c9bd98797a867641783f9659108254d98ff2fb85c38f62ba71f710606186`
- `bpc_compressed_medium_v44.py`: `db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6`
- `bpc_parallel_medium_v42.py`: `68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef`
- `bpc_pure_medium_v41.py`: `e1893081144c47f97191b4b82c9e5d7959774951e3f7bc05860c8d06fe1122cf`

## Gates fixed before execution

At least 10% of full 3x3 action contexts must be unseen. Overall defined-bit
Brier must be at most 0.020. Changed-bit Brier must be below 0.25, copy and
0.5; unseen-changed Brier must be at most 0.25. On changed and unseen-changed
bits, candidate must improve by at least 10% over both action removal and an
action rotation. Raw-state count must exceed active cells divided by 64 and
active occupancy must not exceed the v0.44 ceiling of 33,343. Evaluation must
make zero writes and preserve both model digests. Every frozen source hash must
match this preregistration.

A pass authorizes one separately preregistered, fresh-seed reproduction. It is
evidence only for aligned one-step world prediction, not goal behavior,
Sokoban solving, cross-domain transfer, or AGI.
