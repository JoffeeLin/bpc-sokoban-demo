# BPC v0.5 Learned Reversible-Equivalence Frozen Result

## Decision

**ADOPTED for the pre-registered mechanism claim.** Four inverse action
relations were discovered only from exact round-trip interaction. Those
relations replaced the supplied free-space flood fill inside the learned-world
configuration wave. The frozen model solved and independently replayed all
eight new holdout maps, while an identical-experience wrong-inverse control
solved none.

This is not a pure direct policy, autonomous solver discovery, or an AGI result.

## Frozen protocol

- World learning: 3,000 environments × 80 uniform-random actions = 240,000
  real transitions, unchanged from v0.4.
- Inverse discovery: 600 environments × 60 random actions. A candidate inverse
  was admitted only when forward action + candidate action reconstructed the
  exact prior microstate.
- Reach audit: 4,000 new random states from a disjoint seed.
- Holdout: eight persisted maps, two each with 1/2/3/4 boxes, generated and
  frozen before execution; none overlaps the v0.4 development set.
- The old supplied `reach()` function was replaced with a deliberate exception
  before holdout solving. Any hidden call would have failed the run.
- Evaluation learning was disabled; persistent model writes had to remain zero.
- Causal control: deliberately wrong inverse pairs with the identical learned
  world model, experience, maps, and search budget.

## Result

| Frozen condition | Reach equivalence | Maps solved/replayed |
|---|---:|---:|
| Learned inverse relations | **4,000 / 4,000 exact** | **8 / 8** |
| Wrong inverse relations | 7 / 4,000 exact | **0 / 8** |

The learned orbit had zero symmetric-difference cells across all 4,000 audit
states. The wrong-inverse control disagreed by 50,202 cells. Both unseen
four-box maps passed. Every emitted action sequence solved again under the true
forward environment. All nine pre-registered gates passed.

The learned inverse evidence was unambiguous:

| Forward action | Discovered inverse | Exact round trips | Other candidates |
|---:|---:|---:|---:|
| 0 | 1 | 5,806 | 0 |
| 1 | 0 | 5,810 | 0 |
| 2 | 3 | 5,738 | 0 |
| 3 | 2 | 5,661 | 0 |

## Determinism and integrity

- Model SHA-256: `4b6ce7815dc350acd03e2362511004c66fc536acaea62f1645ac717ddfce8070`
- Protocol SHA-256: `64a9c5b8fd8626df868affce90f94a942bb8613f76f7733cf5bc82dd0256a60b`
- Holdout SHA-256: `a279162d54ec92e570f31d6c9e2dec005a107a65c3b7b66f5a7cd13a908a0cbf`
- Normalized two-run result SHA-256: `bcd6c5b029cd201cfae532731849354e4ddc2c5b3ff145bdbc28e786549eb02c`
- Video SHA-256: `11cdc2da66c39984b59382ed8ac91be497fa5dfa5c538c20e05e6ed317206020`

Two complete formal executions were identical after removing wall-clock timing
fields. Learned inverse mapping, evidence counts, reachable sets, action
sequences, search-state counts, gates, and conclusion were unchanged.

## Supported claim and remaining scaffold

Supported: exact round-trip experience can discover reversible action
relations and use them to construct future-effect-equivalent player regions on
new layouts, replacing one more hand-written solver component.

Still supplied by the program:

- raw local channels and the spatial displacement interface for actions;
- macro box-push candidate enumeration;
- solved-state seeding and backward phase propagation;
- the decision to search over reversible equivalence classes.

Therefore this is a second falsifiable mechanism advance beyond v0.4, not
evidence that BPC discovered the whole algorithm, transfers across arbitrary
tasks, or is AGI.

- GitHub release: `https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v5.0.0`
- Video asset: `https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v5.0.0/bpc_reversible_equivalence_v05_8_unseen.mp4`
- X video: `https://x.com/JoffeeLin/status/2101683972887707777`
- X code-link reply: `https://x.com/JoffeeLin/status/2101685282210971907`
