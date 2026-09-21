# BPC v0.42 parallel-posterior development preregistration

This protocol is committed before the first v0.42 run. v0.41 remains failed.
The v0.41 development set may motivate this mechanism but cannot provide v0.42
adoption evidence.

## Fixed mechanism

The medium, camera, real residual writeback, physical stencils and fixed
`2^20` capacity are unchanged. For each stencil and output bit, v0.42 measures
all four anonymous action posteriors from the same observation. A stencil has
influence only when its between-action posterior variance exceeds the exact
sampling variance expected from its four Beta posteriors. Influential stencil
posteriors are probability-mixed; if none separates actions, the unchanged
v0.41 posterior is used.

This is a probability identity, not a fitted selector, task score, semantic
field or separate learned module. Consistent action renaming must exactly
permute output distributions. The action-removed control uses the identical
capacity, observations and base posterior but cannot resolve actions.

## Fresh experience

- v0.42 training seed `242010`: 120 unique worlds from each of three separate
  physical regimes and 24 uniform random actions per world;
- v0.42 holdout seed `242110`: 24 causally joint worlds, four streams of 24
  uniform random actions;
- every v0.42 initial world must be disjoint from all v0.41 training and
  holdout initial worlds; v0.42 holdout must also be disjoint from v0.42
  training;
- evaluation is frozen and performs zero writes.

## Fixed gates

Adopt for an independent frozen reproduction only if all hold:

1. all stated world-disjointness checks pass;
2. unseen local contexts are at least 10% of holdout contexts;
3. overall defined-bit Brier is at most `0.020`;
4. changed-bit Brier is at most `0.50` and below copy-current;
5. unseen-context changed-bit Brier is at most `0.25`;
6. the candidate improves over both action-removed and rotated-action controls
   by at least 10% on changed and unseen-context changed bits;
7. capacity remains `2^20`, raw training states exceed active cells divided by
   64, and active cells are reported;
8. evaluation writes are zero and candidate/control digests do not change;
9. the complete unit suite, fixed typed output and exact action-renaming tests
   pass before execution.

No threshold will be changed after results. A pass is still development-only:
it authorizes a separately committed frozen seed and same-core non-Sokoban
physical test, not goal behavior or an AGI claim.
