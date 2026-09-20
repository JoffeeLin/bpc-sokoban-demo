#!/usr/bin/env python3
"""Freeze v0.21 hidden-regime evaluation before holdout execution."""
import hashlib,json
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import infer_relational_support_binding,inverse,lab_distance,lab_suite
from bpc_hidden_mode_v21 import (aligned_error,canonical_hidden_sequences,collect_hidden_interface,
    filter_accuracy,fit_hidden_channels,infer_hidden_lag)
from bpc_stochastic_interface_v20 import effect_profiles
from bpc_three_factor_v12 import train
from experiment_v21_hidden_interface_dev import expected_channels

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v21.json';PROTOCOL=ROOT/'protocol_v21_hidden.json'
SOURCES=('bpc_hidden_mode_v21.py','bpc_stochastic_interface_v20.py','bpc_temporal_interface_v19.py','bpc_spatial_interface_v18.py',
    'bpc_cross_generator_v17.py','bpc_composite_binding_v16.py','bpc_open_interface_v15.py','bpc_three_factor_v12.py','bpc_evidence_field_v11.py',
    'bpc_cross_task_v07.py','bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py','experiment_v21_hidden_frozen.py','freeze_v21_hidden.py')
SENSORS=((None,5,2,None,0,4,None,1,3),(3,None,1,5,None,0,None,4,2,None),(None,0,None,4,2,None,5,3,None,1,None))
KINDS=((3,4,5),(4,5,3,4),(5,3,4,5,3));SPATIAL=(2,4,7);DELAYS=(1,3,4)

def channel(permutation,p=.80):return tuple(tuple(p if action==target else (1-p)/3 for action in range(4)) for target in permutation)
CHANNELS=((channel((0,1,2,3),.80),channel((1,2,3,0),.80)),
    (channel((1,3,0,2),.81),channel((2,0,3,1),.81)),
    (channel((3,2,1,0),.79),channel((0,1,2,3),.79)))
TRANSITIONS=(((.965,.035),(.035,.965)),((.945,.055),(.055,.945)),((.925,.075),(.075,.925)));INITIALS=((.5,.5),)*3
MIXES=({'push':54,'collect':15,'open':15},{'push':15,'collect':54,'open':15},{'push':15,'collect':15,'open':54})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_model(model):return {**model,'initial':list(model['initial']),'transition':[list(x) for x in model['transition']],
    'channels':[[list(x) for x in mode] for mode in model['channels']]}
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}


def calibration(config,learner,reference,triples,reference_support,profiles,excluded):
    out=[]
    for index,(seeds,sensors,kinds,spatial,delay,channels,transition,initial) in enumerate(zip(config['target_seeds'],SENSORS,KINDS,SPATIAL,DELAYS,CHANNELS,TRANSITIONS,INITIALS)):
        targets=[];sequences=[];truth=[]
        for seed,mix in zip(seeds,MIXES):
            stats,flat,episodes,initials,sup,labels=collect_hidden_interface(seed,mix,config['calibration_steps'],sensors,kinds,spatial,delay,channels,transition,initial,excluded)
            excluded|=initials;targets.append((stats,sup,flat));sequences.extend(episodes);truth.extend(labels)
        sensor=infer_relational_support_binding(reference,reference_support,triples,targets);assert sensor['mapping']==inverse(sensors,6)
        lag=infer_hidden_lag(profiles,sequences,sensor['mapping'],len(sensors),0,config['maximum_lag']);assert lag['lag']==delay
        canonical=canonical_hidden_sequences(sequences,sensor['mapping'],len(sensors),0,delay);labels=tuple(row[delay:] for row in truth)
        model=fit_hidden_channels(profiles,canonical,restarts=config['hmm_restarts'],iterations=config['hmm_iterations'],prior=.5,seed=config['fit_seeds'][index])
        alignment=aligned_error(model,expected_channels(spatial,0,channels),transition,initial);accuracy=filter_accuracy(profiles,canonical,labels,model,alignment['model_to_truth'])
        assert alignment['maximum_channel_total_variation']<=.14 and alignment['maximum_transition_error']<=.10 and accuracy>=.78
        out.append({'sensor_oracle':list(inverse(sensors,6)),'sensor_binding':norm_sensor(sensor),'actual_spatial_transform_evaluator_only':spatial,
            'selected_gauge_representative':0,'lag_oracle':delay,'lag_probability_evidence':lag,'learned':norm_model(model),'alignment':alignment,
            'filter_accuracy':accuracy,'calibration_sequences':len(sequences),'calibration_transitions':sum(map(len,canonical))})
    return out,excluded


def main():
    config={'train_seed':123010,'reference_seed':214010,'target_seeds':[[214110+i*10+j for j in range(3)] for i in range(3)],'fit_seeds':[214310,214311,214312],
        'calibration_steps':40,'reference_worlds_per_family':100,'maximum_lag':4,'hmm_restarts':6,'hmm_iterations':30,
        'sensor_routes':[list(x) for x in SENSORS],'distractor_kinds':[list(x) for x in KINDS],'actual_spatial_transforms':list(SPATIAL),
        'actuator_delays':list(DELAYS),'hidden_channels':[[[list(row) for row in mode] for mode in pair] for pair in CHANNELS],
        'hidden_transitions':[[list(row) for row in matrix] for matrix in TRANSITIONS],'hidden_initials':[list(x) for x in INITIALS],
        'target_mixtures':MIXES,'holdout_seed':214510,'worlds_per_family':8,'evaluation_seeds':[214710,214810],'episodes_per_map_per_seed':8,'step_budget':128}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;profiles=effect_profiles(triples);calibrated,excluded=calibration(config,learner,reference,triples,reference_support,profiles,excluded)
    suite,attempts=lab_suite(config['holdout_seed'],config['worlds_per_family'],excluded);worlds=[]
    for family,world,distance in suite:
        assert lab_distance(world,family)==distance
        if family=='joint':assert lab_distance(world,family,True,False) is None and lab_distance(world,family,False,True) is None
        worlds.append({'family':family,**world.__dict__,'shortest':distance})
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds};assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-hidden-v21-holdout','seed':config['holdout_seed'],'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-hidden-v21-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a frozen non-neural BPC controller infer two unlabeled actuator regimes and their switching law, then use only ephemeral Bayesian filtering to control disjoint complex worlds through unseen anonymous sensors, D4 frames, stochastic channels, and delays?',
        'config':config,'development_validation_sha256':sha(ROOT/'artifacts'/'v21hidden'/'interface_validation.json'),
        'rejected_attempt_sha256':{name:sha(ROOT/'artifacts'/'v21hidden'/name/'interface_development.json') for name in ('rejected_attempt1_average_lag','rejected_attempt2_weak_control_margin','rejected_attempt3_long_horizon')},
        'expected_training_events':events,'expected_factor_digest':learner.digest(),'reference_interface_digest':reference.digest(),'reference_support':support(reference_support),
        'reference_effect_digest':profiles.digest(),'expected_calibration':calibrated,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'maximum_channel_total_variation':.14,'maximum_transition_absolute_error':.10,'minimum_filter_accuracy':.78,
            'minimum_oracle_fraction_each_interface':.80,'minimum_overall_memoryless_margin_each_interface':.03,
            'minimum_joint_margin_each_interface':.05},
        'controls':['oracle current hidden mode with true channel in the same D4 gauge','stationary memoryless mixture with the same learned parameters',
            'frozen initial belief with no online update','one-slot-shuffled learned emissions','incorrect zero-lag update','three unseen interface configurations',
            'three channel pairs and switching rates absent from development','actual D4 transforms 2, 4, and 7','delays 1 and 3 absent from development',
            'two evaluation random streams','zero model writes and unchanged digest','disjoint training, calibration, and holdout worlds'],
        'classifier_dev':{'model':'jev-1.13.0','batch_items':6,'selected':'hidden two-state actuator regime with online Bayesian belief','confidence':.98,
            'role':'development route classification only; absent from inference, training, frozen evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace interfaces, modes, transitions, channels, lags, worlds, seeds, sources, controls, or thresholds after held-out execution.',
        'boundary':'Developer-frozen synthetic evidence, not third-party blind and not AGI. Two hidden modes, Markov family, sensor schema, D4 family, lag range 0-4, sufficient statistics, terminal events, and Bayesian recursion are supplied. Mode identities and paths are withheld. No neural network, reward, planner, runtime search, classifier runtime, hidden label, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
