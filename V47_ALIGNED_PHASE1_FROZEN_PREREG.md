# BPC v0.47 aligned phase-one frozen preregistration

The development pass authorizes exactly one independent reproduction. This
protocol is committed before that execution. No model, threshold or evaluator
change is allowed.

- training seed `247210`: 120 fresh worlds from each separate physical regime,
  24 random transitions each;
- holdout seed `247310`: 24 fresh joint-physics worlds, four independent
  24-step streams each;
- every initial world excludes all v0.41, v0.42, v0.42 frozen, v0.44 and v0.47
  development initials;
- all eleven v0.47 development gates remain byte-for-byte equivalent;
- all 87 unit tests must pass before the first execution.

Frozen hashes:

- `experiment_v47_aligned_phase1_dev.py`: `3c1acb7f13f93748eb65fb746ece6431ac71e8404a756f018bc944e0bc69b437`
- `bpc_aligned_canvas_v47.py`: `49a3c9bd98797a867641783f9659108254d98ff2fb85c38f62ba71f710606186`
- `bpc_compressed_medium_v44.py`: `db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6`
- `bpc_parallel_medium_v42.py`: `68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef`
- `bpc_pure_medium_v41.py`: `e1893081144c47f97191b4b82c9e5d7959774951e3f7bc05860c8d06fe1122cf`

A first-run pass establishes reproducible aligned one-step prediction on this
world family. It does not establish goals, planning, task success, transfer to
another domain, or AGI. A failure is retained and ends this branch.
