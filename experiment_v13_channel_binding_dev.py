#!/usr/bin/env python3
"""Development-only unseen sensor-permutation binding experiment."""
import json,random,time
from pathlib import Path

from bpc_channel_binding_v13 import BoundFieldPolicy,collect_interface,evaluate_permuted,infer_binding,inverse
from bpc_three_factor_v12 import generate_suite,train

PERMUTATIONS=((4,0,5,2,1,3),(2,5,1,4,3,0),(3,2,4,1,5,0))
TARGET_MIXES=({'push':200,'collect':50,'open':50},{'push':50,'collect':200,'open':50},{'push':50,'collect':50,'open':200})


def main():
    started=time.perf_counter();learner,training=train(121010)
    reference,reference_initials=collect_interface(131010,100,32,exclude=learner.training_initials)
    targets=[];excluded=set(learner.training_initials)|reference_initials
    for index,(permutation,mix) in enumerate(zip(PERMUTATIONS,TARGET_MIXES)):
        target,initials=collect_interface(131110+index,mix,32,permutation,excluded)
        excluded|=initials;targets.append((permutation,mix,target,
            {mode:infer_binding(reference,target,mode) for mode in ('transition','full','static','count')}))
    suite,attempts=generate_suite(131510,8,excluded);conditions={};bindings=[];writes=learner.writes
    rng=random.Random(131610)
    for index,(permutation,mix,target,bindings_by_mode) in enumerate(targets):
        oracle=inverse(permutation);random_mapping=list(range(6));rng.shuffle(random_mapping)
        policies={'learned':BoundFieldPolicy(learner,bindings_by_mode['transition']['mapping']),'oracle':BoundFieldPolicy(learner,oracle),
            'identity':BoundFieldPolicy(learner,range(6)),'static':BoundFieldPolicy(learner,bindings_by_mode['static']['mapping']),
            'count':BoundFieldPolicy(learner,bindings_by_mode['count']['mapping']),'random':BoundFieldPolicy(learner,random_mapping)}
        result,traces=evaluate_permuted(policies,suite,permutation,131710+index,48,64)
        conditions[str(index)]=result
        bindings.append({'observed_to_canonical':list(permutation),'target_mix':mix,'oracle_canonical_to_observed':list(oracle),
            'by_mode':{mode:{**row,'mapping':list(row['mapping']),'second':list(row['second'])} for mode,row in bindings_by_mode.items()},
            'random_mapping':random_mapping,'trace_worlds':{name:len(row) for name,row in traces.items()}})
    output={'development_only':True,'training':training,'factor_digest':learner.digest(),
        'reference_calibration':{'worlds':300,'transitions':reference.transitions,'initial_overlap_with_training':len(reference_initials&learner.training_initials)},
        'target_calibration':{'interfaces':3,'worlds_each':300,'transitions_each':targets[0][2].transitions,'mixtures':TARGET_MIXES},
        'bindings':bindings,'suite':{'worlds':len(suite),'families':{f:sum(x[0]==f for x in suite) for f in ('push','collect','open','joint')},
            'attempts':attempts,'initial_overlap_with_all_prior':sum(tuple((w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates)) in excluded for _,w,_ in suite)},
        'conditions':conditions,'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development synthetic evidence. Reference and target calibration use unlabeled random transitions from disjoint worlds but a supplied balanced generator mixture. The BPC policy gets no task name and performs no runtime planner/search.'}
    destination=Path(__file__).resolve().parent/'artifacts'/'v13binding'/'development.json'
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))


if __name__=='__main__':main()
