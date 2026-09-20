#!/usr/bin/env python3
"""Freeze the v0.6.1 serialization-only repair before holdout execution."""
from __future__ import annotations

import hashlib,json
from pathlib import Path

from bpc_learned_geometry_v06 import learn_push_templates
from bpc_learned_wave_v04 import learn_raw_physics
from bpc_reversible_wave_v05 import discover_inverses

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v061.json';HOLDOUT=ROOT/'holdout_v06.json'
PREVIOUS=ROOT/'protocol_v06.json'
FILES=('bpc_learned_wave_v04.py','bpc_reversible_wave_v05.py','bpc_learned_geometry_v06.py',
       'experiment_v06_frozen.py','experiment_v061_frozen.py','freeze_v061.py')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return json.loads(json.dumps(value))


def main():
    if PROTOCOL.exists():raise SystemExit('v0.6.1 already frozen; refusing to overwrite')
    previous=json.loads(PREVIOUS.read_text());config=previous['config']
    assert sha(HOLDOUT)==previous['holdout_sha256']
    model,_,_,manifest=learn_raw_physics(config['world_seed'],config['world_episodes'],config['world_steps'])
    inverse,inverse_evidence=discover_inverses(config['inverse_seed'],config['inverse_episodes'],config['inverse_steps'])
    templates,evidence,pushes=learn_push_templates(config['template_seed'],config['template_episodes'],config['template_steps'])
    assert canonical(templates)==previous['expected_templates']
    assert canonical(evidence)==previous['expected_template_evidence'] and pushes==previous['expected_template_training_pushes']
    protocol={'format':'bpc-learned-geometry-v061-frozen-protocol','frozen_before_holdout_execution':True,
        'question':previous['question'],'config':config,'expected_model_sha256':model.digest(),
        'expected_training_manifest':manifest,'expected_inverse':inverse,
        'expected_inverse_evidence':inverse_evidence,'expected_templates':canonical(templates),
        'expected_template_evidence':canonical(evidence),'expected_template_training_pushes':pushes,
        'holdout_sha256':sha(HOLDOUT),'adoption_thresholds':previous['adoption_thresholds'],
        'controls':previous['controls'],'classifier_dev':previous['classifier_dev'],
        'supersedes_protocol_sha256':sha(PREVIOUS),
        'predecessor_failure':'Container-type assertion before audit or holdout; v0.6.1 changes only JSON normalization.',
        'source_sha256':{name:sha(ROOT/name) for name in FILES},
        'failure_policy':previous['failure_policy'],'boundary':previous['boundary']}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
