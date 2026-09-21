#!/usr/bin/env python3
"""BPC v0.34: hierarchical action-suffix probabilities for factor composition."""
import hashlib,pickle,random
from collections import Counter,defaultdict

from bpc_direct_composition_v09 import choose
from bpc_three_factor_v12 import FieldPolicy,ThreeFactorBPC,key,random_world,raw,step,succeeded
from experiment_v5 import erase_zero_effect_cycles


class ActionSuffixes:
    def __init__(self,order=4):self.order=order;self.rows=defaultdict(lambda:defaultdict(lambda:[0]*4));self.writes=0
    def observe(self,signature,compact):
        actions=[action for _,action in compact]
        for index,action in enumerate(actions):
            for length in range(min(self.order,index)+1):
                self.rows[signature][tuple(actions[index-length:index])][action]+=1;self.writes+=1
    def probabilities(self,signatures,history,order=None,shuffle=0,prior=.5,backoff=4.):
        maximum=min(self.order if order is None else order,len(history));probability=[.25]*4
        for length in range(maximum+1):
            counts=[0]*4;context=tuple(history[-length:]) if length else ()
            for signature in signatures:
                for action,value in enumerate(self.rows.get(signature,{}).get(context,(0,0,0,0))):counts[(action+shuffle)%4]+=value
            total=sum(counts)
            if length==0:probability=[(value+prior)/(total+4*prior) for value in counts] if total else probability
            elif total:probability=[(counts[action]+backoff*probability[action])/(total+backoff) for action in range(4)]
        return probability
    def digest(self):
        value=tuple((signature,tuple((context,tuple(counts)) for context,counts in sorted(rows.items()))) for signature,rows in sorted(self.rows.items()))
        return hashlib.sha256(pickle.dumps(value,protocol=5)).hexdigest()


class SuffixPolicy:
    def __init__(self,learner,suffixes,drop=(),order=None,shuffle=0,composition_only=True,rotated=False):
        self.learner=learner;self.suffixes=suffixes;self.base=FieldPolicy(learner,rotated,drop);ordered=tuple(sorted(learner.factors));self.drop={ordered[i] for i in drop if 0<=i<len(ordered)}
        self.order=order;self.shuffle=shuffle;self.composition_only=composition_only;self.history=[]
    def reset(self):self.history=[]
    def probabilities(self,state):
        base=self.base.probabilities(state);active=tuple(signature for signature in self.learner.active(state) if signature not in self.drop)
        if not self.history or (self.composition_only and len(active)<2):return base
        temporal=self.suffixes.probabilities(active,self.history,self.order,self.shuffle);values=[base[action]*temporal[action] for action in range(4)];total=sum(values)
        return [value/total for value in values]
    def chose(self,action):self.history.append(action);self.history=self.history[-self.suffixes.order:]


def train(seed,uniform_episodes=800,guided_rounds=2,guided_episodes=400,steps=120):
    """Use the unchanged v0.12 experience schedule and successful compact traces."""
    rng=random.Random(seed);learner=ThreeFactorBPC();suffixes=ActionSuffixes();events=Counter();schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect','open'):
        for guided in schedule:
            world=random_world(rng,family);initial=world;trace=[];learner.training_initials.add(key(world))
            for _ in range(steps):
                before=raw(world);probability=FieldPolicy(learner).probabilities(before);action=choose(probability,rng) if guided and rng.random()>.25 else rng.randrange(4)
                nxt=step(world,action);trace.append((before,action,raw(nxt)));world=nxt
                if succeeded(family,initial,world):
                    compact=erase_zero_effect_cycles(trace);signature,length=learner.observe_success(trace);suffixes.observe(signature,compact)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=length;events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,suffixes,dict(events)
