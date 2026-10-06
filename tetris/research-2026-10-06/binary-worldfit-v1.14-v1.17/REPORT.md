# BPC Binary World-Fit v1.14–v1.17 — Single-Field Scaffold Deletion

Date: 2026-10-06
Status: exact/mechanism-equivalence deletion series; full frozen Tetris promotion pending restoration of the archived v1.13 field/evaluator artifacts.

## Baseline

The last fully frozen checkpoint in the repository is v1.13, with the previously recorded 8-seed world regression remaining exact.

This series deliberately targets structures that duplicate or privilege information already present in the single SharedField.

## v1.14 — delete the special Gauge relation family

Old geometry used two relation forms:

- whole-object displacement: `kgauge(Action, dx,dy)`;
- local geometry: `kdirv(Action, input-relation, output-relation)`.

v1.14 deletes `kgauge`.

Whole-object displacement becomes the mapping of the ordinary self relation:

```
Action × relation(0,0) -> relation(dx,dy)
```

through the same `kdirv` field used by every local spatial relation.

A field migration is supplied.

Random multimodal equivalence audit:

```
GAUGE_TO_SELF_RELATION_EQUIV 1000000/1000000 = 100.000000%
```

Thus the superposed displacement readout is algebraically identical after key migration.

## v1.15 — delete named empty/persistent/process identities

The convenience identities:

```
w_empty()
w_persist()
w_process()
screen_proc()
screen_rest()
```

are removed from the core.

Every former use is replaced directly by the underlying physical representation:

```
cellwave(B,T,outside)
frame_bit × temporal_trace_bit
```

No field key changes are introduced by this deletion; it removes semantic vocabulary from the implementation while preserving the exact same BIT/relation encoding.

## v1.16 — delete the global ScopeCache

The learned action-coupled address scope was previously copied from SharedField into a persistent global `ScopeCache`.

v1.16 removes that second state.

Address participation is read directly from the single SharedField using the same noisy-OR over:

```
Action-port × screen-address × BIT
```

support relations.

Random exact equivalence:

```
SCOPE_CACHE_TO_DIRECT_EQUIV 3000000/3000000 = 100.000000%
maxerr = 0
```

The learned scope relation is retained; only its duplicate persistent cache is removed.

## v1.17 — delete the global SpawnRelCache

Spawn displacement amplitudes were also copied into a separate persistent global relation cache.

v1.17 removes it.

The same mature cross-screen relations are read directly from SharedField in the identical deterministic dy/dx order.  The historical 256-positive-relation capacity is reproduced exactly so this test changes storage topology, not inference semantics.

Random sparse/dense relation-field audit, including cases with more than 256 positive candidates:

```
SPAWN_CACHE_TO_DIRECT_EQUIV 200/200 = 100.000000%
maxerr = 0
```

Both the predicted spawn field and spawn compatibility carrier are bit-for-bit floating-point identical in the audit.

## Current interpretation

After this series, the candidate core no longer needs:

- a separate whole-object Gauge relation family;
- named empty/persistent/process identities;
- a persistent/global action-scope cache;
- a persistent/global Spawn relation cache.

The intended persistent cognitive state is therefore closer to:

```
one SharedField
+ current visible BIT field
+ temporal trace
+ external Action-port BIT
```

rather than one SharedField plus multiple copied helper fields.

## Important evidence boundary

The exact v1.13 frozen SharedField binary and independent evaluator were not archived alongside the v1.13 core/result files and are not available in the current session.

Therefore this series is **not** claimed as a new promoted full Tetris checkpoint yet.

What is established here:

- v1.14 key migration/readout equivalence;
- v1.15 definitional source equivalence;
- v1.16 cache/direct scope equivalence;
- v1.17 cache/direct Spawn equivalence.

What remains pending:

- migrate the exact frozen v1.13 field;
- rerun the full 8-seed Tetris regression;
- rerun autoplay line-clear verification;
- O2/O3/UBSan on the composed v1.17 candidate.

## Reproducibility rule going forward

Every future promoted checkpoint should archive together:

```
core
frozen field
field migration/provenance
independent evaluator
formal result
engineering audit
```

so purity deletion can always be independently rerun.
