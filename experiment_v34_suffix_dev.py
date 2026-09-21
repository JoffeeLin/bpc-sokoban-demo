#!/usr/bin/env python3
"""Fresh development evaluation for hierarchical action-suffix memory."""
import json,random,time
from collections import Counter
from pathlib import Path

from bpc_direct_composition_v09 import choose
from bpc_fourth_factor_v28 import step as joint_step
from bpc_suffix_policy_v34 import SuffixPolicy,train
from bpc_temporal_cross_generator_v33 import generate
from bpc_three_factor_v12 import FieldPolicy,UniformPolicy,World3,generate_suite as generate_old,key,raw,step as old_step,succeeded

ROOT=Path(__file__).resolve().parent;EXPECTED='4f005ee784ce677cdc339533e3e0156b0aabea9bd6b47d2a8c6de0542245020e'


def evaluate(policies,suite,seed,episodes,steps,joint=True):
    rows={name:Counter() for name in policies}
    for index,(family,initial,_) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                if hasattr(policy,'reset'):policy.reset()
                rng=random.Random(seed+index*100000+episode);world=initial
                for _ in range(steps):
                    action=choose(policy.probabilities(raw(world)),rng)
                    if hasattr(policy,'chose'):policy.chose(action)
                    world=joint_step(world,action) if joint else old_step(world,action)
                    success=world.marks==0 if joint else succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success;row[f'map_{index}_successes']+=success
    return {name:dict(row) for name,row in rows.items()}


def main():
    started=time.perf_counter();learner,suffixes,training=train(123010);assert learner.digest()==EXPECTED
    frozen=json.loads((ROOT/'holdout_v33_temporal.json').read_text());excluded=set(learner.training_initials)|{key(World3(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')])) for row in frozen['worlds']}
    suite,attempts=generate(234110,24,excluded);old_suite,old_attempts=generate_old(234210,4,excluded|{key(world) for _,world,_ in suite});ordered=tuple(sorted(learner.factors))
    policies={'suffix':SuffixPolicy(learner,suffixes),'field':FieldPolicy(learner),'first_order':SuffixPolicy(learner,suffixes,order=1),
        'rotated_history':SuffixPolicy(learner,suffixes,shuffle=1),'order_zero':SuffixPolicy(learner,suffixes,order=0),
        'rotated':SuffixPolicy(learner,suffixes,rotated=True),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=SuffixPolicy(learner,suffixes,drop=(index,))
    writes=(learner.writes,suffixes.writes);digests=(learner.digest(),suffixes.digest());conditions=evaluate(policies,suite,234310,32,48)
    retention=evaluate({'suffix':policies['suffix'],'field':policies['field']},old_suite,234410,16,128,False);total=conditions['suffix']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')]
    gates={'base_factor_digest_exact':learner.digest()==EXPECTED,'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'suffix_success_at_least_75pct':conditions['suffix']['successes']>=total*.75,
        'every_map_has_at_least_4_suffix_successes':all(conditions['suffix'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),
        'suffix_beats_field_first_order_rotated_history_and_order_zero_by_5pct':all(conditions['suffix']['successes']-conditions[name]['successes']>=total*.05 for name in ('field','first_order','rotated_history','order_zero')),
        'suffix_beats_each_factor_deletion_by_10pct':all(conditions['suffix']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),
        'suffix_beats_uniform_and_rotated_by_30pct':all(conditions['suffix']['successes']-conditions[name]['successes']>=total*.30 for name in ('uniform','rotated')),
        'retains_at_least_95pct_of_field_each_old_family':all(retention['suffix'].get(f'{family}_successes',0)>=retention['field'].get(f'{family}_successes',0)*.95 for family in ('push','collect','open','joint')),
        'evaluation_writes_zero_and_digests_unchanged':(learner.writes,suffixes.writes)==writes and (learner.digest(),suffixes.digest())==digests}
    result={'development_only':True,'candidate':'hierarchical factor-conditioned action suffixes with structural composition gate','step_budget':48,'episodes_per_world':32,
        'training':training,'factor_digest':learner.digest(),'suffix_digest':suffixes.digest(),'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered]},
        'suite':{'seed':234110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},
        'conditions':conditions,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),'evaluation_writes':{'factor':learner.writes-writes[0],'suffix':suffixes.writes-writes[1]},
        'classifier_dev':{'model':'jev-1.13.0','selected':'variable-order suffix probability memory','confidence':.83,'role':'development route classification only'},
        'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds and action seed, not frozen evidence. No neural network, reward, task score, planner, runtime search, semantic model rule, classifier runtime, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v34suffix'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
