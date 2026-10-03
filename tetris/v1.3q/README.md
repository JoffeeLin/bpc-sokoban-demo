# BPC Tetris v1.3q

Anonymous-region relation birth from residual reality.

This directory reuses the unchanged support files in `../v1.2/`.

Reproduce one formal seed:

```bash
gcc -O2 -std=c11 -Wall -Wextra -Werror -I../v1.2 bpc_tetris_v1_3q_strict_probability_birth.c -lm -o v13q
./v13q 15000 20000 5000 1500 400 0
```

Arguments: `base local candidate_train candidate_validation eval seed`.

Formal result: 3 independent seeds, exactly 3 strong mature relations per seed, average terminal full 50.17%, recursive final full 17.92%. Disabling/flipping/shifting the mature relations drives terminal full to 0%.

See `REPORT.md` and `result_summary_v1_3q.csv`.
