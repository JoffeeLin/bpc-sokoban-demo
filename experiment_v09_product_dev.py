#!/usr/bin/env python3
"""Development ablation: independent specialist probability composition."""
import json,pickle,time
from pathlib import Path

from bpc_direct_composition_v09 import ProductPolicy,evaluate

ROOT=Path(__file__).resolve().parent;SOURCE=ROOT/'artifacts'/'v09direct'/'development_models.pkl'


def main():
    started=time.perf_counter()
    with SOURCE.open('rb') as file:shared,specialists,holdout=pickle.load(file)
    product=ProductPolicy(specialists['push'],specialists['collect'])
    models={'shared':shared,'product':product,'collect_only':specialists['collect'],'push_only':specialists['push'],
            'rotated':product,'uniform':shared}
    conditions={}
    for steps in (32,160):conditions[str(steps)]=evaluate(models,holdout,99_109,64,steps)[0]
    output={'development_only':True,'reused_training_and_maps':True,'mechanism':'equal product of independent specialist Choice probabilities',
            'conditions_by_step_budget':conditions,'seconds':time.perf_counter()-started,
            'boundary':'Same exposed development maps; no frozen claim. Probability composition only, not learned task routing.'}
    destination=ROOT/'artifacts'/'v09direct'/'product_development.json';destination.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
