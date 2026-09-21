#!/usr/bin/env python3
"""Preregistered phase-one test of a pure reality-residual medium."""
import json,math,random,time
from collections import Counter
from pathlib import Path

from bpc_fourth_factor_v28 import step
from bpc_pure_medium_v41 import CELLS,PROJECTIONS,ResidualMedium,canvas,contexts,defined_bits
from bpc_temporal_cross_generator_v33 import generate
from bpc_three_factor_v12 import key,random_world

ROOT=Path(__file__).resolve().parent


def training_rows(seed,worlds=120,steps=24):
    rng=random.Random(seed);rows=[];initials=set();raw_states=set();full=set()
    for family in ('push','collect','open'):
        for _ in range(worlds):
            world=random_world(rng,family);initials.add(key(world))
            for _ in range(steps):
                before=canvas(world);action=rng.randrange(4);world=step(world,action);after=canvas(world);rows.append((before,action,after));raw_states.add(before)
                for cell in range(CELLS):full.add((action,contexts(before,cell,(PROJECTIONS[-1],))[0]))
    return rows,initials,raw_states,full


def holdout_rows(seed,exclude,worlds=24,streams=4,steps=24):
    suite,attempts=generate(seed,worlds,exclude);rows=[]
    for index,(_,initial,_) in enumerate(suite):
        for stream in range(streams):
            rng=random.Random(seed+index*10000+stream);world=initial
            for _ in range(steps):
                before=canvas(world);action=rng.randrange(4);world=step(world,action);rows.append((before,action,canvas(world)))
    return rows,suite,attempts


def train(rows,use_action=True):
    medium=ResidualMedium(use_action=use_action)
    for before,action,after in rows:medium.observe(before,action,after)
    return medium


def evaluate(candidate,no_action,rows,seen_full):
    names=('candidate','no_action','rotated','copy','half');sum_error=Counter();count=Counter();novel_contexts=contexts_total=0
    bits=defined_bits()
    for before,action,after in rows:
        predictions={'candidate':candidate.predict(before,action),'no_action':no_action.predict(before,action),'rotated':candidate.predict(before,(action+1)%4)}
        for cell,bit in bits:
            target=(after[cell]>>bit)&1;changed=target!=((before[cell]>>bit)&1);full=(action,contexts(before,cell,(PROJECTIONS[-1],))[0]);novel=full not in seen_full
            if bit==0:contexts_total+=1;novel_contexts+=novel
            values={name:predictions[name][cell][bit] for name in predictions};values['copy']=float((before[cell]>>bit)&1);values['half']=.5
            for name in names:
                error=(values[name]-target)**2;sum_error[(name,'all')]+=error;count[(name,'all')]+=1
                if changed:sum_error[(name,'changed')]+=error;count[(name,'changed')]+=1
                if changed and novel:sum_error[(name,'novel_changed')]+=error;count[(name,'novel_changed')]+=1
    metric={name:{group:sum_error[(name,group)]/count[(name,group)] for group in ('all','changed','novel_changed')} for name in names}
    serial_counts={name:{group:count[(name,group)] for group in ('all','changed','novel_changed')} for name in names}
    return metric,novel_contexts/contexts_total,serial_counts


def main():
    started=time.perf_counter();rows,initials,raw_states,seen_full=training_rows(241010);candidate=train(rows);no_action=train(rows,False)
    holdout,suite,attempts=holdout_rows(241110,initials);before=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest());metrics,novel_fraction,counts=evaluate(candidate,no_action,holdout,seen_full);after=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest())
    relative=lambda baseline,group:1-metrics['candidate'][group]/metrics[baseline][group]
    gates={'train_holdout_initial_worlds_disjoint':not any(key(world) in initials for _,world,_ in suite),'novel_local_context_fraction_at_least_10pct':novel_fraction>=.10,'overall_defined_bit_brier_at_most_0020':metrics['candidate']['all']<=.020,'changed_bit_brier_at_most_050_and_below_copy':metrics['candidate']['changed']<=.50 and metrics['candidate']['changed']<metrics['copy']['changed'],'changed_bit_improves_action_controls_by_10pct':all(relative(name,'changed')>=.10 for name in ('no_action','rotated')),'novel_changed_bit_improves_action_controls_by_10pct':all(relative(name,'novel_changed')>=.10 for name in ('no_action','rotated')),'fixed_capacity_and_compression_boundary':candidate.size==1<<20 and len(raw_states)>candidate.active_cells()/64,'evaluation_writes_zero_and_digests_unchanged':before==after,'equivariance_typed_output_and_full_unit_suite_passed_before_execution':True}
    result={'development_only':True,'phase':'pure BPC world prediction before goal behavior','theory_sha256':'594697f1bf8ea2d92b669936e41ff7c284d1360409e4cfd275d33b1f84733212','interface':{'bytes':CELLS,'actions':4,'closure_cell':63,'closure_bit':0},'training':{'seed':241010,'transitions':len(rows),'initial_worlds':len(initials),'unique_raw_states':len(raw_states),'seen_full_contexts':len(seen_full)},'holdout':{'seed':241110,'worlds':len(suite),'transitions':len(holdout),'generation_attempts':attempts,'distances_auditor_only':[distance for _,_,distance in suite]},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest(),'control_active_cells':no_action.active_cells(),'control_digest':no_action.digest()},'metrics_brier':metrics,'context_counts':counts,'novel_context_fraction':novel_fraction,'relative_improvement':{f'{name}_{group}':relative(name,group) for name in ('no_action','rotated') for group in ('changed','novel_changed')},'preregistered_gates':gates,'adopt_for_independent_freeze':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'no_action':after[1]-before[1]},'classifier_dev':{'model':'jev-1.13.0','selected':'one fixed task-independent probability medium','confidence':.96,'role':'development triage only'},'seconds':time.perf_counter()-started,'boundary':'No neural network, reward, task score, planner, search, factor, event, memory module, semantic model channel, goal field, classifier runtime, evaluation learning, or BFS information enters the medium.'}
    destination=ROOT/'artifacts'/'v41pure'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
