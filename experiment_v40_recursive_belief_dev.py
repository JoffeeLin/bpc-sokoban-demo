#!/usr/bin/env python3
"""Fresh preregistered development test of recursive anonymous-factor belief."""
import json,random,time
from collections import Counter
from pathlib import Path

from bpc_direct_composition_v09 import choose
from bpc_fourth_factor_v28 import step as joint_step
from bpc_recursive_belief_v40 import RecursiveBeliefPolicy,train
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
                    before=raw(world);action=choose(policy.probabilities(before),rng)
                    if hasattr(policy,'chose'):policy.chose(action)
                    nxt=joint_step(world,action) if joint else old_step(world,action);after=raw(nxt)
                    if hasattr(policy,'observed'):policy.observed(before,action,after)
                    world=nxt;success=world.marks==0 if joint else succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success;row[f'map_{index}_successes']+=success
    return {name:dict(row) for name,row in rows.items()}


def main():
    started=time.perf_counter();learner,temporal,boundary,emissions,training=train(123010);assert training==EXPECTED
    frozen=json.loads((ROOT/'holdout_v33_temporal.json').read_text());excluded=set(learner.training_initials)|{key(World3(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')])) for row in frozen['worlds']}
    for old_seed in range(234110,240110,1000):
        previous,_=generate(old_seed,24,excluded);excluded|={key(world) for _,world,_ in previous}
    suite,attempts=generate(240110,24,excluded);old_suite,old_attempts=generate_old(240210,4,excluded|{key(world) for _,world,_ in suite});ordered=tuple(sorted(learner.factors));build=lambda **kw:RecursiveBeliefPolicy(learner,temporal,boundary,emissions,**kw)
    policies={'recursive':build(),'memoryless':build(memoryless=True),'no_action_update':build(use_action=False),'no_effect_update':build(use_effect=False),'no_boundary_reset':build(use_boundary=False),'shuffled_emission':build(shuffle_emission=1),'hard_map':build(hard=True),'field':FieldPolicy(learner),'rotated':build(rotated=True,shuffle_emission=1),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=build(drop=(index,))
    writes=(learner.writes,temporal.writes,boundary.writes,emissions.writes);digests=(learner.digest(),temporal.digest(),boundary.digest(),emissions.digest());conditions=evaluate(policies,suite,240310,32,48)
    retention=evaluate({'recursive':policies['recursive'],'field':policies['field']},old_suite,240410,16,128,False);total=conditions['recursive']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')];comparisons=('memoryless','no_action_update','no_effect_update','no_boundary_reset','shuffled_emission','hard_map','field')
    gates={'old_training_events_exact':training==EXPECTED,'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),'recursive_success_at_least_75pct':conditions['recursive']['successes']>=total*.75,'every_map_has_at_least_4_recursive_successes':all(conditions['recursive'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),'recursive_beats_same_information_controls_by_5pct':all(conditions['recursive']['successes']-conditions[name]['successes']>=total*.05 for name in comparisons),'recursive_beats_each_factor_deletion_by_10pct':all(conditions['recursive']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),'recursive_beats_uniform_and_rotated_by_30pct':all(conditions['recursive']['successes']-conditions[name]['successes']>=total*.30 for name in ('uniform','rotated')),'retains_at_least_95pct_of_field_each_old_family':all(retention['recursive'].get(f'{family}_successes',0)>=retention['field'].get(f'{family}_successes',0)*.95 for family in ('push','collect','open','joint')),'evaluation_writes_zero_and_digests_unchanged':(learner.writes,temporal.writes,boundary.writes,emissions.writes)==writes and (learner.digest(),temporal.digest(),boundary.digest(),emissions.digest())==digests}
    result={'development_only':True,'candidate':'recursive anonymous-factor probability state updated by chosen action, raw effect, and learned boundary','step_budget':48,'episodes_per_world':32,'training':training,'digests':{'factor':learner.digest(),'temporal':temporal.digest(),'boundary':boundary.digest(),'emission':emissions.digest()},'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered]},'suite':{'seed':240110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},'conditions':conditions,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_independent_freeze':all(gates.values()),'evaluation_writes':dict(zip(('factor','temporal','boundary','emission'),[(learner.writes,temporal.writes,boundary.writes,emissions.writes)[i]-writes[i] for i in range(4)])),'classifier_dev':{'model':'jev-1.13.0','selected':'recursive factor belief','confidence':.94,'role':'development route classification only'},'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds, not frozen evidence. No neural network, reward, task score, planner, runtime search, semantic phase, classifier runtime, joint-task training, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v40recursive'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
