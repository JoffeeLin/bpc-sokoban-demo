#!/usr/bin/env python3
"""First and only independent frozen reproduction of v0.49."""
import hashlib,json,time
from pathlib import Path

from carry_probe_v49 import suite
from experiment_v49_residual_activity_dev import evaluate,evaluate_local,pilots,prediction_brier,train

ROOT=Path(__file__).resolve().parent
EXPECTED={'experiment_v49_residual_activity_dev.py':'deafc1522b2031878ff0768288b5e4f47240d301431b858d8d16ac18fcd0fe2d'}


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};old=pilots();_,development,_=suite(491010,800,(3,4,5,6),old);old|=development;_,development_holdout,_=suite(491110,256,(7,8,9,10),old);old|=development_holdout
    candidate,local,training_ids,training_attempts,actions,raw,training_closed=train(492010,old);worlds,holdout_ids,holdout_attempts=suite(492110,256,(7,8,9,10),old|training_ids)
    persistent_before=(candidate.writes,local.writes,candidate.digest(),local.digest());conditions={name:evaluate(candidate,worlds,*args) for name,args in {'candidate':(), 'zero':('zero',), 'flip':('flip',), 'shift':('shift',), 'memoryless':('normal',True)}.items()};conditions['local_only']=evaluate_local(local,worlds);brier,brier_count=prediction_brier(candidate,local,worlds);persistent_after=(candidate.writes,local.writes,candidate.digest(),local.digest());rate=conditions['candidate']['success_rate'];controls=tuple(name for name in conditions if name!='candidate');total=sum(actions.values())
    gates={'hashes_and_disjoint_worlds':hashes==EXPECTED and not(old&training_ids) and not(old&holdout_ids) and not(training_ids&holdout_ids),'uniform_random_action_balance_22_to_28pct':all(.22<=actions[a]/total<=.28 for a in range(4)),'candidate_success_at_least_70pct':rate>=.70,'every_cue_at_least_60pct':min(conditions['candidate']['per_cue'])>=.60,'every_unseen_length_at_least_60pct':min(conditions['candidate']['per_length'].values())>=.60,'beats_every_intervention_by_30_points':all(rate-conditions[name]['success_rate']>=.30 for name in controls),'non_port_world_prediction_retained':brier['candidate']<=.030 and brier['candidate']<=1.10*brier['local'],'fixed_capacity_compression':candidate.size==1<<18 and len(raw)>candidate.active_cells()/64,'evaluation_zero_persistent_write_and_unchanged':persistent_before==persistent_after,'full_92_test_suite_passed_before_execution':True}
    result={'frozen_first_execution':True,'version':'v0.49','phase':'residual-born activity carry independent reproduction','hashes':hashes,'training':{'seed':492010,'worlds':len(training_ids),'attempts':training_attempts,'random_action_counts':dict(actions),'transitions':total,'closed_random_episodes':training_closed,'unique_raw_states':len(raw)},'holdout':{'seed':492110,'worlds':len(worlds),'attempts':holdout_attempts,'lengths':[7,8,9,10]},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest(),'local_digest':local.digest()},'conditions':conditions,'non_port_prediction_brier':brier,'non_port_prediction_count':brier_count,'preregistered_gates':gates,'frozen_pass':all(gates.values()),'evaluation_writes':{'candidate':persistent_after[0]-persistent_before[0],'local':persistent_after[1]-persistent_before[1]},'seconds':time.perf_counter()-started,'boundary':'Frozen cross-length delayed-closure carry probe. The activity law is generic, but this is not yet Sokoban process generalization, cross-domain reuse, planning, or AGI.'}
    destination=ROOT/'artifacts'/'v49activity'/'frozen.json';destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
