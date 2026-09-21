#!/usr/bin/env python3
"""Raw physical domain with barriers, particles and causal persistent terrain."""
import random

SIDE=8;CELLS=SIDE*SIDE
DIRECTIONS=((-1,0),(0,1),(1,0),(0,-1))


def random_lattice(rng,wall_rate,particle_rate,phase_rate):
    cells=[]
    for y in range(SIDE):
        for x in range(SIDE):
            phase=int(rng.random()<phase_rate)<<2;boundary=x in (0,SIDE-1) or y in (0,SIDE-1);wall=boundary or rng.random()<wall_rate
            cells.append(phase|1 if wall else phase|(int(rng.random()<particle_rate)<<1))
    return bytes(cells)


def step_lattice(state,action):
    dy,dx=DIRECTIONS[action];particles={i for i,value in enumerate(state) if value&2};moves=[]
    for source in particles:
        y,x=divmod(source,SIDE);target=(y+dy)*SIDE+x+dx
        if not state[target]&3 and (state[target]>>2&1)==(action&1):moves.append((source,target))
    output=bytearray(state)
    for source,target in moves:output[source]&=~2;output[target]|=2
    return bytes(output)
