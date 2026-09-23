# BPC v0.48 independent frozen reproduction

The v0.48 development run passed every gate fixed in
`V48_ALIGNED_BOUNDARY_PREREG.md`.  One independent reproduction is therefore
authorized with no change to the core, camera, controls, thresholds, training
size or holdout size.

- training seed: `482010` (150 new rotation orbits);
- holdout seed: `482110` (128 new rotation orbits);
- all v0.45, v0.46 and v0.48 development worlds are excluded;
- every gate from development remains fixed, including at least 70% aggregate
  strict closure selection, at least 60% per orientation, and at least a
  30-point lead over every control;
- the complete unit suite passes before the first and only frozen execution;
- no debugging, rerun, threshold change or seed replacement is allowed after
  reading the result.

Passing this reproduction establishes only reproducible one-step coupling of
an external one-bit closure boundary through the unchanged BPC medium.  It is
not an internal-state zero/flip result and not long-process generalization.
