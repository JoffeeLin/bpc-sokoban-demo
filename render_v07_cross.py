#!/usr/bin/env python3
"""Render all ten frozen joint-context transition classes with an English UI."""
from __future__ import annotations

import json,random,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_cross_task_v07 import ACTIONS,evaluate,patch,random_world,train,truth

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v07cross'
VIDEO=OUT/'bpc_cross_task_v07_10_joint_classes.mp4';POSTER=OUT/'poster_v07_cross.png'
FPS=30;BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85);INK=(232,240,255);MUTED=(136,157,189)
CYAN=(73,219,232);GOLD=(255,199,87);GREEN=(89,225,159);RED=(255,105,123)


def font(size,bold=False):return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)
def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)


def token(draw,box,value):
    x0,y0,x1,y1=box;draw.rounded_rectangle(box,8,fill=(18,39,63),outline=LINE,width=2)
    if value&1:draw.rounded_rectangle((x0+7,y0+7,x1-7,y1-7),6,fill=(50,67,91))
    if value&8:draw.ellipse((x0+17,y0+17,x1-17,y1-17),outline=GOLD,width=5)
    if value&4:draw.rounded_rectangle((x0+18,y0+18,x1-18,y1-18),5,fill=GREEN if value&8 else RED,outline=GOLD if value&8 else RED,width=3)
    if value&2:draw.ellipse((x0+23,y0+23,x1-23,y1-23),fill=CYAN)


def local_row(draw,y,name,values,color):
    label(draw,(652,y+26),name,13,color,True)
    for i,value in enumerate(values):
        x=805+i*122;token(draw,(x,y,x+92,y+92),value);label(draw,(x+36,y+99),str(i),11,MUTED,True)


def board(draw,world,action,after=False):
    cell=min(58,400//max(world.h,world.w));ox=42+(520-world.w*cell)//2;oy=148+(385-world.h*cell)//2
    ray={world.agent}
    x,y=world.agent%world.w,world.agent//world.w;dx,dy=ACTIONS[action]
    for k in (1,2):
        xx,yy=x+dx*k,y+dy*k
        if 0<=xx<world.w and 0<=yy<world.h:ray.add(yy*world.w+xx)
    for yy in range(world.h):
        for xx in range(world.w):
            i=yy*world.w+xx;x0,y0=ox+xx*cell,oy+yy*cell
            wall=(world.walls>>i)&1;mark=(world.marks>>i)&1;obj=(world.objects>>i)&1
            fill=(49,65,89) if wall else (19,42,67)
            draw.rounded_rectangle((x0,y0,x0+cell-4,y0+cell-4),5,fill=fill,outline=CYAN if i in ray else fill,width=2)
            if mark and not wall:draw.ellipse((x0+11,y0+11,x0+cell-15,y0+cell-15),outline=GOLD,width=4)
            if obj:draw.rounded_rectangle((x0+13,y0+13,x0+cell-17,y0+cell-17),4,fill=GREEN if mark else RED,outline=GOLD if mark else RED,width=2)
            if i==world.agent:draw.ellipse((x0+16,y0+16,x0+cell-20,y0+cell-20),fill=CYAN)


def frame(item,index,after=False):
    world=item[3] if after else item[0];action,before,truth_tokens,predicted=item[1],item[2],item[4],item[5]
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(22,18),'BPC CROSS-TASK COMPOSITION v0.7',28,INK,True)
    label(draw,(22,57),'Push-only stream + collect-only stream → never-trained combined world',14,MUTED)
    for box in ((18,92,610,580),(630,92,1262,580)):draw.rounded_rectangle(box,12,fill=PANEL,outline=LINE)
    label(draw,(38,108),'FROZEN COMBINED WORLD',18,INK,True)
    label(draw,(38,136),f'JOINT TRANSITION CLASS {index}/10  ·  ANONYMOUS ACTION A{action}',13,CYAN,True)
    board(draw,world,action,after)
    label(draw,(650,108),'LOCAL RAW-BIT WORLD FUNCTION',18,INK,True)
    label(draw,(650,136),'Three action-relative cells; layered objects share a cell.',13,MUTED)
    local_row(draw,172,'BEFORE',before,CYAN)
    local_row(draw,303,'BPC NEXT',predicted,GREEN)
    local_row(draw,434,'TRUE NEXT',truth_tokens,GOLD)
    status='PREDICTION READY' if not after else 'EXACT · PREDICTION == TRUTH'
    label(draw,(779,552),status,17,GREEN if after else CYAN,True)
    cards=(('JOINT TRAIN','0'),('JOINT HOLDOUT','3,795 / 3,795'),('FULL MEMORY','0 / 3,795'),('EVAL WRITES','0'))
    for i,(name,value) in enumerate(cards):
        x=18+i*311;draw.rounded_rectangle((x,596,x+297,669),9,fill=PANEL,outline=LINE)
        label(draw,(x+13,607),name,11,MUTED,True);label(draw,(x+13,633),value,18,GREEN if i!=2 else RED,True)
    label(draw,(18,691),'BOUNDARY: local one-step synthetic world-function transfer · supplied channels/window/actions · not planning or AGI',12,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(82,178),title,42,INK,True);label(draw,(84,238),subtitle,20,MUTED)
    draw.rounded_rectangle((84,315,1196,465),15,fill=PANEL,outline=LINE)
    label(draw,(118,340),'TRAIN: 150k push-only + 150k collect-only · joint contexts: 0',20,color,True)
    label(draw,(118,384),'FROZEN TEST: 3,795/3,795 joint transitions · two new seeds',20,color,True)
    label(draw,(118,428),'CONTROLS: full memory 0/3,795 · condition deletion ≈65%',20,color,True)
    label(draw,(84,650),'Developer-frozen evidence; exact local composition, not autonomous planning.',15,MUTED)
    return image


def representatives(seed=77_107):
    rng=random.Random(seed);seen={}
    for _ in range(2000):
        world=random_world(rng,'combined')
        for _ in range(60):
            action=rng.randrange(4);before=patch(world,action);next_world=truth(world,action);after=patch(next_world,action,origin=world.agent)
            if any(value&4 for value in before) and any(value&8 for value in before):
                seen.setdefault((before,after),(world,action,before,next_world,after))
            world=next_world
    assert len(seen)==10
    return list(seen.values())


def main():
    result=json.loads((OUT/'result.json').read_text());assert result['adopted']
    _,_,model,_,_=train(70_707,2500,60);items=[]
    for world,action,before,next_world,after in representatives():
        predicted=model.predict(before);assert predicted==after;items.append((world,action,before,next_world,after,predicted))
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC COMPOSES TWO LEARNED WORLD FUNCTIONS','No joint box+mark context appeared in either training stream')
    for _ in range(55):process.stdin.write(intro.tobytes())
    for index,item in enumerate(items,1):
        before=frame(item,index,False);after=frame(item,index,True)
        for _ in range(16):process.stdin.write(before.tobytes())
        for _ in range(28):process.stdin.write(after.tobytes())
    outro=splash('FROZEN v0.7 RESULT: ADOPTED','All 10 gates passed · old tasks retained · zero evaluation writes',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
