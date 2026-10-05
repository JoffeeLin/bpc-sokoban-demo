# BPC Binary World-Fit v1.03–v1.11 — scaffold deletion report

Date: 2026-10-06
Stable starting checkpoint: v1.01 fixed-point execution, 312,839/312,839 exact.

## v1.03 — remove global scope max-normalization (positive)
The learned screen participation scope previously computed all address amplitudes and divided by the global maximum. v1.03 deletes that global normalization; every address uses only its own action-coupled structural support. 8-seed rollout remains 312,839/312,839 exact.

## v1.04 — remove hard-coded cardinal-only Closure neighborhood (positive)
Closure no longer pre-filters local relations with `abs(dx)+abs(dy)==1`. All eight one-hop relations participate; the field itself suppresses immature directions. 8-seed rollout remains exact.

## v1.05 — zero-mean/centroid Geometry anchor (negative)
Attempted to delete the minimum-x/minimum-y object anchor and place the relaxed relation shape using centroid/zero-mean gauge only. Result: 61,460/69,295 = 88.69%. Every first divergence was Rotate. This rejects the naive assumption that the controlled reference rotation preserves centroid gauge.

## v1.06 — remove Closure direction candidate extractor (positive)
Deleted the helper that first scans the current state to collect which local directions exist. All eight local relation waves are always eligible; field amplitude alone decides participation. 8-seed rollout remains 312,839/312,839.

## v1.07 — remove direct global y-order comparison in Closure (positive)
Deleted `cy>sy/cy<sy` relation classification. A source instance now walks ordinary local one-hop relation waves in both vertical directions and records whichever closure waves are actually reached. 8-seed rollout remains exact.

## v1.08 — remove Closure output winner / `else` branch (positive)
Survival and shift/birth consequences now superpose independently. The program no longer gives shift priority over survival. 8-seed rollout remains exact.

## v1.09 — continuous Closure seed amplitude (positive)
Deleted the hidden `closure amplitude > 0 -> full-strength seed` conversion. Opposite-boundary reachability is still structural, but each reached seed carries the actual closure amplitude into death/birth consequences. 8-seed rollout remains exact.

## v1.10 — continuous pair-context participation (positive)
Deleted the hidden `two relation types appeared -> full pair gate` conversion. Each relation keeps its actual participation amplitude; pair inhibition is weighted by the product of those amplitudes. 8-seed rollout remains exact.

## v1.11 — remove Spawn destination action-scope gate (positive)
Spawn cross-screen relations no longer require the destination to pass `scope>0` before writing a candidate. Relation topology itself determines the destination; only the physical 15x20 screen boundary remains. 8-seed rollout remains exact.

## v1.11 formal result
- 8-seed rollout: 312,839 / 312,839 = 100%
- O2/O3 full output diff: 0 bytes
- UBSan reduced smoke stderr: 0 bytes
- source SHA-256: d18de2091c89e6c9d83a73a0e19f859c3272cc1d3b5df5df32648464c4bd6a63
- result SHA-256: 76606e7935c08074133a20b61d23144bc40acde6f44eec63426da54b46706339

## Current remaining structural scaffolds
1. Geometry still uses a minimum-coordinate anchor after local relation relaxation; naive centroid removal is disproven by v1.05.
2. Spawn and Closure remain separate execution helpers even though both live in the same BIT+RELATION field.
3. Learned action-coupled screen scope remains a derived structural support field and is still used by Geometry/Closure compatibility.
4. Full visible screen dimensions (15x20) and action-port count remain physical substrate assumptions.
5. Final binary readout still thresholds continuous amplitudes at the physical pixel boundary.