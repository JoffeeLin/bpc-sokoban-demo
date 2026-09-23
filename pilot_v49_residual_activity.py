#!/usr/bin/env python3
"""Development-only pilot; seeds here are permanently excluded from v0.49."""
import json,random

from bpc_port_interference_v45 import PortInterferenceMedium
from bpc_residual_activity_v49 import ResidualActivityMedium
from carry_probe_v49 import suite


def train(seed=490001,episodes=800):
    worlds,identities,_=suite(seed,episodes,(3,4,5,6));rng=random.Random(seed+1);candidate=ResidualActivityMedium(power=18);local=PortInterferenceMedium(power=18)
    for initial in worlds:
        state=initial;candidate.begin()
        for _ in range(28):
            action=rng.randrange(4);before=state.image();state=state.step(action);after=state.image();candidate.advance(before,action,after,True);local.observe(before,action,after)
            if state.closed:break
    return candidate,local,identities
def evaluate(model,worlds,mode='normal',memoryless=False):
    successes=steps=0;per=[0]*4;counts=[0]*4
    for initial in worlds:
        state=initial;model.begin(mode,memoryless);counts[state.cue]+=1
        for _ in range(initial.length+5):
            values=[model.probability(state.image(),a,63,0) for a in range(4)];action=min(range(4),key=values.__getitem__);before=state.image();state=state.step(action);model.advance(before,action,state.image());steps+=1
            if state.closed:break
        successes+=state.closed;per[initial.cue]+=state.closed
    return {'success_rate':successes/len(worlds),'per_cue':[per[i]/counts[i] for i in range(4)],'mean_steps':steps/len(worlds)}
def main():
    candidate,_,old=train();worlds,_,attempts=suite(490101,160,(7,8,9,10),old);result={'pilot_only':True,'attempts':attempts,'conditions':{name:evaluate(candidate,worlds,*args) for name,args in {'candidate':(), 'zero':('zero',), 'flip':('flip',), 'shift':('shift',), 'memoryless':('normal',True)}.items()}};print(json.dumps(result,indent=2))
if __name__=='__main__':main()
