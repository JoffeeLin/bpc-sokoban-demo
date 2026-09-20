#!/usr/bin/env python3
"""Execute the pre-registered v0.20 stochastic-channel evaluation once."""
import hashlib,inspect,json,re,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import LabWorld,infer_relational_support_binding,inverse,lab_distance
from bpc_spatial_interface_v18 import transformed_delta
from bpc_stochastic_interface_v20 import (StochasticGaugePolicy,collect_stochastic,effect_profiles,evaluate_stochastic,fit_gauge,fit_mixture,infer_stochastic_gauge,mode_rows)
from bpc_three_factor_v12 import key,train

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v20_stochastic.json';HOLDOUT=ROOT/'holdout_v20.json';OUT=ROOT/'artifacts'/'v20stochastic'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_gauge(row):return {**row,'rows':[list(x) for x in row['rows']]}
def norm_stochastic(row):return {**row,'gauges':[norm_gauge(x) for x in row['gauges']],'single':norm_gauge(row['single']),
    'candidate_lags':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['candidate_lags']],
    'per_stream':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['per_stream']]}
def expected_rows(actual,candidate,channels):
    out=[]
    for row in channels:
        if row is None:out.append((0.,0.,0.,0.,1.));continue
        values=[]
        for action in range(4):
            delta=transformed_delta(candidate,action);physical=next(x for x in range(4) if transformed_delta(actual,x)==delta);values.append(row[physical])
        out.append(tuple(values)+(0.,))
    return tuple(out)
def error(learned,truth):return sum(abs(a-b) for row,target in zip(learned,truth) for a,b in zip(row,target))/(2*len(learned))
def identity_rows(total):return tuple(tuple(1. if component==(slot if slot<4 else 4) else 0. for component in range(5)) for slot in range(total))
def total(rows,name,key='successes'):return sum(row[name].get(key,0) for row in rows)


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    assert sha(HOLDOUT)==protocol['holdout_sha256'];suite=[]
    for row in json.loads(HOLDOUT.read_text())['worlds']:
        world=LabWorld(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates']);assert lab_distance(world,row['family'])==row['shortest']
        if row['family']=='joint':assert lab_distance(world,row['family'],True,False) is None and lab_distance(world,row['family'],False,True) is None
        suite.append((row['family'],world,row['shortest']))
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter();learner,events=train(config['train_seed'])
    assert events==protocol['expected_training_events'] and learner.digest()==protocol['expected_factor_digest'];excluded=set(learner.training_initials)
    reference,triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;profiles=effect_profiles(triples);assert reference.digest()==protocol['reference_interface_digest'] and support(reference_support)==protocol['reference_support'] and profiles.digest()==protocol['reference_effect_digest'];interfaces=[]
    for index,(seeds,sensors,channels,kinds,spatial,delays,expected) in enumerate(zip(config['target_seeds'],config['sensor_routes'],config['stochastic_channels'],config['distractor_kinds'],config['spatial_transforms'],config['temporal_delays'],protocol['expected_calibration'])):
        sensors=tuple(sensors);channels=tuple(tuple(x) if x else None for x in channels);kinds=tuple(kinds);sensor_delay,actuator_delay=delays;targets=[];sequences=[];streams=[];regimes=[]
        for seed,mix,expected_regime in zip(seeds,config['target_mixtures'],expected['regimes']):
            target,flat,episodes,initials,target_support=collect_stochastic(seed,mix,config['calibration_steps'],sensors,channels,kinds,spatial,sensor_delay,actuator_delay,excluded)
            excluded|=initials;targets.append((target,target_support,flat));sequences.extend(episodes);streams.append(episodes);assert target.digest()==expected_regime['interface_digest'] and support(target_support)==expected_regime['support'];regimes.append(expected_regime)
        sensor=infer_relational_support_binding(reference,reference_support,triples,targets);stochastic=infer_stochastic_gauge(profiles,sequences,sensor['mapping'],len(sensors),len(channels),streams,config['maximum_total_lag'])
        assert norm_sensor(sensor)==expected['sensor_binding'] and norm_stochastic(stochastic)==expected['stochastic_binding']
        interfaces.append({'index':index,'sensors':sensors,'channels':channels,'kinds':kinds,'spatial':spatial,'sensor_delay':sensor_delay,'actuator_delay':actuator_delay,'sensor':sensor,'stochastic':stochastic,'sensor_oracle':inverse(sensors,6)})
    holdout_keys={key(world) for _,world,_ in suite};assert not holdout_keys&excluded;writes=learner.writes;digest=learner.digest();conditions={};trace_counts={}
    for interface in interfaces:
        stochastic=interface['stochastic'];channels=interface['channels'];learned=tuple({'transform':x['transform'],'rows':x['rows']} for x in stochastic['gauges'])
        oracle=({'transform':interface['spatial'],'rows':expected_rows(interface['spatial'],interface['spatial'],channels)},)
        deterministic=tuple({'transform':x['transform'],'rows':mode_rows(x['rows'])} for x in stochastic['gauges'])
        identity=tuple({'transform':x['transform'],'rows':identity_rows(len(channels))} for x in stochastic['gauges'])
        shuffled=tuple({'transform':x['transform'],'rows':x['rows'][1:]+x['rows'][:1]} for x in stochastic['gauges'])
        policies={name:StochasticGaugePolicy(learner,interface['sensor_oracle'] if name=='oracle' else interface['sensor']['mapping'],len(interface['sensors']),rows,len(channels)) for name,rows in
            {'learned':learned,'oracle':oracle,'deterministic':deterministic,'identity':identity,'shuffled':shuffled}.items()}
        by_seed={};by_trace={}
        for seed in config['eval_seeds']:
            result,traces=evaluate_stochastic(policies,suite,interface['sensors'],channels,interface['kinds'],interface['spatial'],interface['sensor_delay'],interface['actuator_delay'],seed,config['episodes_per_map'],config['step_budget'])
            by_seed[str(seed)]=result;by_trace[str(seed)]={name:len(row) for name,row in traces.items()}
        conditions[str(interface['index'])]=by_seed;trace_counts[str(interface['index'])]=by_trace
    rows=[row for interface in conditions.values() for row in interface.values()];per={}
    for interface in interfaces:
        local=list(conditions[str(interface['index'])].values());episodes=total(local,'oracle','episodes');per[str(interface['index'])]={'episodes':episodes,**{name:total(local,name) for name in ('learned','oracle','deterministic','identity','shuffled')}}
    gauge_errors=[error(x['rows'],expected_rows(interface['spatial'],x['transform'],interface['channels'])) for interface in interfaces for x in interface['stochastic']['gauges']]
    stream_errors=[error(x['rows'],expected_rows(interface['spatial'],x['transform'],interface['channels'])) for interface in interfaces for stream in interface['stochastic']['per_stream'] for x in stream['gauges']]
    source='\n'.join(inspect.getsource(x) for x in (fit_mixture,fit_gauge,infer_stochastic_gauge,StochasticGaugePolicy.probabilities));forbidden=('family','goal','reward','loss','gradient','torch','tensorflow','sklearn','shortest','classifier','planner','search');source_scan={word:re.search(rf'\b{word}\b',source.lower()) is None for word in forbidden};each=list(per.values())
    lag_exact=sum(x['stochastic']['lag']==x['sensor_delay']+x['actuator_delay'] for x in interfaces);stream_lag_exact=sum(row['lag']==x['sensor_delay']+x['actuator_delay'] for x in interfaces for row in x['stochastic']['per_stream'])
    gate={'four_unseen_sensor_interfaces_recovered':all(x['sensor']['mapping']==x['sensor_oracle'] for x in interfaces),'all_twelve_sensor_streams_recovered':all(all(row['mapping']==x['sensor_oracle'] for row in x['sensor']['per_stream']) for x in interfaces),
        'all_four_unseen_total_lags_recovered':lag_exact==4,'all_twelve_stream_total_lags_recovered':stream_lag_exact==12,
        'all_gauge_channels_within_frozen_tv':max(gauge_errors)<=threshold['maximum_gauge_channel_total_variation'],'all_stream_gauge_channels_within_frozen_tv':max(stream_errors)<=threshold['maximum_stream_gauge_channel_total_variation'],
        'actual_lags_absent_from_development':set(x['sensor_delay']+x['actuator_delay'] for x in interfaces).isdisjoint({1,3}),'holdout_initials_disjoint_from_training_and_calibration':not holdout_keys&excluded,
        'each_interface_at_least_80pct_oracle':all(x['learned']>=x['oracle']*threshold['minimum_oracle_fraction_each_interface'] for x in each),
        'each_interface_beats_identity_by_5pct':all(x['learned']-x['identity']>=x['episodes']*threshold['minimum_identity_margin_each_interface'] for x in each),
        'each_interface_beats_shuffled_by_5pct':all(x['learned']-x['shuffled']>=x['episodes']*threshold['minimum_shuffled_margin_each_interface'] for x in each),
        'anonymous_probability_source':all(source_scan.values()),'frozen_policy_and_model_writes_zero':learner.writes==writes and learner.digest()==digest}
    names=('learned','oracle','deterministic','identity','shuffled');episodes=total(rows,'oracle','episodes')
    result={'format':'bpc-stochastic-v20','evidence_level':'developer-frozen held-out synthetic stochastic-channel and cross-generator transfer; not third-party blind','question':protocol['question'],'training':events,'factor_digest':learner.digest(),
        'calibration':{'reference_generator':'original','target_generator':'independent rectangular lab','reference_interface_digest':reference.digest(),'reference_effect_digest':profiles.digest(),
            'interfaces':[{'sensor_routes':list(x['sensors']),'stochastic_channels_evaluator_only':[list(y) if y else None for y in x['channels']],'distractor_kinds':list(x['kinds']),
                'spatial_transform_evaluator_only':x['spatial'],'sensor_delay_evaluator_only':x['sensor_delay'],'actuator_delay_evaluator_only':x['actuator_delay'],'sensor_oracle':list(x['sensor_oracle']),
                'sensor_binding':norm_sensor(x['sensor']),'stochastic_binding':norm_stochastic(x['stochastic'])} for x in interfaces]},
        'holdout':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')},'initial_overlap_with_all_prior':len(holdout_keys&excluded)},
        'conditions':conditions,'worlds_with_success_trace':trace_counts,'per_interface':per,'aggregate':{'episodes_per_condition':episodes,**{f'{name}_successes':total(rows,name) for name in names},
            'lag_exact':lag_exact,'stream_lag_exact':stream_lag_exact,'maximum_gauge_channel_error':max(gauge_errors),'maximum_stream_gauge_channel_error':max(stream_errors)},
        'source_scan':source_scan,'model_writes_during_evaluation':learner.writes-writes,'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'A frozen non-neural direct BPC controller inferred unseen stochastic actuator probability channels while jointly recovering anonymous sensor interfaces, D4 gauge classes, and end-to-end lags, then preserved control on disjoint independent-generator worlds.',
        'boundary':protocol['boundary']}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
