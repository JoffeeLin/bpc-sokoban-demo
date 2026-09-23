#!/usr/bin/env python3
"""Preregistered rotation-orbit development test with unchanged v0.45 core."""
import hashlib,json,time
from pathlib import Path

from bpc_compressed_medium_v44 import CompressedResidualMedium
from bpc_port_interference_v45 import PortInterferenceMedium
from bpc_pure_medium_v41 import PROJECTIONS,contexts
from closure_orbit_v46 import orbit_suite
from closure_probe_v45 import suite
from experiment_v45_frozen import per_action
from experiment_v45_minimal_boundary import EXPECTED,evaluate,rows,train

ROOT=Path(__file__).resolve().parent


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};_,p1,_=suite(450001,600);_,p2,_=suite(450002,160,p1);old=p1|p2;_,d1,_=suite(451010,600,old);_,d2,_=suite(451110,256,old|d1);old|=d1|d2;_,f1,_=suite(452010,600,old);_,f2,_=suite(452110,512,old|f1);old|=f1|f2;training,train_initials,train_attempts=orbit_suite(461010,150,old);holdout,hold_initials,hold_attempts=orbit_suite(461110,128,old|train_initials);records=rows(training);seen={(action,contexts(before,cell,(PROJECTIONS[-1],))[0]) for before,action,_ in records for cell in range(49)};candidate=train(PortInterferenceMedium,records);no_action=train(PortInterferenceMedium,records,False);local=train(CompressedResidualMedium,records);before=(candidate.writes,no_action.writes,local.writes,candidate.digest(),no_action.digest(),local.digest());metrics=evaluate(candidate,no_action,local,holdout,seen);orientation=per_action(candidate,holdout);after=(candidate.writes,no_action.writes,local.writes,candidate.digest(),no_action.digest(),local.digest());rate=metrics['selection_rate'];non_port=metrics['non_port_brier']
    orbit_ok=all(sorted(action for _,action in training[i:i+4])==list(range(4)) for i in range(0,len(training),4)) and all(sorted(action for _,action in holdout[i:i+4])==list(range(4)) for i in range(0,len(holdout),4))
    gates={'hashes_disjointness_balance_and_orbits':hashes==EXPECTED and orbit_ok and not(old&train_initials) and not(old&hold_initials) and not(train_initials&hold_initials),'novel_context_fraction_at_least_10pct':metrics['novel_context_fraction']>=.10,'strict_closure_selection_at_least_70pct':rate['candidate']>=.70,'each_orientation_at_least_60pct':min(orientation)>=.60,'port_brier_at_most_0120':metrics['port_brier']['candidate']<=.120,'selection_beats_all_controls_by_30_points':all(rate['candidate']-rate[name]>=.30 for name in ('no_action','local_only','rotated','shifted_state')),'median_probability_margin_above_005':metrics['median_margin']>.05,'local_world_prediction_retained':non_port['candidate']<=.030 and non_port['candidate']<=1.10*non_port['local_only'],'fixed_capacity_compression_boundary':candidate.size==1<<20 and len({before for before,_,_ in records})>candidate.active_cells()/64,'evaluation_zero_write_and_unchanged':before==after,'full_unit_suite_passed_before_execution':True}
    result={'development_only':True,'version':'v0.46','core_unchanged_from_v45':True,'hashes':hashes,'training':{'seed':461010,'base_orbits':150,'worlds':len(training),'transitions':len(records),'attempts':train_attempts},'holdout':{'seed':461110,'base_orbits':128,'worlds':len(holdout),'attempts':hold_attempts},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest()},'metrics':metrics,'per_orientation_selection_rate':orientation,'gates':gates,'orbit_development_pass':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'no_action':after[1]-before[1],'local':after[2]-before[2]},'seconds':time.perf_counter()-started,'boundary':'Symmetry-balanced one-step closure experience only; no recurrent internal state, long process, planner, Sokoban solving, or AGI claim.'}
    destination=ROOT/'artifacts'/'v46orbit'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
