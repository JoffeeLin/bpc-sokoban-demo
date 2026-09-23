# v0.49 residual-activity pilot log

All runs below used pilot seeds `490001` / `490101`, which are permanently
excluded from development and frozen evidence.  Thresholds were not yet fixed;
these runs only debugged the task-independent physical law and the intervention
definitions.

| Iteration | Candidate | Zero | Flip | Shift | Memoryless | Finding |
|---|---:|---:|---:|---:|---:|---|
| equal write through every active action | 35.00% | 21.88% | 56.25% | 40.63% | 21.88% | ordinary non-closure steps dominated the activity field |
| residual-weighted, every active action | 54.38% | 19.38% | 63.75% | 40.00% | 19.38% | closure residual still leaked into non-causal action phases |
| residual-weighted, current action phase only | 81.25% | 22.50% | 83.75% | 23.13% | 22.50% | action-coordinate rotation was not a polarity flip |
| naive `1-p` polarity | 81.25% | 22.50% | 85.63% | 23.13% | 22.50% | both values could lie below the instantaneous baseline |
| reflect activity displacement around baseline | **81.25%** | **22.50%** | **30.63%** | **23.13%** | **22.50%** | candidate finally has the required intervention ordering |

The final pilot used unseen decorations and longer closure lengths `7–10`
after random-action experience only on lengths `3–6`.  Per-cue candidate rates
were 70.0%, 90.0%, 77.5% and 87.5%.  This authorizes preregistration; it is not
held-out evidence and is not a Sokoban or AGI result.
