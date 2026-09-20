#!/usr/bin/env python3
"""Render 12 frozen v0.16 traces across four composite open interfaces."""
import json,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_composite_binding_v16 import CompositeBoundPolicy,composite_expose,evaluate_composite
from bpc_cross_task_v07 import bit
from bpc_open_interface_v15 import canonicalize_subset
from bpc_three_factor_v12 import World3,raw,step,train

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v16composite'
VIDEO=OUT/'bpc_composite_binding_v16_12_unseen_worlds.mp4';POSTER=OUT/'poster_v16_composite_binding.png'
FPS=30;BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85);INK=(232,240,255);MUTED=(136,157,189)
CYAN=(73,219,232);GOLD=(255,199,87);GREEN=(89,225,159);RED=(255,105,123);VIOLET=(177,137,255);ORANGE=(255,148,76)


def font(size,bold=False):return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)
def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)
def numbers(values):return ' '.join('×' if x is None else str(x) for x in values)


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


def panel(draw,rect,item,world,turn,learner):
    interface,index,sensors,channel,actuators,action,initial,path=item;x0,y0,x1,y1=rect
    draw.rounded_rectangle(rect,11,fill=PANEL,outline=LINE);label(draw,(x0+14,y0+10),f'UNSEEN WORLD {index:02d} · COMPOSITE I/O {interface+1}',13,CYAN,True)
    board(draw,world,x0+14,y0+43);sx=x0+210;observed=composite_expose(raw(world),sensors);canonical=canonicalize_subset(observed,channel,len(sensors))
    probability=CompositeBoundPolicy(learner,channel,len(sensors),action,len(actuators)).probabilities(observed);choice=path[turn] if turn<len(path) else None
    label(draw,(sx,y0+42),'SENSOR  O→C  '+numbers(sensors),10,MUTED,True)
    label(draw,(sx,y0+60),'SELECT  C→O  '+numbers(channel),10,GREEN,True)
    label(draw,(sx,y0+79),'ACTION  O→C  '+numbers(actuators),10,MUTED,True)
    label(draw,(sx,y0+97),'SELECT  C→O  '+numbers(action),10,GREEN,True)
    active=learner.active(canonical);label(draw,(sx,y0+116),'SUPPORT  20,160 → 4  ·  STREAMS 4/4',10,VIOLET,True)
    status='SUCCESS' if world.marks==0 else ('READY' if choice is None else f'DIRECT O{choice} → C{actuators[choice]}')
    label(draw,(sx,y0+135),status,11,GREEN if status=='SUCCESS' else GOLD,True)
    for slot,value in enumerate(probability):
        yy=y0+158+slot*16;label(draw,(sx,yy),f'O{slot}',8,INK,True)
        draw.rounded_rectangle((sx+27,yy,sx+27+int(value*160),yy+8),3,fill=CYAN if slot==choice else (52,83,115))
        label(draw,(sx+195,yy-2),f'{value:.2f}',8,MUTED)


def frame(group,states,turn,learner):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(22,16),'BPC COMPOSITE-INTERFACE BINDING v0.16',27,INK,True)
    label(draw,(22,52),'Reject displaced-XOR sensor distractors · bind unseen actions · frozen direct policy · no search',14,MUTED)
    rects=((18,82,620,338),(640,82,1262,338),(18,354,620,610),(640,354,1262,610))
    for slot,item in enumerate(group):panel(draw,rects[slot],item,states[slot],turn,learner)
    cards=(('LEARNED','1,844'),('ORACLE','1,844'),('SENSOR ONLY','169'),('ACTION ONLY','435'),('IDENTITY','161'),('RANDOM','125'))
    for i,(name,value) in enumerate(cards):
        x=18+i*207;draw.rounded_rectangle((x,626,x+195,680),8,fill=PANEL,outline=LINE);label(draw,(x+9,635),name,9,MUTED,True)
        label(draw,(x+9,652),value+' / 2,304',12,GREEN if i<2 else RED,True)
    label(draw,(18,698),'BOUNDARY: supplied composite formula + 4 calibration regimes · synthetic frozen evidence · not arbitrary grounding or AGI',11,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(76,115),title,37,INK,True);label(draw,(79,173),subtitle,19,MUTED)
    draw.rounded_rectangle((79,238,1201,538),15,fill=PANEL,outline=LINE)
    label(draw,(112,267),'4 / 4 UNSEEN COMPOSITE SENSOR INTERFACES RECOVERED',18,color,True)
    label(draw,(112,312),'16 / 16 UNLABELED STREAMS CHOSE THE ORACLE BASIS',18,color,True)
    label(draw,(112,357),'SUPPORT INVARIANCE: 20,160 ASSIGNMENTS → 4 BASES',18,color,True)
    label(draw,(112,402),'MULTI-REGIME PROBABILITIES SELECTED THE CORRECT BASIS',18,color,True)
    label(draw,(112,447),'LEARNED = ORACLE: 1,844 / 2,304 JOINT EPISODES',18,color,True)
    label(draw,(112,492),'SENSOR ONLY 169 · ACTION ONLY 435 · IDENTITY 161 · RANDOM 125',16,color,True)
    label(draw,(79,650),'48 unseen worlds · 2 action seeds · 0 overlap · 0 evaluation writes · all 16 gates passed',15,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text());assert result['adopted'];protocol=json.loads((ROOT/'protocol_v16_composite.json').read_text());config=protocol['config']
    learner,events=train(config['train_seed']);assert events==result['training'] and learner.digest()==result['factor_digest'];suite=[]
    for row in json.loads((ROOT/'holdout_v16.json').read_text())['worlds']:
        suite.append((row['family'],World3(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates']),row['shortest']))
    traces=[];bindings=[];seed=config['eval_seeds'][0]
    for sensors,actuators,row in zip(config['sensor_routes'],config['actuator_routes'],result['calibration']['interfaces']):
        sensors=tuple(sensors);actuators=tuple(actuators);channel=tuple(row['channel_binding']['mapping']);action=tuple(row['action_binding']['mapping'])
        policy={'learned':CompositeBoundPolicy(learner,channel,len(sensors),action,len(actuators))}
        _,found=evaluate_composite(policy,suite,sensors,actuators,seed,config['episodes_per_map'],config['step_budget'])
        traces.append(found['learned']);bindings.append((sensors,channel,actuators,action))
    joint=[i for i,(family,_,_) in enumerate(suite) if family=='joint'];items=[]
    for group in range(3):
        for interface,(sensors,channel,actuators,action) in enumerate(bindings):
            index=joint[group*4+interface];assert index in traces[interface]
            items.append((interface,index+1,sensors,channel,actuators,action,suite[index][1],traces[interface][index]))
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC REJECTS CAUSALLY COMPOSED DISTRACTORS','No labels · displaced-XOR planes · unseen sensor and actuator layouts')
    for _ in range(55):process.stdin.write(intro.tobytes())
    for start in range(0,12,4):
        group=items[start:start+4];states=[item[6] for item in group];longest=max(len(item[7]) for item in group)
        for turn in range(longest+1):
            image=frame(group,states,turn,learner)
            for _ in range(2):process.stdin.write(image.tobytes())
            for slot,item in enumerate(group):
                if turn<len(item[7]):
                    route=item[4][item[7][turn]]
                    if route is not None:states[slot]=step(states[slot],route)
        for _ in range(18):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.16 RESULT: ADOPTED','Support invariance + multi-regime probabilities · no runtime search',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
