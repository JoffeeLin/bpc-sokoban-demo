# BPC Binary World-Fit v0.21–v0.26

Date: 2026-10-05
Goal: continue the strict game-fitting line: external input is a black/white screen plus an external operation carrier; all learned functions must live in one BPC probability medium. This phase specifically attacks family-specific learning stores, handwritten collision, handwritten line-clear propagation, distance-specific closure memory, whole-chain closure scanning, and lock-triggered downstream scheduling.

## v0.21 — direct shared-field learning (negative)
All observers wrote directly into the same `SharedField`; no family-specific learned parameter stores and no export/consolidation stage remained.

Initial result: 0/8000 long-rollout states.

Diagnosis: the learned relations themselves were correct, but Beta smoothing leaves a tiny positive probability for relations whose true amplitude should be zero. The recursive Action lifetime path treated e.g. ~0.0002 as a surviving carrier and executed an extra micro-step.

## v0.21b — centered binary amplitude (positive)
Use one generic binary readout for recurrent carrier amplitude:

`A = max(0, 2P - 1)`

No HardDrop/Life-specific threshold is introduced. This converts all `P<=0.5` evidence to zero positive wave and preserves positive evidence continuously.

Result:
- 8-seed rollout: 312,839 / 312,839 = 100%
- FIELD_OFF: 0/100

This promotes direct learning into the shared field.

## v0.22 — learned proposal × destination-state interference (positive)
Deleted the model-side rule equivalent to:

`if target occupied/outside -> blocked`

Geometry now only proposes destination waves. Each proposed target collides with a generic destination-state token:
- empty
- occupied
- physical boundary

Compatibility is learned from raw before/after micro-reality into the same SharedField. Multi-voxel rigid feasibility is the product/interference of all local compatibility waves. Spawn uses the same compatibility relation.

Learned representative compatibility:
- empty ≈ 0.9999
- occupied ≈ 0.0001
- boundary probability remains below 0.5 and therefore has zero positive centered amplitude

Formal 8-seed long rollout: all 312,839 / 312,839 exact (first six from the main run, final two from the remainder run).

Causal control: forcing occupied/boundary compatibility open reduces a 100-episode audit to ~65.99%.

Conclusion: handwritten Collision is not required.

## v0.23 — remove `sf_clear()/hole/movehole` propagation (negative stress result)
Deleted the dedicated clear executor and hole-propagation state. Closure consequence became a learned relation between a closure carrier and the relative vertical address of each occupied voxel, with outputs:
- persist
- reuse existing +1 down effect
- disappear

Ordinary rollout seeds remained exact, but explicit 1–4 line stress was only 361/10,000 = 3.61%.

Diagnosis: the implementation still learned a different function for every relative distance (`rdy=-1,-2,...`). The unseen extreme relation `rdy=-19` remained at 0.5, so top-to-bottom generalization failed. This is rejected as a final solution.

## v0.24 — distance-free closure relation reuse (positive)
Removed distance-specific closure functions. Physical address topology is compressed into only three generic relative relations:
- same address
- closure reachable below the current voxel
- closure reachable above the current voxel

The learned consequences are:
- same -> disappear
- closure below -> apply one previously learned +1 spatial effect
- closure above -> persist

Multiple closure waves superpose; their repeated +1 effect composes without a distance table or clear-specific propagator.

Results:
- 1/2/3/4 line stress: 10,000/10,000
- vertical-through-board non-clear: 2,500/2,500
- 8 independent long-rollout seeds: 312,839/312,839 exact

## v0.25 — one-sided local boundary wave (negative)
Replaced the whole-chain `boundary_seed_dir()` scanner with one-hop local propagation from a physical boundary.

Failure: LineClear stress 0/10,000, while ordinary rollout still appeared exact.

Diagnosis: if one row reached the opposite boundary, partially propagated edge waves from unrelated rows were incorrectly included in the same closure seed.

## v0.25b — opposite-boundary wave interference (current stable checkpoint)
No whole-chain scanner. Two ordinary local waves propagate independently from opposite physical boundaries through occupied one-hop relations. A closure carrier exists only where the two waves overlap/interfere.

This rejects incomplete boundary fragments without row labels or top-1 selection.

Results:
- 1/2/3/4 line stress: 10,000/10,000
- vertical non-clear: 2,500/2,500
- 8 long-rollout seeds: 312,839/312,839 exact
- O2/O3 representative full output diff: 0 bytes
- UBSan reduced smoke stderr: 0 bytes

At this checkpoint the model contains neither:
- handwritten occupied/outside collision decision;
- `clear_line()`/row detector;
- hole propagation;
- distance-specific clear shift table;
- whole-chain closure scanner.

Collision is learned proposal-state interference. Clear consequence is closure-wave × address relation × previously learned spatial effect.

## v0.26 — remove lock-triggered downstream scheduler (pilot positive, not promoted)
Deleted:

`if (lockamp > 0.5) downstream_relax(...)`

Spawn/closure relations remain eligible every micro-step; their amplitudes decide whether they have any effect.

Pilot:
- 1–4 line stress 10,000/10,000
- vertical negative 2,500/2,500
- first formal long-rollout seed exact

However computational cost increased substantially because closure relaxation is now evaluated on every ordinary tick. Full 8-seed freeze was not completed within the interactive execution budget. v0.26 is therefore purity-positive but efficiency-unfrozen; v0.25b remains the stable baseline.

## Current stable scientific description

`0/1 screen + self-born temporal trace + anonymous operation carrier`
`-> one shared probability field`
`-> reality-born geometry relations`
`-> learned proposal/destination interference`
`-> raw consequence routes`
`-> learned carrier lifetime`
`-> opposite-boundary local-wave interference`
`-> closure/address relation coupling`
`-> reuse of existing +1 spatial effect`
`-> sparse cross-region spawn relation`
`-> next 0/1 screen`

## Remaining major scaffolds
1. Key namespace still contains family labels (`GAUGE/ROUTE/LIFE/SPAWN/CLOSURE/...`) even though all values share one field.
2. Candidate observers are still family-specific during learning.
3. Binary screen is internally decomposed using a self-born temporal trace into transient vs persistent information instances; this is causal and necessary, but execution helpers still treat these identities differently.
4. Physical address topology is supplied by the lattice.
5. Preview region is physically located in a fixed visible side area.

Next target: remove relation-family namespaces and make function identity arise from collisions among primitive information/action/address waves, without sacrificing v0.25b's regression.