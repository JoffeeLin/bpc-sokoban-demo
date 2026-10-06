# BPC Binary World-Fit v1.12–v1.13 — execution scaffold deletion

Date: 2026-10-06
Baseline: v1.11, 312,839/312,839 exact.

## v1.12 — unified downstream commit
Deleted separate `spawned state` and `cleared state` update procedures. Spawn-related process proposals and Closure-related persistent proposals are now computed from the same pre-state and committed once into the same B/T output field. No separate intermediate world states remain in downstream execution.

Result: 8-seed rollout 312,839/312,839 exact.

## v1.13 — fullscreen B/T commit
Deleted the region branch that treated learned action-scope pixels with process/rest composition while passing other screen pixels through a separate path. All 15x20 pixels now use the same B/T composition law. Closure participation remains controlled by its learned relation/scope amplitudes, not by the commit operator.

Result: 8-seed rollout 312,839/312,839 exact.

Engineering audit for v1.13:
- GCC C11 O2 `-Wall -Wextra -Werror -pedantic`: PASS
- GCC C11 O3 same flags: PASS
- O2/O3 full output diff: 0 bytes
- UBSan reduced smoke stderr: 0 bytes
- source SHA-256: 30c60001c935352ad5a811710e6cf20addf37c106ca7d48ebdacd83fec1288f0
- result SHA-256: 57e776a34ca448baf3f49d3b526de50ab33c35ecefbcca5a6094758a431c70fe

Current frontier after v1.13:
`binary visible screen + self-born temporal trace + action-port bit`
`-> BIT + RELATION field`
`-> learned structural support`
`-> local relation geometry`
`-> continuous compatibility / action lifetime / downstream carrier`
`-> continuous closure seed and pair context`
`-> simultaneous downstream proposals`
`-> one fullscreen B/T commit`

Remaining high-value scaffolds:
1. Geometry still uses a minimum-coordinate anchor after local relation relaxation; naive centroid replacement is invalid for the current reference rotation.
2. Spawn and Closure still have different lower-level proposal generators, even though their proposals share one medium and one commit.
3. Learned action-scope remains a derived structural-support field used as physical topology.
4. Full 15x20 screen size and five action ports remain physical substrate assumptions.