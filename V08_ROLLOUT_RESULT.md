# BPC v0.8: frozen multi-step cross-task rollout

## Result

**ADOPTED for open-loop prediction only.** The v0.7 fragment-chain world
function was recursively fed its own predictions under supplied random actions.
Training still contained `150,000` push-only and `150,000` collect-only
transitions, with zero joint local contexts.

Across two new frozen seeds, every fragment-chain trajectory was exact at every
horizon from 1 through 64 steps:

| Frozen condition at 64 steps | Seed 88108 | Seed 88208 | Combined |
|---|---:|---:|---:|
| Fragment-chain complete trajectories | **3,000 / 3,000** | **3,000 / 3,000** | **6,000 / 6,000** |
| Joint-mechanism trajectories | **839 / 839** | **842 / 842** | **1,681 / 1,681** |
| Condition deletion on joint trajectories | 548 / 839 | 533 / 842 | 1,081 / 1,681 |
| Full-context memory known | 0 / 839 | 0 / 842 | **0 / 1,681** |

The complete frozen ladder contained `762,000` recursively predicted steps.
Both 64-step source-family retention tests were `1,000 / 1,000`, the first
holdout repeated bit-for-bit, and evaluation performed zero model writes. All
ten pre-registered gates passed.

## Evidence

- Protocol: [`protocol_v08_rollout.json`](protocol_v08_rollout.json)
- Runner: [`experiment_v08_rollout_frozen.py`](experiment_v08_rollout_frozen.py)
- Result: [`artifacts/v08rollout/result.json`](artifacts/v08rollout/result.json)
- Result SHA-256:
  `54ae1aaed50e1456543b1f9e7097e5a388f8643c6dc851d75539d7f2a378f722`

The learned rollout function reconstructs the changed cells from model output
and is source-audited not to call the true transition function.

## Boundary

This is multi-step **open-loop prediction**, not a new action-selection
mechanism. Actions, raw channels, local window, global state container, task
generators, and evaluation remain supplied. Exact rollout does not by itself
establish planning, direct control, autonomous goal formation, or AGI.
