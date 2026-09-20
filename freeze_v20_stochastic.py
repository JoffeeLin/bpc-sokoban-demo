#!/usr/bin/env python3
"""Freeze v0.20 stochastic-channel evaluation before holdout execution."""
import hashlib,json
from pathlib import Path

from bpc_composite_binding_v16 import collect_composite_interface
from bpc_cross_generator_v17 import infer_relational_support_binding,inverse,lab_distance,lab_suite
from bpc_spatial_interface_v18 import transformed_delta
from bpc_stochastic_interface_v20 import collect_stochastic,effect_profiles,infer_stochastic_gauge
from bpc_three_factor_v12 import train

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v20.json';PROTOCOL=ROOT/'protocol_v20_stochastic.json'
SOURCES=('bpc_stochastic_interface_v20.py','bpc_temporal_interface_v19.py','bpc_spatial_interface_v18.py','bpc_cross_generator_v17.py',
    'bpc_composite_binding_v16.py','bpc_open_interface_v15.py','bpc_three_factor_v12.py','bpc_evidence_field_v11.py','bpc_cross_task_v07.py',
    'bpc_direct_composition_v09.py','general_bpc_v7.py','experiment_v5.py','experiment_v20_stochastic_frozen.py','freeze_v20_stochastic.py')
SENSORS=((1,None,5,0,None,3,2,None,4),(None,4,2,None,5,1,None,0,3,None),(2,None,0,None,4,5,None,3,None,1,None),(None,3,None,1,5,None,0,None,4,2,None,None))
CHANNELS=(
    ((.13,.55,.19,.13),(.14,.17,.12,.57),None,(.58,.11,.20,.11),(.17,.13,.55,.15)),
    (None,(.12,.18,.55,.15),(.54,.21,.13,.12),( .11,.57,.18,.14),None,(.15,.14,.13,.58)),
    ((.12,.19,.14,.55),None,(.57,.18,.13,.12),None,(.18,.12,.56,.14),None,(.13,.58,.17,.12)),
    (None,(.56,.20,.12,.12),None,(.14,.13,.16,.57),(.17,.57,.14,.12),None,(.13,.15,.58,.14),None))
KINDS=((3,5,4),(4,3,5,4),(5,4,3,5,4),(3,4,5,3,4,5));SPATIAL=(2,3,5,6);TEMPORAL=((0,2),(1,1),(0,4),(2,2))
MIXES=({'push':90,'collect':24,'open':24},{'push':24,'collect':90,'open':24},{'push':24,'collect':24,'open':90})


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def support(row):return [sorted(x) for x in sorted(row,key=lambda x:(len(x),tuple(x)))]
def norm_sensor(row):return {**row,'mapping':list(row['mapping']),'second':list(row['second']),'per_stream':[{**x,'mapping':list(x['mapping'])} for x in row['per_stream']]}
def norm_gauge(row):return {**row,'rows':[list(x) for x in row['rows']]}
def norm_stochastic(row):return {**row,'gauges':[norm_gauge(x) for x in row['gauges']],'single':norm_gauge(row['single']),
    'candidate_lags':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['candidate_lags']],
    'per_stream':[{**x,'gauges':[norm_gauge(y) for y in x['gauges']]} for x in row['per_stream']]}
def expected_rows(actual,candidate,channels):
    out=[]
    for row in channels:
        if row is None:out.append((0.,0.,0.,0.,1.));continue
        values=[]
        for action in range(4):
            delta=transformed_delta(candidate,action);physical=next(x for x in range(4) if transformed_delta(actual,x)==delta);values.append(row[physical])
        out.append(tuple(values)+(0.,))
    return tuple(out)
def error(learned,truth):return sum(abs(a-b) for row,target in zip(learned,truth) for a,b in zip(row,target))/(2*len(learned))


def main():
    config={'train_seed':122010,'reference_seed':202010,'target_seeds':[[202110+i*10+j for j in range(3)] for i in range(4)],'calibration_steps':32,
        'reference_worlds_per_family':100,'sensor_routes':[list(x) for x in SENSORS],'stochastic_channels':[[list(x) if x else None for x in rows] for rows in CHANNELS],
        'distractor_kinds':[list(x) for x in KINDS],'spatial_transforms':list(SPATIAL),'temporal_delays':[list(x) for x in TEMPORAL],
        'maximum_total_lag':4,'target_mixtures':MIXES,'holdout_seed':202510,'worlds_per_family':12,'eval_seeds':[202610,202710],
        'episodes_per_map':12,'step_budget':112}
    learner,events=train(config['train_seed']);excluded=set(learner.training_initials)
    reference,triples,initials,reference_support=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded)
    excluded|=initials;profiles=effect_profiles(triples);calibration=[]
    for seeds,sensors,channels,kinds,spatial,delays in zip(config['target_seeds'],SENSORS,CHANNELS,KINDS,SPATIAL,TEMPORAL):
        sensor_delay,actuator_delay=delays;targets=[];sequences=[];streams=[];regimes=[]
        for seed,mix in zip(seeds,MIXES):
            target,flat,episodes,initials,target_support=collect_stochastic(seed,mix,config['calibration_steps'],sensors,channels,kinds,spatial,sensor_delay,actuator_delay,excluded)
            excluded|=initials;targets.append((target,target_support,flat));sequences.extend(episodes);streams.append(episodes);regimes.append({'interface_digest':target.digest(),'support':support(target_support)})
        sensor=infer_relational_support_binding(reference,reference_support,triples,targets);sensor_oracle=inverse(sensors,6)
        assert sensor['mapping']==sensor_oracle and all(x['mapping']==sensor_oracle for x in sensor['per_stream'])
        stochastic=infer_stochastic_gauge(profiles,sequences,sensor['mapping'],len(sensors),len(channels),streams,config['maximum_total_lag']);lag=sensor_delay+actuator_delay
        assert stochastic['lag']==lag and all(x['lag']==lag for x in stochastic['per_stream'])
        errors=[error(x['rows'],expected_rows(spatial,x['transform'],channels)) for x in stochastic['gauges']]
        stream_errors=[error(x['rows'],expected_rows(spatial,x['transform'],channels)) for stream in stochastic['per_stream'] for x in stream['gauges']]
        assert max(errors)<=.12 and max(stream_errors)<=.20
        calibration.append({'regimes':regimes,'sensor_oracle':list(sensor_oracle),'sensor_binding':norm_sensor(sensor),'total_lag_oracle':lag,
            'stochastic_binding':norm_stochastic(stochastic),'maximum_gauge_channel_error':max(errors),'maximum_stream_gauge_channel_error':max(stream_errors)})
    suite,attempts=lab_suite(config['holdout_seed'],config['worlds_per_family'],excluded);worlds=[]
    for family,world,distance in suite:
        assert lab_distance(world,family)==distance
        if family=='joint':assert lab_distance(world,family,True,False) is None and lab_distance(world,family,False,True) is None
        worlds.append({'family':family,**world.__dict__,'shortest':distance})
    keys={(x['h'],x['w'],x['walls'],x['agent'],x['objects'],x['marks'],x['switches'],x['gates']) for x in worlds};assert len(keys)==len(worlds) and not keys&excluded
    HOLDOUT.write_text(json.dumps({'format':'bpc-stochastic-v20-holdout','seed':config['holdout_seed'],'generation_attempts':attempts,'worlds':worlds},indent=2)+'\n')
    protocol={'format':'bpc-stochastic-v20-frozen-protocol','frozen_before_holdout_execution':True,
        'question':'Can a frozen non-neural BPC direct controller identify previously unseen stochastic actuator probability channels jointly with anonymous sensors, nuisance actuators, D4 gauge, and end-to-end lag, then preserve control on disjoint worlds?',
        'config':config,'development_result_sha256':sha(ROOT/'artifacts'/'v20stochastic'/'development.json'),'rejected_attempt_sha256':sha(ROOT/'artifacts'/'v20stochastic'/'rejected_attempt1_noop_nonidentifiable.json'),
        'expected_training_events':events,'expected_factor_digest':learner.digest(),'reference_interface_digest':reference.digest(),'reference_support':support(reference_support),
        'reference_effect_digest':profiles.digest(),'expected_calibration':calibration,'holdout_sha256':sha(HOLDOUT),
        'adoption_thresholds':{'maximum_gauge_channel_total_variation':.12,'maximum_stream_gauge_channel_total_variation':.20,'minimum_oracle_fraction_each_interface':.80,
            'minimum_identity_margin_each_interface':.05,'minimum_shuffled_margin_each_interface':.05},
        'controls':['oracle stochastic channel and physical D4 frame over the same environment','argmax deterministic channel from the learned probabilities',
            'identity stochastic channel using the same learned sensor and spatial gauges','one-slot-shuffled learned probability rows using the same observations',
            'four new stochastic matrices absent from development','four actual non-identity D4 transforms absent as actual transforms in development',
            'total lags 2 and 4 absent from development','three independent unlabeled regimes per interface','two evaluation action/effect seeds',
            'zero model writes and unchanged model digest','disjoint training, calibration, and holdout worlds'],
        'classifier_dev':{'model':'jev-1.13.0','batch_items':16,'selected':'unknown stochastic actuator channel','confidence':.83,
            'role':'development route classification only; absent from inference, training, frozen evaluation, and runtime'},
        'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
        'failure_policy':'Retain failures. Do not replace mechanisms, channels, lag candidates, interfaces, transforms, worlds, seeds, sources, controls, or thresholds after held-out execution.',
        'boundary':'Developer-frozen synthetic evidence, not third-party blind and not AGI. Useful actuator slots mix four supplied physical directions; structurally inactive nuisance slots are a separate no-effect class. Candidate lag 0-4, D4 family, schema, statistics, generators, terminal events, and backward probability channel are supplied. The development deterministic argmax control was stronger and remains a reported control. No neural network, task label, reward, planner, runtime search, classifier runtime, or evaluation learning is used.'}
    PROTOCOL.write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(protocol,indent=2))


if __name__=='__main__':main()
