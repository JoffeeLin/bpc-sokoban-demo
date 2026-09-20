#!/usr/bin/env python3
"""BPC v0.19 development: anonymous end-to-end temporal gauge binding."""
from __future__ import annotations

import math,random
from collections import Counter

from bpc_cross_generator_v17 import (apply_slot,changed,done,key,lab_raw,lab_world,variable_expose)
from bpc_direct_composition_v09 import choose
from bpc_open_interface_v15 import CHANNELS,OpenInterfaceStats
from bpc_spatial_interface_v18 import (GaugeAveragedPolicy,action_candidates,spatial_action_stats,spatial_expose)

MAX_LAG=4


def delayed_apply(world,phase,queue,issued,actions,actuator_delay):
    """Issue now; execute the slot that has waited actuator_delay steps."""
    queue.append(issued)
    if len(queue)<=actuator_delay:return world,phase
    return apply_slot(world,phase,queue.pop(0),actions)


def temporal_observation(history,sensor_delay,sensors,kinds,spatial):
    world,phase=history[max(0,len(history)-1-sensor_delay)]
    return spatial_expose(variable_expose(lab_raw(world),sensors,kinds,phase),len(sensors),spatial)


def scripted_observations(initial,issued,sensors,actions,kinds,spatial,sensor_delay,actuator_delay):
    """Deterministic observation trace used to expose temporal-gauge equivalence."""
    world=initial;phase=0;queue=[];history=[(world,phase)];out=[temporal_observation(history,sensor_delay,sensors,kinds,spatial)]
    for slot in issued:
        world,phase=delayed_apply(world,phase,queue,slot,actions,actuator_delay);history.append((world,phase))
        out.append(temporal_observation(history,sensor_delay,sensors,kinds,spatial))
    return tuple(out)


def collect_temporal(seed,counts,steps,sensors,actions,kinds,spatial,sensor_delay,actuator_delay,exclude=()):
    rng=random.Random(seed);stats=OpenInterfaceStats(len(sensors));flat=[];sequences=[];support=set();initials=set();exclude=set(exclude)
    counts={family:counts for family in ('push','collect','open')} if isinstance(counts,int) else counts
    for family,total in counts.items():
        accepted=0
        while accepted<total:
            world=lab_world(rng,family);identity=key(world)
            if identity in initials or identity in exclude:continue
            accepted+=1;initials.add(identity);phase=0;queue=[];history=[(world,phase)];sequence=[]
            for _ in range(steps):
                before=temporal_observation(history,sensor_delay,sensors,kinds,spatial);issued=rng.randrange(len(actions))
                world,phase=delayed_apply(world,phase,queue,issued,actions,actuator_delay);history.append((world,phase))
                after=temporal_observation(history,sensor_delay,sensors,kinds,spatial);stats.observe(before,after)
                triple=(before,issued,after);sequence.append(triple);flat.append(triple);support.add(changed(before,after,len(sensors)))
            sequences.append(tuple(sequence))
    return stats,tuple(flat),tuple(sequences),initials,support


def temporal_action_stats(sequences,sensor_mapping,observed_channels,actions,transform,lag):
    aligned=[]
    for sequence in sequences:
        for index,(before,_,after) in enumerate(sequence):
            if index>=lag:aligned.append((before,sequence[index-lag][1],after))
    return spatial_action_stats(aligned,sensor_mapping,observed_channels,actions,transform)


def logsumexp(values):
    top=max(values);return top+math.log(sum(math.exp(value-top) for value in values))


def gauges_for_lag(reference,sequences,sensor_mapping,observed_channels,actions,lag):
    gauges=[];all_values=[]
    for transform in range(8):
        target=temporal_action_stats(sequences,sensor_mapping,observed_channels,actions,transform,lag);ranked=sorted(action_candidates(reference,target));all_values.extend(x[0] for x in ranked)
        top=ranked[-1][0];z=sum(math.exp(value-top) for value,_ in ranked);gauges.append({'transform':transform,'mapping':ranked[-1][1],
            'log_probability':top,'posterior':1/z,'log_margin':top-ranked[-2][0],'candidate_slots':ranked[-1][1]})
    return tuple(gauges),logsumexp(all_values)


def infer_temporal_gauge(reference,sequences,sensor_mapping,observed_channels,actions,stream_sequences=(),maximum_lag=MAX_LAG):
    """Marginalize D4/action hypotheses, then select the identifiable total lag."""
    candidates=[]
    for lag in range(maximum_lag+1):
        gauges,evidence=gauges_for_lag(reference,sequences,sensor_mapping,observed_channels,actions,lag)
        candidates.append({'lag':lag,'log_evidence':evidence,'gauges':gauges})
    ranked=sorted(candidates,key=lambda row:(row['log_evidence'],row['lag']));top=ranked[-1]['log_evidence'];z=sum(math.exp(row['log_evidence']-top) for row in ranked)
    selected=ranked[-1];single=max(selected['gauges'],key=lambda row:(row['log_probability'],row['transform'],row['mapping']));streams=[]
    for sequences_in_stream in stream_sequences:
        rows=[]
        for lag in range(maximum_lag+1):
            gauges,evidence=gauges_for_lag(reference,sequences_in_stream,sensor_mapping,observed_channels,actions,lag);rows.append({'lag':lag,'log_evidence':evidence,'gauges':gauges})
        rows.sort(key=lambda row:(row['log_evidence'],row['lag']));streams.append({'lag':rows[-1]['lag'],'log_margin':rows[-1]['log_evidence']-rows[-2]['log_evidence'],'gauges':rows[-1]['gauges']})
    return {'lag':selected['lag'],'posterior':1/z,'log_margin':top-ranked[-2]['log_evidence'],'single':single,
        'gauges':selected['gauges'],'candidate_lags':tuple(candidates),'per_stream':tuple(streams)}


def evaluate_temporal(policies,suite,sensors,actions,kinds,spatial,sensor_delay,actuator_delay,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;phase=0;queue=[];history=[(world,phase)];path=[]
                for _ in range(steps):
                    observed=temporal_observation(history,sensor_delay,sensors,kinds,spatial);identity=(name,observed)
                    if identity not in cache:cache[identity]=policy.probabilities(observed)
                    issued=choose(cache[identity],rng);path.append(issued);world,phase=delayed_apply(world,phase,queue,issued,actions,actuator_delay);history.append((world,phase));success=done(family,initial,world)
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces


def averaged_policy(learner,sensor_mapping,observed_channels,gauges,observed_actions):
    return GaugeAveragedPolicy(learner,sensor_mapping,observed_channels,((x['transform'],x['mapping']) for x in gauges),observed_actions)
