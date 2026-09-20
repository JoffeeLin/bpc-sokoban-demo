#!/usr/bin/env python3
"""BPC v0.24 development: joint raw-effect emission probabilities."""
import hashlib,math,pickle,random
from collections import Counter

from bpc_cross_generator_v17 import done,lab_raw,lab_step,variable_expose
from bpc_direct_composition_v09 import choose
from bpc_hidden_mode_v21 import reverse_channel,sample,stationary,update_belief
from bpc_open_interface_v15 import canonicalize_subset
from bpc_spatial_interface_v18 import spatial_expose,spatial_restore
from bpc_stochastic_interface_v20 import effect_features
from bpc_three_factor_v12 import FieldPolicy


class JointEffectProfiles:
    """One categorical probability for the complete raw transition signature."""
    def __init__(self,actions=4,prior=.5):self.actions=actions;self.prior=prior;self.n=[0]*actions;self.rows=[Counter() for _ in range(actions)]
    def observe(self,before,action,after):self.n[action]+=1;self.rows[action][effect_features(before,after)]+=1
    def logs(self,before,after):
        value=effect_features(before,after);return tuple(math.log((row[value]+self.prior)/(self.n[action]+self.prior*(len(row)+1))) for action,row in enumerate(self.rows))
    def digest(self):return hashlib.sha256(pickle.dumps((self.actions,self.prior,tuple(self.n),tuple(tuple(sorted(x.items())) for x in self.rows)),protocol=5)).hexdigest()


def joint_profiles(triples):
    out=JointEffectProfiles()
    for before,action,after in triples:out.observe(before,action,after)
    return out


def advance(belief,transition):return tuple(sum(belief[i]*transition[i][j] for i in range(len(belief))) for j in range(len(belief)))


def evaluate_joint(learner,joint,factored,model,suite,sensors,kinds,spatial,delay,mapping,transform,
        environment_channels,oracle_channels,true_transition,true_initial,seed,episodes,steps):
    learned=model['channels'];shuffled=tuple(tuple(mode[(slot+1)%4] for slot in range(4)) for mode in learned);flat=stationary(model['transition'])
    conditions={'joint':(learned,model['transition'],flat,'online',delay,joint),'factored':(learned,model['transition'],flat,'online',delay,factored),
        'memoryless':(learned,model['transition'],flat,'fixed',delay,joint),'shuffled':(shuffled,model['transition'],flat,'online',delay,joint),
        'zero_lag':(learned,model['transition'],flat,'online',0,joint),'oracle':(oracle_channels,true_transition,true_initial,'oracle',delay,joint)}
    rows={name:Counter() for name in conditions};field=FieldPolicy(learner)
    restore=lambda value:spatial_restore(canonicalize_subset(value,mapping,len(sensors)),6,transform)
    observe=lambda world:spatial_expose(variable_expose(lab_raw(world),sensors,kinds,0),len(sensors),spatial)
    for index,(family,initial_world,_) in enumerate(suite):
        for episode in range(episodes):
            base=seed+index*100000+episode
            for name,(channels,transition,initial_belief,kind,assumed_lag,profiles) in conditions.items():
                action_rng=random.Random(base);effect_rng=random.Random(base+700000001);mode_rng=random.Random(base+800000003)
                world=initial_world;mode=sample(true_initial,mode_rng);belief=initial_belief;queue=[];issued=[]
                for t in range(steps):
                    old=restore(observe(world));controller=tuple(1. if i==mode else 0. for i in range(len(true_initial))) if kind=='oracle' else belief
                    slot=choose(reverse_channel(field.probabilities(old),controller,channels),action_rng);issued.append(slot);queue.append(slot)
                    if len(queue)>delay:world=lab_step(world,sample(environment_channels[mode][queue.pop(0)],effect_rng))
                    new=restore(observe(world));success=done(family,initial_world,world)
                    if success:break
                    if kind=='online' and t>=assumed_lag:_,belief=update_belief(belief,issued[t-assumed_lag],profiles.logs(old,new),transition,channels)
                    elif kind=='online':belief=advance(belief,transition)
                    mode=sample(true_transition[mode],mode_rng)
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
    return {name:dict(value) for name,value in rows.items()}
