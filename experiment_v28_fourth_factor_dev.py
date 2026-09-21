#!/usr/bin/env python3
"""Development-only fourth-factor acquisition and recombination test."""
import json,pickle,time
from pathlib import Path

from bpc_fourth_factor_v28 import collect_place_traces,evaluate as evaluate_four,generate_suite as generate_four
from bpc_three_factor_v12 import FieldPolicy,SharedPolicy,ThreeFactorBPC,UniformPolicy,evaluate as evaluate_old,generate_suite as generate_old,train

ROOT=Path(__file__).resolve().parent


def clear_caches(learner):
    learner.shared.encoder.cache.clear()
    for factor in learner.factors.values():factor.encoder.cache.clear()


def clone(value):return pickle.loads(pickle.dumps(value,protocol=5))


def main():
    started=time.perf_counter();old,training=train(123010);clear_caches(old);augmented=clone(old);traces,place_initials,trace_attempts=collect_place_traces(228010,600)
    scratch=ThreeFactorBPC()
    for trace in traces:augmented.observe_success(trace);scratch.observe_success(trace)
    clear_caches(augmented);clear_caches(scratch);signature=(1,2,3);assert signature in augmented.factors and set(scratch.factors)=={signature}
    new_index=tuple(sorted(augmented.factors)).index(signature);excluded=set(old.training_initials)|place_initials
    joint_suite,joint_attempts=generate_four(228110,12,excluded);excluded|={tuple((w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates)) for _,w,_ in joint_suite}
    old_suite,old_attempts=generate_old(228210,4,excluded)
    policies={'augmented':FieldPolicy(augmented),'old_only':FieldPolicy(old),'new_factor_deleted':FieldPolicy(augmented,drop=(new_index,)),
        'scratch_same_new_experience':FieldPolicy(scratch),'shared_cube':SharedPolicy(augmented),'rotated':FieldPolicy(augmented,rotated=True),'uniform':UniformPolicy()}
    writes=augmented.writes;digest=augmented.digest();joint=evaluate_four(policies,joint_suite,228310)
    retention,_=evaluate_old({'augmented':policies['augmented'],'old_only':policies['old_only']},old_suite,228410,16,128)
    total=joint['augmented']['episodes'];families=('push','collect','open','joint')
    gates={'new_signature_exact_and_600_successes':augmented.successes[signature]==600 and scratch.successes[signature]==600,
        'every_joint_map_has_augmented_success':all(joint['augmented'].get(f'map_{i}_successes',0)>0 for i in range(len(joint_suite))),
        'augmented_beats_old_only_by_10pct':joint['augmented']['successes']-joint['old_only']['successes']>=total*.10,
        'augmented_beats_same_experience_scratch_by_10pct':joint['augmented']['successes']-joint['scratch_same_new_experience']['successes']>=total*.10,
        'augmented_beats_new_factor_deleted_by_10pct':joint['augmented']['successes']-joint['new_factor_deleted']['successes']>=total*.10,
        'augmented_beats_rotated_by_20pct':joint['augmented']['successes']-joint['rotated']['successes']>=total*.20,
        'augmented_beats_uniform_by_20pct':joint['augmented']['successes']-joint['uniform']['successes']>=total*.20,
        'retains_at_least_95pct_of_old_successes_each_family':all(retention['augmented'].get(f'{family}_successes',0)>=retention['old_only'].get(f'{family}_successes',0)*.95 for family in families),
        'evaluation_writes_zero_and_digest_unchanged':augmented.writes==writes and augmented.digest()==digest}
    result={'development_only':True,'mechanism':'add one anonymous terminal co-change factor (1,2,3), then sum its unchanged probability evidence with three retained factors',
        'training':training,'place_training':{'successful_traces':len(traces),'attempts':trace_attempts,'signature':list(signature)},
        'joint_suite':{'worlds':len(joint_suite),'generation_attempts':joint_attempts,'distances':[x[2] for x in joint_suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},
        'joint_conditions':joint,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_v28_freeze':all(gates.values()),
        'classifier_dev':{'model':'jev-1.13.0','batch_items':10,'selected':'fourth anonymous factor plus same-experience scratch and deletion controls','confidence':.95,'role':'route classification only'},
        'evaluation_writes':augmented.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development-only generated evidence. Terminal success and raw channels are supplied; no task name enters the model. No neural network, reward, scalar task score, planner, runtime search, semantic rule, classifier runtime, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v28fourth'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
