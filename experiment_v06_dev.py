#!/usr/bin/env python3
"""Development-only check of learned macro push geometry."""
from __future__ import annotations

import json,time
from pathlib import Path

from bpc_learned_geometry_v06 import audit_templates,learn_push_templates,solve
from bpc_learned_wave_v04 import learn_raw_physics,parse,replay
from bpc_reversible_wave_v05 import discover_inverses

ROOT=Path(__file__).resolve().parent


def main():
    model,_,experience,manifest=learn_raw_physics(40_404,3000,80)
    inverse,inverse_evidence=discover_inverses(50_505,600,60)
    templates,template_evidence,pushes=learn_push_templates(60_606,3000,80)
    wrong=tuple(templates[(a+1)%4] for a in range(4));maps=json.loads((ROOT/'holdout_v05.json').read_text())
    started=time.perf_counter();conditions={}
    for name,candidate in (('learned_geometry',templates),('rotated_geometry',wrong)):
        outcomes={}
        for item in maps:
            level=parse(item['map']);outcome=solve(level,model,inverse,candidate)
            outcome['replay_solved']=outcome['solved'] and replay(level,outcome['sequence'])[0]
            outcomes[item['id']]=outcome
        conditions[name]=outcomes
    result={'development_only':True,'question':'Can raw transition deltas replace supplied macro push geometry?',
        'training_experience':experience,'training_manifest':manifest,'inverse':inverse,
        'inverse_evidence':inverse_evidence,'templates':templates,'template_evidence':template_evidence,
        'template_training_pushes':pushes,
        'template_audit':{'learned':audit_templates(templates,66_006,500,80),
                          'rotated':audit_templates(wrong,66_006,500,80)},
        'conditions':conditions,
        'solved':{name:sum(x['solved'] for x in rows.values()) for name,rows in conditions.items()},
        'replayed':{name:sum(x['replay_solved'] for x in rows.values()) for name,rows in conditions.items()},
        'model_writes':model.writes,'seconds':time.perf_counter()-started,
        'boundary':'Development reuse of v0.5 holdouts. Local action-relative addressing, terminal seeding, equivalence-class choice, and backward wave remain supplied.'}
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
