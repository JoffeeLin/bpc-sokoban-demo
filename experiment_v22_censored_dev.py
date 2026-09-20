#!/usr/bin/env python3
"""Post-v0.21-failure development probe on all failed-holdout interfaces."""
import json,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import LabWorld
from bpc_censored_filter_v22 import evaluate_censored
from bpc_stochastic_interface_v20 import effect_profiles
from bpc_three_factor_v12 import train
from experiment_v21_hidden_horizon_sweep import model
from experiment_v21_hidden_interface_dev import expected_channels
from freeze_v21_hidden import CHANNELS,DELAYS,HOLDOUT,INITIALS,KINDS,PROTOCOL,SENSORS,SPATIAL,TRANSITIONS

ROOT=Path(__file__).resolve().parent


def main():
    started=time.perf_counter();protocol=json.loads(PROTOCOL.read_text());holdout=json.loads(HOLDOUT.read_text());config=protocol['config'];learner,_=train(config['train_seed']);excluded=set(learner.training_initials)
    _,triples,_,_=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded);profiles=effect_profiles(triples)
    suite=[(row['family'],LabWorld(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')]),row['shortest']) for row in holdout['worlds']]
    conditions={};writes=learner.writes
    for index,row in enumerate(protocol['expected_calibration']):
        learned=model(row);oracle=expected_channels(SPATIAL[index],row['selected_gauge_representative'],CHANNELS[index])
        conditions[str(index)]=evaluate_censored(learner,profiles,learned,suite,SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],tuple(row['sensor_binding']['mapping']),
            row['selected_gauge_representative'],CHANNELS[index],oracle,TRANSITIONS[index],INITIALS[index],215010+index,8,128)
    per=[]
    for key,row in conditions.items():per.append({'interface':int(key),'episodes':row['censored']['episodes'],'joint_episodes':64,
        **{name:value['successes'] for name,value in row.items()},**{f'{name}_joint':value['joint_successes'] for name,value in row.items()}})
    gates={'each_censored_at_least_original_overall':all(x['censored']>=x['original'] for x in per),
        'failed_interface_2_censored_beats_original_joint_by_5pct':per[2]['censored_joint']-per[2]['original_joint']>=per[2]['joint_episodes']*.05,
        'failed_interface_2_censored_beats_memoryless_joint_by_5pct':per[2]['censored_joint']-per[2]['memoryless_joint']>=per[2]['joint_episodes']*.05,
        'each_censored_beats_shuffled_joint_by_5pct':all(x['censored_joint']-x['shuffled_joint']>=x['joint_episodes']*.05 for x in per),
        'evaluation_writes_zero':learner.writes==writes}
    result={'development_only':True,'v21_frozen_result_was_non_adopted':True,'mechanism':'raw canonical no-change transitions are missing emissions; Markov time still advances',
        'conditions':conditions,'diagnostic':{'per_interface':per},'preregistered_gates':gates,'adopt_for_v22_freeze':all(gates.values()),
        'classifier_dev':{'model':'jev-1.13.0','selected':'censor non-identifiable no-change emissions','confidence':.85,'role':'route classification only'},
        'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,'boundary':'Development reuse of the already-observed failed v0.21 holdout; never frozen evidence.'}
    destination=ROOT/'artifacts'/'v22censored'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
