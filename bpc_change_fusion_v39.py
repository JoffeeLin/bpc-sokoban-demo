#!/usr/bin/env python3
"""BPC v0.39: compose direct control with factor-specific raw-change Betas."""
import random
from collections import Counter

from bpc_direct_composition_v09 import choose
from bpc_effect_transition_v37 import compact_transitions
from bpc_event_boundary_v38 import BoundaryPolicy,EventBoundary,norm
from bpc_temporal_policy_v32 import ActionTransitions
from bpc_three_factor_v12 import FieldPolicy,ThreeFactorBPC,key,random_world,raw,step,succeeded


class ChangeFusionPolicy:
    def __init__(self,learner,temporal,boundary,drop=(),mode='factor',power=1.,rotate_change=0,rotated=False):
        self.learner=learner;self.inner=BoundaryPolicy(learner,temporal,boundary,drop=drop,rotated=rotated);ordered=tuple(sorted(learner.factors));self.drop={ordered[i] for i in drop if 0<=i<len(ordered)}
        self.mode=mode;self.power=power;self.rotate_change=rotate_change
    def reset(self):self.inner.reset()
    def probabilities(self,state):
        base=self.inner.probabilities(state);active=tuple(signature for signature in self.learner.active(state) if signature not in self.drop)
        if not active or self.mode=='none':return base
        if self.mode=='shared':change=self.learner.shared.change_probabilities(state)
        else:
            rows=[]
            for signature in active:
                cube=self.learner.factors[signature]
                if self.mode=='global':
                    row=[]
                    for action in range(4):
                        no,yes=cube.change_prior[action];row.append((yes+1)/(no+yes+2))
                    rows.append(row)
                else:rows.append(cube.change_probabilities(state))
            change=[sum(row[action] for row in rows)/len(rows) for action in range(4)]
        change=change[-self.rotate_change:]+change[:-self.rotate_change] if self.rotate_change else change
        if self.mode=='change_only':return norm(change)
        return norm([base[action]*(change[action]**self.power) for action in range(4)])
    def observed(self,before,action,after):self.inner.observed(before,action,after)


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
                    factor=learner.factors[signature]
                    for state,old_action,after in trace:
                        changed=state!=after;factor.observe_transition(state,old_action,changed);learner.shared.observe_transition(state,old_action,changed)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=length;events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,temporal,boundary,dict(events)


def transition_writes(learner):return sum(cube.writes for cube in learner.factors.values())+learner.shared.writes
