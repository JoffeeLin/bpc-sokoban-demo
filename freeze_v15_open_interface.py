#!/usr/bin/env python3
"""Freeze v0.15 open-interface calibration and unseen holdout."""
import hashlib,json
from pathlib import Path

from bpc_open_interface_v15 import (action_stats,collect_open_interface,infer_action_subset,
    infer_sensor_subset,inverse_subset)
from bpc_three_factor_v12 import generate_suite,train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v15.json';PROTOCOL=ROOT/'protocol_v15_open_interface.json'
SOURCES=('bpc_open_interface_v15.py','bpc_three_factor_v12.py','bpc_evidence_field_v11.py','bpc_cross_task_v07.py',
    'bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py','experiment_v15_open_interface_frozen.py','freeze_v15_open_interface.py')
SENSORS=((None,4,2,0,None,5,1,3),(1,5,None,3,0,2,None,4),(3,None,1,4,2,0,5,None),(5,2,4,None,1,None,3,0))
ACTUATORS=((1,None,3,2,0,None),(None,0,3,1,None,2),(2,1,None,0,3,None),(3,None,2,None,0,1))
MIXES=({'push':210,'collect':45,'open':45},{'push':45,'collect':210,'open':45},
       {'push':45,'collect':45,'open':210},{'push':100,'collect':100,'open':100})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(row):
    return {**row,'mapping':list(row['mapping']),'second':list(row['second']),
        **({'candidate_slots':list(row['candidate_slots'])} if 'candidate_slots' in row else {})}


def main():
    config={'train_seed':121010,'reference_seed':153010,'target_seeds':[153110,153111,153112,153113],
        'calibration_steps':32,'reference_worlds_per_family':100,'sensor_routes':[list(x) for x in SENSORS],
        'actuator_routes':[list(x) for x in ACTUATORS],'target_mixtures':MIXES,
        'holdout_seed':153510,'worlds_per_family':12,'eval_seeds':[153610,153710],
        'episodes_per_map':24,'step_budget':64,'random_binding_seed':153810}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,triples,initials=collect_open_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;reference_actions=action_stats(triples,range(6),6,4);calibration=[]
    for seed,sensor,actuator,mix in zip(config['target_seeds'],SENSORS,ACTUATORS,MIXES):
        target,triples,initials=collect_open_interface(seed,mix,config['calibration_steps'],sensor,actuator,excluded);excluded|=initials
        channel=infer_sensor_subset(reference,target);target_actions=action_stats(triples,channel['mapping'],len(sensor),len(actuator));action=infer_action_subset(reference_actions,target_actions)
        calibration.append({'target_interface_digest':target.digest(),'target_action_digest':target_actions.digest(),
            'channel_oracle':list(inverse_subset(sensor,6)),'channel_binding':norm(channel),
            'action_oracle':list(inverse_subset(actuator,4)),'action_binding':norm(action)})
    suite,attempts=generate_suite(config['holdout_seed'],config['worlds_per_family'],excluded)
    worlds=[{'family':family,'h':world.h,'w':world.w,'walls':world.walls,'agent':world.agent,'objects':world.objects,
        'marks':world.marks,'switches':world.switches,'gates':world.gates,'shortest':distance} for family,world,distance in suite]
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds}
    assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-open-interface-v15-holdout','seed':config['holdout_seed'],
        'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-open-interface-v15-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a frozen non-neural BPC policy identify its canonical six-sensor/four-action interface inside simultaneous unseen eight-channel/six-slot interfaces containing deterministic state-keyed random nuisance planes and permanent zero-effect action slots, using only unlabeled transition probabilities under calibration-distribution shift?',
        'config':config,'expected_training_events':events,'expected_factor_digest':learner.digest(),
        'reference_interface_digest':reference.digest(),'reference_action_digest':reference_actions.digest(),
        'expected_calibration':calibration,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'sensor_log_margin':500.,'action_log_margin':5000.,'joint_rate':.45,
            'sensor_only_joint_margin':.45,'action_only_joint_margin':.40,'identity_joint_margin':.40,'random_joint_margin':.40},
        'controls':['oracle canonical sensor/action subsets over the same frozen policy','learned sensor subset with first-four action slots',
            'first-six sensor slots with learned action subset','first-six/first-four slots with no inference','fixed random six-of-eight and four-of-six subsets',
            'four unseen eight-channel/six-slot interfaces','three shifted and one balanced unlabeled calibration distributions',
            'two independent action-sampling seeds','zero policy/model writes','disjoint training, calibration, and holdout initial worlds'],
        'classifier_dev':{'model':'jev-1.13.0','chosen_label':'high value next frozen experiment','confidence':.93,
            'role':'development route classification only; absent from binders, BPC policy training, frozen evaluation, and runtime'},
        'retained_development_failures':['marginal occupancy/change/cochange confused a displaced composite nuisance with a real plane',
            'unfiltered action likelihood confused a permanent zero-effect slot with a frequently blocked real action',
            'action-conditioned local joint statistics still did not identify the composite nuisance under mixture shift; that harder case remains unsupported'],
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace routes, nuisance mechanisms, streams, worlds, seeds, frozen sources, or thresholds after execution.',
        'boundary':'Developer-frozen synthetic open-interface transfer. Six canonical planes and four canonical actions are embedded in supplied eight-channel/six-slot interfaces with deterministic state-keyed random nuisance planes. Composite causal nuisance rejection failed and is not claimed. Nuisance synthesis, null-slot mechanism, coordinate grid, calibration samplers, mixture schedules, interaction budget, likelihood families, generators, and terminal events remain supplied. No entity, task, direction, success, or reward labels enter binding; no neural network, planner, search, joint-task policy training, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
