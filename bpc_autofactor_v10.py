#!/usr/bin/env python3
"""BPC v0.10 development: discover and route anonymous event factors."""
from __future__ import annotations

import hashlib,math,pickle,random
from collections import Counter,deque

from bpc_cross_task_v07 import World,random_world,truth
from bpc_direct_composition_v09 import ACTIONS,choose,generate_holdout,raw
from experiment_v5 import erase_zero_effect_cycles
from general_bpc_v7 import RelationalBPC,RelationalEncoder


def new_cube():return RelationalBPC(RelationalEncoder(7,7,4,radius=2,rarity=3))


def changed_planes(before:bytes,after:bytes,channels=4):
    """Return raw bit planes changed by the terminal reality transition."""
    return tuple(c for c in range(channels) if any(before[i+c]!=after[i+c] for i in range(0,len(before),channels)))


class AnonymousFactorBPC:
    """Split successful traces by terminal co-change, then route by raw presence.

    The learner receives no task-family name.  A factor identity is only the
    tuple of raw bit planes that changed on the successful terminal step.
    Planes common to all factors are removed from each factor's activation
    condition; the remaining raw planes decide which factors are present.
    """
    def __init__(self):
        self.factors={};self.shared=new_cube();self.successes=Counter();self.writes=0;self.training_initials=set()

    def observe_success(self,trace,compact=None):
        signature=changed_planes(trace[-1][0],trace[-1][2])
        factor=self.factors.setdefault(signature,new_cube())
        compact=compact if compact is not None else erase_zero_effect_cycles(trace)
        factor.observe_success(compact);self.shared.observe_success(compact)
        self.successes[signature]+=1;self.writes+=len(compact)
        return signature

    def common_planes(self):
        signatures=list(self.factors)
        return set.intersection(*(set(x) for x in signatures)) if signatures else set()

    def required_planes(self):
        common=self.common_planes()
        return {signature:tuple(c for c in signature if c not in common) for signature in self.factors}

    @staticmethod
    def present_planes(state,channels=4):
        return {c for c in range(channels) if any(state[i+c] for i in range(0,len(state),channels))}

    def active(self,state,permuted=False):
        present=self.present_planes(state);required=self.required_planes()
        exclusive=sorted({c for row in required.values() for c in row})
        swap=dict(zip(exclusive,reversed(exclusive))) if permuted else {}
        return tuple(signature for signature,row in sorted(required.items())
                     if all(swap.get(c,c) in present for c in row))

    @staticmethod
    def pool(rows):
        if not rows:return [.25]*ACTIONS
        values=[1.]*ACTIONS
        for row in rows:
            for action in range(ACTIONS):values[action]*=row[action]
        total=sum(values);return [value/total for value in values]

    def probabilities(self,state,mode='auto',oracle=()):
        if mode=='shared':return self.shared.probabilities(state)
        if mode=='all':signatures=tuple(sorted(self.factors))
        elif mode=='permuted':signatures=self.active(state,True)
        elif mode=='oracle':signatures=tuple(oracle)
        else:signatures=self.active(state)
        return self.pool([self.factors[x].probabilities(state) for x in signatures])

    def digest(self):
        rows=tuple((signature,cube.digest()) for signature,cube in sorted(self.factors.items()))
        return hashlib.sha256(pickle.dumps((rows,self.successes),protocol=5)).hexdigest()


def train(seed,uniform_episodes=1000,guided_rounds=2,guided_episodes=500,steps=100):
    rng=random.Random(seed);learner=AnonymousFactorBPC();events=Counter();schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect'):
        for guided in schedule:
            world=random_world(rng,family);trace=[];pushed=False
            learner.training_initials.add((world.h,world.w,world.walls,world.agent,world.objects,world.marks))
            for _ in range(steps):
                before=raw(world)
                probability=learner.probabilities(before)
                action=choose(probability,rng) if guided and rng.random()>.25 else rng.randrange(ACTIONS)
                nxt=truth(world,action);after=raw(nxt);trace.append((before,action,after))
                pushed|=nxt.objects!=world.objects;world=nxt
                success=pushed if family=='push' else world.marks==0
                if success:
                    compact=erase_zero_effect_cycles(trace);signature=learner.observe_success(trace,compact)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=len(compact)
                    events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,dict(events)


def shortest_push(world,limit=100000):
    initial=world.objects;queue=deque([(world,0)]);seen={(world.agent,world.objects)}
    while queue:
        state,distance=queue.popleft()
        if state.objects!=initial:return distance
        for action in range(ACTIONS):
            nxt=truth(state,action);key=(nxt.agent,nxt.objects)
            if key not in seen:
                seen.add(key)
                if len(seen)>limit:return None
                queue.append((nxt,distance+1))
    return None


def shortest_collect(world,limit=100000):
    queue=deque([(world,0)]);seen={(world.agent,world.marks)}
    while queue:
        state,distance=queue.popleft()
        if state.marks==0:return distance
        for action in range(ACTIONS):
            nxt=truth(state,action);key=(nxt.agent,nxt.marks)
            if key not in seen:
                seen.add(key)
                if len(seen)>limit:return None
                queue.append((nxt,distance+1))
    return None


def generate_suite(seed,count,exclude=()):
    rng=random.Random(seed);combined,attempts=generate_holdout(rng.randrange(1<<30),count);out=[]
    exclude=set(exclude)
    for family,distance_fn in (('push',shortest_push),('collect',shortest_collect)):
        seen=set();tries=0
        while len(seen)<count and tries<100000:
            tries+=1;world=random_world(rng,family);distance=distance_fn(world)
            key=(world.h,world.w,world.walls,world.agent,world.objects,world.marks)
            if distance is not None and 2<=distance<=20 and key not in seen and key not in exclude:
                seen.add(key);out.append((family,world,distance))
        if len([x for x in out if x[0]==family])<count:raise RuntimeError(f'not enough {family} worlds')
    out.extend(('combined',world,distance) for world,distance in combined)
    return out,attempts


def signature_roles(learner):
    required=learner.required_planes()
    singles={row[0]:signature for signature,row in required.items() if len(row)==1}
    return singles


def evaluate(learner,suite,seed,episodes,steps):
    roles=signature_roles(learner);rows={name:Counter() for name in ('auto','oracle','all','shared','permuted','uniform')}
    traces={name:{} for name in rows};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        oracle=(roles[2],) if family=='push' else (roles[3],) if family=='collect' else (roles[2],roles[3])
        for episode in range(episodes):
            for name in rows:
                rng=random.Random(seed+index*100000+episode);world=initial;path=[]
                for _ in range(steps):
                    before=raw(world);key=(name,before,oracle)
                    if name=='auto':
                        rows[name]['routing_decisions']+=1
                        rows[name]['routing_mismatches']+=learner.active(before)!=tuple(sorted(oracle))
                    if key not in cache:cache[key]=[.25]*4 if name=='uniform' else learner.probabilities(before,name,oracle)
                    probability=cache[key]
                    action=choose(probability,rng);path.append(action);nxt=truth(world,action)
                    success=nxt.objects!=initial.objects if family=='push' else nxt.marks==0
                    world=nxt
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success
                row[f'{family}_episodes']+=1;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
