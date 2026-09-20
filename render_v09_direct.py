#!/usr/bin/env python3
"""Render the first frozen direct-control success on all sixteen v0.9 worlds."""
from __future__ import annotations

import json,pickle,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_cross_task_v07 import World,bit,truth
from bpc_direct_composition_v09 import ProductPolicy,evaluate,raw

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v09direct';VIDEO=OUT/'bpc_direct_composition_v09_16_worlds.mp4';POSTER=OUT/'poster_v09_direct.png'
FPS=30;BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85);INK=(232,240,255);MUTED=(136,157,189)
CYAN=(73,219,232);GOLD=(255,199,87);GREEN=(89,225,159);RED=(255,105,123)


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


def panel(draw,rect,index,world,distance,action,probability,step,total):
    x0,y0,x1,y1=rect;draw.rounded_rectangle(rect,11,fill=PANEL,outline=LINE)
    label(draw,(x0+14,y0+10),f'NEW WORLD {index:02d}  ·  SHORTEST {distance}',14,CYAN,True)
    board(draw,world,x0+14,y0+43)
    sx=x0+210;label(draw,(sx,y0+48),f'DIRECT STEP {step:02d}/{total:02d}',13,MUTED,True)
    status='COLLECTED' if world.marks==0 else ('READY' if action is None else f'SAMPLED A{action}')
    label(draw,(sx,y0+75),status,17,GREEN if world.marks==0 else GOLD,True)
    for a,value in enumerate(probability or (.25,)*4):
        y=y0+112+a*27;label(draw,(sx,y+2),f'A{a}',12,INK,True);draw.rounded_rectangle((sx+35,y,sx+35+int(value*245),y+15),4,fill=CYAN if a==action else (52,83,115))
        label(draw,(sx+287,y),f'{value:.2f}',11,MUTED)


def frame(group,states,step,model):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(22,16),'BPC DIRECT TASK COMPOSITION v0.9',27,INK,True)
    label(draw,(22,52),'Independent push-only Choice × collect-only Choice · no joint training or runtime search',14,MUTED)
    rects=((18,82,620,338),(640,82,1262,338),(18,354,620,610),(640,354,1262,610))
    for slot,item in enumerate(group):
        index,initial,distance,path=item;world=states[slot];action=path[step] if step<len(path) else None
        probability=model.probabilities(raw(world)) if world.marks else None
        panel(draw,rects[slot],index,world,distance,action,probability,step,len(path))
    cards=(('PRODUCT','942 / 2,048'),('COLLECT ONLY','830 / 2,048'),('SHARED CUBE','610 / 2,048'),('ROTATED','71 / 2,048'))
    for i,(name,value) in enumerate(cards):
        x=18+i*311;draw.rounded_rectangle((x,626,x+297,680),8,fill=PANEL,outline=LINE);label(draw,(x+12,635),name,10,MUTED,True)
        label(draw,(x+12,652),value,16,GREEN if i==0 else RED if i==3 else INK,True)
    label(draw,(18,698),'BOUNDARY: equal product + raw encoder + binary success events supplied · direct stochastic policy · not AGI',11,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(82,174),title,41,INK,True);label(draw,(84,235),subtitle,20,MUTED)
    draw.rounded_rectangle((84,310,1196,468),15,fill=PANEL,outline=LINE)
    label(draw,(118,337),'TRAIN: 2,000 push-only + 2,000 collect-only episodes · joint tasks: 0',19,color,True)
    label(draw,(118,383),'FROZEN DIRECT CONTROL: 942/2,048 · all 16 new worlds solved',19,color,True)
    label(draw,(118,429),'CONTROLS: collect 830 · shared 610 · random 235 · rotated 71',19,color,True)
    label(draw,(84,650),'Developer-frozen synthetic evidence. Equal probability multiplication is supplied.',15,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text());assert result['adopted']
    with (OUT/'development_models.pkl').open('rb') as file:shared,specialists,_=pickle.load(file)
    assert {'shared':shared.digest(),'push':specialists['push'].digest(),'collect':specialists['collect'].digest()}==result['model_digests']
    data=json.loads((ROOT/'holdout_v09.json').read_text());holdout=[]
    for row in data['worlds']:
        holdout.append((World(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks']),row['shortest']))
    product=ProductPolicy(specialists['push'],specialists['collect']);condition,traces=evaluate({'product':product},holdout,99_309,64,32)
    assert condition['product']==result['conditions']['99309']['32']['product'] and len(traces['product'])==16
    items=[(i+1,world,distance,traces['product'][i]) for i,(world,distance) in enumerate(holdout)]
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC COMPOSES TWO DIRECT POLICIES','Separate probability cubes cooperate on push-required collection')
    for _ in range(55):process.stdin.write(intro.tobytes())
    for start in range(0,16,4):
        group=items[start:start+4];states=[item[1] for item in group];longest=max(len(item[3]) for item in group)
        for step in range(longest+1):
            image=frame(group,states,step,product)
            for _ in range(2):process.stdin.write(image.tobytes())
            for slot,item in enumerate(group):
                if step<len(item[3]):states[slot]=truth(states[slot],item[3][step])
        for _ in range(18):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.9 RESULT: ADOPTED','All 10 gates passed · direct actions · zero evaluation writes',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
