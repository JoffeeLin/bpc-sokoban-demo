#!/usr/bin/env python3
"""BPC v0.37: next-action probabilities conditioned on anonymous raw effects."""
import hashlib,pickle,random
from collections import Counter,defaultdict

from bpc_direct_composition_v09 import choose
from bpc_three_factor_v12 import FieldPolicy,ThreeFactorBPC,changed_planes,key,random_world,raw,step,succeeded


def compact_transitions(trace):
    """Cycle erasure that retains anonymous before/after observations."""
    states,actions=[trace[0][0]],[];location={states[0]:0}
    for _,action,after in trace:
        if after in location:
            index=location[after];states,actions=states[:index+1],actions[:index];location={state:i for i,state in enumerate(states)}
        else:actions.append(action);states.append(after);location[after]=len(states)-1
    return [(states[i],actions[i],states[i+1]) for i in range(len(actions))]


class EffectTransitions:
    def __init__(self):
        self.rows=defaultdict(lambda:defaultdict(lambda:[0]*4));self.event=defaultdict(lambda:defaultdict(lambda:[0]*4));self.action=defaultdict(lambda:[[0]*4 for _ in range(4)]);self.effects=set();self.writes=0
    def observe(self,signature,compact):
        for (before,previous,after),(_,nxt,_) in zip(compact,compact[1:]):
            effect=changed_planes(before,after);self.effects.add(effect);self.rows[signature][(previous,effect)][nxt]+=1;self.event[signature][effect][nxt]+=1;self.action[signature][previous][nxt]+=1;self.writes+=3
    def probabilities(self,signatures,previous,effect,mode='full',shuffle_effect=False,rotate_action=0,prior=.5):
        if shuffle_effect and self.effects:
            ordered=tuple(sorted(self.effects));effect=ordered[(ordered.index(effect)+1)%len(ordered)] if effect in ordered else effect
        counts=[0]*4
        for signature in signatures:
            if mode=='event':row=self.event.get(signature,{}).get(effect,(0,0,0,0))
            elif mode=='action':row=self.action.get(signature,[[0]*4 for _ in range(4)])[previous]
            elif mode=='erased':row=self.action.get(signature,[[0]*4 for _ in range(4)])[previous]
            else:row=self.rows.get(signature,{}).get((previous,effect),(0,0,0,0))
            for action,value in enumerate(row):counts[(action+rotate_action)%4]+=value
        total=sum(counts)
        if not total and mode=='full':return self.probabilities(signatures,previous,effect,'action',False,rotate_action,prior)
        return [(value+prior)/(total+4*prior) for value in counts] if total else None
    def digest(self):
        clean=lambda table:tuple((signature,tuple((key,tuple(value)) for key,value in sorted(rows.items(),key=lambda x:repr(x[0])))) for signature,rows in sorted(table.items()))
        value=(clean(self.rows),clean(self.event),tuple((signature,tuple(map(tuple,rows))) for signature,rows in sorted(self.action.items())))
        return hashlib.sha256(pickle.dumps(value,protocol=5)).hexdigest()


class EffectPolicy:
    def __init__(self,learner,effects,drop=(),mode='full',shuffle_effect=False,rotate_action=0,rotated=False):
        self.learner=learner;self.effects=effects;self.base=FieldPolicy(learner,rotated,drop);ordered=tuple(sorted(learner.factors));self.drop={ordered[i] for i in drop if 0<=i<len(ordered)}
        self.mode=mode;self.shuffle_effect=shuffle_effect;self.rotate_action=rotate_action;self.context=None
    def reset(self):self.context=None
    def probabilities(self,state):
        base=self.base.probabilities(state)
        if self.context is None:return base
        previous,effect,signatures=self.context;signatures=tuple(signature for signature in signatures if signature not in self.drop)
        if len(signatures)<2:return base
        transition=self.effects.probabilities(signatures,previous,effect,self.mode,self.shuffle_effect,self.rotate_action)
        if transition is None:return base
        values=[base[action]*transition[action] for action in range(4)];total=sum(values);return [value/total for value in values]
    def observed(self,before,action,after):self.context=(action,changed_planes(before,after),self.learner.active(before))


def train(seed,uniform_episodes=800,guided_rounds=2,guided_episodes=400,steps=120):
    rng=random.Random(seed);learner=ThreeFactorBPC();effects=EffectTransitions();events=Counter();schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect','open'):
        for guided in schedule:
            world=random_world(rng,family);initial=world;trace=[];learner.training_initials.add(key(world))
            for _ in range(steps):
                before=raw(world);probability=FieldPolicy(learner).probabilities(before);action=choose(probability,rng) if guided and rng.random()>.25 else rng.randrange(4)
                nxt=step(world,action);trace.append((before,action,raw(nxt)));world=nxt
                if succeeded(family,initial,world):
                    compact=compact_transitions(trace);signature,length=learner.observe_success(trace);effects.observe(signature,compact)
                    events[f'{family}_success']+=1;events[f'{family}_compact_steps']+=length;events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,effects,dict(events)
