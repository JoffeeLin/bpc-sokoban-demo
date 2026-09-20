# BPC v0.4 Learned-World Frozen Result

## Decision

**ADOPTED for the pre-registered hybrid claim.** A 48-row local transition
probability cube, formed only from random raw game transitions, replaced the
hand-written Sokoban push-validity test inside the fixed v0.3 configuration
wave. It solved and independently replayed all 12 frozen unseen maps, including
three four-box maps although training experience contained only one to three
boxes.

This is not a pure direct policy or an AGI result.

## Historical v0.3 reproduction

The supplied `BPC_Sokoban_General_v0.3_实验包.zip` had SHA-256
`107145ee2cc50468cf35749a5082aa76475090f7c22461ad7955ab745e60a898`.
Every internal manifest hash passed. Fresh `-O2`, `-O3`, `-Werror`, and UBSan
builds reproduced the included 1/2/3/4/5/6/8-box results; UBSan exited zero
without diagnostics.

The archive itself identifies the remaining gap: v0.3 supplies Sokoban local
physics and player-reachability compression. v0.4 tests removal of the first of
those two supplied mechanisms.

## Frozen protocol

- Training: 3,000 generated environments × 80 uniform-random actions =
  240,000 real transitions.
- Training environments: 2,857 unique maps, one to three boxes.
- Learned state: 48 exact Dirichlet rows over three action-relative raw cells.
- Validation: 40,000 new raw transitions from a disjoint seed.
- Holdout: 12 persisted maps, three each with 1/2/3/4 boxes; shortest reference
  action distance 6–23.
- The reference solver filtered solvability only. No reference solution action
  entered BPC learning or inference.
- Evaluation learning disabled; model writes required to remain zero.
- Closest causal ablation: identical experience but remove the third cell
  (the cell beyond the possible box).

## Result

| Frozen condition | Local transition result | Maps solved |
|---|---:|---:|
| Full three-cell `F_world` | **40,000 / 40,000** | **12 / 12** |
| Remove third cell | 24,513 / 40,000 overall; **0 / 688 pushes** | **0 / 12** |

The primary model solved every held-out map and every emitted sequence solved
again under the independent true forward environment. All three unseen
four-box maps passed. Persistent evaluation writes were zero. All eight
pre-registered gates passed.

## Determinism and integrity

- Model SHA-256: `4b6ce7815dc350acd03e2362511004c66fc536acaea62f1645ac717ddfce8070`
- Training-level manifest SHA-256: `48a78844f2475bcc29289d6ad19062710f9df459dba5255552efb6d6f3d015c2`
- Protocol SHA-256: `12f4231bb2ad90d9b58cc7bc44d253a552a987436ae7e6a132defc6337458424`
- Holdout SHA-256: `a97a2a3ca2c6a99101512cbb066865da4626159fb024e9603e27a53417f40d03`
- Normalized two-run result SHA-256: `d6dff0928c3a7a205b3095dddae2ac23fa88a526934f55e132ec851279d5eb27`
- Video SHA-256: `c58c63c77914308efab9fe39c21f8e20b468bc0d88889c5676d8ef5924a6200f`

The two full formal executions were identical after removing wall-clock timing
fields. Model digest, maps, actions, state counts, gates, and conclusions were
unchanged.

## Supported claim and remaining scaffold

Supported: the learned three-cell local world function transfers from random
experience to unseen layouts and an unseen object count when placed inside the
same scale-independent recursive wave shell. The causal ablation establishes
that the third-cell relation is necessary in this experiment.

Still supplied by the program:

- raw cell channels;
- player reachable-component computation;
- macro predecessor candidate geometry;
- solved-state seeding and backward wave propagation;
- the decision to compress future-equivalent player positions.

Therefore this is evidence that one previously supplied world-law component
can be learned and reused, not evidence that BPC autonomously discovered the
whole solver, arbitrary task rules, cross-task general intelligence, or AGI.

- GitHub release: `https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v4.0.0`
- Video asset: `https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v4.0.0/bpc_learned_world_v04_12_unseen.mp4`
