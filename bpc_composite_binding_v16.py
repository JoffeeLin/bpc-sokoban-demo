#!/usr/bin/env python3
"""BPC v0.16 development: support-invariant binding with composite distractors."""
from __future__ import annotations

import itertools,math,random
from collections import Counter

from bpc_direct_composition_v09 import choose
from bpc_open_interface_v15 import (CELLS,CANONICAL_ACTIONS,OpenBoundPolicy,OpenInterfaceStats,
    sensor_log_probability)
from bpc_three_factor_v12 import CHANNELS,key,random_world,raw,step,succeeded


def composite_expose(canonical,routes):
    """Expose canonical planes plus supplied displaced-XOR composite distractors."""
    routes=tuple(routes);assert sorted(x for x in routes if x is not None)==list(range(CHANNELS))
    out=bytearray(CELLS*len(routes));modes={slot:mode for mode,slot in enumerate(i for i,x in enumerate(routes) if x is None)}
    for cell in range(CELLS):
        for observed,channel in enumerate(routes):
            if channel is None:
                mode=modes[observed];a=(mode*2+1)%CHANNELS;b=(mode*3+2)%CHANNELS;other=(cell+mode+1)%CELLS
                out[cell*len(routes)+observed]=canonical[cell*CHANNELS+a]^canonical[other*CHANNELS+b]
            else:out[cell*len(routes)+observed]=canonical[cell*CHANNELS+channel]
    return bytes(out)


def changed(before,after,channels):return frozenset(c for c in range(channels) if before[c::channels]!=after[c::channels])


def collect_composite_interface(seed,worlds_per_family=100,steps=32,
        sensor_routes=tuple(range(CHANNELS)),actuator_routes=tuple(range(CANONICAL_ACTIONS)),exclude=()):
    rng=random.Random(seed);interface=OpenInterfaceStats(len(sensor_routes));triples=[];initials=set();support=set();exclude=set(exclude)
    counts={family:worlds_per_family for family in ('push','collect','open')} if isinstance(worlds_per_family,int) else worlds_per_family
    for family,total in counts.items():
        count=0
        while count<total:
            world=random_world(rng,family);identity=key(world)
            if identity in exclude or identity in initials:continue
            initials.add(identity);count+=1
            for _ in range(steps):
                before=composite_expose(raw(world),sensor_routes);action=rng.randrange(len(actuator_routes));route=actuator_routes[action]
                if route is not None:world=step(world,route)
                after=composite_expose(raw(world),sensor_routes);interface.observe(before,after);triples.append((before,action,after));support.add(changed(before,after,len(sensor_routes)))
    return interface,triples,initials,support


def projected_support(support,mapping):
    return {frozenset(canonical for canonical,observed in enumerate(mapping) if observed in signature) for signature in support}


def infer_support_binding(reference,reference_support,target_rows):
    """Exact probability assignment after empirical transition-support invariance."""
    rows=[]
    for mapping in itertools.permutations(range(target_rows[0][0].channels),reference.channels):
        if all(projected_support(support,mapping)<=reference_support for _,support in target_rows):
            per=tuple(sensor_log_probability(reference,target,mapping) for target,_ in target_rows);rows.append((sum(per),mapping,per))
    if len(rows)<2:return {'mapping':None,'compatible':len(rows)}
    rows.sort();top=rows[-1][0];z=sum(math.exp(value-top) for value,_,_ in rows);per_stream=[]
    for stream in range(len(target_rows)):
        ranked=sorted((row[2][stream],row[1]) for row in rows)
        per_stream.append({'mapping':ranked[-1][1],'log_margin':ranked[-1][0]-ranked[-2][0]})
    return {'mapping':rows[-1][1],'posterior':1/z,'log_margin':rows[-1][0]-rows[-2][0],
        'second':rows[-2][1],'compatible':len(rows),'per_stream':tuple(per_stream)}


def evaluate_composite(policies,suite,sensor_routes,actuator_routes,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;path=[]
                for _ in range(steps):
                    observed=composite_expose(raw(world),sensor_routes);identity=(name,observed)
                    if identity not in cache:cache[identity]=policy.probabilities(observed)
                    action=choose(cache[identity],rng);path.append(action);route=actuator_routes[action]
                    if route is not None:world=step(world,route)
                    success=succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces


CompositeBoundPolicy=OpenBoundPolicy
