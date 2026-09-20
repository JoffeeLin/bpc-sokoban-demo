#!/usr/bin/env python3
"""Freeze v0.6 inputs, learned geometry, causal control, and gates."""
from __future__ import annotations

import hashlib,json
from pathlib import Path

from bpc_learned_geometry_v06 import learn_push_templates
from bpc_learned_wave_v04 import learn_raw_physics
from bpc_reversible_wave_v05 import discover_inverses
from v04_maps import generate,text

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v06.json';HOLDOUT=ROOT/'holdout_v06.json'
FILES=('bpc_learned_wave_v04.py','bpc_reversible_wave_v05.py','bpc_learned_geometry_v06.py',
       'v04_maps.py','experiment_v06_frozen.py','freeze_v06.py')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if PROTOCOL.exists():raise SystemExit('v0.6 already frozen; refusing to overwrite')
    config={'world_seed':40_404,'world_episodes':3000,'world_steps':80,
        'inverse_seed':50_505,'inverse_episodes':600,'inverse_steps':60,
        'template_seed':60_606,'template_episodes':3000,'template_steps':80,
        'audit_seed':66_006,'audit_episodes':1000,'audit_steps':80,
        'holdout_count':8,'holdout_seed':66_006,'state_limit':5_000_000}
    model,_,_,manifest=learn_raw_physics(config['world_seed'],config['world_episodes'],config['world_steps'])
    inverse,inverse_evidence=discover_inverses(config['inverse_seed'],config['inverse_episodes'],config['inverse_steps'])
    templates,template_evidence,pushes=learn_push_templates(
        config['template_seed'],config['template_episodes'],config['template_steps'])
    generated=generate(config['holdout_count'],config['holdout_seed'])
    maps=[{'id':f'V6H{i+1}','boxes':level.boxes.bit_count(),'shortest_actions':distance,
           'reference_states':states,'map':text(level)} for i,(level,distance,states) in enumerate(generated)]
    prior=set()
    for name in ('holdout_v04.json','holdout_v05.json'):
        prior.update(x['map'] for x in json.loads((ROOT/name).read_text()))
    assert not prior.intersection(x['map'] for x in maps),'v0.6 holdout overlaps a development set'
    HOLDOUT.write_text(json.dumps(maps,indent=2)+'\n')
    protocol={'format':'bpc-learned-geometry-v06-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can anonymous local delta templates learned only from random interaction replace supplied macro box-behind and player-behind geometry on new layouts?',
        'config':config,'expected_model_sha256':model.digest(),'expected_training_manifest':manifest,
        'expected_inverse':inverse,'expected_inverse_evidence':inverse_evidence,
        'expected_templates':templates,'expected_template_evidence':template_evidence,
        'expected_template_training_pushes':pushes,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'template_min_support':900,'template_audit_rate':1.0,
            'rotated_template_max_audit_rate':0.0,'solve_margin':0.75},
        'controls':['rotate the learned templates across action identities with identical experience and world model',
            'source scan forbids hard-coded action vectors, action xor inverse, and moved() in the v0.6 macro solver'],
        'classifier_dev':{'model':'jev-1.13.0','role':'development candidate routing only; absent from training evaluation and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in FILES},
        'failure_policy':'Retain every miss; do not replace maps, alter seeds, change code, or lower gates after execution.',
        'boundary':'Developer-frozen mechanism evidence. Local action-relative addressing, terminal seeding, equivalence-class choice, and backward propagation remain supplied.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
