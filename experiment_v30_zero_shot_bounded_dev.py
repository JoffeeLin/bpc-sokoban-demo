#!/usr/bin/env python3
"""Fresh development suite with a fixed 4x-shortest-path control horizon."""
import json,time
from pathlib import Path

from bpc_fourth_factor_v28 import evaluate,generate_suite
from bpc_three_factor_v12 import FieldPolicy,SharedPolicy,UniformPolicy,train

ROOT=Path(__file__).resolve().parent


def main():
    started=time.perf_counter();learner,training=train(123010);suite,attempts=generate_suite(230110,24,learner.training_initials);ordered=tuple(sorted(learner.factors))
    policies={'full':FieldPolicy(learner),'shared_cube':SharedPolicy(learner),'rotated':FieldPolicy(learner,rotated=True),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=FieldPolicy(learner,drop=(index,))
    writes=learner.writes;digest=learner.digest();conditions=evaluate(policies,suite,230310,32,48);total=conditions['full']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')]
    gates={'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'full_success_at_least_75pct':conditions['full']['successes']>=total*.75,
        'every_map_has_at_least_4_full_successes':all(conditions['full'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),
        'full_beats_each_factor_deletion_by_10pct':all(conditions['full']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),
        'full_beats_shared_cube_by_5pct':conditions['full']['successes']-conditions['shared_cube']['successes']>=total*.05,
        'full_beats_uniform_by_30pct':conditions['full']['successes']-conditions['uniform']['successes']>=total*.30,
        'full_beats_rotated_by_30pct':conditions['full']['successes']-conditions['rotated']['successes']>=total*.30,
        'evaluation_writes_zero_and_digest_unchanged':learner.writes==writes and learner.digest()==digest}
    result={'development_only':True,'candidate':'unchanged old three-factor BPC; zero object-mark training','step_budget':48,'episodes_per_world':32,
        'training':training,'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered]},
        'suite':{'seed':230110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'conditions':conditions,
        'preregistered_gates':gates,'adopt_for_v30_freeze':all(gates.values()),'evaluation_writes':learner.writes-writes,
        'classifier_dev':{'model':'jev-1.13.0','selected':'fresh freeze only after source audit and individual factor deletions','confidence':.65,'role':'route classification only'},
        'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds and action seed, not frozen evidence. Fixed 48-step horizon was committed before execution. No neural network, reward, task score, planner, runtime search, semantic model rule, classifier runtime, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v30bounded'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
