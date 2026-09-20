#!/usr/bin/env python3
"""Development-only stochastic actuator-channel plus temporal/D4 gauge experiment."""
import json,random,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import infer_relational_support_binding,inverse,lab_suite
from bpc_spatial_interface_v18 import transformed_delta
from bpc_stochastic_interface_v20 import (StochasticGaugePolicy,collect_stochastic,effect_profiles,evaluate_stochastic,
    infer_stochastic_gauge,mode_rows)
from bpc_three_factor_v12 import train

SENSORS=((4,None,0,2,None,5,3,None,1),(None,2,4,1,None,3,None,5,0,None),(5,None,3,None,0,1,None,None,2,4,None))
KINDS=((0,1,2),(2,0,1,2),(1,2,0,1,2));SPATIAL=(1,4,7);TEMPORAL=((0,1),(1,2),(1,0))
CHANNELS=(
    (None,(.13,.08,.62,.17),(.60,.23,.08,.09),(.11,.17,.12,.60),(.09,.59,.21,.11)),
    ((.13,.54,.20,.13),None,(.14,.17,.12,.57),(.58,.11,.20,.11),None,(.17,.13,.55,.15)),
    (None,(.13,.19,.15,.53),(.56,.20,.13,.11),None,(.19,.12,.53,.16),(.11,.56,.18,.15),None))
MIXES=({'push':90,'collect':24,'open':24},{'push':24,'collect':90,'open':24},{'push':24,'collect':24,'open':90})


def expected_rows(actual,candidate,channels):
    out=[]
    for row in channels:
        if row is None:out.append((0.,0.,0.,0.,1.));continue
        values=[]
        for action in range(4):
            delta=transformed_delta(candidate,action);physical=next(x for x in range(4) if transformed_delta(actual,x)==delta);values.append(row[physical])
        out.append(tuple(values)+(0.,))
    return tuple(out)


def error(learned,expected):return sum(abs(a-b) for row,truth in zip(learned,expected) for a,b in zip(row,truth))/(2*len(learned))
def identity_rows(total):return tuple(tuple(1. if component==(slot if slot<4 else 4) else 0. for component in range(5)) for slot in range(total))
def gauge_rows(gauges,fn):return tuple({'transform':x['transform'],'rows':fn(x['rows'])} for x in gauges)
def norm_gauge(row):return {**row,'rows':[list(x) for x in row['rows']]}
def norm_binding(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_stochastic(row):return {**row,'gauges':[norm_gauge(x) for x in row['gauges']],'single':norm_gauge(row['single']),
    'candidate_lags':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['candidate_lags']],
    'per_stream':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['per_stream']]}


def main():
    started=time.perf_counter();learner,training=train(122010);excluded=set(learner.training_initials)
    reference,triples,initials,reference_support=collect_composite_interface(201010,100,32,exclude=excluded);excluded|=initials;profiles=effect_profiles(triples)
    bindings=[];interfaces=[]
    for index,(sensors,channels,kinds,spatial,delays) in enumerate(zip(SENSORS,CHANNELS,KINDS,SPATIAL,TEMPORAL)):
        for row in channels:
            if row is not None:assert abs(sum(row)-1)<1e-9
        sensor_delay,actuator_delay=delays;targets=[];sequences=[];streams=[];regimes=[]
        for seed,mix in zip(range(201110+index*10,201113+index*10),MIXES):
            target,flat,episodes,initials,support=collect_stochastic(seed,mix,32,sensors,channels,kinds,spatial,sensor_delay,actuator_delay,excluded);excluded|=initials
            targets.append((target,support,flat));sequences.extend(episodes);streams.append(episodes);regimes.append({'digest':target.digest(),'support_size':len(support)})
        sensor=infer_relational_support_binding(reference,reference_support,triples,targets)
        stochastic=infer_stochastic_gauge(profiles,sequences,sensor['mapping'],len(sensors),len(channels),streams)
        total_lag=sensor_delay+actuator_delay;gauge_error=[{'transform':x['transform'],'total_variation':error(x['rows'],expected_rows(spatial,x['transform'],channels))} for x in stochastic['gauges']]
        stream_error=[[{'transform':x['transform'],'total_variation':error(x['rows'],expected_rows(spatial,x['transform'],channels))} for x in stream['gauges']] for stream in stochastic['per_stream']]
        interfaces.append((sensors,channels,kinds,spatial,sensor_delay,actuator_delay,sensor,stochastic));bindings.append({'sensor_routes':list(sensors),'channels':[list(x) if x else None for x in channels],
            'spatial_oracle':spatial,'sensor_delay_evaluator_only':sensor_delay,'actuator_delay_evaluator_only':actuator_delay,'total_lag_oracle':total_lag,
            'channel_oracle':list(inverse(sensors,6)),'sensor_binding':norm_binding(sensor),'stochastic_binding':norm_stochastic(stochastic),
            'gauge_channel_error':gauge_error,'stream_gauge_channel_error':stream_error,'regimes':regimes})
    suite,attempts=lab_suite(201510,4,excluded);conditions={};writes=learner.writes
    for index,(sensors,channels,kinds,spatial,sensor_delay,actuator_delay,sensor,stochastic) in enumerate(interfaces):
        learned=tuple({'transform':x['transform'],'rows':x['rows']} for x in stochastic['gauges']);oracle=({'transform':spatial,'rows':expected_rows(spatial,spatial,channels)},)
        deterministic=gauge_rows(stochastic['gauges'],mode_rows);identity=tuple({'transform':x['transform'],'rows':identity_rows(len(channels))} for x in stochastic['gauges'])
        shuffled=tuple({'transform':x['transform'],'rows':x['rows'][1:]+x['rows'][:1]} for x in stochastic['gauges'])
        policies={name:StochasticGaugePolicy(learner,sensor['mapping'] if name!='oracle' else inverse(sensors,6),len(sensors),rows,len(channels)) for name,rows in
            {'learned':learned,'oracle':oracle,'deterministic':deterministic,'identity':identity,'shuffled':shuffled}.items()}
        result,traces=evaluate_stochastic(policies,suite,sensors,channels,kinds,spatial,sensor_delay,actuator_delay,201710+index,12,96);conditions[str(index)]=result
        bindings[index]['trace_worlds']={name:len(row) for name,row in traces.items()}
    total=lambda name:sum(row[name]['successes'] for row in conditions.values());episodes=sum(row['oracle']['episodes'] for row in conditions.values());per=[]
    for key,row in conditions.items():per.append({'interface':int(key),'episodes':row['oracle']['episodes'],**{name:row[name]['successes'] for name in ('learned','oracle','deterministic','identity','shuffled')}})
    diagnostic={'sensor_exact':sum(x['sensor_binding']['mapping']==x['channel_oracle'] for x in bindings),'lag_exact':sum(x['stochastic_binding']['lag']==x['total_lag_oracle'] for x in bindings),
        'stream_lag_exact':sum(x['lag']==row['total_lag_oracle'] for row in bindings for x in row['stochastic_binding']['per_stream']),
        'maximum_gauge_channel_error':max(x['total_variation'] for row in bindings for x in row['gauge_channel_error']),
        'maximum_stream_gauge_channel_error':max(x['total_variation'] for row in bindings for stream in row['stream_gauge_channel_error'] for x in stream),
        'learned_successes':total('learned'),'oracle_successes':total('oracle'),'deterministic_successes':total('deterministic'),'identity_successes':total('identity'),'shuffled_successes':total('shuffled'),
        'episodes':episodes,'per_interface':per}
    gates={'sensor_exact_3_of_3':diagnostic['sensor_exact']==3,'lag_exact_3_of_3':diagnostic['lag_exact']==3,'all_9_stream_lags_exact':diagnostic['stream_lag_exact']==9,
        'all_gauge_channels_within_12pct_tv':diagnostic['maximum_gauge_channel_error']<=.12,'all_stream_gauge_channels_within_20pct_tv':diagnostic['maximum_stream_gauge_channel_error']<=.20,
        'each_interface_at_least_80pct_oracle':all(x['learned']>=x['oracle']*.8 for x in per),'each_interface_beats_identity_by_5pct':all(x['learned']-x['identity']>=x['episodes']*.05 for x in per),
        'each_interface_beats_shuffled_by_5pct':all(x['learned']-x['shuffled']>=x['episodes']*.05 for x in per),'evaluation_writes_zero':learner.writes==writes}
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),'classifier_dev':{'model':'jev-1.13.0','batch_items':16,
        'selected':'unknown stochastic actuator channel','confidence':.83,'role':'candidate routing only; absent from inference, training, evaluation, and runtime'},
        'reference':{'generator':'original','worlds':300,'interface_digest':reference.digest()},'target':{'generator':'independent rectangular lab','bindings':bindings,'suite':{'worlds':len(suite),'attempts':attempts}},
        'conditions':conditions,'diagnostic':diagnostic,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development-only synthetic stochastic-channel transfer. Useful slots mix four physical directions; structurally inactive nuisance slots are a separate no-effect class. Candidate lag 0-4, D4 family, schema, statistics, generators, terminal events, and backward probability channel are supplied. No neural network, label, reward, planner, runtime search, classifier runtime, or evaluation write is used.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v20stochastic'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
