#!/usr/bin/env python3
"""Development-only test of task-name-free BPC factor discovery and routing."""
import json,time
from pathlib import Path

from bpc_autofactor_v10 import evaluate,generate_suite,train


def main():
    started=time.perf_counter();learner,training=train(101010);suite,attempts=generate_suite(101110,12)
    writes=learner.writes;conditions={};trace_counts={}
    for steps in (32,160):
        result,traces=evaluate(learner,suite,101210,64,steps);conditions[str(steps)]=result
        trace_counts[str(steps)]={name:len(row) for name,row in traces.items()}
    output={'development_only':True,'training':training,'discovered_signatures':[list(x) for x in sorted(learner.factors)],
        'required_planes':{str(k):list(v) for k,v in learner.required_planes().items()},'factor_digest':learner.digest(),
        'suite':{'worlds':len(suite),'families':{family:sum(x[0]==family for x in suite) for family in ('push','collect','combined')},
                 'shortest_distances':[distance for _,_,distance in suite],'combined_generation_attempts':attempts},
        'conditions_by_step_budget':conditions,'worlds_with_success_trace':trace_counts,
        'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development synthetic evidence. The co-change factorization and raw-presence routing receive no task name; equal probability multiplication, raw channels, task generators, binary success events, and limits remain supplied.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v10autofactor'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
