#!/usr/bin/env python3
"""BPC v0.36: learned action-run survival from separate successful traces."""
import hashlib,pickle,random
from collections import Counter,defaultdict

from bpc_direct_composition_v09 import choose
from bpc_three_factor_v12 import FieldPolicy,ThreeFactorBPC,key,random_world,raw,step,succeeded
from experiment_v5 import erase_zero_effect_cycles


class RunSurvival:
    def __init__(self):self.rows=defaultdict(lambda:defaultdict(Counter));self.writes=0
    def observe(self,signature,compact):
        actions=[action for _,action in compact]
        for index in range(len(actions)):
            if index and actions[index]==actions[index-1]:continue
            end=index+1
            while end<len(actions) and actions[end]==actions[index]:end+=1
            self.rows[signature][actions[index]][end-index]+=1;self.writes+=1
    def probability(self,signatures,action,age,shuffle_action=0,shuffle_factor=0,ordered=()):
        values=[]
        for signature in signatures:
            paired=ordered[(ordered.index(signature)+shuffle_factor)%len(ordered)] if shuffle_factor and signature in ordered else signature
            counts=self.rows.get(paired,{}).get((action+shuffle_action)%4,{})
            eligible=sum(value for length,value in counts.items() if length>=age);continued=sum(value for length,value in counts.items() if length>age)
            if eligible:values.append((continued+.5)/(eligible+1.))
        return sum(values)/len(values) if values else .5
    def digest(self):
        value=tuple((signature,tuple((action,tuple(sorted(counts.items()))) for action,counts in sorted(rows.items()))) for signature,rows in sorted(self.rows.items()))
        return hashlib.sha256(pickle.dumps(value,protocol=5)).hexdigest()


class RunPolicy:
    def __init__(self,learner,runs,drop=(),shuffle_action=0,shuffle_factor=0,no_age=False,rotated=False):
        self.learner=learner;self.runs=runs;self.base=FieldPolicy(learner,rotated,drop);self.ordered=tuple(sorted(learner.factors));self.drop={self.ordered[i] for i in drop if 0<=i<len(self.ordered)}
        self.shuffle_action=shuffle_action;self.shuffle_factor=shuffle_factor;self.no_age=no_age;self.previous=None;self.age=0
    def reset(self):self.previous=None;self.age=0
    def probabilities(self,state):
        base=self.base.probabilities(state);active=tuple(signature for signature in self.learner.active(state) if signature not in self.drop)
        if self.previous is None or len(active)<2:return base
        survival=self.runs.probability(active,self.previous,1 if self.no_age else self.age,self.shuffle_action,self.shuffle_factor,self.ordered)
        probability=[(1-survival)*value for value in base];probability[self.previous]+=survival;return probability
    def chose(self,action):
        if action==self.previous:self.age+=1
        else:self.previous=action;self.age=1


def train(seed,uniform_episodes=800,guided_rounds=2,guided_episodes=400,steps=120):
    rng=random.Random(seed);learner=ThreeFactorBPC();runs=RunSurvival();events=Counter();schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect','open'):
        for guided in schedule:
            world=random_world(rng,family);initial=world;trace=[];learner.training_initials.add(key(world))
            for _ in range(steps):
                before=raw(world);probability=FieldPolicy(learner).probabilities(before);action=choose(probability,rng) if guided and rng.random()>.25 else rng.randrange(4)
                nxt=step(world,action);trace.append((before,action,raw(nxt)));world=nxt
                if succeeded(family,initial,world):
                    compact=erase_zero_effect_cycles(trace);signature,length=learner.observe_success(trace);runs.observe(signature,compact)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=length;events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,runs,dict(events)
