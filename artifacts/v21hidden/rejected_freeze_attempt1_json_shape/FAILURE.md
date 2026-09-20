# Rejected frozen execution attempt 1

The run stopped before constructing or evaluating the holdout suite. Rebuilt
calibration values matched numerically, but the verifier compared native Python
tuples against arrays loaded from JSON. The assertion therefore failed on
container shape. The original protocol, holdout, freezer, and evaluator are
retained here. The repair normalizes the rebuilt object through JSON before the
same equality check; no seed, world, model, interface, threshold, or control was
changed.
