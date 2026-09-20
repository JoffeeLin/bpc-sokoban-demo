#!/usr/bin/env python3
"""BPC v0.7 development: anonymous bit functions compose across task families."""
from __future__ import annotations

import hashlib,pickle,random
from collections import Counter
from dataclasses import dataclass

ACTIONS=((-1,0),(1,0),(0,-1),(0,1));BITS=4;CELLS=3;WIDTH=BITS*CELLS


@dataclass(frozen=True)
class World:
    h:int;w:int;walls:int;agent:int;objects:int;marks:int


def bit(mask,i):return (mask>>i)&1
def positions(mask):
    while mask:
        low=mask&-mask;yield low.bit_length()-1;mask-=low


def moved(world:World,i:int,action:int,amount:int=1):
    x,y=i%world.w,i//world.w;dx,dy=ACTIONS[action];x+=dx*amount;y+=dy*amount
    return y*world.w+x if 0<=x<world.w and 0<=y<world.h else -1


def token(world:World,i:int,agent=None,objects=None,marks=None):
    if i<0:return 1
    agent=world.agent if agent is None else agent;objects=world.objects if objects is None else objects
    marks=world.marks if marks is None else marks
    return bit(world.walls,i)|(i==agent)<<1|bit(objects,i)<<2|bit(marks,i)<<3


def patch(world:World,action:int,origin=None,agent=None,objects=None,marks=None):
    origin=world.agent if origin is None else origin;agent=world.agent if agent is None else agent
    return tuple(token(world,moved(world,origin,action,k),agent,objects,marks) for k in range(CELLS))


def flatten(tokens):
    return sum(((value>>b)&1)<<(cell*BITS+b) for cell,value in enumerate(tokens) for b in range(BITS))


def unflatten(value):
    return tuple(sum(((value>>(cell*BITS+b))&1)<<b for b in range(BITS)) for cell in range(CELLS))


def truth(world:World,action:int):
    near=moved(world,world.agent,action);objects,marks=world.objects,world.marks
    if near<0 or bit(world.walls,near):return world
    if bit(objects,near):
        far=moved(world,world.agent,action,2)
        if far<0 or bit(world.walls|objects,far):return world
        objects^=(1<<near)|(1<<far)
    marks&=~(1<<near)
    return World(world.h,world.w,world.walls,near,objects,marks)


def random_world(rng:random.Random,family:str):
    h=w=rng.choice((5,6,7));inside=[y*w+x for y in range(1,h-1) for x in range(1,w-1)]
    border={y*w+x for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)}
    inner=set(rng.sample(inside,rng.randrange(0,max(1,len(inside)//7))));free=[i for i in inside if i not in inner]
    n_objects=0 if family=='collect' else rng.choice((1,2,3));n_marks=0 if family=='push' else rng.choice((1,2,3))
    chosen=rng.sample(free,1+n_objects+n_marks);agent=chosen[0]
    objects=sum(1<<i for i in chosen[1:1+n_objects]);marks=sum(1<<i for i in chosen[1+n_objects:])
    return World(h,w,sum(1<<i for i in border|inner),agent,objects,marks)


class CompressedBitWorld:
    """Delete raw input conditions that never change one future output bit."""
    def __init__(self):self.samples={};self.contexts=[];self.rows=[];self.writes=0
    def observe(self,before,after):
        key=flatten(before);value=flatten(after);self.samples.setdefault(key,Counter())[value]+=1;self.writes+=1
    @staticmethod
    def deterministic(samples,active,output):
        seen={}
        for before,afters in samples.items():
            key=sum(((before>>i)&1)<<k for k,i in enumerate(active));values={(after>>output)&1 for after in afters}
            if len(values)!=1:return False
            value=next(iter(values))
            if key in seen and seen[key]!=value:return False
            seen[key]=value
        return True
    def freeze(self):
        self.contexts=[];self.rows=[]
        for output in range(WIDTH):
            active=list(range(WIDTH));changed=True
            while changed:
                changed=False
                for condition in tuple(active):
                    candidate=[x for x in active if x!=condition]
                    if self.deterministic(self.samples,candidate,output):active=candidate;changed=True
            row={}
            for before,afters in self.samples.items():
                key=sum(((before>>i)&1)<<k for k,i in enumerate(active));values={(after>>output)&1 for after in afters}
                if len(values)==1:row[key]=next(iter(values))
            self.contexts.append(tuple(active));self.rows.append(row)
    def predict(self,before):
        before=flatten(before);output=0
        for bit_index,(active,row) in enumerate(zip(self.contexts,self.rows)):
            key=sum(((before>>i)&1)<<k for k,i in enumerate(active))
            if key not in row:return None
            output|=row[key]<<bit_index
        return unflatten(output)
    def digest(self):return hashlib.sha256(pickle.dumps((self.contexts,self.rows),protocol=5)).hexdigest()


class ResidualPrimeWorld:
    """Compose anonymous changes: copy every bit, then apply learned prime residuals."""
    def __init__(self):self.samples={};self.clauses=[];self.writes=0
    def observe(self,before,after):
        before=flatten(before);after=flatten(after)
        self.samples.setdefault(before,set()).add(before^after);self.writes+=1
    def freeze(self):
        self.clauses=[]
        for output in range(WIDTH):
            positive={before for before,residuals in self.samples.items() if any((value>>output)&1 for value in residuals)}
            negative={before for before,residuals in self.samples.items() if any(not ((value>>output)&1) for value in residuals)}
            primes=set()
            for before in positive:
                valid=[]
                for mask in range(1<<WIDTH):
                    if all((before^other)&mask for other in negative):
                        if not any((smaller&mask)==smaller for smaller in valid):valid.append(mask)
                primes.update((mask,before&mask) for mask in valid)
            self.clauses.append(tuple(sorted(primes)))
    def predict(self,before):
        source=flatten(before);output=source
        for bit_index,clauses in enumerate(self.clauses):
            if any(source&mask==value for mask,value in clauses):output^=1<<bit_index
        return unflatten(output)
    def digest(self):return hashlib.sha256(pickle.dumps(self.clauses,protocol=5)).hexdigest()


class FragmentChainWorld(CompressedBitWorld):
    """Gate predicted bit changes by anonymous co-change implications."""
    def __init__(self):super().__init__();self.prerequisites=[]
    def freeze(self):
        super().freeze();residuals=[]
        for before,afters in self.samples.items():
            residuals.extend(before^after for after in afters)
        self.prerequisites=[]
        for output in range(WIDTH):
            positive=[value for value in residuals if (value>>output)&1]
            shared=(1<<WIDTH)-1
            for value in positive:shared&=value
            self.prerequisites.append(shared&~(1<<output) if positive else 0)
    def predict(self,before):
        predicted=super().predict(before)
        if predicted is None:return None
        source=flatten(before);residual=source^flatten(predicted)
        while True:
            gated=residual
            for output,required in enumerate(self.prerequisites):
                if (gated>>output)&1 and required&gated!=required:gated&=~(1<<output)
            if gated==residual:break
            residual=gated
        return unflatten(source^residual)
    def digest(self):return hashlib.sha256(pickle.dumps((self.contexts,self.rows,self.prerequisites),protocol=5)).hexdigest()


class FullContextWorld:
    def __init__(self):self.rows={};self.writes=0
    def observe(self,before,after):self.rows.setdefault(tuple(before),Counter())[tuple(after)]+=1;self.writes+=1
    def freeze(self):pass
    def predict(self,before):
        row=self.rows.get(tuple(before));return max(row,key=lambda x:(row[x],x)) if row else None


def train(seed:int,episodes:int,steps:int):
    rng=random.Random(seed);compressed=CompressedBitWorld();residual=ResidualPrimeWorld();fragments=FragmentChainWorld();full=FullContextWorld();events=Counter()
    for family in ('push','collect'):
        for _ in range(episodes):
            world=random_world(rng,family)
            for _ in range(steps):
                action=rng.randrange(4);before=patch(world,action);next_world=truth(world,action)
                after=patch(next_world,action,origin=world.agent)
                compressed.observe(before,after);residual.observe(before,after);fragments.observe(before,after);full.observe(before,after)
                events[family]+=1;events[f'{family}_changed']+=next_world!=world
                events['composition_inputs']+=any(value&4 for value in before) and any(value&8 for value in before)
                world=next_world
    compressed.freeze();residual.freeze();fragments.freeze();full.freeze();return compressed,residual,fragments,full,dict(events)


def evaluate(models:dict,seed:int,episodes:int,steps:int,family:str='combined'):
    rng=random.Random(seed);result={name:Counter() for name in models}
    for _ in range(episodes):
        world=random_world(rng,family)
        for _ in range(steps):
            action=rng.randrange(4);before=patch(world,action);next_world=truth(world,action)
            after=patch(next_world,action,origin=world.agent)
            composition=any(value&4 for value in before) and any(value&8 for value in before)
            for name,model in models.items():
                predicted=model.predict(before);row=result[name];row['total']+=1;row['known']+=predicted is not None;row['correct']+=predicted==after
                if composition:
                    row['composition_total']+=1;row['composition_known']+=predicted is not None;row['composition_correct']+=predicted==after
            world=next_world
    return {name:dict(row) for name,row in result.items()}
