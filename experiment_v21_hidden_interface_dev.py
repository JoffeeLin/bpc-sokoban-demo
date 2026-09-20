#!/usr/bin/env python3
"""Development: hidden actuator regimes plus anonymous sensors, D4, and lag."""
import json,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import infer_relational_support_binding,inverse,lab_suite
from bpc_hidden_mode_v21 import (aligned_error,canonical_hidden_sequences,collect_hidden_interface,
    evaluate_hidden_interface,filter_accuracy,fit_hidden_channels,infer_hidden_lag)
from bpc_spatial_interface_v18 import transformed_delta
from bpc_stochastic_interface_v20 import effect_profiles
from bpc_three_factor_v12 import train

SENSORS=((4,None,0,2,None,5,3,None,1),(None,2,4,1,None,3,None,5,0,None))
KINDS=((0,1,2),(2,0,1,2));SPATIAL=(1,6);DELAYS=(2,4)
CHANNELS=(
    (((.82,.06,.06,.06),(.06,.82,.06,.06),(.06,.06,.82,.06),(.06,.06,.06,.82)),
     ((.06,.82,.06,.06),(.82,.06,.06,.06),(.06,.06,.06,.82),(.06,.06,.82,.06))),
    (((.06,.82,.06,.06),(.82,.06,.06,.06),(.06,.06,.06,.82),(.06,.06,.82,.06)),
     ((.06,.06,.82,.06),(.06,.06,.06,.82),(.82,.06,.06,.06),(.06,.82,.06,.06))))
TRANSITIONS=(((.97,.03),(.03,.97)),((.94,.06),(.06,.94)))
INITIALS=((.5,.5),(.5,.5))
MIXES=({'push':54,'collect':15,'open':15},{'push':15,'collect':54,'open':15},{'push':15,'collect':15,'open':54})


def expected_channels(actual,candidate,modes):
    out=[]
    for mode in modes:
        rows=[]
        for row in mode:
            values=[]
            for action in range(4):
                delta=transformed_delta(candidate,action);physical=next(x for x in range(4) if transformed_delta(actual,x)==delta);values.append(row[physical])
            rows.append(tuple(values))
        out.append(tuple(rows))
    return tuple(out)


def norm_model(model):return {**model,'initial':list(model['initial']),'transition':[list(x) for x in model['transition']],
    'channels':[[list(x) for x in mode] for mode in model['channels']]}
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}


def main():
    started=time.perf_counter();learner,training=train(123010);excluded=set(learner.training_initials)
    reference,triples,initials,reference_support=collect_composite_interface(212010,100,32,exclude=excluded);excluded|=initials;profiles=effect_profiles(triples);interfaces=[];records=[]
    for index,(sensors,kinds,spatial,delay,channels,transition,initial) in enumerate(zip(SENSORS,KINDS,SPATIAL,DELAYS,CHANNELS,TRANSITIONS,INITIALS)):
        targets=[];sequences=[];truth=[];stream_rows=[]
        for seed,mix in zip(range(212110+index*10,212113+index*10),MIXES):
            stats,flat,episodes,initials,support,labels=collect_hidden_interface(seed,mix,40,sensors,kinds,spatial,delay,channels,transition,initial,excluded);excluded|=initials
            targets.append((stats,support,flat));sequences.extend(episodes);truth.extend(labels);stream_rows.append(episodes)
        sensor=infer_relational_support_binding(reference,reference_support,triples,targets)
        # D4 is an observational gauge: choose representative zero and learn the
        # actuator rows in that same frame.  Preserve hidden-mode dependence when
        # comparing lags instead of first collapsing it into one average channel.
        transform=0;lag_row=infer_hidden_lag(profiles,sequences,sensor['mapping'],len(sensors),transform);lag=lag_row['lag']
        canonical=canonical_hidden_sequences(sequences,sensor['mapping'],len(sensors),transform,lag);aligned_truth=tuple(row[lag:] for row in truth)
        model=fit_hidden_channels(profiles,canonical,restarts=6,iterations=30,prior=.5,seed=212310+index);oracle=expected_channels(spatial,transform,channels)
        alignment=aligned_error(model,oracle,transition,initial);accuracy=filter_accuracy(profiles,canonical,aligned_truth,model,alignment['model_to_truth'])
        interfaces.append((sensors,kinds,spatial,delay,channels,transition,initial,sensor,transform,model,oracle));records.append({'sensor_oracle':list(inverse(sensors,6)),
            'sensor_binding':norm_sensor(sensor),'spatial_oracle':spatial,'selected_equivalent_transform':transform,'lag_oracle':delay,'selected_lag':lag,
            'lag_probability_evidence':lag_row,'learned':norm_model(model),'alignment':alignment,'filter_accuracy':accuracy,
            'calibration_sequences':len(sequences),'calibration_transitions':sum(map(len,canonical))})
    suite,attempts=lab_suite(212510,4,excluded);conditions={};writes=learner.writes
    for index,(sensors,kinds,spatial,delay,channels,transition,initial,sensor,transform,model,oracle) in enumerate(interfaces):
        rows,traces=evaluate_hidden_interface(learner,profiles,model,suite,sensors,kinds,spatial,delay,sensor['mapping'],transform,channels,oracle,transition,initial,212710+index,16,128)
        conditions[str(index)]=rows;records[index]['trace_worlds']={name:len(row) for name,row in traces.items()}
    per=[]
    for key,row in conditions.items():per.append({'interface':int(key),'episodes':row['online']['episodes'],**{name:row[name]['successes'] for name in row}})
    diagnostic={'sensor_exact':sum(row['sensor_binding']['mapping']==row['sensor_oracle'] for row in records),'lag_exact':sum(row['selected_lag']==row['lag_oracle'] for row in records),
        'maximum_channel_total_variation':max(row['alignment']['maximum_channel_total_variation'] for row in records),
        'maximum_transition_error':max(row['alignment']['maximum_transition_error'] for row in records),'minimum_filter_accuracy':min(row['filter_accuracy'] for row in records),'per_interface':per}
    gates={'sensor_exact_2_of_2':diagnostic['sensor_exact']==2,'lag_exact_2_of_2':diagnostic['lag_exact']==2,
        'all_channels_within_14pct_tv':diagnostic['maximum_channel_total_variation']<=.14,'all_transitions_within_10pct':diagnostic['maximum_transition_error']<=.10,
        'all_filter_accuracy_at_least_78pct':diagnostic['minimum_filter_accuracy']>=.78,
        'each_online_at_least_78pct_oracle':all(x['online']>=x['oracle']*.78 for x in per),
        'each_online_beats_memoryless_by_5pct':all(x['online']-x['memoryless']>=x['episodes']*.05 for x in per),
        'each_online_beats_shuffled_by_5pct':all(x['online']-x['shuffled']>=x['episodes']*.05 for x in per),
        'each_online_beats_zero_lag_by_5pct':all(x['online']-x['zero_lag']>=x['episodes']*.05 for x in per),'evaluation_writes_zero':learner.writes==writes}
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),'reference':{'generator':'original','worlds':300,'interface_digest':reference.digest(),'effect_digest':profiles.digest()},
        'target':{'generator':'independent rectangular lab','interfaces':records,'suite_worlds':len(suite),'generation_attempts':attempts},'conditions':conditions,
        'diagnostic':diagnostic,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),'evaluation_writes':learner.writes-writes,
        'classifier_dev':{'model':'jev-1.13.0','batch_items':6,'selected':'hidden two-state actuator regime with online Bayesian belief','confidence':.98,
            'role':'route classification only; absent from inference, training, evaluation, and runtime'},'seconds':time.perf_counter()-started,
        'boundary':'Development-only synthetic transfer, not frozen, third-party blind, or AGI. Hidden mode identities and paths are withheld. Sensor schema, two-state Markov family, D4 family, lag range 0-4, statistics, terminal events, and Bayesian recursion are supplied. No neural network, reward, planner, runtime search, classifier runtime, hidden label, or evaluation write is used.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v21hidden'/'interface_development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
