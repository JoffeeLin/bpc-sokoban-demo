#!/usr/bin/env python3
"""Development-only spatial-residue experiment; never reads v6 holdout data."""

from __future__ import annotations

import json
import random
from collections import defaultdict

import bpc_sokoban as base
from experiment_v5 import erase_zero_effect_cycles, generate_maps
from general_bpc_v6 import SpatialResidueBPC

MAPS, MAP_SEED, EPISODES = 60, 66_103, 500
GUIDED_EPISODES, GUIDED_EPSILON = 150, 0.35
EVAL_EPISODES, EVAL_SEED = 32, 92_011


def collect(levels: list[int]) -> tuple[SpatialResidueBPC, dict[str, int]]:
    rng, model, success = random.Random(6_200_001), SpatialResidueBPC(), {}
    for level in levels:
        found = 0
        for _ in range(EPISODES if level >= 10 else base.TRAIN_EPISODES):
            world, trace = base.World(level), []
            while not world.terminal:
                raw, action = world.observation(), rng.randrange(4)
                world.step(action)
                trace.append((raw, action, world.observation()))
            if world.success:
                found += 1
                compact = erase_zero_effect_cycles(trace)
                # Recover reality-observed successor packets after loop death.
                compact_path = []
                by_state = defaultdict(list)
                for raw, action, nxt in trace:
                    by_state[(raw, action)].append(nxt)
                for raw, action in compact:
                    compact_path.append((raw, action, by_state[(raw, action)].pop(0)))
                model.observe_success_path(compact_path)
        success[str(level + 1)] = found
    # One self-experience pass: probabilities guide exploration, but only actual
    # terminal successes write. No planned or counterfactual action is supplied.
    for level in levels:
        found = 0
        for episode in range(GUIDED_EPISODES):
            world, trace = base.World(level), []
            model.reset_episode()
            while not world.terminal:
                raw = world.observation()
                probability = model.probabilities(raw)
                if rng.random() < GUIDED_EPSILON:
                    action = rng.randrange(4)
                else:
                    value, cumulative, action = rng.random(), 0.0, 0
                    for index, p in enumerate(probability):
                        cumulative += float(p)
                        if value <= cumulative:
                            action = index
                            break
                world.step(action)
                trace.append((raw, action, world.observation()))
                model.advance(raw, action)
            if world.success:
                found += 1
                compact = erase_zero_effect_cycles(trace)
                by_state = defaultdict(list)
                for raw, action, nxt in trace:
                    by_state[(raw, action)].append(nxt)
                model.observe_success_path([(raw, action, by_state[(raw, action)].pop(0))
                                            for raw, action in compact])
        success[f"{level + 1}:guided"] = found
    return model, success


def evaluate(model: SpatialResidueBPC | None, levels: list[int], transported: bool = True,
             rotated: bool = False) -> dict[str, int]:
    result, test_model = {}, model.rotated() if model is not None and rotated else model
    before = None if test_model is None else test_model.writes
    for level in levels:
        wins = 0
        for episode in range(EVAL_EPISODES):
            rng, world = random.Random(EVAL_SEED + level * 10000 + episode), base.World(level)
            if test_model is not None:
                test_model.reset_episode()
            while not world.terminal:
                raw = world.observation()
                probability = [0.25] * 4 if test_model is None else test_model.probabilities(raw, transported)
                value, total, action = rng.random(), 0.0, 0
                for index, p in enumerate(probability):
                    total += float(p)
                    if value <= total:
                        action = index
                        break
                world.step(action)
                if test_model is not None:
                    test_model.advance(raw, action)
            wins += int(world.success)
        result[f"D{level + 1}"] = wins
    if test_model is not None:
        assert before == test_model.writes
    return result


def main() -> None:
    base.MAX_STEPS = 96
    original = base.LEVEL_MAPS
    maps = generate_maps(MAPS, MAP_SEED)
    base.LEVEL_MAPS = original + maps
    base.OBS_CACHE.clear()
    training = list(base.TRAIN_LEVELS) + list(range(10, 50))
    development = list(base.TEST_LEVELS) + list(range(50, 70))
    model, experience = collect(training)
    result = {
        "development_only": True,
        "experience": experience,
        "conditions": {
            "full": evaluate(model, development),
            "no_transport": evaluate(model, development, transported=False),
            "rotated": evaluate(model, development, rotated=True),
            "uniform": evaluate(None, development),
        },
        "model_sha256": model.digest(),
        "writes": model.writes,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
