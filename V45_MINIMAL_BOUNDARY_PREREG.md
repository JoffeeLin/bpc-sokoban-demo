# BPC v0.45 minimal closure-boundary preregistration

This protocol is committed before the first model-level v0.45 result. The
generator-only pilot used discarded seeds `450001/450002`; it trained no model
and observed no prediction or action score.

## Fixed mechanism and boundary

The v0.44 compact local predictor is unchanged. v0.45 adds one task-independent
interface law: any byte with physical carrier bit 7 is a one-bit data port.
The port's data bit receives translation-shared evidence from every sensor
cell through the same fixed Beta medium and parallel action-posterior rule.
There is no goal name, coordinate, object parser, reward, value, reverse wave,
rollout, path enumeration or planner in the core.

Expected hashes:

- `bpc_port_interference_v45.py`: `27e9a2158fc9df3c3519c08d0d122b10aaa93e0d73c753cd39652e6ada49f85d`
- `bpc_compressed_medium_v44.py`: `db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6`

## Fresh experience

- training seed `451010`: 600 unique one-step closure worlds, exactly balanced
  across the four anonymous closing actions;
- every action is physically tried once from an independent reset of each
  state, yielding 2,400 real transitions; no solution path or preferred action
  is supplied to the model;
- holdout seed `451110`: 256 fresh balanced worlds, all disjoint from training
  and the discarded generator pilot;
- the model receives only 64 anonymous bytes, action 0–3 and real next bytes.

The only external behavior measurement chooses the action with the lowest
predicted next port bit. This is a one-step physical measurement, not a rollout.
Ties fail.

## Fixed controls and gates

Controls are the same port medium with action removed, the v0.44 local-only
medium, rotated action channels, and a shifted-state query from another
holdout world. The local next-state prediction of v0.45 is also compared with
the unchanged v0.44 core trained on identical transitions.

All gates must pass:

1. hashes and all world-disjointness/balance checks pass;
2. at least 10% of holdout full local contexts are unseen;
3. strict one-step closure selection is at least 70%;
4. port Brier over all four actions is at most 0.120;
5. selection exceeds action-removed, local-only, rotated-action and shifted-
   state controls by at least 30 percentage points each;
6. median correct-vs-best-other probability margin exceeds 0.05;
7. non-port next-state Brier is at most 0.030 and no more than 10% above the
   identically trained v0.44 local-only core;
8. unique raw states exceed active cells divided by 64 at fixed `2^20`
   capacity;
9. evaluation performs zero writes and leaves all digests unchanged;
10. fixed typed probabilities, exact action renaming and the complete unit
    suite pass before execution.

A pass establishes only the minimal one-step E coupling needed before second-
stage work. It does not satisfy the theory's internal-state ablation or third-
stage long-process requirements and is not Sokoban solving or AGI.
