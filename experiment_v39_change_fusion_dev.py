#!/usr/bin/env python3
"""Fresh development test of factor-specific raw-change probability fusion."""
import json,random,time
from collections import Counter
from pathlib import Path

from bpc_change_fusion_v39 import ChangeFusionPolicy,train,transition_writes
from bpc_direct_composition_v09 import choose
from bpc_fourth_factor_v28 import step as joint_step
from bpc_temporal_cross_generator_v33 import generate
from bpc_three_factor_v12 import FieldPolicy,UniformPolicy,World3,generate_suite as generate_old,key,raw,step as old_step,succeeded

ROOT=Path(__file__).resolve().parent
EXPECTED={'push_success':1138,'push_compact_steps':4251,'signature_(1, 2)':1138,'push_episodes':1600,'collect_success':1522,'collect_compact_steps':9880,'signature_(1, 3)':1522,'collect_episodes':1600,'open_success':1450,'open_compact_steps':5234,'signature_(1, 4, 5)':1450,'open_episodes':1600}


def evaluate(policies,suite,seed,episodes,steps,joint=True):
    rows={name:Counter() for name in policies}
    for index,(family,initial,_) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                if hasattr(policy,'reset'):policy.reset()
                rng=random.Random(seed+index*100000+episode);world=initial
                for _ in range(steps):
                    before=raw(world);action=choose(policy.probabilities(before),rng);nxt=joint_step(world,action) if joint else old_step(world,action);after=raw(nxt)
                    if hasattr(policy,'observed'):policy.observed(before,action,after)
                    world=nxt;success=world.marks==0 if joint else succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success;row[f'map_{index}_successes']+=success
    return {name:dict(row) for name,row in rows.items()}


def main():
    started=time.perf_counter();learner,temporal,boundary,training=train(123010);assert training==EXPECTED
    frozen=json.loads((ROOT/'holdout_v33_temporal.json').read_text());excluded=set(learner.training_initials)|{key(World3(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')])) for row in frozen['worlds']}
    for old_seed in (234110,235110,236110,237110,238110):
        previous,_=generate(old_seed,24,excluded);excluded|={key(world) for _,world,_ in previous}
    suite,attempts=generate(239110,24,excluded);old_suite,old_attempts=generate_old(239210,4,excluded|{key(world) for _,world,_ in suite});ordered=tuple(sorted(learner.factors))
    policies={'change_fusion':ChangeFusionPolicy(learner,temporal,boundary),'boundary':ChangeFusionPolicy(learner,temporal,boundary,mode='none'),
        'v7_power_024':ChangeFusionPolicy(learner,temporal,boundary,power=.24),'global_change':ChangeFusionPolicy(learner,temporal,boundary,mode='global'),
        'shared_change':ChangeFusionPolicy(learner,temporal,boundary,mode='shared'),'rotated_change':ChangeFusionPolicy(learner,temporal,boundary,rotate_change=1),
        'change_only':ChangeFusionPolicy(learner,temporal,boundary,mode='change_only'),'field':FieldPolicy(learner),
        'rotated':ChangeFusionPolicy(learner,temporal,boundary,rotated=True,rotate_change=1),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=ChangeFusionPolicy(learner,temporal,boundary,drop=(index,))
    writes=(learner.writes,temporal.writes,boundary.writes,transition_writes(learner));digests=(learner.digest(),temporal.digest(),boundary.digest());conditions=evaluate(policies,suite,239310,32,48)
    retention=evaluate({'change_fusion':policies['change_fusion'],'field':policies['field']},old_suite,239410,16,128,False);total=conditions['change_fusion']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')]
    comparisons=('boundary','v7_power_024','global_change','shared_change','rotated_change','change_only','field')
    gates={'old_training_events_exact':training==EXPECTED,'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'change_fusion_success_at_least_75pct':conditions['change_fusion']['successes']>=total*.75,
        'every_map_has_at_least_4_change_fusion_successes':all(conditions['change_fusion'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),
        'change_fusion_beats_same_information_controls_by_5pct':all(conditions['change_fusion']['successes']-conditions[name]['successes']>=total*.05 for name in comparisons),
        'change_fusion_beats_each_factor_deletion_by_10pct':all(conditions['change_fusion']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),
        'change_fusion_beats_uniform_and_rotated_by_30pct':all(conditions['change_fusion']['successes']-conditions[name]['successes']>=total*.30 for name in ('uniform','rotated')),
        'retains_at_least_95pct_of_field_each_old_family':all(retention['change_fusion'].get(f'{family}_successes',0)>=retention['field'].get(f'{family}_successes',0)*.95 for family in ('push','collect','open','joint')),
        'evaluation_writes_zero_and_digests_unchanged':(learner.writes,temporal.writes,boundary.writes,transition_writes(learner))==writes and (learner.digest(),temporal.digest(),boundary.digest())==digests}
    result={'development_only':True,'candidate':'factor-balanced P(raw change | current raw relations, action) product with event-boundary direct control','step_budget':48,'episodes_per_world':32,
        'training':training,'factor_digest':learner.digest(),'temporal_digest':temporal.digest(),'boundary_digest':boundary.digest(),'transition_writes':transition_writes(learner),'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered]},
        'suite':{'seed':239110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},
        'conditions':conditions,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),'evaluation_writes':{'factor':learner.writes-writes[0],'temporal':temporal.writes-writes[1],'boundary':boundary.writes-writes[2],'transitions':transition_writes(learner)-writes[3]},
        'classifier_dev':{'model':'jev-1.13.0','selected':'factor-specific typed raw-change probability product','confidence':.82,'known_weak_v7_fixed_power':.98,'role':'development route classification only'},
        'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds and action seed, not frozen evidence. No neural network, reward, task score, planner, runtime search, semantic collision rule, classifier runtime, joint-task training, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v39change'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
