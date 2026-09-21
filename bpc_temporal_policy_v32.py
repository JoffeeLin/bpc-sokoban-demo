#!/usr/bin/env python3
"""BPC v0.32: factor-conditioned action transitions from successful traces."""
import hashlib,pickle,random
from collections import Counter,defaultdict

from bpc_direct_composition_v09 import choose
from bpc_three_factor_v12 import FieldPolicy,ThreeFactorBPC,changed_planes,key,random_world,raw,step,succeeded
from experiment_v5 import erase_zero_effect_cycles


class ActionTransitions:
    def __init__(self):self.rows=defaultdict(lambda:[[0]*4 for _ in range(4)]);self.order0=defaultdict(lambda:[0]*4);self.writes=0
    def observe(self,signature,compact):
        actions=[action for _,action in compact]
        for action in actions:self.order0[signature][action]+=1;self.writes+=1
        for previous,action in zip(actions,actions[1:]):self.rows[signature][previous][action]+=1;self.writes+=1
    def probabilities(self,signatures,previous,shuffle=0,order0=False,prior=.5):
        counts=[0]*4
        for signature in signatures:
            row=self.order0.get(signature,[0]*4) if order0 else self.rows.get(signature,[[0]*4 for _ in range(4)])[previous]
            for action,value in enumerate(row):counts[(action+shuffle)%4]+=value
        total=sum(counts);return tuple((value+prior)/(total+4*prior) for value in counts) if total else None
    def digest(self):
        value=(tuple((key,tuple(map(tuple,value))) for key,value in sorted(self.rows.items())),tuple((key,tuple(value)) for key,value in sorted(self.order0.items())))
        return hashlib.sha256(pickle.dumps(value,protocol=5)).hexdigest()


class TemporalPolicy:
    def __init__(self,learner,temporal,drop=(),shuffle=0,order0=False,rotated=False):
        self.learner=learner;self.temporal=temporal;self.base=FieldPolicy(learner,rotated,drop);ordered=tuple(sorted(learner.factors));self.drop={ordered[i] for i in drop if 0<=i<len(ordered)}
        self.shuffle=shuffle;self.order0=order0;self.previous=None
    def reset(self):self.previous=None
    def probabilities(self,state):
        base=self.base.probabilities(state);active=tuple(key for key in self.learner.active(state) if key not in self.drop)
        if self.previous is None:return base
        transition=self.temporal.probabilities(active,self.previous,self.shuffle,self.order0)
        if transition is None:return base
        values=[base[action]*transition[action] for action in range(4)];total=sum(values);return [value/total for value in values]
    def chose(self,action):self.previous=action


def train(seed,uniform_episodes=800,guided_rounds=2,guided_episodes=400,steps=120):
    """Exact v0.12 experience schedule, with an extra read of compact action pairs."""
    rng=random.Random(seed);learner=ThreeFactorBPC();temporal=ActionTransitions();events=Counter();schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect','open'):
        for guided in schedule:
            world=random_world(rng,family);initial=world;trace=[];learner.training_initials.add(key(world))
            for _ in range(steps):
                before=raw(world);probability=FieldPolicy(learner).probabilities(before);action=choose(probability,rng) if guided and rng.random()>.25 else rng.randrange(4)
                nxt=step(world,action);trace.append((before,action,raw(nxt)));world=nxt
                if succeeded(family,initial,world):
                    compact=erase_zero_effect_cycles(trace);signature,length=learner.observe_success(trace);temporal.observe(signature,compact)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=length;events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,temporal,dict(events)
