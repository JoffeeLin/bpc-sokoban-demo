# BPC Tetris D1-Function v0.14b

This experiment continues the full-game Direct-Fit line without Lock/Spawn/Clear labels.

Pipeline:

```
Reality + action
  -> error-writeback Function Cube F1
  -> first full-frame prediction P1
  -> real future residual D1
  -> D1 accumulates a second function wave F2
  -> F2 × current raw reality
  -> next residual prediction
```

The key v0.14b change is a generic cross-field relation: the complete 417-bit visible state is mechanically partitioned into 27 anonymous 16-bit blocks. Every block participates equally with F2. The model is not told which block is preview, which event is Lock, or what Spawn means.

Formal result: Lock exact rises from 0% to about 42–48% across four independent training-world seeds. Turning the cross-field layer off returns Lock exact to 0% in every seed.

Clear remains 0%; full Tetris is not yet solved.

See REPORT.md and result_summary.csv.
