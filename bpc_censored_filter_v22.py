#!/usr/bin/env python3
"""BPC v0.22 development: censor non-identifiable no-change emissions."""
import random
from collections import Counter

from bpc_cross_generator_v17 import done,lab_raw,lab_step,variable_expose
from bpc_direct_composition_v09 import choose
from bpc_hidden_mode_v21 import reverse_channel,sample,stationary,update_belief
from bpc_open_interface_v15 import canonicalize_subset
from bpc_spatial_interface_v18 import spatial_expose,spatial_restore
from bpc_three_factor_v12 import FieldPolicy


def advance(belief,transition):return tuple(sum(belief[i]*transition[i][j] for i in range(len(belief))) for j in range(len(belief)))


def censored_update(belief,slot,before,after,profiles,transition,channels):
    """No canonical change carries no mode identity, but time still advances."""
    if before==after:return belief,advance(belief,transition)
    return update_belief(belief,slot,profiles.logs(before,after),transition,channels)


def evaluate_censored(learner,profiles,model,suite,sensors,kinds,spatial,delay,mapping,transform,
        environment_channels,oracle_channels,true_transition,true_initial,seed,episodes,steps):
    learned=model['channels'];shuffled=tuple(tuple(mode[(slot+1)%4] for slot in range(4)) for mode in learned);flat=stationary(model['transition'])
    conditions={'censored':(learned,model['transition'],flat,'censored',delay),'original':(learned,model['transition'],flat,'original',delay),
        'memoryless':(learned,model['transition'],flat,'fixed',delay),'shuffled':(shuffled,model['transition'],flat,'censored',delay),
        'zero_lag':(learned,model['transition'],flat,'censored',0),'oracle':(oracle_channels,true_transition,true_initial,'oracle',delay)}
    rows={name:Counter() for name in conditions};field=FieldPolicy(learner)
    restore=lambda value:spatial_restore(canonicalize_subset(value,mapping,len(sensors)),6,transform)
    observe=lambda world:spatial_expose(variable_expose(lab_raw(world),sensors,kinds,0),len(sensors),spatial)
    for index,(family,initial_world,_) in enumerate(suite):
        for episode in range(episodes):
            base=seed+index*100000+episode
            for name,(channels,transition,initial_belief,kind,assumed_lag) in conditions.items():
                action_rng=random.Random(base);effect_rng=random.Random(base+700000001);mode_rng=random.Random(base+800000003)
                world=initial_world;mode=sample(true_initial,mode_rng);belief=initial_belief;queue=[];issued=[]
                for t in range(steps):
                    before=observe(world);old=restore(before);controller=tuple(1. if i==mode else 0. for i in range(len(true_initial))) if kind=='oracle' else belief
                    slot=choose(reverse_channel(field.probabilities(old),controller,channels),action_rng);issued.append(slot);queue.append(slot)
                    if len(queue)>delay:world=lab_step(world,sample(environment_channels[mode][queue.pop(0)],effect_rng))
                    new=restore(observe(world));success=done(family,initial_world,world)
                    if success:break
                    if kind in ('censored','original') and t>=assumed_lag:
                        if kind=='censored':_,belief=censored_update(belief,issued[t-assumed_lag],old,new,profiles,transition,channels)
                        else:_,belief=update_belief(belief,issued[t-assumed_lag],profiles.logs(old,new),transition,channels)
                    elif kind in ('censored','original'):belief=advance(belief,transition)
                    mode=sample(true_transition[mode],mode_rng)
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
    return {name:dict(value) for name,value in rows.items()}
