#!/usr/bin/env python3
"""BPC v0.14 development: anonymous sensor and actuator binding."""
from __future__ import annotations

import hashlib,itertools,math,pickle,random
from collections import Counter

from bpc_channel_binding_v13 import InterfaceStats,canonicalize,infer_binding,inverse,log_categorical,permute_state
from bpc_direct_composition_v09 import choose
from bpc_three_factor_v12 import CHANNELS,FieldPolicy,key,random_world,raw,step,succeeded

ACTIONS=4;CELLS=49;WIDTH=7
def inverse_action(observed_to_canonical):return tuple(observed_to_canonical.index(c) for c in range(ACTIONS))


class ActionStats:
    """Anonymous action-conditional probability counts over raw bit motion."""
    def __init__(self):
        self.transitions=[0]*ACTIONS
        self.delta=[[Counter() for _ in range(CHANNELS)] for _ in range(ACTIONS)]
        self.flips=[[Counter() for _ in range(CHANNELS)] for _ in range(ACTIONS)]
        self.motion=[[Counter() for _ in range(CHANNELS)] for _ in range(ACTIONS)]
        self.total=[Counter() for _ in range(ACTIONS)]

    def observe(self,before,action,after):
        changed=0
        for channel in range(CHANNELS):
            old=[before[i+channel] for i in range(0,len(before),CHANNELS)]
            new=[after[i+channel] for i in range(0,len(after),CHANNELS)]
            lost=[i for i,(a,b) in enumerate(zip(old,new)) if a and not b]
            gained=[i for i,(a,b) in enumerate(zip(old,new)) if b and not a]
            flip=len(lost)+len(gained);changed+=flip
            self.delta[action][channel][sum(new)-sum(old)]+=1;self.flips[action][channel][flip]+=1
            for source in lost:
                for target in gained:
                    dx=target%WIDTH-source%WIDTH;dy=target//WIDTH-source//WIDTH
                    if abs(dx)<=1 and abs(dy)<=1:self.motion[action][channel][(dx,dy)]+=1
        self.total[action][changed]+=1;self.transitions[action]+=1

    def digest(self):
        rows=(tuple(self.transitions),
            tuple(tuple(tuple(sorted(x.items())) for x in row) for row in self.delta),
            tuple(tuple(tuple(sorted(x.items())) for x in row) for row in self.flips),
            tuple(tuple(tuple(sorted(x.items())) for x in row) for row in self.motion),
            tuple(tuple(sorted(x.items())) for x in self.total))
        return hashlib.sha256(pickle.dumps(rows,protocol=5)).hexdigest()


def action_log_probability(reference,target,mapping):
    value=0.
    for canonical,observed in enumerate(mapping):
        value+=log_categorical(target.total[observed],reference.total[canonical])
        for channel in range(CHANNELS):
            value+=log_categorical(target.delta[observed][channel],reference.delta[canonical][channel])
            value+=log_categorical(target.flips[observed][channel],reference.flips[canonical][channel])
            value+=log_categorical(target.motion[observed][channel],reference.motion[canonical][channel])
    return value


def infer_action_binding(reference,target):
    rows=sorted((action_log_probability(reference,target,mapping),mapping) for mapping in itertools.permutations(range(ACTIONS)))
    top=rows[-1][0];z=sum(math.exp(value-top) for value,_ in rows)
    return {'mapping':rows[-1][1],'posterior':1/z,'log_margin':rows[-1][0]-rows[-2][0],'second':rows[-2][1]}


def action_stats(triples,channel_mapping):
    stats=ActionStats()
    for before,action,after in triples:
        stats.observe(canonicalize(before,channel_mapping),action,canonicalize(after,channel_mapping))
    return stats


def collect_joint_interface(seed,worlds_per_family=100,steps=32,
        observed_to_canonical=tuple(range(CHANNELS)),observed_action_to_canonical=tuple(range(ACTIONS)),exclude=()):
    rng=random.Random(seed);interface=InterfaceStats();triples=[];initials=set();exclude=set(exclude)
    counts={family:worlds_per_family for family in ('push','collect','open')} if isinstance(worlds_per_family,int) else worlds_per_family
    for family,total in counts.items():
        count=0
        while count<total:
            world=random_world(rng,family);identity=key(world)
            if identity in exclude or identity in initials:continue
            initials.add(identity);count+=1
            for _ in range(steps):
                before=permute_state(raw(world),observed_to_canonical);action=rng.randrange(ACTIONS)
                world=step(world,observed_action_to_canonical[action]);after=permute_state(raw(world),observed_to_canonical)
                interface.observe(before,after);triples.append((before,action,after))
    return interface,triples,initials


class JointBoundPolicy:
    def __init__(self,learner,channel_mapping,action_mapping):
        self.field=FieldPolicy(learner);self.channel_mapping=tuple(channel_mapping);self.action_mapping=tuple(action_mapping)
    def probabilities(self,observed):
        canonical=self.field.probabilities(canonicalize(observed,self.channel_mapping));out=[0.]*ACTIONS
        for action,target in enumerate(self.action_mapping):out[target]=canonical[action]
        return out


def evaluate_joint(policies,suite,sensor_permutation,action_permutation,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;path=[]
                for _ in range(steps):
                    observed=permute_state(raw(world),sensor_permutation);identity=(name,observed)
                    if identity not in cache:cache[identity]=policy.probabilities(observed)
                    action=choose(cache[identity],rng);path.append(action);world=step(world,action_permutation[action])
                    success=succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
