# BPC Binary World-Fit v0.62–v0.70 — Inference Scaffold Deletion

Date: 2026-10-06

## Goal
Continue reducing the frozen black/white-screen world model without adding any Tetris rule. The capability invariant remains the same controlled 10x20 world: eight independent long-rollout seeds must stay exact.

## v0.62 — superposed gauge readout
Removed top-1 / best-gauge selection. Every positive gauge wave participates continuously; the translation component is the weighted centroid and only the final physical lattice landing is rounded.

Frozen world regression remains 312,839 / 312,839 exact; clear stress remains 10,000 / 10,000.

## v0.63 — superposed Spawn participation / raw-screen Spawn relation evidence
Spawn displacement amplitudes are allowed to superpose rather than selecting a single strongest displacement. A parallel raw-screen relation experiment also showed that the old Preview-channel identity can be migrated to ordinary physical screen displacement.

## v0.64 — terminal state is only a visible screen pixel
Removed the separate internal GameOver variable at the frozen API. The terminal signal is read/written only at its visible binary screen address.

Eight-seed regression remains exact.

## v0.65 — Preview is screen-native
Removed the internal `prev[16]` reconstruction from frozen inference. Spawn reads the 4x4 preview region directly from the binary screen.

Eight-seed regression remains exact.

## v0.66 — remove recurrent Action-mass renormalization
Deleted the global normalization that forced surviving Action carriers to preserve total injected mass. Re-entry amplitude is now exactly the learned Action->Action consequence amplitude.

Eight-seed regression remains 312,839 / 312,839 exact.

## v0.67b — no persistent proc/rest world decomposition
Deleted the persistent internal `proc[]` / `rest[]` state split. The only persistent model state is:

`binary visible frame B + self-born temporal trace T`

Process and persistent participation are derived locally as `B*T` and `B*(1-T)` only while a relation is evaluated, then immediately written back to B/T. They are not retained as two semantic world states.

Eight-seed regression: 312,839 / 312,839 exact.

## v0.68 — Spawn has no Preview/channel token
Migrated the mature Spawn displacement relation from the old channel-addressed key into an ordinary raw-screen displacement key. A visible source pixel in the side-screen preview region and a destination board pixel are related only by physical displacement; no `Preview`/channel namespace is present.

An initial ~70% run was invalid because it accidentally migrated from an older field checkpoint. Rebuilding the migration from the current frozen field restored the valid result:

312,839 / 312,839 exact.

## v0.69 — delete discrete geometry-effect Route classifier
Removed `PT_GEOMEFFECT`, `sf_geom_dir_code()` and the intermediate discrete geometry-effect signature from Route lookup.

Route is now directly:

`Action carrier x feasibility wave x consequence wave`

A first ~2% run was invalid because the upstream v0.68 field artifact had been polluted. Rebuilding v0.68 from its frozen source and then remigrating v0.69 produced the valid result:

312,839 / 312,839 exact.

Relation count changes from 444 to 456 because the former effect-equivalent route entries are expanded onto the physical Action carriers. This is a deliberate scaffold deletion, not a compression improvement.

## v0.70 — Closure uses ordinary spatial relation tokens
Removed the Closure-specific `PT_ADDRREL` namespace and the `same/below/above` address token family.

Closure consequence now uses the same ordinary spatial relation token as the rest of geometry:

- same address: `trel(0,0)`
- closure physically below source: `trel(0,+1)`
- closure physically above source: `trel(0,-1)`

The old mature probabilities are migrated without changing their evidence.

Formal result:
- eight-seed rollout: 312,839 / 312,839 exact;
- O2/O3 full evaluator output diff: 0 bytes;
- UBSan same-equation smoke: 4,025 / 4,025 exact, stderr 0 bytes.

SHA-256:
- core: `0fd3bc144ddfd5e349950e9ee966619bc9d4451bfefe71b2e2a8f8818d86d003`
- frozen field: `846d9a100bc1717486a0c4d3f0d4e6c0ea9c07c48f74271790613f98db8e8eb4`

## Current promoted checkpoint
**Binary World-Fit v0.70**

Current frozen inference now has no:
- Tetris semantic `State` API;
- hidden Lock output;
- fixed Spawn-before-Clear order;
- GameOver break scheduler;
- top-1 gauge selection;
- Action mass renormalizer;
- persistent Active/World (`proc/rest`) state containers;
- Preview intermediate array;
- Preview/channel identity in Spawn relation address;
- discrete geometry-effect classifier in Route;
- Closure-specific address-relation namespace.

## Remaining high-value scaffolds
1. Route outcomes still use a dedicated consequence vocabulary (`candidate / persist / persistent-write`).
2. Closure outcomes still use dedicated effect tokens for source death and +1 birth, even though their address relation is now ordinary spatial relation.
3. Geometry still contains explicit synchronous coordinate-relaxation code and final lattice rounding.
4. Primitive token *types* (`ACTION`, `REL`, `FEAS`, `ROUTE`, `BOUNDARY`, `PROPOSAL`, `DESTSTATE`, `EFFECT`) remain supplied by the substrate.
5. Some inference helpers remain separate procedures even though their learned values share one field.
6. Training/reference reality remains a separate program, as intentionally required for causal evaluation; further purity should target the BPC kernel rather than delete the external reality.