#!/usr/bin/env python3
"""Preregistered development revalidation of phase-one aligned Sokoban physics."""
import hashlib,json,random,time
from collections import Counter
from pathlib import Path

from bpc_aligned_canvas_v47 import aligned_canvas
from bpc_compressed_medium_v44 import CompressedResidualMedium
from bpc_fourth_factor_v28 import step
from bpc_pure_medium_v41 import CELLS,PROJECTIONS,contexts,defined_bits
from bpc_temporal_cross_generator_v33 import generate
from bpc_three_factor_v12 import key,random_world
from experiment_v41_pure_medium_dev import holdout_rows,training_rows
from experiment_v42_parallel_posterior_dev import fresh_training

ROOT=Path(__file__).resolve().parent
EXPECTED={'bpc_aligned_canvas_v47.py':'49a3c9bd98797a867641783f9659108254d98ff2fb85c38f62ba71f710606186',
    'bpc_compressed_medium_v44.py':'db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6',
    'bpc_parallel_medium_v42.py':'68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef',
    'bpc_pure_medium_v41.py':'e1893081144c47f97191b4b82c9e5d7959774951e3f7bc05860c8d06fe1122cf'}


def old_initials():
    """All v0.41/v0.42/v0.44 Sokoban initials; bytes are irrelevant here."""
    _,train,_,_=training_rows(241010);_,suite,_=holdout_rows(241110,train);old=set(train)|{key(w) for _,w,_ in suite}
    _,train,_,_,_=fresh_training(242010,old);_,suite,_=holdout_rows(242110,old|train);old|=train|{key(w) for _,w,_ in suite}
    _,train,_,_,_=fresh_training(243010,old);_,suite,_=holdout_rows(243110,old|train);old|=train|{key(w) for _,w,_ in suite}
    _,train,_,_,_=fresh_training(245010,old);_,suite,_=holdout_rows(245110,old|train);return old|train|{key(w) for _,w,_ in suite}


def training(seed,exclude,worlds=120,steps=24):
    rng=random.Random(seed);records=[];initials=set();raw=set();full=set();attempts=0
    for family in ('push','collect','open'):
        accepted=0
        while accepted<worlds:
            world=random_world(rng,family);identity=key(world);attempts+=1
            if identity in exclude or identity in initials:continue
            initials.add(identity);accepted+=1
            for _ in range(steps):
                before=aligned_canvas(world);action=rng.randrange(4);world=step(world,action);after=aligned_canvas(world)
                records.append((before,action,after));raw.add(before)
                for cell in range(CELLS):full.add((action,contexts(before,cell,(PROJECTIONS[-1],))[0]))
    return records,initials,raw,full,attempts


def holdout(seed,exclude,worlds=24,streams=4,steps=24):
    suite,attempts=generate(seed,worlds,exclude);records=[]
    for index,(_,initial,_) in enumerate(suite):
        for stream in range(streams):
            rng=random.Random(seed+index*10000+stream);world=initial
            for _ in range(steps):
                before=aligned_canvas(world);action=rng.randrange(4);world=step(world,action);records.append((before,action,aligned_canvas(world)))
    return records,suite,attempts


def train(records,use_action=True):
    medium=CompressedResidualMedium(use_action=use_action)
    for before,action,after in records:medium.observe(before,action,after)
    return medium


def evaluate(candidate,no_action,records,seen):
    names=('candidate','no_action','rotated','copy','half');errors=Counter();counts=Counter();novel=total=0
    for before,action,after in records:
        predictions={'candidate':candidate.predict(before,action),'no_action':no_action.predict(before,action),'rotated':candidate.predict(before,(action+1)%4)}
        for cell,bit in defined_bits():
            target=(after[cell]>>bit)&1;changed=target!=((before[cell]>>bit)&1);unseen=(action,contexts(before,cell,(PROJECTIONS[-1],))[0]) not in seen
            if bit==0:total+=1;novel+=unseen
            values={name:predictions[name][cell][bit] for name in predictions};values['copy']=float((before[cell]>>bit)&1);values['half']=.5
            for name in names:
                error=(values[name]-target)**2;errors[name,'all']+=error;counts[name,'all']+=1
                if changed:errors[name,'changed']+=error;counts[name,'changed']+=1
                if changed and unseen:errors[name,'novel_changed']+=error;counts[name,'novel_changed']+=1
    metrics={name:{group:errors[name,group]/counts[name,group] for group in ('all','changed','novel_changed')} for name in names}
    return metrics,novel/total,{name:{group:counts[name,group] for group in ('all','changed','novel_changed')} for name in names}


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};old=old_initials()
    rows,initials,raw,seen,attempts=training(247010,old);records,suite,holdout_attempts=holdout(247110,old|initials);holdout_initials={key(w) for _,w,_ in suite}
    candidate,no_action=train(rows),train(rows,False);before=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest());metrics,novel,counts=evaluate(candidate,no_action,records,seen);after=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest())
    relative=lambda name,group:1-metrics['candidate'][group]/metrics[name][group]
    gates={'hashes_match_preregistration':hashes==EXPECTED,'fresh_initials_disjoint':not(old&initials) and not(old&holdout_initials) and not(initials&holdout_initials),'novel_context_fraction_at_least_10pct':novel>=.10,'overall_brier_at_most_0020':metrics['candidate']['all']<=.020,'changed_brier_below_025_copy_and_half':metrics['candidate']['changed']<.25 and metrics['candidate']['changed']<metrics['copy']['changed'] and metrics['candidate']['changed']<metrics['half']['changed'],'novel_changed_brier_at_most_025':metrics['candidate']['novel_changed']<=.25,'changed_improves_action_controls_by_10pct':all(relative(name,'changed')>=.10 for name in ('no_action','rotated')),'novel_changed_improves_action_controls_by_10pct':all(relative(name,'novel_changed')>=.10 for name in ('no_action','rotated')),'compression_and_v44_occupancy_ceiling':len(raw)>candidate.active_cells()/64 and candidate.active_cells()<=33343,'evaluation_zero_write_and_unchanged':before==after,'aligned_geometry_and_full_unit_suite_passed_before_execution':True}
    result={'development_only':True,'version':'v0.47','phase':'phase-one aligned Sokoban world prediction revalidation','hashes':hashes,'training':{'seed':247010,'transitions':len(rows),'initial_worlds':len(initials),'generation_attempts':attempts,'unique_raw_states':len(raw),'seen_full_contexts':len(seen)},'holdout':{'seed':247110,'worlds':len(suite),'transitions':len(records),'generation_attempts':holdout_attempts},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest(),'control_digest':no_action.digest()},'metrics_brier':metrics,'context_counts':counts,'novel_context_fraction':novel,'relative_improvement':{f'{name}_{group}':relative(name,group) for name in ('no_action','rotated') for group in ('changed','novel_changed')},'preregistered_gates':gates,'adopt_for_independent_freeze':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'no_action':after[1]-before[1]},'seconds':time.perf_counter()-started,'boundary':'Correctly aligned camera, physical next-state prediction only. No reward, task score, planner, search, goal behavior, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v47aligned'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
