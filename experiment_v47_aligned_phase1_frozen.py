#!/usr/bin/env python3
"""Independent frozen reproduction of v0.47 aligned phase-one prediction."""
import hashlib,json,time
from pathlib import Path

from bpc_three_factor_v12 import key
from experiment_v47_aligned_phase1_dev import evaluate,holdout,old_initials,train,training

ROOT=Path(__file__).resolve().parent
EXPECTED={'experiment_v47_aligned_phase1_dev.py':'3c1acb7f13f93748eb65fb746ece6431ac71e8404a756f018bc944e0bc69b437',
    'bpc_aligned_canvas_v47.py':'49a3c9bd98797a867641783f9659108254d98ff2fb85c38f62ba71f710606186',
    'bpc_compressed_medium_v44.py':'db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6',
    'bpc_parallel_medium_v42.py':'68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef',
    'bpc_pure_medium_v41.py':'e1893081144c47f97191b4b82c9e5d7959774951e3f7bc05860c8d06fe1122cf'}


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};old=old_initials()
    _,dev_initials,_,_,_=training(247010,old);_,dev_suite,_=holdout(247110,old|dev_initials);old|=dev_initials|{key(w) for _,w,_ in dev_suite}
    rows,initials,raw,seen,attempts=training(247210,old);records,suite,holdout_attempts=holdout(247310,old|initials);holdout_initials={key(w) for _,w,_ in suite}
    candidate,no_action=train(rows),train(rows,False);before=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest());metrics,novel,counts=evaluate(candidate,no_action,records,seen);after=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest())
    relative=lambda name,group:1-metrics['candidate'][group]/metrics[name][group]
    gates={'hashes_match_preregistration':hashes==EXPECTED,'fresh_initials_disjoint':not(old&initials) and not(old&holdout_initials) and not(initials&holdout_initials),'novel_context_fraction_at_least_10pct':novel>=.10,'overall_brier_at_most_0020':metrics['candidate']['all']<=.020,'changed_brier_below_025_copy_and_half':metrics['candidate']['changed']<.25 and metrics['candidate']['changed']<metrics['copy']['changed'] and metrics['candidate']['changed']<metrics['half']['changed'],'novel_changed_brier_at_most_025':metrics['candidate']['novel_changed']<=.25,'changed_improves_action_controls_by_10pct':all(relative(name,'changed')>=.10 for name in ('no_action','rotated')),'novel_changed_improves_action_controls_by_10pct':all(relative(name,'novel_changed')>=.10 for name in ('no_action','rotated')),'compression_and_v44_occupancy_ceiling':len(raw)>candidate.active_cells()/64 and candidate.active_cells()<=33343,'evaluation_zero_write_and_unchanged':before==after,'aligned_geometry_and_full_unit_suite_passed_before_execution':True}
    result={'frozen_first_execution':True,'version':'v0.47','phase':'phase-one aligned Sokoban world prediction independent reproduction','hashes':hashes,'training':{'seed':247210,'transitions':len(rows),'initial_worlds':len(initials),'generation_attempts':attempts,'unique_raw_states':len(raw),'seen_full_contexts':len(seen)},'holdout':{'seed':247310,'worlds':len(suite),'transitions':len(records),'generation_attempts':holdout_attempts},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest(),'control_digest':no_action.digest()},'metrics_brier':metrics,'context_counts':counts,'novel_context_fraction':novel,'relative_improvement':{f'{name}_{group}':relative(name,group) for name in ('no_action','rotated') for group in ('changed','novel_changed')},'preregistered_gates':gates,'frozen_pass':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'no_action':after[1]-before[1]},'seconds':time.perf_counter()-started,'boundary':'Correctly aligned camera, physical next-state prediction only. No reward, task score, planner, search, goal behavior, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v47aligned'/'frozen.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
