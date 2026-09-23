# BPC v0.48 aligned minimal-boundary preregistration

v0.48 re-runs the one-step closure experiment only after correcting the camera
geometry discovered in v0.47.  The BPC medium, capacity, probability update and
port-interference mechanism are unchanged.  This is a development experiment;
the fixed result decides whether one independent frozen reproduction is
authorized.

Protocol fixed before the first execution:

- camera: the v0.47 physical 8x8 row-aligned byte field;
- experience: 150 fresh rotation orbits (600 worlds, four reset actions each);
- holdout: 128 fresh rotation orbits (512 worlds), disjoint from every v0.45,
  v0.46 and v0.48 training world;
- fixed seeds: training `481010`, holdout `481110`;
- candidate: unchanged v0.45 port-interference medium;
- controls: action removed, port pathway absent, action rotated, state shifted,
  physical carrier removed at query time, spatial condition channel zeroed at
  query time, and probability readout polarity flipped;
- all evaluation calls are read-only and model digests must remain unchanged.

Fixed adoption gates:

1. all source hashes match and all rotation orbits are balanced and disjoint;
2. at least 10% of held-out action/context pairs are unseen;
3. strict closure selection is at least 70% overall and 60% in every physical
   orientation;
4. one-bit port Brier is at most 0.120 and median probability margin exceeds
   0.05;
5. selection beats every causal/control condition by at least 30 points;
6. ordinary non-port world prediction Brier is at most 0.030 and no more than
   10% worse than the unchanged local medium;
7. fixed-capacity compression and zero-write evaluation checks pass;
8. the complete unit suite passes before execution.

A development pass authorizes exactly one new frozen run with new seeds.  It
does **not** establish recurrent internal state, zero/flip ablation of such a
state, long-process closure, planning, general Sokoban solving, or AGI.
