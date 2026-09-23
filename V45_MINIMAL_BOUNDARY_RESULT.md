# BPC v0.45 minimal closure-boundary development result

Status: **DEVELOPMENT PASS / NOT YET FROZEN**. The first run used preregistration
commit `068b7a1`; both source hashes matched and all 81 tests passed before
execution.

## Evidence

- 600 balanced training worlds, 2,400 real reset transitions;
- 256 disjoint balanced holdout worlds;
- 13.58% unseen full local contexts;
- strict one-step closure selection: **74.22%**;
- port Brier: **0.09784**;
- median correct-vs-best-other probability margin: **0.18233**;
- active medium cells: **14,652** at fixed `2^20` capacity;
- evaluation writes: zero, with every digest unchanged.

Selection controls were action removed 0%, local-only port 0%, rotated action
8.20%, and shifted state 10.94%. Non-port next-state Brier was 0.005030 versus
0.005002 for the identically trained v0.44 local-only core, satisfying the
world-prediction retention gate.

## Interpretation and boundary

An ordinary physical one-bit port can now receive action-dependent evidence
from translation-shared sensor patterns through the same probability medium.
The system is not given a correct action, solution path, reward, value, goal
coordinate, object role, rollout or planner. The external measurement only
chooses the action with the smallest predicted next port bit; ties fail.

All ten preregistered gates passed. This establishes a development-level
one-step closure coupling, not the supplied theory's full second-stage result:
there is no recurrent internal state to zero/flip/shift. It also does not
establish long-process behavior, Sokoban solving, or AGI. Independent frozen
reproduction is required before adoption.
