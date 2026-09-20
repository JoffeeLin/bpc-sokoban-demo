#!/usr/bin/env python3
"""Execute the pre-registered v0.9 direct probability-composition test."""
from __future__ import annotations

import hashlib,inspect,json,time
from pathlib import Path

from bpc_cross_task_v07 import World
from bpc_direct_composition_v09 import ProductPolicy,evaluate,fixed_step,shortest,train

ROOT=Path(__file__).resolve().parent;PROTOCOL=ROOT/'protocol_v09_direct.json';HOLDOUT=ROOT/'holdout_v09.json';OUT=ROOT/'artifacts'/'v09direct'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def total(rows,budget,name,key):return sum(row[budget][name][key] for row in rows)


def main():
    protocol=json.loads(PROTOCOL.read_text())
    for name,expected in protocol['source_sha256'].items():assert sha(ROOT/name)==expected,f'source changed after freeze: {name}'
    assert sha(HOLDOUT)==protocol['holdout_sha256'];data=json.loads(HOLDOUT.read_text());holdout=[]
    for row in data['worlds']:
        world=World(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'])
        assert shortest(world)==row['shortest'] and shortest(world,True) is None;holdout.append((world,row['shortest']))
    config=protocol['config'];threshold=protocol['adoption_thresholds'];started=time.perf_counter()
    shared,specialists,events=train(config['train_seed'],config['uniform_episodes'],config['guided_rounds'],config['guided_episodes'],config['train_steps'])
    digests={'shared':shared.digest(),'push':specialists['push'].digest(),'collect':specialists['collect'].digest()}
    assert events==protocol['expected_training_events'] and digests==protocol['expected_model_digests']
    product=ProductPolicy(specialists['push'],specialists['collect']);models={'product':product,'shared':shared,
        'collect_only':specialists['collect'],'push_only':specialists['push'],'rotated':product,'uniform':shared}
    writes={'shared':shared.writes,'push':specialists['push'].writes,'collect':specialists['collect'].writes}
    holdouts={}
    for seed in config['eval_seeds']:
        by_budget={}
        for budget in config['step_budgets']:by_budget[str(budget)]=evaluate(models,holdout,seed,config['episodes_per_map'],budget)[0]
        holdouts[str(seed)]=by_budget
    rows=list(holdouts.values());short='32';long='160';episodes=len(holdout)*config['episodes_per_map']*len(rows)
    product_short=total(rows,short,'product','successes');collect_short=total(rows,short,'collect_only','successes')
    shared_short=total(rows,short,'shared','successes');uniform_short=total(rows,short,'uniform','successes')
    rotated_short=total(rows,short,'rotated','successes');product_long=total(rows,long,'product','successes');collect_long=total(rows,long,'collect_only','successes')
    source=inspect.getsource(ProductPolicy);forbidden=('family','reward','score','loss','gradient','torch','tensorflow','sklearn')
    source_scan={word:word not in source for word in forbidden}
    per_world=[sum(row[short]['product'][f'world_{i}_successes'] for row in rows) for i in range(1,len(holdout)+1)]
    gate={
        'holdout_all_requires_push':all(shortest(world,True) is None for world,_ in holdout),
        'product_rate_at_least_30pct':product_short/episodes>=threshold['product_rate'],
        'product_beats_collect_by_5pp':(product_short-collect_short)/episodes>=threshold['collect_margin'],
        'product_beats_shared_by_8pp':(product_short-shared_short)/episodes>=threshold['shared_margin'],
        'product_beats_uniform_by_20pp':(product_short-uniform_short)/episodes>=threshold['uniform_margin'],
        'product_beats_rotated_by_25pp':(product_short-rotated_short)/episodes>=threshold['rotated_margin'],
        'product_not_worse_at_160_steps':product_long>=collect_long,
        'all_sixteen_worlds_have_success':all(per_world),
        'anonymous_equal_product_source':all(source_scan.values()),
        'frozen_model_writes_zero':shared.writes==writes['shared'] and specialists['push'].writes==writes['push'] and specialists['collect'].writes==writes['collect']}
    result={'format':'bpc-direct-composition-v09','evidence_level':'developer-frozen held-out synthetic direct control; not third-party blind',
        'question':protocol['question'],'training':events,'model_digests':digests,'holdout':{'worlds':len(holdout),
        'shortest_distances':[distance for _,distance in holdout],'generation_attempts':data['attempts']},
        'conditions':holdouts,'aggregate':{'episodes_per_condition_budget':episodes,'product_32':product_short,
        'collect_only_32':collect_short,'shared_32':shared_short,'uniform_32':uniform_short,'rotated_32':rotated_short,
        'product_160':product_long,'collect_only_160':collect_long,'product_32_per_world':per_world},
        'source_scan':source_scan,'model_writes_during_evaluation':{name:model.writes-writes[name] for name,model in {'shared':shared,**specialists}.items()},
        'gate':gate,'adopted':all(gate.values()),'seconds':time.perf_counter()-started,'protocol_sha256':sha(PROTOCOL),
        'holdout_sha256':sha(HOLDOUT),'source_sha256':protocol['source_sha256'],
        'supported_claim':'Two independently learned BPC Choice distributions combine by an equal probability product to improve direct action selection on new tasks that require both source mechanisms.',
        'boundary':'The equal product, raw encoder, task generators, binary success events, episode limits, and evaluation criterion are supplied. No runtime planner/search or combined-task training; not autonomous task routing or AGI.'}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
