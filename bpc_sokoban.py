#!/usr/bin/env python3
"""One-file BPC Sokoban demo: train, verify held-out transfer, and record MP4."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import random
import subprocess
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
MODEL_PATH = ARTIFACTS / "model.pkl"
RESULT_PATH = ARTIFACTS / "result.json"
VIDEO_PATH = ARTIFACTS / "bpc_sokoban_10_levels.mp4"
POSTER_PATH = ARTIFACTS / "poster.png"

SIZE, MAX_STEPS = 9, 72
ACTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))
ACTION_NAMES = ("UP", "RIGHT", "DOWN", "LEFT")
TRAIN_LEVELS = (0, 2, 4, 6, 8)
TEST_LEVELS = (1, 3, 5, 7, 9)
TRAIN_EPISODES = 12_000
EVAL_EPISODES = 32
SEED = 20_260_920

# Ten independently generated, solver-validated layouts. They are frozen here
# as literal inputs; no transform pairs or generated variants enter evaluation.
LEVEL_MAPS = (
    ("#########", "## #    #", "# #  #G #", "##P    ##", "#   #   #", "# #  B ##", "#       #", "# #    ##", "#########"),
    ("#########", "# #  #  #", "#    #  #", "##      #", "#  #    #", "# ##    #", "# #     #", "#   BGP##", "#########"),
    ("#########", "#  ##   #", "#       #", "##B # # #", "#      ##", "#    #  #", "# P     #", "# G  #  #", "#########"),
    ("#########", "#     ###", "#  B#   #", "# #     #", "#  G P# #", "#   ## ##", "#  #    #", "# ##    #", "#########"),
    ("#########", "#    #  #", "###     #", "#    G# #", "# B  ## #", "#  P#   #", "#      ##", "##     ##", "#########"),
    ("#########", "###    P#", "# ## G  #", "#    B  #", "#   #   #", "##  ##  #", "# # #   #", "#     # #", "#########"),
    ("#########", "# #  #  #", "#  ##   #", "##     ##", "#   # # #", "# P    ##", "# # B   #", "#  #  G #", "#########"),
    ("#########", "#   #   #", "#  #    #", "###     #", "#### P# #", "#    B# #", "##      #", "#      G#", "#########"),
    ("#########", "#   # ###", "## ##   #", "#   ### #", "## P    #", "# #   # #", "##G  B  #", "#     # #", "#########"),
    ("#########", "# ## #  #", "# # #   #", "#  G   ##", "#  #    #", "#       #", "#  B  P##", "##      #", "#########"),
)
COLORS = {
    "wall": (31, 52, 80), "floor": (12, 27, 48), "goal": (255, 200, 87),
    "box": (255, 107, 122), "player": (69, 217, 230), "box_goal": (92, 225, 161),
}
OBS_CACHE: dict[tuple[int, tuple[int, int], tuple[int, int]], bytes] = {}


class World:
    """Game physics only; no route, planner, labels, or coordinates are exposed to BPC."""

    def __init__(self, level: int):
        self.level = level
        self.walls, self.player_start, self.box_start, self.goal = set(), None, None, None
        for y, row in enumerate(LEVEL_MAPS[level]):
            for x, value in enumerate(row):
                if value == "#": self.walls.add((x, y))
                elif value == "P": self.player_start = (x, y)
                elif value == "B": self.box_start = (x, y)
                elif value == "G": self.goal = (x, y)
        assert self.player_start and self.box_start and self.goal
        self.reset()

    def reset(self) -> None:
        self.player, self.box, self.steps = self.player_start, self.box_start, 0
        self.terminal = self.success = self.last_changed = self.last_pushed = False

    def open(self, p: tuple[int, int]) -> bool:
        x, y = p
        return 0 < x < SIZE - 1 and 0 < y < SIZE - 1 and p not in self.walls

    def deadlocked(self) -> bool:
        if self.box == self.goal:
            return False
        x, y = self.box
        horizontal = not self.open((x - 1, y)) or not self.open((x + 1, y))
        vertical = not self.open((x, y - 1)) or not self.open((x, y + 1))
        return horizontal and vertical

    def step(self, action: int) -> dict[str, bool]:
        dx, dy = ACTIONS[action]
        before = self.player, self.box
        candidate = self.player[0] + dx, self.player[1] + dy
        if self.open(candidate):
            if candidate == self.box:
                beyond = self.box[0] + dx, self.box[1] + dy
                if self.open(beyond):
                    self.box, self.player = beyond, candidate
            else:
                self.player = candidate
        self.steps += 1
        self.last_changed = before != (self.player, self.box)
        self.last_pushed = before[1] != self.box
        self.success = self.box == self.goal
        self.terminal = self.success or self.deadlocked() or self.steps >= MAX_STEPS
        return {"changed": self.last_changed, "pushed": self.last_pushed,
                "success": self.success, "terminal": self.terminal}

    def cells(self) -> list[list[str]]:
        grid = [["wall"] * SIZE for _ in range(SIZE)]
        for y in range(1, SIZE - 1):
            for x in range(1, SIZE - 1):
                if (x, y) not in self.walls:
                    grid[y][x] = "floor"
        gx, gy = self.goal
        grid[gy][gx] = "goal"
        bx, by = self.box
        grid[by][bx] = "box_goal" if self.box == self.goal else "box"
        px, py = self.player
        grid[py][px] = "player"
        return grid

    def observation(self) -> bytes:
        # 9×9 RGB with the two high bits of each channel = 486 raw binary bits.
        key = self.level, self.player, self.box
        if key in OBS_CACHE:
            return OBS_CACHE[key]
        bits = bytearray()
        for row in self.cells():
            for cell in row:
                for channel in COLORS[cell]:
                    q = channel >> 6
                    bits.extend((q & 1, (q >> 1) & 1))
        OBS_CACHE[key] = bytes(bits)
        return OBS_CACHE[key]


@lru_cache(maxsize=None)
def canonical(bits: bytes) -> tuple[bytes, bool]:
    # Identity only: no mirror/rotation shortcut is available to the model.
    return bits, False


def canonical_action(action: int, reflected: bool) -> int:
    return 3 if reflected and action == 1 else 1 if reflected and action == 3 else action


def empty_counts() -> list[int]:
    return [0, 0, 0, 0]


class BPC:
    """Sparse state×action×outcome probability cube with exact Beta(1,1) counts."""

    def __init__(self, seed: int = SEED):
        self.counts: dict[bytes, list[int]] = defaultdict(empty_counts)
        self.trajectory: set[bytes] = set()
        self.rng = random.Random(seed)
        self.writes = 0

    @staticmethod
    def key(canonical_bits: bytes, action: int) -> bytes:
        return canonical_bits + bytes((action,))

    def reset_episode(self) -> None:
        self.trajectory.clear()

    def predict(self, bits: bytes) -> tuple[list[float], list[bytes]]:
        frame, reflected = canonical(bits)
        values, keys = [], []
        for action in range(4):
            key = self.key(frame, canonical_action(action, reflected))
            goal_yes, goal_n, move_yes, move_n = self.counts[key]
            p_goal = (goal_yes + 1) / (goal_n + 2)
            p_move = (move_yes + 1) / (move_n + 2)
            values.append(p_goal * p_move)
            keys.append(key)
        return values, keys

    def decide(self, bits: bytes, explore: bool) -> tuple[int, list[float]]:
        if explore:
            return self.rng.randrange(4), []
        values, _ = self.predict(bits)
        return max(range(4), key=values.__getitem__), values

    def observe(self, bits: bytes, action: int, changed: bool, terminal: bool,
                success: bool, learn: bool) -> None:
        frame, reflected = canonical(bits)
        key = self.key(frame, canonical_action(action, reflected))
        self.trajectory.add(key)
        if not learn:
            return
        row = self.counts[key]
        row[2] += int(changed)
        row[3] += 1
        self.writes += 1
        if terminal:
            for visited in self.trajectory:
                row = self.counts[visited]
                row[0] += int(success)
                row[1] += 1
                self.writes += 1

    def digest(self) -> str:
        packed = pickle.dumps(dict(sorted(self.counts.items())), protocol=5)
        return hashlib.sha256(packed).hexdigest()


def run_episode(model: BPC, level: int, explore: bool, learn: bool,
                trace: bool = False) -> tuple[bool, list[dict]]:
    world, frames = World(level), []
    model.reset_episode()
    while not world.terminal:
        before = world.observation()
        action, values = model.decide(before, explore)
        event = world.step(action)
        model.observe(before, action, event["changed"], event["terminal"], event["success"], learn)
        if trace:
            frames.append({"world": world, "action": action, "values": values})
    return world.success, frames


def evaluate(model: BPC, levels: tuple[int, ...], episodes: int = EVAL_EPISODES) -> dict[int, int]:
    return {level: sum(run_episode(model, level, False, False)[0] for _ in range(episodes)) for level in levels}


def train() -> dict:
    model = BPC()
    train_successes = {}
    for level in TRAIN_LEVELS:
        train_successes[level] = sum(run_episode(model, level, True, True)[0] for _ in range(TRAIN_EPISODES))
    before = model.writes
    frozen = evaluate(model, tuple(range(10)))
    zero = evaluate(BPC(7), tuple(range(10)))
    assert before == model.writes, "frozen evaluation wrote to memory"
    assert all(zero[level] == 0 for level in range(10)), zero
    trained_pass = all(frozen[level] == EVAL_EPISODES for level in TRAIN_LEVELS)
    unseen_passes = sum(frozen[level] == EVAL_EPISODES for level in TEST_LEVELS)
    adopted = trained_pass and unseen_passes == len(TEST_LEVELS)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as file:
        pickle.dump(model, file, protocol=5)
    result = {
        "format": "bpc-sokoban-python-diverse-cross-level-v2", "development_only": True,
        "blind_result": False, "agi_claim": False,
        "input": "9x9 RGB high-2-bit raw binary (486 bits)",
        "model": "one shared sparse BPC probability cube", "train_levels": [1, 3, 5, 7, 9],
        "unseen_levels": [2, 4, 6, 8, 10], "train_episodes_per_level": TRAIN_EPISODES,
        "train_successes": {str(k + 1): v for k, v in train_successes.items()},
        "frozen_successes": {str(k + 1): v for k, v in frozen.items()},
        "zero_control_successes": {str(k + 1): v for k, v in zero.items()},
        "frozen_persistent_writes": model.writes - before, "memory_cells": len(model.counts),
        "model_sha256": model.digest(), "trained_levels_passed": trained_pass,
        "unseen_levels_passed": unseen_passes, "adopted": adopted,
        "prior": "identity raw-frame query only; no mirror/rotation mapping and no planner",
        "boundary": "five independently generated held-out layouts; failure is retained; no AGI claim",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


def load_model() -> BPC:
    with MODEL_PATH.open("rb") as file:
        return pickle.load(file)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}", size)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int,
         color=(230, 239, 255), bold=False) -> None:
    draw.text(xy, value, font=font(size, bold), fill=color)


def render(world: World, action: int | None, values: list[float], condition: str,
           status: str, result: dict) -> Image.Image:
    img = Image.new("RGB", (1280, 720), (7, 16, 30))
    d = ImageDraw.Draw(img)
    ink, muted, cyan, gold, green, red = (230, 239, 255), (130, 151, 184), (69, 217, 230), (255, 200, 87), (92, 225, 161), (255, 107, 122)
    text(d, (18, 15), "BPC PLAYS 10 SOKOBAN MAZES", 28, ink, True)
    text(d, (18, 53), "486 raw visual bits → one frozen sparse probability cube → action → observed change", 14, muted)
    tag_color = cyan if condition == "TRAINED FROZEN" else gold
    text(d, (975, 24), f"LEVEL {world.level + 1}/10 · {condition}", 18, tag_color, True)
    panels = ((18, 90, 615, 590), (645, 90, 1262, 590))
    for box in panels:
        d.rounded_rectangle(box, 12, fill=(13, 25, 44), outline=(34, 54, 83), width=1)
    text(d, (34, 104), "LIVE BOARD", 20, ink, True)
    text(d, (34, 137), "No coordinates, object labels, route, search tree, or neural network.", 13, muted)
    cell, ox, oy = 41, 140, 180
    grid = world.cells()
    for y, row in enumerate(grid):
        for x, kind in enumerate(row):
            color = COLORS["floor"] if kind not in ("wall",) else COLORS["wall"]
            d.rounded_rectangle((ox + x * cell, oy + y * cell, ox + (x + 1) * cell - 4, oy + (y + 1) * cell - 4), 3, fill=color)
    gx, gy = world.goal
    cx, cy = ox + gx * cell + 18, oy + gy * cell + 18
    d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=gold)
    d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(7, 16, 30))
    bx, by = world.box
    box_color = green if world.success else red
    d.rectangle((ox + bx * cell + 9, oy + by * cell + 9, ox + bx * cell + 28, oy + by * cell + 28), fill=box_color)
    px, py = world.player
    pcx, pcy = ox + px * cell + 18, oy + py * cell + 18
    d.ellipse((pcx - 10, pcy - 10, pcx + 10, pcy + 10), fill=cyan)
    text(d, (54, 548), "CYAN: AGENT   RED: BOX   GOLD: GOAL   GREEN: COMPLETE", 14, ink)
    text(d, (661, 104), "SPARSE BPC QUERY + EVIDENCE", 20, ink, True)
    text(d, (661, 137), "Exact value = P(success) × P(change); bars are relative", 13, muted)
    peak = max(values, default=1.0) or 1.0
    for i, name in enumerate(ACTION_NAMES):
        y = 220 + i * 56
        value = values[i] if values else 0.0
        text(d, (675, y), name, 15, muted)
        d.rounded_rectangle((750, y + 2, 1110, y + 20), 8, fill=(21, 38, 64))
        d.rounded_rectangle((750, y + 2, 750 + int(360 * value / peak), y + 20), 8, fill=(69, 217, 230))
        text(d, (1125, y), f"{value:.2e}", 14, ink)
    action_text = "PREDICTING…" if action is None else f"EXECUTED: {ACTION_NAMES[action]}" + (" · PUSH" if world.last_pushed else "")
    if world.success:
        action_text += " · GOAL REACHED"
    text(d, (661, 470), action_text, 20, gold, True)
    text(d, (661, 512), "ONE SHARED MODEL · FROZEN WRITES = 0", 16, green, True)
    cards = ((18, 602, 310, 672), (324, 602, 616, 672), (630, 602, 950, 672), (964, 602, 1262, 672))
    unseen_total = sum(result["frozen_successes"][str(level)] for level in (2, 4, 6, 8, 10))
    zero_total = sum(result["zero_control_successes"].values())
    labels = (("TRAINED LEVELS", "1 · 3 · 5 · 7 · 9"), ("UNSEEN LEVELS", "2 · 4 · 6 · 8 · 10"),
              ("UNSEEN FROZEN EVAL", f"{unseen_total} / 160"), ("ZERO CONTROL / WRITES", f"{zero_total} / 320     ·     0"))
    for box, (label, value) in zip(cards, labels):
        d.rounded_rectangle(box, 10, fill=(13, 25, 44), outline=(34, 54, 83), width=1)
        text(d, (box[0] + 14, box[1] + 8), label, 12, muted)
        metric_color = red if label == "UNSEEN FROZEN EVAL" and unseen_total < 160 else green if "EVAL" in label or "WRITES" in label else ink
        text(d, (box[0] + 14, box[1] + 31), value, 18, metric_color, True)
    text(d, (18, 688), status, 13, green if world.success else red)
    return img


def record() -> None:
    model = load_model()
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    before = model.writes
    fps, step_frames, hold_frames = 30, 3, 10
    process = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", "1280x720", "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
        "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(VIDEO_PATH),
    ], stdin=subprocess.PIPE)
    poster = None
    for level in range(10):
        world = World(level)
        model.reset_episode()
        condition = "TRAINED FROZEN" if level in TRAIN_LEVELS else "UNSEEN FROZEN"
        values, _ = model.predict(world.observation())
        first = render(world, None, values, condition, "BOUNDARY: independent held-out layouts; pure direct policy; no planner or AGI claim.", result)
        for _ in range(hold_frames):
            process.stdin.write(first.tobytes())
        while not world.terminal:
            before_frame = world.observation()
            action, values = model.decide(before_frame, False)
            event = world.step(action)
            model.observe(before_frame, action, event["changed"], event["terminal"], event["success"], False)
            values, _ = model.predict(world.observation())
            frame = render(world, action, values, condition, "BOUNDARY: independent held-out layouts; pure direct policy; no planner or AGI claim.", result)
            for _ in range(step_frames):
                process.stdin.write(frame.tobytes())
        final_status = "LEVEL COMPLETE · NEXT LEVEL" if world.success else "LEVEL FAILED · DEADLOCK OR STEP LIMIT · FROZEN WRITES = 0"
        if level == 9:
            final_status = "DIVERSE UNSEEN RESULT: 0 / 160 · NOT ADOPTED · FROZEN WRITES = 0"
        poster = render(world, action, values, condition, final_status, result)
        for _ in range(hold_frames if level < 9 else fps * 2):
            process.stdin.write(poster.tobytes())
    process.stdin.close()
    assert process.wait() == 0
    assert before == model.writes
    poster.save(POSTER_PATH)
    print(f"VIDEO_READY {VIDEO_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("train", "test", "record", "all"), nargs="?", default="all")
    args = parser.parse_args()
    if args.command in ("train", "all"):
        train()
    if args.command == "test":
        model, result = load_model(), json.loads(RESULT_PATH.read_text())
        before = model.writes
        frozen = evaluate(model, tuple(range(10)))
        assert before == model.writes
        print("BPC_TEST_RESULT", frozen, "writes=0", "adopted=", result["adopted"], result["model_sha256"])
    if args.command in ("record", "all"):
        record()


if __name__ == "__main__":
    main()
