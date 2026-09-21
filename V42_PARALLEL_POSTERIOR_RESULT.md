# BPC v0.42 parallel-posterior development result

Status: **DEVELOPMENT PASS / NOT YET FROZEN**. The implementation and gates
were fixed in commit `efd74b3` before the first run. This result authorizes an
independent frozen reproduction and a same-core non-Sokoban physical test. It
does not establish goal-directed behavior, Sokoban solving, or AGI.

## Fixed run

- fresh training seed `242010`: 8,640 transitions and 360 unique initial
  worlds;
- fresh holdout seed `242110`: 24 joint-physics worlds and 2,304 transitions;
- every initial world was disjoint from the v0.41 development experiment;
- the fixed `2^20`-cell medium made 17,694,720 training writes;
- evaluation made zero writes and left both model digests unchanged;
- all 70 tests passed before execution.

## Evidence

| Brier probability residual (lower is better) | Candidate | No action | Rotated action | Copy | 0.5 |
|---|---:|---:|---:|---:|---:|
| all defined bits | 0.006655 | 0.011158 | 0.010019 | 0.004223 | 0.250000 |
| changed bits | 0.145256 | 0.289674 | 0.533168 | 1.000000 | 0.250000 |
| unseen-context changed bits | 0.217190 | 0.320866 | 0.535735 | 1.000000 | 0.250000 |

The local-context novelty rate was 43.01%. On changed bits the candidate
improved over action removal by 49.86% and action rotation by 72.76%. On
unseen-context changed bits the improvements were 32.31% and 59.46%.

All ten fixed gates passed. The result also passes the newly added requirement
that unseen-context changed-bit Brier beat an uninformative 0.5 predictor.

## Interpretation and boundary

v0.41 pooled counts from all physical scales, allowing irrelevant scales to
dilute an action-bearing scale. v0.42 instead measures all four anonymous
action posteriors in parallel and uses only between-action variance that
exceeds the exact Beta sampling variance. The chosen scale is therefore a
consequence of probability evidence, not a hard-coded horizontal axis,
semantic selector, task reward or fitted score.

This is evidence for a reusable local transition-prediction mechanism under
held-out physical composition. It is not evidence that the medium can choose
actions to complete a goal. No GitHub/X breakthrough publication is authorized
until the separately committed frozen reproduction and a non-Sokoban physical
domain both pass without changing the core.
