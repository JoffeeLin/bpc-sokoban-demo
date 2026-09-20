# BPC v0.10: frozen anonymous factor discovery and routing

## Result

**ADOPTED for the bounded claim below.** A single BPC learner received successful
raw trajectories without task-family names. The raw planes that co-changed on
each successful terminal transition became anonymous factor identities. Their
common plane was removed, and the remaining raw-plane presence activated the
factors during direct control.

The frozen holdout contained 48 new initial worlds—16 push-only, 16
collect-only, and 16 push-required collection worlds—with zero overlap against
all 4,000 training initial worlds. Across two new action seeds:

| Frozen 32-step condition | Successes | Rate |
|---|---:|---:|
| Automatic anonymous-factor routing | **4,284 / 6,144** | **69.7%** |
| Task-name oracle routing | **4,284 / 6,144** | **69.7%** |
| Always activate both factors | 4,302 / 6,144 | 70.0% |
| One shared mixed-trace cube | 3,962 / 6,144 | 64.5% |
| Permuted raw-plane activation | 2,749 / 6,144 | 44.7% |
| Uniform random | 2,013 / 6,144 | 32.8% |

On the 2,048 joint-task episodes alone, automatic routing completed 861
(`42.0%`), versus 542 (`26.5%`) for the shared cube and 224 (`10.9%`) for
uniform random. At 160 steps, automatic routing completed 5,629/6,144.

## Mechanism

The learner discovered terminal co-change signatures `(1,2)` and `(1,3)`.
Plane `1` occurred in both and was therefore removed as common. Presence of
exclusive plane `2` activates the first factor; presence of plane `3` activates
the second. These numbers are anonymous raw bit-plane indices, not supplied
entity or task names.

During frozen evaluation, automatic routing made 342,139 decisions with zero
activation mismatches against a task-name oracle. Permuting the two exclusive
plane bindings reduced 32-step success by 1,535 episodes, supporting a causal
role for the discovered binding. Evaluation made zero model writes, and all ten
pre-registered gates passed.

`classifier.dev` routed 18 proposed development directions. It favored raw
co-change factor discovery and rejected runtime planning/search routes. It did
not enter model training, inference, or evaluation.

## Frozen evidence

- Protocol: [`protocol_v10_autofactor.json`](protocol_v10_autofactor.json)
- Holdout: [`holdout_v10.json`](holdout_v10.json)
- Runner: [`experiment_v10_autofactor_frozen.py`](experiment_v10_autofactor_frozen.py)
- Result: [`artifacts/v10autofactor/result.json`](artifacts/v10autofactor/result.json)
- Result SHA-256:
  `9926b9ed34124e6d4cb9db27cf470acccc237acca6d08e8d59c4cbca7ffab9f8`
- Video SHA-256:
  `5a5058c777d24f7c7bde33b8096deec0e655c5bfcba8fe354b69e77e73331efa`
- GitHub release:
  <https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v10.0.0>

## Boundary

This removes supplied task-family labels from factor allocation and runtime
activation. It does **not** remove all supplied structure: raw channelization,
equal probability multiplication, task generators, binary terminal success
events, and evaluation limits remain externally defined.

Always activating both discovered factors was 18 successes (`0.29` percentage
points) above automatic/oracle routing in aggregate. Therefore this result does
not show that routing improves total success; it shows that anonymous raw
co-change can recover oracle factor activation without task names. This remains
developer-frozen synthetic evidence, not autonomous operator invention,
arbitrary planning, language grounding, or AGI.
