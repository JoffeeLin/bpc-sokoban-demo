#!/usr/bin/env python3
"""BPC v0.35: marginalize factor-specific state/temporal posteriors."""
from bpc_three_factor_v12 import FieldPolicy


def norm(values):
    total=sum(values);return [value/total for value in values] if total else [.25]*4


class ResponsibilityPolicy:
    def __init__(self,learner,temporal,drop=(),shuffle_factor=0,state_only=False,temporal_only=False,joint_only=False,rotated=False):
        self.learner=learner;self.temporal=temporal;self.base=FieldPolicy(learner,rotated,drop);self.ordered=tuple(sorted(learner.factors));self.drop={self.ordered[i] for i in drop if 0<=i<len(self.ordered)}
        self.sources=self.base.sources;self.shuffle_factor=shuffle_factor;self.state_only=state_only;self.temporal_only=temporal_only;self.joint_only=joint_only;self.previous=None
    def reset(self):self.previous=None
    def probabilities(self,state):
        base=self.base.probabilities(state);active=tuple(signature for signature in self.learner.active(state) if signature not in self.drop)
        if self.previous is None or len(active)<2:return base
        marginal=[0.]*4
        for signature in active:
            index=self.ordered.index(signature);paired=self.ordered[(index+self.shuffle_factor)%len(self.ordered)]
            spatial=self.sources[signature].probabilities(state);time=self.temporal.probabilities((paired,),self.previous) or [.25]*4
            expert=spatial if self.state_only else time if self.temporal_only else norm([spatial[action]*time[action] for action in range(4)])
            for action in range(4):marginal[action]+=expert[action]
        marginal=norm(marginal)
        return marginal if self.joint_only else norm([base[action]*marginal[action] for action in range(4)])
    def chose(self,action):self.previous=action
