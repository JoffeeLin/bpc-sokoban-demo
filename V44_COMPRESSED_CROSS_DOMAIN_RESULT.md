# BPC v0.44 compressed cross-domain result

Status: **FROZEN PASS**. This was the first execution of preregistration commit
`9064b48`. All three source hashes matched, 76/76 tests passed before execution,
and both tracks passed every fixed gate with zero evaluation writes.

## One compact core, two physical domains

| Frozen holdout | Sokoban physics | Causal particle lattice |
|---|---:|---:|
| full-context novelty | 40.28% | 55.90% |
| all-bit Brier | 0.006686 | 0.012766 |
| changed-bit Brier | 0.184916 | 0.040518 |
| unseen-context changed-bit Brier | 0.231435 | 0.041704 |
| active cells | 10,885 | 14,000 |
| unique raw training states | 2,706 | 3,707 |

On unseen-context changed bits, the Sokoban-physics candidate improved over
action removal by 29.37% and action rotation by 57.18%. The causal-lattice
candidate improved over action removal by 86.35%, action rotation by 94.93%,
and phase-flipped input by 95.40%.

Removing exact 3x3 context storage reduced occupancy from the predecessor's
133,373 to 10,885 cells on Sokoban physics (91.84% lower), and from 649,450 to
14,000 on causal lattice (97.84% lower). Both raw-state/active-cell compression
boundaries and the stronger quarter-occupancy gates passed.

## What passed

- fresh initial worlds excluded every prior development, diagnostic and frozen
  set;
- the same task-independent non-neural core and fixed `2^20` capacity were used
  in both domains, with fresh probability state per domain;
- high fractions of full local contexts were unseen;
- action removal and action rotation failed causally;
- flipping the physical terrain bit failed on the second domain;
- action renaming remained exactly equivariant;
- evaluation wrote nothing and left every model digest unchanged.

## Boundary

This establishes a compact pure-BPC local physical predictor that forms useful
probabilities under unseen composition in two different simulators. It does
**not** establish goal-directed behavior, Sokoban solving, cross-domain weight
transfer, open-ended world modeling, or AGI. Those remain separate experiments.
