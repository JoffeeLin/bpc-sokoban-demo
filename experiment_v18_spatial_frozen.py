#!/usr/bin/env python3
"""Execute the pre-registered v0.18 D4 gauge-class evaluation once."""
import hashlib,inspect,json,random,re,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import LabWorld,infer_relational_support_binding,inverse,lab_distance
from bpc_open_interface_v15 import OpenActionStats,OpenInterfaceStats,action_stats
from bpc_spatial_interface_v18 import (GaugeAveragedPolicy,SpatialBoundPolicy,collect_spatial,evaluate_spatial,
    gauge_equivalent_mapping,infer_spatial_action,infer_spatial_gauges,spatial_action_stats)
from bpc_three_factor_v12 import key,train

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v18_spatial.json';HOLDOUT=ROOT/'holdout_v18.json';OUT=ROOT/'artifacts'/'v18spatial'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_spatial(row):return {**row,'mapping':list(row['mapping']),'second':{**row['second'],'mapping':list(row['second']['mapping'])},'candidate_slots':list(row['candidate_slots']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_gauge(row):return {**row,'mapping':list(row['mapping']),'candidate_slots':list(row['candidate_slots']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def total(rows,name,key='successes'):return sum(row[name].get(key,0) for row in rows)


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
    for index,(seeds,sensors,actions,kinds,spatial,expected) in enumerate(zip(config['target_seeds'],config['sensor_routes'],config['action_routes'],config['distractor_kinds'],config['spatial_transforms'],protocol['expected_calibration'])):
        sensors=tuple(sensors);actions=tuple(actions);kinds=tuple(kinds);targets=[];triples=[];streams=[];regimes=[]
        for seed,mix,expected_regime in zip(seeds,config['target_mixtures'],expected['regimes']):
            target,row,initials,target_support=collect_spatial(seed,mix,config['calibration_steps'],sensors,actions,kinds,spatial,excluded)
            excluded|=initials;targets.append((target,target_support,row));triples.extend(row);streams.append(row)
            assert target.digest()==expected_regime['interface_digest'] and support(target_support)==expected_regime['support']
            regimes.append({'interface_digest':target.digest(),'support':support(target_support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets)
        single=infer_spatial_action(reference_actions,triples,channel['mapping'],len(sensors),len(actions),streams)
        gauges=infer_spatial_gauges(reference_actions,triples,channel['mapping'],len(sensors),len(actions),streams)
        assert norm_sensor(channel)==expected['channel_binding'] and norm_spatial(single)==expected['single_binding']
        assert [norm_gauge(x) for x in gauges]==expected['gauge_bindings']
        interfaces.append({'index':index,'sensors':sensors,'actions':actions,'kinds':kinds,'spatial':spatial,'channel':channel,'single':single,
            'gauges':gauges,'channel_oracle':inverse(sensors,6),'action_oracle':inverse(actions,4),'regimes':regimes})
    holdout_keys={key(world) for _,world,_ in suite};assert not holdout_keys&excluded;writes=learner.writes;digest=learner.digest();conditions={};trace_counts={};rng=random.Random(config['random_binding_seed'])
    for interface in interfaces:
        learned=[(x['transform'],x['mapping']) for x in interface['gauges']]
        shuffled=[(x['transform'],interface['gauges'][(i+1)%8]['mapping']) for i,x in enumerate(interface['gauges'])]
        policy=lambda channels,frame,actions:SpatialBoundPolicy(learner,channels,len(interface['sensors']),frame,actions,len(interface['actions']))
        random_channels=rng.sample(range(len(interface['sensors'])),6);random_frame=rng.randrange(8);random_actions=rng.sample(range(len(interface['actions'])),4)
        policies={'gauge_average':GaugeAveragedPolicy(learner,interface['channel']['mapping'],len(interface['sensors']),learned,len(interface['actions'])),
            'shuffled_gauge':GaugeAveragedPolicy(learner,interface['channel']['mapping'],len(interface['sensors']),shuffled,len(interface['actions'])),
            'ml_single':policy(interface['channel']['mapping'],interface['single']['transform'],interface['single']['mapping']),
            'oracle':policy(interface['channel_oracle'],interface['spatial'],interface['action_oracle']),
            'no_spatial':policy(interface['channel']['mapping'],0,interface['single']['mapping']),
            'random':policy(random_channels,random_frame,random_actions)}
        by_seed={};by_trace={}
        for seed in config['eval_seeds']:
            result,traces=evaluate_spatial(policies,suite,interface['sensors'],interface['actions'],interface['kinds'],interface['spatial'],seed,config['episodes_per_map'],config['step_budget'])
            by_seed[str(seed)]=result;by_trace[str(seed)]={name:len(row) for name,row in traces.items()}
        interface['random_channels']=tuple(random_channels);interface['random_frame']=random_frame;interface['random_actions']=tuple(random_actions)
        conditions[str(interface['index'])]=by_seed;trace_counts[str(interface['index'])]=by_trace
    rows=[row for interface in conditions.values() for row in interface.values()];per_interface={}
    for interface in interfaces:
        local=list(conditions[str(interface['index'])].values());episodes=total(local,'oracle','episodes')
        per_interface[str(interface['index'])]={'episodes':episodes,**{name:total(local,name) for name in ('gauge_average','shuffled_gauge','ml_single','oracle','no_spatial','random')}}
    gauge_exact=sum(row['mapping']==gauge_equivalent_mapping(x['spatial'],row['transform'],x['action_oracle']) for x in interfaces for row in x['gauges'])
    stream_exact=sum(stream['mapping']==gauge_equivalent_mapping(x['spatial'],row['transform'],x['action_oracle']) for x in interfaces for row in x['gauges'] for stream in row['per_stream'])
    source='\n'.join(inspect.getsource(x) for x in (OpenInterfaceStats.observe,OpenActionStats.observe,spatial_action_stats,infer_spatial_gauges,GaugeAveragedPolicy.probabilities))
    forbidden=('family','goal','reward','loss','gradient','torch','tensorflow','sklearn','shortest','classifier');source_scan={word:re.search(rf'\b{word}\b',source.lower()) is None for word in forbidden}
    each=list(per_interface.values());gate={'four_unseen_sensor_interfaces_recovered':all(x['channel']['mapping']==x['channel_oracle'] for x in interfaces),
        'all_sixteen_sensor_streams_recovered':all(all(row['mapping']==x['channel_oracle'] for row in x['channel']['per_stream']) for x in interfaces),
        'all_active_action_slot_sets_recovered':all(all(set(row['candidate_slots'])==set(x['action_oracle']) for row in x['gauges']) for x in interfaces),
        'all_32_gauge_action_pairs_equivalent':gauge_exact==32,'all_128_stream_gauge_action_pairs_equivalent':stream_exact==128,
        'actual_transforms_nonidentity_and_absent_from_development':set(config['spatial_transforms']).isdisjoint({0,1,4,7}),
        'holdout_initials_disjoint_from_training_and_calibration':not holdout_keys&excluded,
        'each_interface_at_least_85pct_oracle':all(x['gauge_average']>=x['oracle']*threshold['minimum_oracle_fraction_each_interface'] for x in each),
        'each_interface_beats_shuffled_by_5pct':all(x['gauge_average']-x['shuffled_gauge']>=x['episodes']*threshold['minimum_shuffled_margin_each_interface'] for x in each),
        'each_interface_beats_no_spatial_by_5pct':all(x['gauge_average']-x['no_spatial']>=x['episodes']*threshold['minimum_no_spatial_margin_each_interface'] for x in each),
        'anonymous_probability_source':all(source_scan.values()),'frozen_policy_and_model_writes_zero':learner.writes==writes and learner.digest()==digest}
    names=('gauge_average','shuffled_gauge','ml_single','oracle','no_spatial','random');episodes=total(rows,'oracle','episodes')
    result={'format':'bpc-spatial-v18','evidence_level':'developer-frozen held-out synthetic D4 gauge-class and cross-generator transfer; not third-party blind',
        'question':protocol['question'],'training':events,'factor_digest':learner.digest(),
        'calibration':{'reference_generator':'original','target_generator':'independent rectangular lab','reference_interface_digest':reference.digest(),
            'interfaces':[{'sensor_routes':list(x['sensors']),'action_routes':list(x['actions']),'distractor_kinds':list(x['kinds']),
                'spatial_transform_evaluator_only':x['spatial'],'channel_oracle':list(x['channel_oracle']),'channel_binding':norm_sensor(x['channel']),
                'action_oracle':list(x['action_oracle']),'single_binding':norm_spatial(x['single']),'gauge_bindings':[norm_gauge(row) for row in x['gauges']],
                'random_channels':list(x['random_channels']),'random_frame':x['random_frame'],'random_actions':list(x['random_actions'])} for x in interfaces]},
        'holdout':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')},'initial_overlap_with_all_prior':len(holdout_keys&excluded)},
        'conditions':conditions,'worlds_with_success_trace':trace_counts,'per_interface':per_interface,
        'aggregate':{'episodes_per_condition':episodes,**{f'{name}_successes':total(rows,name) for name in names},'gauge_pairs_exact':gauge_exact,'stream_gauge_pairs_exact':stream_exact},
        'source_scan':source_scan,'model_writes_during_evaluation':learner.writes-writes,'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'A frozen non-neural direct BPC controller learned the complete observationally equivalent D4 gauge-action class from unlabeled transitions and preserved control across four new variable-width sensor/action interfaces, four new actual spatial transforms, held-out nuisance families, and disjoint unseen worlds from an independent rectangular generator.',
        'boundary':protocol['boundary']}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
