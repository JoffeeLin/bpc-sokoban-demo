# BPC Query-Trace Consequence Lifecycle v0.3d

Date: 2026-10-04

The byte-identical source and results are maintained once in the integrated core:
[C source](../bpc-query-function-core-v0.1/src/bpc_consequence_lifecycle_v03d.c) and
[frozen results](../bpc-query-function-core-v0.1/results/v03d_RESULTS.csv).
This directory retains the original report and [verification record](VERIFICATION.txt).

## Result

This experiment closes a missing loop in voxel-accumulated function theory:

`accumulated function -> query participation -> prediction -> real residual -> future-use utility -> participation -> query-error writeback -> changed function`

and then, after reality returns to the old rule:

`future utility disappears -> relation participation decays -> death`.

The world contains anonymous action A0/A1, raw context C0/C1, and two random nuisance bits. Phase I is A0->+1, A1->-1. Phase II changes only A0&C1->+2. Phase III restores the original world.

## Development negatives

- v0.3a: evaluating utility inside a redundant ensemble caused many correlated nuisance relations to claim the same residual.
- v0.3b: standalone predictive utility still gave positive value to coarse nuisance correlates.
- v0.3c: finite query-energy conservation isolated the correct relation A0*C1, but its effect amplitude was too weak because query error was not yet written back into the participating relation itself.

## v0.3d mechanism

There is no binary mature flag and no residual-norm maturity threshold.

1. A weak candidate receives a small task-independent counterfactual probe.
2. A participating relation is judged by removal from the conserved relation ensemble.
3. Future real consequence improvement is accumulated as continuous utility.
4. Simultaneous relations share finite effect energy, avoiding duplicate residual amplification.
5. After utility determines actual participation, the current query error is written only through relations that truly participated, proportional to participation strength.
6. When later reality no longer benefits from a relation, utility vanishes and participation decays to zero.

## Five-seed frozen result

Normal mechanism:

| seed | Phase-II final | effective K after adaptation | restored final | effective K after restore |
|---:|---:|---:|---:|---:|
| 0 | 100% | 1 | 100% | 0 |
| 1 | 100% | 1 | 100% | 0 |
| 2 | 100% | 1 | 100% | 0 |
| 3 | 100% | 1 | 100% | 0 |
| 4 | 100% | 1 | 100% | 0 |

The only effective relation during adaptation is A0*C1.

Most seeds reach 100% by 100 new real experiences; two reach it by 50.

When Phase III restores the original world, A0*C1 loses future utility and dies while prediction remains 100%.

## Controls

- utility OFF: Phase II remains about 74-77%; the new conditional rule is not learned.
- utility reversed: also remains about 74-77%.
- shifted utility addresses can eventually recover 100% accuracy, but by proliferating redundant relations.

Representative shifted-utility seed0:
- Phase-II final = 100%
- effective K after adaptation = 8
- after reality restoration effective K = 16, with 7 still above the stronger diagnostic cut.

Therefore accuracy alone is insufficient. Correct trace grounding is distinguished by the same G with much lower K and clean death.

This directly connects query-residual learning to the BPC criterion:

`G up, K/G down`.

## Parameter robustness

Representative sweep:
- utility_scale = 15,20,30,40
- trace_lr = 0.20,0.35,0.50

Across 12 combinations x 5 seeds:
- Phase II final = 100%
- restored reality final = 100%

Representative low/mid/high settings keep exactly one effective relation during adaptation.

## Boundary

This is not yet a fully pure BPC core.

Remaining scaffolds:
1. the support family is still predeclared as all pair combinations among active raw tokens;
2. pair existence is therefore still an allowed algebra supplied by the program;
3. coarse Phase-I functions are frozen to isolate fine-function dynamics;
4. finite query-energy normalization is hand-specified bottom physics;
5. this is a minimal synthetic world.

The fixed maturity threshold from v0.2 has been removed. The next frontier is support topology itself: persistent residual plus actual query traces should grow a new support coordinate locally without a predeclared pair/triple candidate table.
