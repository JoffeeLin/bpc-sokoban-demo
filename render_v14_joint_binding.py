#!/usr/bin/env python3
"""Render 12 frozen v0.14 traces across four dual-permuted interfaces."""
import json,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_channel_binding_v13 import canonicalize,permute_state
from bpc_cross_task_v07 import bit
from bpc_joint_binding_v14 import JointBoundPolicy,evaluate_joint
from bpc_three_factor_v12 import World3,raw,step,train

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v14joint'
VIDEO=OUT/'bpc_joint_binding_v14_12_unseen_worlds.mp4';POSTER=OUT/'poster_v14_joint_binding.png'
FPS=30;BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85);INK=(232,240,255);MUTED=(136,157,189)
CYAN=(73,219,232);GOLD=(255,199,87);GREEN=(89,225,159);RED=(255,105,123);VIOLET=(177,137,255);ORANGE=(255,148,76)


def font(size,bold=False):return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)
def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)
def numbers(values):return ' '.join(str(x) for x in values)


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
    interface,index,sensor,channel,actuator,action,initial,path=item;x0,y0,x1,y1=rect
    draw.rounded_rectangle(rect,11,fill=PANEL,outline=LINE);label(draw,(x0+14,y0+10),f'UNSEEN WORLD {index:02d} · INTERFACE {interface+1}',13,CYAN,True)
    board(draw,world,x0+14,y0+43);sx=x0+210;observed=permute_state(raw(world),sensor);canonical=canonicalize(observed,channel)
    probability=JointBoundPolicy(learner,channel,action).probabilities(observed);choice=path[turn] if turn<len(path) else None
    label(draw,(sx,y0+42),'SENSOR  OBS→CAN  '+numbers(sensor),10,MUTED,True)
    label(draw,(sx,y0+60),'LEARNED CAN→OBS  '+numbers(channel),10,GREEN,True)
    label(draw,(sx,y0+79),'ACTION  OBS→CAN  '+numbers(actuator),10,MUTED,True)
    label(draw,(sx,y0+97),'LEARNED CAN→OBS  '+numbers(action),10,GREEN,True)
    active=learner.active(canonical);label(draw,(sx,y0+117),'ACTIVE  '+(' × '.join('F'+''.join(map(str,x)) for x in active) or 'NONE'),11,VIOLET,True)
    status='SUCCESS' if world.marks==0 else ('READY' if choice is None else f'DIRECT SAMPLE O{choice} → C{actuator[choice]}')
    label(draw,(sx,y0+138),status,12,GREEN if status=='SUCCESS' else GOLD,True)
    for action_id,value in enumerate(probability):
        yy=y0+166+action_id*19;label(draw,(sx,yy),f'O{action_id}',9,INK,True)
        draw.rounded_rectangle((sx+28,yy,sx+28+int(value*165),yy+10),3,fill=CYAN if action_id==choice else (52,83,115))
        label(draw,(sx+202,yy-2),f'{value:.2f}',8,MUTED)


def frame(group,states,turn,learner):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(22,16),'BPC JOINT SENSOR + ACTUATOR BINDING v0.14',27,INK,True)
    label(draw,(22,52),'Unlabeled transitions recover both unseen interface orders · frozen direct policy · no search',14,MUTED)
    rects=((18,82,620,338),(640,82,1262,338),(18,354,620,610),(640,354,1262,610))
    for slot,item in enumerate(group):panel(draw,rects[slot],item,states[slot],turn,learner)
    cards=(('LEARNED','1,509'),('ORACLE','1,509'),('SENSOR ONLY','79'),('ACTION ONLY','297'),('NO BIND','222'),('RANDOM','144'))
    for i,(name,value) in enumerate(cards):
        x=18+i*207;draw.rounded_rectangle((x,626,x+195,680),8,fill=PANEL,outline=LINE);label(draw,(x+9,635),name,9,MUTED,True)
        label(draw,(x+9,652),value+' / 2,304',12,GREEN if i<2 else RED,True)
    label(draw,(18,698),'BOUNDARY: supplied 6×4 interface + calibration families · synthetic transfer · not arbitrary grounding or AGI',11,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image)
    label(draw,(76,132),title,39,INK,True);label(draw,(79,192),subtitle,20,MUTED)
    draw.rounded_rectangle((79,258,1201,520),15,fill=PANEL,outline=LINE)
    label(draw,(112,288),'4 / 4 UNSEEN SENSOR ORDERS RECOVERED',18,color,True)
    label(draw,(112,333),'4 / 4 UNSEEN ACTUATOR ORDERS RECOVERED',18,color,True)
    label(draw,(112,378),'LEARNED = ORACLE: 1,509 / 2,304 JOINT EPISODES',18,color,True)
    label(draw,(112,423),'SENSOR ONLY: 79 · ACTION ONLY: 297',18,color,True)
    label(draw,(112,468),'NO BIND: 222 · RANDOM: 144',18,color,True)
    label(draw,(79,650),'48 unseen worlds · 2 action seeds · 0 overlap · 0 evaluation writes',15,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text());assert result['adopted'];protocol=json.loads((ROOT/'protocol_v14_joint_binding.json').read_text());config=protocol['config']
    learner,events=train(config['train_seed']);assert events==result['training'] and learner.digest()==result['factor_digest'];suite=[]
    for row in json.loads((ROOT/'holdout_v14.json').read_text())['worlds']:
        suite.append((row['family'],World3(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates']),row['shortest']))
    traces=[];bindings=[];seed=config['eval_seeds'][0]
    for index,(sensor,actuator,row) in enumerate(zip(config['sensor_permutations'],config['actuator_permutations'],result['calibration']['interfaces'])):
        sensor=tuple(sensor);actuator=tuple(actuator);channel=tuple(row['channel_binding']['mapping']);action=tuple(row['action_binding']['mapping'])
        policy={'learned':JointBoundPolicy(learner,channel,action)};_,found=evaluate_joint(policy,suite,sensor,actuator,seed,config['episodes_per_map'],config['step_budget'])
        traces.append(found['learned']);bindings.append((sensor,channel,actuator,action))
    joint=[i for i,(family,_,_) in enumerate(suite) if family=='joint'];items=[]
    for group in range(3):
        for interface,(sensor,channel,actuator,action) in enumerate(bindings):
            index=joint[group*4+interface];assert index in traces[interface]
            items.append((interface,index+1,sensor,channel,actuator,action,suite[index][1],traces[interface][index]))
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC REBINDS BOTH SIDES OF AN UNSEEN INTERFACE','No labels · unseen sensor and actuator orders · unchanged direct policy')
    for _ in range(55):process.stdin.write(intro.tobytes())
    for start in range(0,12,4):
        group=items[start:start+4];states=[item[6] for item in group];longest=max(len(item[7]) for item in group)
        for turn in range(longest+1):
            image=frame(group,states,turn,learner)
            for _ in range(2):process.stdin.write(image.tobytes())
            for slot,item in enumerate(group):
                if turn<len(item[7]):states[slot]=step(states[slot],item[4][item[7][turn]])
        for _ in range(18):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.14 RESULT: ADOPTED','All 13 gates passed · bidirectional interface transfer · no runtime search',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
