# BPC Tetris Minimal v3.9

Frozen checkpoint for the minimal Tetris line.

Main result: action dispatch, candidate-world selection, action-specific stay/lock logic, action lifetime rules, abstract move/stay/lock slots and pivot-specific rotation inference were successively removed while frozen Tetris rollout stayed exact.

Formal v3.9: **7,729 / 7,729 ticks exact** across five world/hash pairs.

Latent-history ablation: visible rotation accuracy falls from **100% to 31.88%** when the anonymous history anchor is zeroed. Under the current external rotation world, history is causally necessary, but its semantic interpretation as a hand-coded "pivot" is not.

The next strict experiment is to remove the supervised Spawn→latent target and test whether the process state can be born from real rotation residuals without top-1 search or object labels.
