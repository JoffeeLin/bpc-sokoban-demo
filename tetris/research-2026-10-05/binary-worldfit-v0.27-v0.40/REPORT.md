# BPC Binary World-Fit v0.27–v0.40 — Purity Compression Report

Date: 2026-10-05

## Goal
Continue fitting the controlled 10×20 Tetris world from a black/white visible screen plus external operation input while removing researcher-provided function categories and special training curricula. Capability must remain frozen: exact next-frame prediction, multi-line clear, vertical non-clear control, and long recurrent rollout.

## Capability floor
The stable capability target remains:
- external state: 0/1 screen + self-born temporal trace + anonymous operation carrier;
- 1/2/3/4 line stress: 10,000/10,000;
- vertical through-board non-clear: 2,500/2,500;
- 8-seed long rollout: 312,839/312,839 exact.

## v0.27 — remove function-family namespace
Deleted K_GAUGE/K_ROUTE/K_LIFE/K_SPAWN/K_CLOSURE-style family namespaces from field addresses. Keys are collisions of participating primitive waves (action, relation, address, boundary, effect, destination state). Capability preserved.

## v0.28 — visible consequence Action-lifetime attempt (negative)
A first attempt to learn carrier lifetime directly from visible consequences collapsed long rollout to ~70%. It confused one-micro consequence with macro action continuation.

## v0.28b — visible trajectory lifetime (positive)
Corrected the temporal credit: compare one internal micro-consequence against the final real consequence along ordinary visible trajectories. Long rollout returned to exactness.

## v0.29 — route credit from visible transitions
Candidate/persist/world consequence routes are credited only when their complete predicted visible transition matches/reduces the real transition residual. The route field compresses effect-equivalent consequences; capability preserved.

## v0.30b — Spawn relation from ordinary visible transitions
Removed the dedicated Spawn displacement curriculum. Preview→future-board displacement is born from ordinary visible game transitions. Formal 8-seed rollout remained 312,839/312,839.

## v0.31 — Closure from final visible residual (negative)
Removed dedicated closure training and attempted direct model-mid→final credit. LineClear stress fell to 0/10,000. This showed final-address equality alone cannot assign instance-level credit through occlusion.

## v0.32 — residual-reduction closure credit
Candidate closure consequences receive credit by reduction of whole-screen residual. Single-line closure reached 100%, but 2/3/4-line remained 0%. Higher-order composition was still missing.

## v0.32b — pairwise competitive credit (negative)
Forcing candidate effects to compete directly suppressed jointly useful effects. Closure collapsed, showing high-order functions cannot be learned as mutually exclusive local winners.

## v0.33 — atomic death + birth effects
Removed persist/down/gone outcome labels. Closure consequences were decomposed into generic source-death and +1-birth effects. Single-line reached 100%, but multi-line remained 0%, revealing a relation-of-relation conflict.

## v0.34 — relation×relation pair context
Introduced generic high-order relation-pair coupling. Initial training observed the wrong temporal point (one microstep before lock), so no useful pair coupling was born; multi-line remained 25% total (single-line only).

## v0.35 — macro-time pair residual (positive but still curriculum-assisted)
Credit was moved to the correct macro time: after action recursion reaches lock, before closure/spawn. Relation-of-relation gating then formed and all 1–4-line stress returned to 10,000/10,000. Formal 8-seed rollout was exact with field frozen. This still retained dedicated closure experience.

## v0.36 — no clear curriculum, ordinary slow-play only
Closure learning was moved to ordinary external-player Screen+Action→Screen transitions, with final descent emitted as repeated Down operations. Multi-line 2/3/4 generalized, but single-line failed: 7,500/10,000 total. This exposed occlusion in local residual attribution.

## v0.37 — joint function-combination credit
Added joint death+birth function hypotheses. The model learned the shift relation and high-order pair gate, but same-address source-death was still hidden by incoming pixels; single-line remained 0 while 2/3/4 were exact.

Representative learned state before the fix:
- same-address: death amplitude 0, false birth amplitude >0;
- closure-below: joint death+birth ~1;
- closure-above: unwanted birth;
- pair gate learned ~0.04.

## v0.38 — whole-world leave-one-coupling-out residual credit (positive)
Local pixel identity credit was replaced with a global counterfactual:

- force one participating coupling OFF → final visible residual e0;
- force the same coupling ON → final visible residual e1;
- only the alternative that reduces the entire next-frame residual receives credit.

No source-instance semantic label is required. Ordinary game trajectories only.

A short training stream learned:
- same-address death amplitude ≈ 0.898, birth = 0;
- closure-below birth amplitude ≈ 0.987;
- closure-above death/birth = 0;
- high-order pair gate ≈ 0.111.

Formal frozen result:
- 1/2/3/4 line stress: 10,000/10,000;
- vertical non-clear: 2,500/2,500;
- 8-seed rollout: 312,839/312,839 exact.

This is the first closure result in this branch where the high-order clear function is born only from ordinary play plus whole-world residual credit, without a dedicated clear curriculum.

## v0.39 — Spawn/GameOver split from ordinary Lock transitions
The dedicated blocked/unblocked Spawn training set was cleared from the field and relearned only from ordinary real lock transitions. The model's own lock mid-state plus learned closure defines the pre-spawn world; the real final screen supplies the outcome residual.

2,500 observed locks produced:
- Spawn: 2,340;
- GameOver: 160;
- C=1 → direct ≈ 0.999573, complement ≈ 0.000427;
- C=0 → direct ≈ 0.006173, complement ≈ 0.993827.

Formal frozen result remains:
- clear stress 10,000/10,000;
- vertical negative 2,500/2,500;
- 8-seed rollout 312,839/312,839 exact.

## v0.40 — Collision compatibility from ordinary visible residual counterfactuals
The one-cell artificial collision micro-curriculum was erased. Compatibility for empty / occupied / boundary destinations was relearned only from ordinary game transitions by whole-transition ON/OFF counterfactual residual credit.

Learned compatibility after two ordinary-play passes:
- empty probability ≈ 0.999976 → positive amplitude ≈ 0.999953;
- occupied probability ≈ 0.000410 → positive amplitude 0;
- boundary probability ≈ 0.000313 → positive amplitude 0.

Formal frozen result:
- clear stress 10,000/10,000;
- vertical negative 2,500/2,500;
- 8-seed rollout 312,839/312,839 exact.

Therefore Collision is now free of both a handwritten inference rule and a dedicated collision training curriculum in the final field.

## Current stable checkpoint
**Binary World-Fit v0.40**.

Current training provenance is now much closer to the strict target:

`ordinary black/white game trajectory + operation`
`→ participating relation hypotheses`
`→ whole-world residual credit`
`→ one shared probability field`
`→ recurrent world dynamics`

## Remaining major scaffolds
1. Geometry gauge/basis/phase still begins from a researcher-designed 1/2/3-voxel micro curriculum. This is now the largest dedicated curriculum left.
2. Internal execution still reconstructs transient/persistent information from screen+temporal trace and treats the two roles differently in C helpers.
3. Geometry inference still contains discrete best-gauge / best-basis / signed-phase extraction before applying the transform; this should eventually become continuous wave participation.
4. Physical lattice/address topology and visible Preview screen region are supplied as physical substrate.
5. Some observer code remains function-specific even though the learned field and the successful closure/collision credit rule are increasingly unified.

## Next target
Remove the dedicated geometry micro-curriculum. Geometry must be born from ordinary 4-cell game transitions by residual comparison across spatial-relation hypotheses, without single-cell/domino teaching examples. Only after that survives the frozen regression should discrete geometry selection or internal transient/persistent execution be attacked.