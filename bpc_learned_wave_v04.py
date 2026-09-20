#!/usr/bin/env python3
"""BPC v0.4: a raw-experience local world function inside a configuration wave.

The learned table sees three action-relative raw cells.  Sokoban names are
used only by the environment/parser and evaluator.  The configuration-wave
shell still supplies reachable-component compression; that remaining
scaffold is reported explicitly rather than presented as learned intelligence.
"""
from __future__ import annotations

import hashlib,pickle,random
from collections import Counter,defaultdict,deque
from dataclasses import dataclass

ACTIONS=((-1,0),(1,0),(0,-1),(0,1))
ACTION_NAMES="LRUD"
STATIC_MASK,DYNAMIC_MASK=3,12


@dataclass(frozen=True)
class Level:
    h:int; w:int; walls:int; goals:int; player:int; boxes:int


def bit(mask,i): return (mask>>i)&1
def positions(mask):
    while mask:
        low=mask&-mask; yield low.bit_length()-1; mask-=low


def parse(text:str)->Level:
    rows=text.splitlines(); h=len(rows); w=max(map(len,rows)); walls=goals=boxes=0; player=-1
    for y,row in enumerate(rows):
        for x,ch in enumerate(row.ljust(w)):
            i=y*w+x
            if ch=='#': walls|=1<<i
            elif ch=='.': goals|=1<<i
            elif ch=='$': boxes|=1<<i
            elif ch=='*': boxes|=1<<i; goals|=1<<i
            elif ch=='@': player=i
            elif ch=='+': player=i; goals|=1<<i
            elif ch!=' ': raise ValueError(f'bad map char {ch!r}')
    if player<0 or boxes.bit_count()!=goals.bit_count(): raise ValueError('need one player and boxes == goals')
    return Level(h,w,walls,goals,player,boxes)


def moved(level:Level,i:int,action:int,amount:int=1)->int:
    x,y=i%level.w,i//level.w; dx,dy=ACTIONS[action]; x+=dx*amount; y+=dy*amount
    return y*level.w+x if 0<=x<level.w and 0<=y<level.h else -1


def token(level:Level,boxes:int,player:int,i:int)->int:
    if i<0:return 1
    return bit(level.walls,i)|(bit(level.goals,i)<<1)|(bit(boxes,i)<<2)|((i==player)<<3)


def patch_at(level:Level,boxes:int,player:int,origin:int,action:int)->tuple[int,int,int]:
    return tuple(token(level,boxes,player,moved(level,origin,action,k)) for k in range(3))


def patch(level:Level,boxes:int,player:int,action:int)->tuple[int,int,int]:
    return patch_at(level,boxes,player,player,action)


def truth_step(level:Level,boxes:int,player:int,action:int)->tuple[int,int]:
    near=moved(level,player,action)
    if near<0 or bit(level.walls,near): return boxes,player
    if bit(boxes,near):
        far=moved(level,player,action,2)
        if far<0 or bit(level.walls|boxes,far): return boxes,player
        boxes^=(1<<near)|(1<<far)
    return boxes,near


class LocalWorldBPC:
    """Exact Dirichlet counts for raw local transition outcomes."""
    def __init__(self,depth:int=3):
        self.depth=depth; self.rows=defaultdict(Counter); self.writes=0

    def observe(self,before:tuple[int,...],after:tuple[int,...]):
        self.rows[before[:self.depth]][after]+=1; self.writes+=1

    def predict(self,before:tuple[int,...],minimum:int=2)->tuple[int,...]|None:
        row=self.rows.get(before[:self.depth])
        if not row or sum(row.values())<minimum:return None
        return max(row,key=lambda x:(row[x],x))

    def probability(self,before:tuple[int,...],after:tuple[int,...])->float:
        row=self.rows.get(before[:self.depth],{}); total=sum(row.values())
        return (row.get(after,0)+1)/(total+max(1,len(row)))

    def digest(self):
        rows=sorted((key,sorted(value.items())) for key,value in self.rows.items())
        return hashlib.sha256(pickle.dumps((self.depth,rows),protocol=5)).hexdigest()


def apply_prediction(level:Level,boxes:int,player:int,action:int,model:LocalWorldBPC):
    before=patch(level,boxes,player,action); after=model.predict(before)
    if after is None:return None
    cells=[moved(level,player,action,k) for k in range(3)]
    next_boxes=boxes; next_player=[]
    for i,value in zip(cells,after):
        if i<0:
            if value!=1:return None
            continue
        if value&STATIC_MASK != token(level,boxes,player,i)&STATIC_MASK:return None
        next_boxes=(next_boxes|1<<i) if value&4 else (next_boxes&~(1<<i))
        if value&8:next_player.append(i)
    if len(next_player)!=1 or next_boxes.bit_count()!=boxes.bit_count():return None
    return next_boxes,next_player[0]


def random_level(rng:random.Random)->Level:
    h=w=rng.choice((5,6,7)); cells=[y*w+x for y in range(1,h-1) for x in range(1,w-1)]
    border={y*w+x for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)}
    inside_walls=set(rng.sample(cells,rng.randrange(0,max(1,len(cells)//6))))
    free=[i for i in cells if i not in inside_walls]; n=min(rng.choice((1,2,3)),(len(free)-1)//2)
    chosen=rng.sample(free,1+2*n); player=chosen[0]
    boxes=sum(1<<i for i in chosen[1:1+n]); goals=sum(1<<i for i in chosen[1+n:])
    walls=sum(1<<i for i in border|inside_walls)
    return Level(h,w,walls,goals,player,boxes)


def learn_raw_physics(seed:int,episodes:int,steps:int):
    rng=random.Random(seed); full,no_far=LocalWorldBPC(3),LocalWorldBPC(2); events=Counter(); levels=[]
    for _ in range(episodes):
        level=random_level(rng); boxes,player=level.boxes,level.player
        levels.append((level.h,level.w,level.walls,level.goals,level.player,level.boxes))
        for _ in range(steps):
            action=rng.randrange(4); origin=player; before=patch(level,boxes,player,action)
            next_boxes,next_player=truth_step(level,boxes,player,action)
            after=patch_at(level,next_boxes,next_player,origin,action)
            full.observe(before,after); no_far.observe(before,after)
            events['box_change' if boxes!=next_boxes else 'move' if player!=next_player else 'blocked']+=1
            boxes,player=next_boxes,next_player
    manifest={"episodes":episodes,"steps_per_episode":steps,"unique_levels":len(set(levels)),
              "levels_sha256":hashlib.sha256(pickle.dumps(levels,protocol=5)).hexdigest()}
    return full,no_far,dict(events),manifest


def validate_physics(model:LocalWorldBPC,seed:int,episodes:int,steps:int):
    rng=random.Random(seed); result=Counter()
    for _ in range(episodes):
        level=random_level(rng); boxes,player=level.boxes,level.player
        for _ in range(steps):
            action=rng.randrange(4); origin=player; before=patch(level,boxes,player,action)
            next_boxes,next_player=truth_step(level,boxes,player,action)
            after=patch_at(level,next_boxes,next_player,origin,action); predicted=model.predict(before)
            kind='box_change' if boxes!=next_boxes else 'other'
            result[f'{kind}_total']+=1; result[f'{kind}_known']+=predicted is not None
            result[f'{kind}_correct']+=predicted==after
            boxes,player=next_boxes,next_player
    return dict(result)


def reach(level:Level,boxes:int,start:int):
    if start<0 or bit(level.walls|boxes,start):return 0,-1
    seen=1<<start; queue=deque([start])
    while queue:
        p=queue.popleft()
        for action in range(4):
            q=moved(level,p,action)
            if q>=0 and not bit(level.walls|boxes|seen,q):seen|=1<<q; queue.append(q)
    return seen,(seen&-seen).bit_length()-1


def components(level:Level,boxes:int):
    remaining=((1<<(level.h*level.w))-1)&~(level.walls|boxes); out=[]
    while remaining:
        start=(remaining&-remaining).bit_length()-1; mask,anchor=reach(level,boxes,start)
        out.append(anchor); remaining&=~mask
    return out


def solve(level:Level,model:LocalWorldBPC,limit:int=5_000_000):
    """Backward phase wave; local push validity is read from learned F_world."""
    terminal=level.goals; field={}; queue=deque()
    for anchor in components(level,terminal):field[(terminal,anchor)]=0; queue.append((terminal,anchor))
    initial_anchor=reach(level,level.boxes,level.player)[1]; initial=(level.boxes,initial_anchor)
    while queue and initial not in field and len(field)<limit:
        boxes,anchor=queue.popleft(); phase=field[(boxes,anchor)]; area,_=reach(level,boxes,anchor)
        for current_box in positions(boxes):
            for action in range(4):
                prior_box=moved(level,current_box,action^1)
                prior_player=moved(level,current_box,action^1,2)
                if prior_box<0 or prior_player<0 or not bit(area,prior_box):continue
                pred_boxes=(boxes&~(1<<current_box))|(1<<prior_box)
                if bit(level.walls|pred_boxes,prior_player):continue
                prediction=apply_prediction(level,pred_boxes,prior_player,action,model)
                if prediction!=(boxes,prior_box):continue
                pred_anchor=reach(level,pred_boxes,prior_player)[1]; state=(pred_boxes,pred_anchor)
                if state not in field:field[state]=phase+1;queue.append(state)
    if initial not in field:return {"solved":False,"complete":not queue,"states":len(field)}
    boxes,player=level.boxes,level.player; phase=field[initial]; sequence=[]; pushes=0
    while phase:
        area,_=reach(level,boxes,player); selected=None
        for box in positions(boxes):
            for action in range(4):
                stance=moved(level,box,action^1)
                if stance<0 or not bit(area,stance):continue
                prediction=apply_prediction(level,boxes,stance,action,model)
                if prediction is None or prediction[0]==boxes:continue
                nb,np=prediction; na=reach(level,nb,np)[1]; next_phase=field.get((nb,na))
                if next_phase is not None and next_phase<phase:
                    selected=(box,stance,action,nb,np,next_phase);break
            if selected:break
        if selected is None:raise RuntimeError('learned field readout inconsistency')
        box,stance,action,boxes,next_player,phase=selected
        walk=walk_path(level,boxes^(1<<moved(level,box,action))^(1<<box),player,stance)
        sequence.extend(ACTION_NAMES[a] for a in walk); sequence.append(ACTION_NAMES[action])
        player=next_player;pushes+=1
    return {"solved":boxes==level.goals,"complete":False,"states":len(field),
            "push_phase":pushes,"actions":len(sequence),"sequence":"".join(sequence)}


def replay(level:Level,sequence:str):
    """Independent forward execution with the true environment boundary."""
    boxes,player=level.boxes,level.player
    for symbol in sequence:
        boxes,player=truth_step(level,boxes,player,ACTION_NAMES.index(symbol))
    return boxes==level.goals,boxes,player


def walk_path(level:Level,boxes:int,start:int,target:int):
    queue=deque([start]); parent={start:None}; used={}
    while queue:
        p=queue.popleft()
        if p==target:break
        for action in range(4):
            q=moved(level,p,action)
            if q>=0 and q not in parent and not bit(level.walls|boxes,q):
                parent[q]=p; used[q]=action; queue.append(q)
    if target not in parent:raise RuntimeError('stance unreachable')
    out=[]; p=target
    while parent[p] is not None:out.append(used[p]);p=parent[p]
    return out[::-1]
