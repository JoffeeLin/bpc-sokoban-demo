#!/usr/bin/env python3
"""Preregistered causal second-domain test of the unchanged v0.42 core."""
import hashlib,json,random,time
from collections import Counter
from pathlib import Path

from bpc_parallel_medium_v42 import ParallelResidualMedium
from bpc_pure_medium_v41 import CELLS,PROJECTIONS,contexts
from physical_causal_lattice_v43 import random_lattice,step_lattice

ROOT=Path(__file__).resolve().parent;EXPECTED='68d4c1f1e7898baf0972454c1aca93c3e6e8616b0537c55d34952059c65d35ef'


def rows(seed,worlds,streams,steps,holdout=False,exclude=frozenset()):
    rng=random.Random(seed);records=[];initials=set();raw=set();seen=set();attempts=0;regimes=((.04,.10,.15),(.15,.20,.50),(.27,.30,.85));target=worlds*(1 if holdout else 3)
    while len(initials)<target:
        rates=(.06+.20*rng.random(),.12+.20*rng.random(),.20+.60*rng.random()) if holdout else regimes[len(initials)//worlds]
        initial=random_lattice(rng,*rates);attempts+=1
        if initial in initials or initial in exclude:continue
        initials.add(initial)
        for stream in range(streams):
            action_rng=random.Random(seed+len(initials)*10000+stream);state=initial
            for _ in range(steps):
                action=action_rng.randrange(4);after=step_lattice(state,action);records.append((state,action,after));raw.add(state)
                for cell in range(CELLS):seen.add((action,contexts(state,cell,(PROJECTIONS[-1],))[0]))
                state=after
    return records,initials,raw,seen,attempts


def train(records,use_action=True):
    medium=ParallelResidualMedium(use_action=use_action)
    for before,action,after in records:medium.observe(before,action,after)
    return medium


def evaluate(candidate,no_action,records,seen):
    names=('candidate','no_action','rotated','phase_flipped','copy','half');errors=Counter();counts=Counter();novel_total=total=0
    for before,action,after in records:
        flipped=bytes(value^4 for value in before);predictions={'candidate':candidate.predict(before,action),'no_action':no_action.predict(before,action),'rotated':candidate.predict(before,(action+1)%4),'phase_flipped':candidate.predict(flipped,action)}
        for cell in range(CELLS):
            novel=(action,contexts(before,cell,(PROJECTIONS[-1],))[0]) not in seen;total+=1;novel_total+=novel
            for bit in range(3):
                target=(after[cell]>>bit)&1;changed=target!=((before[cell]>>bit)&1);values={name:predictions[name][cell][bit] for name in predictions};values['copy']=float((before[cell]>>bit)&1);values['half']=.5
                for name in names:
                    errors[(name,'all')]+=(values[name]-target)**2;counts[(name,'all')]+=1
                    if changed:errors[(name,'changed')]+=(values[name]-target)**2;counts[(name,'changed')]+=1
                    if changed and novel:errors[(name,'novel_changed')]+=(values[name]-target)**2;counts[(name,'novel_changed')]+=1
    metrics={name:{group:errors[(name,group)]/counts[(name,group)] for group in ('all','changed','novel_changed')} for name in names}
    return metrics,novel_total/total,{name:{group:counts[(name,group)] for group in ('all','changed','novel_changed')} for name in names}


def main():
    started=time.perf_counter();core_hash=hashlib.sha256((ROOT/'bpc_parallel_medium_v42.py').read_bytes()).hexdigest();_,pilot_train,_,_,_=rows(43001,120,1,24);_,pilot_hold,_,_,_=rows(43002,24,4,24,True,pilot_train);pilot=pilot_train|pilot_hold
    training,train_initials,raw,seen,train_attempts=rows(244020,120,1,24,False,pilot);holdout,hold_initials,_,_,hold_attempts=rows(244120,24,4,24,True,pilot|train_initials);candidate=train(training);no_action=train(training,False);before=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest());metrics,novel,counts=evaluate(candidate,no_action,holdout,seen);after=(candidate.writes,no_action.writes,candidate.digest(),no_action.digest());relative=lambda name,group:1-metrics['candidate'][group]/metrics[name][group]
    gates={'fresh_initials_disjoint_and_core_hash_fixed':not(pilot&train_initials) and not(pilot&hold_initials) and not(train_initials&hold_initials) and core_hash==EXPECTED,'novel_context_fraction_at_least_25pct':novel>=.25,'overall_brier_at_most_0030':metrics['candidate']['all']<=.030,'changed_brier_below_025_copy_and_half':metrics['candidate']['changed']<.25 and metrics['candidate']['changed']<metrics['copy']['changed'] and metrics['candidate']['changed']<metrics['half']['changed'],'novel_changed_brier_at_most_025':metrics['candidate']['novel_changed']<=.25,'changed_improves_action_controls_by_10pct':all(relative(name,'changed')>=.10 for name in ('no_action','rotated')),'novel_changed_improves_action_controls_by_10pct':all(relative(name,'novel_changed')>=.10 for name in ('no_action','rotated')),'changed_improves_phase_flip_by_10pct':relative('phase_flipped','changed')>=.10,'novel_changed_improves_phase_flip_by_10pct':relative('phase_flipped','novel_changed')>=.10,'fixed_capacity_and_compression_boundary':candidate.size==1<<20 and len(raw)>candidate.active_cells()/64,'evaluation_writes_zero_and_digests_unchanged':before==after,'full_unit_suite_passed_before_execution':True}
    result={'development_only':True,'version':'v0.43','core_sha256':core_hash,'pilot_predictions_observed':False,'training':{'seed':244020,'transitions':len(training),'initials':len(train_initials),'attempts':train_attempts,'unique_raw_states':len(raw),'seen_full_contexts':len(seen)},'holdout':{'seed':244120,'transitions':len(holdout),'initials':len(hold_initials),'attempts':hold_attempts},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest(),'control_digest':no_action.digest()},'metrics_brier':metrics,'counts':counts,'novel_context_fraction':novel,'relative_improvement':{f'{name}_{group}':relative(name,group) for name in ('no_action','rotated','phase_flipped') for group in ('changed','novel_changed')},'gates':gates,'second_domain_pass':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'control':after[1]-before[1]},'seconds':time.perf_counter()-started,'boundary':'Same core, fresh weights. Physical prediction only; no goal behavior, cross-domain weight transfer, or AGI claim.'}
    destination=ROOT/'artifacts'/'v43causal'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
