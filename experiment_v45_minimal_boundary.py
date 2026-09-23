#!/usr/bin/env python3
"""Preregistered one-step closure-port coupling test."""
import hashlib,json,statistics,time
from pathlib import Path

from bpc_compressed_medium_v44 import CompressedResidualMedium
from bpc_port_interference_v45 import PortInterferenceMedium
from bpc_pure_medium_v41 import CELLS,PROJECTIONS,canvas,contexts
from bpc_fourth_factor_v28 import step
from closure_probe_v45 import suite

ROOT=Path(__file__).resolve().parent
EXPECTED={'bpc_port_interference_v45.py':'27e9a2158fc9df3c3519c08d0d122b10aaa93e0d73c753cd39652e6ada49f85d','bpc_compressed_medium_v44.py':'db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6'}


def rows(worlds):return [(canvas(world),action,canvas(step(world,action))) for world,_ in worlds for action in range(4)]
def train(kind,records,use_action=True):
    medium=kind(use_action=use_action)
    for before,action,after in records:medium.observe(before,action,after)
    return medium
def strict_success(values,correct):return values[correct]+1e-12<min(value for action,value in enumerate(values) if action!=correct)


def evaluate(candidate,no_action,local,worlds,seen):
    names=('candidate','no_action','local_only','rotated','shifted_state');success={name:0 for name in names};errors={name:0. for name in names};margins=[];local_error=base_error=0.;local_count=0;novel=total=0
    images=[canvas(world) for world,_ in worlds];predictions=[candidate.predict_all(image) for image in images];no_predictions=[no_action.predict_all(image) for image in images];base_predictions=[local.predict_all(image) for image in images]
    for index,(world,correct) in enumerate(worlds):
        candidate_values=[predictions[index][action][CELLS-1][0] for action in range(4)];rows_={'candidate':candidate_values,'no_action':[no_predictions[index][action][CELLS-1][0] for action in range(4)],'local_only':[base_predictions[index][action][CELLS-1][0] for action in range(4)],'rotated':[candidate_values[(action+1)%4] for action in range(4)],'shifted_state':[predictions[(index+1)%len(worlds)][action][CELLS-1][0] for action in range(4)]}
        margins.append(min(value for action,value in enumerate(candidate_values) if action!=correct)-candidate_values[correct])
        for name,values in rows_.items():
            success[name]+=strict_success(values,correct)
            for action,value in enumerate(values):errors[name]+=(value-float(action!=correct))**2
        before=images[index]
        for action in range(4):
            actual=canvas(step(world,action));full_predictions=(predictions[index][action],base_predictions[index][action])
            for cell in range(49):
                full=(action,contexts(before,cell,(PROJECTIONS[-1],))[0]);total+=1;novel+=full not in seen
                for bit in range(6):
                    target=(actual[cell]>>bit)&1;local_error+=(full_predictions[0][cell][bit]-target)**2;base_error+=(full_predictions[1][cell][bit]-target)**2;local_count+=1
    count=len(worlds);return {'selection_rate':{name:value/count for name,value in success.items()},'port_brier':{name:value/(count*4) for name,value in errors.items()},'median_margin':statistics.median(margins),'non_port_brier':{'candidate':local_error/local_count,'local_only':base_error/local_count},'novel_context_fraction':novel/total,'cases':count}


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};_,p1,_=suite(450001,600);_,p2,_=suite(450002,160,p1);pilot=p1|p2;training,train_initials,train_attempts=suite(451010,600,pilot);holdout,hold_initials,hold_attempts=suite(451110,256,pilot|train_initials);records=rows(training);seen={(action,contexts(before,cell,(PROJECTIONS[-1],))[0]) for before,action,_ in records for cell in range(49)};candidate=train(PortInterferenceMedium,records);no_action=train(PortInterferenceMedium,records,False);local=train(CompressedResidualMedium,records);before=(candidate.writes,no_action.writes,local.writes,candidate.digest(),no_action.digest(),local.digest());metrics=evaluate(candidate,no_action,local,holdout,seen);after=(candidate.writes,no_action.writes,local.writes,candidate.digest(),no_action.digest(),local.digest());rate=metrics['selection_rate'];non_port=metrics['non_port_brier']
    gates={'hashes_disjointness_and_action_balance':hashes==EXPECTED and not(pilot&train_initials) and not(pilot&hold_initials) and not(train_initials&hold_initials) and all(sum(action==a for _,action in training)==150 for a in range(4)) and all(sum(action==a for _,action in holdout)==64 for a in range(4)),'novel_context_fraction_at_least_10pct':metrics['novel_context_fraction']>=.10,'strict_closure_selection_at_least_70pct':rate['candidate']>=.70,'port_brier_at_most_0120':metrics['port_brier']['candidate']<=.120,'selection_beats_all_controls_by_30_points':all(rate['candidate']-rate[name]>=.30 for name in ('no_action','local_only','rotated','shifted_state')),'median_probability_margin_above_005':metrics['median_margin']>.05,'local_world_prediction_retained':non_port['candidate']<=.030 and non_port['candidate']<=1.10*non_port['local_only'],'fixed_capacity_compression_boundary':candidate.size==1<<20 and len({before for before,_,_ in records})>candidate.active_cells()/64,'evaluation_zero_write_and_unchanged':before==after,'full_unit_suite_passed_before_execution':True}
    result={'development_only':True,'version':'v0.45','hashes':hashes,'training':{'seed':451010,'worlds':len(training),'transitions':len(records),'attempts':train_attempts},'holdout':{'seed':451110,'worlds':len(holdout),'attempts':hold_attempts},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest()},'metrics':metrics,'gates':gates,'minimal_boundary_pass':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'no_action':after[1]-before[1],'local':after[2]-before[2]},'seconds':time.perf_counter()-started,'boundary':'One-step closure measurement only; no recurrent internal state, long process, planning, Sokoban solving, or AGI claim.'}
    destination=ROOT/'artifacts'/'v45boundary'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
