#!/usr/bin/env python3
"""Three independent development seeds for the v0.11 evidence-field route."""
import json,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from bpc_autofactor_v10 import generate_suite,train
from bpc_evidence_field_v11 import EvidenceFieldPolicy,ProductPolicy,SharedPolicy,evaluate


def run(seed):
    learner,training=train(seed);suite,attempts=generate_suite(seed+100,12,learner.training_initials)
    policies={'field':EvidenceFieldPolicy(learner),'product':ProductPolicy(learner),
        'no_prior':EvidenceFieldPolicy(learner,'no_prior'),'shared':SharedPolicy(learner),
        'rotated':EvidenceFieldPolicy(learner,rotated=True)}
    result,_=evaluate(policies,suite,seed+200,64,32)
    return {'seed':seed,'training':training,'attempts':attempts,'result':result,
        'field_minus_product':result['field']['successes']-result['product']['successes'],
        'field_minus_shared':result['field']['successes']-result['shared']['successes']}


def main():
    started=time.perf_counter();seeds=(111011,111012,111013)
    with ProcessPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,seeds))
    output={'development_only':True,'rows':rows,
        'aggregate':{'field_minus_product':sum(x['field_minus_product'] for x in rows),
            'field_wins_product':sum(x['field_minus_product']>0 for x in rows),
            'field_ties_product':sum(x['field_minus_product']==0 for x in rows),
            'field_minus_shared':sum(x['field_minus_shared'] for x in rows)},
        'seconds':time.perf_counter()-started,
        'boundary':'Development seed sweep only; no frozen claim. Candidate selection must not use target frozen outcomes.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v11field'/'sweep.json'
    destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
