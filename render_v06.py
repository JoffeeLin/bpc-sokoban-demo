#!/usr/bin/env python3
"""Render all eight frozen v0.6.1 replays with an honest English UI."""
from __future__ import annotations

import json,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_learned_geometry_v06 import learn_push_templates
from bpc_learned_wave_v04 import ACTION_NAMES,learn_raw_physics,parse,truth_step
from bpc_reversible_wave_v05 import discover_inverses,learned_reach

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v061'
VIDEO=OUT/'bpc_learned_geometry_v06_8_unseen.mp4';POSTER=OUT/'poster_v06.png'
FPS=30;ACTION_FRAMES=3;HOLD_FRAMES=14
INK=(232,240,255);MUTED=(136,157,189);CYAN=(73,219,232);GOLD=(255,199,87)
GREEN=(89,225,159);RED=(255,105,123);BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85)


def font(size,bold=False):
    return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)


def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)


def canvas():
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(22,18),'BPC LEARNED MACRO GEOMETRY v0.6',28,INK,True)
    label(draw,(22,58),'Random push deltas → anonymous action templates → frozen reversible wave',14,MUTED)
    for box in ((18,92,610,590),(630,92,1262,590)):draw.rounded_rectangle(box,12,fill=PANEL,outline=LINE)
    return image,draw


def board(draw,level,boxes,player,area):
    cell=min(50,400//max(level.h,level.w));ox=42+(500-level.w*cell)//2;oy=156+(380-level.h*cell)//2
    for y in range(level.h):
        for x in range(level.w):
            i=y*level.w+x;x0,y0=ox+x*cell,oy+y*cell;wall=(level.walls>>i)&1
            goal=(level.goals>>i)&1;box=(boxes>>i)&1;reachable=(area>>i)&1
            fill=(30,52,80) if wall else (19,48,66) if reachable else (15,32,54)
            draw.rounded_rectangle((x0,y0,x0+cell-4,y0+cell-4),4,fill=fill)
            if reachable and not wall:draw.ellipse((x0+5,y0+5,x0+9,y0+9),fill=CYAN)
            if goal and not wall:
                c=(x0+cell//2-2,y0+cell//2-2);draw.ellipse((c[0]-9,c[1]-9,c[0]+9,c[1]+9),fill=GOLD)
                draw.ellipse((c[0]-4,c[1]-4,c[0]+4,c[1]+4),fill=fill)
            if box:draw.rounded_rectangle((x0+9,y0+9,x0+cell-13,y0+cell-13),5,fill=GREEN if goal else RED)
            if i==player:
                c=(x0+cell//2-2,y0+cell//2-2);draw.ellipse((c[0]-10,c[1]-10,c[0]+10,c[1]+10),fill=CYAN)


def vec(value):return f'({value[0]:+d},{value[1]:+d})'


def cards(draw):
    values=(('TEMPLATE AUDIT','1,443 / 1,443'),('NEW HOLDOUT','8 / 8'),
            ('ROTATED TEMPLATE','0 / 8'),('MANUAL MACRO VECTORS','NONE'))
    for i,(name,value) in enumerate(values):
        x=18+i*311;draw.rounded_rectangle((x,607,x+297,674),9,fill=PANEL,outline=LINE)
        label(draw,(x+13,616),name,11,MUTED,True);label(draw,(x+13,638),value,18,RED if i==2 else GREEN,True)


def frame(level,boxes,player,area,index,item,templates,evidence,action=None,pushes=0,solved=False):
    image,draw=canvas();result=item['result']
    label(draw,(38,108),'TRUE-PHYSICS REPLAY + LEARNED ORBIT',18,INK,True)
    label(draw,(38,136),'No holdout solution action entered learning or inference.',13,MUTED);board(draw,level,boxes,player,area)
    label(draw,(645,108),'LEARNED ANONYMOUS PUSH TEMPLATES',18,INK,True)
    label(draw,(645,139),'Prior-player relative deltas; no macro action vectors in solver.',13,MUTED)
    label(draw,(650,179),f'NEW LEVEL V6H{index}/8',17,CYAN,True);label(draw,(1000,179),f'{item["boxes"]} BOX'+('ES' if item['boxes']>1 else ''),17,GOLD,True)
    label(draw,(650,222),'ACTION  REMOVED   ADDED     NEXT      SUPPORT',12,MUTED,True)
    for a,(removed,added,next_player) in enumerate(templates):
        y=249+a*37;draw.rounded_rectangle((650,y,1138,y+29),6,fill=(18,36,60))
        label(draw,(665,y+5),f'A{a}',15,INK,True);label(draw,(735,y+5),vec(removed),15,CYAN,True)
        label(draw,(840,y+5),vec(added),15,CYAN,True);label(draw,(945,y+5),vec(next_player),15,CYAN,True)
        label(draw,(1050,y+5),f'{evidence[a][0]["count"]:,}',15,GREEN,True)
    label(draw,(650,416),'CURRENT FROZEN READOUT',12,MUTED,True)
    status='READY' if action is None else f'EXECUTE A{ACTION_NAMES.index(action)}'
    label(draw,(650,441),status,18,CYAN,True);label(draw,(945,441),f'{area.bit_count()} equivalent positions',14,INK)
    label(draw,(650,478),f'{result["states"]:,} macro states',15,INK);label(draw,(945,478),f'{pushes}/{result["push_phase"]} pushes',15,GOLD,True)
    label(draw,(650,511),'Rotated templates: 0/1,443 audit · 0/8 maps',15,RED,True)
    if solved:
        draw.rounded_rectangle((650,543,1242,575),8,fill=(20,70,58));label(draw,(846,548),'SOLVED · REPLAY VERIFIED',18,GREEN,True)
    cards(draw);label(draw,(18,691),'BOUNDARY: local addressing + terminal seed + backward wave supplied · not cross-task or AGI',12,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(88,195),title,42,INK,True);label(draw,(90,260),subtitle,20,MUTED)
    draw.rounded_rectangle((90,330,1190,442),14,fill=PANEL,outline=LINE)
    label(draw,(120,352),'4 unique learned templates  ·  1,443/1,443 push audit',21,color,True)
    label(draw,(120,393),'8/8 new maps  ·  rotated templates 0/8  ·  zero eval writes',21,color,True)
    label(draw,(90,650),'Developer-frozen mechanism evidence. Preserved v0.6 runner failure; not AGI.',15,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text());maps=json.loads((ROOT/'holdout_v06.json').read_text())
    model,_,_,_=learn_raw_physics(40_404,3000,80);inverse,_=discover_inverses(50_505,600,60)
    templates,evidence,_=learn_push_templates(60_606,3000,80)
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC LEARNS MACRO PUSH GEOMETRY','A third supplied Sokoban mechanism is replaced by interaction')
    for _ in range(45):process.stdin.write(intro.tobytes())
    for index,spec in enumerate(maps,1):
        item={**spec,'result':result['conditions']['primary'][spec['id']]};level=parse(item['map']);boxes,player=level.boxes,level.player;pushes=0
        area,_=learned_reach(level,boxes,player,model,inverse);image=frame(level,boxes,player,area,index,item,templates,evidence)
        for _ in range(HOLD_FRAMES):process.stdin.write(image.tobytes())
        for symbol in item['result']['sequence']:
            action=ACTION_NAMES.index(symbol);nb,np=truth_step(level,boxes,player,action);pushes+=nb!=boxes;boxes,player=nb,np
            area,_=learned_reach(level,boxes,player,model,inverse);image=frame(level,boxes,player,area,index,item,templates,evidence,symbol,pushes,boxes==level.goals)
            for _ in range(ACTION_FRAMES):process.stdin.write(image.tobytes())
        for _ in range(HOLD_FRAMES):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.6.1 RESULT: ADOPTED','All preregistered gates passed; every action sequence replayed',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
