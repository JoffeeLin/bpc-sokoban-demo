#!/usr/bin/env python3
"""Development-only three-mechanism direct composition experiment."""
import json,time
from pathlib import Path

from bpc_three_factor_v12 import FieldPolicy,ProductPolicy,SharedPolicy,UniformPolicy,evaluate,generate_suite,train


def main():
    started=time.perf_counter();learner,training=train(121010);suite,attempts=generate_suite(121110,8,learner.training_initials)
    policies={'field':FieldPolicy(learner),'product':ProductPolicy(learner),'shared':SharedPolicy(learner),
        'drop_0':FieldPolicy(learner,drop=(0,)),'drop_1':FieldPolicy(learner,drop=(1,)),
        'drop_2':FieldPolicy(learner,drop=(2,)),'rotated':FieldPolicy(learner,rotated=True),
        'uniform':UniformPolicy()}
    writes=learner.writes;conditions={};trace_counts={}
    for budget in (64,256):
        result,traces=evaluate(policies,suite,121210,64,budget);conditions[str(budget)]=result
        trace_counts[str(budget)]={name:len(row) for name,row in traces.items()}
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'discovered_signatures':[list(x) for x in sorted(learner.factors)],
        'required_planes':{str(k):list(v) for k,v in learner.required_planes().items()},
        'suite':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','open','joint')},
            'shortest_distances':[distance for _,_,distance in suite],'attempts':attempts,
            'initial_overlap_with_training':sum(tuple((w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates)) in learner.training_initials for _,w,_ in suite)},
        'conditions_by_step_budget':conditions,'worlds_with_success_trace':trace_counts,
        'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development synthetic evidence. Three task generators and binary terminal events are supplied. The BPC learner gets no family name; its runtime is one additive evidence query with no planner/search.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v12three'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
