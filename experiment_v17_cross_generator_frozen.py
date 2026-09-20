#!/usr/bin/env python3
"""Execute the pre-registered v0.17 cross-generator evaluation once."""
import hashlib,inspect,json,random,re,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface,projected_support
from bpc_cross_generator_v17 import (LabWorld,VariableBoundPolicy,collect_variable,evaluate_variable,
    infer_relational_support_binding,inverse,lab_distance,same_cell_counts,same_cell_log_probability,same_cell_support_compatible)
from bpc_open_interface_v15 import OpenActionStats,OpenInterfaceStats,action_stats,infer_action_subset
from bpc_three_factor_v12 import key,train

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v17_cross_generator.json';HOLDOUT=ROOT/'holdout_v17.json';OUT=ROOT/'artifacts'/'v17crossgen'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def total(rows,name,key):return sum(row[name].get(key,0) for row in rows)
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_action(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'candidate_slots':list(row['candidate_slots'])}


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    assert sha(HOLDOUT)==protocol['holdout_sha256'];suite=[]
    for row in json.loads(HOLDOUT.read_text())['worlds']:
        world=LabWorld(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates'])
        assert lab_distance(world,row['family'])==row['shortest']
        if row['family']=='joint':assert lab_distance(world,row['family'],True,False) is None and lab_distance(world,row['family'],False,True) is None
        suite.append((row['family'],world,row['shortest']))
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter();learner,events=train(config['train_seed'])
    assert events==protocol['expected_training_events'] and learner.digest()==protocol['expected_factor_digest'];excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;reference_actions=action_stats(reference_triples,range(6),6,4)
    assert reference.digest()==protocol['reference_interface_digest'] and support(reference_support)==protocol['reference_support']
    assert reference_actions.digest()==protocol['reference_action_digest'];interfaces=[]
    for index,(seeds,sensors,actions,kinds,expected) in enumerate(zip(config['target_seeds'],config['sensor_routes'],config['action_routes'],config['distractor_kinds'],protocol['expected_calibration'])):
        sensors=tuple(sensors);actions=tuple(actions);kinds=tuple(kinds);targets=[];triples=[];regimes=[]
        for seed,mix,expected_regime in zip(seeds,config['target_mixtures'],expected['regimes']):
            target,row,initials,target_support=collect_variable(seed,mix,config['calibration_steps'],sensors,actions,kinds,excluded)
            excluded|=initials;targets.append((target,target_support,row));triples.extend(row)
            assert target.digest()==expected_regime['interface_digest'] and support(target_support)==expected_regime['support']
            regimes.append({'interface_digest':target.digest(),'support':support(target_support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets)
        target_actions=action_stats(triples,channel['mapping'],len(sensors),len(actions));action=infer_action_subset(reference_actions,target_actions)
        assert norm_sensor(channel)==expected['channel_binding'] and norm_action(action)==expected['action_binding']
        assert target_actions.digest()==expected['target_action_digest'];assert list(inverse(sensors,6))==expected['channel_oracle'];assert list(inverse(actions,4))==expected['action_oracle']
        interfaces.append({'index':index,'sensors':sensors,'actions':actions,'kinds':kinds,'channel':channel,'action':action,
            'channel_oracle':inverse(sensors,6),'action_oracle':inverse(actions,4),'regimes':regimes})
    holdout_keys={key(world) for _,world,_ in suite};assert not holdout_keys&excluded;writes=learner.writes;digest=learner.digest();conditions={};trace_counts={};rng=random.Random(config['random_binding_seed'])
    for interface in interfaces:
        random_channels=rng.sample(range(len(interface['sensors'])),6);random_actions=rng.sample(range(len(interface['actions'])),4)
        policies={'learned':VariableBoundPolicy(learner,interface['channel']['mapping'],len(interface['sensors']),interface['action']['mapping'],len(interface['actions'])),
            'oracle':VariableBoundPolicy(learner,interface['channel_oracle'],len(interface['sensors']),interface['action_oracle'],len(interface['actions'])),
            'sensor_only':VariableBoundPolicy(learner,interface['channel']['mapping'],len(interface['sensors']),range(4),len(interface['actions'])),
            'action_only':VariableBoundPolicy(learner,range(6),len(interface['sensors']),interface['action']['mapping'],len(interface['actions'])),
            'identity':VariableBoundPolicy(learner,range(6),len(interface['sensors']),range(4),len(interface['actions'])),
            'random':VariableBoundPolicy(learner,random_channels,len(interface['sensors']),random_actions,len(interface['actions']))}
        by_seed={};by_trace={}
        for seed in config['eval_seeds']:
            result,traces=evaluate_variable(policies,suite,interface['sensors'],interface['actions'],interface['kinds'],seed,config['episodes_per_map'],config['step_budget'])
            by_seed[str(seed)]=result;by_trace[str(seed)]={name:len(row) for name,row in traces.items()}
        interface['random_channels']=tuple(random_channels);interface['random_actions']=tuple(random_actions);conditions[str(interface['index'])]=by_seed;trace_counts[str(interface['index'])]=by_trace
    rows=[row for interface in conditions.values() for row in interface.values()];joint_episodes=sum(x[0]=='joint' for x in suite)*config['episodes_per_map']*len(config['eval_seeds'])*len(interfaces);episodes=len(suite)*config['episodes_per_map']*len(config['eval_seeds'])*len(interfaces)
    names=('learned','oracle','sensor_only','action_only','identity','random');joint={name:total(rows,name,'joint_successes') for name in names};oracle_exact=all(row['learned']==row['oracle'] for row in rows)
    source='\n'.join(inspect.getsource(x) for x in (projected_support,same_cell_counts,same_cell_support_compatible,same_cell_log_probability,infer_relational_support_binding,OpenInterfaceStats.observe,OpenActionStats.observe,infer_action_subset,VariableBoundPolicy.probabilities))
    forbidden=('push','collect','open','joint','family','goal','reward','score','loss','gradient','torch','tensorflow','sklearn','search','shortest','left','right','up','down')
    source_scan={word:re.search(rf'\b{word}\b',source.lower()) is None for word in forbidden}
    gate={'four_unseen_variable_sensor_interfaces_recovered':all(tuple(x['channel']['mapping'])==x['channel_oracle'] for x in interfaces),
        'all_sixteen_unlabeled_streams_agree_with_oracle':all(all(tuple(row['mapping'])==x['channel_oracle'] for row in x['channel']['per_stream']) for x in interfaces),
        'compatible_mapping_count_in_frozen_range':all(threshold['minimum_compatible_mappings']<=x['channel']['compatible']<=threshold['maximum_compatible_mappings'] for x in interfaces),
        'combined_sensor_log_margin_at_least_8000':all(x['channel']['log_margin']>=threshold['combined_sensor_log_margin'] for x in interfaces),
        'each_stream_sensor_log_margin_at_least_800':all(all(row['log_margin']>=threshold['per_stream_sensor_log_margin'] for row in x['channel']['per_stream']) for x in interfaces),
        'four_unseen_variable_action_interfaces_recovered':all(tuple(x['action']['mapping'])==x['action_oracle'] for x in interfaces),
        'all_noncanonical_action_slots_rejected':all(set(x['action']['candidate_slots'])==set(x['action_oracle']) for x in interfaces),
        'holdout_initials_disjoint_from_training_and_calibration':not holdout_keys&excluded,
        'learned_matches_oracle_every_condition':oracle_exact and joint['learned']==joint['oracle'],
        'learned_joint_rate_at_least_55pct':joint['learned']/joint_episodes>=threshold['joint_rate'],
        'both_bindings_beat_sensor_only_by_45pp':(joint['learned']-joint['sensor_only'])/joint_episodes>=threshold['sensor_only_joint_margin'],
        'both_bindings_beat_action_only_by_40pp':(joint['learned']-joint['action_only'])/joint_episodes>=threshold['action_only_joint_margin'],
        'both_bindings_beat_identity_by_45pp':(joint['learned']-joint['identity'])/joint_episodes>=threshold['identity_joint_margin'],
        'both_bindings_beat_random_by_40pp':(joint['learned']-joint['random'])/joint_episodes>=threshold['random_joint_margin'],
        'anonymous_support_probability_source':all(source_scan.values()),'frozen_policy_and_model_writes_zero':learner.writes==writes and learner.digest()==digest}
    result={'format':'bpc-cross-generator-v17','evidence_level':'developer-frozen held-out synthetic cross-generator and held-out-distractor-family transfer; not third-party blind',
        'question':protocol['question'],'training':events,'factor_digest':learner.digest(),
        'calibration':{'reference_generator':'original','target_generator':'independent rectangular lab','reference_interface_digest':reference.digest(),
            'reference_support':support(reference_support),'reference_action_digest':reference_actions.digest(),
            'interfaces':[{'sensor_routes':list(x['sensors']),'action_routes':list(x['actions']),'distractor_kinds':list(x['kinds']),'regimes':x['regimes'],
                'channel_oracle':list(x['channel_oracle']),'channel_binding':norm_sensor(x['channel']),'action_oracle':list(x['action_oracle']),
                'action_binding':norm_action(x['action']),'random_channels':list(x['random_channels']),'random_actions':list(x['random_actions'])} for x in interfaces]},
        'holdout':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')},'initial_overlap_with_all_prior':len(holdout_keys&excluded)},
        'conditions':conditions,'worlds_with_success_trace':trace_counts,'aggregate':{'episodes_per_condition':episodes,'joint_episodes':joint_episodes,
            **{f'{name}_total':total(rows,name,'successes') for name in names},**{f'{name}_joint':value for name,value in joint.items()}},
        'source_scan':source_scan,'model_writes_during_evaluation':learner.writes-writes,'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'A frozen non-neural BPC controller trained on the original square-map generator preserved oracle direct control on disjoint unseen worlds from an independently implemented rectangular-map generator while recovering four variable-width anonymous sensor/action interfaces containing held-out composite sensor families and non-null nuisance actuators from unlabeled transitions.',
        'boundary':protocol['boundary']}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
