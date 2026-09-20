#!/usr/bin/env python3
"""BPC v0.18 development: anonymous D4 spatial-frame and variable-I/O binding."""
from __future__ import annotations

import itertools,math,random
from collections import Counter

from bpc_cross_generator_v17 import (apply_slot,changed,collect_variable,done,
    lab_raw,variable_expose)
from bpc_cross_task_v07 import ACTIONS as DELTAS
from bpc_direct_composition_v09 import choose
from bpc_open_interface_v15 import (OpenActionStats,OpenInterfaceStats,
    action_log_probability,active_action_slots,canonicalize_subset)
from bpc_three_factor_v12 import CHANNELS,FieldPolicy

WIDTH=7;TRANSFORMS=8


def transform_xy(x,y,transform):
    """Map a canonical cell to one of eight anonymous square-frame gauges."""
    if transform>=4:x=WIDTH-1-x
    for _ in range(transform%4):x,y=WIDTH-1-y,x
    return x,y


def spatial_expose(state,channels,transform):
    out=bytearray(len(state))
    for y in range(WIDTH):
        for x in range(WIDTH):
            tx,ty=transform_xy(x,y,transform);source=(y*WIDTH+x)*channels;target=(ty*WIDTH+tx)*channels
            out[target:target+channels]=state[source:source+channels]
    return bytes(out)


def spatial_restore(state,channels,transform):
    out=bytearray(len(state))
    for y in range(WIDTH):
        for x in range(WIDTH):
            tx,ty=transform_xy(x,y,transform);target=(y*WIDTH+x)*channels;source=(ty*WIDTH+tx)*channels
            out[target:target+channels]=state[source:source+channels]
    return bytes(out)


def collect_spatial(seed,counts,steps,sensors,actions,kinds,transform,exclude=()):
    _,triples,initials,_=collect_variable(seed,counts,steps,sensors,actions,kinds,exclude);stats=OpenInterfaceStats(len(sensors));rows=[];support=set()
    for before,action,after in triples:
        before=spatial_expose(before,len(sensors),transform);after=spatial_expose(after,len(sensors),transform)
        stats.observe(before,after);rows.append((before,action,after));support.add(changed(before,after,len(sensors)))
    return stats,rows,initials,support


def spatial_action_stats(triples,sensor_mapping,observed_channels,actions,transform):
    stats=OpenActionStats(actions)
    for before,action,after in triples:
        before=spatial_restore(canonicalize_subset(before,sensor_mapping,observed_channels),CHANNELS,transform)
        after=spatial_restore(canonicalize_subset(after,sensor_mapping,observed_channels),CHANNELS,transform);stats.observe(before,action,after)
    return stats


def action_candidates(reference,target):
    slots=active_action_slots(target,reference.actions)
    return tuple((action_log_probability(reference,target,mapping),mapping) for mapping in itertools.permutations(slots,reference.actions))


def infer_spatial_action(reference,triples,sensor_mapping,observed_channels,actions,stream_triples=()):
    """Equal-prior product over eight spatial gauges and anonymous action injections."""
    rows=[]
    for transform in range(TRANSFORMS):
        target=spatial_action_stats(triples,sensor_mapping,observed_channels,actions,transform)
        rows.extend((value,transform,mapping,target) for value,mapping in action_candidates(reference,target))
    rows.sort(key=lambda x:(x[0],x[1],x[2]));top=rows[-1][0];z=sum(math.exp(x[0]-top) for x in rows);streams=[]
    for stream in stream_triples:
        ranked=[]
        for transform in range(TRANSFORMS):
            target=spatial_action_stats(stream,sensor_mapping,observed_channels,actions,transform)
            ranked.extend((value,transform,mapping) for value,mapping in action_candidates(reference,target))
        ranked.sort();streams.append({'transform':ranked[-1][1],'mapping':ranked[-1][2],'log_margin':ranked[-1][0]-ranked[-2][0]})
    return {'transform':rows[-1][1],'mapping':rows[-1][2],'posterior':1/z,'log_margin':rows[-1][0]-rows[-2][0],
        'second':{'transform':rows[-2][1],'mapping':rows[-2][2]},'candidate_slots':active_action_slots(rows[-1][3],reference.actions),'per_stream':tuple(streams)}


def infer_spatial_gauges(reference,triples,sensor_mapping,observed_channels,actions,stream_triples=()):
    """Infer the best anonymous actuator injection separately inside every D4 gauge."""
    gauges=[]
    for transform in range(TRANSFORMS):
        target=spatial_action_stats(triples,sensor_mapping,observed_channels,actions,transform);ranked=sorted(action_candidates(reference,target))
        top=ranked[-1][0];z=sum(math.exp(value-top) for value,_ in ranked);streams=[]
        for stream in stream_triples:
            stream_target=spatial_action_stats(stream,sensor_mapping,observed_channels,actions,transform)
            stream_ranked=sorted(action_candidates(reference,stream_target));streams.append({'mapping':stream_ranked[-1][1],
                'log_margin':stream_ranked[-1][0]-stream_ranked[-2][0]})
        gauges.append({'transform':transform,'mapping':ranked[-1][1],'log_probability':top,'posterior':1/z,
            'log_margin':top-ranked[-2][0],'candidate_slots':active_action_slots(target,reference.actions),'per_stream':tuple(streams)})
    return tuple(gauges)


def transformed_delta(transform,action):
    """Evaluator geometry: direction vector after exposing a D4 frame."""
    x,y=transform_xy(3,3,transform);tx,ty=transform_xy(3+DELTAS[action][0],3+DELTAS[action][1],transform)
    return tx-x,ty-y


def gauge_equivalent_mapping(actual_transform,candidate_transform,actual_mapping):
    """Evaluator-only expected action injection for an equivalent candidate gauge."""
    mapping=[]
    for candidate_action in range(4):
        delta=transformed_delta(candidate_transform,candidate_action)
        physical=next(action for action in range(4) if transformed_delta(actual_transform,action)==delta)
        mapping.append(actual_mapping[physical])
    return tuple(mapping)


class SpatialBoundPolicy:
    def __init__(self,learner,sensor_mapping,observed_channels,transform,action_mapping,observed_actions):
        self.field=FieldPolicy(learner);self.sensor_mapping=tuple(sensor_mapping);self.observed_channels=observed_channels;self.transform=transform
        self.action_mapping=tuple(action_mapping);self.observed_actions=observed_actions

    def probabilities(self,observed):
        state=canonicalize_subset(observed,self.sensor_mapping,self.observed_channels);state=spatial_restore(state,CHANNELS,self.transform)
        canonical=self.field.probabilities(state);out=[0.]*self.observed_actions
        for action,slot in enumerate(self.action_mapping):out[slot]=canonical[action]
        return out


class GaugeAveragedPolicy:
    """Average direct BPC action probabilities over paired, observationally equivalent D4 gauges."""
    def __init__(self,learner,sensor_mapping,observed_channels,hypotheses,observed_actions):
        self.field=FieldPolicy(learner);self.sensor_mapping=tuple(sensor_mapping);self.observed_channels=observed_channels
        self.hypotheses=tuple((transform,tuple(mapping)) for transform,mapping in hypotheses);self.observed_actions=observed_actions

    def probabilities(self,observed):
        canonicalize=canonicalize_subset(observed,self.sensor_mapping,self.observed_channels);out=[0.]*self.observed_actions
        for transform,mapping in self.hypotheses:
            canonical=self.field.probabilities(spatial_restore(canonicalize,CHANNELS,transform))
            for action,slot in enumerate(mapping):out[slot]+=canonical[action]
        total=sum(out)
        return [value/total for value in out]


def evaluate_spatial(policies,suite,sensors,actions,kinds,transform,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;phase=0;path=[]
                for _ in range(steps):
                    observed=spatial_expose(variable_expose(lab_raw(world),sensors,kinds,phase),len(sensors),transform);cache_key=(name,observed)
                    if cache_key not in cache:cache[cache_key]=policy.probabilities(observed)
                    slot=choose(cache[cache_key],rng);path.append(slot);world,phase=apply_slot(world,phase,slot,actions);success=done(family,initial,world)
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
