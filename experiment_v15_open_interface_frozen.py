#!/usr/bin/env python3
"""Execute the pre-registered v0.15 open-interface transfer once."""
import hashlib,inspect,json,random,re,time
from pathlib import Path

from bpc_open_interface_v15 import (OpenActionStats,OpenBoundPolicy,OpenInterfaceStats,action_stats,
    collect_open_interface,evaluate_open,infer_action_subset,infer_sensor_subset,inverse_subset)
from bpc_three_factor_v12 import World3,key,shortest,train

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v15_open_interface.json';HOLDOUT=ROOT/'holdout_v15.json';OUT=ROOT/'artifacts'/'v15open'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def total(rows,name,key):return sum(row[name].get(key,0) for row in rows)
def norm(row):
    return {**row,'mapping':list(row['mapping']),'second':list(row['second']),
        **({'candidate_slots':list(row['candidate_slots'])} if 'candidate_slots' in row else {})}


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    assert sha(HOLDOUT)==protocol['holdout_sha256'];suite=[]
    for row in json.loads(HOLDOUT.read_text())['worlds']:
        world=World3(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates'])
        goal='collect' if row['family']=='joint' else row['family'];assert shortest(world,goal)==row['shortest']
        if row['family']=='joint':assert shortest(world,'collect',fixed_objects=True) is None and shortest(world,'collect',fixed_gates=True) is None
        suite.append((row['family'],world,row['shortest']))
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter();learner,events=train(config['train_seed'])
    assert events==protocol['expected_training_events'] and learner.digest()==protocol['expected_factor_digest'];excluded=set(learner.training_initials)
    reference,triples,initials=collect_open_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;reference_actions=action_stats(triples,range(6),6,4)
    assert reference.digest()==protocol['reference_interface_digest'] and reference_actions.digest()==protocol['reference_action_digest'];interfaces=[]
    for index,(seed,sensor,actuator,mix,expected) in enumerate(zip(config['target_seeds'],config['sensor_routes'],config['actuator_routes'],config['target_mixtures'],protocol['expected_calibration'])):
        sensor=tuple(sensor);actuator=tuple(actuator);target,triples,initials=collect_open_interface(seed,mix,config['calibration_steps'],sensor,actuator,excluded);excluded|=initials
        channel=infer_sensor_subset(reference,target);target_actions=action_stats(triples,channel['mapping'],len(sensor),len(actuator));action=infer_action_subset(reference_actions,target_actions)
        assert target.digest()==expected['target_interface_digest'] and target_actions.digest()==expected['target_action_digest']
        assert norm(channel)==expected['channel_binding'] and norm(action)==expected['action_binding']
        assert list(inverse_subset(sensor,6))==expected['channel_oracle'] and list(inverse_subset(actuator,4))==expected['action_oracle']
        interfaces.append({'index':index,'sensor':sensor,'actuator':actuator,'mix':mix,'channel':channel,'action':action,
            'channel_oracle':inverse_subset(sensor,6),'action_oracle':inverse_subset(actuator,4)})
    holdout_keys={key(world) for _,world,_ in suite};assert not holdout_keys&excluded
    writes=learner.writes;digest=learner.digest();conditions={};trace_counts={};rng=random.Random(config['random_binding_seed'])
    for interface in interfaces:
        random_channels=rng.sample(range(len(interface['sensor'])),6);random_actions=rng.sample(range(len(interface['actuator'])),4)
        policies={'learned':OpenBoundPolicy(learner,interface['channel']['mapping'],len(interface['sensor']),interface['action']['mapping'],len(interface['actuator'])),
            'oracle':OpenBoundPolicy(learner,interface['channel_oracle'],len(interface['sensor']),interface['action_oracle'],len(interface['actuator'])),
            'sensor_only':OpenBoundPolicy(learner,interface['channel']['mapping'],len(interface['sensor']),range(4),len(interface['actuator'])),
            'action_only':OpenBoundPolicy(learner,range(6),len(interface['sensor']),interface['action']['mapping'],len(interface['actuator'])),
            'identity':OpenBoundPolicy(learner,range(6),len(interface['sensor']),range(4),len(interface['actuator'])),
            'random':OpenBoundPolicy(learner,random_channels,len(interface['sensor']),random_actions,len(interface['actuator']))}
        by_seed={};by_trace={}
        for seed in config['eval_seeds']:
            result,traces=evaluate_open(policies,suite,interface['sensor'],interface['actuator'],seed,config['episodes_per_map'],config['step_budget'])
            by_seed[str(seed)]=result;by_trace[str(seed)]={name:len(row) for name,row in traces.items()}
        interface['random_channels']=tuple(random_channels);interface['random_actions']=tuple(random_actions)
        conditions[str(interface['index'])]=by_seed;trace_counts[str(interface['index'])]=by_trace
    rows=[row for interface in conditions.values() for row in interface.values()]
    joint_episodes=sum(x[0]=='joint' for x in suite)*config['episodes_per_map']*len(config['eval_seeds'])*len(interfaces)
    episodes=len(suite)*config['episodes_per_map']*len(config['eval_seeds'])*len(interfaces)
    joint={name:total(rows,name,'joint_successes') for name in ('learned','oracle','sensor_only','action_only','identity','random')}
    oracle_exact=all(row['learned']==row['oracle'] for row in rows)
    source='\n'.join(inspect.getsource(x) for x in (OpenInterfaceStats.observe,__import__('bpc_open_interface_v15').sensor_log_probability,
        infer_sensor_subset,OpenActionStats.observe,__import__('bpc_open_interface_v15').action_log_probability,
        infer_action_subset,OpenBoundPolicy.probabilities))
    forbidden=('push','collect','open','family','goal','reward','score','loss','gradient','torch','tensorflow','sklearn','search','shortest',
        'north','south','east','west','up','down','left','right')
    source_scan={word:re.search(rf'\b{word}\b',source.lower()) is None for word in forbidden}
    gate={'four_unseen_sensor_subsets_recovered':all(tuple(x['channel']['mapping'])==x['channel_oracle'] for x in interfaces),
        'four_unseen_actuator_subsets_recovered':all(tuple(x['action']['mapping'])==x['action_oracle'] for x in interfaces),
        'all_permanent_zero_effect_slots_rejected':all(set(x['action']['candidate_slots'])==set(x['action_oracle']) for x in interfaces),
        'sensor_log_margin_at_least_500':all(x['channel']['log_margin']>=threshold['sensor_log_margin'] for x in interfaces),
        'action_log_margin_at_least_5000':all(x['action']['log_margin']>=threshold['action_log_margin'] for x in interfaces),
        'holdout_initials_disjoint_from_training_and_calibration':not holdout_keys&excluded,
        'learned_matches_oracle_every_condition':oracle_exact and joint['learned']==joint['oracle'],
        'learned_joint_rate_at_least_45pct':joint['learned']/joint_episodes>=threshold['joint_rate'],
        'both_subsets_beat_sensor_only_by_45pp':(joint['learned']-joint['sensor_only'])/joint_episodes>=threshold['sensor_only_joint_margin'],
        'both_subsets_beat_action_only_by_40pp':(joint['learned']-joint['action_only'])/joint_episodes>=threshold['action_only_joint_margin'],
        'both_subsets_beat_identity_by_40pp':(joint['learned']-joint['identity'])/joint_episodes>=threshold['identity_joint_margin'],
        'both_subsets_beat_random_by_40pp':(joint['learned']-joint['random'])/joint_episodes>=threshold['random_joint_margin'],
        'anonymous_open_interface_source':all(source_scan.values()),'frozen_policy_and_model_writes_zero':learner.writes==writes and learner.digest()==digest}
    result={'format':'bpc-open-interface-v15','evidence_level':'developer-frozen held-out synthetic open-interface transfer; not third-party blind',
        'question':protocol['question'],'training':events,'factor_digest':learner.digest(),
        'calibration':{'reference_interface_digest':reference.digest(),'reference_action_digest':reference_actions.digest(),
            'interfaces':[{'sensor_routes':list(x['sensor']),'actuator_routes':list(x['actuator']),'target_mix':x['mix'],
                'channel_oracle':list(x['channel_oracle']),'channel_binding':norm(x['channel']),
                'action_oracle':list(x['action_oracle']),'action_binding':norm(x['action']),
                'random_channels':list(x['random_channels']),'random_actions':list(x['random_actions'])} for x in interfaces]},
        'holdout':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')},
            'initial_overlap_with_all_prior':len(holdout_keys&excluded)},'conditions':conditions,'worlds_with_success_trace':trace_counts,
        'aggregate':{'episodes_per_condition':episodes,'joint_episodes':joint_episodes,
            **{f'{name}_total':total(rows,name,'successes') for name in ('learned','oracle','sensor_only','action_only','identity','random')},
            **{f'{name}_joint':value for name,value in joint.items()}},'source_scan':source_scan,
        'model_writes_during_evaluation':learner.writes-writes,'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'A frozen non-neural BPC controller identified its canonical six-sensor/four-action interface inside four simultaneous unseen eight-channel/six-slot interfaces with deterministic state-keyed random nuisance planes and permanent zero-effect action slots, using unlabeled transition probabilities under calibration-distribution shift, and exactly preserved oracle-subset direct control on disjoint unseen worlds.',
        'boundary':protocol['boundary']}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
