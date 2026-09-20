#!/usr/bin/env python3
"""Render the twelve frozen v0.4 replays with an honest English UI."""
from __future__ import annotations

import json,pickle,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_learned_wave_v04 import ACTION_NAMES,parse,patch,patch_at,truth_step

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'artifacts'/'v04'
VIDEO=OUT/'bpc_learned_world_v04_12_unseen.mp4'; POSTER=OUT/'poster_v04.png'
FPS=30; ACTION_FRAMES=3; HOLD_FRAMES=12
NAMES={'L':'LEFT','R':'RIGHT','U':'UP','D':'DOWN'}
INK=(232,240,255); MUTED=(136,157,189); CYAN=(73,219,232); GOLD=(255,199,87)
GREEN=(89,225,159); RED=(255,105,123); BG=(7,16,30); PANEL=(13,26,45); LINE=(34,55,85)


def font(size,bold=False):
    name='Arial Bold.ttf' if bold else 'Arial.ttf'
    return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{name}',size)


def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)


def base():
    image=Image.new('RGB',(1280,720),BG); draw=ImageDraw.Draw(image)
    label(draw,(22,18),'BPC LEARNED-WORLD SOKOBAN v0.4',28,INK,True)
    label(draw,(22,58),'240,000 random raw interactions → 48 local transition rows → one frozen configuration wave',14,MUTED)
    for box in ((18,92,610,590),(630,92,1262,590)):
        draw.rounded_rectangle(box,12,fill=PANEL,outline=LINE,width=1)
    return image,draw


def board(draw,level,boxes,player):
    cell=min(50,400//max(level.h,level.w)); ox=42+(500-level.w*cell)//2; oy=156+(380-level.h*cell)//2
    for y in range(level.h):
        for x in range(level.w):
            i=y*level.w+x; x0,y0=ox+x*cell,oy+y*cell
            wall=(level.walls>>i)&1; goal=(level.goals>>i)&1; box=(boxes>>i)&1
            draw.rounded_rectangle((x0,y0,x0+cell-4,y0+cell-4),4,
                fill=(30,52,80) if wall else (15,32,54))
            if goal and not wall:
                c=(x0+cell//2-2,y0+cell//2-2); draw.ellipse((c[0]-9,c[1]-9,c[0]+9,c[1]+9),fill=GOLD)
                draw.ellipse((c[0]-4,c[1]-4,c[0]+4,c[1]+4),fill=(15,32,54))
            if box:
                color=GREEN if goal else RED; draw.rounded_rectangle((x0+9,y0+9,x0+cell-13,y0+cell-13),5,fill=color)
            if i==player:
                c=(x0+cell//2-2,y0+cell//2-2); draw.ellipse((c[0]-10,c[1]-10,c[0]+10,c[1]+10),fill=CYAN)


def cards(draw):
    values=(('LOCAL F_world','40,000 / 40,000'),('FROZEN HOLDOUT','12 / 12'),
            ('REMOVE THIRD CELL','0 / 12'),('UNSEEN 4-BOX','3 / 3'))
    for i,(name,value) in enumerate(values):
        x=18+i*311; draw.rounded_rectangle((x,607,x+297,674),9,fill=PANEL,outline=LINE,width=1)
        label(draw,(x+13,616),name,11,MUTED,True)
        label(draw,(x+13,638),value,18,RED if i==2 else GREEN,True)


def frame(level,boxes,player,index,item,action=None,before=None,probability=0.,pushes=0,solved=False):
    image,draw=base(); result=item['result']
    label(draw,(38,108),'LIVE TRUE-PHYSICS REPLAY',19,INK,True)
    label(draw,(38,137),'No solution action was supplied to learning or inference.',13,MUTED)
    board(draw,level,boxes,player)
    label(draw,(645,108),'LEARNED LOCAL WORLD QUERY',19,INK,True)
    label(draw,(645,139),'Three action-relative raw cells; exact probability counts.',13,MUTED)
    label(draw,(650,183),f'UNSEEN LEVEL H{index}/12',17,CYAN,True)
    label(draw,(970,183),f'{item["boxes"]} BOX' + ('ES' if item['boxes']>1 else ''),17,GOLD,True)
    draw.rounded_rectangle((650,224,1242,296),8,fill=(18,36,60))
    if before is None:
        label(draw,(668,238),'RAW QUERY',11,MUTED,True); label(draw,(668,258),'waiting for first action…',17,INK)
    else:
        bits='   '.join(f'{value:04b}' for value in before)
        label(draw,(668,238),'RAW CELL BITS: CURRENT · NEXT · BEYOND',11,MUTED,True)
        label(draw,(668,258),bits,19,INK,True)
    label(draw,(650,326),'FROZEN WAVE READOUT',13,MUTED,True)
    label(draw,(650,352),f'{result["states"]:,} macro states',23,INK,True)
    label(draw,(650,387),f'{result["push_phase"]} push phases',18,GOLD,True)
    label(draw,(650,432),'EXECUTED',12,MUTED,True)
    status='READY' if action is None else f'{NAMES[action]}'
    if action is not None:status+=f'  ·  P(F_world)={probability:.3f}'
    label(draw,(650,454),status,22,CYAN,True)
    label(draw,(650,493),f'PUSHES {pushes}/{result["push_phase"]}   ·   MODEL WRITES 0',16,GREEN,True)
    if solved:
        draw.rounded_rectangle((650,529,1242,570),8,fill=(20,70,58)); label(draw,(846,537),'SOLVED · REPLAY VERIFIED',18,GREEN,True)
    cards(draw)
    label(draw,(18,691),'BOUNDARY: learned local physics + supplied reachability compression/backward wave · not direct policy or AGI',12,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG); draw=ImageDraw.Draw(image)
    label(draw,(88,205),title,44,INK,True); label(draw,(90,274),subtitle,21,MUTED)
    draw.rounded_rectangle((90,340,1190,438),14,fill=PANEL,outline=LINE,width=1)
    label(draw,(120,365),'48 learned rows  ·  12/12 frozen maps  ·  3/3 unseen four-box  ·  0 eval writes',21,color,True)
    label(draw,(90,650),'Developer-frozen local holdout. Hybrid mechanism evidence, not an AGI claim.',15,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text()); maps=json.loads((ROOT/'holdout_v04.json').read_text())
    with (OUT/'model.pkl').open('rb') as file:model=pickle.load(file)
    items=[]
    for spec in maps:
        items.append({**spec,'result':result['conditions']['primary'][spec['id']]})
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s','1280x720','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','19',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('A LOCAL WORLD LAW LEARNED FROM EXPERIENCE','Then reused across unseen layouts and an unseen box count')
    for _ in range(45):process.stdin.write(intro.tobytes())
    for index,item in enumerate(items,1):
        level=parse(item['map']); boxes,player=level.boxes,level.player; pushes=0
        first=frame(level,boxes,player,index,item)
        for _ in range(HOLD_FRAMES):process.stdin.write(first.tobytes())
        for symbol in item['result']['sequence']:
            action=ACTION_NAMES.index(symbol); before=patch(level,boxes,player,action); origin=player
            nb,np=truth_step(level,boxes,player,action)
            after=patch_at(level,nb,np,origin,action); probability=model.probability(before,after)
            pushes+=nb!=boxes; boxes,player=nb,np
            image=frame(level,boxes,player,index,item,symbol,before,probability,pushes,boxes==level.goals)
            for _ in range(ACTION_FRAMES):process.stdin.write(image.tobytes())
        for _ in range(HOLD_FRAMES):process.stdin.write(image.tobytes())
    outro=splash('FROZEN RESULT: ADOPTED','All preregistered gates passed; the remaining scaffold is stated, not hidden',GREEN)
    POSTER.parent.mkdir(parents=True,exist_ok=True);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close(); code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
