#!/usr/bin/env python3
"""Deterministic offline Sokoban map generation and audit helpers."""
from __future__ import annotations

import hashlib, random
from collections import deque

import bpc_sokoban as game


def parse(level):
    walls=set(); player=box=goal=None
    for y,row in enumerate(level):
        for x,value in enumerate(row):
            if value=='#': walls.add((x,y))
            elif value=='P': player=(x,y)
            elif value=='B': box=(x,y)
            elif value=='G': goal=(x,y)
    assert player is not None and box is not None and goal is not None
    return walls,player,box,goal


def solution_distance(level):
    """Shortest distance is used only as an offline difficulty filter."""
    walls,player,box,goal=parse(level)
    queue=deque([(player,box,0)]); seen={(player,box)}
    while queue:
        player,box,distance=queue.popleft()
        if box==goal: return distance
        for dx,dy in game.ACTIONS:
            candidate=(player[0]+dx,player[1]+dy); next_box=box
            if candidate in walls: continue
            if candidate==box:
                next_box=(box[0]+dx,box[1]+dy)
                if next_box in walls: continue
            state=(candidate,next_box)
            if state not in seen:
                seen.add(state); queue.append((candidate,next_box,distance+1))
    return None


def generate(count,seed,distance=(5,10),wall_count=(7,12),max_jaccard=.50):
    """Generate diverse maps; never expose a route or action to the model."""
    rng=random.Random(seed); output=[]; wall_sets=[]
    inside=[(x,y) for y in range(1,8) for x in range(1,8)]
    while len(output)<count:
        walls=set(rng.sample(inside,rng.randint(*wall_count)))
        free=[position for position in inside if position not in walls]
        player,box,goal=rng.sample(free,3)
        rows=[['#']*9 for _ in range(9)]
        for y in range(1,8):
            for x in range(1,8): rows[y][x]='#' if (x,y) in walls else ' '
        for position,value in ((player,'P'),(box,'B'),(goal,'G')):
            rows[position[1]][position[0]]=value
        level=tuple(''.join(row) for row in rows); steps=solution_distance(level)
        if steps is None or not distance[0]<=steps<=distance[1]: continue
        if any(len(walls&old)/len(walls|old)>max_jaccard for old in wall_sets): continue
        output.append(level); wall_sets.append(walls)
    return tuple(output)


def digest(maps):
    payload='\n\n'.join('\n'.join(level) for level in maps).encode()
    return hashlib.sha256(payload).hexdigest()


def max_wall_jaccard(left,right=None):
    def internal(level):
        return {(x,y) for x,y in parse(level)[0] if 0<x<8 and 0<y<8}
    a=[internal(level) for level in left]
    b=a if right is None else [internal(level) for level in right]
    pairs=((x,y) for i,x in enumerate(a) for j,y in enumerate(b)
           if right is not None or i<j)
    return max((len(x&y)/len(x|y) for x,y in pairs),default=0.)
