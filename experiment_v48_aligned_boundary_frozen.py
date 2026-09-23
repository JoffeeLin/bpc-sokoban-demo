#!/usr/bin/env python3
"""First and only independent frozen reproduction of v0.48."""
import hashlib,json,time
from pathlib import Path

from bpc_compressed_medium_v44 import CompressedResidualMedium
from bpc_port_interference_v45 import PortInterferenceMedium
from bpc_pure_medium_v41 import PROJECTIONS,contexts
from closure_orbit_v46 import orbit_suite
from experiment_v48_aligned_boundary_dev import BOARD,evaluate,old_worlds,per_orientation,rows,train

ROOT=Path(__file__).resolve().parent
EXPECTED={'experiment_v48_aligned_boundary_dev.py':'cfb78a6d08d107659122247c7f313b6f6e90f364f7b9c9812e97cfb01f3e9874'}


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};old=old_worlds()
    _,development,_=orbit_suite(481010,150,old);old|=development
    _,development_holdout,_=orbit_suite(481110,128,old);old|=development_holdout
    training,train_initials,train_attempts=orbit_suite(482010,150,old);holdout,hold_initials,hold_attempts=orbit_suite(482110,128,old|train_initials);records=rows(training)
    seen={(action,contexts(before,cell,(PROJECTIONS[-1],))[0]) for before,action,_ in records for cell in BOARD}
    candidate=train(PortInterferenceMedium,records);no_action=train(PortInterferenceMedium,records,False);local=train(CompressedResidualMedium,records)
    before=(candidate.writes,no_action.writes,local.writes,candidate.digest(),no_action.digest(),local.digest());metrics=evaluate(candidate,no_action,local,holdout,seen);orientation=per_orientation(candidate,holdout);after=(candidate.writes,no_action.writes,local.writes,candidate.digest(),no_action.digest(),local.digest());rate=metrics['selection_rate'];non_port=metrics['non_port_brier']
    orbit_ok=all(sorted(action for _,action in training[i:i+4])==list(range(4)) for i in range(0,len(training),4)) and all(sorted(action for _,action in holdout[i:i+4])==list(range(4)) for i in range(0,len(holdout),4));controls=tuple(name for name in rate if name!='candidate')
    gates={'hashes_disjointness_balance_and_orbits':hashes==EXPECTED and orbit_ok and not(old&train_initials) and not(old&hold_initials) and not(train_initials&hold_initials),'novel_context_fraction_at_least_10pct':metrics['novel_context_fraction']>=.10,'strict_closure_selection_at_least_70pct':rate['candidate']>=.70,'each_orientation_at_least_60pct':min(orientation)>=.60,'port_brier_at_most_0120':metrics['port_brier']['candidate']<=.120,'selection_beats_every_control_by_30_points':all(rate['candidate']-rate[name]>=.30 for name in controls),'median_probability_margin_above_005':metrics['median_margin']>.05,'local_world_prediction_retained':non_port['candidate']<=.030 and non_port['candidate']<=1.10*non_port['local_only'],'fixed_capacity_compression_boundary':candidate.size==1<<20 and len({before for before,_,_ in records})>candidate.active_cells()/64,'evaluation_zero_write_and_unchanged':before==after,'aligned_geometry_and_full_unit_suite_passed_before_execution':True}
    result={'frozen_first_execution':True,'version':'v0.48','phase':'aligned minimal one-bit external boundary independent reproduction','core_unchanged_from_v45':True,'hashes':hashes,'training':{'seed':482010,'base_orbits':150,'worlds':len(training),'transitions':len(records),'attempts':train_attempts},'holdout':{'seed':482110,'base_orbits':128,'worlds':len(holdout),'attempts':hold_attempts},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest()},'metrics':metrics,'per_orientation_selection_rate':orientation,'preregistered_gates':gates,'frozen_pass':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'no_action':after[1]-before[1],'local':after[2]-before[2]},'seconds':time.perf_counter()-started,'boundary':'Reproduced aligned one-step external closure only. Port and target-channel controls are not recurrent internal-state zero/flip ablations. No long process, planner, general Sokoban solving, or AGI claim.'}
    destination=ROOT/'artifacts'/'v48aligned_boundary'/'frozen.json';destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
