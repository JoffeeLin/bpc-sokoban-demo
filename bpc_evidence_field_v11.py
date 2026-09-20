#!/usr/bin/env python3
"""BPC v0.11 development: one additive field query over anonymous factors."""
from __future__ import annotations

import math,random
from collections import Counter

from bpc_autofactor_v10 import signature_roles
from bpc_cross_task_v07 import truth
from bpc_direct_composition_v09 import choose,raw

ACTIONS=4;TEMPERATURE=.72


def components(source,state):
    """Recover prior and relational log evidence before final Choice softmax."""
    by_family={i:[] for i in range(8 if source.encoder.high_order else 5)}
    for address in source.encoder.encode(state):
        row=source.cube.get(address)
        if row is not None:by_family[address[0]].append(row)
    total=sum(source.success_prior);prior=[(x+1)/(total+4) for x in source.success_prior];families=[]
    for rows in by_family.values():
        local=[0.]*ACTIONS;support=0.
        for row in rows:
            count=sum(row[:ACTIONS])
            if count<3:continue
            probability=[(row[a]+1)/(count+ACTIONS) for a in range(ACTIONS)];reliability=min(4.,math.log1p(count))
            for action in range(ACTIONS):local[action]+=reliability*math.log(probability[action])
            support+=reliability
        if support:families.append([x/support for x in local])
    evidence=[sum(row[a] for row in families)/len(families) if families else 0. for a in range(ACTIONS)]
    return prior,evidence


def normalize(logits,temperature=TEMPERATURE):
    top=max(logits);values=[math.exp((x-top)/temperature) for x in logits];total=sum(values)
    return [x/total for x in values]


class EvidenceFieldPolicy:
    """Add factor evidence in one field; include one pooled learned prior."""
    def __init__(self,learner,mode='sum',rotated=False,permuted=False):
        self.learner=learner;self.mode=mode;self.permuted=permuted
        self.sources={key:(cube.rotated() if rotated else cube) for key,cube in learner.factors.items()}

    def probabilities(self,state):
        active=self.learner.active(state,self.permuted)
        if not active:return [.25]*ACTIONS
        rows=[components(self.sources[key],state) for key in active];counts=[0]*ACTIONS
        for key in active:
            for action,value in enumerate(self.sources[key].success_prior):counts[action]+=value
        total=sum(counts);prior=[(x+1)/(total+ACTIONS) for x in counts]
        evidence=[sum(row[1][a] for row in rows) for a in range(ACTIONS)]
        if self.mode=='mean':evidence=[x/len(rows) for x in evidence]
        if self.mode=='no_prior':prior=[.25]*ACTIONS
        logits=[.12*math.log(prior[a])+evidence[a] for a in range(ACTIONS)]
        return normalize(logits)


class ProductPolicy:
    def __init__(self,learner):self.learner=learner
    def probabilities(self,state):return self.learner.probabilities(state)


class SharedPolicy:
    def __init__(self,learner):self.learner=learner
    def probabilities(self,state):return self.learner.shared.probabilities(state)


def evaluate(policies,suite,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    roles=signature_roles(next(iter(policies.values())).learner)
    for index,(family,initial,distance) in enumerate(suite):
        oracle=(roles[2],) if family=='push' else (roles[3],) if family=='collect' else (roles[2],roles[3])
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;path=[]
                for _ in range(steps):
                    state=raw(world);key=(name,state)
                    if key not in cache:cache[key]=policy.probabilities(state)
                    action=choose(cache[key],rng);path.append(action);nxt=truth(world,action)
                    success=nxt.objects!=initial.objects if family=='push' else nxt.marks==0;world=nxt
                    if name=='field':
                        rows[name]['routing_decisions']+=1
                        rows[name]['routing_mismatches']+=policy.learner.active(state)!=tuple(sorted(oracle))
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
