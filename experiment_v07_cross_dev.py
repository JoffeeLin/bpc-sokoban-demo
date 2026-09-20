#!/usr/bin/env python3
"""Development test: separately learned task functions on unseen combinations."""
import json,time
from pathlib import Path

from bpc_cross_task_v07 import evaluate,train


def main():
    started=time.perf_counter();compressed,residual,fragments,full,events=train(70_707,2500,60)
    writes=fragments.writes
    result=evaluate({'condition_deleted':compressed,'residual_prime':residual,'fragment_chain':fragments,'full_context':full},77_007,1000,60)
    assert compressed.writes==writes
    output={'development_only':True,
        'question':'Can condition-deleted anonymous bit functions compose push-only and collect-only experience in a never-trained combined world?',
        'training':events,'distinct_training_inputs':len(compressed.samples),
        'context_widths':[len(x) for x in compressed.contexts],
        'model_digests':{'condition_deleted':compressed.digest(),'residual_prime':residual.digest(),'fragment_chain':fragments.digest()},
        'residual_clause_counts':[len(x) for x in residual.clauses],
        'fragment_prerequisites':fragments.prerequisites,
        'evaluation':result,'evaluation_writes':fragments.writes-writes,
        'seconds':time.perf_counter()-started,
        'boundary':'One-step local world-function transfer only. Raw bit channels, action-relative three-cell addressing, task generators, and evaluator remain supplied; no planning or AGI claim.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v07cross'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
