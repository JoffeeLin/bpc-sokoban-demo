#!/usr/bin/env python3
"""BPC v6: anonymous spatial residues and probability-only action binding.

The encoder receives raw fixed-width binary voxel groups.  It assigns no names
to voxel values.  Rare groups become temporary residues; pair/triple offsets
and nearby raw matter form reusable probability conditions.  A one-step
transition residue is transported through the episode by actual actions and
observed raw change.  The external boundary samples the resulting probability.
"""

from __future__ import annotations

import hashlib
import math
import pickle
from collections import defaultdict

import numpy as np


def _counts() -> np.ndarray:
    return np.zeros(4, dtype=np.uint32)


class SpatialResidueBPC:
    def __init__(self, height: int = 9, width: int = 9, channels: int = 6,
                 radius: int = 4, rarity: int = 2):
        self.height, self.width, self.channels = height, width, channels
        self.radius, self.rarity = radius, rarity
        self.weights = 1 << np.arange(channels, dtype=np.uint16)
        self.table: dict[tuple, np.ndarray] = defaultdict(_counts)
        self.global_counts = np.zeros(4, dtype=np.uint32)
        self.previous_action: int | None = None
        self.previous_raw: bytes | None = None
        self.cache: dict[bytes, tuple[tuple, ...]] = {}
        self.writes = 0

    def reset_episode(self) -> None:
        self.previous_action = None
        self.previous_raw = None

    def _tokens(self, raw: bytes) -> np.ndarray:
        bits = np.frombuffer(raw, dtype=np.uint8)
        if bits.size != self.height * self.width * self.channels or np.any(bits > 1):
            raise ValueError("invalid raw voxel packet")
        return (bits.reshape(-1, self.channels).astype(np.uint16) * self.weights).sum(1).reshape(self.height, self.width)

    def _rare(self, tokens: np.ndarray) -> list[tuple[int, int, int]]:
        values, counts = np.unique(tokens, return_counts=True)
        allowed = set(map(int, values[counts <= self.rarity]))
        return [(int(tokens[y, x]), x, y) for y in range(self.height)
                for x in range(self.width) if int(tokens[y, x]) in allowed]

    def features(self, raw: bytes, transported: bool = True) -> tuple[tuple, ...]:
        tokens = self._tokens(raw)
        cached = self.cache.get(raw)
        if cached is None:
            output, rare = [], self._rare(tokens)
            # Anonymous rare-to-rare relations preserve direction and distance.
            for lv, lx, ly in rare:
                output.append((0, lv))
                for rv, rx, ry in rare:
                    output.append((1, lv, rv, rx - lx, ry - ly))
                # Nearby raw matter lets the same relation react to local walls.
                for y in range(max(0, ly - self.radius), min(self.height, ly + self.radius + 1)):
                    for x in range(max(0, lx - self.radius), min(self.width, lx + self.radius + 1)):
                        output.append((2, lv, int(tokens[y, x]), x - lx, y - ly))
            # Three anonymous residues express player/box/goal-like configurations
            # without assigning any of those names to raw values.
            for ov, ox, oy in rare:
                for av, ax, ay in rare:
                    for bv, bx, by in rare:
                        output.append((3, ov, av, bv, ax - ox, ay - oy, bx - ox, by - oy))
            cached = tuple(output)
            self.cache[raw] = cached
        output, rare = list(cached), self._rare(tokens)
        if transported and self.previous_action is not None and self.previous_raw is not None:
            before = self._tokens(self.previous_raw)
            changed = np.argwhere(before != tokens)
            # Only reality-derived change positions enter the persistent process
            # residue; no object identity or hidden coordinate is supplied.
            signature = tuple(sorted((int(tokens[y, x]), int(x), int(y)) for y, x in changed))
            output.append((4, self.previous_action, signature))
            for value, x, y in rare:
                output.append((5, self.previous_action, value, x, y, signature))
        return tuple(output)

    def observe_success_path(self, path: list[tuple[bytes, int, bytes]], transported: bool = True) -> None:
        self.reset_episode()
        for raw, action, next_raw in path:
            for feature in self.features(raw, transported):
                self.table[feature][action] += 1
            self.global_counts[action] += 1
            self.previous_raw, self.previous_action = raw, action
            self.writes += 1
        self.reset_episode()

    def probabilities(self, raw: bytes, transported: bool = True,
                      temperature: float = 0.72) -> np.ndarray:
        features = self.features(raw, transported)
        family_logp = {kind: np.zeros(4, dtype=np.float64) for kind in range(6)}
        family_weight = {kind: 0.0 for kind in range(6)}
        for feature in features:
            row = self.table.get(feature)
            if row is None:
                continue
            n = int(row.sum())
            if n < 2:
                continue
            weight = min(4.0, math.log1p(n))
            kind = feature[0]
            family_logp[kind] += weight * np.log((row + 1.0) / (n + 4.0))
            family_weight[kind] += weight
        prior = (self.global_counts + 1.0) / (int(self.global_counts.sum()) + 4.0)
        active = [family_logp[kind] / family_weight[kind]
                  for kind in family_logp if family_weight[kind]]
        logits = np.log(prior) if not active else np.mean(active, axis=0) + 0.15 * np.log(prior)
        logits = (logits - logits.max()) / temperature
        p = np.exp(logits)
        return p / p.sum()

    def advance(self, raw: bytes, action: int) -> None:
        self.previous_raw, self.previous_action = raw, action

    def rotated(self) -> "SpatialResidueBPC":
        model = pickle.loads(pickle.dumps(self, protocol=5))
        model.global_counts = np.roll(model.global_counts, 1)
        for key in model.table:
            model.table[key] = np.roll(model.table[key], 1)
        return model

    def digest(self) -> str:
        rows = [(key, tuple(map(int, value))) for key, value in sorted(self.table.items(), key=lambda item: repr(item[0]))]
        return hashlib.sha256(pickle.dumps((rows, tuple(map(int, self.global_counts))), protocol=5)).hexdigest()
