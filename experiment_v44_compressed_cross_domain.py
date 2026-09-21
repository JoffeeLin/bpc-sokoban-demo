#!/usr/bin/env python3
"""Preregistered fresh two-domain test of the compressed pure-BPC core."""
import hashlib,json,time
from pathlib import Path

from bpc_compressed_medium_v44 import CompressedResidualMedium
from experiment_v41_pure_medium_dev import evaluate as evaluate_sokoban,holdout_rows,training_rows
from experiment_v42_parallel_posterior_dev import fresh_training
from experiment_v43_causal_lattice import evaluate as evaluate_lattice,rows as lattice_rows
from bpc_three_factor_v12 import key

ROOT=Path(__file__).resolve().parent
EXPECTED={'bpc_compressed_medium_v44.py':'db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6','bpc_parallel_medium_v42.py':'68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef','bpc_pure_medium_v41.py':'e1893081144c47f97191b4b82c9e5d7959774951e3f7bc05860c8d06fe1122cf'}


def train(records,use_action=True):
    medium=CompressedResidualMedium(use_action=use_action)
    for before,action,after in records:medium.observe(before,action,after)
    return medium


def measures(candidate,control,records,seen,evaluator):
    before=(candidate.writes,control.writes,candidate.digest(),control.digest());metrics,novel,counts=evaluator(candidate,control,records,seen);after=(candidate.writes,control.writes,candidate.digest(),control.digest());relative=lambda name,group:1-metrics['candidate'][group]/metrics[name][group]
    return metrics,novel,counts,{f'{name}_{group}':relative(name,group) for name in metrics if name not in ('candidate','copy','half') for group in ('changed','novel_changed')},before==after,{'candidate':after[0]-before[0],'control':after[1]-before[1]}


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};hashes_ok=hashes==EXPECTED
    _,v41train,_,_=training_rows(241010);_,v41suite,_=holdout_rows(241110,v41train);old=set(v41train)|{key(world) for _,world,_ in v41suite};_,v42train,_,_,_=fresh_training(242010,old);_,v42suite,_=holdout_rows(242110,old|v42train);old|=v42train|{key(world) for _,world,_ in v42suite};_,vftrain,_,_,_=fresh_training(243010,old);_,vfsuite,_=holdout_rows(243110,old|vftrain);old|=vftrain|{key(world) for _,world,_ in vfsuite}
    srows,sinitials,sraw,sseen,sattempts=fresh_training(245010,old);shold,ssuite,shattempts=holdout_rows(245110,old|sinitials);shold_initials={key(world) for _,world,_ in ssuite};sc=train(srows);sn=train(srows,False);sm,snovel,scount,srelative,sunchanged,swrites=measures(sc,sn,shold,sseen,evaluate_sokoban)
    sgates={'fresh_initials_disjoint':not(old&sinitials) and not(old&shold_initials) and not(sinitials&shold_initials),'novel_context_fraction_at_least_10pct':snovel>=.10,'overall_brier_at_most_0020':sm['candidate']['all']<=.020,'changed_brier_below_025_copy_and_half':sm['candidate']['changed']<.25 and sm['candidate']['changed']<sm['copy']['changed'] and sm['candidate']['changed']<sm['half']['changed'],'novel_changed_brier_at_most_025':sm['candidate']['novel_changed']<=.25,'changed_improves_action_controls_by_10pct':all(srelative[f'{name}_changed']>=.10 for name in ('no_action','rotated')),'novel_changed_improves_action_controls_by_10pct':all(srelative[f'{name}_novel_changed']>=.10 for name in ('no_action','rotated')),'compression_and_quarter_occupancy':len(sraw)>sc.active_cells()/64 and sc.active_cells()<=33343,'evaluation_zero_write_and_unchanged':sunchanged}
    _,pilot_train,_,_,_=lattice_rows(43001,120,1,24);_,pilot_hold,_,_,_=lattice_rows(43002,24,4,24,True,pilot_train);lold=pilot_train|pilot_hold;_,v43train,_,_,_=lattice_rows(244020,120,1,24,False,lold);_,v43hold,_,_,_=lattice_rows(244120,24,4,24,True,lold|v43train);lold|=v43train|v43hold
    lrows,linitials,lraw,lseen,lattempts=lattice_rows(245020,120,1,24,False,lold);lhold,lhold_initials,_,_,lhattempts=lattice_rows(245120,24,4,24,True,lold|linitials);lc=train(lrows);ln=train(lrows,False);lm,lnovel,lcount,lrelative,lunchanged,lwrites=measures(lc,ln,lhold,lseen,evaluate_lattice)
    lgates={'fresh_initials_disjoint':not(lold&linitials) and not(lold&lhold_initials) and not(linitials&lhold_initials),'novel_context_fraction_at_least_25pct':lnovel>=.25,'overall_brier_at_most_0030':lm['candidate']['all']<=.030,'changed_brier_below_025_copy_and_half':lm['candidate']['changed']<.25 and lm['candidate']['changed']<lm['copy']['changed'] and lm['candidate']['changed']<lm['half']['changed'],'novel_changed_brier_at_most_025':lm['candidate']['novel_changed']<=.25,'changed_improves_action_controls_by_10pct':all(lrelative[f'{name}_changed']>=.10 for name in ('no_action','rotated')),'novel_changed_improves_action_controls_by_10pct':all(lrelative[f'{name}_novel_changed']>=.10 for name in ('no_action','rotated')),'changed_improves_phase_flip_by_10pct':lrelative['phase_flipped_changed']>=.10,'novel_changed_improves_phase_flip_by_10pct':lrelative['phase_flipped_novel_changed']>=.10,'compression_and_quarter_occupancy':len(lraw)>lc.active_cells()/64 and lc.active_cells()<=162362,'evaluation_zero_write_and_unchanged':lunchanged}
    tracks=[{'name':'sokoban_physics','training_seed':245010,'holdout_seed':245110,'training_transitions':len(srows),'holdout_transitions':len(shold),'generation_attempts':[sattempts,shattempts],'unique_raw_states':len(sraw),'active_cells':sc.active_cells(),'metrics_brier':sm,'counts':scount,'novel_context_fraction':snovel,'relative_improvement':srelative,'gates':sgates,'pass':all(sgates.values()),'evaluation_writes':swrites},{'name':'causal_particle_lattice','training_seed':245020,'holdout_seed':245120,'training_transitions':len(lrows),'holdout_transitions':len(lhold),'generation_attempts':[lattempts,lhattempts],'unique_raw_states':len(lraw),'active_cells':lc.active_cells(),'metrics_brier':lm,'counts':lcount,'novel_context_fraction':lnovel,'relative_improvement':lrelative,'gates':lgates,'pass':all(lgates.values()),'evaluation_writes':lwrites}]
    result={'frozen_first_execution':True,'version':'v0.44','hashes':hashes,'hashes_match_preregistration':hashes_ok,'full_unit_suite_passed_before_execution':True,'tracks':tracks,'all_tracks_pass':hashes_ok and all(track['pass'] for track in tracks),'seconds':time.perf_counter()-started,'boundary':'Same compact core, fresh weights per domain. Physical prediction only; no goal behavior, weight transfer, or AGI claim.'}
    destination=ROOT/'artifacts'/'v44compressed'/'cross_domain.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
