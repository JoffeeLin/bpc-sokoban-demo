#!/usr/bin/env python3
"""Development-only simultaneous sensor and actuator permutation experiment."""
import json,random,time
from pathlib import Path

from bpc_channel_binding_v13 import infer_binding,inverse
from bpc_joint_binding_v14 import JointBoundPolicy,action_stats,collect_joint_interface,evaluate_joint,infer_action_binding,inverse_action
from bpc_three_factor_v12 import generate_suite,train

SENSORS=((5,3,0,4,1,2),(2,0,5,1,3,4),(4,2,1,5,0,3))
ACTUATORS=((2,0,3,1),(1,3,0,2),(3,2,1,0))
MIXES=({'push':200,'collect':50,'open':50},{'push':50,'collect':200,'open':50},{'push':50,'collect':50,'open':200})


def main():
    started=time.perf_counter();learner,training=train(121010);excluded=set(learner.training_initials)
    reference,reference_triples,initials=collect_joint_interface(141010,100,32,exclude=excluded);excluded|=initials
    reference_actions=action_stats(reference_triples,range(6));interfaces=[]
    for index,(sensor,actuator,mix) in enumerate(zip(SENSORS,ACTUATORS,MIXES)):
        target,triples,initials=collect_joint_interface(141110+index,mix,32,sensor,actuator,excluded);excluded|=initials
        channel=infer_binding(reference,target,'transition');target_actions=action_stats(triples,channel['mapping']);action=infer_action_binding(reference_actions,target_actions)
        interfaces.append((sensor,actuator,mix,channel,action,target,target_actions))
    suite,attempts=generate_suite(141510,8,excluded);conditions={};bindings=[];writes=learner.writes;rng=random.Random(141610)
    for index,(sensor,actuator,mix,channel,action,target,target_actions) in enumerate(interfaces):
        channel_oracle=inverse(sensor);action_oracle=inverse_action(actuator);random_channels=list(range(6));rng.shuffle(random_channels);random_actions=list(range(4));rng.shuffle(random_actions)
        policies={'learned':JointBoundPolicy(learner,channel['mapping'],action['mapping']),
            'oracle':JointBoundPolicy(learner,channel_oracle,action_oracle),
            'sensor_only':JointBoundPolicy(learner,channel['mapping'],range(4)),
            'action_only':JointBoundPolicy(learner,range(6),action['mapping']),
            'identity':JointBoundPolicy(learner,range(6),range(4)),
            'random':JointBoundPolicy(learner,random_channels,random_actions)}
        result,traces=evaluate_joint(policies,suite,sensor,actuator,141710+index,48,64);conditions[str(index)]=result
        bindings.append({'sensor_observed_to_canonical':list(sensor),'actuator_observed_to_canonical':list(actuator),'target_mix':mix,
            'channel_oracle':list(channel_oracle),'channel_learned':{**channel,'mapping':list(channel['mapping']),'second':list(channel['second'])},
            'action_oracle':list(action_oracle),'action_learned':{**action,'mapping':list(action['mapping']),'second':list(action['second'])},
            'target_interface_digest':target.digest(),'target_action_digest':target_actions.digest(),
            'random_channels':random_channels,'random_actions':random_actions,'trace_worlds':{name:len(row) for name,row in traces.items()}})
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'reference':{'worlds':300,'transitions':reference.transitions,'interface_digest':reference.digest(),'action_digest':reference_actions.digest()},
        'bindings':bindings,'suite':{'worlds':len(suite),'families':{f:sum(x[0]==f for x in suite) for f in ('push','collect','open','joint')},
            'attempts':attempts,'initial_overlap_with_all_prior':sum(tuple((w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates)) in excluded for _,w,_ in suite)},
        'conditions':conditions,'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development synthetic interface transfer. Calibration worlds, family mixture, action budget, six sensor planes, and four actuator slots are supplied. Binders receive no entity, task, direction, or success labels; direct evaluation uses no search or writes.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v14joint'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
