#!/usr/bin/env python3
"""Freeze v0.5 inputs, mechanism, controls, and adoption gates."""
from __future__ import annotations

import hashlib,json
from pathlib import Path

from bpc_learned_wave_v04 import learn_raw_physics
from bpc_reversible_wave_v05 import discover_inverses
from v04_maps import generate,text

ROOT=Path(__file__).resolve().parent; PROTOCOL=ROOT/'protocol_v05.json'; HOLDOUT=ROOT/'holdout_v05.json'
FILES=('bpc_learned_wave_v04.py','bpc_reversible_wave_v05.py','v04_maps.py',
       'experiment_v05_frozen.py','freeze_v05.py')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if PROTOCOL.exists():raise SystemExit('v0.5 already frozen; refusing to overwrite')
    config={'training_seed':40_404,'training_episodes':3000,'training_steps':80,
        'inverse_seed':50_505,'inverse_episodes':600,'inverse_steps':60,
        'reach_seed':56_505,'reach_episodes':200,'reach_steps':20,
        'holdout_count':8,'holdout_seed':55_005,'state_limit':5_000_000}
    model,_,_,manifest=learn_raw_physics(config['training_seed'],config['training_episodes'],config['training_steps'])
    inverse,evidence=discover_inverses(config['inverse_seed'],config['inverse_episodes'],config['inverse_steps'])
    generated=generate(config['holdout_count'],config['holdout_seed'])
    maps=[{'id':f'V5H{i+1}','boxes':level.boxes.bit_count(),'shortest_actions':distance,
           'reference_states':states,'map':text(level)} for i,(level,distance,states) in enumerate(generated)]
    old={x['map'] for x in json.loads((ROOT/'holdout_v04.json').read_text())}
    assert not old.intersection(x['map'] for x in maps),'v0.5 holdout overlaps v0.4 development maps'
    HOLDOUT.write_text(json.dumps(maps,indent=2)+'\n')
    protocol={'format':'bpc-reversible-wave-v05-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can action inverses discovered only from exact round-trip experience replace supplied free-space reachability inside the learned-world wave on new Sokoban layouts?',
        'config':config,'expected_model_sha256':model.digest(),'expected_training_manifest':manifest,
        'expected_inverse':inverse,'expected_inverse_evidence':evidence,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'inverse_min_support':5000,'reach_exact_rate':1.0,
            'wrong_inverse_max_reach_exact_rate':0.05,'solve_margin':0.75},
        'controls':['wrong inverse pairs use the identical learned world and identical experience',
            'the old supplied flood fill is disabled before holdout solving'],
        'source_sha256':{name:sha(ROOT/name) for name in FILES},
        'failure_policy':'Retain every miss; do not replace maps, alter seeds, change code, or lower gates after execution.',
        'boundary':'Developer-frozen mechanism evidence. Raw local channels, action displacement, macro push candidate enumeration, terminal seeding, and backward wave remain supplied.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n')
    print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
