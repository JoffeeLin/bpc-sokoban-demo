#!/usr/bin/env python3
"""Execute the pre-registered v0.10 anonymous factor-routing test."""
from __future__ import annotations

import hashlib,inspect,json,time
from pathlib import Path

from bpc_autofactor_v10 import AnonymousFactorBPC,evaluate,shortest_collect,shortest_push,train
from bpc_direct_composition_v09 import fixed_step,shortest
from bpc_cross_task_v07 import World

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v10_autofactor.json';HOLDOUT=ROOT/'holdout_v10.json'
OUT=ROOT/'artifacts'/'v10autofactor'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def total(rows,budget,name,key):return sum(row[budget][name].get(key,0) for row in rows)


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    assert sha(HOLDOUT)==protocol['holdout_sha256'];data=json.loads(HOLDOUT.read_text());suite=[]
    for row in data['worlds']:
        world=World(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks']);family=row['family']
        distance=shortest_push(world) if family=='push' else shortest_collect(world) if family=='collect' else shortest(world)
        assert distance==row['shortest']
        if family=='combined':assert shortest(world,True) is None
        suite.append((family,world,distance))
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter()
    learner,events=train(config['train_seed'],config['uniform_episodes'],config['guided_rounds'],config['guided_episodes'],config['train_steps'])
    assert events==protocol['expected_training_events'] and learner.digest()==protocol['expected_factor_digest']
    assert [list(x) for x in sorted(learner.factors)]==protocol['expected_signatures']
    holdout_keys={(w.h,w.w,w.walls,w.agent,w.objects,w.marks) for _,w,_ in suite}
    writes=learner.writes;holdouts={}
    for seed in config['eval_seeds']:
        by_budget={}
        for budget in config['step_budgets']:by_budget[str(budget)]=evaluate(learner,suite,seed,config['episodes_per_map'],budget)[0]
        holdouts[str(seed)]=by_budget
    rows=list(holdouts.values());short='32';long='160';episodes=len(suite)*config['episodes_per_map']*len(rows)
    combined_episodes=total(rows,short,'auto','combined_episodes');auto_combined=total(rows,short,'auto','combined_successes')
    shared_combined=total(rows,short,'shared','combined_successes');uniform_combined=total(rows,short,'uniform','combined_successes')
    auto_total=total(rows,short,'auto','successes');permuted_total=total(rows,short,'permuted','successes')
    auto_oracle_exact=all(row[budget]['auto']['successes']==row[budget]['oracle']['successes'] and
        all(row[budget]['auto'].get(f'{family}_successes',0)==row[budget]['oracle'].get(f'{family}_successes',0)
            for family in ('push','collect','combined')) for row in rows for budget in (short,long))
    requirements=learner.required_planes();common=learner.common_planes();source='\n'.join(inspect.getsource(x) for x in
        (AnonymousFactorBPC.observe_success,AnonymousFactorBPC.active,AnonymousFactorBPC.probabilities))
    forbidden=('push','collect','family','reward','score','loss','gradient','torch','tensorflow','sklearn')
    source_scan={word:word not in source for word in forbidden};routing_mismatches=total(rows,short,'auto','routing_mismatches')+total(rows,long,'auto','routing_mismatches')
    gate={'two_anonymous_factors_discovered':len(learner.factors)==2,
        'one_common_and_one_exclusive_plane_each':len(common)==1 and all(len(x)==1 for x in requirements.values()),
        'holdout_initials_disjoint_from_training':not holdout_keys&learner.training_initials,
        'auto_matches_task_name_oracle':auto_oracle_exact and routing_mismatches==0,
        'combined_rate_at_least_30pct':auto_combined/combined_episodes>=threshold['combined_rate'],
        'auto_beats_shared_by_8pp_on_joint':(auto_combined-shared_combined)/combined_episodes>=threshold['shared_margin'],
        'auto_beats_uniform_by_20pp_on_joint':(auto_combined-uniform_combined)/combined_episodes>=threshold['uniform_margin'],
        'auto_beats_permuted_by_15pp_overall':(auto_total-permuted_total)/episodes>=threshold['permuted_total_margin'],
        'anonymous_routing_source':all(source_scan.values()),'frozen_model_writes_zero':learner.writes==writes}
    result={'format':'bpc-autofactor-v10','evidence_level':'developer-frozen held-out synthetic direct control; not third-party blind',
        'question':protocol['question'],'training':events,'factor_digest':learner.digest(),
        'discovered_signatures':[list(x) for x in sorted(learner.factors)],
        'common_planes':sorted(common),'required_planes':{str(k):list(v) for k,v in requirements.items()},
        'holdout':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','combined')},
            'shortest_distances':[distance for _,_,distance in suite],'initial_overlap_with_training':len(holdout_keys&learner.training_initials)},
        'conditions':holdouts,'aggregate':{'episodes_per_condition_budget':episodes,'combined_episodes':combined_episodes,
            'auto_32_total':auto_total,'oracle_32_total':total(rows,short,'oracle','successes'),'all_32_total':total(rows,short,'all','successes'),
            'shared_32_total':total(rows,short,'shared','successes'),'permuted_32_total':permuted_total,'uniform_32_total':total(rows,short,'uniform','successes'),
            'auto_32_combined':auto_combined,'shared_32_combined':shared_combined,'uniform_32_combined':uniform_combined,
            'auto_160_total':total(rows,long,'auto','successes'),'oracle_160_total':total(rows,long,'oracle','successes'),
            'routing_decisions':total(rows,short,'auto','routing_decisions')+total(rows,long,'auto','routing_decisions'),
            'routing_mismatches':routing_mismatches},'source_scan':source_scan,'model_writes_during_evaluation':learner.writes-writes,
        'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,'protocol_sha256':sha(PROTOCOL),
        'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'A single BPC learner discovered two anonymous terminal co-change factors and, without receiving a task name, matched oracle factor activation on unseen single and joint direct-control tasks.',
        'boundary':'Equal probability multiplication, raw channelization, generators, binary terminal success events, and evaluation limits are supplied. Always activating all factors is a competitive control; this is not autonomous operator invention, arbitrary planning, or AGI.'}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
