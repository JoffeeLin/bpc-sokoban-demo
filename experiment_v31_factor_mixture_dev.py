#!/usr/bin/env python3
"""Fresh development test of arithmetic anonymous-factor composition."""
import json,time
from pathlib import Path

from bpc_factor_mixture_v31 import MixturePolicy
from bpc_fourth_factor_v28 import evaluate,generate_suite
from bpc_three_factor_v12 import FieldPolicy,ProductPolicy,SharedPolicy,UniformPolicy,evaluate as evaluate_old,generate_suite as generate_old,train

ROOT=Path(__file__).resolve().parent


def main():
    started=time.perf_counter();learner,training=train(123010);suite,attempts=generate_suite(231110,24,learner.training_initials);old_suite,old_attempts=generate_old(231210,4,set(learner.training_initials)|{(w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates) for _,w,_ in suite});ordered=tuple(sorted(learner.factors))
    policies={'mixture':MixturePolicy(learner),'field':FieldPolicy(learner),'product':ProductPolicy(learner),'shared_cube':SharedPolicy(learner),'rotated':MixturePolicy(learner,rotated=True),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=MixturePolicy(learner,drop=(index,))
    writes=learner.writes;digest=learner.digest();conditions=evaluate(policies,suite,231310,32,48)
    retention,_=evaluate_old({'mixture':policies['mixture'],'field':policies['field']},old_suite,231410,16,128);total=conditions['mixture']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')]
    gates={'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'mixture_success_at_least_75pct':conditions['mixture']['successes']>=total*.75,
        'every_map_has_at_least_4_mixture_successes':all(conditions['mixture'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),
        'mixture_beats_field_by_5pct':conditions['mixture']['successes']-conditions['field']['successes']>=total*.05,
        'mixture_beats_product_by_5pct':conditions['mixture']['successes']-conditions['product']['successes']>=total*.05,
        'mixture_beats_each_factor_deletion_by_10pct':all(conditions['mixture']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),
        'mixture_beats_shared_cube_by_5pct':conditions['mixture']['successes']-conditions['shared_cube']['successes']>=total*.05,
        'mixture_beats_uniform_and_rotated_by_30pct':all(conditions['mixture']['successes']-conditions[name]['successes']>=total*.30 for name in ('uniform','rotated')),
        'retains_at_least_95pct_of_field_each_old_family':all(retention['mixture'].get(f'{family}_successes',0)>=retention['field'].get(f'{family}_successes',0)*.95 for family in ('push','collect','open','joint')),
        'evaluation_writes_zero_and_digest_unchanged':learner.writes==writes and learner.digest()==digest}
    result={'development_only':True,'candidate':'arithmetic mixture of three independently learned anonymous factor posteriors','step_budget':48,'episodes_per_world':32,
        'training':training,'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered]},
        'suite':{'seed':231110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},
        'conditions':conditions,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_v31_freeze':all(gates.values()),'evaluation_writes':learner.writes-writes,
        'classifier_dev':{'model':'jev-1.13.0','batch_items':10,'selected':'arithmetic probability mixture of active factors','confidence':.98,'role':'route classification only'},
        'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds and action seed, not frozen evidence. No neural network, reward, task score, planner, runtime search, semantic model rule, classifier runtime, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v31mixture'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
