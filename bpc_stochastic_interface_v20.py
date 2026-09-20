#!/usr/bin/env python3
"""BPC v0.20 development: probabilistic actuator-channel gauge binding."""
from __future__ import annotations

import hashlib,math,pickle,random
from collections import Counter

from bpc_cross_generator_v17 import changed,done,key,lab_raw,lab_step,lab_world,variable_expose
from bpc_direct_composition_v09 import choose
from bpc_open_interface_v15 import OpenInterfaceStats,canonicalize_subset
from bpc_spatial_interface_v18 import spatial_expose,spatial_restore
from bpc_temporal_interface_v19 import logsumexp,temporal_observation
from bpc_three_factor_v12 import CHANNELS,FieldPolicy

COMPONENTS=4


def sample(probability,rng):
    point=rng.random();total=0.
    for index,value in enumerate(probability):
        total+=value
        if point<=total:return index
    return len(probability)-1


def stochastic_apply(world,phase,slot,channels,rng):
    """Sample a physical effect; None slots only perturb nuisance sensor planes."""
    row=channels[slot]
    if row is None:
        mode=sum(x is None for x in channels[:slot]);return world,phase^(1<<mode)
    effect=sample(row,rng)
    return (lab_step(world,effect),phase) if effect<4 else (world,phase)


def delayed_stochastic_apply(world,phase,queue,issued,channels,rng,delay):
    queue.append(issued)
    if len(queue)<=delay:return world,phase
    return stochastic_apply(world,phase,queue.pop(0),channels,rng)


def collect_stochastic(seed,counts,steps,sensors,channels,kinds,spatial,sensor_delay,actuator_delay,exclude=()):
    rng=random.Random(seed);stats=OpenInterfaceStats(len(sensors));flat=[];sequences=[];support=set();initials=set();exclude=set(exclude)
    counts={family:counts for family in ('push','collect','open')} if isinstance(counts,int) else counts
    for family,total in counts.items():
        accepted=0
        while accepted<total:
            world=lab_world(rng,family);identity=key(world)
            if identity in initials or identity in exclude:continue
            accepted+=1;initials.add(identity);phase=0;queue=[];history=[(world,phase)];sequence=[]
            for _ in range(steps):
                before=temporal_observation(history,sensor_delay,sensors,kinds,spatial);issued=rng.randrange(len(channels))
                world,phase=delayed_stochastic_apply(world,phase,queue,issued,channels,rng,actuator_delay);history.append((world,phase))
                after=temporal_observation(history,sensor_delay,sensors,kinds,spatial);stats.observe(before,after)
                triple=(before,issued,after);sequence.append(triple);flat.append(triple);support.add(changed(before,after,len(sensors)))
            sequences.append(tuple(sequence))
    return stats,tuple(flat),tuple(sequences),initials,support


def effect_features(before,after,channels=CHANNELS):
    values=[];changed_total=0
    for channel in range(channels):
        old=before[channel::channels];new=after[channel::channels]
        lost=[i for i,(a,b) in enumerate(zip(old,new)) if a and not b];gained=[i for i,(a,b) in enumerate(zip(old,new)) if b and not a]
        flip=len(lost)+len(gained);changed_total+=flip
        motion=tuple(sorted((target%7-source%7,target//7-source//7) for source in lost for target in gained if abs(target%7-source%7)<=1 and abs(target//7-source//7)<=1))
        values.extend((sum(new)-sum(old),flip,motion))
    return (changed_total,*values)


class EffectProfiles:
    """Action-conditional categorical probabilities over raw transition effects."""
    def __init__(self,actions=COMPONENTS):self.actions=actions;self.n=[0]*actions;self.features=[[Counter() for _ in range(1+CHANNELS*3)] for _ in range(actions)]
    def observe(self,before,action,after):
        self.n[action]+=1
        for index,value in enumerate(effect_features(before,after)):self.features[action][index][value]+=1
    def logs(self,before,after):
        values=effect_features(before,after);out=[]
        for action in range(self.actions):
            value=0.
            for index,item in enumerate(values):
                row=self.features[action][index];value+=math.log((row[item]+1)/(self.n[action]+len(row)+1))
            out.append(value)
        return tuple(out)
    def digest(self):
        rows=(self.actions,tuple(self.n),tuple(tuple(tuple(sorted(x.items())) for x in row) for row in self.features))
        return hashlib.sha256(pickle.dumps(rows,protocol=5)).hexdigest()


def effect_profiles(triples,actions=COMPONENTS):
    out=EffectProfiles(actions)
    for before,action,after in triples:out.observe(before,action,after)
    return out


def fit_mixture(log_rows,iterations=32,prior=.5):
    """Probability-only EM over aggregated raw-effect likelihood vectors."""
    counts=Counter(log_rows);components=len(next(iter(counts)));weights=[1/components]*components
    for _ in range(iterations):
        totals=[prior]*components
        for logs,n in counts.items():
            joint=[math.log(max(weights[i],1e-300))+logs[i] for i in range(components)];z=logsumexp(joint)
            for i,value in enumerate(joint):totals[i]+=n*math.exp(value-z)
        mass=sum(totals);updated=[x/mass for x in totals]
        if max(abs(a-b) for a,b in zip(weights,updated))<1e-9:weights=updated;break
        weights=updated
    evidence=0.
    for logs,n in counts.items():evidence+=n*logsumexp([math.log(max(weights[i],1e-300))+logs[i] for i in range(components)])
    return tuple(weights),evidence


def fit_gauge(reference,sequences,sensor_mapping,observed_channels,observed_actions,transform,lag):
    grouped=[[] for _ in range(observed_actions)];active=[False]*observed_actions
    for sequence in sequences:
        for index,(before,_,after) in enumerate(sequence):
            if index<lag:continue
            issued=sequence[index-lag][1]
            before=spatial_restore(canonicalize_subset(before,sensor_mapping,observed_channels),CHANNELS,transform)
            after=spatial_restore(canonicalize_subset(after,sensor_mapping,observed_channels),CHANNELS,transform)
            grouped[issued].append(reference.logs(before,after));active[issued]|=before!=after
    rows=[];evidence=0.
    for slot,values in enumerate(grouped):
        if active[slot]:
            weights,value=fit_mixture(values);rows.append(tuple(weights)+(0.,));evidence+=value
        else:
            # A nuisance actuator can perturb ignored raw planes but never the six
            # recovered canonical planes.  Its physical channel is therefore the
            # distinct no-effect component, not a fifth mixture component that is
            # confounded with a blocked directional action.
            rows.append((0.,0.,0.,0.,1.))
    return tuple(rows),evidence


def gauges_for_stochastic_lag(reference,sequences,sensor_mapping,observed_channels,observed_actions,lag):
    gauges=[]
    for transform in range(8):
        rows,evidence=fit_gauge(reference,sequences,sensor_mapping,observed_channels,observed_actions,transform,lag)
        gauges.append({'transform':transform,'rows':rows,'log_probability':evidence})
    top=max(x['log_probability'] for x in gauges);z=sum(math.exp(x['log_probability']-top) for x in gauges)
    return tuple({**x,'posterior':math.exp(x['log_probability']-top)/z} for x in gauges),logsumexp([x['log_probability'] for x in gauges])


def infer_stochastic_gauge(reference,sequences,sensor_mapping,observed_channels,observed_actions,stream_sequences=(),maximum_lag=4):
    candidates=[]
    for lag in range(maximum_lag+1):
        gauges,evidence=gauges_for_stochastic_lag(reference,sequences,sensor_mapping,observed_channels,observed_actions,lag)
        candidates.append({'lag':lag,'log_evidence':evidence,'gauges':gauges})
    ranked=sorted(candidates,key=lambda x:(x['log_evidence'],x['lag']));top=ranked[-1]['log_evidence'];z=sum(math.exp(x['log_evidence']-top) for x in ranked);selected=ranked[-1]
    streams=[]
    for sequence in stream_sequences:
        rows=[]
        for lag in range(maximum_lag+1):
            gauges,evidence=gauges_for_stochastic_lag(reference,sequence,sensor_mapping,observed_channels,observed_actions,lag);rows.append({'lag':lag,'log_evidence':evidence,'gauges':gauges})
        rows.sort(key=lambda x:(x['log_evidence'],x['lag']));streams.append({'lag':rows[-1]['lag'],'log_margin':rows[-1]['log_evidence']-rows[-2]['log_evidence'],'gauges':rows[-1]['gauges']})
    return {'lag':selected['lag'],'posterior':1/z,'log_margin':top-ranked[-2]['log_evidence'],'gauges':selected['gauges'],
        'single':max(selected['gauges'],key=lambda x:(x['log_probability'],x['transform'])),'candidate_lags':tuple(candidates),'per_stream':tuple(streams)}


class StochasticGaugePolicy:
    """Bayesian backward channel followed by direct BPC action probabilities."""
    def __init__(self,learner,sensor_mapping,observed_channels,gauges,observed_actions):
        self.field=FieldPolicy(learner);self.sensor_mapping=tuple(sensor_mapping);self.observed_channels=observed_channels;self.observed_actions=observed_actions
        self.gauges=tuple((x['transform'],tuple(tuple(row) for row in x['rows'])) for x in gauges)
    def probabilities(self,observed):
        canonicalized=canonicalize_subset(observed,self.sensor_mapping,self.observed_channels);out=[0.]*self.observed_actions
        for transform,rows in self.gauges:
            desired=self.field.probabilities(spatial_restore(canonicalized,CHANNELS,transform));denom=[sum(row[a] for row in rows) for a in range(4)]
            for slot,row in enumerate(rows):out[slot]+=sum(desired[a]*row[a]/max(denom[a],1e-300) for a in range(4))
        total=sum(out);return [x/total for x in out]


def mode_rows(rows):
    out=[]
    for row in rows:
        dominant=max(range(5),key=lambda x:(row[x],-x));value=[0.]*5;value[dominant]=1.;out.append(tuple(value))
    return tuple(out)


def evaluate_stochastic(policies,suite,sensors,channels,kinds,spatial,sensor_delay,actuator_delay,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            base=seed+index*100000+episode
            for offset,(name,policy) in enumerate(policies.items()):
                action_rng=random.Random(base);effect_rng=random.Random(base+900000001);world=initial;phase=0;queue=[];history=[(world,phase)];path=[]
                for _ in range(steps):
                    observed=temporal_observation(history,sensor_delay,sensors,kinds,spatial);identity=(name,observed)
                    if identity not in cache:cache[identity]=policy.probabilities(observed)
                    issued=choose(cache[identity],action_rng);path.append(issued)
                    world,phase=delayed_stochastic_apply(world,phase,queue,issued,channels,effect_rng,actuator_delay);history.append((world,phase));success=done(family,initial,world)
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
