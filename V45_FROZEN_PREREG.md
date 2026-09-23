# BPC v0.45 independent frozen reproduction preregistration

This protocol is committed after the v0.45 development pass but before any
frozen model or prediction is observed. The core and development thresholds
remain unchanged.

- training seed `452010`: 600 balanced worlds and all four reset actions;
- holdout seed `452110`: 512 balanced worlds;
- every initial world must be disjoint from the generator pilot, development
  training, development holdout and the other frozen split;
- source hashes must remain exactly those in `V45_MINIMAL_BOUNDARY_PREREG.md`;
- the ten development gates remain unchanged;
- additionally, strict closure selection must reach at least 60% separately
  for each of the four closing-action orientations;
- the complete test suite must pass before the one frozen execution.

No rerun, seed replacement or threshold change is allowed. A pass freezes the
one-step minimal-boundary coupling only. It still does not establish recurrent
internal state, long-process behavior, Sokoban solving or AGI.
