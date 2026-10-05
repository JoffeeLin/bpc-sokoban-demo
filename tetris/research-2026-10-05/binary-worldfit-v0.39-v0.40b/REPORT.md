# BPC Binary World-Fit v0.39–v0.40b — Visible-Trajectory Scaffold Deletion

Date: 2026-10-05

## Goal
Continue deleting family-specific training scaffolds while preserving the strict black/white-screen world-fitting capability.

## v0.39 — Spawn/GameOver split from ordinary visible lock transitions
The previous synthetic Spawn/GameOver split curriculum is replaced at final credit by ordinary visible lock transitions. The learner observes the pre-spawn visible state and the real final visible consequence; no blocked/unblocked semantic label is passed into the field.

Training audit:
- visible lock transitions: 2,500
- direct spawn outcomes: 2,340
- GameOver/complement outcomes: 160
- learned C=1 direct/complement = 0.999573 / 0.000427
- learned C=0 direct/complement = 0.006173 / 0.993827

Formal frozen evaluation:
- 1/2/3/4 line stress = 10,000 / 10,000
- vertical non-clear = 2,500 / 2,500
- seed0..7 = 312,839 / 312,839 exact

## v0.40 — compatibility from ordinary visible-play residual counterfactuals
Dedicated single-cell obstacle compatibility training is removed from final credit. Compatibility of proposal destinations with empty / occupied / boundary states is relearned from ordinary visible gameplay trajectories.

Representative learned probabilities:
- empty ≈ 0.99995
- occupied ≈ 0.0004–0.0008
- boundary ≈ 0.0003–0.0006

The first v0.40 implementation passed the tested formal seeds and clear stress, but v0.40b is the fully frozen version below.

## v0.40b — product-responsibility visible compatibility (PROMOTED)
Compatibility credit is assigned from ordinary visible gameplay using product responsibility: when a proposal succeeds, every participating destination-state relation receives positive credit; when it fails, negative credit for a participant is weighted by the current support of the other participating relations.

Training audit:
- credited visible transitions: 73,351
- success: 64,986
- failure: 8,365
- learned empty = 0.999746
- learned occupied = 0.000333
- learned boundary = 0.000187

Frozen formal evaluation:
- 1/2/3/4 line stress = 10,000 / 10,000
- vertical non-clear = 2,500 / 2,500
- seed0..7 = 312,839 / 312,839 exact
- O2/O3 diff = 0 bytes
- UBSan stderr = 0 bytes

## Current scaffold status after v0.40b
Deleted / no longer required in the promoted line:
- Tetris-specific collision rule
- row detector / clear_line / hole propagator
- whole-chain closure scanner
- function-family namespace (GAUGE/ROUTE/LIFE/SPAWN/CLOSURE as storage class IDs)
- dedicated Action-lifetime semantic rule
- dedicated route target labels
- dedicated Spawn relation curriculum
- dedicated Spawn/GameOver split final curriculum
- dedicated compatibility micro curriculum
- dedicated forced LineClear event curriculum in the current slow-play closure learner

Still present and high priority:
1. Geometry is still bootstrapped by a 1/2/3-voxel micro curriculum and a dedicated geometric observer.
2. Binary screen + temporal trace is internally converted into transient/persistent arrays; the trace is self-born, but execution still treats the two identities structurally differently.
3. Inference still has separate execution helpers for geometry proposal, spawn projection, closure propagation/coupling, route/lifetime readout, rather than one uniform wave propagator.
4. Stable inference still gates downstream relaxation on lock amplitude; scheduler-free participation has only a pilot-positive result because of computational cost.
5. Training is still orchestrated in staged passes rather than one continuous online residual stream.
6. Physical lattice/address topology and the fixed visible Preview region remain substrate assumptions.

## Current promoted checkpoint
**Binary World-Fit v0.40b**

Interpretation: the obvious game-specific scaffolds are largely gone. The remaining work is mostly architectural purity: unify geometry learning, information-instance representation, execution operators, scheduling, and training flow.