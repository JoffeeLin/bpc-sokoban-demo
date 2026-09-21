#!/usr/bin/env python3
"""Fresh development test of observable-effect-conditioned action transitions."""
import json,random,time
from collections import Counter
from pathlib import Path

from bpc_direct_composition_v09 import choose
from bpc_effect_transition_v37 import EffectPolicy,train
from bpc_fourth_factor_v28 import step as joint_step
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
                    before=raw(world);action=choose(policy.probabilities(before),rng)
                    if hasattr(policy,'chose'):policy.chose(action)
                    nxt=joint_step(world,action) if joint else old_step(world,action);after=raw(nxt)
                    if hasattr(policy,'observed'):policy.observed(before,action,after)
                    world=nxt;success=world.marks==0 if joint else succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success;row[f'map_{index}_successes']+=success
    return {name:dict(row) for name,row in rows.items()}


def main():
    started=time.perf_counter();learner,effects,training=train(123010);other,temporal,events=temporal_train(123010);assert learner.digest()==other.digest()==FACTOR and training==events
    frozen=json.loads((ROOT/'holdout_v33_temporal.json').read_text());excluded=set(learner.training_initials)|{key(World3(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')])) for row in frozen['worlds']}
    for old_seed in (234110,235110,236110):
        previous,_=generate(old_seed,24,excluded);excluded|={key(world) for _,world,_ in previous}
    suite,attempts=generate(237110,24,excluded);old_suite,old_attempts=generate_old(237210,4,excluded|{key(world) for _,world,_ in suite});ordered=tuple(sorted(learner.factors))
    policies={'effect':EffectPolicy(learner,effects),'field':FieldPolicy(learner),'first_order':GatedTemporalPolicy(other,temporal),
        'event_only':EffectPolicy(learner,effects,mode='event'),'erased_event':EffectPolicy(learner,effects,mode='erased'),
        'shuffled_event':EffectPolicy(learner,effects,shuffle_effect=True),'rotated_next':EffectPolicy(learner,effects,rotate_action=1),
        'rotated':EffectPolicy(learner,effects,rotated=True),'uniform':UniformPolicy()}
    for index,signature in enumerate(ordered):policies[f'delete_{index}_{signature}']=EffectPolicy(learner,effects,drop=(index,))
    writes=(learner.writes,effects.writes);digests=(learner.digest(),effects.digest());conditions=evaluate(policies,suite,237310,32,48)
    retention=evaluate({'effect':policies['effect'],'field':policies['field']},old_suite,237410,16,128,False);total=conditions['effect']['episodes'];deletions=[name for name in conditions if name.startswith('delete_')]
    comparisons=('field','first_order','event_only','erased_event','shuffled_event','rotated_next')
    gates={'base_factor_digest_and_training_events_exact':learner.digest()==FACTOR and training==events,'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'effect_success_at_least_75pct':conditions['effect']['successes']>=total*.75,
        'every_map_has_at_least_4_effect_successes':all(conditions['effect'].get(f'map_{i}_successes',0)>=4 for i in range(len(suite))),
        'effect_beats_same_information_controls_by_5pct':all(conditions['effect']['successes']-conditions[name]['successes']>=total*.05 for name in comparisons),
        'effect_beats_each_factor_deletion_by_10pct':all(conditions['effect']['successes']-conditions[name]['successes']>=total*.10 for name in deletions),
        'effect_beats_uniform_and_rotated_by_30pct':all(conditions['effect']['successes']-conditions[name]['successes']>=total*.30 for name in ('uniform','rotated')),
        'retains_at_least_95pct_of_field_each_old_family':all(retention['effect'].get(f'{family}_successes',0)>=retention['field'].get(f'{family}_successes',0)*.95 for family in ('push','collect','open','joint')),
        'evaluation_writes_zero_and_digests_unchanged':(learner.writes,effects.writes)==writes and (learner.digest(),effects.digest())==digests}
    result={'development_only':True,'candidate':'P(next anonymous action | old factor, previous action, anonymous raw changed-plane tuple)','step_budget':48,'episodes_per_world':32,
        'training':training,'factor_digest':learner.digest(),'effect_digest':effects.digest(),'training_audit':{'initial_worlds':len(learner.training_initials),'object_and_mark_overlap':sum(bool(row[4] and row[5]) for row in learner.training_initials),'factor_signatures':[list(x) for x in ordered],'effect_signatures':[list(x) for x in sorted(effects.effects)]},
        'suite':{'seed':237110,'worlds':len(suite),'generation_attempts':attempts,'distances':[x[2] for x in suite]},'old_retention_suite':{'worlds':len(old_suite),'generation_attempts':old_attempts},
        'conditions':conditions,'retention_conditions':retention,'preregistered_gates':gates,'adopt_for_freeze':all(gates.values()),'evaluation_writes':{'factor':learner.writes-writes[0],'effects':effects.writes-writes[1]},
        'classifier_dev':{'model':'jev-1.13.0','selected':'observable-effect-conditioned action transition','confidence':.56,'role':'development route classification only'},
        'seconds':time.perf_counter()-started,'boundary':'Fresh development worlds and action seed, not frozen evidence. No neural network, reward, task score, planner, runtime search, semantic effect name, classifier runtime, joint-task training, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v37effects'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
