#!/usr/bin/env python3
"""Development-only variable-interface transfer to an independent world generator."""
import json,random,time
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import (VariableBoundPolicy,collect_variable,evaluate_variable,
    infer_relational_support_binding,inverse,lab_suite)
from bpc_open_interface_v15 import action_stats,infer_action_subset
from bpc_three_factor_v12 import train

SENSORS=((4,None,0,2,None,5,3,None,1),
    (None,2,4,1,None,3,None,5,0,None),
    (5,None,3,None,0,1,None,None,2,4,None))
ACTIONS=((None,3,1,0,2),(0,None,2,None,1,3,None),(None,1,3,None,2,None,0,None))
KINDS=((0,1,2),(2,0,1,2),(1,2,0,1,2))
MIXES=({'push':126,'collect':27,'open':27},{'push':27,'collect':126,'open':27},
    {'push':27,'collect':27,'open':126},{'push':60,'collect':60,'open':60})


def norm_sensor(row):
    if row.get('mapping') is None:return row
    return {**row,'mapping':list(row['mapping']),'second':list(row['second']),
        'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_action(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'candidate_slots':list(row['candidate_slots'])}


def main():
    started=time.perf_counter();learner,training=train(121010);excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(171010,100,32,exclude=excluded);excluded|=initials
    reference_actions=action_stats(reference_triples,range(6),6,4);bindings=[];interfaces=[]
    for index,(sensors,actions,kinds) in enumerate(zip(SENSORS,ACTIONS,KINDS)):
        targets=[];triples=[];regimes=[]
        for regime,(seed,mix) in enumerate(zip(range(171110+index*10,171114+index*10),MIXES)):
            target,row,initials,support=collect_variable(seed,mix,32,sensors,actions,kinds,excluded);excluded|=initials
            targets.append((target,support,row));triples.extend(row);regimes.append({'digest':target.digest(),'support_size':len(support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets)
        if channel.get('mapping') is None:
            bindings.append({'sensor_routes':list(sensors),'action_routes':list(actions),'kinds':list(kinds),'channel_binding':channel,'regimes':regimes});continue
        target_actions=action_stats(triples,channel['mapping'],len(sensors),len(actions));action=infer_action_subset(reference_actions,target_actions)
        interfaces.append((sensors,actions,kinds,channel,action));bindings.append({'sensor_routes':list(sensors),'action_routes':list(actions),'kinds':list(kinds),
            'channel_oracle':list(inverse(sensors,6)),'channel_binding':norm_sensor(channel),'action_oracle':list(inverse(actions,4)),
            'action_binding':norm_action(action),'regimes':regimes,'target_action_digest':target_actions.digest()})
    suite,attempts=lab_suite(171510,8,excluded);conditions={};writes=learner.writes;rng=random.Random(171610)
    for index,(sensors,actions,kinds,channel,action) in enumerate(interfaces):
        oracle_channels=inverse(sensors,6);oracle_actions=inverse(actions,4);random_channels=rng.sample(range(len(sensors)),6);random_actions=rng.sample(range(len(actions)),4)
        policies={'learned':VariableBoundPolicy(learner,channel['mapping'],len(sensors),action['mapping'],len(actions)),
            'oracle':VariableBoundPolicy(learner,oracle_channels,len(sensors),oracle_actions,len(actions)),
            'sensor_only':VariableBoundPolicy(learner,channel['mapping'],len(sensors),range(4),len(actions)),
            'action_only':VariableBoundPolicy(learner,range(6),len(sensors),action['mapping'],len(actions)),
            'identity':VariableBoundPolicy(learner,range(6),len(sensors),range(4),len(actions)),
            'random':VariableBoundPolicy(learner,random_channels,len(sensors),random_actions,len(actions))}
        result,traces=evaluate_variable(policies,suite,sensors,actions,kinds,171710+index,24,64);conditions[str(index)]=result
        bindings[index]['random_channels']=random_channels;bindings[index]['random_actions']=random_actions
        bindings[index]['trace_worlds']={name:len(row) for name,row in traces.items()}
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'classifier_dev':{'model':'jev-1.13.0','chosen_proposal':'cross-generator transfer','confidence':.73,
            'secondary_proposal':'held-out distractor-family transfer','secondary_confidence':.66,
            'role':'candidate routing only; absent from inference, training, evaluation, and runtime'},
        'reference':{'generator':'original','worlds':300,'transitions':reference.transitions,'interface_digest':reference.digest(),
            'action_digest':reference_actions.digest(),'support':[sorted(x) for x in sorted(reference_support,key=lambda x:(len(x),tuple(x)))]},
        'target':{'generator':'independent rectangular lab implementation','bindings':bindings,
            'suite':{'worlds':len(suite),'attempts':attempts,'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')}}},
        'conditions':conditions,'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'mechanism':'Complete change-support and bidirectional conditional co-presence support filter assignments before multi-regime probabilities. All-zero base-rate events are omitted; no channel or formula names enter inference.',
        'boundary':'Development-only synthetic transfer. Canonical semantics, raw planes, maximum 7x7 canvas, formula family, probability mechanisms, calibration schedules, generators, terminal events, and direct policy are supplied. No neural network, task label, reward, planner, search, classifier runtime, or evaluation write is used.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v17crossgen'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
