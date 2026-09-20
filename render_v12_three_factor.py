#!/usr/bin/env python3
"""Render 12 frozen unseen joint traces for BPC v0.12."""
import json,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_cross_task_v07 import bit
from bpc_three_factor_v12 import (FieldPolicy,ProductPolicy,SharedPolicy,UniformPolicy,World3,
    evaluate,raw,step,train)

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v12three'
VIDEO=OUT/'bpc_three_factor_v12_12_unseen_joint_worlds.mp4';POSTER=OUT/'poster_v12_three_factor.png'
FPS=30;BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85);INK=(232,240,255);MUTED=(136,157,189)
CYAN=(73,219,232);GOLD=(255,199,87);GREEN=(89,225,159);RED=(255,105,123);VIOLET=(177,137,255);ORANGE=(255,148,76)


def font(size,bold=False):return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)
def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)


def board(draw,world,x,y,cell=25):
    for yy in range(world.h):
        for xx in range(world.w):
            i=yy*world.w+xx;x0,y0=x+xx*cell,y+yy*cell
            wall=bit(world.walls,i);gate=bit(world.gates,i);mark=bit(world.marks,i);obj=bit(world.objects,i);switch=bit(world.switches,i)
            fill=(50,66,90) if wall else (89,48,62) if gate else (18,42,67)
            draw.rounded_rectangle((x0,y0,x0+cell-3,y0+cell-3),3,fill=fill,outline=ORANGE if gate else None)
            if switch and not wall:draw.rectangle((x0+6,y0+9,x0+cell-9,y0+cell-12),fill=VIOLET)
            if mark and not wall:draw.ellipse((x0+5,y0+5,x0+cell-8,y0+cell-8),outline=GOLD,width=3)
            if obj:draw.rounded_rectangle((x0+6,y0+6,x0+cell-9,y0+cell-9),3,fill=GREEN if mark else RED)
            if i==world.agent:draw.ellipse((x0+7,y0+7,x0+cell-10,y0+cell-10),fill=CYAN)


def panel(draw,rect,item,world,turn,learner,policy):
    index,initial,distance,path=item;x0,y0,x1,y1=rect;draw.rounded_rectangle(rect,11,fill=PANEL,outline=LINE)
    label(draw,(x0+14,y0+10),f'UNSEEN JOINT {index:02d} · d={distance}',13,CYAN,True);board(draw,world,x0+14,y0+43)
    sx=x0+210;state=raw(world);active=learner.active(state);probability=policy.probabilities(state);action=path[turn] if turn<len(path) else None
    label(draw,(sx,y0+47),'INPUT: 7×7×6 RAW BITS',11,MUTED,True)
    label(draw,(sx,y0+68),'ACTIVE  '+(' × '.join('F'+''.join(map(str,x)) for x in active) or 'NONE'),14,VIOLET,True)
    status='SUCCESS' if world.marks==0 else ('READY' if action is None else f'DIRECT SAMPLE A{action}')
    label(draw,(sx,y0+94),status,15,GREEN if status=='SUCCESS' else GOLD,True)
    for action_id,value in enumerate(probability):
        yy=y0+126+action_id*25;label(draw,(sx,yy+1),f'A{action_id}',11,INK,True)
        draw.rounded_rectangle((sx+32,yy,sx+32+int(value*236),yy+14),4,fill=CYAN if action_id==action else (52,83,115))
        label(draw,(sx+276,yy),f'{value:.2f}',10,MUTED)


def frame(group,states,turn,learner,policy):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(22,16),'BPC THREE-FACTOR RECOMBINATION v0.12',27,INK,True)
    label(draw,(22,52),'Separate experience only · unseen worlds require switch + gate + box + target · no planner/search',14,MUTED)
    rects=((18,82,620,338),(640,82,1262,338),(18,354,620,610),(640,354,1262,610))
    for slot,item in enumerate(group):panel(draw,rects[slot],item,states[slot],turn,learner,policy)
    cards=(('BPC FIELD','574 / 768'),('PRODUCT','574 / 768'),('SHARED','437 / 768'),('RANDOM','139 / 768'),('ROTATED','6 / 768'))
    for i,(name,value) in enumerate(cards):
        x=18+i*249;draw.rounded_rectangle((x,626,x+235,680),8,fill=PANEL,outline=LINE);label(draw,(x+10,635),name,10,MUTED,True)
        label(draw,(x+10,652),value,14,GREEN if i<2 else RED if i>2 else INK,True)
    label(draw,(18,698),'BOUNDARY: raw channels + terminal events + additive field rule supplied · frozen synthetic control · not AGI',11,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(76,140),title,39,INK,True);label(draw,(79,200),subtitle,20,MUTED)
    draw.rounded_rectangle((79,270,1201,510),15,fill=PANEL,outline=LINE)
    label(draw,(112,301),'DISCOVERED RAW FACTORS: Δ(1,2) · Δ(1,3) · Δ(1,4,5)',18,color,True)
    label(draw,(112,350),'FROZEN JOINT: 574 / 768 = 74.7% · PRODUCT: 574 / 768',18,color,True)
    label(draw,(112,399),'DROP EACH FACTOR: 474 · 297 · 487 / 768',18,color,True)
    label(draw,(112,448),'SHARED: 437 · RANDOM: 139 · ROTATED: 6 / 768',18,color,True)
    label(draw,(79,650),'48 unseen worlds · 2 action seeds · 0 overlap · 0 evaluation writes',15,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text());assert result['adopted'];protocol=json.loads((ROOT/'protocol_v12_three_factor.json').read_text())
    config=protocol['config'];learner,events=train(config['train_seed'],config['uniform_episodes'],config['guided_rounds'],config['guided_episodes'],config['train_steps'])
    assert events==result['training'] and learner.digest()==result['factor_digest'];data=json.loads((ROOT/'holdout_v12.json').read_text());suite=[]
    for row in data['worlds']:
        suite.append((row['family'],World3(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates']),row['shortest']))
    policies={'field':FieldPolicy(learner),'product':ProductPolicy(learner),'shared':SharedPolicy(learner),
        'drop_0':FieldPolicy(learner,drop=(0,)),'drop_1':FieldPolicy(learner,drop=(1,)),'drop_2':FieldPolicy(learner,drop=(2,)),
        'rotated':FieldPolicy(learner,rotated=True),'uniform':UniformPolicy()}
    condition,traces=evaluate(policies,suite,config['eval_seeds'][0],config['episodes_per_map'],64)
    assert condition==result['conditions'][str(config['eval_seeds'][0])]['64']
    chosen=[i for i,(family,_,_) in enumerate(suite) if family=='joint'];assert len(chosen)==12 and all(i in traces['field'] for i in chosen)
    items=[(i+1,suite[i][1],suite[i][2],traces['field'][i]) for i in chosen];policy=policies['field']
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('THREE LEARNED FACTORS, ONE DIRECT POLICY','No joint-task training · 12 frozen unseen joint worlds')
    for _ in range(55):process.stdin.write(intro.tobytes())
    for start in range(0,12,4):
        group=items[start:start+4];states=[item[1] for item in group];longest=max(len(item[3]) for item in group)
        for turn in range(longest+1):
            image=frame(group,states,turn,learner,policy)
            for _ in range(2):process.stdin.write(image.tobytes())
            for slot,item in enumerate(group):
                if turn<len(item[3]):states[slot]=step(states[slot],item[3][turn])
        for _ in range(18):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.12 RESULT: ADOPTED','All 13 gates passed · direct recombination · no runtime search',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
