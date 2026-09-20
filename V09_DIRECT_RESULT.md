# BPC v0.9: frozen direct task composition

## Result

**ADOPTED for the bounded claim below.** Two BPC policies learned independently:

- `2,000` push-only episodes with no marks;
- `2,000` collect-only episodes with no movable objects.

No combined task entered training. At inference, their four-way `Choice`
probabilities were multiplied equally and normalized. The resulting policy
directly sampled actions without a runtime planner, search, distance function,
or evaluation-time learning.

The frozen holdout contains 16 new worlds. Every world is solvable with true
push dynamics and unsolvable when boxes are fixed, so collection necessarily
requires the unseen task combination.

| Frozen 32-step condition | Successes | Rate |
|---|---:|---:|
| Independent probability product | **942 / 2,048** | **46.0%** |
| Collect-only specialist | 830 / 2,048 | 40.5% |
| Shared mixed-experience cube | 610 / 2,048 | 29.8% |
| Uniform random | 235 / 2,048 | 11.5% |
| Rotate all learned action channels | 71 / 2,048 | 3.5% |

The product improved over collect-only by `5.47` percentage points, over shared
write-mixing by `16.21` points, over random by `34.52` points, and over the
rotated causal control by `42.53` points. Every one of the 16 worlds had a
successful product-policy trace. At 160 steps it remained ahead of collect-only
(`1,720` versus `1,659`). Evaluation performed zero model writes and all ten
pre-registered gates passed.

## Mechanism

Each specialist is an exact, non-neural relation probability cube. It sees a
fixed `7×7×4` raw binary board and four anonymous external action indices.
Successful real trajectories write action counts to translation-shared raw
identity, pair-offset, joint-geometry, nearby-matter, and relation×matter
addresses. The released decision is simply:

`P(a | push experience) × P(a | collect experience)`, normalized over four
actions.

The two channels remain independent. This matters because writing both task
families into one cube diluted evidence: in development, shared write-mixing
scored `240/768` at 32 steps, below collect-only's `275/768`. Equal probability
composition reached `342/768`, which was then tested on wholly new frozen maps
and random seeds.

`ProductPolicy` contains no task-family switch, reward, score, loss, gradient,
or neural-library reference. `classifier.dev` helped reject a premature runtime
planner route; it did not enter model training, inference, or evaluation.

## Frozen evidence

- Protocol: [`protocol_v09_direct.json`](protocol_v09_direct.json)
- Holdout: [`holdout_v09.json`](holdout_v09.json)
- Runner: [`experiment_v09_direct_frozen.py`](experiment_v09_direct_frozen.py)
- Result: [`artifacts/v09direct/result.json`](artifacts/v09direct/result.json)
- Result SHA-256:
  `d5720204698b46f5494e97063bb9f834e1ec403e0a910d1247ee1010a572d6d6`
- Video SHA-256:
  `4df22717c55a9436776e18053eb818e0287e7dedd2ba00c39a35148f695cdbfd`

The holdout, source hashes, training digests, action seeds, step budgets,
controls, thresholds, failure policy, and zero-write gate were frozen before
the runner opened any evaluation world.

## Boundary

The equal product is a **supplied composition rule**, not an autonomously
invented router. The raw encoder, task generators, binary success events,
episode limits, and evaluation criterion are also supplied. Training uses
successful-path selection, though no scalar reward or value function.

This supports bounded cross-task direct control on a synthetic family. It does
not establish arbitrary Sokoban, learned goal formation, language grounding,
unrestricted causal discovery, self-generated task decomposition, or AGI.
