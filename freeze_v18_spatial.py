#!/usr/bin/env python3
"""Freeze v0.18 D4 gauge/action binding before held-out execution."""
import hashlib,json
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import infer_relational_support_binding,inverse,lab_distance,lab_suite
from bpc_open_interface_v15 import action_stats
from bpc_spatial_interface_v18 import collect_spatial,gauge_equivalent_mapping,infer_spatial_action,infer_spatial_gauges
from bpc_three_factor_v12 import train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v18.json';PROTOCOL=ROOT/'protocol_v18_spatial.json'
SOURCES=('bpc_spatial_interface_v18.py','bpc_cross_generator_v17.py','bpc_composite_binding_v16.py','bpc_open_interface_v15.py',
    'bpc_three_factor_v12.py','bpc_evidence_field_v11.py','bpc_cross_task_v07.py','bpc_direct_composition_v09.py',
    'general_bpc_v7.py','experiment_v5.py','experiment_v18_spatial_frozen.py','freeze_v18_spatial.py')
SENSORS=((None,5,2,None,0,4,None,1,3),(3,None,0,5,None,2,4,None,None,1),
    (None,1,None,4,2,None,5,0,None,3,None),(2,None,5,None,1,3,None,None,0,None,4,None))
ACTIONS=((2,None,0,3,1),(None,1,3,None,0,2),(3,None,None,1,2,None,0),(None,2,None,0,3,None,1,None))
KINDS=((3,4,5),(5,3,4,5),(4,5,3,4,5),(3,5,4,3,5,4));SPATIAL=(2,3,5,6)
MIXES=({'push':126,'collect':27,'open':27},{'push':27,'collect':126,'open':27},
    {'push':27,'collect':27,'open':126},{'push':60,'collect':60,'open':60})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_spatial(row):return {**row,'mapping':list(row['mapping']),'second':{**row['second'],'mapping':list(row['second']['mapping'])},'candidate_slots':list(row['candidate_slots']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_gauge(row):return {**row,'mapping':list(row['mapping']),'candidate_slots':list(row['candidate_slots']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}


def main():
    config={'train_seed':121010,'reference_seed':182010,'target_seeds':[[182110+i*10+j for j in range(4)] for i in range(4)],
        'calibration_steps':32,'reference_worlds_per_family':100,'sensor_routes':[list(x) for x in SENSORS],
        'action_routes':[list(x) for x in ACTIONS],'distractor_kinds':[list(x) for x in KINDS],'spatial_transforms':list(SPATIAL),
        'target_mixtures':MIXES,'holdout_seed':182510,'worlds_per_family':12,'eval_seeds':[182610,182710],
        'episodes_per_map':24,'step_budget':64,'random_binding_seed':182810}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;reference_actions=action_stats(reference_triples,range(6),6,4);calibration=[]
    for seeds,sensors,actions,kinds,spatial in zip(config['target_seeds'],SENSORS,ACTIONS,KINDS,SPATIAL):
        targets=[];triples=[];streams=[];regimes=[]
        for seed,mix in zip(seeds,MIXES):
            target,row,initials,target_support=collect_spatial(seed,mix,config['calibration_steps'],sensors,actions,kinds,spatial,excluded)
            excluded|=initials;targets.append((target,target_support,row));triples.extend(row);streams.append(row)
            regimes.append({'interface_digest':target.digest(),'support':support(target_support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets);channel_oracle=inverse(sensors,6)
        assert channel['mapping']==channel_oracle and all(x['mapping']==channel_oracle for x in channel['per_stream'])
        single=infer_spatial_action(reference_actions,triples,channel['mapping'],len(sensors),len(actions),streams)
        gauges=infer_spatial_gauges(reference_actions,triples,channel['mapping'],len(sensors),len(actions),streams);action_oracle=inverse(actions,4)
        expected={transform:gauge_equivalent_mapping(spatial,transform,action_oracle) for transform in range(8)}
        assert all(row['mapping']==expected[row['transform']] and set(row['candidate_slots'])==set(action_oracle) for row in gauges)
        assert all(stream['mapping']==expected[row['transform']] for row in gauges for stream in row['per_stream'])
        calibration.append({'regimes':regimes,'channel_oracle':list(channel_oracle),'channel_binding':norm_sensor(channel),
            'action_oracle':list(action_oracle),'single_binding':norm_spatial(single),'gauge_bindings':[norm_gauge(x) for x in gauges],
            'gauge_expected':[{'transform':x,'mapping':list(expected[x])} for x in range(8)]})
    suite,attempts=lab_suite(config['holdout_seed'],config['worlds_per_family'],excluded);worlds=[]
    for family,world,distance in suite:
        assert lab_distance(world,family)==distance
        if family=='joint':assert lab_distance(world,family,True,False) is None and lab_distance(world,family,False,True) is None
        worlds.append({'family':family,**world.__dict__,'shortest':distance})
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds}
    assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-spatial-v18-holdout','seed':config['holdout_seed'],
        'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-spatial-v18-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a frozen non-neural BPC direct controller preserve control on disjoint unseen independent-generator worlds when sensor planes, actuator slots, nuisance families, and the spatial D4 frame all change, by learning the full observationally equivalent gauge-action class from unlabeled transitions?',
        'config':config,'development_result_sha256':sha(ROOT/'artifacts'/'v18spatial'/'development.json'),
        'expected_training_events':events,'expected_factor_digest':learner.digest(),'reference_interface_digest':reference.digest(),
        'reference_support':support(reference_support),'reference_action_digest':reference_actions.digest(),'expected_calibration':calibration,
        'holdout_sha256':sha(HOLDOUT),'adoption_thresholds':{'minimum_oracle_fraction_each_interface':.85,
            'minimum_shuffled_margin_each_interface':.05,'minimum_no_spatial_margin_each_interface':.05},
        'controls':['oracle binding over the same frozen policy and held-out worlds','maximum-likelihood single gauge',
            'cyclically mismatched gauge-action pairs with identical learned parts','no spatial restoration','fixed random channel, frame, and action binding',
            'four new variable-width interfaces','four actual non-identity D4 transforms absent as actual transforms in development',
            'held-out nuisance formulas 3/4/5 after development used 0/1/2','four independent unlabeled regimes per interface',
            'two evaluation action seeds','zero model writes and unchanged model digest','disjoint training, calibration, and holdout worlds'],
        'classifier_dev':{'model':'jev-1.13.0','batch_items':12,'role':'validation-control routing only; absent from inference, training, evaluation, and runtime',
            'accepted_high_confidence':['disjoint world identities plus zero writes and unchanged digest','source, holdout, seed, threshold, and calibration fingerprint freeze'],
            'rejected_high_confidence':['held-out task success selects a transform','regenerate holdout after random-control result','classifier confidence becomes action probability','claim absolute transform recovery']},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace mechanisms, interfaces, transforms, nuisance families, worlds, seeds, sources, controls, or thresholds after held-out execution.',
        'boundary':'Developer-frozen synthetic gauge-class transfer, not third-party blind and not AGI. Absolute D4 orientation is not identifiable with anonymous actions. Canonical semantics, six raw planes, four actions, maximum 7x7 canvas, D4 candidate family, nuisance formulas, statistics, generators, terminal events, and direct policy remain supplied. No neural network, task label, reward, planner, runtime search, classifier runtime, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
