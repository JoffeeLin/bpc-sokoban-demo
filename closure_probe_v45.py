#!/usr/bin/env python3
"""External one-step closure worlds; the model receives only anonymous bytes."""
import random

from bpc_cross_task_v07 import ACTIONS
from bpc_fourth_factor_v28 import step
from bpc_three_factor_v12 import World3,key


def probe(rng,closing_action):
    w=h=7;border={y*w+x for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)};dx,dy=ACTIONS[closing_action]
    candidates=[(x,y) for y in range(2,5) for x in range(2,5)];ax,ay=rng.choice(candidates);agent=ay*w+ax;target=(ay+dy)*w+ax+dx;reserved={agent,target}
    free=[y*w+x for y in range(1,6) for x in range(1,6) if y*w+x not in reserved];rng.shuffle(free);wall_count=rng.randrange(0,7);walls=set(free[:wall_count]);free=[i for i in free if i not in walls]
    object_count=rng.randrange(0,3);objects=set(free[:object_count]);free=free[object_count:];switches=set(free[:rng.randrange(0,2)]);free=[i for i in free if i not in switches];gates=set(free[:rng.randrange(0,3)])
    world=World3(h,w,sum(1<<i for i in border|walls),agent,sum(1<<i for i in objects),1<<target,sum(1<<i for i in switches),sum(1<<i for i in gates))
    assert step(world,closing_action).marks==0 and all(step(world,a).marks!=0 for a in range(4) if a!=closing_action)
    return world


def suite(seed,count,exclude=()):
    rng=random.Random(seed);exclude=set(exclude);seen=set();out=[];attempts=0
    while len(out)<count:
        attempts+=1;action=len(out)%4;world=probe(rng,action);signature=key(world)
        if signature in exclude or signature in seen:continue
        seen.add(signature);out.append((world,action))
    return out,seen,attempts
