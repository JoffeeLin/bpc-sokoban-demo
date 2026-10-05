#!/usr/bin/env python3
"""Verify physical experiments and documented rejection, not model internals."""
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
mode, out_arg = sys.argv[1:]
out = Path(out_arg)
summary = json.loads((root / "SUMMARY.json").read_text())


def read(name):
    return (out / name).read_text()


def clean(s):
    return re.sub(r" CPU_SECONDS=[0-9.]+", "", s)


def rows(name, prefix):
    return [dict(re.findall(r"(\w+)=([^ ]+)", line))
            for line in read(name).splitlines() if line.startswith(prefix)]


def pair(s):
    assert "identical_current_and_last_3_frames=1" in s and "different_next=1" in s
    probe = [line for line in s.splitlines() if "PAIR_PROBE memory=1 noops=200 mode=0" in line]
    assert len(probe) == 1 and "exact=2/2" in probe[0]
    closed = [line for line in s.splitlines() if "PAIR_SELF_ROLLOUT memory=1" in line]
    assert len(closed) == 2 and all("whole_exact=1" in line and "steps=226" in line for line in closed)
    assert "PAIR_PROBE memory=1 noops=200 mode=2 exact=0/2" in s
    assert s.count("PAIR_BYTES_HASH_FROZEN=1") == 2


reference = read("O2/pair.txt")
pair(reference)
for variant in ["O3", "ubsan"]:
    assert clean(reference) == clean(read(f"{variant}/pair.txt"))
for variant in ["O2", "O3", "ubsan", "local"]:
    assert not read(f"{variant}/stderr.txt")
local = read("local/pair.txt")
assert local.count("whole_exact=0") == 4
assert "global_support=0" in local
for name, meta in summary["pair_fields"].items():
    assert hashlib.sha256((out / "O2" / name).read_bytes()).hexdigest() == meta["sha256"]
print("PHYSICAL_ALIAS_AND_MEMORY_CONTROL_REPRODUCED; O2/O3/UBSAN_AGREE")
if mode == "quick":
    sys.exit(0)
assert mode == "full"
for variant in ["memory", "raw"]:
    meta = summary["full_fields"][variant]
    assert hashlib.sha256((out / f"{variant}.bin").read_bytes()).hexdigest() == meta["sha256"]
    actual = rows(f"{variant}_original_self.txt", "SELF ") + rows(f"{variant}_reserved_self.txt", "SELF ")
    totals = lambda key, idx: sum(int(r[key].split("/")[idx]) for r in actual)
    expected = summary["full_game"][variant]
    assert [totals("exact", 0), totals("exact", 1)] == expected["checked_prefix_exact"]
    assert totals("failed_episodes", 0) == 12000
    assert sum(int(r["real_steps"]) for r in actual) == 468734
    play = rows(f"{variant}_reserved_play.txt", "PLAY_SELF ")
    assert [sum(int(r["exact"].split("/")[i]) for r in play) for i in [0, 1]] == expected["play_exact"]
    for suffix in ["original_self", "reserved_self", "reserved_play", "controls"]:
        assert "FIELD_BYTES_HASH_FROZEN=1" in read(f"{variant}_{suffix}.txt")
assert "TOTAL_TEACHER exact=7328/155895" in read("memory_teacher.txt")
assert "TOTAL 155895/155895" in read("baseline_reserved_self.txt")
assert "FROZEN_BYTE_IDENTICAL=1" in read("baseline_reserved_self.txt")
for what in ["eval", "play"]:
    for variant in ["O3", "ubsan"]:
        assert clean(read(f"O2_{what}.txt")) == clean(read(f"{variant}_{what}.txt"))
assert (out / "memory.bin").read_bytes() == (out / "O3_memory.bin").read_bytes()
print("REPRODUCED_REJECTED_FULL_GAME_CANDIDATE; BASELINE_PRESERVED")
