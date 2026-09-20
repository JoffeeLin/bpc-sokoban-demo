#!/usr/bin/env python3
"""Render 12 frozen v0.18 gauge-average traces across four unseen D4 frames."""
import json,math,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_cross_generator_v17 import LabWorld,apply_slot,lab_raw,variable_expose
from bpc_cross_task_v07 import bit
from bpc_spatial_interface_v18 import GaugeAveragedPolicy,evaluate_spatial,spatial_expose
from bpc_three_factor_v12 import train

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v18spatial'
VIDEO=OUT/'bpc_spatial_gauge_v18_12_unseen_worlds.mp4';POSTER=OUT/'poster_v18_spatial_gauge.png'
FPS=30;BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85);INK=(232,240,255);MUTED=(136,157,189)
CYAN=(73,219,232);GOLD=(255,199,87);GREEN=(89,225,159);RED=(255,105,123);VIOLET=(177,137,255);ORANGE=(255,148,76)


def font(size,bold=False):return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)
def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)
def numbers(values):return ' '.join('×' if x is None else str(x) for x in values)


def board(draw,world,x,y,cell=25):
    for yy in range(world.h):
        for xx in range(world.w):
            i=yy*world.w+xx;x0,y0=x+xx*cell,y+yy*cell;wall=bit(world.walls,i);gate=bit(world.gates,i);mark=bit(world.marks,i);obj=bit(world.objects,i);switch=bit(world.switches,i)
            fill=(50,66,90) if wall else (89,48,62) if gate else (18,42,67);draw.rounded_rectangle((x0,y0,x0+cell-3,y0+cell-3),3,fill=fill,outline=ORANGE if gate else None)
            if switch and not wall:draw.rectangle((x0+6,y0+9,x0+cell-9,y0+cell-12),fill=VIOLET)
            if mark and not wall:draw.ellipse((x0+5,y0+5,x0+cell-8,y0+cell-8),outline=GOLD,width=3)
            if obj:draw.rounded_rectangle((x0+6,y0+6,x0+cell-9,y0+cell-9),3,fill=GREEN if mark else RED)
            if i==world.agent:draw.ellipse((x0+7,y0+7,x0+cell-10,y0+cell-10),fill=CYAN)


def panel(draw,rect,item,state,turn,learner):
    interface,index,sensors,channel,actions,gauges,kinds,spatial,change_compatible,compatible,initial,path=item;world,phase=state;x0,y0,x1,y1=rect
    draw.rounded_rectangle(rect,11,fill=PANEL,outline=LINE);label(draw,(x0+14,y0+10),f'UNSEEN WORLD {index:02d} · D4 FRAME T{spatial} · I/O {interface+1}',13,CYAN,True)
    board(draw,world,x0+14,y0+43);sx=x0+210;observed=spatial_expose(variable_expose(lab_raw(world),sensors,kinds,phase),len(sensors),spatial)
    hypotheses=[(row['transform'],tuple(row['mapping'])) for row in gauges];probability=GaugeAveragedPolicy(learner,channel,len(sensors),hypotheses,len(actions)).probabilities(observed);choice=path[turn] if turn<len(path) else None
    label(draw,(sx,y0+42),f'SENSOR {len(sensors)}  O→C  '+numbers(sensors),9,MUTED,True);label(draw,(sx,y0+59),'SELECT  C→O  '+numbers(channel),9,GREEN,True)
    label(draw,(sx,y0+77),f'ACTION {len(actions)}  O→C  '+numbers(actions),9,MUTED,True);label(draw,(sx,y0+94),'GAUGE PAIRS  8 / 8  · EQUAL PRIOR',9,GREEN,True)
    space=math.factorial(len(sensors))//math.factorial(len(sensors)-6);label(draw,(sx,y0+112),f'SENSOR SUPPORT  {space:,} → {change_compatible} → {compatible}',9,VIOLET,True)
    route=actions[choice] if choice is not None else None;status='SUCCESS' if world.marks==0 else ('READY' if choice is None else f'DIRECT O{choice} → '+('NOISE' if route is None else f'C{route}'))
    label(draw,(sx,y0+130),status,11,GREEN if status=='SUCCESS' else GOLD,True)
    for slot,value in enumerate(probability):
        yy=y0+153+slot*13;label(draw,(sx,yy),f'O{slot}',8,INK,True);draw.rounded_rectangle((sx+27,yy,sx+27+int(value*145),yy+7),3,fill=CYAN if slot==choice else (52,83,115));label(draw,(sx+180,yy-2),f'{value:.2f}',8,MUTED)


def frame(group,states,turn,learner):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image);label(draw,(22,16),'BPC SPATIAL GAUGE-CLASS TRANSFER v0.18',26,INK,True)
    label(draw,(22,52),'Unknown D4 frame · variable sensors/actions · direct probability averaging · no search',14,MUTED)
    rects=((18,82,620,338),(640,82,1262,338),(18,354,620,610),(640,354,1262,610))
    for slot,item in enumerate(group):panel(draw,rects[slot],item,states[slot],turn,learner)
    cards=(('GAUGE AVG','8,339'),('ORACLE','8,367'),('ML SINGLE','8,243'),('SHUFFLED','5,253'),('NO SPATIAL','4,170'),('RANDOM','900'))
    for i,(name,value) in enumerate(cards):
        x=18+i*207;draw.rounded_rectangle((x,626,x+195,680),8,fill=PANEL,outline=LINE);label(draw,(x+9,635),name,9,MUTED,True);label(draw,(x+9,652),value+' / 9,216',12,GREEN if i<3 else RED,True)
    label(draw,(18,698),'BOUNDARY: supplied D4 family, schema, statistics, generators + goals · frozen synthetic evidence · not AGI',11,MUTED)
    return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image);label(draw,(76,105),title,36,INK,True);label(draw,(79,164),subtitle,19,MUTED)
    draw.rounded_rectangle((79,225,1201,548),15,fill=PANEL,outline=LINE)
    rows=('4 NEW NON-IDENTITY D4 FRAMES · 4 NEW VARIABLE INTERFACES','32 / 32 GAUGE–ACTION PAIRS PHYSICALLY EQUIVALENT','128 / 128 INDEPENDENT-STREAM PAIRS AGREE','GAUGE AVERAGE  8,339 / 9,216  (90.5%)','ORACLE  8,367  ·  ML SINGLE  8,243','SHUFFLED PAIRS  5,253  ·  NO SPATIAL  4,170  ·  RANDOM  900')
    for i,row in enumerate(rows):label(draw,(112,250+i*46),row,17 if i<3 else 16,color,True)
    label(draw,(79,650),'48 unseen worlds · 2 action seeds · 0 overlap · 0 evaluation writes · all 12 gates passed',15,MUTED);return image


def main():
    result=json.loads((OUT/'result.json').read_text());assert result['adopted'];protocol=json.loads((ROOT/'protocol_v18_spatial.json').read_text());config=protocol['config']
    learner,events=train(config['train_seed']);assert events==result['training'] and learner.digest()==result['factor_digest'];suite=[]
    for row in json.loads((ROOT/'holdout_v18.json').read_text())['worlds']:
        suite.append((row['family'],LabWorld(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates']),row['shortest']))
    traces=[];bindings=[];seed=config['eval_seeds'][0]
    for sensors,actions,kinds,spatial,row in zip(config['sensor_routes'],config['action_routes'],config['distractor_kinds'],config['spatial_transforms'],result['calibration']['interfaces']):
        sensors=tuple(sensors);actions=tuple(actions);kinds=tuple(kinds);channel=tuple(row['channel_binding']['mapping']);gauges=row['gauge_bindings'];hypotheses=[(x['transform'],tuple(x['mapping'])) for x in gauges]
        policy={'gauge_average':GaugeAveragedPolicy(learner,channel,len(sensors),hypotheses,len(actions))};_,found=evaluate_spatial(policy,suite,sensors,actions,kinds,spatial,seed,config['episodes_per_map'],config['step_budget'])
        traces.append(found['gauge_average']);bindings.append((sensors,channel,actions,gauges,kinds,spatial,row['channel_binding']['change_compatible'],row['channel_binding']['compatible']))
    joint=[i for i,(family,_,_) in enumerate(suite) if family=='joint'];items=[]
    for group in range(3):
        for interface,(sensors,channel,actions,gauges,kinds,spatial,change_compatible,compatible) in enumerate(bindings):
            index=joint[group*4+interface];assert index in traces[interface];items.append((interface,index+1,sensors,channel,actions,gauges,kinds,spatial,change_compatible,compatible,suite[index][1],traces[interface][index]))
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC LEARNS A SPATIAL GAUGE CLASS','Unknown rotation/reflection + anonymous I/O · unlabeled transitions · no search')
    for _ in range(55):process.stdin.write(intro.tobytes())
    for start in range(0,12,4):
        group=items[start:start+4];states=[(item[10],0) for item in group];longest=max(len(item[11]) for item in group)
        for turn in range(longest+1):
            image=frame(group,states,turn,learner)
            for _ in range(2):process.stdin.write(image.tobytes())
            for slot,item in enumerate(group):
                if turn<len(item[11]):states[slot]=apply_slot(states[slot][0],states[slot][1],item[11][turn],item[4])
        for _ in range(18):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.18 RESULT: ADOPTED','Complete D4 gauge-action class · direct control · zero evaluation writes',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
