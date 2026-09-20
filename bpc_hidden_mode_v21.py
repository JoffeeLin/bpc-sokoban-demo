#!/usr/bin/env python3
"""BPC v0.21: unlabeled hidden-mode actuator inference and online filtering."""
from __future__ import annotations

import itertools,math,random
from collections import Counter

from bpc_cross_generator_v17 import changed,done,key,lab_raw,lab_step,lab_world,variable_expose
from bpc_direct_composition_v09 import choose
from bpc_open_interface_v15 import OpenInterfaceStats,canonicalize_subset
from bpc_spatial_interface_v18 import spatial_expose,spatial_restore
from bpc_stochastic_interface_v20 import sample
from bpc_temporal_interface_v19 import logsumexp
from bpc_three_factor_v12 import FieldPolicy


def collect_hidden(seed,counts,steps,channels,transition,initial=(.5,.5),exclude=()):
    """Generate unlabeled calibration streams; hidden modes are evaluator-only."""
    rng=random.Random(seed);sequences=[];truth=[];initials=set();exclude=set(exclude)
    counts={family:counts for family in ('push','collect','open')} if isinstance(counts,int) else counts
    for family,total in counts.items():
        accepted=0
        while accepted<total:
            world=lab_world(rng,family);identity=key(world)
            if identity in exclude or identity in initials:continue
            accepted+=1;initials.add(identity);mode=sample(initial,rng);sequence=[];labels=[]
            for _ in range(steps):
                before=lab_raw(world);slot=rng.randrange(len(channels[0]));effect=sample(channels[mode][slot],rng)
                world=lab_step(world,effect);after=lab_raw(world);sequence.append((before,slot,after));labels.append(mode)
                mode=sample(transition[mode],rng)
            sequences.append(tuple(sequence));truth.append(tuple(labels))
    return tuple(sequences),initials,tuple(truth)


def collect_hidden_interface(seed,counts,steps,sensors,kinds,spatial,delay,channels,transition,initial,exclude=()):
    """Anonymous/D4/delayed observations with modes hidden from every learner."""
    rng=random.Random(seed);stats=OpenInterfaceStats(len(sensors));flat=[];sequences=[];truth=[];initials=set();support=set();exclude=set(exclude)
    counts={family:counts for family in ('push','collect','open')} if isinstance(counts,int) else counts
    observe=lambda world,phase:spatial_expose(variable_expose(lab_raw(world),sensors,kinds,phase),len(sensors),spatial)
    for family,total in counts.items():
        accepted=0
        while accepted<total:
            world=lab_world(rng,family);identity=key(world)
            if identity in exclude or identity in initials:continue
            accepted+=1;initials.add(identity);mode=sample(initial,rng);phase=0;queue=[];sequence=[];labels=[]
            for _ in range(steps):
                before=observe(world,phase);issued=rng.randrange(4);queue.append(issued)
                if len(queue)>delay:world=lab_step(world,sample(channels[mode][queue.pop(0)],rng))
                after=observe(world,phase);triple=(before,issued,after);stats.observe(before,after);flat.append(triple);sequence.append(triple);labels.append(mode);support.add(changed(before,after,len(sensors)))
                mode=sample(transition[mode],rng)
            sequences.append(tuple(sequence));truth.append(tuple(labels))
    return stats,tuple(flat),tuple(sequences),initials,support,tuple(truth)


def canonical_hidden_sequences(sequences,mapping,observed_channels,transform,lag,start=None):
    out=[]
    for sequence in sequences:
        row=[]
        for index,(before,_,after) in enumerate(sequence):
            if index<max(lag,start or 0):continue
            restore=lambda value:spatial_restore(canonicalize_subset(value,mapping,observed_channels),6,transform)
            row.append((restore(before),sequence[index-lag][1],restore(after)))
        out.append(tuple(row))
    return tuple(out)


def infer_hidden_lag(profiles,sequences,mapping,observed_channels,transform=0,maximum_lag=4,prior=.5):
    """Compare equal-length action/effect probability evidence before HMM fitting."""
    candidates=[]
    for lag in range(maximum_lag+1):
        counts=[[prior]*4 for _ in range(4)];rows=canonical_hidden_sequences(sequences,mapping,observed_channels,transform,lag,maximum_lag)
        for sequence in rows:
            for before,slot,after in sequence:
                logs=profiles.logs(before,after);z=logsumexp(logs)
                for action in range(4):counts[slot][action]+=math.exp(logs[action]-z)
        value=sum(math.lgamma(4*prior)-math.lgamma(sum(row))+sum(math.lgamma(x)-math.lgamma(prior) for x in row) for row in counts)
        candidates.append({'lag':lag,'log_probability':value})
    ranked=sorted(candidates,key=lambda x:(x['log_probability'],x['lag']));top=ranked[-1]['log_probability'];z=sum(math.exp(x['log_probability']-top) for x in ranked)
    return {'lag':ranked[-1]['lag'],'posterior':1/z,'log_margin':top-ranked[-2]['log_probability'],'candidates':tuple(candidates)}


def _normalized(values):
    total=sum(values);return tuple(x/total for x in values)


def forward_backward(records,initial,transition,channels):
    """Exact probability recursion; records are (issued slot, component log-likelihoods)."""
    modes=len(initial);emit=[[logsumexp([math.log(max(channels[m][slot][a],1e-300))+logs[a] for a in range(4)])
        for m in range(modes)] for slot,logs in records]
    forward=[[math.log(max(initial[m],1e-300))+emit[0][m] for m in range(modes)]]
    for t in range(1,len(records)):
        forward.append([emit[t][j]+logsumexp([forward[-1][i]+math.log(max(transition[i][j],1e-300)) for i in range(modes)]) for j in range(modes)])
    log_probability=logsumexp(forward[-1]);backward=[[0.]*modes for _ in records]
    for t in range(len(records)-2,-1,-1):
        backward[t]=[logsumexp([math.log(max(transition[i][j],1e-300))+emit[t+1][j]+backward[t+1][j] for j in range(modes)]) for i in range(modes)]
    gamma=[_normalized([math.exp(forward[t][m]+backward[t][m]-log_probability) for m in range(modes)]) for t in range(len(records))]
    xi=[]
    for t in range(len(records)-1):
        row=[[math.exp(forward[t][i]+math.log(max(transition[i][j],1e-300))+emit[t+1][j]+backward[t+1][j]-log_probability) for j in range(modes)] for i in range(modes)]
        z=sum(map(sum,row));xi.append(tuple(tuple(x/z for x in values) for values in row))
    return gamma,xi,log_probability


def _ordered(initial,transition,channels):
    order=sorted(range(len(initial)),key=lambda m:tuple(x for row in channels[m] for x in row))
    return tuple(initial[m] for m in order),tuple(tuple(transition[i][j] for j in order) for i in order),tuple(channels[m] for m in order)


def fit_hidden_channels(profiles,sequences,modes=2,restarts=10,iterations=40,prior=.5,seed=0):
    """Baum-Welch with latent physical-effect responsibilities; no mode labels."""
    prepared=tuple(tuple((slot,profiles.logs(before,after)) for before,slot,after in sequence) for sequence in sequences);rng=random.Random(seed);best=None
    for _ in range(restarts):
        initial=_normalized([rng.random()+.2 for _ in range(modes)])
        transition=tuple(_normalized([rng.random()+(.8 if i==j else .2) for j in range(modes)]) for i in range(modes))
        channels=tuple(tuple(_normalized([rng.random()+.05 for _ in range(4)]) for _ in range(4)) for _ in range(modes))
        for _ in range(iterations):
            initial_counts=[prior]*modes;transition_counts=[[prior]*modes for _ in range(modes)];channel_counts=[[[prior]*4 for _ in range(4)] for _ in range(modes)];total_probability=0.
            for records in prepared:
                gamma,xi,value=forward_backward(records,initial,transition,channels);total_probability+=value
                for m in range(modes):initial_counts[m]+=gamma[0][m]
                for row in xi:
                    for i in range(modes):
                        for j in range(modes):transition_counts[i][j]+=row[i][j]
                for t,(slot,logs) in enumerate(records):
                    for m in range(modes):
                        joint=[math.log(max(channels[m][slot][a],1e-300))+logs[a] for a in range(4)];z=logsumexp(joint)
                        for a in range(4):channel_counts[m][slot][a]+=gamma[t][m]*math.exp(joint[a]-z)
            initial=_normalized(initial_counts);transition=tuple(_normalized(row) for row in transition_counts);channels=tuple(tuple(_normalized(row) for row in mode) for mode in channel_counts)
        total_probability=sum(forward_backward(row,initial,transition,channels)[2] for row in prepared)
        candidate=(total_probability,*_ordered(initial,transition,channels))
        if best is None or candidate[0]>best[0]:best=candidate
    return {'log_probability':best[0],'initial':best[1],'transition':best[2],'channels':best[3],'restarts':restarts,'iterations':iterations}


def update_belief(belief,slot,logs,transition,channels):
    joint=[]
    for m,row in enumerate(channels):joint.append(math.log(max(belief[m],1e-300))+logsumexp([math.log(max(row[slot][a],1e-300))+logs[a] for a in range(4)]))
    top=max(joint);posterior=_normalized([math.exp(x-top) for x in joint]);predicted=tuple(sum(posterior[i]*transition[i][j] for i in range(len(posterior))) for j in range(len(posterior)))
    return posterior,predicted


def stationary(transition):
    belief=tuple(1/len(transition) for _ in transition)
    for _ in range(256):belief=tuple(sum(belief[i]*transition[i][j] for i in range(len(belief))) for j in range(len(belief)))
    return belief


def reverse_channel(desired,belief,channels):
    out=[0.]*len(channels[0])
    for weight,rows in zip(belief,channels):
        denom=[sum(row[a] for row in rows) for a in range(4)]
        for slot,row in enumerate(rows):out[slot]+=weight*sum(desired[a]*row[a]/max(denom[a],1e-300) for a in range(4))
    return _normalized(out)


def aligned_error(model,true_channels,true_transition,true_initial):
    best=None
    for order in itertools.permutations(range(len(true_initial))):
        channel=max(.5*sum(abs(model['channels'][m][slot][a]-true_channels[order[m]][slot][a]) for a in range(4))
            for m in range(len(order)) for slot in range(4))
        transition=max(abs(model['transition'][i][j]-true_transition[order[i]][order[j]]) for i in range(len(order)) for j in range(len(order)))
        initial=max(abs(model['initial'][i]-true_initial[order[i]]) for i in range(len(order)))
        row=(channel+transition+initial,channel,transition,initial,order)
        if best is None or row<best:best=row
    return {'maximum_channel_total_variation':best[1],'maximum_transition_error':best[2],'maximum_initial_error':best[3],'model_to_truth':best[4]}


def filter_accuracy(profiles,sequences,truth,model,model_to_truth):
    correct=total=0
    for sequence,labels in zip(sequences,truth):
        belief=model['initial']
        for (before,slot,after),label in zip(sequence,labels):
            posterior,belief=update_belief(belief,slot,profiles.logs(before,after),model['transition'],model['channels'])
            correct+=model_to_truth[max(range(len(posterior)),key=posterior.__getitem__)]==label;total+=1
    return correct/total


def evaluate_hidden(learner,profiles,model,suite,true_channels,true_transition,true_initial,seed,episodes,steps):
    """Compare ephemeral filtering with same-information causal controls."""
    learned=model['channels'];shuffled=tuple(tuple(mode[(slot+1)%4] for slot in range(4)) for mode in learned);flat=stationary(model['transition'])
    conditions={'online':(learned,model['transition'],model['initial'],'online'),'memoryless':(learned,model['transition'],flat,'fixed'),
        'no_update':(learned,model['transition'],model['initial'],'fixed'),'shuffled':(shuffled,model['transition'],model['initial'],'online'),
        'oracle':(true_channels,true_transition,true_initial,'oracle')};rows={name:Counter() for name in conditions};traces={name:{} for name in conditions};field=FieldPolicy(learner)
    for index,(family,initial_world,_) in enumerate(suite):
        for episode in range(episodes):
            base=seed+index*100000+episode
            for name,(channels,transition,initial_belief,kind) in conditions.items():
                action_rng=random.Random(base);effect_rng=random.Random(base+700000001);mode_rng=random.Random(base+800000003)
                world=initial_world;mode=sample(true_initial,mode_rng);belief=initial_belief;path=[]
                for _ in range(steps):
                    before=lab_raw(world);controller_belief=tuple(1. if i==mode else 0. for i in range(len(true_initial))) if kind=='oracle' else belief
                    slot=choose(reverse_channel(field.probabilities(before),controller_belief,channels),action_rng);path.append(slot)
                    effect=sample(true_channels[mode][slot],effect_rng);world=lab_step(world,effect);after=lab_raw(world);success=done(family,initial_world,world)
                    if success:break
                    if kind=='online':_,belief=update_belief(belief,slot,profiles.logs(before,after),transition,channels)
                    mode=sample(true_transition[mode],mode_rng)
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces


def evaluate_hidden_interface(learner,profiles,model,suite,sensors,kinds,spatial,delay,mapping,transform,
        environment_channels,oracle_channels,true_transition,true_initial,seed,episodes,steps):
    """Frozen online filtering through an anonymous spatial and delayed interface."""
    learned=model['channels'];shuffled=tuple(tuple(mode[(slot+1)%4] for slot in range(4)) for mode in learned);flat=stationary(model['transition'])
    conditions={'online':(learned,model['transition'],flat,'online',delay),'memoryless':(learned,model['transition'],flat,'fixed',delay),
        'no_update':(learned,model['transition'],model['initial'],'fixed',delay),'shuffled':(shuffled,model['transition'],flat,'online',delay),
        'zero_lag':(learned,model['transition'],flat,'online',0),'oracle':(oracle_channels,true_transition,true_initial,'oracle',delay)}
    rows={name:Counter() for name in conditions};traces={name:{} for name in conditions};field=FieldPolicy(learner)
    restore=lambda value:spatial_restore(canonicalize_subset(value,mapping,len(sensors)),6,transform)
    observe=lambda world,phase:spatial_expose(variable_expose(lab_raw(world),sensors,kinds,phase),len(sensors),spatial)
    for index,(family,initial_world,_) in enumerate(suite):
        for episode in range(episodes):
            base=seed+index*100000+episode
            for name,(channels,transition,initial_belief,kind,assumed_lag) in conditions.items():
                action_rng=random.Random(base);effect_rng=random.Random(base+700000001);mode_rng=random.Random(base+800000003)
                world=initial_world;mode=sample(true_initial,mode_rng);belief=initial_belief;queue=[];issued=[];phase=0;path=[]
                for t in range(steps):
                    before=observe(world,phase);canonical=restore(before);controller=tuple(1. if i==mode else 0. for i in range(len(true_initial))) if kind=='oracle' else belief
                    slot=choose(reverse_channel(field.probabilities(canonical),controller,channels),action_rng);path.append(slot);issued.append(slot);queue.append(slot)
                    if len(queue)>delay:world=lab_step(world,sample(environment_channels[mode][queue.pop(0)],effect_rng))
                    after=observe(world,phase);success=done(family,initial_world,world)
                    if success:break
                    if kind=='online' and t>=assumed_lag:
                        old=restore(before);new=restore(after);_,belief=update_belief(belief,issued[t-assumed_lag],profiles.logs(old,new),transition,channels)
                    elif kind=='online':belief=tuple(sum(belief[i]*transition[i][j] for i in range(len(belief))) for j in range(len(belief)))
                    mode=sample(true_transition[mode],mode_rng)
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
