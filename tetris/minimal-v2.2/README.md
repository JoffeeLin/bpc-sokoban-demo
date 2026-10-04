# BPC Tetris Minimal v2.2

This frozen line continues the minimal 3x3-function approach.

## Main result

Five independent frozen rollout seeds produced:

- total compared ticks: **404,330**
- exact ticks: **404,330 / 404,330 = 100.000%**
- total lock events: **124,841**
- action failures: **Left=0, Right=0, Down=0, Rotate=0, Drop=0**
- real pivot injected into the model during rollout: **0**

The model does not require an explicit `Lock -> Clear -> Spawn` program sequence. In v2.2 the learned relaxation deliberately applies the Spawn relation before the Clear relation, opposite to the reference engine order, and repeatedly lets all relations act until the state reaches a fixed point. The final world still matches exactly.

## Important boundary

The current simplified rotation engine contains hidden pivot/orientation state. Exhaustive audit found 3,053 distinct visible active masks, of which 695 have more than one legal next ROT result. Therefore current pixels + ROT alone are not a complete Markov state for this engine.

From v2.0 onward, the true pivot is not supplied to BPC. A latent carrier is born from learned spawn experience and maintained internally through later actions.

See REPORT.md, RESULTS.txt and verification.txt.
