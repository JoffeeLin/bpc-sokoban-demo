#!/usr/bin/env python3
"""Fresh development test of learned action-run survival."""
import json,random,time
from collections import Counter
from pathlib import Path

from bpc_direct_composition_v09 import choose
from bpc_fourth_factor_v28 import step as joint_step
from bpc_run_survival_v36 import RunPolicy,train
from bpc_temporal_cross_generator_v33 import generate
from bpc_temporal_policy_v32 import TemporalPolicy,train as temporal_train
from bpc_three_factor_v12 import FieldPolicy,UniformPolicy,World3,generate_suite as generate_old,key,raw,step as old_step,succeeded

ROOT=Path(__file__).resolve().parent;FACTOR='4f005ee784ce677cdc339533e3e0156b0aabea9bd6b47d2a8c6de0542245020e'


class GatedTemporalPolicy(TemporalPolicy):
    def probabilities(self,state):
        if len(tuple(signature for signature in self.learner.active(state) if signature not in self.drop))<2:return self.base.probabilities(state)
        return super().probabilities(state)


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
    started=time.perf_counter();learner,runs,training=train(123010);other,temporal,events=temporal_train(123010);assert learner.digest()==other.digest()==FACTOR and training==events
    frozen=json.loads((ROOT/'holdout_v33_temporal.json').read_text());excluded=set(learner.training_initials)|{key(World3(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')])) for row in frozen['worlds']}
    for seed in (234110,235110):
        previous,_=generate(seed,24,excluded);excluded|={key(world) for _,world,_ in previous}
    suite,attempts=generate(236110,24,excluded);old_suite,old_attempts=generate_old(236210,4,excluded|{key(world) for _,world,_ in suite});ordered=tuple(sorted(learner.factors))
    policies={'run_survival':RunPolicy(learner,runs),'field':FieldPolicy(learner),'first_order':GatedTemporalPolicy(other,temporal),
        'no_age':RunPolicy(learner,runs,no_age=True),'rotated_duration':RunPolicy(learner,runs,shuffle_action=1),
        'shuffled_factor':RunPolicy(learner,runs,shuffle_factor=1),'rotated':RunPolicy(learner,runs,rotated=True),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=RunPolicy(learner,runs,drop=(index,))
    writes=(learner.writes,runs.writes);digests=(learner.digest(),runs.digest());conditions=evaluate(policies,suite,236310,32,48)
    retention=evaluate({'run_survival':policies['run_survival'],'field':policies['field']},old_suite,236410,16,128,False);total=conditions['run_survival']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')]
    comparisons=('field','first_order','no_age','rotated_duration','shuffled_factor')
    gates={'base_factor_digest_exact':learner.digest()==FACTOR,'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'run_survival_success_at_least_75pct':conditions['run_survival']['successes']>=total*.75,
        'every_map_has_at_least_4_run_survival_successes':all(conditions['run_survival'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),
        'run_survival_beats_same_information_controls_by_5pct':all(conditions['run_survival']['successes']-conditions[name]['successes']>=total*.05 for name in comparisons),
        'run_survival_beats_each_factor_deletion_by_10pct':all(conditions['run_survival']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),
        'run_survival_beats_uniform_and_rotated_by_30pct':all(conditions['run_survival']['successes']-conditions[name]['successes']>=total*.30 for name in ('uniform','rotated')),
        'retains_at_least_95pct_of_field_each_old_family':all(retention['run_survival'].get(f'{family}_successes',0)>=retention['field'].get(f'{family}_successes',0)*.95 for family in ('push','collect','open','joint')),
        'evaluation_writes_zero_and_digests_unchanged':(learner.writes,runs.writes)==writes and (learner.digest(),runs.digest())==digests}
    result={'development_only':True,'candidate':'factor-balanced posterior survival of anonymous action runs','step_budget':48,'episodes_per_world':32,
        'training':training,'factor_digest':learner.digest(),'run_digest':runs.digest(),'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered]},
        'suite':{'seed':236110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},
        'conditions':conditions,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),'evaluation_writes':{'factor':learner.writes-writes[0],'runs':runs.writes-writes[1]},
        'classifier_dev':{'model':'jev-1.13.0','selected':'learned anonymous action-run survival','confidence':.88,'role':'development route classification only'},
        'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds and action seed, not frozen evidence. No neural network, reward, task score, planner, runtime search, semantic model rule, classifier runtime, joint-task training, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v36runs'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
