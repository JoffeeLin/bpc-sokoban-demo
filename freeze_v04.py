#!/usr/bin/env python3
"""Freeze v0.4 inputs, implementation, gates, and expected training digest."""
from __future__ import annotations

import hashlib,json
from pathlib import Path

from bpc_learned_wave_v04 import learn_raw_physics
from v04_maps import generate,text

ROOT=Path(__file__).resolve().parent; PROTOCOL=ROOT/'protocol_v04.json'; HOLDOUT=ROOT/'holdout_v04.json'
FILES=('bpc_learned_wave_v04.py','v04_maps.py','experiment_v04_frozen.py','freeze_v04.py')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if PROTOCOL.exists():raise SystemExit('v0.4 already frozen; refusing to overwrite')
    config={'training_seed':40_404,'training_episodes':3000,'training_steps':80,
        'validation_seed':90_901,'validation_episodes':500,'validation_steps':80,
        'holdout_count':12,'holdout_seed':44_004,'state_limit':5_000_000}
    full,_,_,manifest=learn_raw_physics(config['training_seed'],config['training_episodes'],config['training_steps'])
    generated=generate(config['holdout_count'],config['holdout_seed'])
    maps=[{'id':f'H{i+1}','boxes':level.boxes.bit_count(),'shortest_actions':distance,
           'reference_states':states,'map':text(level)} for i,(level,distance,states) in enumerate(generated)]
    HOLDOUT.write_text(json.dumps(maps,indent=2)+'\n')
    protocol={'format':'bpc-learned-world-v04-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a local transition probability cube learned only from random raw interactions replace supplied Sokoban push physics inside the fixed v0.3 wave shell on unseen layouts and an unseen box count?',
        'config':config,'expected_model_sha256':full.digest(),'expected_training_manifest':manifest,
        'holdout_sha256':sha(HOLDOUT),'archive_v03_sha256':'107145ee2cc50468cf35749a5082aa76475090f7c22461ad7955ab745e60a898',
        'adoption_thresholds':{'no_far_max_push_accuracy':.25,'solve_margin':.75},
        'controls':['no_far removes the third action-relative cell with identical experience'],
        'source_sha256':{name:sha(ROOT/name) for name in FILES},
        'failure_policy':'Retain every miss; do not replace maps, alter seeds, change code, or lower gates after execution.',
        'boundary':'Developer-frozen local evidence. The v0.3 reachability compression and recursive wave shell remain supplied.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n')
    print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
