# BPC v0.7: frozen cross-task transition composition

## Result

**ADOPTED for the narrow claim below.** A non-neural anonymous-bit model saw
two disjoint training families:

- `150,000` push-only transitions with no marks;
- `150,000` collect-only transitions with no movable objects.

It then predicted worlds containing both mechanisms for the first time. No
training patch contained both an object bit and a mark bit.

| Frozen condition | Seed 77107 | Seed 77207 | Combined |
|---|---:|---:|---:|
| Fragment-chain BPC | **2,001 / 2,001** | **1,794 / 1,794** | **3,795 / 3,795** |
| Condition deletion only | 1,288 / 2,001 | 1,190 / 1,794 | 2,478 / 3,795 |
| Residual prime clauses | 1,249 / 2,001 | 1,171 / 1,794 | 2,420 / 3,795 |
| Full-context memory known | 0 / 2,001 | 0 / 1,794 | **0 / 3,795** |

The adopted model was also exact on all `240,000` combined-world transitions,
retained `60,000 / 60,000` push-only and `60,000 / 60,000` collect-only
transitions, repeated the first frozen run bit-for-bit, and performed zero
evaluation writes. All ten pre-registered gates passed.

## Mechanism

The model receives only twelve anonymous input bits: four raw channels at
three action-relative cells. It is not given task names, object names, rewards,
scores, or semantic rules.

1. For every future bit, condition deletion removes predecessor bits while the
   observed future remains deterministic.
2. The model records which anonymous bit changes always co-occurred with each
   learned change.
3. At prediction time, it first proposes the local next state, then repeatedly
   suppresses a change when its learned co-change prerequisites are absent.

This matters in the new joint world. Collect-only experience says that a mark
at the next cell disappears, but it also says that disappearance always
co-occurs with the two agent-location changes. When a new object-on-mark push
is blocked, those movement changes are absent, so the model preserves the mark.
The condition-deletion control cannot make this composition and fails that
interaction.

`FragmentChainWorld` itself contains no family, object, mark, action-vector,
reward, score, loss, gradient, or neural-library reference. `classifier.dev`
ranked shared predecessor/successor fragments as the next development route;
it is absent from training, evaluation, and runtime.

## Frozen protocol

- Protocol: [`protocol_v07_cross.json`](protocol_v07_cross.json)
- Runner: [`experiment_v07_cross_frozen.py`](experiment_v07_cross_frozen.py)
- Machine-readable result:
  [`artifacts/v07cross/result.json`](artifacts/v07cross/result.json)
- Result SHA-256:
  `1df8ea44660fdfd24e62c6c5c37ed19eefdfa1aecf75811c330c8987d3d5be55`
- Video SHA-256:
  `f8d4ddacacc9ab102228365b6e0fef3214b8d58cc48c711b293330ba7ecd5c99`

The protocol fixed code hashes, training and evaluation seeds, minimum joint
event count, causal-control margin, retention gates, deterministic repetition,
source audit, and zero-write requirement before either holdout seed ran.

## Development failures retained

The initial condition-deletion mechanism predicted every new joint context but
only `604 / 938` correctly. A residual-prime alternative reached `575 / 938`
after the observation window was corrected. These failures led to the
co-change prerequisite mechanism; they were not relabeled as successes. The
development evidence is retained in
[`artifacts/v07cross/development.json`](artifacts/v07cross/development.json).

Before protocol freeze, a development observation bug was also found: the
future window reused the previous agent location as both window origin and
future occupant. The two roles were separated, all development evidence was
rerun, and only then were new holdout seeds frozen.

## Claim boundary

This is evidence for exact **local one-step world-function composition** inside
the supplied synthetic generator. It is stronger than cross-layout replay:
the tested local combinations are absent from both training families.

It is not evidence of long-horizon planning, direct policy control, autonomous
task discovery, natural-language understanding, unrestricted causal discovery,
or AGI. The raw channels, action-relative three-cell window, four-action
interface, task generators, and evaluator remain supplied. Co-change
implications can also be spurious outside this controlled world family.
