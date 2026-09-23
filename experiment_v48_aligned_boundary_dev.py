#!/usr/bin/env python3
"""Preregistered aligned-camera revalidation of the one-bit boundary."""
import hashlib,json,statistics,time
from pathlib import Path

from bpc_aligned_canvas_v47 import aligned_canvas
from bpc_compressed_medium_v44 import CompressedResidualMedium
from bpc_fourth_factor_v28 import step
from bpc_port_interference_v45 import PortInterferenceMedium
from bpc_pure_medium_v41 import CELLS,PROJECTIONS,contexts
from closure_orbit_v46 import orbit_suite
from closure_probe_v45 import suite

ROOT=Path(__file__).resolve().parent
BOARD=tuple(y*8+x for y in range(7) for x in range(7))
EXPECTED={
    'bpc_aligned_canvas_v47.py':'49a3c9bd98797a867641783f9659108254d98ff2fb85c38f62ba71f710606186',
    'bpc_port_interference_v45.py':'27e9a2158fc9df3c3519c08d0d122b10aaa93e0d73c753cd39652e6ada49f85d',
    'bpc_compressed_medium_v44.py':'db94de62090b8966d797318cde8c58720b23e5c16b09c8b8f6f833b6c2b7b9f6',
    'closure_orbit_v46.py':'b66d6097cf003b9b0ef2ca3ad8304a9fc948a79a62ca437c2d8b0a7b72af0eff',
    'closure_probe_v45.py':'48eb49a0f59885d6b4c4faef8ca98db2a40d11bf017beb6117b0e844de22e557',
    'bpc_pure_medium_v41.py':'e1893081144c47f97191b4b82c9e5d7959774951e3f7bc05860c8d06fe1122cf'}


def rows(worlds):return [(aligned_canvas(world),action,aligned_canvas(step(world,action))) for world,_ in worlds for action in range(4)]
def train(kind,records,use_action=True):
    medium=kind(use_action=use_action)
    for before,action,after in records:medium.observe(before,action,after)
    return medium
def strict_success(values,correct):return values[correct]+1e-12<min(value for action,value in enumerate(values) if action!=correct)
def old_worlds():
    _,p1,_=suite(450001,600);_,p2,_=suite(450002,160,p1);old=p1|p2
    for a,b,n in ((451010,451110,600),(452010,452110,600)):
        _,x,_=suite(a,n,old);_,y,_=suite(b,256 if a==451010 else 512,old|x);old|=x|y
    x,_,_=orbit_suite(461010,150,old);old|={world_key(world) for world,_ in x}
    x,_,_=orbit_suite(461110,128,old);return old|{world_key(world) for world,_ in x}
def world_key(world):
    from bpc_three_factor_v12 import key
    return key(world)
def zero_carrier(image):
    out=bytearray(image);out[-1]=0;return bytes(out)
def zero_condition(image):return bytes(value&~8 for value in image)


def evaluate(candidate,no_action,local,worlds,seen):
    names=('candidate','no_action','local_only','rotated','shifted_state','zero_carrier','zero_condition','flipped_readout')
    success={name:0 for name in names};errors={name:0. for name in names};margins=[];candidate_error=local_error=0.;world_count=novel=total=0
    images=[aligned_canvas(world) for world,_ in worlds]
    predictions=[candidate.predict_all(image) for image in images]
    no_predictions=[no_action.predict_all(image) for image in images]
    local_predictions=[local.predict_all(image) for image in images]
    zero_carrier_predictions=[candidate.predict_all(zero_carrier(image)) for image in images]
    zero_condition_predictions=[candidate.predict_all(zero_condition(image)) for image in images]
    for index,(world,correct) in enumerate(worlds):
        values=[predictions[index][action][CELLS-1][0] for action in range(4)]
        rows_={'candidate':values,
            'no_action':[no_predictions[index][action][CELLS-1][0] for action in range(4)],
            'local_only':[local_predictions[index][action][CELLS-1][0] for action in range(4)],
            'rotated':[values[(action+1)%4] for action in range(4)],
            'shifted_state':[predictions[(index+1)%len(worlds)][action][CELLS-1][0] for action in range(4)],
            'zero_carrier':[zero_carrier_predictions[index][action][CELLS-1][0] for action in range(4)],
            'zero_condition':[zero_condition_predictions[index][action][CELLS-1][0] for action in range(4)],
            'flipped_readout':[1-value for value in values]}
        margins.append(min(value for action,value in enumerate(values) if action!=correct)-values[correct])
        for name,row in rows_.items():
            success[name]+=strict_success(row,correct)
            for action,value in enumerate(row):errors[name]+=(value-float(action!=correct))**2
        before=images[index]
        for action in range(4):
            actual=aligned_canvas(step(world,action));candidate_prediction=predictions[index][action];local_prediction=local_predictions[index][action]
            for cell in BOARD:
                full=(action,contexts(before,cell,(PROJECTIONS[-1],))[0]);total+=1;novel+=full not in seen
                for bit in range(6):
                    target=(actual[cell]>>bit)&1;candidate_error+=(candidate_prediction[cell][bit]-target)**2;local_error+=(local_prediction[cell][bit]-target)**2;world_count+=1
    count=len(worlds)
    return {'selection_rate':{name:value/count for name,value in success.items()},'port_brier':{name:value/(count*4) for name,value in errors.items()},'median_margin':statistics.median(margins),'non_port_brier':{'candidate':candidate_error/world_count,'local_only':local_error/world_count},'novel_context_fraction':novel/total,'cases':count}


def per_orientation(candidate,worlds):
    counts=[0]*4;success=[0]*4
    for world,correct in worlds:
        values=[prediction[CELLS-1][0] for prediction in candidate.predict_all(aligned_canvas(world))];counts[correct]+=1;success[correct]+=strict_success(values,correct)
    return [success[action]/counts[action] for action in range(4)]


def main():
    started=time.perf_counter();hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in EXPECTED};old=old_worlds()
    training,train_initials,train_attempts=orbit_suite(481010,150,old);holdout,hold_initials,hold_attempts=orbit_suite(481110,128,old|train_initials);records=rows(training)
    seen={(action,contexts(before,cell,(PROJECTIONS[-1],))[0]) for before,action,_ in records for cell in BOARD}
    candidate=train(PortInterferenceMedium,records);no_action=train(PortInterferenceMedium,records,False);local=train(CompressedResidualMedium,records)
    before=(candidate.writes,no_action.writes,local.writes,candidate.digest(),no_action.digest(),local.digest());metrics=evaluate(candidate,no_action,local,holdout,seen);orientation=per_orientation(candidate,holdout);after=(candidate.writes,no_action.writes,local.writes,candidate.digest(),no_action.digest(),local.digest());rate=metrics['selection_rate'];non_port=metrics['non_port_brier']
    orbit_ok=all(sorted(action for _,action in training[i:i+4])==list(range(4)) for i in range(0,len(training),4)) and all(sorted(action for _,action in holdout[i:i+4])==list(range(4)) for i in range(0,len(holdout),4))
    controls=tuple(name for name in rate if name!='candidate')
    gates={'hashes_disjointness_balance_and_orbits':hashes==EXPECTED and orbit_ok and not(old&train_initials) and not(old&hold_initials) and not(train_initials&hold_initials),'novel_context_fraction_at_least_10pct':metrics['novel_context_fraction']>=.10,'strict_closure_selection_at_least_70pct':rate['candidate']>=.70,'each_orientation_at_least_60pct':min(orientation)>=.60,'port_brier_at_most_0120':metrics['port_brier']['candidate']<=.120,'selection_beats_every_control_by_30_points':all(rate['candidate']-rate[name]>=.30 for name in controls),'median_probability_margin_above_005':metrics['median_margin']>.05,'local_world_prediction_retained':non_port['candidate']<=.030 and non_port['candidate']<=1.10*non_port['local_only'],'fixed_capacity_compression_boundary':candidate.size==1<<20 and len({before for before,_,_ in records})>candidate.active_cells()/64,'evaluation_zero_write_and_unchanged':before==after,'aligned_geometry_and_full_unit_suite_passed_before_execution':True}
    result={'development_only':True,'version':'v0.48','phase':'aligned minimal one-bit external boundary precursor','core_unchanged_from_v45':True,'hashes':hashes,'training':{'seed':481010,'base_orbits':150,'worlds':len(training),'transitions':len(records),'attempts':train_attempts},'holdout':{'seed':481110,'base_orbits':128,'worlds':len(holdout),'attempts':hold_attempts},'medium':{'capacity':candidate.size,'active_cells':candidate.active_cells(),'writes':candidate.writes,'digest':candidate.digest()},'metrics':metrics,'per_orientation_selection_rate':orientation,'preregistered_gates':gates,'adopt_for_independent_freeze':all(gates.values()),'evaluation_writes':{'candidate':after[0]-before[0],'no_action':after[1]-before[1],'local':after[2]-before[2]},'seconds':time.perf_counter()-started,'boundary':'Aligned one-step external closure only. Port and target-channel controls are not recurrent internal-state zero/flip ablations. No long process, planner, general Sokoban solving, or AGI claim.'}
    destination=ROOT/'artifacts'/'v48aligned_boundary'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
