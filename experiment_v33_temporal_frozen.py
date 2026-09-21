#!/usr/bin/env python3
"""First and repeated execution of the frozen v0.33 temporal-policy holdout."""
import hashlib,json,random,time
from collections import Counter
from pathlib import Path

from bpc_direct_composition_v09 import choose
from bpc_fourth_factor_v28 import step as joint_step
from bpc_temporal_policy_v32 import TemporalPolicy,train
from bpc_three_factor_v12 import FieldPolicy,UniformPolicy,World3,raw,step as old_step,succeeded

ROOT=Path(__file__).resolve().parent;HOLDOUT=ROOT/'holdout_v33_temporal.json';PROTOCOL=ROOT/'protocol_v33_temporal.json';RESULT=ROOT/'artifacts'/'v33temporal'/'result.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def world(row):return World3(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')])
def suite(rows):return [(row['family'],world(row),row['shortest']) for row in rows]


def policies(learner,temporal):
    out={'temporal':TemporalPolicy(learner,temporal),'field':FieldPolicy(learner),'shuffled_history':TemporalPolicy(learner,temporal,shuffle=1),
        'order_zero':TemporalPolicy(learner,temporal,order0=True),'rotated':TemporalPolicy(learner,temporal,rotated=True),'uniform':UniformPolicy()}
    for index,signature in enumerate(sorted(learner.factors)):out[f'delete_{index}_{signature}']=TemporalPolicy(learner,temporal,drop=(index,))
    return out


def evaluate(learner,temporal,worlds,seed,episodes,steps,joint):
    rows={name:Counter() for name in policies(learner,temporal)};traces={};models=policies(learner,temporal)
    for index,(family,initial,_) in enumerate(worlds):
        for episode in range(episodes):
            for name,policy in models.items():
                if hasattr(policy,'reset'):policy.reset()
                rng=random.Random(seed+index*100000+episode);state=initial;path=[]
                for _ in range(steps):
                    action=choose(policy.probabilities(raw(state)),rng);path.append(action)
                    if hasattr(policy,'chose'):policy.chose(action)
                    state=joint_step(state,action) if joint else old_step(state,action)
                    success=state.marks==0 if joint else succeeded(family,initial,state) if family!='joint' else state.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success;row[f'map_{index}_successes']+=success
                if name=='temporal' and success and index not in traces:traces[index]=path
    return {name:dict(value) for name,value in rows.items()},{str(key):value for key,value in traces.items()}


def bundle(learner,temporal,holdout,config):
    new=[];old=[];traces=[]
    for seed in config['evaluation_seeds']:
        rows,path=evaluate(learner,temporal,suite(holdout['worlds']),seed,config['episodes_per_world_per_seed'],config['step_budget'],True);new.append({'seed':seed,'conditions':rows});traces.append({'seed':seed,'paths':path})
    for seed in config['old_evaluation_seeds']:
        rows,_=evaluate(learner,temporal,suite(holdout['old_worlds']),seed,config['old_episodes_per_world_per_seed'],config['old_step_budget'],False);old.append({'seed':seed,'conditions':rows})
    return {'new':new,'old_retention':old,'traces':traces}


def aggregate(rows):
    out={}
    for item in rows:
        for name,row in item['conditions'].items():
            target=out.setdefault(name,Counter())
            for key,value in row.items():target[key]+=value
    return {name:dict(value) for name,value in out.items()}


def main():
    started=time.perf_counter();protocol=json.loads(PROTOCOL.read_text());holdout=json.loads(HOLDOUT.read_text());config=protocol['config']
    assert sha(HOLDOUT)==protocol['holdout_sha256'] and sha(ROOT/'artifacts'/'v32temporal'/'development.json')==protocol['development_result_sha256']
    assert all(sha(ROOT/name)==value for name,value in protocol['source_sha256'].items())
    learner,temporal,events=train(config['train_seed']);assert learner.digest()==config['expected_factor_digest'] and temporal.digest()==config['expected_temporal_digest'] and events==config['expected_training_events']
    writes=(learner.writes,temporal.writes);digests=(learner.digest(),temporal.digest());first=bundle(learner,temporal,holdout,config);second=bundle(learner,temporal,holdout,config);repeat=first==second
    combined=aggregate(first['new']);old=aggregate(first['old_retention']);total=combined['temporal']['episodes'];deletions=[name for name in combined if name.startswith('delete_')]
    thresholds=protocol['adoption_thresholds'];per_seed=[row['conditions'] for row in first['new']];old_seed=[row['conditions'] for row in first['old_retention']]
    gates={'source_and_holdout_hashes_exact':True,'model_digests_and_training_events_exact':True,
        'actual_training_object_mark_overlap_zero':not any(row[4] and row[5] for row in learner.training_initials),
        'aggregate_temporal_success_at_least_75pct':combined['temporal']['successes']>=total*thresholds['minimum_aggregate_temporal_success_rate'],
        'each_seed_temporal_success_at_least_70pct':all(row['temporal']['successes']>=row['temporal']['episodes']*thresholds['minimum_each_seed_temporal_success_rate'] for row in per_seed),
        'every_world_has_at_least_4_temporal_successes':all(combined['temporal'].get(f'map_{i}_successes',0)>=thresholds['minimum_successes_each_world'] for i in range(config['worlds'])),
        'aggregate_temporal_beats_field_by_5pct':combined['temporal']['successes']-combined['field']['successes']>=total*thresholds['minimum_aggregate_field_margin'],
        'each_seed_temporal_beats_field_by_3pct':all(row['temporal']['successes']-row['field']['successes']>=row['temporal']['episodes']*thresholds['minimum_each_seed_field_margin'] for row in per_seed),
        'temporal_beats_shuffled_and_order_zero_by_5pct':all(combined['temporal']['successes']-combined[name]['successes']>=total*thresholds['minimum_shuffled_and_order_zero_margin'] for name in ('shuffled_history','order_zero')),
        'temporal_beats_each_factor_deletion_by_10pct':all(combined['temporal']['successes']-combined[name]['successes']>=total*thresholds['minimum_each_factor_deletion_margin'] for name in deletions),
        'temporal_beats_uniform_and_rotated_by_30pct':all(combined['temporal']['successes']-combined[name]['successes']>=total*thresholds['minimum_uniform_and_rotated_margin'] for name in ('uniform','rotated')),
        'retains_95pct_of_field_each_old_family_and_seed':all(row['temporal'].get(f'{family}_successes',0)>=row['field'].get(f'{family}_successes',0)*thresholds['minimum_old_family_retention_fraction'] for row in old_seed for family in ('push','collect','open','joint')),
        'deterministic_repeat_exact':repeat,'evaluation_writes_zero_and_digests_unchanged':(learner.writes,temporal.writes)==writes and (learner.digest(),temporal.digest())==digests}
    result={'format':'bpc-temporal-v33-frozen-result','evidence_level':'developer-frozen independent-generator holdout','question':protocol['question'],'config':config,
        'factor_digest':learner.digest(),'temporal_digest':temporal.digest(),'holdout':{'sha256':sha(HOLDOUT),'worlds':len(holdout['worlds']),'maximum_internal_wall_jaccard':holdout['maximum_internal_wall_jaccard']},
        'per_seed':first['new'],'aggregate':combined,'old_retention_per_seed':first['old_retention'],'old_retention_aggregate':old,'first_success_traces':first['traces'],
        'gates':gates,'adopted':all(gates.values()),'repeat_exact':repeat,'evaluation_writes':{'factor':learner.writes-writes[0],'temporal':temporal.writes-writes[1]},
        'protocol_sha256':sha(PROTOCOL),'source_sha256':protocol['source_sha256'],'classifier_dev':protocol['classifier_dev'],'seconds':time.perf_counter()-started,
        'supported_claim':'Only if adopted: bounded zero-shot temporal composition across a new raw interaction and independent generator, with unchanged separate-factor experience.',
        'boundary':protocol['boundary']}
    RESULT.parent.mkdir(parents=True,exist_ok=True);RESULT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
