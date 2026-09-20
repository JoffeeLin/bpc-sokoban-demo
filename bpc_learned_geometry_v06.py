#!/usr/bin/env python3
"""BPC v0.6: macro push geometry learned from raw transition deltas."""
from __future__ import annotations

import random
from collections import Counter,deque

from bpc_learned_wave_v04 import ACTION_NAMES,Level,LocalWorldBPC,apply_prediction,bit,positions,random_level,truth_step
from bpc_reversible_wave_v05 import learned_components,learned_reach,learned_walk


def relative(level:Level,origin:int,target:int):
    return target%level.w-origin%level.w,target//level.w-origin//level.w


def offset(level:Level,origin:int,delta:tuple[int,int]):
    x,y=origin%level.w+delta[0],origin//level.w+delta[1]
    return y*level.w+x if 0<=x<level.w and 0<=y<level.h else -1


def learn_push_templates(seed:int,episodes:int,steps:int):
    """Discover anonymous action-relative push deltas from interaction."""
    rng=random.Random(seed); counts=[Counter() for _ in range(4)]; pushes=0
    for _ in range(episodes):
        level=random_level(rng);boxes,player=level.boxes,level.player
        for _ in range(steps):
            action=rng.randrange(4);next_boxes,next_player=truth_step(level,boxes,player,action)
            if next_boxes!=boxes:
                removed=next(positions(boxes&~next_boxes));added=next(positions(next_boxes&~boxes))
                template=(relative(level,player,removed),relative(level,player,added),
                          relative(level,player,next_player))
                counts[action][template]+=1;pushes+=1
            boxes,player=next_boxes,next_player
    templates=tuple(max(row,key=lambda x:(row[x],x)) for row in counts)
    evidence=[[{'template':template,'count':count} for template,count in sorted(row.items())]
              for row in counts]
    return templates,evidence,pushes


def solve(level:Level,model:LocalWorldBPC,inverse:tuple[int,...],templates:tuple,limit:int=5_000_000):
    """Backward wave whose macro predecessor geometry comes from experience."""
    cache={}
    def lr(boxes,start):
        key=(boxes,start)
        if key not in cache:
            area,anchor=learned_reach(level,boxes,start,model,inverse)
            if area:
                for player in positions(area):cache[(boxes,player)]=(area,anchor)
            else:cache[key]=(area,anchor)
        return cache[key]
    terminal=level.goals;field={};queue=deque()
    for anchor in learned_components(level,terminal,model,inverse):field[(terminal,anchor)]=0;queue.append((terminal,anchor))
    initial=(level.boxes,lr(level.boxes,level.player)[1])
    while queue and initial not in field and len(field)<limit:
        boxes,anchor=queue.popleft();phase=field[(boxes,anchor)];area,_=lr(boxes,anchor)
        for current_box in positions(boxes):
            for action,(removed,added,next_player) in enumerate(templates):
                prior_player=offset(level,current_box,(-added[0],-added[1]))
                if prior_player<0:continue
                prior_box=offset(level,prior_player,removed)
                predicted_player=offset(level,prior_player,next_player)
                if prior_box<0 or predicted_player<0 or not bit(area,prior_box):continue
                pred_boxes=(boxes&~(1<<current_box))|(1<<prior_box)
                prediction=apply_prediction(level,pred_boxes,prior_player,action,model)
                if prediction!=(boxes,predicted_player):continue
                pred_anchor=lr(pred_boxes,prior_player)[1]
                if pred_anchor<0:continue
                state=(pred_boxes,pred_anchor)
                if state not in field:field[state]=phase+1;queue.append(state)
    if initial not in field:return {'solved':False,'complete':not queue,'states':len(field)}
    boxes,player=level.boxes,level.player;phase=field[initial];sequence=[];pushes=0
    while phase:
        area,_=lr(boxes,player);selected=None
        for box in positions(boxes):
            for action,(removed,_added,_next_player) in enumerate(templates):
                stance=offset(level,box,(-removed[0],-removed[1]))
                if stance<0 or not bit(area,stance):continue
                prediction=apply_prediction(level,boxes,stance,action,model)
                if prediction is None or prediction[0]==boxes:continue
                nb,np=prediction;na=lr(nb,np)[1];next_phase=field.get((nb,na))
                if next_phase is not None and next_phase<phase:
                    selected=(stance,action,nb,np,next_phase);break
            if selected:break
        if selected is None:raise RuntimeError('learned geometry field readout inconsistency')
        stance,action,next_boxes,next_player,next_phase=selected
        sequence.extend(ACTION_NAMES[a] for a in learned_walk(level,boxes,player,stance,model,inverse))
        sequence.append(ACTION_NAMES[action]);boxes,player,phase=next_boxes,next_player,next_phase;pushes+=1
    return {'solved':boxes==level.goals,'complete':False,'states':len(field),
            'push_phase':pushes,'actions':len(sequence),'sequence':''.join(sequence)}


def audit_templates(templates:tuple,seed:int,episodes:int,steps:int):
    rng=random.Random(seed);result=Counter()
    for _ in range(episodes):
        level=random_level(rng);boxes,player=level.boxes,level.player
        for _ in range(steps):
            action=rng.randrange(4);next_boxes,next_player=truth_step(level,boxes,player,action)
            if next_boxes!=boxes:
                removed=next(positions(boxes&~next_boxes));added=next(positions(next_boxes&~boxes))
                actual=(relative(level,player,removed),relative(level,player,added),relative(level,player,next_player))
                result['pushes']+=1;result['exact']+=actual==templates[action]
            boxes,player=next_boxes,next_player
    return dict(result)
