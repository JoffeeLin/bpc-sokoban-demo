# BPC Binary World-Fit v1.18 — Generic Closure Relation/Effect Geometry

Date: 2026-10-06
Status: mechanism-equivalence positive; full frozen Tetris promotion pending restoration of the archived frozen field/evaluator artifacts.

## Goal

Remove a real remaining Tetris-shaped execution scaffold from Closure.

Before v1.18, Closure execution had already removed row labels and clear-line procedures, but consequence application still assumed:

- source-to-closure relations are only vertical/same-column;
- birth consequence is only the fixed local effect `(0,+1)`.

That means the executor still knew the geometric form of line-clear relocation.

## v1.18 change

Closure now treats both sides generically.

### Source -> closure relation

Instead of only:

```
same
up
down
```

the executor scans every local ray relation:

```
(dx,dy) in {-1,0,1}^2 \ {(0,0)}
```

and only relations with mature SharedField consequence couplings have any effect.

### Closure -> consequence effect

Instead of a fixed birth effect:

```
(0,+1) -> persistent BIT
```

the executor scans every local output effect relation.

For each:

```
source-to-closure relation
× local effect relation
-> consequence amplitude
```

is read from the same SharedField.

Relation-of-relation pair inhibition is also keyed by the actual effect relation rather than implicitly assuming downward birth.

## Existing field compatibility

The existing frozen evidence has positive consequence support only for the previously learned vertical/downward relations.

Therefore the old line-clear behavior is expected to be a special case of the new generic executor:

```
generic relation/effect field
-> only vertical/down couplings non-zero
-> identical old behavior
```

No new Tetris rule or new positive relation is inserted.

## Equivalence audit

A standalone comparison generated 20,000 randomized multi-line closure states with randomized:

- carrier amplitude;
- closure seed amplitudes;
- death couplings;
- birth couplings;
- joint couplings;
- pair gates.

The generic executor was allowed all 8 local source-relation directions and all local effect directions, while non-vertical field support was zero as in the frozen evidence.

Result:

```
VERTICAL_TO_GENERIC_CLOSURE_EQUIV 20000/20000 = 100.000000%
```

The first implementation exposed one important mistake: multiple closure instances along the same relation ray must remain independent function instances; only relation-presence amplitude may be aggregated for pair context. After preserving that distinction, exact equivalence was restored.

Equivalence source SHA-256:

`587a104e5f3e67fcca8921f4965037cf9a98a0cc64370fc3429c1bc2f7fa981d`

## Scientific interpretation

This deletes another hidden piece of Tetris knowledge.

The core no longer has to encode:

```
line clear -> search same column -> move downward
```

Instead it can express:

```
closure-information instance
× spatial relation to another information instance
× candidate local consequence relation
-> field amplitude
```

The observed Tetris downward relocation is then only one learned relation pattern among possible spatial consequences.

## Evidence boundary

As with v1.14-v1.17, the current repository does not include the exact frozen SharedField binary and evaluator corresponding to the archived full v1.13 regression.

Therefore v1.18 is not yet promoted over the last fully frozen checkpoint.

Established:
- generic closure execution source implemented;
- old vertical executor recovered exactly under current field support in 20,000 randomized audits.

Pending:
- frozen field migration/restoration;
- full 8-seed world regression;
- autoplay verification;
- O2/O3 and UBSan on the composed candidate.
