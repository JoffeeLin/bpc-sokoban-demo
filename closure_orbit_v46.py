#!/usr/bin/env python3
"""Rotation-orbit physical experience for the unchanged one-bit-port core."""
import random

from bpc_cross_task_v07 import ACTIONS
from bpc_three_factor_v12 import World3,key
from closure_probe_v45 import probe


def rotate_point(point,turns):
    x,y=point
    for _ in range(turns):x,y=6-y,x
    return x,y
def rotate_index(index,turns):return rotate_point((index%7,index//7),turns)[1]*7+rotate_point((index%7,index//7),turns)[0]
def rotate_bits(bits,turns):return sum(1<<rotate_index(index,turns) for index in range(49) if bits>>index&1)
def rotate_action(action,turns):
    dx,dy=ACTIONS[action]
    for _ in range(turns):dx,dy=-dy,dx
    return ACTIONS.index((dx,dy))
def rotate_world(world,turns):return World3(7,7,rotate_bits(world.walls,turns),rotate_index(world.agent,turns),rotate_bits(world.objects,turns),rotate_bits(world.marks,turns),rotate_bits(world.switches,turns),rotate_bits(world.gates,turns))


def orbit_suite(seed,bases,exclude=()):
    rng=random.Random(seed);exclude=set(exclude);seen=set();out=[];attempts=0
    while len(out)<bases*4:
        attempts+=1;base=probe(rng,1);orbit=[(rotate_world(base,turns),rotate_action(1,turns)) for turns in range(4)];signatures={key(world) for world,_ in orbit}
        if len(signatures)<4 or signatures&exclude or signatures&seen:continue
        seen|=signatures;out.extend(orbit)
    return out,seen,attempts
