#!/usr/bin/env python3
"""BPC v0.31: arithmetic mixture of independent anonymous factor posteriors."""


class MixturePolicy:
    def __init__(self,learner,rotated=False,drop=()):
        self.learner=learner;ordered=tuple(sorted(learner.factors));self.drop={ordered[i] for i in drop if 0<=i<len(ordered)}
        self.sources={key:(cube.rotated() if rotated else cube) for key,cube in learner.factors.items()}

    def probabilities(self,state):
        active=tuple(key for key in self.learner.active(state) if key not in self.drop)
        if not active:return [.25]*4
        rows=[self.sources[key].probabilities(state) for key in active]
        return [sum(row[action] for row in rows)/len(rows) for action in range(4)]
