# BPC Tetris Minimal v2.6 — One Shared Anonymous Probability Field

Date: 2026-10-04

## Goal

v2.3-v2.5 showed that frozen single-cell relations generalized exactly to exhaustive small-state tests, arbitrary unseen polyominoes, and 1..12 participating cells. v2.6 removes the remaining separate learned parameter banks.

The question is:

> Can Move / Rotate / Spawn / Lock / Row propagation coexist in one fixed anonymous probability medium without any new Tetris-specific training?

## Mechanism

There is one learned storage object only:

`UField { z[], o[] }`

Every experience writes a Beta-style zero/one residual into the same field. Addresses use only physical tokens: external action/carrier identity, raw source/destination channel identity, and physical coordinates. There is no relation-family namespace and no separate Move/Rot/Spawn/Prop parameter array.

Direct hashing deliberately permits interference.

## Capacity result

Frozen arbitrary 1..8-cell polyomino rollout:

| shared field | result |
|---:|---:|
| 2^10 | 0% |
| 2^12 | 0% |
| 2^14 | 0% |
| 2^16 | 2.91% |
| 2^17 | 0% |
| 2^18 | 0% |
| 2^19 | 99.60% |
| 2^20 | 100% representative |
| 2^21 | 100% representative |

This is a shared-medium interference threshold, not a smooth task-learning curve.

## Random-address audit

2^20 is not robust:

- salt 0: 100%
- salt 1: 41.66%
- salt 17: 99.80%
- salt 12345: 100%
- salt 987654321: 100%

The failing salt remains weak at 2^21 (44.65%) but recovers at 2^22.

At 2^22 all five tested address salts are exact.

## Cross-seed reproduction

At 2^22, three independent address salts × three independent rollout seeds:

- compared ticks: **40,653**
- exact: **40,653 / 40,653 = 100%**
- first failure: none
- Left / Right / Down / Rotate / Hard Drop: all 100%

## Collision audit

The frozen model has about **7,070 conceptual relation addresses** before hashing.

Collision slots across five representative salts:

- 2^18: 76..102
- 2^19: 33..50
- 2^20: 18..26
- 2^21: 6..12
- 2^22: 3..6

Collision location matters more than raw count: some smaller-field salts hit critical rotation/spawn relations and collapse the global closure.

## Engineering verification

- C11 `-Wall -Wextra -Werror`: PASS
- O2/O3 representative output: byte-identical
- SHA-256: `762bed5978f1e94a0103c49c0b0a0364d9e4fffd0c9c35a4fa6ba2f16e2d1d28`
- O2/O3 diff: 0 bytes
- UBSan: exit 0
- UBSan stderr: 0 bytes

## Strongest supported conclusion

`minimal physical experiences -> multiple reusable relations -> one shared anonymous probability medium -> exact compositional rollout`

Separate learned parameter banks are therefore not necessary for this controlled Tetris closure.

## Boundary

This is still not a fully pure BPC core. Training still presents micro-experience families separately; address descriptors are hand-designed from physical channels/actions/coordinates; inference still has distinct procedures for translation, rotation, channel coupling, spawn superposition, and row propagation; the latent rotation carrier data structure remains.

The next frontier is to unify how reality becomes relation addresses and residual writes.
