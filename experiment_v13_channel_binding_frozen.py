#!/usr/bin/env python3
"""Execute the pre-registered v0.13 sensor-interface transfer once."""
import hashlib,inspect,json,random,time
from pathlib import Path

from bpc_channel_binding_v13 import BoundFieldPolicy,collect_interface,evaluate_permuted,infer_binding,inverse
from bpc_three_factor_v12 import ThreeFactorBPC,World3,key,shortest,train

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v13_channel_binding.json';HOLDOUT=ROOT/'holdout_v13.json'
OUT=ROOT/'artifacts'/'v13binding'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def total(rows,name,key):return sum(row[name].get(key,0) for row in rows)
def normalized(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second'])}


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    assert sha(HOLDOUT)==protocol['holdout_sha256'];data=json.loads(HOLDOUT.read_text());suite=[]
    for row in data['worlds']:
        world=World3(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates'])
        goal='collect' if row['family']=='joint' else row['family'];assert shortest(world,goal)==row['shortest']
        if row['family']=='joint':
            assert shortest(world,'collect',fixed_objects=True) is None and shortest(world,'collect',fixed_gates=True) is None
        suite.append((row['family'],world,row['shortest']))
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter()
    learner,events=train(config['train_seed']);assert events==protocol['expected_training_events'] and learner.digest()==protocol['expected_factor_digest']
    excluded=set(learner.training_initials);reference,initials=collect_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    assert reference.digest()==protocol['reference_digest'];excluded|=initials;interfaces=[]
    rng=random.Random(config['random_binding_seed'])
    for index,(seed,permutation,mix,expected) in enumerate(zip(config['target_seeds'],config['permutations'],config['target_mixtures'],protocol['expected_calibration'])):
        permutation=tuple(permutation);target,initials=collect_interface(seed,mix,config['calibration_steps'],permutation,excluded);excluded|=initials
        bindings={mode:infer_binding(reference,target,mode) for mode in ('transition','full','static','count')}
        assert target.digest()==expected['target_digest']
        for mode,row in bindings.items():assert normalized(row)==expected['bindings'][mode]
        oracle=inverse(permutation);assert list(oracle)==expected['oracle'];random_mapping=list(range(6));rng.shuffle(random_mapping)
        while tuple(random_mapping)==oracle:rng.shuffle(random_mapping)
        interfaces.append({'index':index,'permutation':permutation,'mix':mix,'target':target,'bindings':bindings,
            'oracle':oracle,'random':tuple(random_mapping)})
    holdout_keys={key(world) for _,world,_ in suite};assert not holdout_keys&excluded
    writes=learner.writes;digest=learner.digest();conditions={};trace_counts={}
    for interface in interfaces:
        policies={'learned':BoundFieldPolicy(learner,interface['bindings']['transition']['mapping']),
            'oracle':BoundFieldPolicy(learner,interface['oracle']),'identity':BoundFieldPolicy(learner,range(6)),
            'static':BoundFieldPolicy(learner,interface['bindings']['static']['mapping']),
            'count':BoundFieldPolicy(learner,interface['bindings']['count']['mapping']),
            'random':BoundFieldPolicy(learner,interface['random'])}
        by_seed={};by_trace={}
        for seed in config['eval_seeds']:
            result,traces=evaluate_permuted(policies,suite,interface['permutation'],seed,config['episodes_per_map'],config['step_budget'])
            by_seed[str(seed)]=result;by_trace[str(seed)]={name:len(row) for name,row in traces.items()}
        conditions[str(interface['index'])]=by_seed;trace_counts[str(interface['index'])]=by_trace
    rows=[row for interface in conditions.values() for row in interface.values()]
    joint_episodes=sum(x[0]=='joint' for x in suite)*config['episodes_per_map']*len(config['eval_seeds'])*len(interfaces)
    episodes=len(suite)*config['episodes_per_map']*len(config['eval_seeds'])*len(interfaces)
    learned_joint=total(rows,'learned','joint_successes');oracle_joint=total(rows,'oracle','joint_successes')
    identity_joint=total(rows,'identity','joint_successes');static_joint=total(rows,'static','joint_successes')
    count_joint=total(rows,'count','joint_successes');random_joint=total(rows,'random','joint_successes')
    exact=[tuple(x['bindings']['transition']['mapping'])==x['oracle'] for x in interfaces]
    static_exact=[tuple(x['bindings']['static']['mapping'])==x['oracle'] for x in interfaces]
    count_exact=[tuple(x['bindings']['count']['mapping'])==x['oracle'] for x in interfaces]
    source='\n'.join(inspect.getsource(x) for x in (__import__('bpc_channel_binding_v13').InterfaceStats.observe,
        __import__('bpc_channel_binding_v13').binding_log_probability,__import__('bpc_channel_binding_v13').infer_binding,
        __import__('bpc_channel_binding_v13').BoundFieldPolicy.probabilities))
    forbidden=('push','collect','open','family','goal','reward','score','loss','gradient','torch','tensorflow','sklearn','search','shortest')
    source_scan={word:word not in source.lower() for word in forbidden}
    oracle_exact=all(row['learned']==row['oracle'] for row in rows)
    gate={'four_unseen_permutations_recovered':all(exact),
        'binding_log_margin_at_least_100':all(x['bindings']['transition']['log_margin']>=threshold['minimum_binding_log_margin'] for x in interfaces),
        'static_and_count_controls_fail_under_shift':sum(static_exact)<=2 and sum(count_exact)<=2,
        'holdout_initials_disjoint_from_training_and_calibration':not holdout_keys&excluded,
        'learned_matches_oracle_every_condition':oracle_exact and learned_joint==oracle_joint,
        'learned_joint_rate_at_least_45pct':learned_joint/joint_episodes>=threshold['joint_rate'],
        'learned_beats_identity_by_35pp_on_joint':(learned_joint-identity_joint)/joint_episodes>=threshold['identity_joint_margin'],
        'learned_beats_random_by_25pp_on_joint':(learned_joint-random_joint)/joint_episodes>=threshold['random_joint_margin'],
        'learned_beats_static_by_8pp_on_joint':(learned_joint-static_joint)/joint_episodes>=threshold['static_joint_margin'],
        'learned_beats_count_by_8pp_on_joint':(learned_joint-count_joint)/joint_episodes>=threshold['count_joint_margin'],
        'anonymous_binding_source':all(source_scan.values()),'frozen_policy_and_model_writes_zero':learner.writes==writes and learner.digest()==digest}
    result={'format':'bpc-channel-binding-v13','evidence_level':'developer-frozen held-out synthetic sensor-interface transfer; not third-party blind',
        'question':protocol['question'],'training':events,'factor_digest':learner.digest(),
        'calibration':{'reference_digest':reference.digest(),'interfaces':[{'observed_to_canonical':list(x['permutation']),
            'target_mix':x['mix'],'target_digest':x['target'].digest(),'oracle':list(x['oracle']),'random':list(x['random']),
            'bindings':{mode:normalized(row) for mode,row in x['bindings'].items()}} for x in interfaces]},
        'holdout':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')},
            'initial_overlap_with_all_prior':len(holdout_keys&excluded)},'conditions':conditions,'worlds_with_success_trace':trace_counts,
        'aggregate':{'episodes_per_condition':episodes,'joint_episodes':joint_episodes,
            'learned_total':total(rows,'learned','successes'),'oracle_total':total(rows,'oracle','successes'),
            'identity_total':total(rows,'identity','successes'),'static_total':total(rows,'static','successes'),
            'count_total':total(rows,'count','successes'),'random_total':total(rows,'random','successes'),
            'learned_joint':learned_joint,'oracle_joint':oracle_joint,'identity_joint':identity_joint,
            'static_joint':static_joint,'count_joint':count_joint,'random_joint':random_joint},
        'source_scan':source_scan,'model_writes_during_evaluation':learner.writes-writes,'gate':gate,'adopted':all(gate.values()),
        'seconds':time.perf_counter()-started,'protocol_sha256':sha(PROTOCOL),'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'A frozen non-neural BPC controller used unlabeled transition probability fingerprints to recover four unseen six-channel sensor permutations under calibration-distribution shift and exactly preserve oracle-bound direct control on disjoint unseen worlds.',
        'boundary':protocol['boundary']}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
