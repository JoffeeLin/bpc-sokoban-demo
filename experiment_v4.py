#!/usr/bin/env python3
"""Frozen development experiment for a distributed raw-relation GeneralBPC."""

from __future__ import annotations

import hashlib
import json
import pickle
import random
from dataclasses import dataclass
from pathlib import Path

from bpc_sokoban import (ACTIONS, BPC, EVAL_EPISODES, LEVEL_MAPS, MAX_STEPS,
                         SEED, SIZE, TEST_LEVELS, TRAIN_EPISODES, TRAIN_LEVELS, World)
from general_bpc import BinaryRelationWave, GeneralBPC

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts" / "v4"
RESULT = OUT / "result.json"
MODEL = OUT / "general_bpc.pkl"
DIMENSIONS, EPOCHS, RETAINED_FAILURES = 1024, 3, 128


@dataclass
class Episode:
    level: int
    success: bool
    steps: list[tuple[bytes, int, bool]]


def collect_same_experience() -> list[Episode]:
    """Uniform reality stream; retain by the rule frozen before execution."""
    rng, kept = random.Random(SEED), []
    for level in TRAIN_LEVELS:
        successes, failures = [], []
        for _ in range(TRAIN_EPISODES):
            world, steps = World(level), []
            while not world.terminal:
                bits, action = world.observation(), rng.randrange(len(ACTIONS))
                event = world.step(action)
                steps.append((bits, action, event["changed"]))
            episode = Episode(level, world.success, steps)
            if world.success:
                successes.append(episode)
            elif len(failures) < RETAINED_FAILURES:
                failures.append(episode)
        kept.extend(successes + failures)
    return kept


def corpus_digest(episodes: list[Episode]) -> str:
    digest = hashlib.sha256()
    for episode in episodes:
        digest.update(bytes((episode.level, int(episode.success))))
        for bits, action, changed in episode.steps:
            digest.update(bits); digest.update(bytes((action, int(changed))))
    return digest.hexdigest()


def replay_exact(model: BPC, episode: Episode, action_rotation: int = 0,
                 success_override: bool | None = None) -> None:
    model.reset_episode()
    label = episode.success if success_override is None else success_override
    for index, (bits, action, changed) in enumerate(episode.steps):
        model.observe(bits, (action + action_rotation) % 4, changed,
                      index == len(episode.steps) - 1, label, True)


def evaluate_general(model: GeneralBPC, encoder: BinaryRelationWave,
                     levels: tuple[int, ...], use_change: bool = True) -> dict[int, int]:
    before, result = model.writes, {}
    for level in levels:
        successes = 0
        for _ in range(EVAL_EPISODES):
            world = World(level)
            while not world.terminal:
                wave = encoder.encode(world.observation())
                action, _ = model.decide(wave, use_change)
                event = world.step(action)
                model.observe(wave, action, False, event["changed"], False)
            successes += int(world.success)
        result[level] = successes
    assert before == model.writes
    return result


def evaluate_exact(model: BPC, levels: tuple[int, ...]) -> dict[int, int]:
    before, result = model.writes, {},
    for level in levels:
        successes = 0
        for _ in range(EVAL_EPISODES):
            world = World(level); model.reset_episode()
            while not world.terminal:
                bits = world.observation(); action, _ = model.decide(bits, False)
                event = world.step(action)
                model.observe(bits, action, event["changed"], event["terminal"], event["success"], False)
            successes += int(world.success)
        result[level] = successes
    assert before == model.writes
    return result


def one_based(values: dict[int, int]) -> dict[str, int]:
    return {str(level + 1): count for level, count in values.items()}


def totals(values: dict[int, int], levels: tuple[int, ...]) -> int:
    return sum(values[level] for level in levels)


def main() -> None:
    episodes = collect_same_experience()
    by_level = {level: [episode for episode in episodes if episode.level == level] for level in TRAIN_LEVELS}
    shared_encoder = BinaryRelationWave(SIZE, SIZE, 6, DIMENSIONS, False)
    locked_encoder = BinaryRelationWave(SIZE, SIZE, 6, DIMENSIONS, True)
    shared = GeneralBPC(4, DIMENSIONS)
    locked = GeneralBPC(4, DIMENSIONS)
    action_rotated = GeneralBPC(4, DIMENSIONS)
    credit_rotated = GeneralBPC(4, DIMENSIONS)
    exact = BPC(SEED)
    curves = []
    order_rng = random.Random(SEED ^ 0xB4C)
    for epoch in range(EPOCHS):
        order = list(episodes); order_rng.shuffle(order)
        rotated_labels = {}
        for level, group in by_level.items():
            labels = [episode.success for episode in group]
            for index, episode in enumerate(group):
                rotated_labels[id(episode)] = labels[(index + 1) % len(labels)]
        for episode in order:
            replay_exact(exact, episode)
            for bits, action, changed in episode.steps:
                shared_wave = shared_encoder.encode(bits)
                shared.observe(shared_wave, action, episode.success, changed)
                action_rotated.observe(shared_wave, (action + 1) % 4, episode.success, changed)
                credit_rotated.observe(shared_wave, action, rotated_labels[id(episode)], changed)
                locked.observe(locked_encoder.encode(bits), action, episode.success, changed)
        curves.append({
            "epoch": epoch + 1,
            "shared_train": one_based(evaluate_general(shared, shared_encoder, TRAIN_LEVELS)),
            "shared_development": one_based(evaluate_general(shared, shared_encoder, TEST_LEVELS)),
        })

    all_levels = tuple(range(len(LEVEL_MAPS)))
    conditions = {
        "exact_full_frame": evaluate_exact(exact, all_levels),
        "position_locked": evaluate_general(locked, locked_encoder, all_levels),
        "position_shared": evaluate_general(shared, shared_encoder, all_levels),
        "position_shared_transition_off": evaluate_general(shared, shared_encoder, all_levels, False),
        "action_rotated": evaluate_general(action_rotated, shared_encoder, all_levels),
        "terminal_credit_rotated": evaluate_general(credit_rotated, shared_encoder, all_levels),
        "untrained_zero": evaluate_general(GeneralBPC(4, DIMENSIONS), shared_encoder, all_levels),
    }
    primary = conditions["position_shared"]
    train_total, dev_total = totals(primary, TRAIN_LEVELS), totals(primary, TEST_LEVELS)
    exact_dev = totals(conditions["exact_full_frame"], TEST_LEVELS)
    action_control = totals(conditions["action_rotated"], TEST_LEVELS)
    credit_control = totals(conditions["terminal_credit_rotated"], TEST_LEVELS)
    gate = {
        "training_at_least_144": train_total >= 144,
        "development_at_least_64": dev_total >= 64,
        "improvement_over_exact_at_least_32": dev_total - exact_dev >= 32,
        "every_development_level_nonzero": all(primary[level] > 0 for level in TEST_LEVELS),
        "beats_action_rotated": dev_total > action_control,
        "beats_terminal_credit_rotated": dev_total > credit_control,
        "evaluation_writes_zero": True,
    }
    source_hash = hashlib.sha256((ROOT / "general_bpc.py").read_bytes() + Path(__file__).read_bytes()).hexdigest()
    result = {
        "format": "bpc-sokoban-general-bpc-v4-development",
        "evidence_level": "development only; evaluation layouts were exposed by v2",
        "theory_question": "Can distributed raw-relation address sharing plus BPC y-p residual writeback form a transferable direct action function?",
        "input": "486 raw binary voxels; no coordinates or semantic object labels supplied to candidate",
        "candidate": "all raw cell-pair relation components continuously enter one normalized BPC-0 wave",
        "no_neural_network": True,
        "no_planner_or_search": True,
        "no_complete_frame_hash": True,
        "no_fixed_future_horizon": True,
        "experience": {
            "generated_per_training_level": TRAIN_EPISODES,
            "retained_rule": f"all successes plus first {RETAINED_FAILURES} failures per level",
            "retained_episodes": len(episodes),
            "retained_steps": sum(len(episode.steps) for episode in episodes),
            "successes_by_level": {str(level + 1): sum(e.success for e in group) for level, group in by_level.items()},
            "corpus_sha256": corpus_digest(episodes),
        },
        "dimensions": DIMENSIONS,
        "epochs": EPOCHS,
        "conditions": {name: one_based(values) for name, values in conditions.items()},
        "curve": curves,
        "primary": {"training_total": train_total, "development_total": dev_total,
                    "exact_development_total": exact_dev, "action_rotated_development_total": action_control,
                    "credit_rotated_development_total": credit_control},
        "gate": gate,
        "adopted": all(gate.values()),
        "frozen_persistent_writes": 0,
        "model_sha256": shared.digest(),
        "candidate_source_sha256": source_hash,
        "theory_boundary": {
            "supported": ["direct raw binary relation wave", "address sharing", "normalized probability read", "y-p original-path writeback", "external action-only discretization"],
            "not_yet_implemented": ["residual-born support lifecycle", "online function-equivalence merge/split", "self-born process voxels", "permanent blind pack"],
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with MODEL.open("wb") as file:
        pickle.dump({"model": shared, "encoder": shared_encoder}, file, protocol=5)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
