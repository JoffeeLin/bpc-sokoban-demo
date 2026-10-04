# BPC Query-Trace Residual Loop v0.1 / v0.2

Date: 2026-10-04

## Goal
Test the missing lower half of voxel-accumulated function theory:

`accumulated function -> query participation -> prediction -> real residual -> participation-trace writeback -> changed function`

and then:

`mature coarse function -> persistent unexplained residual -> finer relation birth -> new relation re-enters query`.

## World
Raw query tokens: anonymous action A0/A1, context bit C0/C1, and two random nuisance bits. Future effect is one of {-2,-1,0,+1,+2}.

Phase I reality:
- A0 -> +1
- A1 -> -1

Phase II changes only one conjunction:
- A0 & C1 -> +2

No semantic exception label is supplied to the model.

## v0.1
The query wave is continuous interference of the future-effect waves of all active raw tokens. The actual active-token trace is retained. Reality residual y-p is written through that trace.

Three-seed final results after 2000 Phase-II experiences:
- correct TRACE writeback: 100%, 100%, 100%
- shifted trace addresses: 25.033%, 24.367%, 25.567%
- whole-field equal writeback: 74.433%, 74.733%, 74.533%
- no writeback: 75.333%, 74.733%, 74.533%

A targeted non-participation audit gives exactly zero drift for functions absent from the query trace. Negative finding: directly updating the mature shared coarse A0 relation can still contaminate the unchanged A0,C0 condition.

## v0.2
Phase-I coarse action functions are first matured. During Phase II all unordered pairs among the currently active raw tokens are equally eligible anonymous candidate supports. Persistent unexplained residual accumulates per pair. No top-1 candidate is selected. A pair becomes active only after repeated coherent residual evidence.

At threshold 1.0, 5/5 seeds mature exactly one relation:
- A0 * C1

After birth all four A/C quadrants are 100%.

Controls:
- no relation birth: 74.900%..75.650%, A0,C1 remains 0%
- mature pair address shift: about 49.8%..51.2%

## Threshold sweep
- 0.80: task solved but 4/5 seeds also birth redundant nuisance relations
- 0.90: 1/5 seed births one redundant nuisance relation
- 1.00: 5/5 birth exactly A0*C1
- 1.10: 5/5 birth exactly A0*C1
- 1.20: 5/5 birth exactly A0*C1

## Interpretation
v0.1 supports participation traces as the causal carrier for Reality Residual. v0.2 supports a second step: persistent residual left by a mature coarse function can form a finer relation that re-enters later queries.

This is not yet a fully pure BPC core. The allowed pair candidate space and the maturity threshold are still supplied bottom-level scaffolds, and v0.2 temporarily freezes the coarse function to isolate the birth mechanism.

The next experiment should replace the fixed maturity threshold with consequence-grounded future reuse, then remove the predeclared pair candidate space.
