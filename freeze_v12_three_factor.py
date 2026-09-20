#!/usr/bin/env python3
"""Freeze v0.12 sources, training identity, and unseen four-family holdout."""
import hashlib,json
from pathlib import Path

from bpc_three_factor_v12 import generate_suite,train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v12.json';PROTOCOL=ROOT/'protocol_v12_three_factor.json'
SOURCES=('bpc_three_factor_v12.py','bpc_evidence_field_v11.py','bpc_cross_task_v07.py',
         'bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py',
         'experiment_v12_three_factor_frozen.py','freeze_v12_three_factor.py')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    config={'train_seed':121010,'uniform_episodes':800,'guided_rounds':2,'guided_episodes':400,'train_steps':120,
            'holdout_seed':122010,'worlds_per_family':12,'eval_seeds':[122110,122210],
            'episodes_per_map':32,'step_budgets':[64,256]}
    learner,events=train(config['train_seed'],config['uniform_episodes'],config['guided_rounds'],config['guided_episodes'],config['train_steps'])
    suite,attempts=generate_suite(config['holdout_seed'],config['worlds_per_family'],learner.training_initials)
    worlds=[{'family':family,'h':world.h,'w':world.w,'walls':world.walls,'agent':world.agent,
             'objects':world.objects,'marks':world.marks,'switches':world.switches,'gates':world.gates,
             'shortest':distance} for family,world,distance in suite]
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds}
    assert len(keys)==len(worlds) and not keys&learner.training_initials
    HOLDOUT.write_text(json.dumps({'format':'bpc-three-factor-v12-holdout','seed':config['holdout_seed'],
        'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-three-factor-v12-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can one non-neural BPC learner discover three anonymous raw-change factors from separate successful experience and directly recombine them on unseen worlds that require all three mechanisms?',
        'config':config,'expected_training_events':events,'expected_factor_digest':learner.digest(),
        'expected_signatures':[list(x) for x in sorted(learner.factors)],'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'joint_rate':.45,'shared_joint_margin':.08,'each_drop_joint_margin':.05,
            'uniform_joint_margin':.30,'rotated_joint_margin':.40,'product_absolute_gap':.01},
        'controls':['explicit equal product over the same learned factor cubes','one shared cube receiving every successful trace',
            'fixed deletion of each global anonymous factor','rotated action semantics','uniform random actions',
            'two independent evaluation seeds','zero evaluation writes','no initial holdout world overlaps a training initial world'],
        'classifier_dev':{'model':'jev-1.13.0','role':'development metric routing only; low-confidence outputs were manually reviewed; absent from model training, evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace holdouts, alter seeds, edit frozen sources, or lower gates after execution.',
        'boundary':'Developer-frozen synthetic evidence. Raw channels, generators, binary terminal events, additive field rule, and limits remain supplied. No planner, search, neural network, task-family input, or joint-task training is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
