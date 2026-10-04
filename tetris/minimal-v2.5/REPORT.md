# BPC Tetris Minimal v2.5 — Compositional Generalization Audit

Date: 2026-10-04

## Purpose

This phase adds no new Tetris rules. It tests whether relations learned from minimal single-cell physical experience behave as reusable functions rather than fitting the seven tetrominoes or a friendly random distribution.

The frozen base is v2.2: learned translation, shared collision carrier, single-cell rotation relation, learned lock channel coupling, preview-to-active spawn relation, all-row line-clear carriers, internally maintained latent rotation carrier, and fixed-point relaxation.

## v2.3 — exhaustive / near-exhaustive audit

- Translation + collision, all 3x3 active masks with 1..4 cells against all disjoint 3x3 obstacle masks, three directions: **48,960 / 48,960 exact**
- Blocked translation subset: **26,112 / 26,112**
- Rotation + collision, all 1..4-cell subsets of the 5x5 pivot-relative window with empty world or every possible single obstacle: **339,025 / 339,025 exact**
- Blocked rotation subset: **49,302 / 49,302**
- Every non-empty 16-bit preview pattern: **65,535 / 65,535 exact**
- Blocked spawn cases: **65,520 / 65,520 exact**
- Every 10-bit row pattern for clear-carrier detection: **1,024 / 1,024**
- Every 10-bit source row for one propagation step: **1,024 / 1,024**

## v2.4 — zero-shot arbitrary polyomino rollout

The seven tetromino catalogue is removed from evaluation. The external world generates arbitrary 1..8-cell preview/polyomino masks. The only validity constraint is that the physical rotation anchor is occupied. No polyomino-specific training is added.

Main run:
- 5,000 episodes, horizon <=150
- **190,184 / 190,184 ticks exact**
- 5,000 / 5,000 full exact episodes
- 59,089 lock events
- 5,000 game-over events
- no failure

By action:
- left 33,881 / 33,881
- right 34,273 / 34,273
- down 38,145 / 38,145
- rotate 26,507 / 26,507
- hard drop 57,378 / 57,378

Five additional independent seeds:
- **227,490 / 227,490 ticks exact**
- 70,306 lock events
- all five seeds without failure

## v2.5 — entity-count ladder

No new training. Exact visible entity count is swept from k=1 to k=12.

Every level remains 100%:
- k=1: 28,898 / 28,898
- k=2: 18,108 / 18,108
- k=3: 11,896 / 11,896
- k=4: 9,125 / 9,125
- k=5: 8,263 / 8,263
- k=6: 7,380 / 7,380
- k=7: 6,879 / 6,879
- k=8: 6,543 / 6,543
- k=9: 6,425 / 6,425
- k=10: 6,374 / 6,374
- k=11: 5,992 / 5,992
- k=12: 6,087 / 6,087

No entity-count frontier was observed within the full 12-cell visible spawn area.

## Engineering verification

- C11 + `-Wall -Wextra -Werror`: PASS
- O2/O3 representative outputs: byte-identical
- O2/O3 diff: 0 bytes
- representative SHA-256: `a87a28677b64d81761d0cf306ae0ff051d1dd28d10515f6495d99f50ad6919cf`
- UBSan stderr: 0 bytes

## Conclusion

The supported conclusion is narrower than “full AGI” but stronger than “Tetris works”:

> A relation learned in a minimal single-cell physical world can be reused spatially, superposed over unseen multi-cell structures, coupled through a shared action wave, recursively reused through time, and combined with other learned local relations without retraining on the resulting global object.

In this controlled world, a tetromino is not a primitive object that needs separate training. It is one four-cell instance inside a larger closure of the same local functions.

The next frontier is architectural unification, not more Tetris rules: replace the separately named Move / Rotation / Spawn / Coupling / RowPropagation structures with one shared anonymous BPC medium and test whether the same exact composition survives.
