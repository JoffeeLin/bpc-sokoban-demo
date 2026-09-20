#!/usr/bin/env python3
"""Development-only test of relational BPC direct control; no v5 holdout read."""
from __future__ import annotations

import json, pickle, random
from collections import defaultdict

import bpc_sokoban as base
from experiment_v5 import erase_zero_effect_cycles, generate_maps
from general_bpc_v7 import RelationalBPC, RelationalEncoder

MAPS, MAP_SEED = 50, 77_031
UNIFORM_EPISODES, GUIDED_ROUNDS, GUIDED_EPISODES = 300, 2, 100
EVAL_EPISODES, EVAL_SEED = 32, 73_911


def choose(p,rng):
    u=rng.random(); c=0.
    for a,x in enumerate(p):
        c+=x
        if u<=c:return a
    return 3


def episode(model,behavior,level,rng,guided,epsilon=.22):
    w,trace=base.World(level),[]
    while not w.terminal:
        raw=w.observation()
        action=(choose(behavior.probabilities(raw),rng) if guided and rng.random()>=epsilon else rng.randrange(4))
        before=raw; event=w.step(action); nxt=w.observation()
        model.observe_transition(before,action,event['changed'])
        behavior.observe_transition(before,action,event['changed'])
        trace.append((before,action,nxt))
    if w.success:
        compact=erase_zero_effect_cycles(trace)
        model.observe_success(compact); behavior.observe_success(compact)
    return int(w.success)


def train(levels):
    model=RelationalBPC(); behavior=RelationalBPC(RelationalEncoder(high_order=True))
    rng,summary=random.Random(7_000_007),defaultdict(int)
    for level in levels:
        for _ in range(UNIFORM_EPISODES): summary[f'{level+1}:uniform']+=episode(model,behavior,level,rng,False)
    for rd in range(GUIDED_ROUNDS):
        for level in levels:
            for _ in range(GUIDED_EPISODES): summary[f'{level+1}:guided{rd+1}']+=episode(model,behavior,level,rng,True)
    return model,dict(summary)


def evaluate(model,levels,rotated=False,uniform=False,change_fused=False,no_joint=False):
    m=model.rotated() if rotated else model; before=m.writes; out={}
    for level in levels:
        wins=0
        for ep in range(EVAL_EPISODES):
            rng=random.Random(EVAL_SEED+level*10000+ep); w=base.World(level)
            while not w.terminal:
                p=([.25]*4 if uniform else m.probabilities(
                    w.observation(),families={0,1,3} if no_joint else None,
                    use_change=change_fused))
                w.step(choose(p,rng))
            wins+=w.success
        out[f'D{level+1}']=wins
    assert m.writes==before
    return out


def main():
    base.MAX_STEPS=128; original=base.LEVEL_MAPS; maps=generate_maps(MAPS,MAP_SEED)
    base.LEVEL_MAPS=original+maps; base.OBS_CACHE.clear()
    training=list(base.TRAIN_LEVELS)+list(range(10,50)); dev=list(base.TEST_LEVELS)+list(range(50,60))
    model,experience=train(training)
    with open('/tmp/v7-dev-model.pkl','wb') as f: pickle.dump(model,f,protocol=5)
    result={'development_only':True,'experience':experience,'conditions':{
        'full':evaluate(model,dev),
        'change_fused':evaluate(model,dev,change_fused=True),
        'no_joint':evaluate(model,dev,no_joint=True),
        'rotated':evaluate(model,dev,True),'uniform':evaluate(model,dev,uniform=True)},
        'model_sha256':model.digest(),'writes':model.writes}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
