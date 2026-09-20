# GeneralBPC v7 Frozen Result

## Decision

**ADOPTED for the stated narrow claim.** One low-order relational probability
cube transferred direct control to all ten unseen layouts and passed all seven
pre-registered gates. This is not an AGI claim.

## Frozen protocol

- Candidate, thresholds, sources, training generator, holdout generator, and
  random seeds were hashed before the first completed holdout execution.
- 40 generated training maps plus five older fixed training maps.
- 10 new holdout maps, shortest solution distance `5–10`.
- Maximum internal-wall Jaccard among holdouts: `0.2941`.
- Maximum training–holdout internal-wall Jaccard: `0.5000`.
- 256 episodes per holdout and condition; 192 action limit.
- Evaluation learning disabled; persistent writes required to remain zero.

An initial preflight protocol incorrectly included the common outer border in
the wall-overlap report. It was invalidated before any holdout outcome existed,
the audit function was corrected, and the invalid preflight protocol was
retained at `artifacts/v7/preflight_invalid_protocol.json`. Maps, model design,
seeds, and gates did not change.

## Result

| Level | Primary | No joint | Change fused | Rotated | Uniform |
|---|---:|---:|---:|---:|---:|
| H1 | 55 | 15 | 52 | 44 | 29 |
| H2 | 213 | 80 | 216 | 5 | 28 |
| H3 | 36 | 42 | 34 | 0 | 30 |
| H4 | 19 | 10 | 16 | 0 | 23 |
| H5 | 18 | 15 | 19 | 43 | 11 |
| H6 | 138 | 92 | 130 | 73 | 55 |
| H7 | 256 | 240 | 256 | 2 | 92 |
| H8 | 139 | 14 | 141 | 0 | 15 |
| H9 | 145 | 112 | 125 | 24 | 87 |
| H10 | 79 | 32 | 88 | 7 | 19 |
| **Total** | **1098** | **652** | **1077** | **198** | **389** |
| **Rate** | **42.89%** | **25.47%** | **42.07%** | **7.73%** | **15.20%** |

Primary gains were `+27.70 pp` over uniform, `+35.16 pp` over action rotation,
and `+17.42 pp` over removing joint relations. The independent raw-change
channel did not causally improve choice (`−0.82 pp` when forced into it).

## Integrity

- Protocol SHA-256: `99831eb7e3050a65129daf3c1ccd9d288d2283fd04a591d76172b4244d45534e`
- Holdout-map SHA-256: `69b1924a88532f5b0d451691d05a254cb7c7fb9b60669ea02e7b62780bdd5601`
- Model SHA-256: `55554318fd2ce782627097a7dd50d18ec5ae820981e3e57d0b9ae5413387fb1e`
- Frozen persistent writes: `0`
- Full deterministic rerun: byte-identical result, trace, and model artifacts.
- Result artifact SHA-256: `1c5e5dd8dfb70872f50465303dbd3324c8f40d10f1e197b326a9993e3f05a48a`
- Trace artifact SHA-256: `1e3afc6e5bb58594f7e0c73cc9ccc710235466d4eed0d8fe11d2e49c42ee33eb`

The published video uses the first successful episode from each fixed 256-run
evaluation block. It does not search outside the pre-registered run for nicer
traces.

## Boundary

Supported: limited same-distribution cross-layout transfer by a non-neural,
non-planning, exact-count BPC controller.

Not supported: arbitrary Sokoban, arbitrary board sizes or box counts,
independent blind replication, cross-task general intelligence, or AGI.
