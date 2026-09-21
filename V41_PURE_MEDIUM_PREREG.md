# BPC v0.41 pure residual-medium phase-one preregistration

This protocol is committed before the first full experiment. It is a
development test of world prediction, not evidence of goal behavior or AGI.

## Fixed experience and holdout

- Training seed `241010`: 120 independently generated worlds from each of the
  three separate physical regimes, 24 uniformly random actions per world.
- Holdout generator seed `241110`: 24 causally joint, independently generated
  worlds; four random streams of 24 actions per world.
- The model receives only 64 anonymous bytes, an action integer 0–3, and the
  real next 64 bytes. Byte 63 bit 0 is the minimal open/closed boundary.
- No successful path, task family, object identity, distance, BFS answer,
  factor, event label, score or evaluation observation is written to the model.

## Fixed medium and controls

The candidate is a `2^20`-cell probability medium with four uniform physical
stencils. Every bit/location/action query addresses that same medium; real next
bits perform saturating Beta writeback. Its capacity cannot grow with maps.
All four anonymous actions can be measured from one unchanged state without an
autoregressive output loop. Action regions are exchangeable: consistently
renaming action channels must only rename the corresponding predictions.

Controls are: the identical medium with action removed, the trained candidate
queried with action channels rotated, copy-current-observation, and an untrained
half-probability medium. All prediction conditions receive the same holdout.

## Fixed gates

Adopt phase one only if all hold:

1. training and holdout initial worlds are disjoint;
2. at least 10% of holdout local `(action, 3x3 bytes)` contexts are unseen in
   training;
3. defined-bit Brier probability residual is at most `0.020` overall;
4. changed-bit Brier is at most `0.50` and below copy-current observation;
5. on changed bits and novel-context changed bits, the candidate improves on
   both action-removed and rotated-action controls by at least 10% relative;
6. fixed medium capacity is unchanged, active cells are reported, and the
   number of training raw states exceeds active cells divided by 64;
7. evaluation performs zero writes and leaves every digest unchanged;
8. the full unit-test suite passes.
9. the action-renaming equivariance and fixed typed probability-output tests
   pass without fitting an action-specific correction.

No gate will be weakened after reading results. A pass authorizes only an
independently committed frozen reproduction plus a second, non-Sokoban physical
world using the same core. It does not authorize a general-intelligence claim.

classifier.dev `jev-1.13.0` was used only for development-route triage. The
medium, controls and evaluator do not call it.
