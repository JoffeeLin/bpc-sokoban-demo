# BPC v0.6.1 Learned Macro-Geometry Frozen Result

## Decision

**ADOPTED for the pre-registered mechanism claim.** Four anonymous push-delta
templates were learned from random interaction and replaced the hand-written
macro box-behind/player-behind geometry used by v0.5. The learned condition
solved and independently replayed all eight new holdout maps; rotating the same
learned templates across action identities solved none.

This is not direct policy control, cross-task transfer, or an AGI result.

## Preserved v0.6 execution failure

The first frozen runner stopped before audit or holdout execution because
tuple-valued evidence was compared directly with its JSON list representation.
The v0.6 protocol and machine-readable failure remain committed. v0.6.1 reused
the still-unexecuted holdout, all seeds, mechanisms, controls, and gates; it
changed only canonical JSON normalization. No failed or difficult map was
replaced.

## Frozen protocol

- World learning: 240,000 random transitions, unchanged from v0.4/v0.5.
- Geometry learning: 240,000 further random interactions containing 4,120
  successful pushes.
- Representation: for each anonymous action, exact relative deltas from the
  prior player to the removed box, added box, and next player.
- Audit: 80,000 interactions from a disjoint seed containing 1,443 pushes.
- Holdout: eight persisted, previously unexecuted maps—two each with 1/2/3/4
  boxes and no overlap with v0.4 or v0.5 development maps.
- Causal control: rotate all learned templates across action identities while
  keeping world model, inverse relations, experience, maps, and budget fixed.
- Static gate: the v0.6 macro solver contains no supplied `ACTIONS`, no
  `action ^ 1`, and no call to `moved()`.
- Evaluation learning disabled; persistent model writes required to remain zero.

## Result

| Frozen condition | Push-template audit | Maps solved/replayed |
|---|---:|---:|
| Learned anonymous geometry | **1,443 / 1,443** | **8 / 8** |
| Rotated learned geometry | **0 / 1,443** | **0 / 8** |

Both unseen four-box maps passed. Every emitted sequence solved again under the
true forward environment. All nine pre-registered gates passed.

The learned templates were unique within experience:

| Anonymous action | Player→removed | Player→added | Player→next | Support |
|---:|---:|---:|---:|---:|
| A0 | `(-1,0)` | `(-2,0)` | `(-1,0)` | 986 |
| A1 | `(1,0)` | `(2,0)` | `(1,0)` | 1,053 |
| A2 | `(0,-1)` | `(0,-2)` | `(0,-1)` | 1,060 |
| A3 | `(0,1)` | `(0,2)` | `(0,1)` | 1,021 |

## Determinism and integrity

- Model SHA-256: `4b6ce7815dc350acd03e2362511004c66fc536acaea62f1645ac717ddfce8070`
- Repaired protocol SHA-256: `ac2c1ef77aa81267414f2d06d08f05ffe9b3e25c132ddc34ebf295ec442aa023`
- Preserved failed protocol SHA-256: `bee35c85d01f8b3154497a176958c6749a7e1995f4ac5f4e122fb26aa45672f2`
- Holdout SHA-256: `26add850a8a923317bc8d097ea95dbf034fc1d304bf3c1508c6fcdd97dc089c0`
- Normalized two-run result SHA-256: `2b6b4a9f5675c4d36d13c2a1648f396ac5fc360c234c06f68ca475cd67f69008`
- Video SHA-256: `3522ba28959d906923134036c6ee77229d121c300cfc41e0e1e58569616d54a8`

Two complete repaired-protocol executions were identical after removing
wall-clock timing fields.

## Supported claim and remaining scaffold

Supported: anonymous raw transition deltas can supply the macro predecessor
geometry required by the existing learned-world reversible wave on new
Sokoban layouts. The rotated-template control establishes action binding as
causal in this experiment.

Still supplied:

- local action-relative cell addressing inside the v0.4 world function;
- solved-state seeding and backward phase propagation;
- the decision to form reversible equivalence classes;
- the single-task Sokoban environment and raw channels.

The next required advance is cross-task composition of learned predecessor and
successor fragments—not simply more maps from the same generator.

- GitHub release: `https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v6.0.0`
- Video asset: `https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v6.0.0/bpc_learned_geometry_v06_8_unseen.mp4`
