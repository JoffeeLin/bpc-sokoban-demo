#!/usr/bin/env python3
"""Execute the pre-registered v0.7 cross-task transition-composition test."""
from __future__ import annotations

import hashlib,inspect,json,time
from pathlib import Path

from bpc_cross_task_v07 import FragmentChainWorld,evaluate,train

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v07_cross.json';OUT=ROOT/'artifacts'/'v07cross'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rate(row,key):return row[key]/row[key.replace('correct','total').replace('known','total')]


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter()
    compressed,residual,fragments,full,events=train(config['train_seed'],config['train_episodes'],config['train_steps'])
    digests={'condition_deleted':compressed.digest(),'residual_prime':residual.digest(),'fragment_chain':fragments.digest()}
    assert events==protocol['expected_training_events'] and digests==protocol['expected_model_digests']
    assert len(compressed.samples)==protocol['expected_distinct_training_inputs'] and events['composition_inputs']==0
    models={'condition_deleted':compressed,'residual_prime':residual,'fragment_chain':fragments,'full_context':full}
    writes={name:model.writes for name,model in models.items()}
    combined={str(seed):evaluate(models,seed,config['eval_episodes'],config['eval_steps']) for seed in config['eval_seeds']}
    retention={family:evaluate(models,seed,config['retention_episodes'],config['retention_steps'],family)
               for family,seed in zip(('push','collect'),config['retention_seeds'])}
    repeated=evaluate(models,config['eval_seeds'][0],config['eval_episodes'],config['eval_steps'])
    source=inspect.getsource(FragmentChainWorld)
    forbidden=('family','objects','marks','ACTIONS','reward','score','loss','gradient','torch','tensorflow','sklearn')
    source_scan={word:word not in source for word in forbidden}
    rows=[combined[str(seed)] for seed in config['eval_seeds']]
    gate={
        'training_contains_zero_compositions':events['composition_inputs']==0,
        'minimum_new_composition_events':all(row['fragment_chain']['composition_total']>=threshold['composition_min_events'] for row in rows),
        'fragment_chain_all_predictions_exact':all(row['fragment_chain']['correct']==row['fragment_chain']['total'] for row in rows),
        'fragment_chain_all_compositions_exact':all(row['fragment_chain']['composition_correct']==row['fragment_chain']['composition_total'] for row in rows),
        'full_context_knows_zero_compositions':all(row['full_context']['composition_known']==0 for row in rows),
        'beats_condition_deleted_by_margin':all(
            rate(row['fragment_chain'],'composition_correct')-rate(row['condition_deleted'],'composition_correct')>=threshold['condition_deleted_margin'] for row in rows),
        'retains_both_training_families':all(
            retention[family]['fragment_chain']['correct']==retention[family]['fragment_chain']['total'] for family in retention),
        'deterministic_repeat':repeated==rows[0],
        'anonymous_model_source':all(source_scan.values()),
        'frozen_model_writes_zero':all(model.writes==writes[name] for name,model in models.items())}
    result={'format':'bpc-cross-task-v07','evidence_level':'developer-frozen held-out synthetic worlds; not third-party blind',
        'question':protocol['question'],'training':events,'distinct_training_inputs':len(compressed.samples),
        'model_digests':digests,'context_widths':[len(x) for x in compressed.contexts],
        'fragment_prerequisites':fragments.prerequisites,'combined_holdouts':combined,'retention':retention,
        'source_scan':source_scan,'model_writes_during_evaluation':{name:model.writes-writes[name] for name,model in models.items()},
        'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,
        'protocol_sha256':sha(PROTOCOL),'source_sha256':protocol['source_sha256'],
        'supported_claim':'Anonymous bit-change fragments learned separately from push-only and collect-only worlds compose exact one-step transitions when both mechanisms first coexist.',
        'boundary':'Local one-step world-function composition only. Raw bit channels, action-relative window, action interface, task generators, and evaluator are supplied; no planning, direct policy, language, or AGI claim.'}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
