#!/usr/bin/env python3
"""Execute the pre-registered v0.12 three-factor held-out test once."""
import hashlib,inspect,json,time
from pathlib import Path

from bpc_three_factor_v12 import (FieldPolicy,ProductPolicy,SharedPolicy,ThreeFactorBPC,UniformPolicy,
    World3,evaluate,key,raw,shortest,train)

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v12_three_factor.json';HOLDOUT=ROOT/'holdout_v12.json'
OUT=ROOT/'artifacts'/'v12three'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def total(rows,budget,name,key):return sum(row[budget][name].get(key,0) for row in rows)


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    assert sha(HOLDOUT)==protocol['holdout_sha256'];data=json.loads(HOLDOUT.read_text());suite=[]
    for row in data['worlds']:
        world=World3(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates'])
        family=row['family'];goal='collect' if family=='joint' else family;distance=shortest(world,goal)
        assert distance==row['shortest']
        if family=='joint':
            assert shortest(world,'collect',fixed_objects=True) is None
            assert shortest(world,'collect',fixed_gates=True) is None
        suite.append((family,world,distance))
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter()
    learner,events=train(config['train_seed'],config['uniform_episodes'],config['guided_rounds'],config['guided_episodes'],config['train_steps'])
    assert events==protocol['expected_training_events'] and learner.digest()==protocol['expected_factor_digest']
    assert [list(x) for x in sorted(learner.factors)]==protocol['expected_signatures']
    policies={'field':FieldPolicy(learner),'product':ProductPolicy(learner),'shared':SharedPolicy(learner),
        'drop_0':FieldPolicy(learner,drop=(0,)),'drop_1':FieldPolicy(learner,drop=(1,)),
        'drop_2':FieldPolicy(learner,drop=(2,)),'rotated':FieldPolicy(learner,rotated=True),'uniform':UniformPolicy()}
    writes=learner.writes;holdouts={};trace_counts={}
    for seed in config['eval_seeds']:
        by_budget={};by_trace={}
        for budget in config['step_budgets']:
            result,traces=evaluate(policies,suite,seed,config['episodes_per_map'],budget)
            by_budget[str(budget)]=result;by_trace[str(budget)]={name:len(path) for name,path in traces.items()}
        holdouts[str(seed)]=by_budget;trace_counts[str(seed)]=by_trace
    rows=list(holdouts.values());short='64';long='256';episodes=len(suite)*config['episodes_per_map']*len(rows)
    joint_episodes=sum(x[0]=='joint' for x in suite)*config['episodes_per_map']*len(rows)
    field_joint=total(rows,short,'field','joint_successes');product_joint=total(rows,short,'product','joint_successes')
    shared_joint=total(rows,short,'shared','joint_successes');uniform_joint=total(rows,short,'uniform','joint_successes')
    rotated_joint=total(rows,short,'rotated','joint_successes');drop_joint=[total(rows,short,f'drop_{i}','joint_successes') for i in range(3)]
    requirements=learner.required_planes();common=learner.common_planes();holdout_keys={key(w) for _,w,_ in suite}
    source='\n'.join(inspect.getsource(x) for x in (ThreeFactorBPC.observe_success,ThreeFactorBPC.active,FieldPolicy.probabilities))
    forbidden=('push','collect','open','family','goal','reward','score','loss','gradient','torch','tensorflow','sklearn','search','shortest')
    source_scan={word:word not in source.lower() for word in forbidden}
    initial_active={family:sorted({len(learner.active(raw(world))) for f,world,_ in suite if f==family}) for family in ('push','collect','open','joint')}
    gate={'three_anonymous_factors_discovered':len(learner.factors)==3,
        'one_common_plane_and_requirements_1_1_2':len(common)==1 and sorted(map(len,requirements.values()))==[1,1,2],
        'holdout_initials_disjoint_from_training':not holdout_keys&learner.training_initials,
        'joint_worlds_require_object_and_gate_mechanisms':all(shortest(w,'collect',fixed_objects=True) is None and shortest(w,'collect',fixed_gates=True) is None for f,w,_ in suite if f=='joint'),
        'joint_initials_activate_three_factors':initial_active['joint']==[3],
        'field_joint_rate_at_least_45pct':field_joint/joint_episodes>=threshold['joint_rate'],
        'field_beats_shared_by_8pp_on_joint':(field_joint-shared_joint)/joint_episodes>=threshold['shared_joint_margin'],
        'each_factor_drop_costs_5pp_on_joint':all((field_joint-x)/joint_episodes>=threshold['each_drop_joint_margin'] for x in drop_joint),
        'field_beats_uniform_by_30pp_on_joint':(field_joint-uniform_joint)/joint_episodes>=threshold['uniform_joint_margin'],
        'field_beats_rotated_by_40pp_on_joint':(field_joint-rotated_joint)/joint_episodes>=threshold['rotated_joint_margin'],
        'field_within_1pp_of_explicit_product':abs(field_joint-product_joint)/joint_episodes<=threshold['product_absolute_gap'],
        'anonymous_runtime_source':all(source_scan.values()),'frozen_model_writes_zero':learner.writes==writes}
    result={'format':'bpc-three-factor-v12','evidence_level':'developer-frozen held-out synthetic direct control; not third-party blind',
        'question':protocol['question'],'training':events,'factor_digest':learner.digest(),
        'discovered_signatures':[list(x) for x in sorted(learner.factors)],'common_planes':sorted(common),
        'required_planes':{str(k):list(v) for k,v in requirements.items()},
        'holdout':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')},
            'shortest_distances':[distance for _,_,distance in suite],'initial_overlap_with_training':len(holdout_keys&learner.training_initials),
            'initial_active_factor_counts':initial_active},'conditions':holdouts,'worlds_with_success_trace':trace_counts,
        'aggregate':{'episodes_per_condition_budget':episodes,'joint_episodes':joint_episodes,
            'field_64_total':total(rows,short,'field','successes'),'field_64_joint':field_joint,
            'product_64_joint':product_joint,'shared_64_joint':shared_joint,'drop_64_joint':drop_joint,
            'rotated_64_joint':rotated_joint,'uniform_64_joint':uniform_joint,
            'field_256_joint':total(rows,long,'field','joint_successes'),'product_256_joint':total(rows,long,'product','joint_successes')},
        'source_scan':source_scan,'model_writes_during_evaluation':learner.writes-writes,'gate':gate,'adopted':all(gate.values()),
        'seconds':time.perf_counter()-started,'protocol_sha256':sha(PROTOCOL),'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'One non-neural BPC learner discovered three anonymous raw-change factors from separate successful experience and directly recombined their learned evidence on unseen worlds requiring all three mechanisms.',
        'boundary':'Raw channels, generators, binary terminal events, additive field rule, and evaluation limits are supplied. The near-equivalent explicit product is a same-information control. This is synthetic direct control, not autonomous operator invention, arbitrary planning, or AGI.'}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
