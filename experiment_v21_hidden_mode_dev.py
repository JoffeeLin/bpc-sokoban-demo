#!/usr/bin/env python3
"""Development-only hidden Markov actuator-regime experiment."""
import json,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import lab_suite
from bpc_hidden_mode_v21 import (aligned_error,collect_hidden,evaluate_hidden,filter_accuracy,
    fit_hidden_channels)
from bpc_stochastic_interface_v20 import effect_profiles
from bpc_three_factor_v12 import train

CHANNELS=(
    ((.82,.06,.06,.06),(.06,.82,.06,.06),(.06,.06,.82,.06),(.06,.06,.06,.82)),
    ((.06,.82,.06,.06),(.82,.06,.06,.06),(.06,.06,.06,.82),(.06,.06,.82,.06)))
TRANSITION=((.95,.05),(.07,.93));INITIAL=(.55,.45)
MIXES=({'push':72,'collect':18,'open':18},{'push':18,'collect':72,'open':18},{'push':18,'collect':18,'open':72})


def norm_model(model):return {**model,'initial':list(model['initial']),'transition':[list(x) for x in model['transition']],
    'channels':[[list(x) for x in mode] for mode in model['channels']]}


def main():
    started=time.perf_counter();learner,training=train(123010);excluded=set(learner.training_initials)
    reference,triples,initials,_=collect_composite_interface(211010,100,32,exclude=excluded);excluded|=initials;profiles=effect_profiles(triples)
    sequences=[];truth=[];streams=[]
    for seed,mix in zip((211110,211111,211112),MIXES):
        rows,initials,labels=collect_hidden(seed,mix,48,CHANNELS,TRANSITION,INITIAL,excluded);excluded|=initials
        sequences.extend(rows);truth.extend(labels);streams.append({'seed':seed,'sequences':len(rows),'transitions':sum(map(len,rows))})
    model=fit_hidden_channels(profiles,sequences,restarts=10,iterations=40,prior=.5,seed=211310);alignment=aligned_error(model,CHANNELS,TRANSITION,INITIAL)
    accuracy=filter_accuracy(profiles,sequences,truth,model,alignment['model_to_truth']);suite,attempts=lab_suite(211510,5,excluded);writes=learner.writes
    conditions,traces=evaluate_hidden(learner,profiles,model,suite,CHANNELS,TRANSITION,INITIAL,211710,18,128)
    diagnostic={**alignment,'filter_accuracy':accuracy,'episodes':conditions['online']['episodes'],
        **{f'{name}_successes':row['successes'] for name,row in conditions.items()},'trace_worlds':{name:len(row) for name,row in traces.items()}}
    gates={'channel_recovery_within_12pct_tv':alignment['maximum_channel_total_variation']<=.12,
        'transition_recovery_within_8pct':alignment['maximum_transition_error']<=.08,'filter_accuracy_at_least_80pct':accuracy>=.80,
        'online_at_least_80pct_oracle':diagnostic['online_successes']>=diagnostic['oracle_successes']*.80,
        'online_beats_memoryless_by_5pct':diagnostic['online_successes']-diagnostic['memoryless_successes']>=diagnostic['episodes']*.05,
        'online_beats_no_update_by_5pct':diagnostic['online_successes']-diagnostic['no_update_successes']>=diagnostic['episodes']*.05,
        'online_beats_shuffled_by_5pct':diagnostic['online_successes']-diagnostic['shuffled_successes']>=diagnostic['episodes']*.05,
        'evaluation_writes_zero':learner.writes==writes}
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),'reference':{'generator':'original','worlds':300,'effect_digest':profiles.digest()},
        'target':{'generator':'independent rectangular lab','hidden_modes':2,'unlabeled_streams':streams,'suite_worlds':len(suite),'generation_attempts':attempts,
            'evaluator_only_channels':CHANNELS,'evaluator_only_transition':TRANSITION,'evaluator_only_initial':INITIAL},'learned':norm_model(model),'conditions':conditions,
        'diagnostic':diagnostic,'preregistered_gates':gates,'adopt_for_interface_integration':all(gates.values()),'evaluation_writes':learner.writes-writes,
        'classifier_dev':{'model':'jev-1.13.0','batch_items':6,'selected':'hidden two-state actuator regime with online Bayesian belief','confidence':.98,
            'role':'development route classification only; absent from inference, training, evaluation, and runtime'},'seconds':time.perf_counter()-started,
        'boundary':'Development-only synthetic hidden-regime evidence, not frozen, third-party blind, or AGI. Two modes and the Markov family are supplied, but mode identities and paths are withheld from fitting and control. The controller uses frozen BPC action probabilities plus learned actuator probabilities and an ephemeral Bayesian belief. No neural network, reward, planner, search, hidden label, classifier runtime, or evaluation write is used.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v21hidden'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
