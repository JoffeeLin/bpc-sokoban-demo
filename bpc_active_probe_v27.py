#!/usr/bin/env python3
"""BPC v0.27: probability-only active sensing of a hidden actuator mode."""
import math


def advance(belief,transition,steps=1):
    """Predict the mode at delayed action execution, without a persistent write."""
    for _ in range(steps):belief=tuple(sum(belief[i]*transition[i][j] for i in range(len(belief))) for j in range(len(belief)))
    return belief


def _binary_entropy(p):
    return -sum(x*math.log2(x) for x in (p,1-p) if x>0)


def change_information(belief,channels,physical_change):
    """I(hidden mode; next raw-change bit) for every anonymous issued slot."""
    out=[]
    for slot in range(len(channels[0])):
        by_mode=[sum(mode[slot][action]*physical_change[action] for action in range(len(physical_change))) for mode in channels]
        marginal=sum(weight*p for weight,p in zip(belief,by_mode))
        out.append(max(0.,_binary_entropy(marginal)-sum(weight*_binary_entropy(p) for weight,p in zip(belief,by_mode))))
    return tuple(out)


def active_replacement(base,task_probability,information,random_source=None):
    """Replace only with an action no less probable under the unchanged task policy."""
    eligible=[slot for slot,p in enumerate(task_probability) if p+1e-15>=task_probability[base] and information[slot]>information[base]+1e-15]
    if not eligible:return base,False
    if random_source is not None:return eligible[random_source.randrange(len(eligible))],True
    return max(eligible,key=lambda slot:(information[slot],task_probability[slot],-slot)),True
