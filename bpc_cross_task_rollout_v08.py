#!/usr/bin/env python3
"""BPC v0.8 development: open-loop rollout from the v0.7 local world function."""
from __future__ import annotations

import random
from collections import Counter

from bpc_cross_task_v07 import World,evaluate,moved,patch,random_world,train,truth


def setbit(mask,index,value):return mask|1<<index if value else mask&~(1<<index)


def learned_step(world:World,action:int,model):
    predicted=model.predict(patch(world,action))
    if predicted is None:return None
    cells=[moved(world,world.agent,action,k) for k in range(3)];agents=0;objects=world.objects;marks=world.marks
    for index,value in zip(cells,predicted):
        if index<0:continue
        if bool(value&1)!=bool((world.walls>>index)&1):return None
        agents=setbit(agents,index,(value>>1)&1);objects=setbit(objects,index,(value>>2)&1);marks=setbit(marks,index,(value>>3)&1)
    if agents.bit_count()!=1:return None
    return World(world.h,world.w,world.walls,agents.bit_length()-1,objects,marks)


def rollout(model,world,actions):
    predicted=world;exact_steps=0;composition=False
    for action in actions:
        before=patch(world,action);composition|=any(value&4 for value in before) and any(value&8 for value in before)
        world=truth(world,action);predicted=learned_step(predicted,action,model) if predicted is not None else None
        exact=predicted==world;exact_steps+=exact
    return {'known':predicted is not None,'exact_steps':exact_steps,'exact_all':exact_steps==len(actions),
            'exact_final':predicted==world,'composition':composition}


def evaluate_rollouts(models,seed,episodes,horizons,family='combined'):
    rng=random.Random(seed);result={name:{str(h):Counter() for h in horizons} for name in models}
    for horizon in horizons:
        for _ in range(episodes):
            world=random_world(rng,family);actions=[rng.randrange(4) for _ in range(horizon)]
            for name,model in models.items():
                outcome=rollout(model,world,actions);row=result[name][str(horizon)];row['episodes']+=1
                row['known']+=outcome['known'];row['exact_all']+=outcome['exact_all'];row['exact_final']+=outcome['exact_final']
                row['exact_steps']+=outcome['exact_steps'];row['steps']+=horizon
                if outcome['composition']:
                    row['composition_episodes']+=1;row['composition_known']+=outcome['known']
                    row['composition_exact_all']+=outcome['exact_all'];row['composition_exact_final']+=outcome['exact_final']
    return {name:{h:dict(row) for h,row in rows.items()} for name,rows in result.items()}


def trained(seed=70_707,episodes=2500,steps=60):
    compressed,residual,fragments,full,events=train(seed,episodes,steps)
    return {'condition_deleted':compressed,'fragment_chain':fragments,'full_context':full},events
