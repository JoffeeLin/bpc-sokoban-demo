#!/usr/bin/env python3
"""Development-only comparison of additive anonymous-factor evidence fields."""
import json,time
from pathlib import Path

from bpc_autofactor_v10 import generate_suite,train
from bpc_evidence_field_v11 import EvidenceFieldPolicy,ProductPolicy,SharedPolicy,evaluate


def main():
    started=time.perf_counter();learner,training=train(111010);suite,attempts=generate_suite(111110,12,learner.training_initials)
    policies={'field':EvidenceFieldPolicy(learner),'product':ProductPolicy(learner),'mean':EvidenceFieldPolicy(learner,'mean'),
        'no_prior':EvidenceFieldPolicy(learner,'no_prior'),'shared':SharedPolicy(learner),
        'permuted':EvidenceFieldPolicy(learner,permuted=True),'rotated':EvidenceFieldPolicy(learner,rotated=True)}
    writes=learner.writes;conditions={};traces={}
    for budget in (32,160):
        result,paths=evaluate(policies,suite,111210,64,budget);conditions[str(budget)]=result
        traces[str(budget)]={name:len(row) for name,row in paths.items()}
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'discovered_signatures':[list(x) for x in sorted(learner.factors)],
        'suite':{'worlds':len(suite),'shortest_distances':[distance for _,_,distance in suite],
            'combined_generation_attempts':attempts,'initial_overlap_with_training':sum((w.h,w.w,w.walls,w.agent,w.objects,w.marks) in learner.training_initials for _,w,_ in suite)},
        'conditions_by_step_budget':conditions,'worlds_with_success_trace':traces,'evaluation_writes':learner.writes-writes,
        'seconds':time.perf_counter()-started,
        'boundary':'Development synthetic direct control. One pooled learned prior plus additive factor evidence is supplied as the BPC query rule; raw channels, terminal success, generators, and limits remain supplied.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v11field'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
