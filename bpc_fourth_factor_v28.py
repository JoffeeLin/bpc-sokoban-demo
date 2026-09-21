#!/usr/bin/env python3
"""BPC v0.28: a fourth anonymous raw-change factor and joint worlds."""
import random
from collections import Counter,deque

from bpc_cross_task_v07 import ACTIONS,bit
from bpc_direct_composition_v09 import choose
from bpc_three_factor_v12 import World3,changed_planes,key,moved,raw


def step(world,action,fixed_objects=False,fixed_gates=False):
    """Old dynamics plus one raw interaction: a moved object clears its destination bit 3."""
    near=moved(world,world.agent,action);objects,marks,switches,gates=world.objects,world.marks,world.switches,world.gates
    if near<0 or bit(world.walls|gates,near):return world
    pushed=False;far=-1
    if bit(objects,near):
        if fixed_objects:return world
        far=moved(world,world.agent,action,2)
        if far<0 or bit(world.walls|objects|gates,far):return world
        objects^=(1<<near)|(1<<far);pushed=True
    marks&=~(1<<near)
    if pushed:marks&=~(1<<far)
    if bit(switches,near):
        switches&=~(1<<near)
        if not fixed_gates:gates=0
    return World3(world.h,world.w,world.walls,near,objects,marks,switches,gates)


def _transform(point,kind,n=7):
    x,y=point
    if kind>=4:x=n-1-x;kind-=4
    for _ in range(kind):x,y=n-1-y,x
    return x,y


def _world(agent,objects,marks,switches=(),gates=(),walls=(),transform=0):
    index=lambda p:_transform(p,transform)[1]*7+_transform(p,transform)[0]
    border={(x,y) for y in range(7) for x in range(7) if x in (0,6) or y in (0,6)}
    bits=lambda points:sum(1<<index(p) for p in points)
    return World3(7,7,bits(border|set(walls)),index(agent),bits(objects),bits(marks),bits(switches),bits(gates))


def place_world(rng):
    """D4-varied alcove: the marked cell is reachable only by moving the object into it."""
    y=rng.choice((2,3,4));agent=(rng.choice((1,2,3)),y);box=(4,y);mark=(5,y)
    walls={(5,y-1),(5,y+1)}
    candidates=[(x,z) for x in range(1,5) for z in range(1,6) if (x,z) not in {agent,box} and z!=y]
    walls|=set(rng.sample(candidates,rng.randrange(0,4)))
    return _world(agent,(box,),(mark,),walls=walls,transform=rng.randrange(8))


def four_factor_world(rng):
    """Gate, alcove placement and a separate collect event in one unseen world."""
    y=3;agent,switch=rng.sample([(x,z) for x in (1,2) for z in range(1,6)],2);gate=(3,y);box=(4,y);alcove=(5,y)
    loose=rng.choice(((4,1),(4,5)));walls={(3,z) for z in range(1,6) if z!=y}|{(5,y-1),(5,y+1)}
    reserved={agent,switch,gate,box,alcove,loose};candidates=[(x,z) for x in (1,2,4) for z in range(1,6) if (x,z) not in reserved and (x,z)!=(4,y)]
    walls|=set(rng.sample(candidates,rng.randrange(0,3)))
    return _world(agent,(box,),(alcove,loose),(switch,),(gate,),walls,rng.randrange(8))


def shortest(world,fixed_objects=False,fixed_gates=False,limit=100000):
    queue=deque([(world,0)]);seen={key(world)}
    while queue:
        state,distance=queue.popleft()
        if state.marks==0:return distance
        for action in range(4):
            nxt=step(state,action,fixed_objects,fixed_gates);identity=key(nxt)
            if identity not in seen:
                seen.add(identity)
                if len(seen)>limit:return None
                queue.append((nxt,distance+1))


def collect_place_traces(seed,total,steps=96):
    """Random experience only; keep successes ending in the new anonymous signature."""
    rng=random.Random(seed);traces=[];initials=set();attempts=0
    while len(traces)<total and attempts<total*200:
        attempts+=1;world=place_world(rng);initials.add(key(world));trace=[]
        for _ in range(steps):
            before=raw(world);action=rng.randrange(4);world=step(world,action);after=raw(world);trace.append((before,action,after))
            if world.marks==0:
                if changed_planes(before,after)==(1,2,3):traces.append(trace)
                break
    if len(traces)<total:raise RuntimeError(f'only {len(traces)} place successes in {attempts} attempts')
    return traces,initials,attempts


def generate_suite(seed,total,exclude=()):
    rng=random.Random(seed);exclude=set(exclude);seen=set();out=[];attempts=0
    while len(out)<total and attempts<total*10000:
        attempts+=1;world=four_factor_world(rng);identity=key(world);distance=shortest(world)
        if identity in exclude or identity in seen or distance is None or not 6<=distance<=40:continue
        if shortest(world,True) is not None or shortest(world,False,True) is not None:continue
        seen.add(identity);out.append(('four',world,distance))
    if len(out)<total:raise RuntimeError(f'only {len(out)} joint worlds in {attempts} attempts')
    return out,attempts


def evaluate(policies,suite,seed,episodes=32,steps=160):
    rows={name:Counter() for name in policies}
    for index,(_,initial,_) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial
                for _ in range(steps):
                    world=step(world,choose(policy.probabilities(raw(world)),rng));success=world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'map_{index}_successes']+=success
    return {name:dict(row) for name,row in rows.items()}
