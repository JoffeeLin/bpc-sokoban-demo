#!/usr/bin/env python3
"""Freeze v0.13 sources, interface calibration, and unseen holdout worlds."""
import hashlib,json,random
from pathlib import Path

from bpc_channel_binding_v13 import collect_interface,infer_binding,inverse
from bpc_three_factor_v12 import generate_suite,train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v13.json';PROTOCOL=ROOT/'protocol_v13_channel_binding.json'
SOURCES=('bpc_channel_binding_v13.py','bpc_three_factor_v12.py','bpc_evidence_field_v11.py',
    'bpc_cross_task_v07.py','bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py',
    'experiment_v13_channel_binding_frozen.py','freeze_v13_channel_binding.py')
PERMUTATIONS=((1,3,5,0,2,4),(5,2,0,4,1,3),(2,4,1,5,3,0),(3,0,4,1,5,2))
MIXES=({'push':210,'collect':45,'open':45},{'push':45,'collect':210,'open':45},
       {'push':45,'collect':45,'open':210},{'push':100,'collect':100,'open':100})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def json_binding(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second'])}


def main():
    config={'train_seed':121010,'reference_seed':132010,'target_seeds':[132110,132111,132112,132113],
        'calibration_steps':32,'reference_worlds_per_family':100,'holdout_seed':132510,'worlds_per_family':12,
        'eval_seeds':[132610,132710],'episodes_per_map':24,'step_budget':64,'random_binding_seed':132810,
        'permutations':[list(x) for x in PERMUTATIONS],'target_mixtures':MIXES}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,initials=collect_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;calibration=[]
    for seed,permutation,mix in zip(config['target_seeds'],PERMUTATIONS,MIXES):
        target,initials=collect_interface(seed,mix,config['calibration_steps'],permutation,excluded);excluded|=initials
        calibration.append({'target_digest':target.digest(),'oracle':list(inverse(permutation)),
            'bindings':{mode:json_binding(infer_binding(reference,target,mode)) for mode in ('transition','full','static','count')}})
    suite,attempts=generate_suite(config['holdout_seed'],config['worlds_per_family'],excluded)
    worlds=[{'family':family,'h':world.h,'w':world.w,'walls':world.walls,'agent':world.agent,'objects':world.objects,
        'marks':world.marks,'switches':world.switches,'gates':world.gates,'shortest':distance} for family,world,distance in suite]
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds}
    assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-channel-binding-v13-holdout','seed':config['holdout_seed'],
        'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-channel-binding-v13-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a frozen non-neural BPC policy use unlabeled probabilistic transition fingerprints to recover unseen raw-channel permutations under calibration-distribution shift and preserve direct control on disjoint unseen worlds?',
        'config':config,'expected_training_events':events,'expected_factor_digest':learner.digest(),
        'reference_digest':reference.digest(),'expected_calibration':calibration,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'minimum_binding_log_margin':100.,'joint_rate':.45,'identity_joint_margin':.35,
            'random_joint_margin':.25,'static_joint_margin':.08,'count_joint_margin':.08},
        'controls':['oracle inverse channel permutation over the same frozen field policy','identity/no binding',
            'static occupancy plus spatial likelihood without transitions','occupancy-count likelihood only',
            'fixed random bindings','four unseen derangements','three shifted and one balanced unlabeled calibration distributions',
            'two independent action seeds','zero policy/model writes','disjoint training, calibration, and holdout initial worlds'],
        'classifier_dev':{'model':'jev-1.13.0','role':'development direction routing only; absent from calibration inference, policy training, frozen evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace permutations, calibration streams, holdout worlds, seeds, frozen sources, or thresholds after execution.',
        'boundary':'Developer-frozen synthetic sensor-interface transfer. The six raw channels, balanced reference sampler, target mixture schedules, interaction budget, transition likelihood family, generators, and terminal events remain supplied. No neural network, planner, search, task name, joint-task policy training, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
