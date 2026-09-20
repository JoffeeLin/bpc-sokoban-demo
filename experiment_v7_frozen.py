#!/usr/bin/env python3
"""Execute the pre-registered GeneralBPC v7 Sokoban holdout once."""
from __future__ import annotations

import hashlib, json, pickle, random
from collections import defaultdict
from pathlib import Path

import bpc_sokoban as game
from experiment_v5 import erase_zero_effect_cycles
from general_bpc_v7 import RelationalBPC, RelationalEncoder
from sokoban_maps import digest, generate, max_wall_jaccard, solution_distance

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'artifacts'/'v7'
PROTOCOL=ROOT/'protocol_v7.json'; HOLDOUT=ROOT/'holdout_v7.json'


def choose(probability,rng):
    threshold=rng.random(); cumulative=0.
    for action,value in enumerate(probability):
        cumulative+=value
        if threshold<=cumulative: return action
    return 3


def train(levels,config):
    model=RelationalBPC(); behavior=RelationalBPC(RelationalEncoder(high_order=True))
    rng=random.Random(config['training_action_seed']); summary=defaultdict(int)
    for level in levels:
        for _ in range(config['uniform_episodes_per_map']):
            summary[f'{level+1}:uniform']+=experience_episode(model,behavior,level,rng,False,config)
    for round_index in range(config['guided_rounds']):
        for level in levels:
            for _ in range(config['guided_episodes_per_map']):
                summary[f'{level+1}:guided{round_index+1}']+=experience_episode(model,behavior,level,rng,True,config)
    return model,dict(summary)


def experience_episode(model,behavior,level,rng,guided,config):
    world=game.World(level); trace=[]
    while not world.terminal:
        raw=world.observation()
        action=(choose(behavior.probabilities(raw,config['temperature']),rng)
                if guided and rng.random()>=config['guided_epsilon'] else rng.randrange(4))
        event=world.step(action); next_raw=world.observation()
        model.observe_transition(raw,action,event['changed'])
        behavior.observe_transition(raw,action,event['changed']); trace.append((raw,action,next_raw))
    if world.success:
        compact=erase_zero_effect_cycles(trace)
        model.observe_success(compact); behavior.observe_success(compact)
    return int(world.success)


def evaluate(model,levels,condition,config,capture=False):
    controlled=model.rotated() if condition=='action_rotated' else model
    before=controlled.writes; successes={}; first_success={}; traces={}
    families={0,1,3} if condition=='no_joint' else None
    for local_index,level in enumerate(levels):
        wins=0
        for episode in range(config['evaluation_episodes_per_map']):
            rng=random.Random(config['evaluation_seed']+local_index*10_000+episode)
            world=game.World(level); frames=[]
            while not world.terminal:
                raw=world.observation()
                before_player,before_box=world.player,world.box
                if condition=='uniform':
                    decision={'choice':[.25]*4,'change':[.5]*4,'confidence':0.}
                else:
                    decision=controlled.decision(raw,config['temperature'],families,
                                                 use_change=condition=='change_fused')
                action=choose(decision['choice'],rng); event=world.step(action)
                if capture:
                    frames.append({'action':action,'choice':decision['choice'],
                        'change_probability':decision['change'],'confidence':decision['confidence'],
                        'player':before_player,'box':before_box,
                        'after_player':world.player,'after_box':world.box,'changed':event['changed'],
                        'pushed':event['pushed'],'success':event['success']})
            if world.success:
                wins+=1
                if capture and str(local_index+1) not in traces:
                    first_success[str(local_index+1)]=episode
                    traces[str(local_index+1)]=frames
        successes[f'H{local_index+1}']=wins
    assert controlled.writes==before, 'evaluation wrote learned state'
    return successes,first_success,traces


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol=json.loads(PROTOCOL.read_text()); config=protocol['config']
    for name,expected in protocol['source_sha256'].items():
        assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    holdout=tuple(tuple(row for row in level) for level in json.loads(HOLDOUT.read_text()))
    training=generate(config['training_map_count'],config['training_map_seed'],(4,16),(5,13),.55)
    assert digest(training)==protocol['training_maps_sha256']
    assert digest(holdout)==protocol['holdout_maps_sha256']
    assert not set(training)&set(holdout)
    original=game.LEVEL_MAPS; game.LEVEL_MAPS=original+training+holdout; game.OBS_CACHE.clear()
    game.MAX_STEPS=config['training_max_steps']
    training_levels=list(game.TRAIN_LEVELS)+list(range(10,10+len(training)))
    model,experience=train(training_levels,config)
    game.MAX_STEPS=config['evaluation_max_steps']
    holdout_start=10+len(training); levels=list(range(holdout_start,holdout_start+len(holdout)))
    conditions={}; first_success={}; traces={}; writes_before=model.writes
    for condition in ('primary','no_joint','change_fused','action_rotated','uniform'):
        values,seeds,record=evaluate(model,levels,condition,config,capture=condition=='primary')
        conditions[condition]=values
        if condition=='primary': first_success,traces=seeds,record
    assert model.writes==writes_before
    episodes=len(holdout)*config['evaluation_episodes_per_map']
    total={name:sum(values.values()) for name,values in conditions.items()}
    threshold=protocol['adoption_thresholds']; primary=conditions['primary']
    gate={
        'aggregate_rate_at_least_30pct':total['primary']/episodes>=threshold['aggregate_rate'],
        'every_map_rate_at_least_1pct':all(x/config['evaluation_episodes_per_map']>=threshold['every_map_rate'] for x in primary.values()),
        'beats_uniform_by_20pp':(total['primary']-total['uniform'])/episodes>=threshold['uniform_margin'],
        'beats_action_rotated_by_20pp':(total['primary']-total['action_rotated'])/episodes>=threshold['rotated_margin'],
        'joint_gain_at_least_10pp':(total['primary']-total['no_joint'])/episodes>=threshold['joint_margin'],
        'frozen_persistent_writes_zero':model.writes-writes_before==0,
        'all_ten_have_recorded_success':len(traces)==len(holdout),
    }
    result={
        'format':'general-bpc-sokoban-v7','evidence_level':'developer-frozen local holdout; not third-party blind',
        'input':'raw 9x9x6 binary voxels plus four anonymous external action indices',
        'model':'translation-shared exact Dirichlet/Beta relation cubes; sampled four-way Choice',
        'jev_influence':'typed Choice probabilities and an independent Noul-like raw-change probability; Jev architecture/API not used',
        'no_neural_network':True,'no_runtime_planner_or_search':True,
        'offline_solver_use':'solvability and shortest-distance filter only; no solution action enters experience or model',
        'training':{'map_count':len(training)+len(game.TRAIN_LEVELS),'experience':experience,
                    'maps_sha256':digest(training),'successes':sum(experience.values())},
        'holdout':{'map_count':len(holdout),'maps_sha256':digest(holdout),
                   'shortest_distances':[solution_distance(x) for x in holdout],
                   'max_internal_wall_jaccard':max_wall_jaccard(holdout),
                   'max_train_holdout_wall_jaccard':max_wall_jaccard(training,holdout)},
        'conditions':conditions,'totals':total,'episodes_per_condition':episodes,
        'primary':{'successes':total['primary'],'episodes':episodes,'rate':total['primary']/episodes},
        'first_success_episode_zero_based':first_success,'gate':gate,'adopted':all(gate.values()),
        'frozen_persistent_writes':model.writes-writes_before,'model_sha256':model.digest(),
        'protocol_sha256':sha(PROTOCOL),'source_sha256':protocol['source_sha256'],
        'boundary':'Tests limited cross-layout transfer inside a 9x9 single-box distribution; not arbitrary Sokoban, Jev reproduction, or AGI.'}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'traces.json').write_text(json.dumps(traces,separators=(',',':'))+'\n')
    model.encoder.cache.clear()
    with (OUT/'model.pkl').open('wb') as file: pickle.dump(model,file,protocol=5)
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
