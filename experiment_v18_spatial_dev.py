#!/usr/bin/env python3
"""Development-only D4 spatial-frame plus variable-interface experiment."""
import json,random,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import (infer_relational_support_binding,inverse,lab_suite)
from bpc_open_interface_v15 import action_stats
from bpc_spatial_interface_v18 import (GaugeAveragedPolicy,SpatialBoundPolicy,collect_spatial,evaluate_spatial,
    gauge_equivalent_mapping,infer_spatial_action,infer_spatial_gauges)
from bpc_three_factor_v12 import train

SENSORS=((4,None,0,2,None,5,3,None,1),(None,2,4,1,None,3,None,5,0,None),(5,None,3,None,0,1,None,None,2,4,None))
ACTIONS=((None,3,1,0,2),(0,None,2,None,1,3,None),(None,1,3,None,2,None,0,None))
KINDS=((0,1,2),(2,0,1,2),(1,2,0,1,2));SPATIAL=(1,4,7)
MIXES=({'push':126,'collect':27,'open':27},{'push':27,'collect':126,'open':27},{'push':27,'collect':27,'open':126},{'push':60,'collect':60,'open':60})


def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_spatial(row):return {**row,'mapping':list(row['mapping']),'second':{**row['second'],'mapping':list(row['second']['mapping'])},'candidate_slots':list(row['candidate_slots']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_gauge(row):return {**row,'mapping':list(row['mapping']),'candidate_slots':list(row['candidate_slots']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}


def main():
    started=time.perf_counter();learner,training=train(121010);excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(181010,100,32,exclude=excluded);excluded|=initials;reference_actions=action_stats(reference_triples,range(6),6,4)
    bindings=[];interfaces=[]
    for index,(sensors,actions,kinds,spatial) in enumerate(zip(SENSORS,ACTIONS,KINDS,SPATIAL)):
        targets=[];triples=[];streams=[];regimes=[]
        for regime,(seed,mix) in enumerate(zip(range(181110+index*10,181114+index*10),MIXES)):
            target,row,initials,support=collect_spatial(seed,mix,32,sensors,actions,kinds,spatial,excluded);excluded|=initials
            targets.append((target,support,row));triples.extend(row);streams.append(row);regimes.append({'digest':target.digest(),'support_size':len(support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets)
        spatial_action=infer_spatial_action(reference_actions,triples,channel['mapping'],len(sensors),len(actions),streams)
        gauges=infer_spatial_gauges(reference_actions,triples,channel['mapping'],len(sensors),len(actions),streams)
        oracle_actions=inverse(actions,4);equivalence=[{'transform':row['transform'],'expected':list(gauge_equivalent_mapping(spatial,row['transform'],oracle_actions)),
            'learned':list(row['mapping']),'exact':row['mapping']==gauge_equivalent_mapping(spatial,row['transform'],oracle_actions)} for row in gauges]
        interfaces.append((sensors,actions,kinds,spatial,channel,spatial_action,gauges));bindings.append({'sensor_routes':list(sensors),'action_routes':list(actions),'kinds':list(kinds),
            'spatial_oracle':spatial,'channel_oracle':list(inverse(sensors,6)),'channel_binding':norm_sensor(channel),'action_oracle':list(inverse(actions,4)),
            'spatial_action_binding':norm_spatial(spatial_action),'gauge_bindings':[norm_gauge(row) for row in gauges],
            'gauge_equivalence':equivalence,'regimes':regimes})
    suite,attempts=lab_suite(181510,8,excluded);conditions={};writes=learner.writes;rng=random.Random(181610)
    for index,(sensors,actions,kinds,spatial,channel,binding,gauges) in enumerate(interfaces):
        oracle_channels=inverse(sensors,6);oracle_actions=inverse(actions,4);random_channels=rng.sample(range(len(sensors)),6);random_actions=rng.sample(range(len(actions)),4);random_spatial=rng.randrange(8)
        policy=lambda channels,frame,act:SpatialBoundPolicy(learner,channels,len(sensors),frame,act,len(actions))
        hypotheses=[(row['transform'],row['mapping']) for row in gauges];shuffled=[(row['transform'],gauges[(i+1)%len(gauges)]['mapping']) for i,row in enumerate(gauges)]
        policies={'gauge_average':GaugeAveragedPolicy(learner,channel['mapping'],len(sensors),hypotheses,len(actions)),
            'shuffled_gauge':GaugeAveragedPolicy(learner,channel['mapping'],len(sensors),shuffled,len(actions)),
            'ml_single':policy(channel['mapping'],binding['transform'],binding['mapping']),'oracle':policy(oracle_channels,spatial,oracle_actions),
            'no_spatial':policy(channel['mapping'],0,binding['mapping']),'sensor_spatial_only':policy(channel['mapping'],binding['transform'],range(4)),
            'action_spatial_only':policy(range(6),binding['transform'],binding['mapping']),'identity':policy(range(6),0,range(4)),
            'random':policy(random_channels,random_spatial,random_actions)}
        result,traces=evaluate_spatial(policies,suite,sensors,actions,kinds,spatial,181710+index,24,64);conditions[str(index)]=result
        bindings[index]['random_channels']=random_channels;bindings[index]['random_actions']=random_actions;bindings[index]['random_spatial']=random_spatial;bindings[index]['trace_worlds']={name:len(x) for name,x in traces.items()}
    total=lambda name:sum(row[name]['successes'] for row in conditions.values());episodes=sum(row['oracle']['episodes'] for row in conditions.values())
    diagnostic={'channel_exact':sum(row['channel_binding']['mapping']==row['channel_oracle'] for row in bindings),
        'gauge_pairs_exact':sum(item['exact'] for row in bindings for item in row['gauge_equivalence']),
        'gauge_average_successes':total('gauge_average'),'oracle_successes':total('oracle'),'ml_single_successes':total('ml_single'),
        'shuffled_gauge_successes':total('shuffled_gauge'),'no_spatial_successes':total('no_spatial'),'episodes':episodes}
    # Fixed before this development run; do not relax after seeing results.
    gates={'channel_exact_3_of_3':diagnostic['channel_exact']==3,'gauge_pairs_exact_24_of_24':diagnostic['gauge_pairs_exact']==24,
        'gauge_average_at_least_80pct_oracle':diagnostic['gauge_average_successes']*5>=diagnostic['oracle_successes']*4,
        'gauge_average_beats_shuffled_by_5pct_episodes':diagnostic['gauge_average_successes']-diagnostic['shuffled_gauge_successes']>=episodes*.05,
        'gauge_average_beats_no_spatial_by_5pct_episodes':diagnostic['gauge_average_successes']-diagnostic['no_spatial_successes']>=episodes*.05}
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'classifier_dev':{'model':'jev-1.13.0','chosen_proposal':'D4 spatial transform from anonymous displacement probabilities','confidence':.64,'role':'candidate routing only; absent from inference, training, evaluation, and runtime'},
        'reference':{'generator':'original','worlds':300,'interface_digest':reference.digest(),'action_digest':reference_actions.digest()},
        'target':{'generator':'independent rectangular lab','bindings':bindings,'suite':{'worlds':len(suite),'attempts':attempts}},
        'conditions':conditions,'diagnostic':diagnostic,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),
        'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development-only synthetic D4 gauge-action binding and direct probability averaging. Absolute orientation is unidentifiable because action slots are also anonymous; oracle geometry is evaluator-only. D4 family, canonical schema, maximum canvas, statistics, generators, terminal events, and policy remain supplied. No neural network, label, reward, planner, runtime search, classifier runtime, or evaluation write is used.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v18spatial'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
