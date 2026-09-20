#!/usr/bin/env python3
"""Freeze v0.17 cross-generator, held-out-family, variable-I/O evaluation."""
import hashlib,json
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import (collect_variable,infer_relational_support_binding,inverse,lab_distance,lab_suite)
from bpc_open_interface_v15 import action_stats,infer_action_subset
from bpc_three_factor_v12 import train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v17.json';PROTOCOL=ROOT/'protocol_v17_cross_generator.json'
SOURCES=('bpc_cross_generator_v17.py','bpc_composite_binding_v16.py','bpc_open_interface_v15.py','bpc_three_factor_v12.py',
    'bpc_evidence_field_v11.py','bpc_cross_task_v07.py','bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py',
    'experiment_v17_cross_generator_frozen.py','freeze_v17_cross_generator.py')
SENSORS=((None,5,2,None,0,4,None,1,3),(3,None,0,5,None,2,4,None,1,None),
    (None,4,1,None,5,3,None,0,None,2,None),(2,None,5,None,1,4,None,None,0,3,None,None))
ACTIONS=((2,0,None,1,3),(None,3,0,None,2,1),(1,None,2,None,0,3,None),(None,2,0,None,3,None,1,None))
KINDS=((3,4,5),(5,3,4,5),(4,5,3,4,5),(3,5,4,3,5,4))
MIXES=({'push':126,'collect':27,'open':27},{'push':27,'collect':126,'open':27},
    {'push':27,'collect':27,'open':126},{'push':60,'collect':60,'open':60})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_action(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'candidate_slots':list(row['candidate_slots'])}


def main():
    config={'train_seed':121010,'reference_seed':172010,'target_seeds':[[172110+i*10+j for j in range(4)] for i in range(4)],
        'calibration_steps':32,'reference_worlds_per_family':100,'sensor_routes':[list(x) for x in SENSORS],
        'action_routes':[list(x) for x in ACTIONS],'distractor_kinds':[list(x) for x in KINDS],'target_mixtures':MIXES,
        'holdout_seed':172510,'worlds_per_family':12,'eval_seeds':[172610,172710],
        'episodes_per_map':24,'step_budget':64,'random_binding_seed':172810}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;reference_actions=action_stats(reference_triples,range(6),6,4);calibration=[]
    for seeds,sensors,actions,kinds in zip(config['target_seeds'],SENSORS,ACTIONS,KINDS):
        targets=[];triples=[];regimes=[]
        for seed,mix in zip(seeds,MIXES):
            target,row,initials,target_support=collect_variable(seed,mix,config['calibration_steps'],sensors,actions,kinds,excluded)
            excluded|=initials;targets.append((target,target_support,row));triples.extend(row)
            regimes.append({'interface_digest':target.digest(),'support':support(target_support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets);oracle=inverse(sensors,6)
        assert channel.get('mapping')==oracle and all(x['mapping']==oracle for x in channel['per_stream'])
        target_actions=action_stats(triples,channel['mapping'],len(sensors),len(actions));action=infer_action_subset(reference_actions,target_actions);action_oracle=inverse(actions,4)
        assert action['mapping']==action_oracle and set(action['candidate_slots'])==set(action_oracle)
        calibration.append({'regimes':regimes,'channel_oracle':list(oracle),'channel_binding':norm_sensor(channel),
            'action_oracle':list(action_oracle),'action_binding':norm_action(action),'target_action_digest':target_actions.digest()})
    suite,attempts=lab_suite(config['holdout_seed'],config['worlds_per_family'],excluded)
    worlds=[]
    for family,world,distance in suite:
        assert lab_distance(world,family)==distance
        if family=='joint':assert lab_distance(world,family,True,False) is None and lab_distance(world,family,False,True) is None
        worlds.append({'family':family,**world.__dict__,'shortest':distance})
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds}
    assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-cross-generator-v17-holdout','seed':config['holdout_seed'],
        'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-cross-generator-v17-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can the frozen non-neural BPC controller transfer from its original square-map generator to an independently implemented rectangular-map physics generator while simultaneously inferring four unseen variable-width interfaces containing held-out composite sensor families and non-null nuisance actuators, using only unlabeled transition and anonymous same-cell conditional probabilities?',
        'config':config,'expected_training_events':events,'expected_factor_digest':learner.digest(),
        'reference_interface_digest':reference.digest(),'reference_support':support(reference_support),'reference_action_digest':reference_actions.digest(),
        'expected_calibration':calibration,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'minimum_compatible_mappings':2,'maximum_compatible_mappings':32,'combined_sensor_log_margin':8000.,
            'per_stream_sensor_log_margin':800.,'action_log_margin':20000.,'joint_rate':.55,
            'sensor_only_joint_margin':.45,'action_only_joint_margin':.40,'identity_joint_margin':.45,'random_joint_margin':.40},
        'controls':['oracle bindings over the same frozen policy and independent-generator worlds','learned sensors with first four action slots',
            'first six sensors with learned actions','first-slot identity binding','fixed random bindings','four variable-width unseen interfaces',
            'held-out distractor formulas 3/4/5 after development used only 0/1/2','non-null nuisance actions alter extra sensor planes',
            'four independently sampled unlabeled regimes per interface','two evaluation action seeds','zero model writes','disjoint training, calibration, and holdout initial worlds'],
        'classifier_dev':{'model':'jev-1.13.0','chosen_proposal':'cross-generator transfer','confidence':.73,
            'secondary_proposal':'held-out distractor-family transfer','secondary_confidence':.66,
            'role':'development route classification only; absent from inference, policy training, frozen evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace formula families, interfaces, generators, worlds, seeds, sources, controls, or thresholds after holdout execution.',
        'boundary':'Developer-frozen synthetic cross-generator transfer. Canonical semantics, six raw planes, four actions, maximum 7x7 canvas, distractor-family code, support-equality rule, same-cell conditional probability statistic, four calibration schedules, generators, terminal events, and direct policy remain supplied. No neural network, task label, reward, planner, search, classifier runtime, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
