#!/usr/bin/env python3
"""Execute the pre-registered v0.8 open-loop cross-task rollout test."""
from __future__ import annotations

import hashlib,inspect,json,time
from pathlib import Path

from bpc_cross_task_rollout_v08 import evaluate_rollouts,learned_step,trained

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v08_rollout.json';OUT=ROOT/'artifacts'/'v08rollout'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter()
    models,events=trained(config['train_seed'],config['train_episodes'],config['train_steps'])
    digests={name:model.digest() for name,model in models.items() if hasattr(model,'digest')}
    assert events==protocol['expected_training_events'] and digests==protocol['expected_model_digests']
    writes={name:model.writes for name,model in models.items()};horizons=tuple(config['horizons'])
    holdouts={str(seed):evaluate_rollouts(models,seed,config['eval_episodes'],horizons) for seed in config['eval_seeds']}
    retention={family:evaluate_rollouts(models,seed,config['retention_episodes'],(config['retention_horizon'],),family)
               for family,seed in zip(('push','collect'),config['retention_seeds'])}
    repeated=evaluate_rollouts(models,config['eval_seeds'][0],config['eval_episodes'],horizons)
    source=inspect.getsource(learned_step);forbidden=('truth','reward','score','loss','gradient','torch','tensorflow','sklearn')
    source_scan={word:word not in source for word in forbidden};longest=str(max(horizons))
    rows=[holdouts[str(seed)] for seed in config['eval_seeds']]
    gate={
        'training_contains_zero_compositions':events['composition_inputs']==0,
        'fragment_chain_all_rollouts_exact':all(
            row['fragment_chain'][str(h)]['exact_all']==config['eval_episodes'] for row in rows for h in horizons),
        'fragment_chain_all_predicted_steps_exact':all(
            row['fragment_chain'][str(h)]['exact_steps']==config['eval_episodes']*h for row in rows for h in horizons),
        'minimum_long_horizon_composition_episodes':all(
            row['fragment_chain'][longest]['composition_episodes']>=threshold['long_horizon_composition_min'] for row in rows),
        'condition_deleted_long_horizon_control_fails':all(
            row['condition_deleted'][longest]['composition_exact_all']/row['condition_deleted'][longest]['composition_episodes']<=threshold['condition_deleted_max_rate'] for row in rows),
        'full_context_knows_zero_composition_rollouts':all(
            row['full_context'][longest]['composition_known']==0 for row in rows),
        'retains_64_step_training_families':all(
            retention[family]['fragment_chain'][str(config['retention_horizon'])]['exact_all']==config['retention_episodes'] for family in retention),
        'deterministic_repeat':repeated==rows[0],
        'learned_rollout_has_no_true_step':all(source_scan.values()),
        'frozen_model_writes_zero':all(model.writes==writes[name] for name,model in models.items())}
    result={'format':'bpc-cross-task-rollout-v08','evidence_level':'developer-frozen held-out synthetic rollouts; not third-party blind',
        'question':protocol['question'],'training':events,'model_digests':digests,'holdouts':holdouts,'retention':retention,
        'source_scan':source_scan,'model_writes_during_evaluation':{name:model.writes-writes[name] for name,model in models.items()},
        'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,'protocol_sha256':sha(PROTOCOL),
        'source_sha256':protocol['source_sha256'],
        'supported_claim':'The separately trained anonymous fragment-chain world function remains exact when recursively rolled forward for up to 64 supplied random actions in never-trained combined worlds.',
        'boundary':'Open-loop prediction with supplied actions and global state reconstruction. Not goal selection, planning, direct policy control, autonomous task discovery, or AGI.'}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
