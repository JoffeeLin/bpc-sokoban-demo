#!/usr/bin/env python3
"""BPC v0.26: raw-relational context conditioned transition emissions."""
import hashlib,math,pickle
from collections import Counter

from bpc_cross_task_v07 import ACTIONS
from bpc_spatial_interface_v18 import spatial_expose,transformed_delta
from bpc_stochastic_interface_v20 import effect_features
from general_bpc_v7 import RelationalBPC,RelationalEncoder


class ChangedEffectProfiles:
    """Joint effect probability conditioned on an observed frame change."""
    def __init__(self,actions=4,prior=.5):self.actions=actions;self.prior=prior;self.n=[0]*actions;self.rows=[Counter() for _ in range(actions)]
    def observe(self,before,action,after):
        if before!=after:self.n[action]+=1;self.rows[action][effect_features(before,after)]+=1
    def logs(self,before,after):
        if before==after:return (0.,)*self.actions
        value=effect_features(before,after);return tuple(math.log((row[value]+self.prior)/(self.n[a]+self.prior*(len(row)+1))) for a,row in enumerate(self.rows))


class ContextEmission:
    """P(change|anonymous raw relations, action) times P(effect|change,action)."""
    def __init__(self):self.change=RelationalBPC(RelationalEncoder(7,7,6,radius=2,rarity=3));self.effect=ChangedEffectProfiles()
    def observe(self,before,action,after):self.change.observe_transition(before,action,before!=after);self.effect.observe(before,action,after)
    def logs(self,before,after):
        changed=before!=after;probability=self.change.change_probabilities(before);conditional=self.effect.logs(before,after)
        return tuple(math.log(max(p if changed else 1-p,1e-300))+conditional[a] for a,p in enumerate(probability))
    def digest(self):
        rows=(self.change.digest(),tuple(self.effect.n),tuple(tuple(sorted(x.items())) for x in self.effect.rows))
        return hashlib.sha256(pickle.dumps(rows,protocol=5)).hexdigest()


def context_emission(triples):
    """D4-shared unlabeled reference transition probabilities."""
    out=ContextEmission()
    for index,(before,action,after) in enumerate(triples):
        for transform in range(8):
            delta=transformed_delta(transform,action);mapped=ACTIONS.index(delta)
            out.observe(spatial_expose(before,6,transform),mapped,spatial_expose(after,6,transform))
        if index%64==0:out.change.encoder.cache.clear()
    out.change.encoder.cache.clear();return out
