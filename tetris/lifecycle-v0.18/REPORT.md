# BPC Tetris v0.18 — Function lifecycle result

## Question

v0.17 showed that a hierarchy

```
Reality -> F1 -> D1 -> F2 -> Cube3 -> D2
```

can make complete Lock frames emerge from zero without Lock/Spawn/Preview labels, but D2 performance rose and then declined with continued writeback.

v0.18 tests whether task-independent fast/slow residual states solve that long-run interference.

## v0.18A: linear fast-to-mature dynamics

Each D2 address uses:

```
r <- rho_fast * r + eta * residual
m <- rho_slow * m + mu * r
readout = m + gamma * r
```

Parameters:
- rho_fast = 0.70
- rho_slow = 0.999
- eta = 0.30
- mu = 0.020
- gamma = 0.25

### Seed-0 long curve

| D2 experience | Frame exact | Lock full | Kr | Km |
|---:|---:|---:|---:|---:|
| 20k | 79.667% | 6.977% | 12,994 | 2,618 |
| 40k | 80.000% | 11.628% | 12,309 | 6,071 |
| 60k | 79.750% | 12.791% | 11,591 | 9,001 |
| 100k | 80.000% | 12.791% | 11,481 | 13,691 |
| 150k | 80.000% | 12.791% | 11,561 | 17,532 |
| 200k | 80.333% | 13.953% | 11,311 | 19,725 |

The visible collapse after 40k is removed, but Km keeps growing while Lock nearly plateaus.

## Three-seed causal reproduction

All final ablations use the same evaluation stream per seed.

| seed | Frame | Lock | Slow-off Lock | Slow-shift Lock | Slow-flip Lock | Mature-only Lock | Km |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 81.950% | 12.458% | 0.000% | 0.000% | 0.000% | 12.458% | 19,725 |
| 1 | 79.850% | 11.881% | 0.000% | 0.000% | 0.000% | 11.881% | 16,583 |
| 2 | 82.225% | 13.149% | 0.692% | 0.000% | 0.000% | 13.495% | 17,995 |
| mean | 81.342% | 12.496% | 0.231% | 0.000% | 0.000% | 12.611% | 18,101 |

This supports a real causal chain from fast residual activity into a mature state. The mature state is not just extra capacity.

## Direct-slow control

A single slow residual state with no fast-to-mature transfer reached:

| experience | Frame | Lock |
|---:|---:|---:|
| 20k | 81.850% | 15.436% |
| 40k | 82.250% | 18.121% |
| 60k | 82.350% | 17.450% |
| 100k | 82.300% | 19.463% |

The execution window prevented a 150k/200k endpoint for this control, so no long-run superiority claim is made. But through 100k, two-timescale maturity is not better than direct slow writeback.

## v0.18B: coherent-only maturity

Replacing linear promotion by:

```
m <- m + mu * r * abs(r)
```

compressed Km to 158 at 20k and 941 at 200k, but complete Lock fell to approximately zero. Thus lower K alone is not success; rare important functions can be pruned.

## v0.18C: true global lazy decay

Each voxel additionally receives a last-tick timestamp and is read as:

```
r(t) = r(t0) * rho_fast^(t-t0)
m(t) = m(t0) * rho_slow^(t-t0)
```

At seed0 / 200k:
- Kr = 4,072
- Km = 16,759
- same-stream Lock = 9.677%
- slow-off / slow-shift / slow-flip Lock = 0%

Global death reduces short-term state count substantially but still does not compress the mature state enough, and Lock is lower.

## Boundary

v0.18 therefore gives **partial positive evidence**:
- mature state is causally real;
- long training no longer shows the same simple 40k collapse;
- mature-only readout preserves nearly all Lock ability.

But the stronger hypothesis fails:
- Km does not stabilize;
- G does not keep rising with K;
- direct-slow is at least as strong through 100k;
- strong compression destroys rare-stage ability;
- global decay alone does not solve mature-state growth;
- complete Clear/GameOver remain without positive evidence.

v0.18 should therefore **not replace v0.17 as the best core**.

## New theoretical target

The next candidate should not tune rho/mu further. Maturity should be grounded by future reuse:

```
residual relation is born
-> reality calls it again
-> did using it reduce later real residual?
-> repeated residual reduction -> mature
-> no reusable future effect -> decay/death
```

In short:

**Function maturity should be consequence-grounded, not time-grounded only.**
