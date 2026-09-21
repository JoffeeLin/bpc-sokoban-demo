#!/usr/bin/env python3
"""Fresh development test of censored anonymous event boundaries."""
import json,random,time
from collections import Counter
from pathlib import Path

from bpc_direct_composition_v09 import choose
from bpc_event_boundary_v38 import BoundaryPolicy,train
from bpc_fourth_factor_v28 import step as joint_step
from bpc_temporal_cross_generator_v33 import generate
from bpc_three_factor_v12 import FieldPolicy,UniformPolicy,World3,generate_suite as generate_old,key,raw,step as old_step,succeeded

ROOT=Path(__file__).resolve().parent;FACTOR='4f005ee784ce677cdc339533e3e0156b0aabea9bd6b47d2a8c6de0542245020e';TEMPORAL='d79e772aa3fc34f5e5189d86e811d50c581af7d8b8a716053f4fd9bb2dde81e1'


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
    started=time.perf_counter();learner,temporal,boundary,training=train(123010);assert learner.digest()==FACTOR and temporal.digest()==TEMPORAL
    frozen=json.loads((ROOT/'holdout_v33_temporal.json').read_text());excluded=set(learner.training_initials)|{key(World3(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')])) for row in frozen['worlds']}
    for old_seed in (234110,235110,236110,237110):
        previous,_=generate(old_seed,24,excluded);excluded|={key(world) for _,world,_ in previous}
    suite,attempts=generate(238110,24,excluded);old_suite,old_attempts=generate_old(238210,4,excluded|{key(world) for _,world,_ in suite});ordered=tuple(sorted(learner.factors))
    policies={'boundary':BoundaryPolicy(learner,temporal,boundary),'field':FieldPolicy(learner),'always_temporal':BoundaryPolicy(learner,temporal,boundary,fixed=1),
        'global_boundary':BoundaryPolicy(learner,temporal,boundary,mode='global'),'shuffled_boundary':BoundaryPolicy(learner,temporal,boundary,mode='shuffle'),
        'inverted_boundary':BoundaryPolicy(learner,temporal,boundary,mode='invert'),'half_temporal':BoundaryPolicy(learner,temporal,boundary,fixed=.5),
        'rotated':BoundaryPolicy(learner,temporal,boundary,rotated=True),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=BoundaryPolicy(learner,temporal,boundary,drop=(index,))
    writes=(learner.writes,temporal.writes,boundary.writes);digests=(learner.digest(),temporal.digest(),boundary.digest());conditions=evaluate(policies,suite,238310,32,48)
    retention=evaluate({'boundary':policies['boundary'],'field':policies['field']},old_suite,238410,16,128,False);total=conditions['boundary']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')]
    comparisons=('field','always_temporal','global_boundary','shuffled_boundary','inverted_boundary','half_temporal')
    gates={'base_temporal_digests_and_training_events_exact':learner.digest()==FACTOR and temporal.digest()==TEMPORAL,'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'boundary_success_at_least_75pct':conditions['boundary']['successes']>=total*.75,
        'every_map_has_at_least_4_boundary_successes':all(conditions['boundary'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),
        'boundary_beats_same_information_controls_by_5pct':all(conditions['boundary']['successes']-conditions[name]['successes']>=total*.05 for name in comparisons),
        'boundary_beats_each_factor_deletion_by_10pct':all(conditions['boundary']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),
        'boundary_beats_uniform_and_rotated_by_30pct':all(conditions['boundary']['successes']-conditions[name]['successes']>=total*.30 for name in ('uniform','rotated')),
        'retains_at_least_95pct_of_field_each_old_family':all(retention['boundary'].get(f'{family}_successes',0)>=retention['field'].get(f'{family}_successes',0)*.95 for family in ('push','collect','open','joint')),
        'evaluation_writes_zero_and_digests_unchanged':(learner.writes,temporal.writes,boundary.writes)==writes and (learner.digest(),temporal.digest(),boundary.digest())==digests}
    result={'development_only':True,'candidate':'Beta P(trace continues | old anonymous factor, anonymous changed-plane tuple)','step_budget':48,'episodes_per_world':32,
        'training':training,'factor_digest':learner.digest(),'temporal_digest':temporal.digest(),'boundary_digest':boundary.digest(),'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered],'boundary_rows':{str(signature):{str(effect):counts for effect,counts in rows.items()} for signature,rows in boundary.rows.items()}},
        'suite':{'seed':238110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},
        'conditions':conditions,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),'evaluation_writes':{'factor':learner.writes-writes[0],'temporal':temporal.writes-writes[1],'boundary':boundary.writes-writes[2]},
        'classifier_dev':{'model':'jev-1.13.0','selected':'censored observable event-boundary posterior','confidence':.72,'role':'development route classification only'},
        'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds and action seed, not frozen evidence. No neural network, reward, task score, planner, runtime search, semantic effect name, classifier runtime, joint-task training, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v38boundary'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
