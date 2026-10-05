# BPC Binary World-Fit v0.71–v0.75 — Primitive Vocabulary Reduction

Date: 2026-10-06

## Goal
Continue deleting historical cognitive vocabulary from the frozen black/white-screen BPC inference kernel while preserving the same exact world-model regression.

## v0.71 — remove dead primitive vocabulary
Deleted historical token types that no longer participated in frozen inference: `AXIS`, `PHASE`, `CHANNEL`, `GEOMEFFECT`, and `ADDRREL`. Surviving token numeric identities were kept fixed, so no field migration was needed.

Result: 312,839 / 312,839 exact.

## v0.72 — remove `PT_ROUTE`
The field no longer stores abstract Route outcomes named `candidate / persist / persistent-write`.

They are encoded only by physical visible-state consequences:
- target/proposal becomes `B=1,T=1`;
- source remains `B=1,T=1`;
- source becomes `B=1,T=0`.

Spawn/GameOver split uses the same physical consequence vocabulary. Mature evidence was migrated without adding supervision.

Result: 312,839 / 312,839 exact.

## v0.73 — remove `PT_EFFECT`
Closure no longer stores abstract `death / +1 birth` effect tokens.

The same mature relations are represented as ordinary visible-state transitions:
- source address -> empty;
- +1 address -> persistent occupancy (`B=1,T=0`).

Result: 312,839 / 312,839 exact.

## v0.74 — remove `PT_PROPOSAL`
A proposal is no longer a primitive object. Compatibility is simply the collision between:

`desired target state B=1,T=1`

and the current destination state (`empty / occupied / physical boundary`). Route direct/spawn consequences likewise use the desired visible state directly.

Result: 312,839 / 312,839 exact.

## v0.75 — remove `PT_ACTION_NEXT`
Action lifetime no longer uses a separate `ActionNext` token. Re-entry is the self-coupling of the same physical Action carrier with its feasibility context.

Result: 312,839 / 312,839 exact.

Engineering freeze:
- O2/O3 full evaluator output diff: 0 bytes;
- UBSan same-equation smoke: 4,025 / 4,025 exact;
- UBSan stderr: 0 bytes.

SHA-256:
- v0.75 core: `212c9d3cca9119b85856680ae454074e1012793e5d96e249585456e0a121748d`
- v0.75 frozen field: `6ef31b4de309ca8d864ed07ec6c1faeb27b49b84867912325610fff6dd445287`

## Current promoted checkpoint
**Binary World-Fit v0.75**

The remaining primitive token families in frozen inference are now close to substrate-level notions:
- physical Action carrier;
- ordinary spatial relation;
- feasibility/carrier context;
- physical boundary relation;
- visible state token.

Remaining high-value scaffolds:
1. `FEAS` is still a dedicated conditioning token rather than the continuous compatibility carrier itself participating directly in downstream coupling.
2. `BOUNDARY` is still a distinct token type; it may be reducible to ordinary lattice-address absence / neighbor topology.
3. Geometry still has an explicit coordinate-relaxation implementation and final lattice rounding.
4. Separate helper procedures remain for geometry, Spawn, Closure, Route/Life readout even though their learned relations share one field.
5. The training program still contains reference-world structures by design; the frozen inference core remains physically separated from them.