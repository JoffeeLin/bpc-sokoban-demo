#!/usr/bin/env python3
"""Execute the immutable v0.21 hidden-regime holdout once."""
import hashlib,json,time
from collections import Counter
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import LabWorld,lab_suite
from bpc_hidden_mode_v21 import evaluate_hidden_interface
from bpc_stochastic_interface_v20 import effect_profiles
from bpc_three_factor_v12 import train
from experiment_v21_hidden_horizon_sweep import model
from experiment_v21_hidden_interface_dev import expected_channels
from freeze_v21_hidden import (CHANNELS,DELAYS,HOLDOUT,INITIALS,KINDS,PROTOCOL,SENSORS,SOURCES,SPATIAL,TRANSITIONS,calibration,sha)

ROOT=Path(__file__).resolve().parent


def add(target,source):
    for key,value in source.items():target[key]+=value


def main():
    started=time.perf_counter();protocol=json.loads(PROTOCOL.read_text());holdout=json.loads(HOLDOUT.read_text());config=protocol['config']
    assert protocol['frozen_before_holdout_execution'] and sha(HOLDOUT)==protocol['holdout_sha256']
    assert {name:sha(ROOT/name) for name in SOURCES}==protocol['source_sha256']
    learner,events=train(config['train_seed']);assert events==protocol['expected_training_events'] and learner.digest()==protocol['expected_factor_digest'];excluded=set(learner.training_initials)
    reference,triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;profiles=effect_profiles(triples);assert reference.digest()==protocol['reference_interface_digest'] and profiles.digest()==protocol['reference_effect_digest']
    calibrated,excluded=calibration(config,learner,reference,triples,reference_support,profiles,excluded)
    # The protocol is JSON, so compare the rebuilt calibration after the same
    # tuple-to-array normalization rather than Python container identities.
    assert json.loads(json.dumps(calibrated))==protocol['expected_calibration']
    suite=[]
    for row in holdout['worlds']:
        world=LabWorld(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')]);suite.append((row['family'],world,row['shortest']))
    conditions={};trace_worlds={};writes=learner.writes;digest=learner.digest()
    for index,row in enumerate(calibrated):
        learned=model(row);oracle=expected_channels(SPATIAL[index],row['selected_gauge_representative'],CHANNELS[index]);totals={name:Counter() for name in ('online','memoryless','no_update','shuffled','zero_lag','oracle')};seen={name:set() for name in totals}
        for seed in config['evaluation_seeds']:
            values,traces=evaluate_hidden_interface(learner,profiles,learned,suite,SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],tuple(row['sensor_binding']['mapping']),
                row['selected_gauge_representative'],CHANNELS[index],oracle,TRANSITIONS[index],INITIALS[index],seed+index,config['episodes_per_map_per_seed'],config['step_budget'])
            for name in totals:add(totals[name],values[name]);seen[name]|=set(traces[name])
        conditions[str(index)]={name:dict(value) for name,value in totals.items()};trace_worlds[str(index)]={name:len(value) for name,value in seen.items()}
    per=[]
    for key,row in conditions.items():
        joint_episodes=config['worlds_per_family']*config['episodes_per_map_per_seed']*len(config['evaluation_seeds'])
        per.append({'interface':int(key),'episodes':row['online']['episodes'],'joint_episodes':joint_episodes,**{name:value['successes'] for name,value in row.items()},
            **{f'{name}_joint':value['joint_successes'] for name,value in row.items()}})
    threshold=protocol['adoption_thresholds'];gates={'protocol_and_sources_unchanged':True,'calibration_exact':True,
        'each_online_at_least_80pct_oracle':all(x['online']>=x['oracle']*threshold['minimum_oracle_fraction_each_interface'] for x in per),
        'each_online_beats_memoryless_by_3pct_overall':all(x['online']-x['memoryless']>=x['episodes']*threshold['minimum_overall_memoryless_margin_each_interface'] for x in per),
        'each_joint_online_beats_memoryless_by_5pct':all(x['online_joint']-x['memoryless_joint']>=x['joint_episodes']*threshold['minimum_joint_margin_each_interface'] for x in per),
        'each_joint_online_beats_shuffled_by_5pct':all(x['online_joint']-x['shuffled_joint']>=x['joint_episodes']*threshold['minimum_joint_margin_each_interface'] for x in per),
        'each_joint_online_beats_zero_lag_by_5pct':all(x['online_joint']-x['zero_lag_joint']>=x['joint_episodes']*threshold['minimum_joint_margin_each_interface'] for x in per),
        'evaluation_writes_zero':learner.writes==writes,'model_digest_unchanged':learner.digest()==digest}
    result={'format':'bpc-hidden-v21-frozen-result','frozen':True,'protocol_sha256':sha(PROTOCOL),'holdout_sha256':sha(HOLDOUT),'conditions':conditions,
        'diagnostic':{'per_interface':per,'trace_worlds':trace_worlds,'online_successes':sum(x['online'] for x in per),'oracle_successes':sum(x['oracle'] for x in per),
            'memoryless_successes':sum(x['memoryless'] for x in per),'no_update_successes':sum(x['no_update'] for x in per),'shuffled_successes':sum(x['shuffled'] for x in per),
            'zero_lag_successes':sum(x['zero_lag'] for x in per),'episodes':sum(x['episodes'] for x in per),'online_joint_successes':sum(x['online_joint'] for x in per),
            'memoryless_joint_successes':sum(x['memoryless_joint'] for x in per),'joint_episodes':sum(x['joint_episodes'] for x in per)},
        'preregistered_gates':gates,'adopted':all(gates.values()),'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':protocol['boundary']}
    destination=ROOT/'artifacts'/'v21hidden'/'result.json';destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
