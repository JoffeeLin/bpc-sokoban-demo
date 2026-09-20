#!/usr/bin/env python3
"""BPC v0.15 development: bind a canonical interface inside larger anonymous I/O."""
from __future__ import annotations

import hashlib,itertools,math,pickle,random
from collections import Counter

from bpc_channel_binding_v13 import log_categorical
from bpc_direct_composition_v09 import choose
from bpc_three_factor_v12 import CHANNELS,FieldPolicy,key,random_world,raw,step,succeeded

CELLS=49;WIDTH=7;CANONICAL_ACTIONS=4


class OpenInterfaceStats:
    """Variable-width anonymous occupancy and transition probability counts."""
    def __init__(self,channels,cells=CELLS):
        self.channels=channels;self.cells=cells;self.frames=0;self.transitions=0
        self.occupancy=[Counter() for _ in range(channels)]
        self.delta=[Counter() for _ in range(channels)]
        self.flips=[Counter() for _ in range(channels)]
        self.active_delta=[Counter() for _ in range(channels)]
        self.active_flips=[Counter() for _ in range(channels)]
        self.motion=[Counter() for _ in range(channels)]
        self.cochange={(a,b):Counter() for a in range(channels) for b in range(a+1,channels)}
        self.joint_delta={(a,b):Counter() for a in range(channels) for b in range(a+1,channels)}

    def observe(self,before,after):
        assert len(before)==len(after)==self.cells*self.channels;changes=[];deltas=[]
        for channel in range(self.channels):
            old=before[channel::self.channels];new=after[channel::self.channels]
            lost=[i for i,(a,b) in enumerate(zip(old,new)) if a and not b];gained=[i for i,(a,b) in enumerate(zip(old,new)) if b and not a]
            n=sum(old);m=sum(new);flip=len(lost)+len(gained);changes.append(bool(flip));deltas.append(m-n)
            self.occupancy[channel][n]+=1;self.delta[channel][m-n]+=1;self.flips[channel][flip]+=1
            if flip:self.active_delta[channel][m-n]+=1;self.active_flips[channel][flip]+=1
            for source in lost:
                for target in gained:
                    dx=target%WIDTH-source%WIDTH;dy=target//WIDTH-source//WIDTH
                    if abs(dx)<=1 and abs(dy)<=1:self.motion[channel][(dx,dy)]+=1
        for pair,row in self.cochange.items():
            a,b=pair;row[(int(changes[a]),int(changes[b]))]+=1
            self.joint_delta[pair][(deltas[a],deltas[b])]+=1
        self.frames+=1;self.transitions+=1

    def digest(self):
        rows=(self.channels,self.cells,self.frames,self.transitions,
            tuple(tuple(sorted(row.items())) for row in self.occupancy),
            tuple(tuple(sorted(row.items())) for row in self.delta),
            tuple(tuple(sorted(row.items())) for row in self.flips),
            tuple(tuple(sorted(row.items())) for row in self.active_delta),
            tuple(tuple(sorted(row.items())) for row in self.active_flips),
            tuple(tuple(sorted(row.items())) for row in self.motion),
            tuple((pair,tuple(sorted(row.items()))) for pair,row in sorted(self.cochange.items())),
            tuple((pair,tuple(sorted(row.items()))) for pair,row in sorted(self.joint_delta.items())))
        return hashlib.sha256(pickle.dumps(rows,protocol=5)).hexdigest()


def sensor_log_probability(reference,target,mapping):
    value=0.
    for canonical,observed in enumerate(mapping):
        value+=log_categorical(target.occupancy[observed],reference.occupancy[canonical])
        value+=log_categorical(target.active_delta[observed],reference.active_delta[canonical])
        value+=log_categorical(target.active_flips[observed],reference.active_flips[canonical])
        value+=log_categorical(target.motion[observed],reference.motion[canonical])
    for a in range(reference.channels):
        for b in range(a+1,reference.channels):
            oa,ob=mapping[a],mapping[b];observed=tuple(sorted((oa,ob)));joint=target.cochange[observed];base=reference.cochange[(a,b)]
            a_only,b_only=(joint[(1,0)],joint[(0,1)]) if oa<ob else (joint[(0,1)],joint[(1,0)])
            value+=log_categorical(Counter({0:a_only,1:joint[(1,1)]}),Counter({0:base[(1,0)],1:base[(1,1)]}))
            value+=log_categorical(Counter({0:b_only,1:joint[(1,1)]}),Counter({0:base[(0,1)],1:base[(1,1)]}))
            delta=target.joint_delta[observed]
            if oa>ob:delta=Counter({(y,x):n for (x,y),n in delta.items()})
            value+=log_categorical(delta,reference.joint_delta[(a,b)])
    return value


def infer_sensor_subset(reference,target):
    rows=sorted((sensor_log_probability(reference,target,mapping),mapping)
        for mapping in itertools.permutations(range(target.channels),reference.channels))
    top=rows[-1][0];z=sum(math.exp(value-top) for value,_ in rows)
    return {'mapping':rows[-1][1],'posterior':1/z,'log_margin':rows[-1][0]-rows[-2][0],'second':rows[-2][1]}


def nuisance_plane(canonical,mode):
    """Deterministic state-keyed random plane independent of task mechanisms."""
    digest=hashlib.sha512(bytes((mode,))+canonical).digest();threshold=(32,20)[mode%2]
    return tuple(value<threshold for value in digest[:CELLS])


def expose(canonical,routes):
    """Expose canonical planes in observed slots; None slots carry nuisance bits."""
    routes=tuple(routes);assert sorted(x for x in routes if x is not None)==list(range(CHANNELS))
    out=bytearray(CELLS*len(routes));modes={slot:nuisance_plane(canonical,mode) for mode,slot in enumerate(i for i,x in enumerate(routes) if x is None)}
    for cell in range(CELLS):
        for observed,canonical_channel in enumerate(routes):
            out[cell*len(routes)+observed]=canonical[cell*CHANNELS+canonical_channel] if canonical_channel is not None else modes[observed][cell]
    return bytes(out)


def canonicalize_subset(observed,mapping,observed_channels):
    out=bytearray(CELLS*CHANNELS)
    for cell in range(CELLS):
        for canonical,slot in enumerate(mapping):out[cell*CHANNELS+canonical]=observed[cell*observed_channels+slot]
    return bytes(out)


def inverse_subset(routes,total):return tuple(tuple(routes).index(index) for index in range(total))


class OpenActionStats:
    """Variable-width action-conditional raw transition probability counts."""
    def __init__(self,actions,channels=CHANNELS):
        self.actions=actions;self.channels=channels;self.transitions=[0]*actions
        self.delta=[[Counter() for _ in range(channels)] for _ in range(actions)]
        self.flips=[[Counter() for _ in range(channels)] for _ in range(actions)]
        self.motion=[[Counter() for _ in range(channels)] for _ in range(actions)]
        self.total=[Counter() for _ in range(actions)]

    def observe(self,before,action,after):
        changed=0
        for channel in range(self.channels):
            old=before[channel::self.channels];new=after[channel::self.channels]
            lost=[i for i,(a,b) in enumerate(zip(old,new)) if a and not b];gained=[i for i,(a,b) in enumerate(zip(old,new)) if b and not a]
            flip=len(lost)+len(gained);changed+=flip;self.delta[action][channel][sum(new)-sum(old)]+=1;self.flips[action][channel][flip]+=1
            for source in lost:
                for target in gained:
                    dx=target%WIDTH-source%WIDTH;dy=target//WIDTH-source//WIDTH
                    if abs(dx)<=1 and abs(dy)<=1:self.motion[action][channel][(dx,dy)]+=1
        self.total[action][changed]+=1;self.transitions[action]+=1

    def digest(self):
        rows=(self.actions,self.channels,tuple(self.transitions),
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


def active_action_slots(target,total):
    return tuple(sorted(sorted(range(target.actions),key=lambda action:(
        sum(n for changed,n in target.total[action].items() if changed),target.transitions[action],action),reverse=True)[:total]))


def infer_action_subset(reference,target):
    candidates=active_action_slots(target,reference.actions)
    rows=sorted((action_log_probability(reference,target,mapping),mapping)
        for mapping in itertools.permutations(candidates,reference.actions))
    top=rows[-1][0];z=sum(math.exp(value-top) for value,_ in rows)
    return {'mapping':rows[-1][1],'posterior':1/z,'log_margin':rows[-1][0]-rows[-2][0],
        'second':rows[-2][1],'candidate_slots':tuple(sorted(candidates))}


def action_stats(triples,sensor_mapping,observed_channels,actions):
    stats=OpenActionStats(actions)
    for before,action,after in triples:
        stats.observe(canonicalize_subset(before,sensor_mapping,observed_channels),action,
            canonicalize_subset(after,sensor_mapping,observed_channels))
    return stats


def collect_open_interface(seed,worlds_per_family=100,steps=32,
        sensor_routes=tuple(range(CHANNELS)),actuator_routes=tuple(range(CANONICAL_ACTIONS)),exclude=()):
    rng=random.Random(seed);interface=OpenInterfaceStats(len(sensor_routes));triples=[];initials=set();exclude=set(exclude)
    counts={family:worlds_per_family for family in ('push','collect','open')} if isinstance(worlds_per_family,int) else worlds_per_family
    for family,total in counts.items():
        count=0
        while count<total:
            world=random_world(rng,family);identity=key(world)
            if identity in exclude or identity in initials:continue
            initials.add(identity);count+=1
            for _ in range(steps):
                before=expose(raw(world),sensor_routes);action=rng.randrange(len(actuator_routes));route=actuator_routes[action]
                if route is not None:world=step(world,route)
                after=expose(raw(world),sensor_routes);interface.observe(before,after);triples.append((before,action,after))
    return interface,triples,initials


class OpenBoundPolicy:
    def __init__(self,learner,sensor_mapping,observed_channels,action_mapping,observed_actions):
        self.field=FieldPolicy(learner);self.sensor_mapping=tuple(sensor_mapping);self.observed_channels=observed_channels
        self.action_mapping=tuple(action_mapping);self.observed_actions=observed_actions

    def probabilities(self,observed):
        canonical=self.field.probabilities(canonicalize_subset(observed,self.sensor_mapping,self.observed_channels));out=[0.]*self.observed_actions
        for action,slot in enumerate(self.action_mapping):out[slot]=canonical[action]
        return out


def evaluate_open(policies,suite,sensor_routes,actuator_routes,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;path=[]
                for _ in range(steps):
                    observed=expose(raw(world),sensor_routes);identity=(name,observed)
                    if identity not in cache:cache[identity]=policy.probabilities(observed)
                    action=choose(cache[identity],rng);path.append(action);route=actuator_routes[action]
                    if route is not None:world=step(world,route)
                    success=succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
