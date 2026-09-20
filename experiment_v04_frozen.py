#!/usr/bin/env python3
"""Execute the pre-registered v0.4 learned-world holdout."""
from __future__ import annotations

import hashlib,json,pickle,time
from pathlib import Path

from bpc_learned_wave_v04 import learn_raw_physics,parse,replay,solve,validate_physics

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'artifacts'/'v04'
PROTOCOL=ROOT/'protocol_v04.json'; HOLDOUT=ROOT/'holdout_v04.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(model,maps,limit):
    writes=model.writes; output={}
    for item in maps:
        level=parse(item['map']); started=time.perf_counter(); result=solve(level,model,limit)
        result['seconds']=time.perf_counter()-started
        if result['solved']:
            result['replay_solved']=replay(level,result['sequence'])[0]
        else:result['replay_solved']=False
        output[item['id']]=result
    assert model.writes==writes
    return output


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():
        assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    maps=json.loads(HOLDOUT.read_text()); assert sha(HOLDOUT)==protocol['holdout_sha256']
    config=protocol['config']; started=time.perf_counter()
    full,no_far,experience,manifest=learn_raw_physics(
        config['training_seed'],config['training_episodes'],config['training_steps'])
    assert full.digest()==protocol['expected_model_sha256']
    assert manifest==protocol['expected_training_manifest']
    validation={
        'full':validate_physics(full,config['validation_seed'],config['validation_episodes'],config['validation_steps']),
        'no_far':validate_physics(no_far,config['validation_seed'],config['validation_episodes'],config['validation_steps'])}
    writes=full.writes
    conditions={'primary':evaluate(full,maps,config['state_limit']),
                'no_far':evaluate(no_far,maps,config['state_limit'])}
    assert full.writes==writes
    threshold=protocol['adoption_thresholds']; primary=conditions['primary']; ablation=conditions['no_far']
    push=validation['full']; no_far_push=validation['no_far']
    gate={
        'full_local_all_correct':all(push[f'{kind}_correct']==push[f'{kind}_total'] for kind in ('other','box_change')),
        'full_local_all_known':all(push[f'{kind}_known']==push[f'{kind}_total'] for kind in ('other','box_change')),
        'no_far_push_accuracy_at_most_25pct':no_far_push['box_change_correct']/no_far_push['box_change_total']<=threshold['no_far_max_push_accuracy'],
        'all_holdouts_solved':all(x['solved'] for x in primary.values()),
        'all_solutions_replay':all(x['replay_solved'] for x in primary.values()),
        'all_unseen_four_box_maps_solved':all(primary[x['id']]['solved'] for x in maps if x['boxes']==4),
        'beats_no_far_by_75pp':(sum(x['solved'] for x in primary.values())-sum(x['solved'] for x in ablation.values()))/len(maps)>=threshold['solve_margin'],
        'frozen_model_writes_zero':full.writes-writes==0}
    result={'format':'bpc-learned-world-v04','evidence_level':'developer-frozen local holdout; not third-party blind',
        'archive_v03_sha256':protocol['archive_v03_sha256'],'training_experience':experience,
        'training_manifest':manifest,'learned_rows':len(full.rows),'model_sha256':full.digest(),
        'validation':validation,'holdout':{'maps':len(maps),'boxes':[x['boxes'] for x in maps],
            'shortest_action_distances':[x['shortest_actions'] for x in maps]},
        'conditions':conditions,'gate':gate,'adopted':all(gate.values()),
        'frozen_model_writes':full.writes-writes,'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'source_sha256':protocol['source_sha256'],
        'supported_claim':'A 48-row local transition probability cube learned from raw random interaction transfers into the fixed v0.3 wave shell on unseen layouts and an unseen four-box count.',
        'boundary':'Not pure direct control or AGI. Reachable-component compression, macro candidate geometry, terminal seeding, backward propagation, and raw cell channels remain supplied.'}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    with (OUT/'model.pkl').open('wb') as file:pickle.dump(full,file,protocol=5)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
