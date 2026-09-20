#!/usr/bin/env python3
"""Development-only variable-cardinality sensor and actuator experiment."""
import json,random,time
from pathlib import Path

from bpc_open_interface_v15 import (OpenBoundPolicy,action_stats,collect_open_interface,evaluate_open,
    infer_action_subset,infer_sensor_subset,inverse_subset)
from bpc_three_factor_v12 import generate_suite,train

SENSORS=((None,5,1,3,None,0,4,2),(3,None,5,0,2,None,1,4),(2,4,None,1,5,3,0,None))
ACTUATORS=((2,None,0,3,None,1),(None,1,3,0,2,None),(3,2,None,1,None,0))
MIXES=({'push':200,'collect':50,'open':50},{'push':50,'collect':200,'open':50},{'push':50,'collect':50,'open':200})


def norm(row):
    return {**row,'mapping':list(row['mapping']),'second':list(row['second']),
        **({'candidate_slots':list(row['candidate_slots'])} if 'candidate_slots' in row else {})}


def main():
    started=time.perf_counter();learner,training=train(121010);excluded=set(learner.training_initials)
    reference,triples,initials=collect_open_interface(151010,100,32,exclude=excluded);excluded|=initials
    reference_actions=action_stats(triples,range(6),6,4);interfaces=[]
    for index,(sensor,actuator,mix) in enumerate(zip(SENSORS,ACTUATORS,MIXES)):
        target,triples,initials=collect_open_interface(151110+index,mix,32,sensor,actuator,excluded);excluded|=initials
        channel=infer_sensor_subset(reference,target);target_actions=action_stats(triples,channel['mapping'],len(sensor),len(actuator));action=infer_action_subset(reference_actions,target_actions)
        interfaces.append((sensor,actuator,mix,channel,action,target,target_actions))
    suite,attempts=generate_suite(151510,8,excluded);conditions={};bindings=[];writes=learner.writes;rng=random.Random(151610)
    for index,(sensor,actuator,mix,channel,action,target,target_actions) in enumerate(interfaces):
        channel_oracle=inverse_subset(sensor,6);action_oracle=inverse_subset(actuator,4)
        random_channels=rng.sample(range(len(sensor)),6);random_actions=rng.sample(range(len(actuator)),4)
        policies={'learned':OpenBoundPolicy(learner,channel['mapping'],len(sensor),action['mapping'],len(actuator)),
            'oracle':OpenBoundPolicy(learner,channel_oracle,len(sensor),action_oracle,len(actuator)),
            'sensor_only':OpenBoundPolicy(learner,channel['mapping'],len(sensor),range(4),len(actuator)),
            'action_only':OpenBoundPolicy(learner,range(6),len(sensor),action['mapping'],len(actuator)),
            'identity':OpenBoundPolicy(learner,range(6),len(sensor),range(4),len(actuator)),
            'random':OpenBoundPolicy(learner,random_channels,len(sensor),random_actions,len(actuator))}
        result,traces=evaluate_open(policies,suite,sensor,actuator,151710+index,24,64);conditions[str(index)]=result
        bindings.append({'sensor_routes':list(sensor),'actuator_routes':list(actuator),'target_mix':mix,
            'channel_oracle':list(channel_oracle),'channel_learned':norm(channel),
            'action_oracle':list(action_oracle),'action_learned':norm(action),
            'target_interface_digest':target.digest(),'target_action_digest':target_actions.digest(),
            'random_channels':random_channels,'random_actions':random_actions,'trace_worlds':{name:len(row) for name,row in traces.items()}})
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'classifier_dev':{'model':'jev-1.13.0','chosen_label':'high value next frozen experiment','confidence':.93,
            'role':'candidate routing only; absent from interface inference, policy training, evaluation, and runtime'},
        'retained_failures':['marginal occupancy/change/cochange confused a displaced composite nuisance with a real plane',
            'unfiltered action likelihood confused a permanent zero-effect slot with a frequently blocked real action',
            'action-conditioned local joint statistics still did not identify the composite nuisance under mixture shift; that harder case remains unsupported'],
        'reference':{'worlds':300,'transitions':reference.transitions,'interface_digest':reference.digest(),'action_digest':reference_actions.digest()},
        'bindings':bindings,'suite':{'worlds':len(suite),'families':{f:sum(x[0]==f for x in suite) for f in ('push','collect','open','joint')},
            'attempts':attempts,'initial_overlap_with_all_prior':sum((w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates) in excluded for _,w,_ in suite)},
        'conditions':conditions,'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development synthetic open-interface transfer. Six canonical planes and four canonical actions are embedded in supplied eight-channel/six-slot interfaces with deterministic state-keyed random nuisance planes. Composite causal nuisance rejection failed and is not claimed. Nuisance synthesis, null-slot mechanism, calibration samplers, generators, and terminal events remain supplied. Binders receive no entity, task, direction, success, or reward labels; evaluation uses no search or writes.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v15open'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
