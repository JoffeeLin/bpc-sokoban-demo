#!/usr/bin/env python3
"""BPC v0.17 development: variable I/O binding across an independent world generator."""
from __future__ import annotations

import itertools,math,random
from collections import Counter,deque
from dataclasses import dataclass

from bpc_composite_binding_v16 import projected_support
from bpc_channel_binding_v13 import log_categorical
from bpc_direct_composition_v09 import choose
from bpc_open_interface_v15 import CELLS,OpenBoundPolicy,OpenInterfaceStats,sensor_log_probability
from bpc_three_factor_v12 import CHANNELS,key

LAB_MOVES=((-1,0),(1,0),(0,-1),(0,1))


@dataclass(frozen=True)
class LabWorld:
    h:int;w:int;walls:int;agent:int;objects:int;marks:int;switches:int;gates:int


def has(mask,index):return index>=0 and bool(mask&(1<<index))


def lab_step(world,action,fixed_objects=False,fixed_gates=False):
    """Independent coordinate implementation of the four canonical effects."""
    dx,dy=LAB_MOVES[action];x,y=world.agent%world.w,world.agent//world.w;nx,ny=x+dx,y+dy
    if not (0<=nx<world.w and 0<=ny<world.h):return world
    near=ny*world.w+nx
    if has(world.walls|world.gates,near):return world
    objects=world.objects
    if has(objects,near):
        if fixed_objects:return world
        fx,fy=nx+dx,ny+dy
        if not (0<=fx<world.w and 0<=fy<world.h):return world
        far=fy*world.w+fx
        if has(world.walls|world.gates|objects,far):return world
        objects=(objects&~(1<<near))|(1<<far)
    marks=world.marks&~(1<<near);switches=world.switches;gates=world.gates
    if has(switches,near):
        switches&=~(1<<near)
        if not fixed_gates:gates=0
    return LabWorld(world.h,world.w,world.walls,near,objects,marks,switches,gates)


def lab_raw(world):
    out=bytearray()
    for y in range(7):
        for x in range(7):
            inside=x<world.w and y<world.h;i=y*world.w+x if inside else -1
            out.extend((int(not inside or has(world.walls,i)),int(inside and i==world.agent),
                int(inside and has(world.objects,i)),int(inside and has(world.marks,i)),
                int(inside and has(world.switches,i)),int(inside and has(world.gates,i))))
    return bytes(out)


def lab_world(rng,family):
    """Rectangular distribution implemented without the training generator."""
    h,w=rng.choice((5,6,7)),rng.choice((5,6,7));inside=[y*w+x for y in range(1,h-1) for x in range(1,w-1)]
    border={y*w+x for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)}
    inner=set(rng.sample(inside,rng.randrange(0,max(1,len(inside)//6))));free=[i for i in inside if i not in inner]
    counts={'push':(rng.randint(1,3),0,0,0),'collect':(0,rng.randint(1,3),0,0),'open':(0,0,1,rng.randint(1,3))}[family]
    chosen=rng.sample(free,1+sum(counts));p=1;agent=chosen[0];nobj,nmark,nswitch,ngate=counts
    objects=sum(1<<i for i in chosen[p:p+nobj]);p+=nobj;marks=sum(1<<i for i in chosen[p:p+nmark]);p+=nmark
    switches=sum(1<<i for i in chosen[p:p+nswitch]);p+=nswitch;gates=sum(1<<i for i in chosen[p:p+ngate])
    return LabWorld(h,w,sum(1<<i for i in border|inner),agent,objects,marks,switches,gates)


def done(family,initial,world):return world.objects!=initial.objects if family=='push' else world.marks==0 if family in ('collect','joint') else world.gates==0


def lab_distance(world,family,fixed_objects=False,fixed_gates=False,limit=200000):
    queue=deque([(world,0)]);seen={key(world)}
    while queue:
        state,distance=queue.popleft()
        if done(family,world,state):return distance
        for action in range(4):
            nxt=lab_step(state,action,fixed_objects,fixed_gates);identity=key(nxt)
            if identity not in seen:
                seen.add(identity)
                if len(seen)>limit:return None
                queue.append((nxt,distance+1))
    return None


def lab_joint(rng):
    """Rectangular two-room puzzles from a separately coded layout sampler."""
    h,w=rng.choice((6,7)),rng.choice((6,7));vertical=rng.random()<.5
    if vertical:
        cut=rng.randrange(2,w-2);door=rng.randrange(1,h-1);barrier={(cut,y) for y in range(1,h-1) if y!=door}
        left=[(x,y) for x in range(1,cut) for y in range(1,h-1)];right=[(x,y) for x in range(cut+1,w-1) for y in range(1,h-1)]
        gate=(cut,door);box=(cut+1,door);far=(min(w-2,cut+2),door)
    else:
        cut=rng.randrange(2,h-2);door=rng.randrange(1,w-1);barrier={(x,cut) for x in range(1,w-1) if x!=door}
        left=[(x,y) for y in range(1,cut) for x in range(1,w-1)];right=[(x,y) for y in range(cut+1,h-1) for x in range(1,w-1)]
        gate=(door,cut);box=(door,cut+1);far=(door,min(h-2,cut+2))
    agent,switch=rng.sample(left,2);mark=rng.choice([p for p in right if p not in (box,far)])
    border={(x,y) for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)};reserved={agent,switch,gate,box,far,mark}
    candidates=[p for p in left+right if p not in reserved];extra=set(rng.sample(candidates,rng.randrange(0,min(3,len(candidates)+1))))
    idx=lambda p:p[1]*w+p[0];walls=sum(1<<idx(p) for p in border|barrier|extra)
    return LabWorld(h,w,walls,idx(agent),1<<idx(box),1<<idx(mark),1<<idx(switch),1<<idx(gate))


def lab_suite(seed,count,exclude=()):
    rng=random.Random(seed);exclude=set(exclude);out=[];attempts=Counter()
    for family in ('push','collect','open','joint'):
        seen=set()
        while len(seen)<count and attempts[family]<100000:
            attempts[family]+=1;world=lab_joint(rng) if family=='joint' else lab_world(rng,family);identity=key(world);distance=lab_distance(world,family)
            if distance is not None and 2<=distance<=28 and identity not in exclude and identity not in seen:
                seen.add(identity);out.append((family,world,distance))
        if len(seen)<count:raise RuntimeError(f'not enough {family} lab worlds')
    return out,dict(attempts)


def nuisance_bit(canonical,cell,mode,kind,phase):
    """Environment-only family; inference never receives kind or formula identity."""
    at=lambda offset,channel:canonical[((cell+offset)%CELLS)*CHANNELS+channel]
    a=at(mode+1,(2*mode+1)%CHANNELS);b=at(2*mode+3,(3*mode+2)%CHANNELS);c=at(3*mode+5,(5*mode+4)%CHANNELS)
    value=(a^b,a&b,a|b,a^b^c,(a&b)^c,(a if b else c))[kind%6]
    return value^(((phase>>mode)&1) and (cell+2*mode)%5==0)


def variable_expose(canonical,routes,kinds,phase=0):
    routes=tuple(routes);slots=[i for i,x in enumerate(routes) if x is None];assert len(kinds)==len(slots)
    assert sorted(x for x in routes if x is not None)==list(range(CHANNELS));modes={slot:i for i,slot in enumerate(slots)};out=bytearray(CELLS*len(routes))
    for cell in range(CELLS):
        for observed,channel in enumerate(routes):
            out[cell*len(routes)+observed]=canonical[cell*CHANNELS+channel] if channel is not None else nuisance_bit(canonical,cell,modes[observed],kinds[modes[observed]],phase)
    return bytes(out)


def inverse(routes,total):return tuple(tuple(routes).index(i) for i in range(total))
def changed(before,after,channels):return frozenset(i for i in range(channels) if before[i::channels]!=after[i::channels])


def infer_bidirectional_support_binding(reference,reference_support,target_rows):
    """Keep mappings that preserve the complete empirical change alphabet."""
    rows=[]
    for mapping in itertools.permutations(range(target_rows[0][0].channels),reference.channels):
        if all(projected_support(support,mapping)==reference_support for _,support in target_rows):
            per=tuple(sensor_log_probability(reference,target,mapping) for target,_ in target_rows);rows.append((sum(per),mapping,per))
    if len(rows)<2:return {'mapping':rows[0][1] if rows else None,'compatible':len(rows),'per_stream':()}
    rows.sort();top=rows[-1][0];z=sum(math.exp(value-top) for value,_,_ in rows);streams=[]
    for stream in range(len(target_rows)):
        ranked=sorted((row[2][stream],row[1]) for row in rows)
        streams.append({'mapping':ranked[-1][1],'log_margin':ranked[-1][0]-ranked[-2][0]})
    return {'mapping':rows[-1][1],'posterior':1/z,'log_margin':rows[-1][0]-rows[-2][0],
        'second':rows[-2][1],'compatible':len(rows),'per_stream':tuple(streams)}


def same_cell_counts(triples,channels):
    """Anonymous bidirectional co-presence; omit the shifting all-zero base rate."""
    rows={(a,b):(Counter(),Counter()) for a in range(channels) for b in range(a+1,channels)}
    for before,_,_ in triples:
        for cell in range(CELLS):
            offset=cell*channels
            for pair,(ab,ba) in rows.items():
                a,b=before[offset+pair[0]],before[offset+pair[1]]
                if a:ab[b]+=1
                if b:ba[a]+=1
    return rows


def same_cell_log_probability(reference,target,mapping):
    value=0.
    for a in range(CHANNELS):
        for b in range(a+1,CHANNELS):
            oa,ob=mapping[a],mapping[b];pair=tuple(sorted((oa,ob)));ab,ba=target[pair]
            if oa>ob:ab,ba=ba,ab
            value+=log_categorical(ab,reference[(a,b)][0])+log_categorical(ba,reference[(a,b)][1])
    return value


def infer_relational_support_binding(reference,reference_support,reference_triples,target_rows):
    """Support equality, then transition and anonymous conditional co-presence probabilities."""
    base=same_cell_counts(reference_triples,reference.channels)
    prepared=[(stats,support,same_cell_counts(triples,stats.channels)) for stats,support,triples in target_rows];rows=[]
    for mapping in itertools.permutations(range(prepared[0][0].channels),reference.channels):
        if all(projected_support(support,mapping)==reference_support for _,support,_ in prepared):
            parts=tuple((sensor_log_probability(reference,stats,mapping),same_cell_log_probability(base,pairs,mapping)) for stats,_,pairs in prepared)
            rows.append((sum(a+b for a,b in parts),mapping,parts))
    if not rows:return {'mapping':None,'compatible':0,'per_stream':()}
    rows.sort();top=rows[-1][0]
    if len(rows)==1:return {'mapping':rows[0][1],'posterior':1.,'log_margin':float('inf'),'second':None,'compatible':1,'per_stream':()}
    z=sum(math.exp(value-top) for value,_,_ in rows);streams=[]
    for stream in range(len(prepared)):
        ranked=sorted((row[2][stream][0]+row[2][stream][1],row[1]) for row in rows)
        streams.append({'mapping':ranked[-1][1],'log_margin':ranked[-1][0]-ranked[-2][0]})
    winner=rows[-1]
    return {'mapping':winner[1],'posterior':1/z,'log_margin':winner[0]-rows[-2][0],'second':rows[-2][1],
        'compatible':len(rows),'sensor_log_probability':sum(x[0] for x in winner[2]),
        'same_cell_log_probability':sum(x[1] for x in winner[2]),'per_stream':tuple(streams)}


def apply_slot(world,phase,slot,routes):
    route=routes[slot]
    if route is not None:return lab_step(world,route),phase
    mode=sum(x is None for x in routes[:slot]);return world,phase^(1<<mode)


def collect_variable(seed,counts,steps,sensors,actions,kinds,exclude=()):
    rng=random.Random(seed);stats=OpenInterfaceStats(len(sensors));triples=[];support=set();initials=set();exclude=set(exclude)
    counts={family:counts for family in ('push','collect','open')} if isinstance(counts,int) else counts
    for family,total in counts.items():
        accepted=0
        while accepted<total:
            world=lab_world(rng,family);identity=key(world)
            if identity in initials or identity in exclude:continue
            accepted+=1;initials.add(identity);phase=0
            for _ in range(steps):
                before=variable_expose(lab_raw(world),sensors,kinds,phase);slot=rng.randrange(len(actions));world,phase=apply_slot(world,phase,slot,actions)
                after=variable_expose(lab_raw(world),sensors,kinds,phase);stats.observe(before,after);triples.append((before,slot,after));support.add(changed(before,after,len(sensors)))
    return stats,triples,initials,support


def evaluate_variable(policies,suite,sensors,actions,kinds,seed,episodes,steps):
    rows={name:Counter() for name in policies};traces={name:{} for name in policies};cache={}
    for index,(family,initial,distance) in enumerate(suite):
        for episode in range(episodes):
            for name,policy in policies.items():
                rng=random.Random(seed+index*100000+episode);world=initial;phase=0;path=[]
                for _ in range(steps):
                    observed=variable_expose(lab_raw(world),sensors,kinds,phase);cache_key=(name,observed)
                    if cache_key not in cache:cache[cache_key]=policy.probabilities(observed)
                    slot=choose(cache[cache_key],rng);path.append(slot);world,phase=apply_slot(world,phase,slot,actions)
                    success=done(family,initial,world)
                    if success:break
                row=rows[name];row['episodes']+=1;row['successes']+=success;row[f'{family}_successes']+=success
                if success and index not in traces[name]:traces[name][index]=path
    return {name:dict(row) for name,row in rows.items()},traces


VariableBoundPolicy=OpenBoundPolicy
