#!/usr/bin/env python3
"""Render frozen v0.10 task-name-free factor discovery and routing traces."""
from __future__ import annotations

import json,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_autofactor_v10 import evaluate,train
from bpc_cross_task_v07 import World,bit,truth
from bpc_direct_composition_v09 import raw

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v10autofactor'
VIDEO=OUT/'bpc_autofactor_v10_12_unseen_worlds.mp4';POSTER=OUT/'poster_v10_autofactor.png'
FPS=30;BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85);INK=(232,240,255);MUTED=(136,157,189)
CYAN=(73,219,232);GOLD=(255,199,87);GREEN=(89,225,159);RED=(255,105,123);VIOLET=(177,137,255)


def font(size,bold=False):return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)
def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)


def board(draw,world,x,y,cell=25):
    for yy in range(world.h):
        for xx in range(world.w):
            i=yy*world.w+xx;x0,y0=x+xx*cell,y+yy*cell;wall=bit(world.walls,i);mark=bit(world.marks,i);obj=bit(world.objects,i)
            fill=(50,66,90) if wall else (18,42,67);draw.rounded_rectangle((x0,y0,x0+cell-3,y0+cell-3),3,fill=fill)
            if mark and not wall:draw.ellipse((x0+5,y0+5,x0+cell-8,y0+cell-8),outline=GOLD,width=3)
            if obj:draw.rounded_rectangle((x0+6,y0+6,x0+cell-9,y0+cell-9),3,fill=GREEN if mark else RED,outline=GOLD if mark else RED)
            if i==world.agent:draw.ellipse((x0+7,y0+7,x0+cell-10,y0+cell-10),fill=CYAN)


def done(family,initial,world):return world.objects!=initial.objects if family=='push' else world.marks==0


def panel(draw,rect,item,world,step,learner):
    index,family,initial,distance,path=item;x0,y0,x1,y1=rect;draw.rounded_rectangle(rect,11,fill=PANEL,outline=LINE)
    label(draw,(x0+14,y0+10),f'UNSEEN {index:02d} · AUDIT {family.upper()} · d={distance}',13,CYAN,True);board(draw,world,x0+14,y0+43)
    sx=x0+210;active=learner.active(raw(world));probability=learner.probabilities(raw(world));action=path[step] if step<len(path) else None
    label(draw,(sx,y0+47),'MODEL INPUT: RAW BITS ONLY',11,MUTED,True)
    label(draw,(sx,y0+68),'ACTIVE  '+(' × '.join('F'+''.join(map(str,x)) for x in active) or 'NONE'),15,VIOLET,True)
    status='DONE' if done(family,initial,world) else ('READY' if action is None else f'SAMPLED A{action}')
    label(draw,(sx,y0+94),status,16,GREEN if status=='DONE' else GOLD,True)
    for a,value in enumerate(probability):
        yy=y0+126+a*25;label(draw,(sx,yy+1),f'A{a}',11,INK,True)
        draw.rounded_rectangle((sx+32,yy,sx+32+int(value*236),yy+14),4,fill=CYAN if a==action else (52,83,115));label(draw,(sx+276,yy),f'{value:.2f}',10,MUTED)


def frame(group,states,step,learner):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(22,16),'BPC ANONYMOUS FACTOR DISCOVERY v0.10',27,INK,True)
    label(draw,(22,52),'Terminal raw co-change discovers factors · raw presence routes them · no task name at decision time',14,MUTED)
    rects=((18,82,620,338),(640,82,1262,338),(18,354,620,610),(640,354,1262,610))
    for slot,item in enumerate(group):panel(draw,rects[slot],item,states[slot],step,learner)
    cards=(('AUTO','4,284 / 6,144'),('ORACLE','4,284 / 6,144'),('SHARED','3,962 / 6,144'),('PERMUTED','2,749 / 6,144'),('ALL','4,302 / 6,144'))
    for i,(name,value) in enumerate(cards):
        x=18+i*249;draw.rounded_rectangle((x,626,x+235,680),8,fill=PANEL,outline=LINE);label(draw,(x+10,635),name,10,MUTED,True)
        label(draw,(x+10,652),value,14,GREEN if i<2 else RED if i==3 else INK,True)
    label(draw,(18,698),'BOUNDARY: equal probability product + raw channels + terminal events supplied · ALL is slightly higher · not AGI',11,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(76,150),title,40,INK,True);label(draw,(79,210),subtitle,20,MUTED)
    draw.rounded_rectangle((79,285,1201,493),15,fill=PANEL,outline=LINE)
    label(draw,(112,315),'DISCOVERED: terminal Δ(1,2) and Δ(1,3) · common plane 1 removed',18,color,True)
    label(draw,(112,360),'FROZEN: AUTO = TASK-NAME ORACLE = 4,284 / 6,144',18,color,True)
    label(draw,(112,405),'342,139 routing decisions · 0 mismatches · 0 evaluation writes',18,color,True)
    label(draw,(112,450),'CAUSAL CONTROL: permuted activation = 2,749 / 6,144',18,color,True)
    label(draw,(79,650),'Developer-frozen synthetic evidence. Factor routing is learned; multiplication is not.',15,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text());assert result['adopted'];protocol=json.loads((ROOT/'protocol_v10_autofactor.json').read_text())
    config=protocol['config'];learner,events=train(config['train_seed'],config['uniform_episodes'],config['guided_rounds'],config['guided_episodes'],config['train_steps'])
    assert events==result['training'] and learner.digest()==result['factor_digest'];data=json.loads((ROOT/'holdout_v10.json').read_text());suite=[]
    for row in data['worlds']:
        suite.append((row['family'],World(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks']),row['shortest']))
    condition,traces=evaluate(learner,suite,config['eval_seeds'][0],config['episodes_per_map'],32)
    assert condition==result['conditions'][str(config['eval_seeds'][0])]['32']
    chosen=[]
    for family in ('push','collect','combined'):
        candidates=[i for i,(name,_,_) in enumerate(suite) if name==family and i in traces['auto']]
        chosen.extend(candidates[:4])
    if len(chosen)!=12:raise RuntimeError('twelve representative success traces unavailable')
    items=[(i+1,*suite[i],traces['auto'][i]) for i in chosen]
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC DISCOVERS ITS OWN EVENT FACTORS','One learner, no task label, direct stochastic control')
    for _ in range(55):process.stdin.write(intro.tobytes())
    for start in range(0,12,4):
        group=items[start:start+4];states=[item[2] for item in group];longest=max(len(item[4]) for item in group)
        for step in range(longest+1):
            image=frame(group,states,step,learner)
            for _ in range(2):process.stdin.write(image.tobytes())
            for slot,item in enumerate(group):
                if step<len(item[4]):states[slot]=truth(states[slot],item[4][step])
        for _ in range(18):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.10 RESULT: ADOPTED','All 10 gates passed · task-name-free factor routing · no runtime search',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
