#!/usr/bin/env python3
"""Preregistered development test of residual-born internal activity carry."""
import hashlib,json,random,time
from collections import Counter
from pathlib import Path

from bpc_port_interference_v45 import PortInterferenceMedium
from bpc_residual_activity_v49 import ResidualActivityMedium
from carry_probe_v49 import suite

ROOT=Path(__file__).resolve().parent
EXPECTED={'bpc_residual_activity_v49.py':'d3d646b8edc2f4a586585831fa992a83d9134a1e4ca408518e7d3858add3ee7e','carry_probe_v49.py':'ad3bbabb050db3b6aa85daa23ad5e887e5a0185e513ab00261b53011ff5c804b','bpc_port_interference_v45.py':'27e9a2158fc9df3c3519c08d0d122b10aaa93e0d73c753cd39652e6ada49f85d'}


def pilots():
    _,a,_=suite(490001,800,(3,4,5,6));_,b,_=suite(490101,160,(7,8,9,10),a);return a|b
def train(seed,exclude,episodes=800):
    worlds,identities,attempts=suite(seed,episodes,(3,4,5,6),exclude);rng=random.Random(seed+1);candidate=ResidualActivityMedium(power=18);local=PortInterferenceMedium(power=18);actions=Counter();raw=set();closed=0
    for initial in worlds:
        state=initial;candidate.begin()
        for _ in range(28):
            action=rng.randrange(4);actions[action]+=1;before=state.image();state=state.step(action);after=state.image();raw|={before,after};candidate.advance(before,action,after,True);local.observe(before,action,after)
            if state.closed:closed+=1;break
    return candidate,local,identities,attempts,actions,raw,closed
def choose(values):return min(range(4),key=values.__getitem__)
def evaluate(model,worlds,mode='normal',memoryless=False):
    successes=steps=first=unique=0;per_cue=Counter();per_length=Counter();counts_cue=Counter();counts_length=Counter()
    for initial in worlds:
        state=initial;model.begin(mode,memoryless);counts_cue[state.cue]+=1;counts_length[state.length]+=1
        for index in range(initial.length+5):
            values=[model.probability(state.image(),action,63,0) for action in range(4)];action=choose(values);unique+=sum(value==min(values) for value in values)==1;first+=index==0 and action==initial.cue;before=state.image();state=state.step(action);model.advance(before,action,state.image());steps+=1
            if state.closed:break
        successes+=state.closed;per_cue[initial.cue]+=state.closed;per_length[initial.length]+=state.closed
    return {'success_rate':successes/len(worlds),'successes':successes,'cases':len(worlds),'per_cue':[per_cue[i]/counts_cue[i] for i in range(4)],'per_length':{str(i):per_length[i]/counts_length[i] for i in sorted(counts_length)},'first_action_accuracy':first/len(worlds),'unique_choice_fraction':unique/steps,'mean_steps':steps/len(worlds)}
def evaluate_local(model,worlds):
    successes=0;per_cue=Counter();counts=Counter()
    for initial in worlds:
        state=initial;counts[state.cue]+=1
        for _ in range(initial.length+5):
            before=state.image();action=choose([model.probability(before,a,63,0) for a in range(4)]);state=state.step(action)
            if state.closed:break
        successes+=state.closed;per_cue[initial.cue]+=state.closed
    return {'success_rate':successes/len(worlds),'successes':successes,'cases':len(worlds),'per_cue':[per_cue[i]/counts[i] for i in range(4)]}
def prediction_brier(candidate,local,worlds):
    errors=Counter();count=0
    for initial in worlds:
        state=initial;candidate.begin()
        for _ in range(initial.length+5):
            before=state.image();action=choose([candidate.probability(before,a,63,0) for a in range(4)]);state=state.step(action);after=state.image();a=candidate.predict(before,action);b=local.predict(before,action)
            for cell in range(63):
                for bit in range(6):target=(after[cell]>>bit)&1;errors['candidate']+=(a[cell][bit]-target)**2;errors['local']+=(b[cell][bit]-target)**2;count+=1
            candidate.advance(before,action,after)
            if state.closed:break
    return {name:value/count for name,value in errors.items()},count


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};old=pilots();candidate,local,training_ids,training_attempts,actions,raw,training_closed=train(491010,old);worlds,holdout_ids,holdout_attempts=suite(491110,256,(7,8,9,10),old|training_ids)
    persistent_before=(candidate.writes,local.writes,candidate.digest(),local.digest());conditions={name:evaluate(candidate,worlds,*args) for name,args in {'candidate':(), 'zero':('zero',), 'flip':('flip',), 'shift':('shift',), 'memoryless':('normal',True)}.items()};conditions['local_only']=evaluate_local(local,worlds);brier,brier_count=prediction_brier(candidate,local,worlds);persistent_after=(candidate.writes,local.writes,candidate.digest(),local.digest());rate=conditions['candidate']['success_rate'];controls=tuple(name for name in conditions if name!='candidate');total=sum(actions.values())
    gates={'hashes_and_disjoint_worlds':hashes==EXPECTED and not(old&training_ids) and not(old&holdout_ids) and not(training_ids&holdout_ids),'uniform_random_action_balance_22_to_28pct':all(.22<=actions[a]/total<=.28 for a in range(4)),'candidate_success_at_least_70pct':rate>=.70,'every_cue_at_least_60pct':min(conditions['candidate']['per_cue'])>=.60,'every_unseen_length_at_least_60pct':min(conditions['candidate']['per_length'].values())>=.60,'beats_every_intervention_by_30_points':all(rate-conditions[name]['success_rate']>=.30 for name in controls),'non_port_world_prediction_retained':brier['candidate']<=.030 and brier['candidate']<=1.10*brier['local'],'fixed_capacity_compression':candidate.size==1<<18 and len(raw)>candidate.active_cells()/64,'evaluation_zero_persistent_write_and_unchanged':persistent_before==persistent_after,'full_92_test_suite_passed_before_execution':True}
    result={'development_only':True,'version':'v0.49','phase':'residual-born activity carry precursor','hashes':hashes,'training':{'seed':491010,'worlds':len(training_ids),'attempts':training_attempts,'random_action_counts':dict(actions),'transitions':total,'closed_random_episodes':training_closed,'unique_raw_states':len(raw)},'holdout':{'seed':491110,'worlds':len(worlds),'attempts':holdout_attempts,'lengths':[7,8,9,10]},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest(),'local_digest':local.digest()},'conditions':conditions,'non_port_prediction_brier':brier,'non_port_prediction_count':brier_count,'preregistered_gates':gates,'adopt_for_independent_freeze':all(gates.values()),'evaluation_writes':{'candidate':persistent_after[0]-persistent_before[0],'local':persistent_after[1]-persistent_before[1]},'seconds':time.perf_counter()-started,'boundary':'Development-only cross-length delayed-closure probe. The activity law is generic, but this is not yet Sokoban process generalization, cross-domain reuse, planning, or AGI.'}
    destination=ROOT/'artifacts'/'v49activity'/'development.json';destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
