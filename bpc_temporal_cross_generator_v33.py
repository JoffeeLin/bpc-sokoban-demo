#!/usr/bin/env python3
"""Independent joint-world generator for the v0.33 temporal-policy freeze."""
import random

from bpc_fourth_factor_v28 import _world,shortest
from bpc_three_factor_v12 import key


def candidate(rng):
    """Separate doorway and object rows; D4 then hides the construction frame."""
    gate_y=rng.randrange(1,6);box_y=rng.choice((2,3,4));left=[(x,y) for x in (1,2) for y in range(1,6)]
    agent,switch=rng.sample(left,2);gate=(3,gate_y);box=(4,box_y);alcove=(5,box_y)
    walls={(3,y) for y in range(1,6) if y!=gate_y}|{(5,box_y-1),(5,box_y+1)}
    far=[(x,y) for x in (4,5) for y in range(1,6) if (x,y) not in walls|{box,alcove}];loose=rng.choice(far)
    reserved={agent,switch,gate,box,alcove,loose};extra=[(x,y) for x in (1,2,4,5) for y in range(1,6) if (x,y) not in reserved|walls]
    walls|=set(rng.sample(extra,rng.randrange(0,min(5,len(extra)+1))))
    return _world(agent,(box,),(alcove,loose),(switch,),(gate,),walls,rng.randrange(8))


def generate(seed,total,exclude=()):
    rng=random.Random(seed);exclude=set(exclude);seen=set();out=[];patterns=[];attempts=0
    while len(out)<total and attempts<total*20000:
        attempts+=1;world=candidate(rng);identity=key(world);distance=shortest(world)
        if identity in exclude or identity in seen or distance is None or not 8<=distance<=24:continue
        if shortest(world,True) is not None or shortest(world,False,True) is not None:continue
        border=sum(1<<(y*world.w+x) for y in range(world.h) for x in range(world.w) if x in (0,world.w-1) or y in (0,world.h-1));pattern=world.walls&~border
        if any((pattern&old).bit_count()/max(1,(pattern|old).bit_count())>.75 for old in patterns):continue
        seen.add(identity);patterns.append(pattern);out.append(('four',world,distance))
    if len(out)<total:raise RuntimeError(f'only {len(out)} independent worlds in {attempts} attempts')
    return out,attempts
