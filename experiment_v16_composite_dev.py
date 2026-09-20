#!/usr/bin/env python3
"""Development-only multi-regime composite-distractor binding experiment."""
import json,random,time
from pathlib import Path

from bpc_composite_binding_v16 import (CompositeBoundPolicy,collect_composite_interface,
    evaluate_composite,infer_support_binding)
from bpc_open_interface_v15 import action_stats,infer_action_subset,inverse_subset
from bpc_three_factor_v12 import generate_suite,train

SENSORS=((4,None,0,2,5,None,3,1),(None,2,4,1,3,5,None,0),(5,3,None,0,1,None,2,4))
ACTUATORS=((None,3,1,0,None,2),(0,None,2,None,1,3),(1,3,None,2,0,None))
MIXES=({'push':210,'collect':45,'open':45},{'push':45,'collect':210,'open':45},
       {'push':45,'collect':45,'open':210},{'push':100,'collect':100,'open':100})


def norm_sensor(row):
    return {**row,'mapping':list(row['mapping']),'second':list(row['second']),
        'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_action(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'candidate_slots':list(row['candidate_slots'])}


def main():
    started=time.perf_counter();learner,training=train(121010);excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(161010,100,32,exclude=excluded);excluded|=initials
    reference_actions=action_stats(reference_triples,range(6),6,4);interfaces=[]
    for index,(sensors,actuators) in enumerate(zip(SENSORS,ACTUATORS)):
        targets=[];triples=[];regime_digests=[]
        for regime,mix in enumerate(MIXES):
            target,row,initials,support=collect_composite_interface(161110+index*10+regime,mix,32,sensors,actuators,excluded)
            excluded|=initials;targets.append((target,support));triples.extend(row);regime_digests.append({'interface_digest':target.digest(),'support':[sorted(x) for x in sorted(support,key=lambda x:(len(x),tuple(x)))]})
        channel=infer_support_binding(reference,reference_support,targets)
        target_actions=action_stats(triples,channel['mapping'],len(sensors),len(actuators));action=infer_action_subset(reference_actions,target_actions)
        interfaces.append((sensors,actuators,channel,action,target_actions,regime_digests))
    suite,attempts=generate_suite(161510,8,excluded);conditions={};bindings=[];writes=learner.writes;rng=random.Random(161610)
    for index,(sensors,actuators,channel,action,target_actions,regime_digests) in enumerate(interfaces):
        channel_oracle=inverse_subset(sensors,6);action_oracle=inverse_subset(actuators,4)
        random_channels=rng.sample(range(len(sensors)),6);random_actions=rng.sample(range(len(actuators)),4)
        policies={'learned':CompositeBoundPolicy(learner,channel['mapping'],len(sensors),action['mapping'],len(actuators)),
            'oracle':CompositeBoundPolicy(learner,channel_oracle,len(sensors),action_oracle,len(actuators)),
            'sensor_only':CompositeBoundPolicy(learner,channel['mapping'],len(sensors),range(4),len(actuators)),
            'action_only':CompositeBoundPolicy(learner,range(6),len(sensors),action['mapping'],len(actuators)),
            'identity':CompositeBoundPolicy(learner,range(6),len(sensors),range(4),len(actuators)),
            'random':CompositeBoundPolicy(learner,random_channels,len(sensors),random_actions,len(actuators))}
        result,traces=evaluate_composite(policies,suite,sensors,actuators,161710+index,24,64);conditions[str(index)]=result
        bindings.append({'sensor_routes':list(sensors),'actuator_routes':list(actuators),
            'channel_oracle':list(channel_oracle),'channel_learned':norm_sensor(channel),
            'action_oracle':list(action_oracle),'action_learned':norm_action(action),'regimes':regime_digests,
            'target_action_digest':target_actions.digest(),'random_channels':random_channels,'random_actions':random_actions,
            'trace_worlds':{name:len(row) for name,row in traces.items()}})
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'classifier_dev':{'model':'jev-1.13.0','chosen_label':'strongest next development mechanism','confidence':.78,
            'role':'candidate routing only; absent from support inference, policy training, evaluation, and runtime'},
        'reference':{'worlds':300,'transitions':reference.transitions,'interface_digest':reference.digest(),
            'action_digest':reference_actions.digest(),'support':[sorted(x) for x in sorted(reference_support,key=lambda x:(len(x),tuple(x)))]},
        'bindings':bindings,'suite':{'worlds':len(suite),'families':{f:sum(x[0]==f for x in suite) for f in ('push','collect','open','joint')},
            'attempts':attempts,'initial_overlap_with_all_prior':sum((w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates) in excluded for _,w,_ in suite)},
        'conditions':conditions,'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development synthetic composite-interface transfer. Four separately sampled unlabeled calibration regimes, canonical/observed cardinalities, displaced-XOR nuisance synthesis, null action slots, samplers, generators, and terminal events are supplied. The binder receives no regime, task, entity, direction, success, or reward names; evaluation uses no search or writes.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v16composite'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
