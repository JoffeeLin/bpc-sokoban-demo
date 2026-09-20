#!/usr/bin/env python3
"""Task-agnostic BPC-0 residual field over distributed raw binary relations.

The encoder never hashes a complete observation. Raw fixed-width bit groups enter
as many overlapping ordered relations; surface-different inputs therefore share
addresses whenever some raw relations recur. Every active component participates
in the normalized probability read and y-p writeback.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _mix64(value: np.ndarray) -> np.ndarray:
    """Stable anonymous address/phase mixing; uint64 overflow is intentional."""
    with np.errstate(over="ignore"):
        value = (value ^ (value >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        value = (value ^ (value >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return value ^ (value >> np.uint64(31))


class BinaryRelationWave:
    """Map raw binary voxel state to a normalized distributed matter wave.

    Grouping is purely physical (adjacent channel bits per cell). No group value
    is named or interpreted. ``position_locked`` exists only as a causal control.
    """

    def __init__(self, height: int, width: int, channels: int, dimensions: int = 1024,
                 position_locked: bool = False):
        self.height, self.width, self.channels = height, width, channels
        self.dimensions, self.position_locked = dimensions, position_locked
        self.cache: dict[bytes, np.ndarray] = {}
        y, x = np.indices((height, width), dtype=np.int64)
        self.x, self.y = x.ravel(), y.ravel()
        n = height * width
        self.left = np.repeat(np.arange(n, dtype=np.int64), n)
        self.right = np.tile(np.arange(n, dtype=np.int64), n)
        self.dx = self.x[self.right] - self.x[self.left]
        self.dy = self.y[self.right] - self.y[self.left]
        self.bit_weights = (np.uint64(1) << np.arange(channels, dtype=np.uint64))

    def _tokens(self, raw_bits: bytes) -> np.ndarray:
        bits = np.frombuffer(raw_bits, dtype=np.uint8)
        expected = self.height * self.width * self.channels
        if bits.size != expected or np.any(bits > 1):
            raise ValueError(f"expected {expected} raw binary voxels")
        return (bits.reshape(-1, self.channels).astype(np.uint64) * self.bit_weights).sum(axis=1)

    def encode(self, raw_bits: bytes) -> np.ndarray:
        cached = self.cache.get(raw_bits)
        if cached is not None:
            return cached
        token = self._tokens(raw_bits)
        packed = token[self.left] | (token[self.right] << np.uint64(self.channels))
        packed |= (self.dx + self.width).astype(np.uint64) << np.uint64(2 * self.channels)
        packed |= (self.dy + self.height).astype(np.uint64) << np.uint64(2 * self.channels + 5)
        if self.position_locked:
            packed ^= self.x[self.left].astype(np.uint64) << np.uint64(2 * self.channels + 10)
            packed ^= self.y[self.left].astype(np.uint64) << np.uint64(2 * self.channels + 14)
        mixed = _mix64(packed + np.uint64(0x9E3779B97F4A7C15))
        address = (mixed % np.uint64(self.dimensions)).astype(np.int64)
        phase = np.where((mixed >> np.uint64(63)) == 0, 1.0, -1.0)
        wave = np.bincount(address, weights=phase, minlength=self.dimensions).astype(np.float64)
        norm = float(np.linalg.norm(wave))
        if norm:
            wave /= norm
        wave.setflags(write=False)
        self.cache[raw_bits] = wave
        return wave


@dataclass
class GeneralBPC:
    """BPC-0 probabilities for a finite external action boundary.

    ``goal`` and ``change`` are anonymous binary events. The environment chooses
    what reality bit is supplied; the field only performs normalized interference
    and error writeback.
    """

    actions: int
    dimensions: int
    learning_rate: float = 0.12

    def __post_init__(self) -> None:
        self.goal_residual = np.zeros((self.actions, self.dimensions), dtype=np.float64)
        self.change_residual = np.zeros_like(self.goal_residual)
        self.goal_bias = np.zeros(self.actions, dtype=np.float64)
        self.change_bias = np.zeros(self.actions, dtype=np.float64)
        self.writes = 0

    @staticmethod
    def _sigmoid(value: np.ndarray | float) -> np.ndarray | float:
        return 1.0 / (1.0 + np.exp(-np.clip(value, -30.0, 30.0)))

    def probabilities(self, wave: np.ndarray, use_change: bool = True) -> np.ndarray:
        goal = self._sigmoid(self.goal_residual @ wave + self.goal_bias)
        if not use_change:
            return np.asarray(goal)
        change = self._sigmoid(self.change_residual @ wave + self.change_bias)
        return np.asarray(goal) * (0.5 + 0.5 * np.asarray(change))

    def decide(self, wave: np.ndarray, use_change: bool = True) -> tuple[int, np.ndarray]:
        probabilities = self.probabilities(wave, use_change)
        return int(np.argmax(probabilities)), probabilities

    def observe(self, wave: np.ndarray, action: int, future_success: bool,
                changed: bool, learn: bool = True) -> None:
        if not learn:
            return
        goal_p = float(self._sigmoid(self.goal_residual[action] @ wave + self.goal_bias[action]))
        change_p = float(self._sigmoid(self.change_residual[action] @ wave + self.change_bias[action]))
        goal_error, change_error = float(future_success) - goal_p, float(changed) - change_p
        rate = self.learning_rate
        self.goal_residual[action] += rate * goal_error * wave
        self.change_residual[action] += rate * change_error * wave
        self.goal_bias[action] += rate * goal_error / self.dimensions**0.5
        self.change_bias[action] += rate * change_error / self.dimensions**0.5
        np.clip(self.goal_residual[action], -8.0, 8.0, out=self.goal_residual[action])
        np.clip(self.change_residual[action], -8.0, 8.0, out=self.change_residual[action])
        self.writes += 2

    def digest(self) -> str:
        import hashlib
        return hashlib.sha256(b"".join((self.goal_residual.tobytes(), self.change_residual.tobytes(),
                                        self.goal_bias.tobytes(), self.change_bias.tobytes()))).hexdigest()
