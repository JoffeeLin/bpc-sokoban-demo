# BPC Tetris v1.71-v1.85 — Scaffold Deletion and Pure Reintegration Report

Date: 2026-10-06

## Status
This batch continues the post-v1.66 attempt to reconnect a minimal BPC kernel to real black/white Tetris transitions without restoring Geometry / Move / Rotate / Collision / Spawn / Closure family observers.

The promoted complete-Tetris baseline remains **Binary World-Fit v1.13**, whose archived formal result is 312,839/312,839 exact over 8 long-rollout seeds. Nothing in this batch replaces that checkpoint.

The purpose here is different: identify which representational and credit scaffolds can be removed while recovering as much real Tetris dynamics as possible from the same global reality residual.

## v1.71 — signed/bidirectional consequence relation
v1.70 used positive-only consequence mass. v1.71 allowed an anonymous relation to carry positive or negative effect. Four independent streams improved from a mean 86.724625% to 90.750875% pixel accuracy, but whole-board exact remained zero and naive signed storage created a very large weak relation cloud.

## v1.72 — delete explicit one-hop local-relation source waves
Keeping only `current nonzero physical pixel × previous bit state × anonymous operation port` raised the 8-seed mean from 87.293938% to **90.106250%**, and every seed improved. Stored relations fell from roughly 243k-259k in v1.70 to roughly 72k-76k.

Therefore the explicit local-neighbor source layer is rejected as a necessary primitive for this stage.

## v1.73-v1.74 — delete output roles and token-like namespaces
The future value no longer needs a special output-slot address. Prediction is measured at the same physical pixel address used for input.

Pixel positions, binary history states and operation ports are represented only as externally supplied unique physical addresses, with no BIT/RELATION/output token namespace inside the relation store.

Representative outputs remain numerically identical to v1.72.

## v1.75 — delete equal-credit writeback
The major capability gain came from deleting a subtler scaffold: v1.70-v1.74 wrote the same destination residual to every participating source relation.

v1.75 keeps one global visible residual, but the residual returns through each relation's exact noisy-OR marginal participation:

`global residual × actual local participation -> relation writeback`

No source class, destination class, Move/Rotate label or local-neighborhood source is introduced.

At 10k training transitions, 8 seeds averaged **99.303125% pixel accuracy** and **553.375/1000 whole-board exact**. At 30k training transitions the mean rose to **99.358188%** and **586.75/1000 exact**.

Increasing seed0 training to 100k did not close the remaining gap, so this is a structural boundary, not merely a data-volume shortage.

## Remaining error localization
At 30k, seed0:
- left: 70.149% whole-board exact
- right: 68.750%
- down: 76.444%
- rotate: **14.232%**

Most failed boards differ by only one to four pixels. The dominant missing computation is higher-order relational/process structure under rotation and no-op/collision contexts.

## Rejected follow-ups
- v1.76: re-add one-hop relations under marginal credit — small gain, ~1.51M relations; rejected.
- v1.77: pair-of-local-relation collisions — rotation 22.846%, but ~2.29M relations; rejected.
- v1.78: translation-shared relative-displacement-only medium — only ~12-13% whole-board; over-compressed.
- v1.79: fixed two-step temporal identity — worse; raw-history fragmentation.
- v1.80: hand-propagated temporal process carrier — did not beat v1.75.
- v1.81: re-enter disappearance events as identities — small gain only, more fragmentation.
- v1.82: continuous temporal residual amplitude in a signed linear field — underperformed.
- v1.83: all-pair anonymous collision slots — static-world pairs polluted the field.
- v1.84: temporal-residual-only collision slots — cleaner but did not beat v1.75.
- v1.85: previous action wave as literal history identity — performance decreased and K grew.

## Current smallest supported Tetris reintegration core
The strongest current research candidate is approximately:

`physical pixel addresses`
`+ anonymous action-port addresses`
`+ one-tick temporal state`
`+ sparse relation mass`
`+ noisy-OR superposition`
`+ one global visible residual`
`+ marginal participation writeback`

Notably absent are explicit model-side Geometry, Move/Rotate/Collision labels, one-hop local-relation source layer, whole-neighborhood identity, dedicated output address class, BIT/RELATION token namespace, action/output head split, and candidate winner/top-1 routing.

## Current frontier
The evidence now points to **functionally compressed process state**: preserve whatever part of history changes future dynamics, while identifying different surface histories that have the same future effect. This is narrower than restoring a Tetris-specific Geometry or Rotate module.

## Promotion rule
No research version in this batch is promoted over v1.13.

Promotion requires:
1. 100% whole-board exact on the non-Lock reintegration slice across multiple seeds;
2. reintegration of Lock / Spawn / LineClear / GameOver without family-specific observers;
3. full long-rollout exactness comparable to v1.13;
4. strict C build, O2/O3 identity and sanitizer checks.
