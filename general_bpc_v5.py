#!/usr/bin/env python3
"""GeneralBPC v5: distributed raw relations, joint supports, and y-p writeback.

This module is task-agnostic. It knows only a rectangular field of fixed-width
raw binary voxel groups and a finite external action boundary. Low-frequency
groups are anonymous addressing anchors; their values never receive names.
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass

import numpy as np

MASK64 = (1 << 64) - 1


def mix64(value: int) -> int:
    value &= MASK64
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
    return value ^ (value >> 31)


class RawRelationEncoder:
    """Create a normalized matter wave without hashing the complete input."""

    def __init__(self, height: int, width: int, channels: int, dimensions: int,
                 radius: int = 4, rarity_limit: int = 2, joint: bool = True):
        self.height, self.width, self.channels = height, width, channels
        self.dimensions, self.radius = dimensions, radius
        self.rarity_limit, self.joint = rarity_limit, joint
        y, x = np.indices((height, width))
        self.x, self.y = x.ravel(), y.ravel()
        self.weights = 1 << np.arange(channels, dtype=np.uint64)
        self.cache: dict[bytes, np.ndarray] = {}

    def _tap(self, wave: np.ndarray, key: int) -> None:
        value = mix64(key + 0x9E3779B97F4A7C15)
        wave[value % self.dimensions] += 1.0 if value >> 63 == 0 else -1.0

    def encode(self, raw_bits: bytes) -> np.ndarray:
        cached = self.cache.get(raw_bits)
        if cached is not None:
            return cached
        bits = np.frombuffer(raw_bits, dtype=np.uint8)
        expected = self.height * self.width * self.channels
        if bits.size != expected or np.any(bits > 1):
            raise ValueError(f"expected {expected} raw binary voxels")
        token = (bits.reshape(-1, self.channels).astype(np.uint64) * self.weights).sum(1)
        values, counts = np.unique(token, return_counts=True)
        rare = set(map(int, values[counts <= self.rarity_limit]))
        anchors = [index for index, value in enumerate(token) if int(value) in rare]
        wave = np.zeros(self.dimensions, dtype=np.float32)
        for left in anchors:
            for right in anchors:
                self._tap(wave, self._pair_key(token, left, right))
            for right in range(token.size):
                if (abs(int(self.x[right] - self.x[left])) <= self.radius and
                        abs(int(self.y[right] - self.y[left])) <= self.radius):
                    self._tap(wave, self._pair_key(token, left, right))
        if self.joint:
            for origin, second, third in itertools.product(anchors, repeat=3):
                key = (int(token[origin]) | (int(token[second]) << 6) | (int(token[third]) << 12) |
                       ((int(self.x[second] - self.x[origin]) + self.width - 1) << 18) |
                       ((int(self.y[second] - self.y[origin]) + self.height - 1) << 23) |
                       ((int(self.x[third] - self.x[origin]) + self.width - 1) << 28) |
                       ((int(self.y[third] - self.y[origin]) + self.height - 1) << 33) | (1 << 38))
                self._tap(wave, key)
        norm = float(np.linalg.norm(wave))
        if norm:
            wave /= norm
        wave.setflags(write=False)
        self.cache[raw_bits] = wave
        return wave

    def _pair_key(self, token: np.ndarray, left: int, right: int) -> int:
        return (int(token[left]) | (int(token[right]) << 6) |
                ((int(self.x[right] - self.x[left]) + self.width - 1) << 12) |
                ((int(self.y[right] - self.y[left]) + self.height - 1) << 17))


@dataclass
class ActionWaveBPC:
    actions: int
    dimensions: int

    def __post_init__(self) -> None:
        self.residual = np.zeros((self.actions, self.dimensions), dtype=np.float32)
        self.bias = np.zeros(self.actions, dtype=np.float64)
        self.writes = 0

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - np.max(logits, axis=-1, keepdims=True)
        values = np.exp(shifted)
        return values / values.sum(axis=-1, keepdims=True)

    def fit(self, counts: dict[bytes, list[int]], encoder: RawRelationEncoder,
            epochs: int = 300, learning_rate: float = 3.0) -> None:
        states, targets, reliability = [], [], []
        for raw_bits, row in counts.items():
            action_counts = np.asarray(row, dtype=np.float64)
            states.append(encoder.encode(raw_bits))
            targets.append((action_counts + 1.0) / (action_counts.sum() + self.actions))
            reliability.append(np.log1p(action_counts.sum()))
        matrix = np.stack(states).astype(np.float32)
        target = np.stack(targets)
        weight = np.asarray(reliability)
        scale = weight.sum() + 1e-12
        for _ in range(epochs):
            probability = self._softmax(matrix @ self.residual.T + self.bias)
            error = (target - probability) * weight[:, None]
            self.residual += (learning_rate * (error.T @ matrix) / scale).astype(np.float32)
            self.bias += learning_rate * error.sum(0) / scale
        self.writes += epochs * len(counts)

    def probabilities(self, wave: np.ndarray, temperature: float = 0.75) -> np.ndarray:
        return self._softmax(((self.residual @ wave + self.bias) / temperature)[None, :])[0]

    def rotated(self, amount: int = 1) -> "ActionWaveBPC":
        model = ActionWaveBPC(self.actions, self.dimensions)
        model.residual = np.roll(self.residual, amount, axis=0)
        model.bias = np.roll(self.bias, amount)
        model.writes = self.writes
        return model

    def digest(self) -> str:
        return hashlib.sha256(self.residual.tobytes() + self.bias.tobytes()).hexdigest()
