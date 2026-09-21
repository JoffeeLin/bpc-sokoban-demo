#!/usr/bin/env python3
"""Freeze the independent-generator v0.33 holdout before candidate execution."""
import hashlib,json
from pathlib import Path

from bpc_fourth_factor_v28 import collect_place_traces,generate_suite
from bpc_temporal_cross_generator_v33 import generate
from bpc_temporal_policy_v32 import train
from bpc_three_factor_v12 import generate_suite as generate_old,key

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v33_temporal.json';PROTOCOL=ROOT/'protocol_v33_temporal.json'
SOURCES=('bpc_temporal_policy_v32.py','bpc_temporal_cross_generator_v33.py','bpc_fourth_factor_v28.py','bpc_three_factor_v12.py',
    'bpc_evidence_field_v11.py','general_bpc_v7.py','bpc_direct_composition_v09.py','bpc_cross_task_v07.py','experiment_v5.py',
    'experiment_v33_temporal_frozen.py','freeze_v33_temporal.py')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def record(family,world,distance):return {'family':family,**world.__dict__,'shortest':distance}


def main():
    learner,temporal,events=train(123010);excluded=set(learner.training_initials);_,place_initials,_=collect_place_traces(228010,600)
    for seed,count,extra in ((228110,12,place_initials),(230110,24,()),(231110,24,()),(232110,24,())):
        suite,_=generate_suite(seed,count,excluded|set(extra));excluded|={key(world) for _,world,_ in suite}
    suite,attempts=generate(233110,24,excluded);excluded|={key(world) for _,world,_ in suite};old_suite,old_attempts=generate_old(233210,4,excluded)
    patterns=[]
    for _,world,_ in suite:
        border=sum(1<<(y*world.w+x) for y in range(world.h) for x in range(world.w) if x in (0,world.w-1) or y in (0,world.h-1));patterns.append(world.walls&~border)
    maximum=max((a&b).bit_count()/max(1,(a|b).bit_count()) for i,a in enumerate(patterns) for b in patterns[i+1:])
    holdout={'format':'bpc-temporal-v33-holdout','generator':'independent doorway/object-row generator','seed':233110,'generation_attempts':attempts,
        'maximum_internal_wall_jaccard':maximum,'worlds':[record(*row) for row in suite],'old_retention_seed':233210,'old_generation_attempts':old_attempts,'old_worlds':[record(*row) for row in old_suite]}
    HOLDOUT.write_text(json.dumps(holdout,indent=2)+'\n')
    config={'train_seed':123010,'holdout_seed':233110,'worlds':24,'evaluation_seeds':[233310,233410],'episodes_per_world_per_seed':16,'step_budget':48,
        'old_retention_seed':233210,'old_evaluation_seeds':[233510,233610],'old_episodes_per_world_per_seed':8,'old_step_budget':128,
        'expected_factor_digest':learner.digest(),'expected_temporal_digest':temporal.digest(),'expected_training_events':events}
    protocol={'format':'bpc-temporal-v33-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can action-transition probabilities learned only from separate successful factors improve zero-shot direct control of unseen worlds containing a new object-on-mark interaction, while retaining old tasks?',
        'config':config,'development_result_sha256':sha(ROOT/'artifacts'/'v32temporal'/'development.json'),'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'minimum_aggregate_temporal_success_rate':.75,'minimum_each_seed_temporal_success_rate':.70,'minimum_successes_each_world':4,
            'minimum_aggregate_field_margin':.05,'minimum_each_seed_field_margin':.03,'minimum_shuffled_and_order_zero_margin':.05,
            'minimum_each_factor_deletion_margin':.10,'minimum_uniform_and_rotated_margin':.30,'minimum_old_family_retention_fraction':.95},
        'controls':['unchanged state-only evidence field','one-column-rotated action-history probabilities','order-zero factor action counts','each anonymous factor deleted globally',
            'rotated action semantics','uniform random','two evaluation action streams','fresh old-task retention worlds','zero persistent evaluation writes','exact deterministic repeat'],
        'generator_audit':{'worlds':len(suite),'distance_min':min(x[2] for x in suite),'distance_max':max(x[2] for x in suite),'maximum_internal_wall_jaccard':maximum,
            'unique_worlds':len({key(world) for _,world,_ in suite}),'all_require_object':all(__import__('bpc_fourth_factor_v28').shortest(world,True) is None for _,world,_ in suite),
            'all_require_gate':all(__import__('bpc_fourth_factor_v28').shortest(world,False,True) is None for _,world,_ in suite)},
        'classifier_dev':{'model':'jev-1.13.0','batch_items':10,'selected':'factor-conditioned action bigram probabilities','confidence':.91,'role':'development route classification only'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},'failure_policy':'Retain failures; do not change worlds, seeds, sources, controls, horizons, or thresholds after execution.',
        'boundary':'Developer-frozen synthetic evidence, not third-party blind or AGI. Raw channels, terminal event, factor signatures, dynamics, generators, first-order temporal family, and direct controller are supplied. No neural network, reward, task score, planner, runtime search, semantic model rule, classifier runtime, or evaluation learning.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
