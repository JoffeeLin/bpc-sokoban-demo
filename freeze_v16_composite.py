#!/usr/bin/env python3
"""Freeze v0.16 composite-distractor calibration and unseen holdout."""
import hashlib,json
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface,infer_support_binding
from bpc_open_interface_v15 import action_stats,infer_action_subset,inverse_subset
from bpc_three_factor_v12 import generate_suite,train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v16.json';PROTOCOL=ROOT/'protocol_v16_composite.json'
SOURCES=('bpc_composite_binding_v16.py','bpc_open_interface_v15.py','bpc_three_factor_v12.py','bpc_evidence_field_v11.py',
    'bpc_cross_task_v07.py','bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py',
    'experiment_v16_composite_frozen.py','freeze_v16_composite.py')
SENSORS=((2,None,5,1,4,0,None,3),(None,0,3,5,1,None,4,2),(4,1,None,2,0,3,5,None),(3,5,2,None,None,4,0,1))
ACTUATORS=((2,0,None,1,None,3),(None,3,0,2,1,None),(1,None,2,3,None,0),(3,1,None,None,2,0))
MIXES=({'push':210,'collect':45,'open':45},{'push':45,'collect':210,'open':45},
       {'push':45,'collect':45,'open':210},{'push':100,'collect':100,'open':100})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):
    return {**row,'mapping':list(row['mapping']),'second':list(row['second']),
        'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_action(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'candidate_slots':list(row['candidate_slots'])}


def main():
    config={'train_seed':121010,'reference_seed':162010,'target_seeds':[[162110+i*10+j for j in range(4)] for i in range(4)],
        'calibration_steps':32,'reference_worlds_per_family':100,'sensor_routes':[list(x) for x in SENSORS],
        'actuator_routes':[list(x) for x in ACTUATORS],'target_mixtures':MIXES,
        'holdout_seed':162510,'worlds_per_family':12,'eval_seeds':[162610,162710],
        'episodes_per_map':24,'step_budget':64,'random_binding_seed':162810}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;reference_actions=action_stats(reference_triples,range(6),6,4);calibration=[]
    for seeds,sensors,actuators in zip(config['target_seeds'],SENSORS,ACTUATORS):
        targets=[];triples=[];regimes=[]
        for seed,mix in zip(seeds,MIXES):
            target,row,initials,target_support=collect_composite_interface(seed,mix,config['calibration_steps'],sensors,actuators,excluded)
            excluded|=initials;targets.append((target,target_support));triples.extend(row)
            regimes.append({'interface_digest':target.digest(),'support':support(target_support)})
        channel=infer_support_binding(reference,reference_support,targets)
        target_actions=action_stats(triples,channel['mapping'],len(sensors),len(actuators));action=infer_action_subset(reference_actions,target_actions)
        calibration.append({'regimes':regimes,'channel_oracle':list(inverse_subset(sensors,6)),'channel_binding':norm_sensor(channel),
            'action_oracle':list(inverse_subset(actuators,4)),'action_binding':norm_action(action),'target_action_digest':target_actions.digest()})
    suite,attempts=generate_suite(config['holdout_seed'],config['worlds_per_family'],excluded)
    worlds=[{'family':family,'h':world.h,'w':world.w,'walls':world.walls,'agent':world.agent,'objects':world.objects,
        'marks':world.marks,'switches':world.switches,'gates':world.gates,'shortest':distance} for family,world,distance in suite]
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds}
    assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-composite-binding-v16-holdout','seed':config['holdout_seed'],
        'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-composite-binding-v16-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a frozen non-neural BPC policy identify its canonical six-sensor/four-action interface inside simultaneous unseen eight-channel/six-slot interfaces whose two nuisance planes are displaced XOR compositions of canonical mechanisms, using transition-support invariance and probabilities across four separately sampled unlabeled calibration regimes?',
        'config':config,'expected_training_events':events,'expected_factor_digest':learner.digest(),
        'reference_interface_digest':reference.digest(),'reference_support':support(reference_support),'reference_action_digest':reference_actions.digest(),
        'expected_calibration':calibration,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'compatible_mappings':4,'combined_sensor_log_margin':10000.,'per_stream_sensor_log_margin':1000.,
            'action_log_margin':20000.,'joint_rate':.45,'sensor_only_joint_margin':.45,'action_only_joint_margin':.40,
            'identity_joint_margin':.45,'random_joint_margin':.45},
        'controls':['oracle canonical subsets over the same frozen policy','learned sensor subset with first-four action slots',
            'first-six sensor slots with learned action subset','first-six/first-four slots with no inference','fixed random six-of-eight and four-of-six subsets',
            'four unseen composite sensor interfaces paired with unseen actuator interfaces','four separately sampled unlabeled calibration regimes per interface',
            'two independent evaluation action seeds','zero policy/model writes','disjoint training, calibration, and holdout initial worlds'],
        'classifier_dev':{'model':'jev-1.13.0','chosen_label':'strongest next development mechanism','confidence':.78,
            'role':'development route classification only; absent from support inference, BPC policy training, frozen evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace interfaces, composite formulas, calibration streams, worlds, seeds, frozen sources, or thresholds after execution.',
        'boundary':'Developer-frozen synthetic composite-interface transfer. Four separately sampled unlabeled calibration regimes, canonical/observed cardinalities, displaced-XOR nuisance synthesis, null action slots, coordinate grid, samplers, mixture schedules, interaction budget, probability families, generators, and terminal events remain supplied. The binder receives no regime, task, entity, direction, success, or reward names; no neural network, planner, search, joint-task policy training, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
