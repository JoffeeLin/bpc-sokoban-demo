#!/usr/bin/env python3
"""Fresh development test of successful-action temporal probability memory."""
import json,random,time
from collections import Counter
from pathlib import Path

from bpc_direct_composition_v09 import choose
from bpc_fourth_factor_v28 import generate_suite,step as joint_step
from bpc_temporal_policy_v32 import TemporalPolicy,train
from bpc_three_factor_v12 import FieldPolicy,UniformPolicy,generate_suite as generate_old,raw,step as old_step,succeeded

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
    started=time.perf_counter();learner,temporal,training=train(123010);assert learner.digest()==EXPECTED
    suite,attempts=generate_suite(232110,24,learner.training_initials);old_suite,old_attempts=generate_old(232210,4,set(learner.training_initials)|{(w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates) for _,w,_ in suite});ordered=tuple(sorted(learner.factors))
    policies={'temporal':TemporalPolicy(learner,temporal),'field':FieldPolicy(learner),'shuffled_history':TemporalPolicy(learner,temporal,shuffle=1),
        'order_zero':TemporalPolicy(learner,temporal,order0=True),'rotated':TemporalPolicy(learner,temporal,rotated=True),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=TemporalPolicy(learner,temporal,drop=(index,))
    writes=(learner.writes,temporal.writes);digests=(learner.digest(),temporal.digest());conditions=evaluate(policies,suite,232310,32,48)
    retention=evaluate({'temporal':policies['temporal'],'field':policies['field']},old_suite,232410,16,128,False);total=conditions['temporal']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')]
    gates={'base_factor_digest_exact':learner.digest()==EXPECTED,'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'temporal_success_at_least_75pct':conditions['temporal']['successes']>=total*.75,
        'every_map_has_at_least_4_temporal_successes':all(conditions['temporal'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),
        'temporal_beats_field_by_5pct':conditions['temporal']['successes']-conditions['field']['successes']>=total*.05,
        'temporal_beats_shuffled_and_order_zero_by_5pct':all(conditions['temporal']['successes']-conditions[name]['successes']>=total*.05 for name in ('shuffled_history','order_zero')),
        'temporal_beats_each_factor_deletion_by_10pct':all(conditions['temporal']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),
        'temporal_beats_uniform_and_rotated_by_30pct':all(conditions['temporal']['successes']-conditions[name]['successes']>=total*.30 for name in ('uniform','rotated')),
        'retains_at_least_95pct_of_field_each_old_family':all(retention['temporal'].get(f'{family}_successes',0)>=retention['field'].get(f'{family}_successes',0)*.95 for family in ('push','collect','open','joint')),
        'evaluation_writes_zero_and_digests_unchanged':(learner.writes,temporal.writes)==writes and (learner.digest(),temporal.digest())==digests}
    result={'development_only':True,'candidate':'factor-conditioned P(next anonymous action | previous anonymous action) from the original successful traces','step_budget':48,'episodes_per_world':32,
        'training':training,'factor_digest':learner.digest(),'temporal_digest':temporal.digest(),'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered]},
        'suite':{'seed':232110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},
        'conditions':conditions,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_v32_freeze':all(gates.values()),'evaluation_writes':{'factor':learner.writes-writes[0],'temporal':temporal.writes-writes[1]},
        'classifier_dev':{'model':'jev-1.13.0','batch_items':10,'selected':'factor-conditioned action bigram probabilities','confidence':.91,'role':'route classification only'},
        'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds and action seed, not frozen evidence. Temporal counts use only original separate successful traces. No neural network, reward, task score, planner, runtime search, semantic model rule, classifier runtime, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v32temporal'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
