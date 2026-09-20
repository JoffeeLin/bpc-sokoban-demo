#!/usr/bin/env python3
"""BPC v0.9 development: direct policy composition from disjoint tasks."""
from __future__ import annotations

import random
from collections import Counter,deque

from bpc_cross_task_v07 import World,bit,moved,random_world,truth
from experiment_v5 import erase_zero_effect_cycles
from general_bpc_v7 import RelationalBPC,RelationalEncoder

SIZE=7;ACTIONS=4


def raw(world:World):
    values=[]
    for y in range(SIZE):
        for x in range(SIZE):
            inside=x<world.w and y<world.h;i=y*world.w+x if inside else -1
            values.extend((int(not inside or bit(world.walls,i)),int(inside and i==world.agent),
                           int(inside and bit(world.objects,i)),int(inside and bit(world.marks,i))))
    return bytes(values)


def model():return RelationalBPC(RelationalEncoder(SIZE,SIZE,4,radius=2,rarity=3))


class ProductPolicy:
    """Keep specialist Choice channels independent, then normalize their product."""
    def __init__(self,*models):self.models=models
    def probabilities(self,state):
        rows=[source.probabilities(state) for source in self.models]
        values=[1.]*ACTIONS
        for row in rows:
            for action in range(ACTIONS):values[action]*=row[action]
        total=sum(values);return [value/total for value in values]
    def rotated(self):return ProductPolicy(*(source.rotated() for source in self.models))


def choose(probability,rng):
    point=rng.random();total=0.
    for action,value in enumerate(probability):
        total+=value
        if point<=total:return action
    return ACTIONS-1


def train(seed,uniform_episodes=1000,guided_rounds=2,guided_episodes=500,steps=100):
    rng=random.Random(seed);shared=model();specialists={'push':model(),'collect':model()};events=Counter()
    schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect'):
        specialist=specialists[family]
        for guided in schedule:
            world=random_world(rng,family);trace=[];pushed=False
            for _ in range(steps):
                before=raw(world)
                action=choose(specialist.probabilities(before),rng) if guided and rng.random()>.25 else rng.randrange(ACTIONS)
                next_world=truth(world,action);after=raw(next_world);changed=next_world!=world
                shared.observe_transition(before,action,changed);specialist.observe_transition(before,action,changed)
                trace.append((before,action,after));pushed|=next_world.objects!=world.objects;world=next_world
                success=pushed if family=='push' else world.marks==0
                if success:
                    compact=erase_zero_effect_cycles(trace);shared.observe_success(compact);specialist.observe_success(compact)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=len(compact);break
            events[f'{family}_episodes']+=1
    return shared,specialists,dict(events)


def fixed_step(world:World,action:int):
    near=moved(world,world.agent,action)
    if near<0 or bit(world.walls|world.objects,near):return world
    return World(world.h,world.w,world.walls,near,world.objects,world.marks&~(1<<near))


def shortest(world:World,fixed=False,limit=100000):
    queue=deque([(world,0)]);seen={(world.agent,world.objects,world.marks)}
    while queue:
        state,distance=queue.popleft()
        if state.marks==0:return distance
        for action in range(ACTIONS):
            nxt=fixed_step(state,action) if fixed else truth(state,action);key=(nxt.agent,nxt.objects,nxt.marks)
            if key not in seen:
                seen.add(key)
                if len(seen)>limit:return None
                queue.append((nxt,distance+1))
    return None


def candidate(rng):
    h=w=7;inside=[y*w+x for y in range(1,6) for x in range(1,6)];border={y*w+x for y in range(h) for x in range(w) if x in (0,6) or y in (0,6)}
    inner=set(rng.sample(inside,rng.randint(4,8)));free=[i for i in inside if i not in inner]
    n_objects=rng.choice((1,1,2));n_marks=rng.choice((1,1,2));chosen=rng.sample(free,1+n_objects+n_marks)
    return World(h,w,sum(1<<i for i in border|inner),chosen[0],sum(1<<i for i in chosen[1:1+n_objects]),sum(1<<i for i in chosen[1+n_objects:]))


def generate_holdout(seed,count):
    rng=random.Random(seed);out=[];attempts=0
    while len(out)<count and attempts<200000:
        attempts+=1;world=candidate(rng);distance=shortest(world);fixed=shortest(world,True)
        if distance is not None and fixed is None and 4<=distance<=40:out.append((world,distance))
    if len(out)<count:raise RuntimeError(f'only {len(out)} push-required worlds after {attempts} attempts')
    return out,attempts


def evaluate(models,holdout,seed,episodes,steps):
    result={name:Counter() for name in models};traces={name:{} for name in models}
    for world_index,(initial,distance) in enumerate(holdout):
        for episode in range(episodes):
            for name,source in models.items():
                rng=random.Random(seed+world_index*100000+episode);controlled=source.rotated() if name=='rotated' else source
                world=initial;path=[]
                for _ in range(steps):
                    state=raw(world);probability=[.25]*4 if name=='uniform' else controlled.probabilities(state)
                    action=choose(probability,rng);path.append(action);world=truth(world,action)
                    if world.marks==0:break
                success=world.marks==0;result[name]['episodes']+=1;result[name]['successes']+=success
                result[name][f'world_{world_index+1}_successes']+=success
                if success and world_index not in traces[name]:traces[name][world_index]=path
    return {name:dict(row) for name,row in result.items()},traces
