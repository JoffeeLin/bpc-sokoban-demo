# BPC Tetris Residual Hierarchy v0.17

Complete-game Direct-Fit experiment for the residual hierarchy:

```
Reality -> F1 -> prediction -> D1 -> F2 -> Cube3 -> D2 -> higher-order closure
```

No Lock / Spawn / Clear labels are used by learning. Event flags are external audit only.

Frozen 3-seed result at D2=40k:
- pre-D2 full-frame mean: 79.522%
- D2 full-frame mean: 80.256%
- complete Lock frame mean: 17.303% (pre-D2: 0%)
- F2-zero Lock: 0% on all three seeds

Engineering:
- C11 -Wall -Wextra -Werror PASS
- O2/O3 representative output diff = 0
- UBSan stderr = 0

See REPORT.md and result_summary.csv.
