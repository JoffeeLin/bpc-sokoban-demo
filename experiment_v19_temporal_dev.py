#!/usr/bin/env python3
"""Development-only temporal-gauge plus variable spatial-interface experiment."""
import json,random,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import infer_relational_support_binding,inverse,lab_suite
from bpc_open_interface_v15 import action_stats
from bpc_spatial_interface_v18 import SpatialBoundPolicy,gauge_equivalent_mapping
from bpc_temporal_interface_v19 import averaged_policy,collect_temporal,evaluate_temporal,infer_temporal_gauge
from bpc_three_factor_v12 import train

SENSORS=((4,None,0,2,None,5,3,None,1),(None,2,4,1,None,3,None,5,0,None),(5,None,3,None,0,1,None,None,2,4,None))
ACTIONS=((None,3,1,0,2),(0,None,2,None,1,3,None),(None,1,3,None,2,None,0,None))
KINDS=((0,1,2),(2,0,1,2),(1,2,0,1,2));SPATIAL=(1,4,7);TEMPORAL=((0,1),(1,2),(1,0))
MIXES=({'push':126,'collect':27,'open':27},{'push':27,'collect':126,'open':27},{'push':27,'collect':27,'open':126},{'push':60,'collect':60,'open':60})


def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_gauge(row):return {**row,'mapping':list(row['mapping']),'candidate_slots':list(row['candidate_slots'])}
def norm_temporal(row):
    return {**row,'single':norm_gauge(row['single']),'gauges':[norm_gauge(x) for x in row['gauges']],
        'candidate_lags':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['candidate_lags']],
        'per_stream':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['per_stream']]}


def main():
    started=time.perf_counter();learner,training=train(121010);excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(191010,100,32,exclude=excluded);excluded|=initials;reference_actions=action_stats(reference_triples,range(6),6,4)
    bindings=[];interfaces=[]
    for index,(sensors,actions,kinds,spatial,delays) in enumerate(zip(SENSORS,ACTIONS,KINDS,SPATIAL,TEMPORAL)):
        sensor_delay,actuator_delay=delays;targets=[];sequences=[];streams=[];regimes=[]
        for seed,mix in zip(range(191110+index*10,191114+index*10),MIXES):
            target,flat,episodes,initials,support=collect_temporal(seed,mix,32,sensors,actions,kinds,spatial,sensor_delay,actuator_delay,excluded);excluded|=initials
            targets.append((target,support,flat));sequences.extend(episodes);streams.append(episodes);regimes.append({'digest':target.digest(),'support_size':len(support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets)
        temporal=infer_temporal_gauge(reference_actions,sequences,channel['mapping'],len(sensors),len(actions),streams)
        total_lag=sensor_delay+actuator_delay;oracle_actions=inverse(actions,4);expected={t:gauge_equivalent_mapping(spatial,t,oracle_actions) for t in range(8)}
        equivalence=[{'transform':x['transform'],'expected':list(expected[x['transform']]),'learned':list(x['mapping']),'exact':x['mapping']==expected[x['transform']]} for x in temporal['gauges']]
        stream_equivalence=[[{'transform':x['transform'],'exact':x['mapping']==expected[x['transform']]} for x in stream['gauges']] for stream in temporal['per_stream']]
        interfaces.append((sensors,actions,kinds,spatial,sensor_delay,actuator_delay,channel,temporal));bindings.append({'sensor_routes':list(sensors),'action_routes':list(actions),'kinds':list(kinds),
            'spatial_oracle':spatial,'sensor_delay_evaluator_only':sensor_delay,'actuator_delay_evaluator_only':actuator_delay,'total_lag_oracle':total_lag,
            'channel_oracle':list(inverse(sensors,6)),'channel_binding':norm_sensor(channel),'action_oracle':list(oracle_actions),'temporal_binding':norm_temporal(temporal),
            'gauge_equivalence':equivalence,'stream_gauge_equivalence':stream_equivalence,'regimes':regimes})
    suite,attempts=lab_suite(191510,8,excluded);conditions={};writes=learner.writes;rng=random.Random(191610)
    for index,(sensors,actions,kinds,spatial,sensor_delay,actuator_delay,channel,temporal) in enumerate(interfaces):
        total_lag=sensor_delay+actuator_delay;oracle_channels=inverse(sensors,6);oracle_actions=inverse(actions,4);by_lag={x['lag']:x['gauges'] for x in temporal['candidate_lags']};shifted=(total_lag+1)%5
        random_channels=rng.sample(range(len(sensors)),6);random_actions=rng.sample(range(len(actions)),4);random_spatial=rng.randrange(8)
        policies={'temporal_average':averaged_policy(learner,channel['mapping'],len(sensors),temporal['gauges'],len(actions)),
            'zero_lag':averaged_policy(learner,channel['mapping'],len(sensors),by_lag[0],len(actions)),
            'shifted_lag':averaged_policy(learner,channel['mapping'],len(sensors),by_lag[shifted],len(actions)),
            'ml_single':SpatialBoundPolicy(learner,channel['mapping'],len(sensors),temporal['single']['transform'],temporal['single']['mapping'],len(actions)),
            'oracle':SpatialBoundPolicy(learner,oracle_channels,len(sensors),spatial,oracle_actions,len(actions)),
            'random':SpatialBoundPolicy(learner,random_channels,len(sensors),random_spatial,random_actions,len(actions))}
        result,traces=evaluate_temporal(policies,suite,sensors,actions,kinds,spatial,sensor_delay,actuator_delay,191710+index,24,72);conditions[str(index)]=result
        bindings[index]['shifted_lag_control']=shifted;bindings[index]['random_channels']=random_channels;bindings[index]['random_actions']=random_actions;bindings[index]['random_spatial']=random_spatial;bindings[index]['trace_worlds']={name:len(x) for name,x in traces.items()}
    total=lambda name:sum(row[name]['successes'] for row in conditions.values());episodes=sum(row['oracle']['episodes'] for row in conditions.values());per_interface=[]
    for key,row in conditions.items():per_interface.append({'interface':int(key),'episodes':row['oracle']['episodes'],**{name:row[name]['successes'] for name in ('temporal_average','zero_lag','shifted_lag','ml_single','oracle','random')}})
    diagnostic={'channel_exact':sum(row['channel_binding']['mapping']==row['channel_oracle'] for row in bindings),
        'lag_exact':sum(row['temporal_binding']['lag']==row['total_lag_oracle'] for row in bindings),
        'stream_lag_exact':sum(x['lag']==row['total_lag_oracle'] for row in bindings for x in row['temporal_binding']['per_stream']),
        'gauge_pairs_exact':sum(x['exact'] for row in bindings for x in row['gauge_equivalence']),
        'stream_gauge_pairs_exact':sum(x['exact'] for row in bindings for stream in row['stream_gauge_equivalence'] for x in stream),
        'temporal_average_successes':total('temporal_average'),'oracle_successes':total('oracle'),'zero_lag_successes':total('zero_lag'),
        'shifted_lag_successes':total('shifted_lag'),'episodes':episodes,'per_interface':per_interface}
    gates={'channel_exact_3_of_3':diagnostic['channel_exact']==3,'total_lag_exact_3_of_3':diagnostic['lag_exact']==3,
        'all_12_stream_lags_exact':diagnostic['stream_lag_exact']==12,'all_24_gauge_pairs_equivalent':diagnostic['gauge_pairs_exact']==24,
        'all_96_stream_gauge_pairs_equivalent':diagnostic['stream_gauge_pairs_exact']==96,
        'each_interface_at_least_80pct_oracle':all(x['temporal_average']>=x['oracle']*.8 for x in per_interface),
        'each_interface_beats_zero_lag_by_5pct':all(x['temporal_average']-x['zero_lag']>=x['episodes']*.05 for x in per_interface),
        'each_interface_beats_shifted_lag_by_5pct':all(x['temporal_average']-x['shifted_lag']>=x['episodes']*.05 for x in per_interface),
        'evaluation_writes_zero':learner.writes==writes}
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'classifier_dev':{'model':'jev-1.13.0','batch_items':14,'selected':'joint sensor and actuator latency frontier','confidence':.82,
            'implemented_identifiable_quantity':'end-to-end lag only','role':'candidate routing only; absent from inference, training, evaluation, and runtime'},
        'reference':{'generator':'original','worlds':300,'interface_digest':reference.digest(),'action_digest':reference_actions.digest()},
        'target':{'generator':'independent rectangular lab','bindings':bindings,'suite':{'worlds':len(suite),'attempts':attempts}},
        'conditions':conditions,'diagnostic':diagnostic,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),
        'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development-only synthetic end-to-end temporal-gauge binding. Sensor and actuator delay are not separately identifiable; only their sum is claimed. Lag candidates 0-4, D4 family, schema, statistics, generators, terminal events, and direct policy remain supplied. No neural network, label, reward, planner, runtime search, classifier runtime, or evaluation write is used.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v19temporal'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
