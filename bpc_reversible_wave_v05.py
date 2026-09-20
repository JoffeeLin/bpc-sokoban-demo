#!/usr/bin/env python3
"""BPC v0.5: future-effect equivalence from learned reversible actions.

This removes v0.4's hand-written free-space flood fill.  A microstate joins an
equivalence orbit only when the learned forward action followed by its
experience-discovered inverse reconstructs the exact prior state.
"""
from __future__ import annotations

import random
from collections import Counter,deque

from bpc_learned_wave_v04 import (ACTION_NAMES,Level,LocalWorldBPC,
    apply_prediction,bit,moved,positions,random_level,truth_step)


def discover_inverses(seed:int,episodes:int,steps:int):
    """Use real round trips; action names and geometry are not consulted."""
    rng=random.Random(seed); counts=[[0]*4 for _ in range(4)]
    for _ in range(episodes):
        level=random_level(rng); boxes,player=level.boxes,level.player
        for _ in range(steps):
            action=rng.randrange(4); before=(boxes,player)
            boxes,player=truth_step(level,boxes,player,action)
            if (boxes,player)==before:continue
            for candidate in range(4):
                if truth_step(level,boxes,player,candidate)==before:
                    counts[action][candidate]+=1
    inverse=tuple(max(range(4),key=lambda b:counts[a][b]) for a in range(4))
    return inverse,counts


def reversible_orbit(level:Level,boxes:int,start:int,model:LocalWorldBPC,inverse:tuple[int,...]):
    """Return only states certified by a learned one-step round trip."""
    root=(boxes,start)
    if not any(apply_prediction(level,boxes,start,a,model) is not None for a in range(4)):
        return set(),{}
    seen={root}; parent={root:None}; used={}; queue=deque([root])
    while queue:
        state=queue.popleft(); current_boxes,player=state
        for action in range(4):
            nxt=apply_prediction(level,current_boxes,player,action,model)
            if nxt is None or nxt==state or nxt in seen:continue
            if apply_prediction(level,nxt[0],nxt[1],inverse[action],model)!=state:continue
            seen.add(nxt);parent[nxt]=state;used[nxt]=action;queue.append(nxt)
    return seen,(parent,used)


def learned_reach(level:Level,boxes:int,start:int,model:LocalWorldBPC,inverse:tuple[int,...]):
    orbit,_=reversible_orbit(level,boxes,start,model,inverse)
    same=[player for state_boxes,player in orbit if state_boxes==boxes]
    if len(same)!=len(orbit) or not same:return 0,-1
    mask=sum(1<<player for player in same)
    return mask,min(same)


def learned_components(level:Level,boxes:int,model:LocalWorldBPC,inverse:tuple[int,...]):
    remaining=(1<<(level.h*level.w))-1; output=[]
    while remaining:
        start=(remaining&-remaining).bit_length()-1
        area,anchor=learned_reach(level,boxes,start,model,inverse)
        if area:output.append(anchor);remaining&=~area
        else:remaining&=~(1<<start)
    return output


def learned_walk(level:Level,boxes:int,start:int,target:int,model:LocalWorldBPC,inverse:tuple[int,...]):
    orbit,graph=reversible_orbit(level,boxes,start,model,inverse); goal=(boxes,target)
    if goal not in orbit:raise RuntimeError('learned reversible orbit does not reach stance')
    parent,used=graph; actions=[]; state=goal
    while parent[state] is not None:actions.append(used[state]);state=parent[state]
    return actions[::-1]


def solve(level:Level,model:LocalWorldBPC,inverse:tuple[int,...],limit:int=5_000_000):
    cache={}
    def lr(boxes,start):
        key=(boxes,start)
        if key not in cache:
            area,anchor=learned_reach(level,boxes,start,model,inverse)
            if area:
                for player in positions(area):cache[(boxes,player)]=(area,anchor)
            else:cache[key]=(area,anchor)
        return cache[key]
    terminal=level.goals; field={}; queue=deque()
    for anchor in learned_components(level,terminal,model,inverse):
        field[(terminal,anchor)]=0;queue.append((terminal,anchor))
    initial_anchor=lr(level.boxes,level.player)[1]
    initial=(level.boxes,initial_anchor)
    while queue and initial not in field and len(field)<limit:
        boxes,anchor=queue.popleft();phase=field[(boxes,anchor)]
        area,_=lr(boxes,anchor)
        for current_box in positions(boxes):
            for action in range(4):
                back=inverse[action]
                prior_box=moved(level,current_box,back)
                prior_player=moved(level,current_box,back,2)
                if prior_box<0 or prior_player<0 or not bit(area,prior_box):continue
                pred_boxes=(boxes&~(1<<current_box))|(1<<prior_box)
                prediction=apply_prediction(level,pred_boxes,prior_player,action,model)
                if prediction!=(boxes,prior_box):continue
                pred_anchor=lr(pred_boxes,prior_player)[1]
                if pred_anchor<0:continue
                state=(pred_boxes,pred_anchor)
                if state not in field:field[state]=phase+1;queue.append(state)
    if initial not in field:return {'solved':False,'complete':not queue,'states':len(field)}
    boxes,player=level.boxes,level.player;phase=field[initial];sequence=[];pushes=0
    while phase:
        area,_=lr(boxes,player);selected=None
        for box in positions(boxes):
            for action in range(4):
                stance=moved(level,box,inverse[action])
                if stance<0 or not bit(area,stance):continue
                prediction=apply_prediction(level,boxes,stance,action,model)
                if prediction is None or prediction[0]==boxes:continue
                nb,np=prediction;na=lr(nb,np)[1]
                next_phase=field.get((nb,na))
                if next_phase is not None and next_phase<phase:
                    selected=(box,stance,action,nb,np,next_phase);break
            if selected:break
        if selected is None:raise RuntimeError('learned reversible field readout inconsistency')
        box,stance,action,next_boxes,next_player,next_phase=selected
        sequence.extend(ACTION_NAMES[a] for a in learned_walk(level,boxes,player,stance,model,inverse))
        sequence.append(ACTION_NAMES[action]);boxes,player,phase=next_boxes,next_player,next_phase;pushes+=1
    return {'solved':boxes==level.goals,'complete':False,'states':len(field),
            'push_phase':pushes,'actions':len(sequence),'sequence':''.join(sequence)}


def audit_reach(model:LocalWorldBPC,inverse:tuple[int,...],seed:int,episodes:int,steps:int):
    """Compare learned orbits with the old supplied flood fill for audit only."""
    from bpc_learned_wave_v04 import reach
    rng=random.Random(seed); result=Counter()
    for _ in range(episodes):
        level=random_level(rng);boxes,player=level.boxes,level.player
        for _ in range(steps):
            hard=reach(level,boxes,player)[0];learned=learned_reach(level,boxes,player,model,inverse)[0]
            result['states']+=1;result['exact']+=hard==learned
            result['symmetric_difference_cells']+=(hard^learned).bit_count()
            action=rng.randrange(4);boxes,player=truth_step(level,boxes,player,action)
    return dict(result)
