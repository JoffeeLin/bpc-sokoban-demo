#!/usr/bin/env python3
"""Development-only causal test of active hidden-mode sensing."""
import json,random,time
from collections import Counter
from pathlib import Path

from bpc_active_probe_v27 import active_replacement,advance,change_information
from bpc_composite_binding_v16 import collect_composite_interface
from bpc_context_emission_v26 import context_emission
from bpc_cross_generator_v17 import LabWorld,done,lab_raw,lab_step,variable_expose
from bpc_direct_composition_v09 import choose
from bpc_hidden_mode_v21 import reverse_channel,sample,stationary,update_belief
from bpc_open_interface_v15 import canonicalize_subset
from bpc_spatial_interface_v18 import spatial_expose,spatial_restore
from bpc_three_factor_v12 import FieldPolicy,train
from experiment_v21_hidden_interface_dev import expected_channels
from freeze_v21_hidden import CHANNELS,DELAYS,HOLDOUT,INITIALS,KINDS,PROTOCOL,SENSORS,SPATIAL,TRANSITIONS

ROOT=Path(__file__).resolve().parent;SOURCE=ROOT/'artifacts'/'v26context'/'development.json'


def model(row):
    value=row['context_model'];return {'initial':tuple(value['initial']),'transition':tuple(map(tuple,value['transition'])),
        'channels':tuple(tuple(map(tuple,mode)) for mode in value['channels'])}


def evaluate(learner,context,learned,suite,sensors,kinds,spatial,delay,mapping,transform,environment,oracle,
        transition,initial,seed,episodes=8,steps=128):
    """Active, random-probe, wrong-probe and passive conditions share experience."""
    wrong=tuple(tuple(mode[(slot+1)%4] for slot in range(4)) for mode in learned['channels']);flat=stationary(learned['transition'])
    conditions=('active','random_probe','wrong_probe','predictive_passive','legacy_passive','memoryless','oracle')
    rows={name:Counter() for name in conditions};field=FieldPolicy(learner)
    restore=lambda value:spatial_restore(canonicalize_subset(value,mapping,len(sensors)),6,transform)
    observe=lambda world:spatial_expose(variable_expose(lab_raw(world),sensors,kinds,0),len(sensors),spatial)
    for index,(family,initial_world,_) in enumerate(suite):
        for episode in range(episodes):
            base_seed=seed+index*100000+episode
            for name in conditions:
                action_rng=random.Random(base_seed);probe_rng=random.Random(base_seed+600000007);effect_rng=random.Random(base_seed+700000001);mode_rng=random.Random(base_seed+800000003)
                world=initial_world;mode=sample(initial,mode_rng);belief=flat;queue=[];issued=[]
                for t in range(steps):
                    old=restore(observe(world));task=field.probabilities(old)
                    if name=='oracle':control=advance(tuple(1. if i==mode else 0. for i in range(len(initial))),transition,delay);task_channels=oracle
                    elif name=='legacy_passive':control=belief;task_channels=learned['channels']
                    else:control=advance(belief,learned['transition'],delay);task_channels=learned['channels']
                    task_probability=reverse_channel(task,control,task_channels);base=choose(task_probability,action_rng);slot=base;replaced=False
                    if name in ('active','random_probe','wrong_probe'):
                        information=change_information(control,wrong if name=='wrong_probe' else learned['channels'],context.change.change_probabilities(old))
                        slot,replaced=active_replacement(base,task_probability,information,probe_rng if name=='random_probe' else None)
                        rows[name]['probe_opportunities']+=bool(any(x>information[base]+1e-15 and task_probability[i]+1e-15>=task_probability[base] for i,x in enumerate(information)))
                        rows[name]['probe_replacements']+=replaced
                    issued.append(slot);queue.append(slot)
                    if len(queue)>delay:world=lab_step(world,sample(environment[mode][queue.pop(0)],effect_rng))
                    new=restore(observe(world));success=done(family,initial_world,world)
                    if success:break
                    if name!='memoryless' and t>=delay:_,belief=update_belief(belief,issued[t-delay],context.logs(old,new),learned['transition'],learned['channels'])
                    elif name!='memoryless':belief=advance(belief,learned['transition'])
                    mode=sample(transition[mode],mode_rng)
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
    return {name:dict(row) for name,row in rows.items()}


def main():
    started=time.perf_counter();protocol=json.loads(PROTOCOL.read_text());holdout=json.loads(HOLDOUT.read_text());source=json.loads(SOURCE.read_text());config=protocol['config']
    learner,_=train(config['train_seed']);excluded=set(learner.training_initials)
    _,triples,initials,_=collect_composite_interface(config['reference_seed'],config['reference_worlds_per_family'],config['calibration_steps'],exclude=excluded);excluded|=initials
    context=context_emission(triples);assert context.digest()==source['context_digest']
    suite=[(row['family'],LabWorld(*[row[x] for x in ('h','w','walls','agent','objects','marks','switches','gates')]),row['shortest']) for row in holdout['worlds']]
    conditions={};writes=learner.writes;digest=learner.digest()
    for index,row in enumerate(protocol['expected_calibration']):
        learned=model(source['calibration'][index]);oracle=expected_channels(SPATIAL[index],row['selected_gauge_representative'],CHANNELS[index])
        conditions[str(index)]=evaluate(learner,context,learned,suite,SENSORS[index],KINDS[index],SPATIAL[index],DELAYS[index],tuple(row['sensor_binding']['mapping']),
            row['selected_gauge_representative'],CHANNELS[index],oracle,TRANSITIONS[index],INITIALS[index],221710+index)
    per=[]
    for key,row in conditions.items():per.append({'interface':int(key),'episodes':row['active']['episodes'],'complex_episodes':64,
        **{name:value['successes'] for name,value in row.items()},**{f'{name}_complex':value['joint_successes'] for name,value in row.items()},
        **{f'{name}_probes':value.get('probe_replacements',0) for name,value in row.items()}})
    gates={'each_predictive_passive_at_least_legacy_overall':all(x['predictive_passive']>=x['legacy_passive'] for x in per),
        'each_active_at_least_predictive_passive_overall':all(x['active']>=x['predictive_passive'] for x in per),
        'failed_interface_2_active_beats_predictive_complex_by_5pct':per[2]['active_complex']-per[2]['predictive_passive_complex']>=per[2]['complex_episodes']*.05,
        'each_active_at_least_random_probe_overall':all(x['active']>=x['random_probe'] for x in per),
        'failed_interface_2_active_beats_random_probe_complex_by_5pct':per[2]['active_complex']-per[2]['random_probe_complex']>=per[2]['complex_episodes']*.05,
        'each_active_beats_wrong_probe_complex_by_5pct':all(x['active_complex']-x['wrong_probe_complex']>=x['complex_episodes']*.05 for x in per),
        'active_probe_used_each_interface':all(x['active_probes']>0 for x in per),'evaluation_writes_zero_and_digest_unchanged':learner.writes==writes and learner.digest()==digest}
    result={'development_only':True,'v21_frozen_result_was_non_adopted':True,'source':str(SOURCE.relative_to(ROOT)),
        'mechanism':'predict hidden mode through actuator delay; among actions no less probable under the unchanged BPC task distribution, choose maximum I(mode; raw-change)',
        'conditions':conditions,'diagnostic':{'per_interface':per},'preregistered_gates':gates,'adopt_for_v27_freeze':all(gates.values()),
        'classifier_dev':{'model':'jev-1.13.0','batch_items':10,'selected':'active raw-observation probe under same-experience controls','confidence':.99,'role':'route classification only'},
        'evaluation_writes':learner.writes-writes,'seconds':time.perf_counter()-started,
        'boundary':'Development reuse of observed v0.21 holdout. Probability statistics only; no reward, semantic rule, planner, neural network, classifier runtime, hidden label, or evaluation learning.'}
    destination=ROOT/'artifacts'/'v27active'/'development.json';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
