#!/usr/bin/env python3
"""GeneralBPC v5 frozen cross-layout experiment."""

from __future__ import annotations

import hashlib
import json
import pickle
import random
from collections import defaultdict, deque
from pathlib import Path

import bpc_sokoban as base
from general_bpc_v5 import ActionWaveBPC, RawRelationEncoder

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts" / "v5"
HOLDOUT_PATH = ROOT / "holdout_v5.json"
TRAIN_MAPS, TRAIN_MAP_SEED, TRAIN_MAP_EPISODES = 100, 19_577, 1_000
DIMENSIONS, EPOCHS, EVAL_EPISODES = 16_384, 300, 256
TEMPERATURE, EVAL_SEED = 0.75, 881


def parse_map(level_map: tuple[str, ...]) -> tuple[set[tuple[int, int]], tuple[int, int], tuple[int, int], tuple[int, int]]:
    walls, player, box, goal = set(), None, None, None
    for y, row in enumerate(level_map):
        for x, value in enumerate(row):
            if value == "#": walls.add((x, y))
            elif value == "P": player = (x, y)
            elif value == "B": box = (x, y)
            elif value == "G": goal = (x, y)
    assert player and box and goal
    return walls, player, box, goal


def solution_distance(level_map: tuple[str, ...]) -> int | None:
    walls, player, box, goal = parse_map(level_map)
    queue, seen = deque([(player, box, 0)]), {(player, box)}
    while queue:
        player, box, distance = queue.popleft()
        if box == goal:
            return distance
        for dx, dy in base.ACTIONS:
            candidate, next_box = (player[0] + dx, player[1] + dy), box
            if candidate in walls:
                continue
            if candidate == box:
                next_box = box[0] + dx, box[1] + dy
                if next_box in walls:
                    continue
            state = candidate, next_box
            if state not in seen:
                seen.add(state); queue.append((candidate, next_box, distance + 1))
    return None


def generate_maps(count: int, seed: int) -> tuple[tuple[str, ...], ...]:
    """Offline solvability filter; no solution action is returned to BPC."""
    rng, output, wall_sets = random.Random(seed), [], []
    inside = [(x, y) for y in range(1, 8) for x in range(1, 8)]
    while len(output) < count:
        walls = set(rng.sample(inside, rng.randint(5, 13)))
        free = [position for position in inside if position not in walls]
        player, box, goal = rng.sample(free, 3)
        rows = [["#"] * 9 for _ in range(9)]
        for y in range(1, 8):
            for x in range(1, 8):
                rows[y][x] = "#" if (x, y) in walls else " "
        for position, value in ((player, "P"), (box, "B"), (goal, "G")):
            rows[position[1]][position[0]] = value
        level_map = tuple("".join(row) for row in rows)
        distance = solution_distance(level_map)
        if distance is None or not 4 <= distance <= 16:
            continue
        if any(len(walls & previous) / len(walls | previous) > 0.55 for previous in wall_sets):
            continue
        output.append(level_map); wall_sets.append(walls)
    return tuple(output)


def erase_zero_effect_cycles(trace: list[tuple[bytes, int, bytes]]) -> list[tuple[bytes, int]]:
    """Remove only segments proven by reality to return to the identical raw state."""
    states, actions = [trace[0][0]], []
    location = {states[0]: 0}
    for _, action, next_state in trace:
        if next_state in location:
            index = location[next_state]
            states, actions = states[:index + 1], actions[:index]
            location = {state: i for i, state in enumerate(states)}
        else:
            actions.append(action); states.append(next_state); location[next_state] = len(states) - 1
    return list(zip(states[:-1], actions))


def collect_experience(training_indices: list[int]) -> tuple[dict, dict, dict]:
    rng = random.Random(base.SEED)
    compact = defaultdict(lambda: [0, 0, 0, 0])
    raw = defaultdict(lambda: [0, 0, 0, 0])
    summary = {}
    for level in training_indices:
        episodes = base.TRAIN_EPISODES if level < 10 else TRAIN_MAP_EPISODES
        successes = 0
        for _ in range(episodes):
            world, trace = base.World(level), []
            while not world.terminal:
                state, action = world.observation(), rng.randrange(4)
                world.step(action); trace.append((state, action, world.observation()))
            if not world.success:
                continue
            successes += 1
            for state, action, _ in trace:
                raw[state][action] += 1
            for state, action in erase_zero_effect_cycles(trace):
                compact[state][action] += 1
        summary[str(level + 1)] = {"episodes": episodes, "successes": successes}
    return dict(compact), dict(raw), summary


def evaluate(model: ActionWaveBPC | None, encoder: RawRelationEncoder | None,
             levels: list[int], names: list[str]) -> dict[str, int]:
    before = None if model is None else model.writes
    result = {}
    for level, name in zip(levels, names):
        successes = 0
        for episode in range(EVAL_EPISODES):
            rng, world = random.Random(EVAL_SEED + level * 10_000 + episode), base.World(level)
            while not world.terminal:
                probability = ([0.25] * 4 if model is None else
                               model.probabilities(encoder.encode(world.observation()), TEMPERATURE))
                threshold, cumulative, action = rng.random(), 0.0, 0
                for index, value in enumerate(probability):
                    cumulative += float(value)
                    if threshold <= cumulative:
                        action = index; break
                world.step(action)
            successes += int(world.success)
        result[name] = successes
    if model is not None:
        assert before == model.writes, "evaluation wrote persistent state"
    return result


def digest_maps(maps: tuple[tuple[str, ...], ...]) -> str:
    return hashlib.sha256("\n\n".join("\n".join(level) for level in maps).encode()).hexdigest()


def total(values: dict[str, int]) -> int:
    return sum(values.values())


def main() -> None:
    original_maps = base.LEVEL_MAPS
    training_maps = generate_maps(TRAIN_MAPS, TRAIN_MAP_SEED)
    holdout_maps = tuple(tuple(row for row in level) for level in json.loads(HOLDOUT_PATH.read_text()))
    base.LEVEL_MAPS = original_maps + training_maps + holdout_maps
    base.OBS_CACHE.clear()
    training_indices = list(base.TRAIN_LEVELS) + list(range(10, 10 + len(training_maps)))
    compact, raw, experience = collect_experience(training_indices)

    joint_encoder = RawRelationEncoder(9, 9, 6, DIMENSIONS, joint=True)
    primary = ActionWaveBPC(4, DIMENSIONS); primary.fit(compact, joint_encoder, EPOCHS)
    joint_encoder.cache.clear()
    no_loop = ActionWaveBPC(4, DIMENSIONS); no_loop.fit(raw, joint_encoder, EPOCHS)
    joint_encoder.cache.clear()
    pair_encoder = RawRelationEncoder(9, 9, 6, DIMENSIONS, joint=False)
    no_joint = ActionWaveBPC(4, DIMENSIONS); no_joint.fit(compact, pair_encoder, EPOCHS)
    pair_encoder.cache.clear()
    rotated = primary.rotated()

    development_levels, development_names = list(base.TEST_LEVELS), [f"D{level + 1}" for level in base.TEST_LEVELS]
    holdout_start = 10 + len(training_maps)
    holdout_levels = list(range(holdout_start, holdout_start + len(holdout_maps)))
    holdout_names = [f"H{index + 1}" for index in range(len(holdout_maps))]
    conditions = {}
    for name, model, encoder in (
        ("primary", primary, joint_encoder), ("no_joint", no_joint, pair_encoder),
        ("no_loop_death", no_loop, joint_encoder), ("action_rotated", rotated, joint_encoder),
        ("uniform_zero", None, None)):
        conditions[name] = {
            "development": evaluate(model, encoder, development_levels, development_names),
            "holdout": evaluate(model, encoder, holdout_levels, holdout_names),
        }

    denominator = len(holdout_maps) * EVAL_EPISODES
    primary_total = total(conditions["primary"]["holdout"])
    uniform_total = total(conditions["uniform_zero"]["holdout"])
    no_joint_total = total(conditions["no_joint"]["holdout"])
    no_loop_total = total(conditions["no_loop_death"]["holdout"])
    rotated_total = total(conditions["action_rotated"]["holdout"])
    gate = {
        "holdout_rate_at_least_40pct": primary_total / denominator >= 0.40,
        "every_holdout_at_least_5pct": all(value / EVAL_EPISODES >= 0.05 for value in conditions["primary"]["holdout"].values()),
        "beats_uniform_by_20pp": (primary_total - uniform_total) / denominator >= 0.20,
        "joint_gain_at_least_3pp": (primary_total - no_joint_total) / denominator >= 0.03,
        "loop_death_gain_at_least_3pp": (primary_total - no_loop_total) / denominator >= 0.03,
        "beats_action_rotated_by_20pp": (primary_total - rotated_total) / denominator >= 0.20,
        "frozen_writes_zero": True,
    }
    source_hash = hashlib.sha256((ROOT / "general_bpc_v5.py").read_bytes() + Path(__file__).read_bytes()).hexdigest()
    result = {
        "format": "general-bpc-sokoban-v5",
        "evidence_level": "developer-frozen local holdout; not independent blind",
        "input": "raw 9x9x6 binary voxels and anonymous external action indices",
        "model": "position-shared raw pair and anonymous three-group joint waves; softmax probability; y-p original-path writeback",
        "no_neural_network": True, "no_planner_or_search_in_model": True,
        "offline_solver_use": "solvability and shortest-distance range filter only; no solution actions enter experience or model",
        "experience": experience,
        "compact_function_states": len(compact), "uncompressed_success_states": len(raw),
        "training_maps_sha256": digest_maps(training_maps), "holdout_maps_sha256": digest_maps(holdout_maps),
        "conditions": conditions,
        "primary_holdout": {"successes": primary_total, "episodes": denominator, "rate": primary_total / denominator},
        "gate": gate, "adopted": all(gate.values()), "frozen_persistent_writes": 0,
        "model_sha256": primary.digest(), "candidate_source_sha256": source_hash,
        "boundary": "A pass would support limited same-generator cross-layout transfer only, not arbitrary Sokoban, a finished universal BPC, or AGI.",
        "fixed_prior_disclosure": "rarity<=2 raw-group anchoring, radius 4, and three-group joint capacity are experimenter-provided non-semantic addressing priors.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    with (OUT / "model.pkl").open("wb") as file:
        pickle.dump({"model": primary, "config": {"dimensions": DIMENSIONS, "temperature": TEMPERATURE}}, file, protocol=5)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
