#!/usr/bin/env python3
"""BPC v0.38: censored event-boundary posterior gates temporal control."""
import hashlib,pickle,random
from collections import Counter,defaultdict

from bpc_direct_composition_v09 import choose
from bpc_effect_transition_v37 import compact_transitions
from bpc_temporal_policy_v32 import ActionTransitions
from bpc_three_factor_v12 import FieldPolicy,ThreeFactorBPC,changed_planes,key,random_world,raw,step,succeeded


def norm(values):
    total=sum(values);return [value/total for value in values]


class EventBoundary:
    def __init__(self):self.rows=defaultdict(lambda:defaultdict(lambda:[0,0]));self.effects=set();self.writes=0
    def observe(self,signature,compact):
        for index,(before,_,after) in enumerate(compact):
            effect=changed_planes(before,after);continued=int(index+1<len(compact));self.effects.add(effect);self.rows[signature][effect][continued]+=1;self.writes+=1
    def probability(self,signatures,effect,mode='effect'):
        if mode=='shuffle' and self.effects:
            ordered=tuple(sorted(self.effects));effect=ordered[(ordered.index(effect)+1)%len(ordered)] if effect in ordered else effect
        values=[]
        for signature in signatures:
            if mode=='global':
                no=yes=0
                for row in self.rows.get(signature,{}).values():no+=row[0];yes+=row[1]
            else:no,yes=self.rows.get(signature,{}).get(effect,(0,0))
            if no+yes:values.append((yes+1)/(no+yes+2))
        value=sum(values)/len(values) if values else .5
        return 1-value if mode=='invert' else value
    def digest(self):
        value=tuple((signature,tuple((effect,tuple(counts)) for effect,counts in sorted(rows.items()))) for signature,rows in sorted(self.rows.items()))
        return hashlib.sha256(pickle.dumps(value,protocol=5)).hexdigest()


class BoundaryPolicy:
    def __init__(self,learner,temporal,boundary,drop=(),mode='effect',fixed=None,rotated=False):
        self.learner=learner;self.temporal=temporal;self.boundary=boundary;self.base=FieldPolicy(learner,rotated,drop);ordered=tuple(sorted(learner.factors));self.drop={ordered[i] for i in drop if 0<=i<len(ordered)}
        self.mode=mode;self.fixed=fixed;self.context=None
    def reset(self):self.context=None
    def probabilities(self,state):
        base=self.base.probabilities(state)
        if self.context is None:return base
        previous,effect,signatures=self.context;signatures=tuple(signature for signature in signatures if signature not in self.drop)
        if len(signatures)<2:return base
        transition=self.temporal.probabilities(signatures,previous)
        if transition is None:return base
        temporal=norm([base[action]*transition[action] for action in range(4)]);continuation=self.fixed if self.fixed is not None else self.boundary.probability(signatures,effect,self.mode)
        return [(1-continuation)*base[action]+continuation*temporal[action] for action in range(4)]
    def observed(self,before,action,after):self.context=(action,changed_planes(before,after),self.learner.active(before))


def train(seed,uniform_episodes=800,guided_rounds=2,guided_episodes=400,steps=120):
    rng=random.Random(seed);learner=ThreeFactorBPC();temporal=ActionTransitions();boundary=EventBoundary();events=Counter();schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect','open'):
        for guided in schedule:
            world=random_world(rng,family);initial=world;trace=[];learner.training_initials.add(key(world))
            for _ in range(steps):
                before=raw(world);probability=FieldPolicy(learner).probabilities(before);action=choose(probability,rng) if guided and rng.random()>.25 else rng.randrange(4)
                nxt=step(world,action);trace.append((before,action,raw(nxt)));world=nxt
                if succeeded(family,initial,world):
                    compact=compact_transitions(trace);signature,length=learner.observe_success(trace);temporal.observe(signature,[(state,action) for state,action,_ in compact]);boundary.observe(signature,compact)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=length;events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,temporal,boundary,dict(events)
