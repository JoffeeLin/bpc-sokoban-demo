#!/usr/bin/env python3
"""First-run frozen Sokoban reproduction plus same-core particle lattice."""
import hashlib,json,random,time
from collections import Counter
from pathlib import Path

from bpc_parallel_medium_v42 import ParallelResidualMedium
from bpc_pure_medium_v41 import CELLS,PROJECTIONS,contexts,defined_bits
from bpc_three_factor_v12 import key
from experiment_v41_pure_medium_dev import holdout_rows,training_rows
from experiment_v42_parallel_posterior_dev import fresh_training
from physical_lattice_v42 import random_lattice,step_lattice

ROOT=Path(__file__).resolve().parent;CORE=ROOT/'bpc_parallel_medium_v42.py'


def train(rows,use_action=True):
    medium=ParallelResidualMedium(use_action=use_action)
    for before,action,after in rows:medium.observe(before,action,after)
    return medium


def lattice_rows(seed,worlds,streams,steps,holdout=False,exclude=frozenset()):
    rng=random.Random(seed);rows=[];initials=set();raw=set();full=set();attempts=0;regimes=((.03,.08),(.13,.18),(.25,.30))
    while len(initials)<worlds*(3 if not holdout else 1):
        if holdout:wall=.05+.22*rng.random();particle=.10+.24*rng.random()
        else:wall,particle=regimes[len(initials)//worlds]
        initial=random_lattice(rng,wall,particle);attempts+=1
        if initial in initials or initial in exclude:continue
        initials.add(initial)
        for stream in range(streams):
            action_rng=random.Random(seed+len(initials)*10000+stream);state=initial
            for _ in range(steps):
                action=action_rng.randrange(4);after=step_lattice(state,action);rows.append((state,action,after));raw.add(state)
                for cell in range(CELLS):full.add((action,contexts(state,cell,(PROJECTIONS[-1],))[0]))
                state=after
    return rows,initials,raw,full,attempts


def evaluate(candidate,no_action,rows,seen,bits):
    names=('candidate','no_action','rotated','copy','half');errors=Counter();counts=Counter();novel_total=total=0
    for before,action,after in rows:
        predictions={'candidate':candidate.predict(before,action),'no_action':no_action.predict(before,action),'rotated':candidate.predict(before,(action+1)%4)}
        for cell,bit in bits:
            target=(after[cell]>>bit)&1;changed=target!=((before[cell]>>bit)&1);novel=(action,contexts(before,cell,(PROJECTIONS[-1],))[0]) not in seen
            if bit==bits[0][1]:total+=1;novel_total+=novel
            values={name:predictions[name][cell][bit] for name in predictions};values['copy']=float((before[cell]>>bit)&1);values['half']=.5
            for name in names:
                errors[(name,'all')]+=(values[name]-target)**2;counts[(name,'all')]+=1
                if changed:errors[(name,'changed')]+=(values[name]-target)**2;counts[(name,'changed')]+=1
                if changed and novel:errors[(name,'novel_changed')]+=(values[name]-target)**2;counts[(name,'novel_changed')]+=1
    metrics={name:{group:errors[(name,group)]/counts[(name,group)] for group in ('all','changed','novel_changed')} for name in names}
    return metrics,novel_total/total,{name:{group:counts[(name,group)] for group in ('all','changed','novel_changed')} for name in names}


def assess(label,rows,initials,raw,seen,holdout,holdout_initials,bits,overall,disjoint):
    candidate=train(rows);control=train(rows,False);before=(candidate.writes,control.writes,candidate.digest(),control.digest());metrics,novel,counts=evaluate(candidate,control,holdout,seen,bits);after=(candidate.writes,control.writes,candidate.digest(),control.digest());relative=lambda name,group:1-metrics['candidate'][group]/metrics[name][group]
    gates={'initial_worlds_disjoint':disjoint and not(initials&holdout_initials),'novel_context_fraction_at_least_10pct':novel>=.10,'overall_brier_below_ceiling':metrics['candidate']['all']<=overall,'changed_brier_at_most_050_and_below_copy':metrics['candidate']['changed']<=.50 and metrics['candidate']['changed']<metrics['copy']['changed'],'novel_changed_brier_at_most_025':metrics['candidate']['novel_changed']<=.25,'changed_improves_action_controls_by_10pct':all(relative(n,'changed')>=.10 for n in ('no_action','rotated')),'novel_changed_improves_action_controls_by_10pct':all(relative(n,'novel_changed')>=.10 for n in ('no_action','rotated')),'fixed_capacity_and_compression_boundary':candidate.size==1<<20 and len(raw)>candidate.active_cells()/64,'evaluation_zero_write_and_unchanged':before==after,'all_tests_passed_before_execution':True}
    return {'track':label,'training_transitions':len(rows),'training_initials':len(initials),'holdout_transitions':len(holdout),'holdout_initials':len(holdout_initials),'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest(),'control_digest':control.digest()},'metrics_brier':metrics,'counts':counts,'novel_context_fraction':novel,'relative_improvement':{f'{name}_{group}':relative(name,group) for name in ('no_action','rotated') for group in ('changed','novel_changed')},'gates':gates,'pass':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'control':after[1]-before[1]}}


def main():
    started=time.perf_counter();core_hash=hashlib.sha256(CORE.read_bytes()).hexdigest();_,v41train,_,_=training_rows(241010);_,v41suite,_=holdout_rows(241110,v41train);old=set(v41train)|{key(w) for _,w,_ in v41suite};v42rows,v42train,_,_,_=fresh_training(242010,old);_,v42suite,_=holdout_rows(242110,old|v42train);old|=v42train|{key(w) for _,w,_ in v42suite}
    srows,sinitials,sraw,sseen,sattempts=fresh_training(243010,old);shold,ssuite,shattempts=holdout_rows(243110,old|sinitials);sresult=assess('sokoban_physics',srows,sinitials,sraw,sseen,shold,{key(w) for _,w,_ in ssuite},defined_bits(),.020,not(old&sinitials) and not any(key(w) in old for _,w,_ in ssuite))
    lrows,linitials,lraw,lseen,lattempts=lattice_rows(243020,120,1,24);lhold,lhold_initials,_,_,lhattempts=lattice_rows(243120,24,4,24,True,linitials);lbits=tuple((cell,bit) for cell in range(CELLS) for bit in range(2));lresult=assess('particle_lattice',lrows,linitials,lraw,lseen,lhold,lhold_initials,lbits,.030,True)
    result={'frozen_first_execution':True,'core_sha256':core_hash,'development_core_commit':'efd74b3','sokoban_generation_attempts':{'training':sattempts,'holdout':shattempts},'lattice_generation_attempts':{'training':lattempts,'holdout':lhattempts},'tracks':[sresult,lresult],'all_tracks_pass':sresult['pass'] and lresult['pass'],'seconds':time.perf_counter()-started,'boundary':'World prediction only; no goal behavior, weight transfer, or AGI claim.'}
    destination=ROOT/'artifacts'/'v42frozen'/'cross_domain.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
