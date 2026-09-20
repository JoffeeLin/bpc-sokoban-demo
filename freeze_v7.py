#!/usr/bin/env python3
"""Create the v7 holdout and immutable protocol before evaluation."""
from __future__ import annotations

import hashlib, json
from pathlib import Path

from sokoban_maps import digest, generate, max_wall_jaccard, solution_distance

ROOT=Path(__file__).resolve().parent
FILES=('bpc_sokoban.py','general_bpc_v7.py','sokoban_maps.py','experiment_v7_frozen.py')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path=ROOT/'protocol_v7.json'; holdout_path=ROOT/'holdout_v7.json'
    if protocol_path.exists():
        raise SystemExit('v7 is already frozen; refusing to overwrite')
    training=generate(40,77_031,(4,16),(5,13),.55)
    holdout=generate(10,20_260_920,(5,10),(7,12),.50)
    assert not set(training)&set(holdout)
    if holdout_path.exists():
        existing=tuple(tuple(row for row in level) for level in json.loads(holdout_path.read_text()))
        assert existing==holdout,'existing holdout differs from the fixed seed'
    else:
        holdout_path.write_text(json.dumps(holdout,indent=2)+'\n')
    protocol={
        'format':'general-bpc-sokoban-v7-frozen-protocol',
        'frozen_before_holdout_execution':True,
        'question':'Can one relation-count BPC trained on other layouts directly control ten unseen Sokoban layouts above fixed causal controls?',
        'config':{'training_map_count':40,'training_map_seed':77_031,
            'training_action_seed':7_000_007,'uniform_episodes_per_map':300,
            'guided_rounds':2,'guided_episodes_per_map':100,'guided_epsilon':.22,
            'training_max_steps':128,'holdout_map_count':10,'holdout_map_seed':20_260_920,
            'evaluation_episodes_per_map':256,'evaluation_seed':73_911,
            'evaluation_max_steps':192,'temperature':.72},
        'adoption_thresholds':{'aggregate_rate':.30,'every_map_rate':.01,
            'uniform_margin':.20,'rotated_margin':.20,'joint_margin':.10},
        'training_maps_sha256':digest(training),'holdout_maps_sha256':digest(holdout),
        'holdout_shortest_distances':[solution_distance(x) for x in holdout],
        'holdout_max_internal_wall_jaccard':max_wall_jaccard(holdout),
        'train_holdout_max_wall_jaccard':max_wall_jaccard(training,holdout),
        'source_sha256':{name:sha(ROOT/name) for name in FILES},
        'controls':['no_joint','change_fused','action_rotated','uniform'],
        'failure_policy':'Retain a miss; do not tune on this holdout or lower thresholds.'}
    protocol_path.write_text(json.dumps(protocol,indent=2)+'\n')
    print(json.dumps(protocol,indent=2))


if __name__=='__main__': main()
