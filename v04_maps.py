#!/usr/bin/env python3
"""Deterministic v0.4 holdout generation; solution actions never reach BPC."""
from __future__ import annotations

import random
from collections import deque

from bpc_learned_wave_v04 import Level,bit,positions,truth_step


def distance(level:Level,limit:int=300_000):
    start=(level.boxes,level.player); queue=deque([(start,0)]); seen={start}
    while queue and len(seen)<limit:
        (boxes,player),steps=queue.popleft()
        if boxes==level.goals:return steps,len(seen)
        for action in range(4):
            state=truth_step(level,boxes,player,action)
            if state not in seen:seen.add(state);queue.append((state,steps+1))
    return None,len(seen)


def generate(count:int,seed:int):
    rng=random.Random(seed); output=[]; used=set(); attempts=0
    while len(output)<count:
        attempts+=1
        if attempts>100_000:raise RuntimeError('holdout generation exhausted')
        boxes_count=1+len(output)%4; side=6+min(boxes_count,3)
        h=w=side; border={y*w+x for y in range(h) for x in range(w)
                         if x in (0,w-1) or y in (0,h-1)}
        inside=[y*w+x for y in range(1,h-1) for x in range(1,w-1)]
        walls=border|set(rng.sample(inside,rng.randrange(0,min(5,len(inside)-2*boxes_count))))
        free=[i for i in inside if i not in walls]
        if len(free)<2*boxes_count+1:continue
        picked=rng.sample(free,2*boxes_count+1); player=picked[0]
        boxes=sum(1<<i for i in picked[1:1+boxes_count]); goals=sum(1<<i for i in picked[1+boxes_count:])
        level=Level(h,w,sum(1<<i for i in walls),goals,player,boxes)
        signature=(h,w,level.walls,goals,player,boxes)
        if signature in used:continue
        shortest,states=distance(level)
        if shortest is None or not 3+boxes_count<=shortest<=42:continue
        output.append((level,shortest,states));used.add(signature)
    return tuple(output)


def text(level:Level):
    rows=[]
    for y in range(level.h):
        row=[]
        for x in range(level.w):
            i=y*level.w+x; ch='#' if bit(level.walls,i) else '.' if bit(level.goals,i) else ' '
            if bit(level.boxes,i):ch='*' if bit(level.goals,i) else '$'
            if i==level.player:ch='+' if bit(level.goals,i) else '@'
            row.append(ch)
        rows.append(''.join(row))
    return '\n'.join(rows)


def from_text(value:str):
    from bpc_learned_wave_v04 import parse
    return parse(value)
