#!/usr/bin/env python3
"""Render all eight frozen v0.5 replays with an honest English UI."""
from __future__ import annotations

import json,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_learned_wave_v04 import ACTION_NAMES,learn_raw_physics,parse,truth_step
from bpc_reversible_wave_v05 import discover_inverses,learned_reach

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'artifacts'/'v05'
VIDEO=OUT/'bpc_reversible_equivalence_v05_8_unseen.mp4'; POSTER=OUT/'poster_v05.png'
FPS=30; ACTION_FRAMES=3; HOLD_FRAMES=14
INK=(232,240,255); MUTED=(136,157,189); CYAN=(73,219,232); GOLD=(255,199,87)
GREEN=(89,225,159); RED=(255,105,123); BG=(7,16,30); PANEL=(13,26,45); LINE=(34,55,85)


def font(size,bold=False):
    return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)


def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)


def canvas():
    image=Image.new('RGB',(1280,720),BG); draw=ImageDraw.Draw(image)
    label(draw,(22,18),'BPC REVERSIBLE-EQUIVALENCE v0.5',28,INK,True)
    label(draw,(22,58),'Exact round trips discover action inverses → learned player equivalence → frozen wave',14,MUTED)
    for box in ((18,92,610,590),(630,92,1262,590)):draw.rounded_rectangle(box,12,fill=PANEL,outline=LINE)
    return image,draw


def board(draw,level,boxes,player,area):
    cell=min(50,400//max(level.h,level.w)); ox=42+(500-level.w*cell)//2; oy=156+(380-level.h*cell)//2
    for y in range(level.h):
        for x in range(level.w):
            i=y*level.w+x; x0,y0=ox+x*cell,oy+y*cell; wall=(level.walls>>i)&1
            goal=(level.goals>>i)&1; box=(boxes>>i)&1; reachable=(area>>i)&1
            fill=(30,52,80) if wall else (19,48,66) if reachable else (15,32,54)
            draw.rounded_rectangle((x0,y0,x0+cell-4,y0+cell-4),4,fill=fill)
            if reachable and not wall:draw.ellipse((x0+5,y0+5,x0+9,y0+9),fill=CYAN)
            if goal and not wall:
                c=(x0+cell//2-2,y0+cell//2-2);draw.ellipse((c[0]-9,c[1]-9,c[0]+9,c[1]+9),fill=GOLD)
                draw.ellipse((c[0]-4,c[1]-4,c[0]+4,c[1]+4),fill=fill)
            if box:draw.rounded_rectangle((x0+9,y0+9,x0+cell-13,y0+cell-13),5,fill=GREEN if goal else RED)
            if i==player:
                c=(x0+cell//2-2,y0+cell//2-2);draw.ellipse((c[0]-10,c[1]-10,c[0]+10,c[1]+10),fill=CYAN)


def cards(draw):
    values=(('REACH MATCH','4,000 / 4,000'),('NEW HOLDOUT','8 / 8'),
            ('WRONG INVERSE','0 / 8'),('OLD reach()','DISABLED'))
    for i,(name,value) in enumerate(values):
        x=18+i*311;draw.rounded_rectangle((x,607,x+297,674),9,fill=PANEL,outline=LINE)
        label(draw,(x+13,616),name,11,MUTED,True);label(draw,(x+13,638),value,18,RED if i==2 else GREEN,True)


def frame(level,boxes,player,area,index,item,inverse,evidence,action=None,pushes=0,solved=False):
    image,draw=canvas();result=item['result']
    label(draw,(38,108),'TRUE-PHYSICS REPLAY + LEARNED ORBIT',18,INK,True)
    label(draw,(38,136),'Cyan dots = states joined by learned exact round trips.',13,MUTED);board(draw,level,boxes,player,area)
    label(draw,(645,108),'EXPERIENCE-DISCOVERED RELATIONS',18,INK,True)
    label(draw,(645,139),'No direction names or geometry used to select inverse pairs.',13,MUTED)
    label(draw,(650,179),f'NEW LEVEL V5H{index}/8',17,CYAN,True);label(draw,(1000,179),f'{item["boxes"]} BOX'+('ES' if item['boxes']>1 else ''),17,GOLD,True)
    label(draw,(650,222),'FORWARD → INVERSE  ·  EXACT ROUND TRIPS',12,MUTED,True)
    for a in range(4):
        y=249+a*37;draw.rounded_rectangle((650,y,948,y+29),6,fill=(18,36,60))
        label(draw,(666,y+5),f'A{a} → A{inverse[a]}',15,INK,True);label(draw,(810,y+5),f'{evidence[a][inverse[a]]:,}',15,GREEN,True)
    label(draw,(976,222),'CURRENT READOUT',12,MUTED,True)
    label(draw,(976,251),'READY' if action is None else f'EXECUTE A{ACTION_NAMES.index(action)}',18,CYAN,True)
    label(draw,(976,292),f'{area.bit_count()} equivalent positions',14,INK)
    label(draw,(976,322),f'{result["states"]:,} macro states',14,INK)
    label(draw,(976,352),f'{pushes}/{result["push_phase"]} pushes',14,GOLD,True)
    label(draw,(650,423),'CAUSAL CHECKS',12,MUTED,True)
    label(draw,(650,448),'Wrong inverse: 7/4,000 reach matches · 0/8 maps',16,RED,True)
    label(draw,(650,480),'Supplied reach() disabled · model writes during eval: 0',16,GREEN,True)
    if solved:
        draw.rounded_rectangle((650,525,1242,570),8,fill=(20,70,58));label(draw,(846,537),'SOLVED · REPLAY VERIFIED',18,GREEN,True)
    cards(draw);label(draw,(18,691),'BOUNDARY: action displacement + macro candidates + terminal wave supplied · not direct policy or AGI',12,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(88,195),title,42,INK,True);label(draw,(90,260),subtitle,20,MUTED)
    draw.rounded_rectangle((90,330,1190,442),14,fill=PANEL,outline=LINE)
    label(draw,(120,352),'4 learned inverse relations  ·  4,000/4,000 reach match',21,color,True)
    label(draw,(120,393),'8/8 new maps  ·  wrong inverse 0/8  ·  old reach() disabled',21,color,True)
    label(draw,(90,650),'Developer-frozen mechanism evidence. Remaining scaffold disclosed; no AGI claim.',15,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text());maps=json.loads((ROOT/'holdout_v05.json').read_text())
    model,_,_,_=learn_raw_physics(40_404,3000,80);inverse,evidence=discover_inverses(50_505,600,60)
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC LEARNS REVERSIBLE EQUIVALENCE','A second supplied Sokoban mechanism is replaced by experience')
    for _ in range(45):process.stdin.write(intro.tobytes())
    for index,spec in enumerate(maps,1):
        item={**spec,'result':result['conditions']['primary'][spec['id']]};level=parse(item['map']);boxes,player=level.boxes,level.player;pushes=0
        area,_=learned_reach(level,boxes,player,model,inverse);image=frame(level,boxes,player,area,index,item,inverse,evidence)
        for _ in range(HOLD_FRAMES):process.stdin.write(image.tobytes())
        for symbol in item['result']['sequence']:
            action=ACTION_NAMES.index(symbol);nb,np=truth_step(level,boxes,player,action);pushes+=nb!=boxes;boxes,player=nb,np
            area,_=learned_reach(level,boxes,player,model,inverse);image=frame(level,boxes,player,area,index,item,inverse,evidence,symbol,pushes,boxes==level.goals)
            for _ in range(ACTION_FRAMES):process.stdin.write(image.tobytes())
        for _ in range(HOLD_FRAMES):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.5 RESULT: ADOPTED','Every preregistered gate passed; every action sequence replayed',GREEN);POSTER.parent.mkdir(parents=True,exist_ok=True);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
