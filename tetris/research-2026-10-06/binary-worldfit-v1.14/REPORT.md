# BPC Binary World-Fit v1.14 — Gauge as Ordinary Self-Relation Mapping

Date: 2026-10-06
Status: mechanism-equivalence deletion candidate; NOT yet promoted as a new full Tetris checkpoint.

## Goal

Delete the remaining special Geometry gauge relation family.

Before v1.14, geometry used two relation mechanisms:

1. `kgauge(Action, dx,dy)` for whole-object displacement;
2. `kdirv(Action, input-relation, output-relation)` for local shape relation mapping.

This means translation still had a privileged relation type even though local geometry had already been unified.

## v1.14 change

Delete `kgauge`.

Whole-object displacement is represented as the mapping of the ordinary self relation:

```
Action × relation(0,0) -> relation(dx,dy)
```

using the same `kdirv` field as every local spatial relation.

Thus Geometry now has one relation form:

```
Action × input spatial relation -> output spatial relation
```

instead of separate Gauge + Direction-Map mechanisms.

A field migration copies each old gauge probability to:

```
old: wavecollide(Action, relation(dx,dy))
new: Action × relation(0,0) × relation(dx,dy)
```

and removes the old gauge keys.

## Mechanism-equivalence test

A standalone exact-equivalence audit generated 1,000,000 random multimodal probability fields, including absent, sub-threshold, positive, and competing displacement waves.

Result:

```
GAUGE_TO_SELF_RELATION_EQUIV 1000000/1000000 = 100.000000%
```

The weighted superposed displacement readout is algebraically identical after the key migration.

Source SHA-256 of the equivalence audit:

`2ae3b53b38c3cdb361536b1f4c828bd426b0f96d92aebfd9b4b245b5849618ea`

## Scientific interpretation

This supports deleting a privileged whole-object Gauge mechanism.

Translation and rotation/shape geometry can now be represented by the same physical relation law:

```
Action wave
× current spatial relation wave
-> future spatial relation wave
```

The special case of whole-object displacement is simply the self relation `(0,0)`.

This is closer to the target BPC principle that a function is identified by participating waves, not by a researcher-provided function family.

## Evidence boundary

The current repository archive contains the v1.13 frozen core and formal results, but not the exact v1.13 frozen SharedField binary and evaluator artifacts needed to rerun the full 8-seed Tetris regression in this session.

Therefore v1.14 is deliberately classified as:

- **mechanism-equivalence positive**;
- **field migration specified**;
- **full frozen world regression pending artifact restoration**.

It is NOT yet claimed as a promoted replacement for v1.13.

## Reproducibility correction

Future promoted checkpoints should archive together:

```
core source
frozen field
field migration/provenance
independent evaluator
formal results
engineering audit
```

so subsequent scaffold deletions can always rerun the complete frozen regression without depending on transient session files.
