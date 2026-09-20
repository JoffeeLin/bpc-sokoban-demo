#!/usr/bin/env python3
"""Freeze v0.14 joint sensor/actuator calibration and unseen holdout."""
import hashlib,json
from pathlib import Path

from bpc_channel_binding_v13 import infer_binding,inverse
from bpc_joint_binding_v14 import action_stats,collect_joint_interface,infer_action_binding,inverse_action
from bpc_three_factor_v12 import generate_suite,train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v14.json';PROTOCOL=ROOT/'protocol_v14_joint_binding.json'
SOURCES=('bpc_joint_binding_v14.py','bpc_channel_binding_v13.py','bpc_three_factor_v12.py','bpc_evidence_field_v11.py',
    'bpc_cross_task_v07.py','bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py',
    'experiment_v14_joint_binding_frozen.py','freeze_v14_joint_binding.py')
SENSORS=((1,5,3,0,2,4),(3,2,0,5,1,4),(5,0,4,2,3,1),(2,4,5,1,0,3))
ACTUATORS=((1,0,3,2),(1,2,3,0),(2,3,1,0),(3,2,0,1))
MIXES=({'push':210,'collect':45,'open':45},{'push':45,'collect':210,'open':45},
       {'push':45,'collect':45,'open':210},{'push':100,'collect':100,'open':100})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second'])}


def main():
    config={'train_seed':121010,'reference_seed':142010,'target_seeds':[142110,142111,142112,142113],
        'calibration_steps':32,'reference_worlds_per_family':100,'sensor_permutations':[list(x) for x in SENSORS],
        'actuator_permutations':[list(x) for x in ACTUATORS],'target_mixtures':MIXES,
        'holdout_seed':142510,'worlds_per_family':12,'eval_seeds':[142610,142710],
        'episodes_per_map':24,'step_budget':64,'random_binding_seed':142810}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,triples,initials=collect_joint_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;reference_actions=action_stats(triples,range(6));calibration=[]
    for seed,sensor,actuator,mix in zip(config['target_seeds'],SENSORS,ACTUATORS,MIXES):
        target,triples,initials=collect_joint_interface(seed,mix,config['calibration_steps'],sensor,actuator,excluded);excluded|=initials
        channel=infer_binding(reference,target,'transition');target_actions=action_stats(triples,channel['mapping']);action=infer_action_binding(reference_actions,target_actions)
        calibration.append({'target_interface_digest':target.digest(),'target_action_digest':target_actions.digest(),
            'channel_oracle':list(inverse(sensor)),'channel_binding':norm(channel),
            'action_oracle':list(inverse_action(actuator)),'action_binding':norm(action)})
    suite,attempts=generate_suite(config['holdout_seed'],config['worlds_per_family'],excluded)
    worlds=[{'family':family,'h':world.h,'w':world.w,'walls':world.walls,'agent':world.agent,'objects':world.objects,
        'marks':world.marks,'switches':world.switches,'gates':world.gates,'shortest':distance} for family,world,distance in suite]
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds}
    assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-joint-binding-v14-holdout','seed':config['holdout_seed'],
        'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-joint-binding-v14-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a frozen non-neural BPC policy recover simultaneous unseen sensor-channel and actuator-action permutations from unlabeled transitions under calibration-distribution shift, then preserve direct control on disjoint unseen worlds?',
        'config':config,'expected_training_events':events,'expected_factor_digest':learner.digest(),
        'reference_interface_digest':reference.digest(),'reference_action_digest':reference_actions.digest(),
        'expected_calibration':calibration,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'sensor_log_margin':100.,'action_log_margin':1000.,'joint_rate':.45,
            'sensor_only_joint_margin':.40,'action_only_joint_margin':.40,'identity_joint_margin':.35,'random_joint_margin':.35},
        'controls':['oracle inverse sensor and actuator permutations over the same frozen policy','learned sensor binding with identity actuator binding',
            'identity sensor binding with learned actuator binding','identity/no binding','fixed random sensor and actuator bindings',
            'four unseen sensor derangements paired with four unseen actuator derangements','three shifted and one balanced unlabeled calibration distributions',
            'two independent action-sampling seeds','zero policy/model writes','disjoint training, calibration, and holdout initial worlds'],
        'classifier_dev':{'model':'jev-1.13.0','role':'development route classification only; absent from binders, BPC policy training, frozen evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace permutations, streams, worlds, seeds, frozen sources, or thresholds after execution.',
        'boundary':'Developer-frozen synthetic interface transfer. Sensor/action cardinalities, coordinate grid, calibration samplers, mixture schedules, interaction budget, likelihood families, generators, and terminal events remain supplied. No entity, task, direction, or success labels enter binding; no neural network, planner, search, joint-task policy training, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
