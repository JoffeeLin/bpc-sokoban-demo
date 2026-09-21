# v0.42 frozen reproduction and cross-domain preregistration

This protocol is committed before either frozen result is observed. The core
is exactly `bpc_parallel_medium_v42.py` from development commit `efd74b3`; its
hash is recorded at runtime and it may not change during this test.

## Track A: independent Sokoban-physics reproduction

- training seed `243010`: 120 unique worlds in each of the same three separate
  regimes, with 24 uniform random actions per world;
- holdout seed `243110`: 24 joint-physics worlds, four streams and 24 uniform
  random actions per stream;
- all initial worlds are excluded from every v0.41 and v0.42 development
  training and holdout world;
- inputs remain 64 anonymous bytes, action 0–3 and real next bytes.

Track A uses the ten v0.42 development gates unchanged: at least 10% novel
contexts; all-bit Brier at most 0.020; changed-bit Brier at most 0.50 and below
copy; unseen-context changed-bit Brier at most 0.25; at least 10% improvement
over both action-removed and rotated-action controls on both changed subsets;
fixed capacity/compression; zero evaluation writes; disjoint worlds; all tests.

## Track B: independent particle-lattice physics

The same unmodified medium is trained from scratch on a different raw physical
world. An 8x8 byte lattice contains fixed barriers and anonymous mobile bits.
Each of four anonymous actions applies one global direction; all unblocked
mobile bits advance simultaneously by one cell. The model receives no names,
coordinates, force vector, object identity, simulator rule or reward.

- training seed `243020`: 120 unique lattices from each of three fixed
  wall/particle density regimes, 24 uniform random actions each;
- holdout seed `243120`: 24 unique lattices drawn from continuous unseen density
  combinations, four streams and 24 uniform random actions;
- training and holdout initial bytes must be disjoint;
- only the two physically defined input bits across all 64 cells are scored.

Track B uses the same metric gates as Track A, except that its overall defined-
bit Brier ceiling is 0.030. It must also keep the core hash identical to Track
A and use the same `2^20` capacity without domain-specific model parameters.

## Adoption boundary

The frozen milestone passes only if every gate in both tracks passes in the
first execution. No rerun, threshold change or core patch is allowed. A pass
would establish same-core, held-out local physical prediction in two domains.
It still would not establish goal-directed Sokoban behavior, cross-domain
weight transfer, or AGI, and therefore does not by itself authorize an X video
claiming game-solving generalization.
