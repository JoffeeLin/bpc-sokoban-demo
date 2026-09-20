#!/usr/bin/env python3
"""BPC v0.12 development: three anonymous mechanisms in one evidence field."""
from __future__ import annotations

import hashlib,math,pickle,random
from collections import Counter,deque
from dataclasses import dataclass

from bpc_cross_task_v07 import ACTIONS,bit
from bpc_direct_composition_v09 import choose
from bpc_evidence_field_v11 import components,normalize
from experiment_v5 import erase_zero_effect_cycles
from general_bpc_v7 import RelationalBPC,RelationalEncoder

SIZE=7;CHANNELS=6


@dataclass(frozen=True)
class World3:
    h:int;w:int;walls:int;agent:int;objects:int;marks:int;switches:int;gates:int


def moved(world,i,action,amount=1):
    x,y=i%world.w,i//world.w;dx,dy=ACTIONS[action];x+=dx*amount;y+=dy*amount
    return y*world.w+x if 0<=x<world.w and 0<=y<world.h else -1


def step(world,action,fixed_objects=False,fixed_gates=False):
    near=moved(world,world.agent,action);objects,marks,switches,gates=world.objects,world.marks,world.switches,world.gates
    if near<0 or bit(world.walls|gates,near):return world
    if bit(objects,near):
        if fixed_objects:return world
        far=moved(world,world.agent,action,2)
        if far<0 or bit(world.walls|objects|gates,far):return world
        objects^=(1<<near)|(1<<far)
    marks&=~(1<<near)
    if bit(switches,near):
        switches&=~(1<<near)
        if not fixed_gates:gates=0
    return World3(world.h,world.w,world.walls,near,objects,marks,switches,gates)


def raw(world):
    values=[]
    for y in range(SIZE):
        for x in range(SIZE):
            inside=x<world.w and y<world.h;i=y*world.w+x if inside else -1
            values.extend((int(not inside or bit(world.walls,i)),int(inside and i==world.agent),
                int(inside and bit(world.objects,i)),int(inside and bit(world.marks,i)),
                int(inside and bit(world.switches,i)),int(inside and bit(world.gates,i))))
    return bytes(values)


def changed_planes(before,after):
    return tuple(c for c in range(CHANNELS) if any(before[i+c]!=after[i+c] for i in range(0,len(before),CHANNELS)))


def new_cube():return RelationalBPC(RelationalEncoder(SIZE,SIZE,CHANNELS,radius=2,rarity=3))


class ThreeFactorBPC:
    """Discover terminal co-change factors and query their union additively."""
    def __init__(self):self.factors={};self.shared=new_cube();self.successes=Counter();self.writes=0;self.training_initials=set()
    def observe_success(self,trace):
        signature=changed_planes(trace[-1][0],trace[-1][2]);factor=self.factors.setdefault(signature,new_cube())
        compact=erase_zero_effect_cycles(trace);factor.observe_success(compact);self.shared.observe_success(compact)
        self.successes[signature]+=1;self.writes+=len(compact);return signature,len(compact)
    def common_planes(self):
        rows=list(self.factors);return set.intersection(*(set(x) for x in rows)) if rows else set()
    def required_planes(self):
        common=self.common_planes();return {key:tuple(x for x in key if x not in common) for key in self.factors}
    @staticmethod
    def present(state):return {c for c in range(CHANNELS) if any(state[i+c] for i in range(0,len(state),CHANNELS))}
    def active(self,state):
        present=self.present(state);return tuple(key for key,row in sorted(self.required_planes().items()) if all(x in present for x in row))
    def digest(self):
        rows=tuple((key,cube.digest()) for key,cube in sorted(self.factors.items()))
        return hashlib.sha256(pickle.dumps((rows,self.successes),protocol=5)).hexdigest()


class FieldPolicy:
    def __init__(self,learner,rotated=False,drop=()):
        self.learner=learner
        ordered=tuple(sorted(learner.factors))
        # Freeze ablations to global anonymous signatures, not shifting active positions.
        self.drop={ordered[i] for i in drop if 0<=i<len(ordered)}
        self.sources={key:(cube.rotated() if rotated else cube) for key,cube in learner.factors.items()}
    def probabilities(self,state):
        active=tuple(key for key in self.learner.active(state) if key not in self.drop)
        if not active:return [.25]*4
        counts=[0]*4;rows=[]
        for key in active:
            source=self.sources[key];rows.append(components(source,state))
            for action,value in enumerate(source.success_prior):counts[action]+=value
        total=sum(counts);prior=[(x+1)/(total+4) for x in counts]
        evidence=[sum(row[1][a] for row in rows) for a in range(4)]
        return normalize([.12*math.log(prior[a])+evidence[a] for a in range(4)])


class ProductPolicy:
    def __init__(self,learner):self.learner=learner
    def probabilities(self,state):
        active=self.learner.active(state);values=[1.]*4
        if not active:return [.25]*4
        for key in active:
            row=self.learner.factors[key].probabilities(state)
            for action in range(4):values[action]*=row[action]
        total=sum(values);return [x/total for x in values]


class SharedPolicy:
    def __init__(self,learner):self.learner=learner
    def probabilities(self,state):return self.learner.shared.probabilities(state)


class UniformPolicy:
    def probabilities(self,state):return [.25]*4


def key(world):return (world.h,world.w,world.walls,world.agent,world.objects,world.marks,world.switches,world.gates)


def random_world(rng,family):
    h=w=rng.choice((5,6,7));inside=[y*w+x for y in range(1,h-1) for x in range(1,w-1)]
    border={y*w+x for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)}
    inner=set(rng.sample(inside,rng.randrange(0,max(1,len(inside)//8))));free=[i for i in inside if i not in inner]
    counts={'push':(rng.choice((1,2,3)),0,0,rng.choice((0,0,1))),
            'collect':(0,rng.choice((1,2,3)),0,0),'open':(0,0,1,rng.choice((1,2,3)))}[family]
    n_objects,n_marks,n_switches,n_gates=counts;chosen=rng.sample(free,1+sum(counts));p=1
    agent=chosen[0];objects=sum(1<<i for i in chosen[p:p+n_objects]);p+=n_objects
    marks=sum(1<<i for i in chosen[p:p+n_marks]);p+=n_marks
    switches=sum(1<<i for i in chosen[p:p+n_switches]);p+=n_switches;gates=sum(1<<i for i in chosen[p:p+n_gates])
    return World3(h,w,sum(1<<i for i in border|inner),agent,objects,marks,switches,gates)


def succeeded(family,initial,world):
    return world.objects!=initial.objects if family=='push' else world.marks==0 if family=='collect' else world.gates==0


def train(seed,uniform_episodes=800,guided_rounds=2,guided_episodes=400,steps=120):
    rng=random.Random(seed);learner=ThreeFactorBPC();events=Counter();schedule=[False]*uniform_episodes
    for _ in range(guided_rounds):schedule.extend([True]*guided_episodes)
    for family in ('push','collect','open'):
        for guided in schedule:
            world=random_world(rng,family);initial=world;trace=[];learner.training_initials.add(key(world))
            for _ in range(steps):
                before=raw(world);probability=FieldPolicy(learner).probabilities(before)
                action=choose(probability,rng) if guided and rng.random()>.25 else rng.randrange(4)
                nxt=step(world,action);trace.append((before,action,raw(nxt)));world=nxt
                if succeeded(family,initial,world):
                    signature,length=learner.observe_success(trace);events[f'{family}_success']+=1
                    events[f'{family}_compact_steps']+=length;events[f'signature_{signature}']+=1;break
            events[f'{family}_episodes']+=1
    return learner,dict(events)


def shortest(world,goal,fixed_objects=False,fixed_gates=False,limit=200000):
    initial=world;queue=deque([(world,0)]);seen={key(world)}
    while queue:
        state,distance=queue.popleft()
        done=state.objects!=initial.objects if goal=='push' else state.marks==0 if goal=='collect' else state.gates==0
        if done:return distance
        for action in range(4):
            nxt=step(state,action,fixed_objects,fixed_gates);identity=key(nxt)
            if identity not in seen:
                seen.add(identity)
                if len(seen)>limit:return None
                queue.append((nxt,distance+1))
    return None


def combined_candidate(rng):
    w=h=7;door_y=rng.choice((2,3,4));border={(x,y) for y in range(h) for x in range(w) if x in (0,6) or y in (0,6)}
    vertical=rng.random()<.5
    if vertical:
        barrier={(3,y) for y in range(1,6) if y!=door_y};gate=(3,door_y);box=(4,door_y);far=(5,door_y)
        left=[(x,y) for y in range(1,6) for x in (1,2)];right=[(x,y) for y in range(1,6) for x in (4,5) if (x,y)!=box and (x,y)!=far]
    else:
        barrier={(x,3) for x in range(1,6) if x!=door_y};gate=(door_y,3);box=(door_y,4);far=(door_y,5)
        left=[(x,y) for x in range(1,6) for y in (1,2)];right=[(x,y) for x in range(1,6) for y in (4,5) if (x,y)!=box and (x,y)!=far]
    agent,switch=rng.sample(left,2);mark=rng.choice(right);reserved={agent,switch,gate,box,far,mark}
    candidates=[p for p in left+right if p not in reserved];extra=set(rng.sample(candidates,rng.randrange(0,min(4,len(candidates)+1))))
    if rng.random()<.5:
        transform=lambda p:(6-p[0],p[1])
    else:transform=lambda p:p
    points=[transform(p) for p in (agent,switch,gate,box,mark)];agent,switch,gate,box,mark=points
    walls={transform(p) for p in border|barrier|extra};idx=lambda p:p[1]*w+p[0]
    return World3(h,w,sum(1<<idx(p) for p in walls),idx(agent),1<<idx(box),1<<idx(mark),1<<idx(switch),1<<idx(gate))


def generate_suite(seed,count,exclude=()):
    rng=random.Random(seed);exclude=set(exclude);out=[];attempts=Counter()
    for family,goal in (('push','push'),('collect','collect'),('open','open')):
        seen=set()
        while len(seen)<count and attempts[family]<100000:
            attempts[family]+=1;world=random_world(rng,family);distance=shortest(world,goal);identity=key(world)
            if distance is not None and 2<=distance<=24 and identity not in seen and identity not in exclude:
                seen.add(identity);out.append((family,world,distance))
        if len(seen)<count:raise RuntimeError(f'not enough {family} worlds')
    seen=set()
    while len(seen)<count and attempts['joint']<100000:
        attempts['joint']+=1;world=combined_candidate(rng);distance=shortest(world,'collect');identity=key(world)
        if distance is not None and shortest(world,'collect',fixed_objects=True) is None and shortest(world,'collect',fixed_gates=True) is None and identity not in seen:
            seen.add(identity);out.append(('joint',world,distance))
    if len(seen)<count:raise RuntimeError(f'not enough joint worlds after {attempts["joint"]}')
    return out,dict(attempts)


def evaluate(policies,suite,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;path=[]
                for _ in range(steps):
                    state=raw(world);cache_key=(name,state)
                    if cache_key not in cache:cache[cache_key]=policy.probabilities(state)
                    action=choose(cache[cache_key],rng);path.append(action);world=step(world,action)
                    success=succeeded(family,initial,world) if family!='joint' else world.marks==0
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces
