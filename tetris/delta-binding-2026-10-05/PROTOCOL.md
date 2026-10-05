# Current-carrier binding — phase 2 frozen C protocol

Source: `b63bea76b2575ff90f165ca27ee247f76e42730e`,
`tetris/support-joint-2026-10-05`. The successful 373-coupling game remains
the benchmark. Previous experiment files and fields are not overwritten.

Phase 1's complete protocol and source snapshot are preserved in `phase1/`.
Its four variants had identical raw-prediction fingerprints, occupied cell
counts and self-prefix metrics across all three training seeds. The reason
is exact: symmetric XOR history obeys `current = XOR(all six port traces)`
after reset, every real action and external observation. Omitting the explicit
current bit from a local key therefore leaves an invertible query. Encoding
next bits as XOR changes remains a bit-complement reparameterization.
No learning mechanism was deleted in that phase. Its promised full run is
stopped for this algebraic equivalence, rather than presented as four new
independent mechanisms. No phase-1 held-out streams are reused in phase 2.

The next physical candidate removes the target site's entire nine-bit code
from each local key, leaving current raw identity only in the carrier/readout
and in neighbor/global conditions. This is a uniform target-relative omission
over all pixels, time lags and anonymous ports; there are no task roles or
learned-object labels. It can lose necessary information and must be tested.

Three independent MODE=2 fields:

| ID | Learned target | Target site's code in local query | Readout |
|---|---|---|---|
| next | next bit | present | predicted next bit |
| carrier_next | next bit | omitted | predicted next bit |
| carrier_delta | actual XOR change | omitted | current XOR predicted change |

`carrier_delta` is the candidate; `carrier_next` isolates query omission
from relational reconstruction. An independent MODE=0 original priority
model supplies a historical reference, never runtime selection. The original
intact-key delta arm was already checked for equivalence in phase 1.

Every field uses one 32-byte cell table, a 10,000,000-cell upper bound,
ETA=0.5, four fixed local supports and one conditional global support.
All supports contribute their additive logistic residual, with no ranking
in MODE=2. For the delta field, real `y=current XOR next` writes `y-p`;
global birth compares reconstructed raw output against the actual next bit.
No evidence/ties preserve current identity under both encodings. Counts,
sequential physical pixel teaching, support normalizer and all audit code
are unchanged. Inventory may differ through residual-triggered global births.

This remains a one-step probability field with a fixed reconstruction
primitive. The global cache still contains the complete raw state, and
neighbor histories can still correlate with target identity. It is not full
identity factorization, learned propagation or proof of dynamic functions.
The one-bit-equivalent change is replaced solely because of the XOR invariant,
without tuning any readout rate, radius, budget or acceptance threshold.

Frozen before the first phase-2 candidate execution:

- Pilot: all three MODE=2 arms, each 2,000 real pieces, seeds 55971–55973,
  then the same two executed histories repeated 100 times. New streams
  20261171–20261173, 100 episodes each, horizon 120. Record self-prefix,
  complete error-free episodes, truth-fed diagnostics and raw prediction
  fingerprints. Do not tune against these streams.
- History: independent cold fields taught the original pair only; six
  no-ops in teaching, 200 in testing. Record both whole 226-step self-rollouts
  and erase/swap/next-port-offset controls, whether successful or failing.
  Test the port XOR invariant on actual worlds and external observations.
- Full: both carrier arms, 20,000 real pieces, seed 55901, plus identical
  pair replay. Existing compatible next and original priority fields may be
  reused after SHA256 verification. Fresh world indices 36–39, 1,000 episodes
  each, horizon 120. The real world continues after model failure to preserve
  the same RNG/actual trajectories across arms. Teacher forcing uses only
  100 episodes per index and is diagnostic. Five new continuous tape streams
  20261181–20261185, 10,000 pieces each, no truth-fed board replacement.
  Initial raw frames and external preview inputs retain the inherited audit
  interface and are explicitly not learned lifecycle completion.
- Both carrier arms receive full exposure even after a poor pilot, to
  distinguish small-data failure. No parameters change after this freeze.
- Diagnostics: 100 truth-fed worlds, seed 4899039; raw changed/unchanged bit
  errors per physical port. Residual phase reversal and address rotation use
  100 self-predicted worlds, seed 20261191, followed by exact byte restoration.
  Original operation/history controls remain as supplementary checks.
- Implementation: strict C11/Werror; full-table bytes frozen throughout all
  validation; candidate O2/O3 full-field byte equality; UBSan smoke; native
  header mismatch rejection. Unchanged 373-coupling benchmark on 36–39.

Acceptance requires increased permanent-unseen continuous prediction with
history effects preserved and acceptable structural cost. Prefix gain and
static-pixel accuracy are partial evidence; zero error-free episodes is not
Pure BPC game closure. Cell counts/native bytes are storage proxies, not a
measurement of irreducible theoretical K. Fixed radii, bounded raw frames,
XOR history, hash conditions/global cache, hard readout/birth decisions and
external lifecycle timing all remain open assumptions.

Teaching uses only the existing handwritten tapes and actually executed
frames. No synthetic teaching boards, semantic annotations, scoring policy,
task-directed tape choice or self-generated teacher targets are introduced.

Uploaded theory sources: voxel-function section 3.8 (XOR group relations),
function-compression section 11 (preserve identity, causal binding tests,
and warning that changed targets alone do not prove directed behavior).
