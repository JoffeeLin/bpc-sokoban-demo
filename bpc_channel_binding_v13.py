#!/usr/bin/env python3
"""BPC v0.13 development: probabilistic binding of permuted raw channels."""
from __future__ import annotations

import hashlib,itertools,math,pickle,random
from collections import Counter

from bpc_direct_composition_v09 import choose
from bpc_three_factor_v12 import CHANNELS,FieldPolicy,evaluate,key,random_world,raw,step,succeeded


def permute_state(state,observed_to_canonical):
    """Expose canonical bits through an arbitrary anonymous sensor ordering."""
    out=bytearray(len(state))
    for i in range(0,len(state),CHANNELS):
        for observed,canonical in enumerate(observed_to_canonical):out[i+observed]=state[i+canonical]
    return bytes(out)


def canonicalize(state,canonical_to_observed):
    out=bytearray(len(state))
    for i in range(0,len(state),CHANNELS):
        for canonical,observed in enumerate(canonical_to_observed):out[i+canonical]=state[i+observed]
    return bytes(out)


def inverse(observed_to_canonical):return tuple(observed_to_canonical.index(c) for c in range(CHANNELS))


class InterfaceStats:
    """Anonymous Dirichlet/Beta counts over raw occupancy and change events."""
    def __init__(self,cells=49):
        self.cells=cells;self.frames=0;self.transitions=0
        self.occupancy=[Counter() for _ in range(CHANNELS)]
        self.delta=[Counter() for _ in range(CHANNELS)]
        self.flips=[Counter() for _ in range(CHANNELS)]
        self.ones=[[0]*cells for _ in range(CHANNELS)]
        self.cochange={(a,b):Counter() for a in range(CHANNELS) for b in range(a+1,CHANNELS)}

    def observe(self,before,after):
        counts=[];changes=[]
        for channel in range(CHANNELS):
            old=[before[i+channel] for i in range(0,len(before),CHANNELS)]
            new=[after[i+channel] for i in range(0,len(after),CHANNELS)]
            n=sum(old);m=sum(new);flip=sum(a!=b for a,b in zip(old,new));counts.append(n);changes.append(bool(flip))
            self.occupancy[channel][n]+=1;self.delta[channel][m-n]+=1;self.flips[channel][flip]+=1
            for i,value in enumerate(old):self.ones[channel][i]+=value
        for pair,row in self.cochange.items():row[(int(changes[pair[0]]),int(changes[pair[1]]))]+=1
        self.frames+=1;self.transitions+=1

    def digest(self):
        rows=(self.frames,self.transitions,
            tuple(tuple(sorted(row.items())) for row in self.occupancy),
            tuple(tuple(sorted(row.items())) for row in self.delta),
            tuple(tuple(sorted(row.items())) for row in self.flips),tuple(tuple(row) for row in self.ones),
            tuple((pair,tuple(sorted(row.items()))) for pair,row in sorted(self.cochange.items())))
        return hashlib.sha256(pickle.dumps(rows,protocol=5)).hexdigest()


def log_categorical(target,reference):
    bins=set(target)|set(reference);total=sum(reference.values())+len(bins)
    return sum(n*math.log((reference.get(value,0)+1)/total) for value,n in target.items())


def log_bernoulli(target_ones,target_n,reference_ones,reference_n):
    p=(reference_ones+1)/(reference_n+2)
    return target_ones*math.log(p)+(target_n-target_ones)*math.log1p(-p)


def binding_log_probability(reference,target,mapping,mode='full'):
    """Equal-prior posterior term for canonical->observed channel assignment."""
    spatial=mode in ('static','full');dynamic=mode in ('transition','full')
    value=0.
    for canonical,observed in enumerate(mapping):
        value+=log_categorical(target.occupancy[observed],reference.occupancy[canonical])
        if spatial:
            for cell in range(reference.cells):
                value+=log_bernoulli(target.ones[observed][cell],target.frames,reference.ones[canonical][cell],reference.frames)
        if dynamic:
            value+=log_categorical(target.delta[observed],reference.delta[canonical])
            value+=log_categorical(target.flips[observed],reference.flips[canonical])
    if dynamic:
        for a in range(CHANNELS):
            for b in range(a+1,CHANNELS):
                observed=tuple(sorted((mapping[a],mapping[b])))
                value+=log_categorical(target.cochange[observed],reference.cochange[(a,b)])
    return value


def infer_binding(reference,target,mode='full'):
    rows=[]
    for mapping in itertools.permutations(range(CHANNELS)):
        rows.append((binding_log_probability(reference,target,mapping,mode),mapping))
    rows.sort(reverse=True);top=rows[0][0];z=sum(math.exp(value-top) for value,_ in rows)
    return {'mapping':rows[0][1],'posterior':1/z,'log_margin':rows[0][0]-rows[1][0],
        'second':rows[1][1],'mode':mode}


def collect_interface(seed,worlds_per_family=100,steps=32,observed_to_canonical=tuple(range(CHANNELS)),exclude=()):
    """Collect unlabeled raw transitions; family names never enter statistics."""
    rng=random.Random(seed);stats=InterfaceStats();initials=set();exclude=set(exclude)
    counts={family:worlds_per_family for family in ('push','collect','open')} if isinstance(worlds_per_family,int) else worlds_per_family
    for family,total in counts.items():
        count=0
        while count<total:
            world=random_world(rng,family);identity=key(world)
            if identity in exclude or identity in initials:continue
            initials.add(identity);count+=1
            for _ in range(steps):
                before=permute_state(raw(world),observed_to_canonical);world=step(world,rng.randrange(4))
                after=permute_state(raw(world),observed_to_canonical);stats.observe(before,after)
    return stats,initials


class BoundFieldPolicy:
    def __init__(self,learner,mapping):self.field=FieldPolicy(learner);self.mapping=tuple(mapping)
    def probabilities(self,observed):return self.field.probabilities(canonicalize(observed,self.mapping))


def evaluate_permuted(policies,suite,observed_to_canonical,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;path=[]
                for _ in range(steps):
                    state=permute_state(raw(world),observed_to_canonical);identity=(name,state)
                    if identity not in cache:cache[identity]=policy.probabilities(state)
                    action=choose(cache[identity],rng);path.append(action);world=step(world,action)
                    success=succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
