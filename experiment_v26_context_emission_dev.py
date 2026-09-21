#!/usr/bin/env python3
"""State-conditioned raw-relational emission development experiment."""
import json,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_context_emission_v26 import context_emission
from bpc_cross_generator_v17 import LabWorld
from bpc_hidden_mode_v21 import aligned_error,canonical_hidden_sequences,collect_hidden_interface,filter_accuracy,fit_hidden_channels
from bpc_joint_fit_v25 import evaluate_refit
from bpc_stochastic_interface_v20 import effect_profiles
from bpc_three_factor_v12 import train
from experiment_v21_hidden_horizon_sweep import model
from experiment_v21_hidden_interface_dev import expected_channels
from freeze_v21_hidden import CHANNELS,DELAYS,HOLDOUT,INITIALS,KINDS,MIXES,PROTOCOL,SENSORS,SPATIAL,TRANSITIONS

ROOT=Path(__file__).resolve().parent


def norm(value):return {**value,'initial':list(value['initial']),'transition':[list(x) for x in value['transition']],
    'channels':[[list(x) for x in mode] for mode in value['channels']]}


def main():
    started=time.perf_counter();protocol=json.loads(PROTOCOL.read_text());holdout=json.loads(HOLDOUT.read_text());config=protocol['config'];learner,_=train(config['train_seed']);excluded=set(learner.training_initials)
    _,triples,initials,_=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded);excluded|=initials
    factored=effect_profiles(triples);context=context_emission(triples);models=[];calibration=[]
    for index,row in enumerate(protocol['expected_calibration']):
        sequences=[];truth=[]
        for seed,mix in zip(config['target_seeds'][index],MIXES):
            _,_,episodes,initials,_,labels=collect_hidden_interface(seed,mix,config['calibration_steps'],SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],CHANNELS[index],TRANSITIONS[index],INITIALS[index],excluded)
            excluded|=initials;sequences.extend(episodes);truth.extend(labels)
        mapping=tuple(row['sensor_binding']['mapping']);lag=row['lag_oracle'];canonical=canonical_hidden_sequences(sequences,mapping,len(SENSORS[index]),0,lag);labels=tuple(x[lag:] for x in truth)
        fitted=fit_hidden_channels(context,canonical,restarts=config['hmm_restarts'],iterations=config['hmm_iterations'],prior=.5,seed=220310+index)
        alignment=aligned_error(fitted,expected_channels(SPATIAL[index],0,CHANNELS[index]),TRANSITIONS[index],INITIALS[index]);accuracy=filter_accuracy(context,canonical,labels,fitted,alignment['model_to_truth'])
        models.append(fitted);calibration.append({'context_model':norm(fitted),'alignment':alignment,'filter_accuracy':accuracy})
    suite=[(row['family'],LabWorld(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')]),row['shortest']) for row in holdout['worlds']]
    conditions={};writes=learner.writes
    for index,row in enumerate(protocol['expected_calibration']):
        oracle=expected_channels(SPATIAL[index],row['selected_gauge_representative'],CHANNELS[index])
        values=evaluate_refit(learner,context,factored,models[index],model(row),suite,SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],tuple(row['sensor_binding']['mapping']),
            row['selected_gauge_representative'],CHANNELS[index],oracle,TRANSITIONS[index],INITIALS[index],220710+index,8,128)
        conditions[str(index)]={'context_fit':values['joint_fit'],'factored_fit':values['factored_fit'],'memoryless':values['memoryless'],
            'shuffled':values['shuffled'],'zero_lag':values['zero_lag'],'oracle':values['oracle']}
    per=[]
    for key,row in conditions.items():per.append({'interface':int(key),'episodes':row['context_fit']['episodes'],'complex_episodes':64,
        **{name:value['successes'] for name,value in row.items()},**{f'{name}_complex':value['joint_successes'] for name,value in row.items()}})
    gates={'all_context_channel_error_within_14pct':all(x['alignment']['maximum_channel_total_variation']<=.14 for x in calibration),
        'all_context_transition_error_within_10pct':all(x['alignment']['maximum_transition_error']<=.10 for x in calibration),
        'all_context_filter_accuracy_at_least_78pct':all(x['filter_accuracy']>=.78 for x in calibration),
        'each_context_fit_at_least_factored_fit_overall':all(x['context_fit']>=x['factored_fit'] for x in per),
        'failed_interface_2_context_beats_factored_complex_by_5pct':per[2]['context_fit_complex']-per[2]['factored_fit_complex']>=per[2]['complex_episodes']*.05,
        'failed_interface_2_context_beats_memoryless_complex_by_5pct':per[2]['context_fit_complex']-per[2]['memoryless_complex']>=per[2]['complex_episodes']*.05,
        'each_context_beats_shuffled_complex_by_5pct':all(x['context_fit_complex']-x['shuffled_complex']>=x['complex_episodes']*.05 for x in per),'evaluation_writes_zero':learner.writes==writes}
    result={'development_only':True,'v21_frozen_result_was_non_adopted':True,
        'mechanism':'D4-shared RelationalBPC learns P(raw change|raw context,action); a joint category learns P(effect|change,action)',
        'context_digest':context.digest(),'calibration':calibration,'conditions':conditions,'diagnostic':{'per_interface':per},'preregistered_gates':gates,
        'adopt_for_v26_freeze':all(gates.values()),'classifier_dev':{'model':'jev-1.13.0','selected':'raw-relational context-conditioned change emission','confidence':.93,'role':'route classification only'},
        'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development reuse of the already-observed failed v0.21 calibration and holdout; raw relations only, no semantic labels or rules; never frozen evidence.'}
    destination=ROOT/'artifacts'/'v26context'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
