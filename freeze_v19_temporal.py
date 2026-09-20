#!/usr/bin/env python3
"""Freeze v0.19 end-to-end temporal-gauge evaluation before holdout execution."""
import hashlib,json
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import infer_relational_support_binding,inverse,lab_distance,lab_suite
from bpc_open_interface_v15 import action_stats
from bpc_spatial_interface_v18 import gauge_equivalent_mapping
from bpc_temporal_interface_v19 import collect_temporal,infer_temporal_gauge
from bpc_three_factor_v12 import train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v19.json';PROTOCOL=ROOT/'protocol_v19_temporal.json'
SOURCES=('bpc_temporal_interface_v19.py','bpc_spatial_interface_v18.py','bpc_cross_generator_v17.py','bpc_composite_binding_v16.py',
    'bpc_open_interface_v15.py','bpc_three_factor_v12.py','bpc_evidence_field_v11.py','bpc_cross_task_v07.py',
    'bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py','experiment_v19_temporal_frozen.py','freeze_v19_temporal.py')
SENSORS=((1,None,5,0,None,3,2,None,4),(None,4,2,None,5,1,None,0,3,None),
    (2,None,0,None,4,5,None,3,None,1,None),(None,3,None,1,5,None,0,None,4,2,None,None))
ACTIONS=((1,3,None,0,2),(None,2,0,None,3,1),(2,None,1,None,0,3,None),(None,0,None,3,1,None,2,None))
KINDS=((3,5,4),(4,3,5,4),(5,4,3,5,4),(3,4,5,3,4,5));SPATIAL=(2,3,5,6);TEMPORAL=((0,2),(1,1),(0,4),(2,2))
MIXES=({'push':126,'collect':27,'open':27},{'push':27,'collect':126,'open':27},{'push':27,'collect':27,'open':126},{'push':60,'collect':60,'open':60})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_gauge(row):return {**row,'mapping':list(row['mapping']),'candidate_slots':list(row['candidate_slots'])}
def norm_temporal(row):return {**row,'single':norm_gauge(row['single']),'gauges':[norm_gauge(x) for x in row['gauges']],
    'candidate_lags':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['candidate_lags']],
    'per_stream':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['per_stream']]}


def main():
    config={'train_seed':121010,'reference_seed':192010,'target_seeds':[[192110+i*10+j for j in range(4)] for i in range(4)],
        'calibration_steps':32,'reference_worlds_per_family':100,'sensor_routes':[list(x) for x in SENSORS],
        'action_routes':[list(x) for x in ACTIONS],'distractor_kinds':[list(x) for x in KINDS],'spatial_transforms':list(SPATIAL),
        'temporal_delays':[list(x) for x in TEMPORAL],'maximum_total_lag':4,'target_mixtures':MIXES,
        'holdout_seed':192510,'worlds_per_family':12,'eval_seeds':[192610,192710],'episodes_per_map':24,'step_budget':80,'random_binding_seed':192810}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,reference_triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;reference_actions=action_stats(reference_triples,range(6),6,4);calibration=[]
    for seeds,sensors,actions,kinds,spatial,delays in zip(config['target_seeds'],SENSORS,ACTIONS,KINDS,SPATIAL,TEMPORAL):
        sensor_delay,actuator_delay=delays;targets=[];sequences=[];streams=[];regimes=[]
        for seed,mix in zip(seeds,MIXES):
            target,flat,episodes,initials,target_support=collect_temporal(seed,mix,config['calibration_steps'],sensors,actions,kinds,spatial,sensor_delay,actuator_delay,excluded)
            excluded|=initials;targets.append((target,target_support,flat));sequences.extend(episodes);streams.append(episodes)
            regimes.append({'interface_digest':target.digest(),'support':support(target_support)})
        channel=infer_relational_support_binding(reference,reference_support,reference_triples,targets);channel_oracle=inverse(sensors,6)
        assert channel['mapping']==channel_oracle and all(x['mapping']==channel_oracle for x in channel['per_stream'])
        temporal=infer_temporal_gauge(reference_actions,sequences,channel['mapping'],len(sensors),len(actions),streams,config['maximum_total_lag'])
        total_lag=sensor_delay+actuator_delay;action_oracle=inverse(actions,4);expected={t:gauge_equivalent_mapping(spatial,t,action_oracle) for t in range(8)}
        assert temporal['lag']==total_lag and all(x['lag']==total_lag for x in temporal['per_stream'])
        assert all(x['mapping']==expected[x['transform']] and set(x['candidate_slots'])==set(action_oracle) for x in temporal['gauges'])
        assert all(x['mapping']==expected[x['transform']] for stream in temporal['per_stream'] for x in stream['gauges'])
        calibration.append({'regimes':regimes,'channel_oracle':list(channel_oracle),'channel_binding':norm_sensor(channel),
            'action_oracle':list(action_oracle),'total_lag_oracle':total_lag,'temporal_binding':norm_temporal(temporal),
            'gauge_expected':[{'transform':x,'mapping':list(expected[x])} for x in range(8)]})
    suite,attempts=lab_suite(config['holdout_seed'],config['worlds_per_family'],excluded);worlds=[]
    for family,world,distance in suite:
        assert lab_distance(world,family)==distance
        if family=='joint':assert lab_distance(world,family,True,False) is None and lab_distance(world,family,False,True) is None
        worlds.append({'family':family,**world.__dict__,'shortest':distance})
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds};assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-temporal-v19-holdout','seed':config['holdout_seed'],'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-temporal-v19-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a frozen non-neural BPC direct controller infer an unseen end-to-end sensorimotor lag jointly with anonymous sensor slots, actuator slots, and D4 spatial gauge from unlabeled transitions, then preserve control on disjoint independent-generator worlds?',
        'config':config,'development_result_sha256':sha(ROOT/'artifacts'/'v19temporal'/'development.json'),
        'expected_training_events':events,'expected_factor_digest':learner.digest(),'reference_interface_digest':reference.digest(),
        'reference_support':support(reference_support),'reference_action_digest':reference_actions.digest(),'expected_calibration':calibration,
        'holdout_sha256':sha(HOLDOUT),'adoption_thresholds':{'minimum_oracle_fraction_each_interface':.80,
            'minimum_zero_lag_margin_each_interface':.05,'minimum_shifted_lag_margin_each_interface':.05},
        'controls':['oracle sensor, spatial, and action binding over the same delayed environment','maximum-probability single spatial gauge inside learned lag',
            'zero-lag alignment using the same observations and issued actions','one-step-shifted history alignment using the same observations and issued actions',
            'fixed random channel, spatial, and action binding','four new variable-width interfaces','four actual non-identity D4 transforms absent as actual transforms in development',
            'total lags 2 and 4 absent as actual lags in development','two different sensor/actuator decompositions for each total lag',
            'held-out nuisance formulas 3/4/5','four independent unlabeled regimes per interface','two evaluation action seeds',
            'zero model writes and unchanged model digest','disjoint training, calibration, and holdout worlds'],
        'classifier_dev':{'model':'jev-1.13.0','batch_items':14,'selected':'joint sensor and actuator latency frontier','confidence':.82,
            'implemented_identifiable_quantity':'end-to-end lag only','role':'development route classification only; absent from inference, training, frozen evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace mechanisms, lag candidates, decompositions, interfaces, transforms, nuisance families, worlds, seeds, sources, controls, or thresholds after held-out execution.',
        'boundary':'Developer-frozen synthetic end-to-end temporal-gauge transfer, not third-party blind and not AGI. Sensor and actuator delay are observationally non-identifiable separately; only their sum is claimed. Lag candidates 0-4, D4 family, schema, statistics, generators, terminal events, and direct policy remain supplied. No neural network, task label, reward, planner, runtime search, classifier runtime, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
