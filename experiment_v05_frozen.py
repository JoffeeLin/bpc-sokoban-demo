#!/usr/bin/env python3
"""Execute the pre-registered v0.5 reversible-equivalence holdout."""
from __future__ import annotations

import hashlib,json,time
from pathlib import Path

import bpc_learned_wave_v04 as supplied
from bpc_learned_wave_v04 import learn_raw_physics,parse,replay
from bpc_reversible_wave_v05 import audit_reach,discover_inverses,solve

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'artifacts'/'v05'
PROTOCOL=ROOT/'protocol_v05.json'; HOLDOUT=ROOT/'holdout_v05.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(model,inverse,maps,limit):
    writes=model.writes; output={}
    for item in maps:
        level=parse(item['map']); started=time.perf_counter(); result=solve(level,model,inverse,limit)
        result['seconds']=time.perf_counter()-started
        result['replay_solved']=result['solved'] and replay(level,result['sequence'])[0]
        output[item['id']]=result
    assert model.writes==writes
    return output


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():
        assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    maps=json.loads(HOLDOUT.read_text()); assert sha(HOLDOUT)==protocol['holdout_sha256']
    config=protocol['config']; threshold=protocol['adoption_thresholds']; started=time.perf_counter()
    model,_,experience,manifest=learn_raw_physics(
        config['training_seed'],config['training_episodes'],config['training_steps'])
    assert model.digest()==protocol['expected_model_sha256']
    assert manifest==protocol['expected_training_manifest']
    inverse,evidence=discover_inverses(config['inverse_seed'],config['inverse_episodes'],config['inverse_steps'])
    assert list(inverse)==protocol['expected_inverse'] and evidence==protocol['expected_inverse_evidence']
    wrong=(2,3,0,1)
    reach={'learned':audit_reach(model,inverse,config['reach_seed'],config['reach_episodes'],config['reach_steps']),
           'wrong_inverse':audit_reach(model,wrong,config['reach_seed'],config['reach_episodes'],config['reach_steps'])}
    old_reach=supplied.reach
    def disabled(*_args,**_kwargs):raise AssertionError('supplied reach() was called during v0.5 holdout')
    supplied.reach=disabled
    try:
        writes=model.writes
        conditions={'primary':evaluate(model,inverse,maps,config['state_limit']),
                    'wrong_inverse':evaluate(model,wrong,maps,config['state_limit'])}
        old_reach_disabled=True
    finally:supplied.reach=old_reach
    assert model.writes==writes
    primary=conditions['primary']; ablation=conditions['wrong_inverse']; states=reach['learned']['states']
    unique=all(evidence[a][inverse[a]]>=threshold['inverse_min_support'] and
               all(value==0 for b,value in enumerate(evidence[a]) if b!=inverse[a]) for a in range(4))
    gate={'inverse_uniquely_discovered':unique,
        'learned_reach_exact':reach['learned']['exact']/states>=threshold['reach_exact_rate'] and reach['learned']['symmetric_difference_cells']==0,
        'wrong_inverse_reach_at_most_5pct':reach['wrong_inverse']['exact']/states<=threshold['wrong_inverse_max_reach_exact_rate'],
        'all_new_holdouts_solved':all(x['solved'] for x in primary.values()),
        'all_solutions_replay':all(x['replay_solved'] for x in primary.values()),
        'all_unseen_four_box_maps_solved':all(primary[x['id']]['solved'] for x in maps if x['boxes']==4),
        'beats_wrong_inverse_by_75pp':(sum(x['solved'] for x in primary.values())-sum(x['solved'] for x in ablation.values()))/len(maps)>=threshold['solve_margin'],
        'supplied_reach_disabled':old_reach_disabled,'frozen_model_writes_zero':model.writes-writes==0}
    result={'format':'bpc-reversible-wave-v05','evidence_level':'developer-frozen local holdout; not third-party blind',
        'training_experience':experience,'training_manifest':manifest,'model_sha256':model.digest(),
        'inverse':inverse,'inverse_evidence':evidence,'reach_audit':reach,
        'holdout':{'maps':len(maps),'boxes':[x['boxes'] for x in maps],
            'shortest_action_distances':[x['shortest_actions'] for x in maps]},
        'conditions':conditions,'gate':gate,'adopted':all(gate.values()),
        'frozen_model_writes':model.writes-writes,'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'source_sha256':protocol['source_sha256'],
        'supported_claim':'Exact action inverses discovered from round-trip experience form free-space equivalence classes that transfer to new Sokoban layouts inside the fixed learned-world wave.',
        'boundary':'Not direct control or AGI. Raw local channels, action displacement, macro push candidate enumeration, terminal seeding, and backward propagation remain supplied.'}
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
