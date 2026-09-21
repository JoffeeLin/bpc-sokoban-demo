#!/usr/bin/env python3
"""BPC v0.40: recursively update an anonymous factor probability state."""
import hashlib,pickle,random
from collections import Counter,defaultdict

from bpc_direct_composition_v09 import choose
from bpc_effect_transition_v37 import compact_transitions
from bpc_event_boundary_v38 import EventBoundary
from bpc_temporal_policy_v32 import ActionTransitions
from bpc_three_factor_v12 import FieldPolicy,ThreeFactorBPC,changed_planes,key,random_world,raw,step,succeeded


def norm(values,n=4):
    total=sum(values);return [value/total for value in values] if total else [1/n]*n


class FactorEmissions:
    """Dirichlet P(raw changed-plane tuple | anonymous factor, action)."""
    def __init__(self):self.rows=defaultdict(lambda:defaultdict(Counter));self.effects=set();self.writes=0
    def observe(self,signature,trace):
        for before,action,after in trace:
            effect=changed_planes(before,after);self.rows[signature][action][effect]+=1;self.effects.add(effect);self.writes+=1
    def probability(self,signature,action,effect,paired=None,prior=.5):
        row=self.rows.get(paired or signature,{}).get(action,{});total=sum(row.values());k=len(self.effects)+1
        return (row.get(effect,0)+prior)/(total+prior*k) if total else 1/k
    def digest(self):
        value=tuple((signature,tuple((action,tuple(sorted(row.items()))) for action,row in sorted(rows.items()))) for signature,rows in sorted(self.rows.items()))
        return hashlib.sha256(pickle.dumps(value,protocol=5)).hexdigest()


class RecursiveBeliefPolicy:
    """Direct policy whose factor mixture is a recursively updated posterior."""
    def __init__(self,learner,temporal,boundary,emissions,drop=(),use_action=True,use_effect=True,use_boundary=True,memoryless=False,shuffle_emission=0,hard=False,rotated=False):
        self.learner=learner;self.temporal=temporal;self.boundary=boundary;self.emissions=emissions;self.base=FieldPolicy(learner,rotated,drop);self.ordered=tuple(sorted(learner.factors));self.drop={self.ordered[i] for i in drop if 0<=i<len(self.ordered)}
        self.use_action=use_action;self.use_effect=use_effect;self.use_boundary=use_boundary;self.memoryless=memoryless;self.shuffle_emission=shuffle_emission;self.hard=hard;self.reset()
    def reset(self):self.previous=None;self.belief={};self.experts={};self.visible=()
    def _active(self,state):return tuple(signature for signature in self.learner.active(state) if signature not in self.drop)
    def _masked(self,active,values=None):
        values=self.belief if values is None else values;return dict(zip(active,norm([values.get(signature,0) for signature in active],len(active)))) if active else {}
    def probabilities(self,state):
        active=self._active(state);self.belief=self._masked(active,{} if self.memoryless else None);self.visible=active
        if not active:return [.25]*4
        self.experts={}
        for signature in active:
            spatial=self.base.sources[signature].probabilities(state);time=self.temporal.probabilities((signature,),self.previous) if self.previous is not None else None
            self.experts[signature]=norm([spatial[a]*time[a] for a in range(4)]) if time else spatial
        weights=self.belief
        if self.hard:
            chosen=max(active,key=lambda signature:(weights[signature],signature));weights={signature:float(signature==chosen) for signature in active}
        marginal=[sum(weights[signature]*self.experts[signature][action] for signature in active) for action in range(4)]
        base=self.base.probabilities(state);return norm([base[action]*marginal[action] for action in range(4)])
    def chose(self,action):
        if self.use_action and self.visible:self.belief=self._masked(self.visible,{signature:self.belief[signature]*self.experts[signature][action] for signature in self.visible})
        self.previous=action
    def observed(self,before,action,after):
        active_before=tuple(signature for signature in self.visible if signature not in self.drop);effect=changed_planes(before,after)
        if self.use_effect and active_before:
            values={}
            for signature in active_before:
                index=self.ordered.index(signature);paired=self.ordered[(index+self.shuffle_emission)%len(self.ordered)]
                values[signature]=self.belief[signature]*self.emissions.probability(signature,action,effect,paired)
            self.belief=self._masked(active_before,values)
        continuation=sum(self.belief.get(signature,0)*self.boundary.probability((signature,),effect) for signature in active_before) if self.use_boundary else 1.
        active_after=self._active(after);posterior=self._masked(active_after);uniform=self._masked(active_after,{})
        self.belief={signature:continuation*posterior[signature]+(1-continuation)*uniform[signature] for signature in active_after}


def train(seed,uniform_episodes=800,guided_rounds=2,guided_episodes=400,steps=120):
    """Keep the v0.12 worlds/actions; only read more anonymous probabilities."""
    rng=random.Random(seed);learner=ThreeFactorBPC();temporal=ActionTransitions();boundary=EventBoundary();emissions=FactorEmissions();events=Counter();schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect','open'):
        for guided in schedule:
            world=random_world(rng,family);initial=world;trace=[];learner.training_initials.add(key(world))
            for _ in range(steps):
                before=raw(world);probability=FieldPolicy(learner).probabilities(before);action=choose(probability,rng) if guided and rng.random()>.25 else rng.randrange(4)
                nxt=step(world,action);trace.append((before,action,raw(nxt)));world=nxt
                if succeeded(family,initial,world):
                    compact=compact_transitions(trace);signature,length=learner.observe_success(trace);temporal.observe(signature,[(state,old_action) for state,old_action,_ in compact]);boundary.observe(signature,compact);emissions.observe(signature,trace)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=length;events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,temporal,boundary,emissions,dict(events)
