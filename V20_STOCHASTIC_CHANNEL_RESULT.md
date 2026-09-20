# BPC v0.20: frozen stochastic actuator-channel transfer

## Result

**ADOPTED for the bounded claim below.**  The frozen non-neural controller now
receives delayed, D4-transformed observations through an anonymous variable
sensor interface and issues commands through an unseen stochastic actuator
channel.  Each useful actuator slot samples one of four physical effects from
an unknown probability row.  Other slots perturb nuisance planes but have no
canonical effect.  Calibration contains only observations, issued slots, and
next observations.

Four new interfaces, three independent calibration streams per interface, 48
holdout worlds, and two evaluation seeds were frozen before execution.  Across
4,608 episodes per condition:

| Frozen condition | Successes | Rate |
|---|---:|---:|
| Learned stochastic channel + temporal/D4 gauge average | **3,875 / 4,608** | **84.1%** |
| Oracle stochastic channel and physical frame | 3,871 / 4,608 | 84.0% |
| Deterministic argmax of each learned channel row | 4,179 / 4,608 | 90.7% |
| Identity actuator channel | 2,480 / 4,608 | 53.8% |
| One-slot-shuffled learned rows | 1,569 / 4,608 | 34.0% |

Every interface passed separately.  All four unseen total lags and all 12
independent-stream lags were exact.  Maximum channel total-variation error was
`0.02583`; maximum single-stream error was `0.04150`.  All 13 preregistered
gates passed.  Evaluation made zero model writes and preserved the model
digest.

## Mechanism

For every supplied lag `0–4` and every D4 gauge, v0.20:

1. aligns observations with the issued slot from that candidate lag;
2. maps the recovered six raw sensor planes into the candidate spatial frame;
3. represents each transition only by anonymous per-plane count, flip, and
   local-motion events;
4. estimates each useful actuator row as a four-component probability mixture
   by expectation maximization over canonical reference effects;
5. assigns a slot to the separate nuisance class only when it never changes
   any recovered canonical plane; and
6. maps direct BPC action probabilities back through the learned channel using
   the normalized reverse conditional probabilities, averaged across all eight
   observationally equivalent D4 gauges.

No task, entity, direction, goal, reward, or evaluator success enters binding
or inference.  `classifier.dev` (`jev-1.13.0`) routed 16 candidate frontiers and
selected stochastic actuator channels at confidence `0.83`; it is absent from
training, inference, frozen evaluation, and runtime.

## Preserved negative result

The first development mechanism included “no physical effect” as a fifth
continuous mixture component for every useful actuator.  It achieved
`484/576` control successes but failed its mechanism gates: maximum full-data
channel error was `0.23770` against a frozen `0.12` threshold and maximum
single-stream error was `0.26071` against `0.20`.  A blocked directional action
and a sampled no-effect action can produce the same raw transition under that
unconditional statistic, so the decomposition was not identifiable.  The raw
failed result is retained at
[`artifacts/v20stochastic/rejected_attempt1_noop_nonidentifiable.json`](artifacts/v20stochastic/rejected_attempt1_noop_nonidentifiable.json).

The identifiable replacement restricts useful slots to mixtures of the four
physical directions and treats structurally inactive nuisance slots as a
separate class.  Thresholds were not relaxed.  The accepted development error
dropped to `0.02312` overall and `0.03306` per stream before the frozen protocol
was produced.

## Important control boundary

The complete learned probability channel did **not** beat the deterministic
argmax control: `3,875` versus `4,179` successes.  Therefore v0.20 is evidence
for accurate stochastic-channel identification plus preserved control, not
evidence that retaining the full channel improves the best policy.  The
four-episode difference from oracle is sampling variation under equivalent
probability routing, not superiority over oracle.

## Frozen evidence

- Protocol: [`protocol_v20_stochastic.json`](protocol_v20_stochastic.json)
- Holdout: [`holdout_v20.json`](holdout_v20.json)
- Frozen runner: [`experiment_v20_stochastic_frozen.py`](experiment_v20_stochastic_frozen.py)
- Core mechanism: [`bpc_stochastic_interface_v20.py`](bpc_stochastic_interface_v20.py)
- Result: [`artifacts/v20stochastic/result.json`](artifacts/v20stochastic/result.json)
- Video: [12 frozen stochastic-control traces](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/download/v20.0.0/bpc_stochastic_channel_v20_12_unseen_worlds.mp4)
- Release: [v20.0.0](https://github.com/JoffeeLin/bpc-sokoban-demo/releases/tag/v20.0.0)
- Result SHA-256: `86597054a9d585d1e81763766cce6d57b72c6d000738fc2175181a347e4e8c66`
- Protocol SHA-256: `5b07829b89612ea7fbd8d09f112bf476510e905bc40017d714640ade074659f7`
- Holdout SHA-256: `cf814ea084df4b564fbf61975f1727852208cd74a92ef0bfa05e4c4963c16c4c`
- Accepted development SHA-256: `adc5f004735019682c3660045ddc165e31826b52420a40f328779921485039fe`
- Rejected attempt SHA-256: `b197d0dc00d7a59190529447dd9640a1dfeeba814017d5d77e46cafb5a17894d`
- Video SHA-256: `115970a93bf1efa5342e72dbd2cbaba4bcb5bc74aee48b0f33da609375c66c08`
- Poster SHA-256: `0ba4c170079321f996ba38182c1cfd88db9a64d1219984d1f9906246884a075c`

## Boundary

This is developer-frozen held-out synthetic evidence, not a third-party blind
result.  Useful actuator slots mix four supplied physical directions;
structurally inactive nuisance slots are a separate no-effect class.  Lag
candidates `0–4`, D4 family, canonical schema, maximum 7×7 canvas, statistics,
generators, terminal events, and the backward probability channel remain
supplied.  This does not establish arbitrary stochastic dynamics, causal
world-model discovery, optimal stochastic control, open-world grounding, or
AGI.
