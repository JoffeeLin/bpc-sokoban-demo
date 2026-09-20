#!/usr/bin/env python3
"""Execute the pre-registered v0.19 end-to-end temporal-gauge evaluation once."""
import hashlib,inspect,json,random,re,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import LabWorld,infer_relational_support_binding,inverse,lab_distance
from bpc_open_interface_v15 import OpenActionStats,OpenInterfaceStats,action_stats
from bpc_spatial_interface_v18 import GaugeAveragedPolicy,SpatialBoundPolicy,gauge_equivalent_mapping
from bpc_temporal_interface_v19 import (averaged_policy,collect_temporal,evaluate_temporal,gauges_for_lag,
    infer_temporal_gauge,temporal_action_stats)
from bpc_three_factor_v12 import key,train

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v19_temporal.json';HOLDOUT=ROOT/'holdout_v19.json';OUT=ROOT/'artifacts'/'v19temporal'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_gauge(row):return {**row,'mapping':list(row['mapping']),'candidate_slots':list(row['candidate_slots'])}
def norm_temporal(row):return {**row,'single':norm_gauge(row['single']),'gauges':[norm_gauge(x) for x in row['gauges']],
    'candidate_lags':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['candidate_lags']],
    'per_stream':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['per_stream']]}
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
    assert reference.digest()==protocol['reference_interface_digest'] and support(reference_support)==protocol['reference_support'];assert reference_actions.digest()==protocol['reference_action_digest'];interfaces=[]
    for index,(seeds,sensors,actions,kinds,spatial,delays,expected) in enumerate(zip(config['target_seeds'],config['sensor_routes'],config['action_routes'],config['distractor_kinds'],config['spatial_transforms'],config['temporal_delays'],protocol['expected_calibration'])):
        sensors=tuple(sensors);actions=tuple(actions);kinds=tuple(kinds);sensor_delay,actuator_delay=delays;targets=[];sequences=[];streams=[];regimes=[]
        for seed,mix,expected_regime in zip(seeds,config['target_mixtures'],expected['regimes']):
            target,flat,episodes,initials,target_support=collect_temporal(seed,mix,config['calibration_steps'],sensors,actions,kinds,spatial,sensor_delay,actuator_delay,excluded)
            excluded|=initials;targets.append((target,target_support,flat));sequences.extend(episodes);streams.append(episodes)
            assert target.digest()==expected_regime['interface_digest'] and support(target_support)==expected_regime['support'];regimes.append({'interface_digest':target.digest(),'support':support(target_support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets)
        temporal=infer_temporal_gauge(reference_actions,sequences,channel['mapping'],len(sensors),len(actions),streams,config['maximum_total_lag'])
        assert norm_sensor(channel)==expected['channel_binding'] and norm_temporal(temporal)==expected['temporal_binding']
        interfaces.append({'index':index,'sensors':sensors,'actions':actions,'kinds':kinds,'spatial':spatial,'sensor_delay':sensor_delay,'actuator_delay':actuator_delay,
            'channel':channel,'temporal':temporal,'channel_oracle':inverse(sensors,6),'action_oracle':inverse(actions,4),'regimes':regimes})
    holdout_keys={key(world) for _,world,_ in suite};assert not holdout_keys&excluded;writes=learner.writes;digest=learner.digest();conditions={};trace_counts={};rng=random.Random(config['random_binding_seed'])
    for interface in interfaces:
        lag=interface['sensor_delay']+interface['actuator_delay'];by_lag={x['lag']:x['gauges'] for x in interface['temporal']['candidate_lags']};shifted=(lag+1)%(config['maximum_total_lag']+1)
        random_channels=rng.sample(range(len(interface['sensors'])),6);random_frame=rng.randrange(8);random_actions=rng.sample(range(len(interface['actions'])),4)
        policies={'temporal_average':averaged_policy(learner,interface['channel']['mapping'],len(interface['sensors']),interface['temporal']['gauges'],len(interface['actions'])),
            'zero_lag':averaged_policy(learner,interface['channel']['mapping'],len(interface['sensors']),by_lag[0],len(interface['actions'])),
            'shifted_lag':averaged_policy(learner,interface['channel']['mapping'],len(interface['sensors']),by_lag[shifted],len(interface['actions'])),
            'ml_single':SpatialBoundPolicy(learner,interface['channel']['mapping'],len(interface['sensors']),interface['temporal']['single']['transform'],interface['temporal']['single']['mapping'],len(interface['actions'])),
            'oracle':SpatialBoundPolicy(learner,interface['channel_oracle'],len(interface['sensors']),interface['spatial'],interface['action_oracle'],len(interface['actions'])),
            'random':SpatialBoundPolicy(learner,random_channels,len(interface['sensors']),random_frame,random_actions,len(interface['actions']))}
        by_seed={};by_trace={}
        for seed in config['eval_seeds']:
            result,traces=evaluate_temporal(policies,suite,interface['sensors'],interface['actions'],interface['kinds'],interface['spatial'],interface['sensor_delay'],interface['actuator_delay'],seed,config['episodes_per_map'],config['step_budget'])
            by_seed[str(seed)]=result;by_trace[str(seed)]={name:len(row) for name,row in traces.items()}
        interface['shifted_lag']=shifted;interface['random_channels']=tuple(random_channels);interface['random_frame']=random_frame;interface['random_actions']=tuple(random_actions);conditions[str(interface['index'])]=by_seed;trace_counts[str(interface['index'])]=by_trace
    rows=[row for interface in conditions.values() for row in interface.values()];per_interface={}
    for interface in interfaces:
        local=list(conditions[str(interface['index'])].values());episodes=total(local,'oracle','episodes');per_interface[str(interface['index'])]={'episodes':episodes,**{name:total(local,name) for name in ('temporal_average','zero_lag','shifted_lag','ml_single','oracle','random')}}
    lag_exact=sum(x['temporal']['lag']==x['sensor_delay']+x['actuator_delay'] for x in interfaces);stream_lag_exact=sum(stream['lag']==x['sensor_delay']+x['actuator_delay'] for x in interfaces for stream in x['temporal']['per_stream'])
    gauge_exact=sum(row['mapping']==gauge_equivalent_mapping(x['spatial'],row['transform'],x['action_oracle']) for x in interfaces for row in x['temporal']['gauges'])
    stream_gauge_exact=sum(row['mapping']==gauge_equivalent_mapping(x['spatial'],row['transform'],x['action_oracle']) for x in interfaces for stream in x['temporal']['per_stream'] for row in stream['gauges'])
    source='\n'.join(inspect.getsource(x) for x in (OpenInterfaceStats.observe,OpenActionStats.observe,temporal_action_stats,gauges_for_lag,infer_temporal_gauge,GaugeAveragedPolicy.probabilities))
    forbidden=('family','goal','reward','loss','gradient','torch','tensorflow','sklearn','shortest','classifier');source_scan={word:re.search(rf'\b{word}\b',source.lower()) is None for word in forbidden};each=list(per_interface.values())
    gate={'four_unseen_sensor_interfaces_recovered':all(x['channel']['mapping']==x['channel_oracle'] for x in interfaces),
        'all_sixteen_sensor_streams_recovered':all(all(row['mapping']==x['channel_oracle'] for row in x['channel']['per_stream']) for x in interfaces),
        'all_four_unseen_total_lags_recovered':lag_exact==4,'all_sixteen_stream_total_lags_recovered':stream_lag_exact==16,
        'all_32_temporal_gauge_action_pairs_equivalent':gauge_exact==32,'all_128_stream_temporal_gauge_pairs_equivalent':stream_gauge_exact==128,
        'actual_lags_absent_from_development':set(x['sensor_delay']+x['actuator_delay'] for x in interfaces).isdisjoint({1,3}),
        'each_total_lag_has_two_distinct_physical_decompositions':all(len({(x['sensor_delay'],x['actuator_delay']) for x in interfaces if x['sensor_delay']+x['actuator_delay']==lag})==2 for lag in (2,4)),
        'holdout_initials_disjoint_from_training_and_calibration':not holdout_keys&excluded,
        'each_interface_at_least_80pct_oracle':all(x['temporal_average']>=x['oracle']*threshold['minimum_oracle_fraction_each_interface'] for x in each),
        'each_interface_beats_zero_lag_by_5pct':all(x['temporal_average']-x['zero_lag']>=x['episodes']*threshold['minimum_zero_lag_margin_each_interface'] for x in each),
        'each_interface_beats_shifted_lag_by_5pct':all(x['temporal_average']-x['shifted_lag']>=x['episodes']*threshold['minimum_shifted_lag_margin_each_interface'] for x in each),
        'anonymous_probability_source':all(source_scan.values()),'frozen_policy_and_model_writes_zero':learner.writes==writes and learner.digest()==digest}
    names=('temporal_average','zero_lag','shifted_lag','ml_single','oracle','random');episodes=total(rows,'oracle','episodes')
    result={'format':'bpc-temporal-v19','evidence_level':'developer-frozen held-out synthetic end-to-end temporal-gauge and cross-generator transfer; not third-party blind',
        'question':protocol['question'],'training':events,'factor_digest':learner.digest(),
        'calibration':{'reference_generator':'original','target_generator':'independent rectangular lab','reference_interface_digest':reference.digest(),
            'interfaces':[{'sensor_routes':list(x['sensors']),'action_routes':list(x['actions']),'distractor_kinds':list(x['kinds']),'spatial_transform_evaluator_only':x['spatial'],
                'sensor_delay_evaluator_only':x['sensor_delay'],'actuator_delay_evaluator_only':x['actuator_delay'],'total_lag':x['temporal']['lag'],'channel_oracle':list(x['channel_oracle']),
                'channel_binding':norm_sensor(x['channel']),'action_oracle':list(x['action_oracle']),'temporal_binding':norm_temporal(x['temporal']),
                'shifted_lag_control':x['shifted_lag'],'random_channels':list(x['random_channels']),'random_frame':x['random_frame'],'random_actions':list(x['random_actions'])} for x in interfaces]},
        'holdout':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')},'initial_overlap_with_all_prior':len(holdout_keys&excluded)},
        'conditions':conditions,'worlds_with_success_trace':trace_counts,'per_interface':per_interface,
        'aggregate':{'episodes_per_condition':episodes,**{f'{name}_successes':total(rows,name) for name in names},'lag_exact':lag_exact,'stream_lag_exact':stream_lag_exact,'gauge_pairs_exact':gauge_exact,'stream_gauge_pairs_exact':stream_gauge_exact},
        'source_scan':source_scan,'model_writes_during_evaluation':learner.writes-writes,'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'A frozen non-neural direct BPC controller inferred unseen identifiable end-to-end lags from unlabeled transitions while jointly recovering variable sensor/action interfaces and a D4 gauge class, then preserved control on disjoint worlds from an independent rectangular generator.',
        'boundary':protocol['boundary']}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
