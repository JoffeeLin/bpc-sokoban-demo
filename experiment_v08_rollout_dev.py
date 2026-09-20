#!/usr/bin/env python3
"""Development-only multi-step cross-task rollout test."""
import json,time
from pathlib import Path

from bpc_cross_task_rollout_v08 import evaluate_rollouts,trained


def main():
    started=time.perf_counter();models,events=trained();writes={name:model.writes for name,model in models.items()}
    result=evaluate_rollouts(models,88_008,2000,(1,2,4,8,16,32))
    output={'development_only':True,'training':events,'holdout_seed':88008,'episodes_per_horizon':2000,
        'conditions':result,'evaluation_writes':{name:model.writes-writes[name] for name,model in models.items()},
        'seconds':time.perf_counter()-started,
        'boundary':'Open-loop prediction under supplied random actions; not planning, goal selection, direct control, or AGI.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v08rollout'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
