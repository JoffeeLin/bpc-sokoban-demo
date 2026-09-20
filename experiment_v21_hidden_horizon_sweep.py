#!/usr/bin/env python3
"""Development-only horizon sensitivity; never used as frozen evidence."""
import json,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import lab_suite
from bpc_hidden_mode_v21 import collect_hidden_interface,evaluate_hidden_interface
from bpc_stochastic_interface_v20 import effect_profiles
from bpc_three_factor_v12 import train
from experiment_v21_hidden_interface_dev import CHANNELS,DELAYS,INITIALS,KINDS,MIXES,SENSORS,SPATIAL,TRANSITIONS,expected_channels

ROOT=Path(__file__).resolve().parent;SOURCE=ROOT/'artifacts'/'v21hidden'/'rejected_attempt3_long_horizon'/'interface_development.json'


def model(row):
    value=row['learned'];return {'log_probability':value['log_probability'],'initial':tuple(value['initial']),
        'transition':tuple(map(tuple,value['transition'])),'channels':tuple(tuple(map(tuple,mode)) for mode in value['channels'])}


def main():
    started=time.perf_counter();source=json.loads(SOURCE.read_text());learner,_=train(123010);excluded=set(learner.training_initials)
    _,triples,initials,_=collect_composite_interface(212010,100,32,exclude=excluded);excluded|=initials;profiles=effect_profiles(triples)
    for index in range(2):
        for seed,mix in zip(range(212110+index*10,212113+index*10),MIXES):
            _,_,_,initials,_,_=collect_hidden_interface(seed,mix,40,SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],CHANNELS[index],TRANSITIONS[index],INITIALS[index],excluded);excluded|=initials
    suite,_=lab_suite(212510,4,excluded);out={}
    for steps in (48,64,80,96,112,128):
        per=[]
        for index,row in enumerate(source['target']['interfaces']):
            learned=model(row);oracle_channels=expected_channels(SPATIAL[index],row['selected_equivalent_transform'],CHANNELS[index])
            rows,_=evaluate_hidden_interface(learner,profiles,learned,suite,SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],
                tuple(row['sensor_binding']['mapping']),row['selected_equivalent_transform'],CHANNELS[index],oracle_channels,TRANSITIONS[index],INITIALS[index],213000+index,16,steps)
            per.append({name:value['successes'] for name,value in rows.items()})
        out[str(steps)]=per
    result={'development_only':True,'source':str(SOURCE.relative_to(ROOT)),'episodes_per_interface':256,'horizons':out,'seconds':time.perf_counter()-started,
        'boundary':'Post-development horizon sensitivity only. It cannot validate or replace a frozen result. The committed script fixes an oracle-frame bug found after the saved sweep; the saved oracle rows are invalid and unused.'}
    destination=ROOT/'artifacts'/'v21hidden'/'horizon_sweep.json';destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
