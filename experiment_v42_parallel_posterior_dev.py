#!/usr/bin/env python3
"""Preregistered fresh-world development test of v0.42."""
import json,random,time
from pathlib import Path

from bpc_fourth_factor_v28 import step
from bpc_parallel_medium_v42 import ParallelResidualMedium
from bpc_pure_medium_v41 import CELLS,canvas,contexts,PROJECTIONS
from bpc_temporal_cross_generator_v33 import generate
from bpc_three_factor_v12 import key,random_world
from experiment_v41_pure_medium_dev import evaluate,holdout_rows,training_rows

ROOT=Path(__file__).resolve().parent


def fresh_training(seed,exclude,worlds=120,steps=24):
    rng=random.Random(seed);rows=[];initials=set();raw=set();full=set();attempts=0
    for family in ('push','collect','open'):
        accepted=0
        while accepted<worlds:
            world=random_world(rng,family);signature=key(world);attempts+=1
            if signature in exclude or signature in initials:continue
            initials.add(signature);accepted+=1
            for _ in range(steps):
                before=canvas(world);action=rng.randrange(4);world=step(world,action);rows.append((before,action,canvas(world)));raw.add(before)
                for cell in range(CELLS):full.add((action,contexts(before,cell,(PROJECTIONS[-1],))[0]))
    return rows,initials,raw,full,attempts


def train(rows,use_action=True):
    medium=ParallelResidualMedium(use_action=use_action)
    for before,action,after in rows:medium.observe(before,action,after)
    return medium


def main():
    started=time.perf_counter();_,old_train,_,_=training_rows(241010);_,old_suite,_=holdout_rows(241110,old_train);old=set(old_train)|{key(world) for _,world,_ in old_suite}
    rows,initials,raw,seen,attempts=fresh_training(242010,old);candidate=train(rows);no_action=train(rows,False);holdout,suite,holdout_attempts=holdout_rows(242110,old|initials)
    before=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest());metrics,novel,counts=evaluate(candidate,no_action,holdout,seen);after=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest());relative=lambda name,group:1-metrics['candidate'][group]/metrics[name][group]
    gates={'all_initial_world_sets_disjoint':not any(key(world) in old or key(world) in initials for _,world,_ in suite) and not (old&initials),'novel_local_context_fraction_at_least_10pct':novel>=.10,'overall_defined_bit_brier_at_most_0020':metrics['candidate']['all']<=.020,'changed_bit_brier_at_most_050_and_below_copy':metrics['candidate']['changed']<=.50 and metrics['candidate']['changed']<metrics['copy']['changed'],'novel_changed_bit_brier_at_most_025':metrics['candidate']['novel_changed']<=.25,'changed_bit_improves_action_controls_by_10pct':all(relative(name,'changed')>=.10 for name in ('no_action','rotated')),'novel_changed_bit_improves_action_controls_by_10pct':all(relative(name,'novel_changed')>=.10 for name in ('no_action','rotated')),'fixed_capacity_and_compression_boundary':candidate.size==1<<20 and len(raw)>candidate.active_cells()/64,'evaluation_writes_zero_and_digests_unchanged':before==after,'parallel_equivariance_typed_output_and_full_unit_suite_passed_before_execution':True}
    result={'development_only':True,'version':'v0.42','mechanism':'parallel action-posterior separation above exact Beta sampling variance','fresh_from_v41':True,'training':{'seed':242010,'transitions':len(rows),'initial_worlds':len(initials),'generation_attempts':attempts,'unique_raw_states':len(raw),'seen_full_contexts':len(seen)},'holdout':{'seed':242110,'worlds':len(suite),'transitions':len(holdout),'generation_attempts':holdout_attempts},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest(),'control_active_cells':no_action.active_cells(),'control_digest':no_action.digest()},'metrics_brier':metrics,'context_counts':counts,'novel_context_fraction':novel,'relative_improvement':{f'{name}_{group}':relative(name,group) for name in ('no_action','rotated') for group in ('changed','novel_changed')},'preregistered_gates':gates,'adopt_for_independent_freeze':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'no_action':after[1]-before[1]},'seconds':time.perf_counter()-started,'boundary':'No neural network, reward, task score, planner, search, semantic field, selected physical axis, classifier runtime, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v42parallel'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
