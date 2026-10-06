# BPC Binary World-Fit v1.14–v1.24 — scaffold equivalence deletion report

Date: 2026-10-06

## Evidence status
The formally frozen v1.13 report records 312,839/312,839 exact rollout, but the currently recoverable v1.13 source artifact does not match the report's frozen source SHA-256. Therefore this batch is intentionally classified as **strict old-vs-new equivalence evidence**, not a promoted 8-seed world checkpoint. No 8-seed claim is made for this batch until the exact frozen source/field pair is restored.

## v1.14 — Gauge becomes an ordinary self-relation mapping
The separate gauge concept can be represented as the ordinary relation map `self relation (0,0) -> output relation (dx,dy)` with identical amplitudes.
Result: 1,000,000/1,000,000 exact in the standalone equivalence experiment.

## v1.16 — Remove ScopeCache as a stored intermediate field
The action-address structural support amplitude is exactly the direct product-complement of the underlying action/address support relations. The cache is only a performance memoization layer, not a required cognitive object.
Result: 3,000,000/3,000,000 exact, max error 0.

## v1.17 — Remove SpawnRelCache
Spawn relation cache entries can be read directly from the relation field without changing proposal or compatibility-carrier numerics.
Result: 200/200 randomized relation fields exact, max error 0.

## v1.18 — Closure uses generic spatial relation geometry
The vertical-special Closure consequence executor can be expressed as a generic spatial-relation executor. Because the frozen support is zero for unsupported non-vertical effects, the generic operator collapses exactly to the previous behavior.
Result: 20,000/20,000 exact.

## v1.19 — Combined equivalence
The above deletion ideas were exercised together in one randomized harness:
- gauge/self-relation: 300,000/300,000;
- scope direct support: 800,000/800,000;
- Spawn direct field read: 120/120;
- generic Closure geometry: 8,000/8,000.
All exact.

## v1.20 — Spawn becomes generic relation scatter + compatibility interference
The Spawn-specific lower-level projector is unnecessary. Its exact computation is:
`source BIT x relation wave -> target proposal`, followed by ordinary target compatibility interference.
Result: 300/300 randomized sparse fields exact, max error 0.

## v1.21 — Closure boundary propagation becomes generic relation propagation
The Closure-specific one-side propagation helper is equivalent to:
`relation-boundary seed -> generic one-hop relation propagation -> re-entry to fixed point`.
Opposite-side closure is simply interference of the two propagated waves.
Result: 200,000/200,000 exact.

## v1.22 — Remove materialized process/rest states
`process=B*T` and `rest=B*(1-T)` do not need to be materialized as separate world-state arrays. Proposal and commit algebra can operate directly on B/T bits.
Result: 500,000/500,000 random states exact.

## v1.23 — Replace min-coordinate anchor selector with a physical boundary wave
The reference world's bounding-box min anchor does not require a `min(x),min(y)` selector. A carrier emitted from the left/top physical screen boundary and propagated until its first occupancy interference produces the same anchor.
Result: 1,000,000/1,000,000 random objects exact.
This preserves the reference rotation semantics while removing a discrete coordinate winner.

## v1.24 — One relation operator for Spawn and Closure propagation
A single `relation_apply` operator is sufficient:
- Spawn: one application of relation scatter;
- Closure reachability: the same operator re-enters until fixed point.
Results:
- Spawn: 50,000/50,000 exact;
- Closure re-entry: 100,000/100,000 exact.

## Engineering audit
- C11 `-Wall -Wextra -Werror -pedantic`: pass for v1.19–v1.24.
- O2/O3 result diff: 0 for v1.19–v1.24.
- UBSan: clean; v1.22–v1.24 use reduced-smoke sample counts with identical equations.

## Purity implication
This batch supports deleting the following as necessary cognitive structures:
- separate Gauge family;
- stored ScopeCache;
- stored SpawnRelCache;
- Spawn-specific projection physics;
- Closure-specific propagation physics;
- materialized process/rest world states;
- min-coordinate anchor selector.

The lower-level candidate medium can be stated more compactly as:
`BIT + RELATION + local propagation + interference + re-entry + residual field`.

## Next step
Restore the exact frozen source/field pair and merge these algebraically equivalent deletions into the full 8-seed evaluator. In parallel, continue equivalence reduction on proposal generation and output commit without making unsupported capability claims.