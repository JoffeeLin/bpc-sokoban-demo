#!/usr/bin/env python3
"""Execute v0.6.1: the frozen serialization-only repair of v0.6."""
from __future__ import annotations

import json,re,time

from bpc_learned_geometry_v06 import audit_templates,learn_push_templates
from bpc_learned_wave_v04 import learn_raw_physics
from bpc_reversible_wave_v05 import discover_inverses
from experiment_v06_frozen import HOLDOUT,ROOT,evaluate,sha

OUT=ROOT/'artifacts'/'v061';PROTOCOL=ROOT/'protocol_v061.json'


def canonical(value):return json.loads(json.dumps(value))


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    maps=json.loads(HOLDOUT.read_text());assert sha(HOLDOUT)==protocol['holdout_sha256']
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter()
    model,_,experience,manifest=learn_raw_physics(config['world_seed'],config['world_episodes'],config['world_steps'])
    assert model.digest()==protocol['expected_model_sha256'] and manifest==protocol['expected_training_manifest']
    inverse,inverse_evidence=discover_inverses(config['inverse_seed'],config['inverse_episodes'],config['inverse_steps'])
    assert list(inverse)==protocol['expected_inverse'] and inverse_evidence==protocol['expected_inverse_evidence']
    templates,evidence,pushes=learn_push_templates(config['template_seed'],config['template_episodes'],config['template_steps'])
    assert canonical(templates)==protocol['expected_templates']
    assert canonical(evidence)==protocol['expected_template_evidence'] and pushes==protocol['expected_template_training_pushes']
    rotated=tuple(templates[(action+1)%4] for action in range(4))
    audit={'learned':audit_templates(templates,config['audit_seed'],config['audit_episodes'],config['audit_steps']),
           'rotated':audit_templates(rotated,config['audit_seed'],config['audit_episodes'],config['audit_steps'])}
    writes=model.writes;conditions={'primary':evaluate(model,inverse,templates,maps,config['state_limit']),
                                    'rotated_geometry':evaluate(model,inverse,rotated,maps,config['state_limit'])}
    assert model.writes==writes
    source=(ROOT/'bpc_learned_geometry_v06.py').read_text()
    forbidden={'supplied_ACTIONS':r'\bACTIONS\b','xor_inverse':r'action\s*\^\s*1','supplied_moved':r'\bmoved\s*\('}
    source_scan={name:not re.search(pattern,source) for name,pattern in forbidden.items()}
    primary=conditions['primary'];ablation=conditions['rotated_geometry']
    learned_rate=audit['learned']['exact']/audit['learned']['pushes'];rotated_rate=audit['rotated']['exact']/audit['rotated']['pushes']
    unique=all(len(row)==1 and row[0]['count']>=threshold['template_min_support'] for row in evidence)
    gate={'push_templates_uniquely_discovered':unique,
        'learned_template_audit_exact':learned_rate>=threshold['template_audit_rate'],
        'rotated_template_audit_zero':rotated_rate<=threshold['rotated_template_max_audit_rate'],
        'all_new_holdouts_solved':all(x['solved'] for x in primary.values()),
        'all_solutions_replay':all(x['replay_solved'] for x in primary.values()),
        'all_unseen_four_box_maps_solved':all(primary[x['id']]['solved'] for x in maps if x['boxes']==4),
        'beats_rotated_geometry_by_75pp':(sum(x['solved'] for x in primary.values())-sum(x['solved'] for x in ablation.values()))/len(maps)>=threshold['solve_margin'],
        'no_handwritten_macro_action_geometry':all(source_scan.values()),
        'frozen_model_writes_zero':model.writes-writes==0}
    result={'format':'bpc-learned-geometry-v061','evidence_level':'developer-frozen local holdout; not third-party blind',
        'predecessor_failure':protocol['predecessor_failure'],'training_experience':experience,
        'training_manifest':manifest,'model_sha256':model.digest(),'inverse':inverse,
        'inverse_evidence':inverse_evidence,'templates':templates,'template_evidence':evidence,
        'template_training_pushes':pushes,'template_audit':audit,
        'holdout':{'maps':len(maps),'boxes':[x['boxes'] for x in maps],
            'shortest_action_distances':[x['shortest_actions'] for x in maps]},
        'conditions':conditions,'source_scan':source_scan,'gate':gate,'adopted':all(gate.values()),
        'frozen_model_writes':model.writes-writes,'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'source_sha256':protocol['source_sha256'],
        'supported_claim':'Anonymous push-delta templates learned from random interaction replace supplied macro predecessor geometry inside the fixed learned-world reversible wave on new layouts.',
        'boundary':'Not direct control, cross-task transfer, or AGI. Local action-relative addressing, terminal seeding, equivalence-class choice, and backward propagation remain supplied.'}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
