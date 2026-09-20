#!/usr/bin/env python3
"""Development-only direct policy composition test."""
import json,pickle,time
from pathlib import Path

from bpc_direct_composition_v09 import evaluate,generate_holdout,train


def main():
    started=time.perf_counter();shared,specialists,training=train(90_909)
    holdout,attempts=generate_holdout(99_009,12);writes={name:model.writes for name,model in {'shared':shared,**specialists}.items()}
    models={'shared':shared,'push_only':specialists['push'],'collect_only':specialists['collect'],'rotated':shared,'uniform':shared}
    conditions={};trace_counts={}
    for steps in (32,160):
        result,traces=evaluate(models,holdout,99_109,64,steps);conditions[str(steps)]=result
        trace_counts[str(steps)]={name:len(row) for name,row in traces.items()}
    output={'development_only':True,'training':training,'holdout':{'worlds':len(holdout),'generation_attempts':attempts,
        'shortest_distances':[distance for _,distance in holdout],'fixed_box_solutions':[None for _ in holdout]},
        'conditions_by_step_budget':conditions,'worlds_with_success_trace':trace_counts,
        'evaluation_writes':{name:model.writes-writes[name] for name,model in {'shared':shared,**specialists}.items()},
        'seconds':time.perf_counter()-started,
        'boundary':'Development direct policy on supplied push-required collect tasks; no runtime planner/search, but task generators and binary success events are supplied.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v09direct'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n')
    with (destination.parent/'development_models.pkl').open('wb') as file:pickle.dump((shared,specialists,holdout),file,protocol=5)
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
