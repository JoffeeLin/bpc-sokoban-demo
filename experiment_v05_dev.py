#!/usr/bin/env python3
"""Development-only test of learned reversible future-effect equivalence."""
from __future__ import annotations

import json,time
from pathlib import Path

from bpc_learned_wave_v04 import learn_raw_physics,parse,replay
from bpc_reversible_wave_v05 import audit_reach,discover_inverses,solve

ROOT=Path(__file__).resolve().parent


def main():
    full,_,experience,manifest=learn_raw_physics(40_404,3000,80)
    inverse,counts=discover_inverses(50_505,600,60); wrong=(2,3,0,1)
    maps=json.loads((ROOT/'holdout_v04.json').read_text()); started=time.perf_counter()
    reach={'learned':audit_reach(full,inverse,55_505,120,20),
           'wrong_inverse':audit_reach(full,wrong,55_505,120,20)}
    conditions={}
    for name,pairing in (('learned_inverse',inverse),('wrong_inverse',wrong)):
        outcomes={}
        for item in maps:
            level=parse(item['map']);outcome=solve(level,full,pairing)
            outcome['replay_solved']=outcome['solved'] and replay(level,outcome['sequence'])[0]
            outcomes[item['id']]=outcome
        conditions[name]=outcomes
    result={'development_only':True,'question':'Can exact learned round trips replace supplied free-space flood fill?',
        'training_experience':experience,'training_manifest':manifest,'inverse':inverse,
        'inverse_evidence':counts,'reach_audit':reach,'conditions':conditions,
        'solved':{name:sum(x['solved'] for x in outcomes.values()) for name,outcomes in conditions.items()},
        'replayed':{name:sum(x['replay_solved'] for x in outcomes.values()) for name,outcomes in conditions.items()},
        'model_writes':full.writes,'seconds':time.perf_counter()-started,
        'boundary':'Development reuse of v0.4 holdouts. Local token channels, macro push-candidate geometry, terminal seeding, and backward wave remain supplied.'}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
