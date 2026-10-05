# BPC Binary World-Fit v0.41–v0.43 — Scheduler / Geometry Scaffold Audit

Date: 2026-10-05

## Baseline
Promoted baseline before this batch: **v0.40b**.

Frozen capability floor:
- 8-seed rollout: 312,839 / 312,839 exact;
- 1/2/3/4-line stress: 10,000 / 10,000;
- vertical non-clear: 2,500 / 2,500;
- O2/O3 output diff: 0 bytes;
- UBSan stderr: 0 bytes.

## v0.41 — always-participating downstream relation waves (pilot positive)
The explicit `if (lockamp > threshold) downstream_relax(...)` scheduler was weakened into algebraic carrier participation. Spawn/closure relations are conceptually present every microstep; a zero carrier only provides a numerical short-circuit.

Pilot result:
- clear stress: 2,000 / 2,000;
- vertical non-clear: 500 / 500;
- seed0: 11,812 / 11,812 exact.

Status: **purity-positive pilot, not promoted**. Full 8-seed freeze was not completed in this batch; the main issue is computational cost rather than an observed capability failure.

## v0.42 — remove 1/2/3-voxel Geometry micro curriculum (negative)
The dedicated 1/2/3-cell geometry curriculum was removed. Gauge/basis/phase evidence was extracted only from ordinary real gameplay transitions.

Natural play correctly recovered:
- Left gauge = (-1,0)
- Right gauge = (+1,0)
- Down gauge = (0,+1)
- Rotate gauge = (0,0), basis swap
- Drop macro relation = (0,+1)

However phase credit was ambiguous for relation-preserving translations, leaving their phase near neutral. Because `sf_geom_targets()` requires a mature phase, downstream visible compatibility received zero usable credit.

Result:
- compatibility evidence: 0 usable transitions;
- clear stress: 0 / 2,000;
- not promoted.

## v0.42b — relation-preserving translation continuity (partial positive)
When normalized local relations are unchanged across a visible transition, the observer now treats this as relation-preserving translation and credits identity basis / positive phases without using action semantics or a Tetromino catalogue.

Learned:
- Left/Right/Down/Drop geometry correct;
- Rotate gauge/basis correct;
- compatibility relearned from ordinary visible play:
  - empty = 0.999655
  - occupied = 0.000496
  - boundary = 0.000219
- clear stress: 2,000 / 2,000;
- vertical non-clear: 500 / 500.

But Rotate retained one unresolved phase/chirality component:
- Rotate phase = (neutral, -1).

Long-rollout result:
- seed0: 1,839 / 2,136 = 86.10%
- seed1: 1,727 / 2,025 = 85.28%

Status: **partial positive, not promoted**. The micro curriculum is gone, but the current global gauge/basis/phase parameterization cannot uniquely infer rotation chirality from the available anonymous point-set correspondence.

## v0.43 — two-step function re-entry phase credit (negative)
Attempted to resolve the remaining phase ambiguity using ordinary repeated-action trajectories:

`F(F(screen)) -> real two-step screen`

This failed as a universal phase credit mechanism. For 90-degree rotation, clockwise and counter-clockwise transforms both square to a 180-degree transform, so two-step re-entry does not carry chirality information. Re-entry also incorrectly neutralized translation phases when used indiscriminately.

Result:
- compatibility evidence collapsed to zero;
- clear stress: 0 / 2,000;
- seed0/seed1 immediate divergence;
- not promoted.

## Current promoted checkpoint
**Binary World-Fit v0.40b** remains the stable baseline.

## Current scaffold status
Promoted line has already deleted:
- Tetris-specific collision rule;
- row detector / `clear_line` / hole propagation;
- whole-chain closure scanner;
- function-family storage namespace;
- dedicated Action-lifetime semantic rule;
- dedicated route target labels;
- dedicated Spawn relation curriculum;
- dedicated Spawn/GameOver final curriculum;
- dedicated compatibility micro curriculum;
- dedicated forced LineClear event curriculum.

Still unresolved:
1. Geometry micro curriculum / dedicated geometry observer: **v0.42–v0.43 show the micro curriculum can be removed, but the current gauge/basis/phase representation is not pure or robust enough to preserve rotation chirality.**
2. Internal transient/persistent split derived from temporal trace.
3. Separate execution helpers instead of one uniform relation-wave propagator.
4. Stable lock-triggered downstream scheduling (v0.41 is only pilot-positive).
5. Staged training orchestration instead of one continuous residual stream.
6. Physical lattice/address topology and fixed Preview region as substrate assumptions.

## Next route
Do not patch global `phase` again. Backport the already-verified Pure-Tetris v0.39 geometry mechanism:
- local one-hop relation waves;
- simultaneous local constraint relaxation;
- no global coordinate algebra;
- no traversal / visited / known state;
- iterate to field stability.

Then learn those local relation mappings only from ordinary visible gameplay transitions.