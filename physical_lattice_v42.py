#!/usr/bin/env python3
"""Independent raw-pixel domain: simultaneous particles under global force."""
import random

SIDE=8;CELLS=SIDE*SIDE
DIRECTIONS=((-1,0),(0,1),(1,0),(0,-1))


def random_lattice(rng,wall_rate,particle_rate):
    cells=[]
    for y in range(SIDE):
        for x in range(SIDE):
            boundary=x in (0,SIDE-1) or y in (0,SIDE-1);wall=boundary or rng.random()<wall_rate
            cells.append(1 if wall else (2 if rng.random()<particle_rate else 0))
    return bytes(cells)


def step_lattice(state,action):
    dy,dx=DIRECTIONS[action];particles={i for i,value in enumerate(state) if value&2};moves=[]
    for source in particles:
        y,x=divmod(source,SIDE);target=(y+dy)*SIDE+x+dx
        if not state[target]&1 and target not in particles:moves.append((source,target))
    output=bytearray(state)
    for source,target in moves:output[source]&=~2;output[target]|=2
    return bytes(output)
