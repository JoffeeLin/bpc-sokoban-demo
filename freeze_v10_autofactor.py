#!/usr/bin/env python3
"""Freeze v0.10 sources, training identity, and unseen mixed holdout."""
import hashlib,json
from pathlib import Path

from bpc_autofactor_v10 import generate_suite,train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v10.json';PROTOCOL=ROOT/'protocol_v10_autofactor.json'
SOURCES=('bpc_autofactor_v10.py','bpc_direct_composition_v09.py','bpc_cross_task_v07.py','general_bpc_v7.py',
         'experiment_v5.py','experiment_v10_autofactor_frozen.py','freeze_v10_autofactor.py')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    config={'train_seed':101010,'uniform_episodes':1000,'guided_rounds':2,'guided_episodes':500,'train_steps':100,
            'holdout_seed':102010,'worlds_per_family':16,'eval_seeds':[102110,102210],
            'episodes_per_map':64,'step_budgets':[32,160]}
    learner,events=train(config['train_seed'],config['uniform_episodes'],config['guided_rounds'],config['guided_episodes'],config['train_steps'])
    suite,attempts=generate_suite(config['holdout_seed'],config['worlds_per_family'],learner.training_initials)
    worlds=[{'family':family,'h':world.h,'w':world.w,'walls':world.walls,'agent':world.agent,
             'objects':world.objects,'marks':world.marks,'shortest':distance} for family,world,distance in suite]
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks']) for x in worlds}
    assert len(keys)==len(worlds),(len(keys),len(worlds))
    overlap=keys&learner.training_initials;assert not overlap,len(overlap)
    HOLDOUT.write_text(json.dumps({'format':'bpc-autofactor-v10-holdout','seed':config['holdout_seed'],
        'combined_generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-autofactor-v10-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can one BPC learner discover anonymous event factors from terminal raw co-change and match task-name oracle routing on unseen single and joint tasks?',
        'config':config,'expected_training_events':events,'expected_factor_digest':learner.digest(),
        'expected_signatures':[list(x) for x in sorted(learner.factors)],'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'combined_rate':.30,'shared_margin':.08,'uniform_margin':.20,'permuted_total_margin':.15},
        'controls':['task-name oracle routing over the same discovered factors','always activate every discovered factor',
            'one shared cube receiving every successful trace','permuted raw-plane activation','uniform random actions',
            'two independent evaluation seeds','zero evaluation writes','no initial holdout world overlaps a training initial world'],
        'classifier_dev':{'model':'jev-1.13.0','role':'development route classification only; absent from model training, evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace holdouts, alter seeds, edit frozen sources, or lower gates after execution.',
        'boundary':'Developer-frozen synthetic evidence. Factor identities and activation are learned without task names. Equal probability multiplication, raw channels, generators, binary terminal events, and limits remain supplied.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
