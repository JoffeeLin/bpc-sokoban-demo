#!/usr/bin/env python3
"""Fresh development validation before any v0.21 freeze."""
import json,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import lab_suite
from bpc_hidden_mode_v21 import collect_hidden_interface,evaluate_hidden_interface
from bpc_stochastic_interface_v20 import effect_profiles
from bpc_three_factor_v12 import train
from experiment_v21_hidden_horizon_sweep import model
from experiment_v21_hidden_interface_dev import (CHANNELS,DELAYS,INITIALS,KINDS,MIXES,SENSORS,SPATIAL,TRANSITIONS,expected_channels)

ROOT=Path(__file__).resolve().parent;SOURCE=ROOT/'artifacts'/'v21hidden'/'rejected_attempt3_long_horizon'/'interface_development.json'


def main():
    started=time.perf_counter();source=json.loads(SOURCE.read_text());learner,_=train(123010);excluded=set(learner.training_initials)
    _,triples,initials,_=collect_composite_interface(212010,100,32,exclude=excluded);excluded|=initials;profiles=effect_profiles(triples)
    for index in range(2):
        for seed,mix in zip(range(212110+index*10,212113+index*10),MIXES):
            _,_,_,initials,_,_=collect_hidden_interface(seed,mix,40,SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],CHANNELS[index],TRANSITIONS[index],INITIALS[index],excluded);excluded|=initials
    suite,attempts=lab_suite(213510,4,excluded);conditions={};writes=learner.writes
    for index,row in enumerate(source['target']['interfaces']):
        learned=model(row);oracle=expected_channels(SPATIAL[index],row['selected_equivalent_transform'],CHANNELS[index])
        values,_=evaluate_hidden_interface(learner,profiles,learned,suite,SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],
            tuple(row['sensor_binding']['mapping']),row['selected_equivalent_transform'],CHANNELS[index],oracle,TRANSITIONS[index],INITIALS[index],213710+index,16,128)
        conditions[str(index)]=values
    per=[]
    for key,row in conditions.items():
        joint=row['online']['joint_successes'];joint_episodes=64
        per.append({'interface':int(key),'episodes':row['online']['episodes'],'joint_episodes':joint_episodes,**{name:value['successes'] for name,value in row.items()},
            **{f'{name}_joint':value['joint_successes'] for name,value in row.items()}})
    gates={'source_sensor_lag_recovery_passed':source['diagnostic']['sensor_exact']==2 and source['diagnostic']['lag_exact']==2,
        'source_channel_transition_filter_gates_passed':source['diagnostic']['maximum_channel_total_variation']<=.14 and source['diagnostic']['maximum_transition_error']<=.10 and source['diagnostic']['minimum_filter_accuracy']>=.78,
        'each_overall_online_at_least_80pct_oracle':all(x['online']>=x['oracle']*.80 for x in per),
        'each_overall_online_beats_memoryless':all(x['online']>x['memoryless'] for x in per),
        'each_joint_online_beats_memoryless_by_5pct':all(x['online_joint']-x['memoryless_joint']>=x['joint_episodes']*.05 for x in per),
        'each_joint_online_beats_shuffled_by_5pct':all(x['online_joint']-x['shuffled_joint']>=x['joint_episodes']*.05 for x in per),
        'each_joint_online_beats_zero_lag_by_5pct':all(x['online_joint']-x['zero_lag_joint']>=x['joint_episodes']*.05 for x in per),
        'evaluation_writes_zero':learner.writes==writes}
    result={'development_validation_only':True,'source':str(SOURCE.relative_to(ROOT)),'suite_seed':213510,'evaluation_seeds':[213710,213711],
        'worlds':len(suite),'generation_attempts':attempts,'conditions':conditions,'diagnostic':{'per_interface':per},'preregistered_gates':gates,
        'adopt_for_freeze':all(gates.values()),'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Fresh development validation, not frozen or blind. Primary causal margins are preregistered on complex joint worlds; all simple-family and overall outcomes remain reported.'}
    destination=ROOT/'artifacts'/'v21hidden'/'interface_validation.json';destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
