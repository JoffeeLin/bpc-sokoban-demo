#!/usr/bin/env python3
"""Task-agnostic BPC typed-decision kernel using exact probability counts.

The caller supplies anonymous, hashable features and external action indices.
The kernel contains no game rules, semantic labels, planner, optimizer, neural
network, or task-specific reward score.
"""
from __future__ import annotations

import hashlib, math, pickle
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Hashable, Iterable


@dataclass(frozen=True)
class Decision:
    choice: tuple[float,...]
    confidence: float
    defer: bool
    channels: dict[str,tuple[float,...]]


class GeneralBPC:
    """Shared sparse feature × action probability cubes.

    `encoder` maps raw input to hashable tuples whose first element identifies
    an anonymous feature family.  Family normalization prevents a prolific
    family from winning merely by emitting more addresses.
    """
    def __init__(self,actions:int,encoder:Callable[[object],Iterable[tuple]],defer_below:float=0.):
        if actions<2: raise ValueError('actions must be >=2')
        self.actions=actions; self.encoder=encoder; self.defer_below=defer_below
        self.choice=defaultdict(lambda:[0]*actions); self.prior=[0]*actions
        self.binary:dict[str,dict[Hashable,list[int]]]={}
        self.binary_prior:dict[str,list[list[int]]]={}
        self.writes=0

    def observe_success(self,path:Iterable[tuple[object,int]])->None:
        for raw,action in path:
            for feature in self.encoder(raw): self.choice[feature][action]+=1
            self.prior[action]+=1; self.writes+=1

    def observe_binary(self,name:str,raw:object,action:int,outcome:bool)->None:
        cube=self.binary.setdefault(name,{})
        prior=self.binary_prior.setdefault(name,[[0,0] for _ in range(self.actions)])
        prior[action][int(outcome)]+=1; self.writes+=1
        for feature in self.encoder(raw):
            row=cube.setdefault(feature,[0]*(2*self.actions))
            row[action]+=int(outcome); row[self.actions+action]+=1; self.writes+=1

    def _choice(self,raw:object,temperature:float,families:set[int]|None)->tuple[float,...]:
        grouped:dict[int,list[list[int]]]=defaultdict(list)
        for feature in self.encoder(raw):
            if families is not None and feature[0] not in families: continue
            row=self.choice.get(feature)
            if row is not None: grouped[feature[0]].append(row)
        total=sum(self.prior); logits=[.12*math.log((x+1)/(total+self.actions)) for x in self.prior]
        family_logits=[]
        for rows in grouped.values():
            local=[0.]*self.actions; support=0.
            for row in rows:
                n=sum(row)
                if n<3: continue
                reliability=min(4.,math.log1p(n)); support+=reliability
                for action in range(self.actions):
                    local[action]+=reliability*math.log((row[action]+1)/(n+self.actions))
            if support: family_logits.append([x/support for x in local])
        if family_logits:
            for action in range(self.actions):
                logits[action]+=sum(x[action] for x in family_logits)/len(family_logits)
        peak=max(logits); values=[math.exp((x-peak)/temperature) for x in logits]; z=sum(values)
        return tuple(x/z for x in values)

    def channel(self,name:str,raw:object)->tuple[float,...]:
        cube=self.binary.get(name,{}); prior=self.binary_prior.get(name,[[0,0] for _ in range(self.actions)])
        features=tuple(self.encoder(raw)); output=[]
        for action in range(self.actions):
            no,yes=prior[action]; logs=[math.log((yes+1)/(yes+no+2))]
            for feature in features:
                row=cube.get(feature)
                if row is not None and row[self.actions+action]:
                    logs.append(math.log((row[action]+1)/(row[self.actions+action]+2)))
            output.append(math.exp(sum(logs)/len(logs)))
        return tuple(output)

    def decide(self,raw:object,temperature:float=.72,families:set[int]|None=None)->Decision:
        probability=self._choice(raw,temperature,families)
        entropy=-sum(p*math.log(p) for p in probability if p)
        confidence=1-entropy/math.log(self.actions)
        channels={name:self.channel(name,raw) for name in self.binary}
        return Decision(probability,confidence,confidence<self.defer_below,channels)

    def digest(self)->str:
        choice=sorted(((repr(k),tuple(v)) for k,v in self.choice.items()))
        binary={name:sorted((repr(k),tuple(v)) for k,v in cube.items()) for name,cube in self.binary.items()}
        return hashlib.sha256(pickle.dumps((self.actions,choice,self.prior,binary,self.binary_prior),protocol=5)).hexdigest()
