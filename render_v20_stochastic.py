#!/usr/bin/env python3
"""Render 12 frozen v0.20 traces with visible stochastic actuator effects."""
import json,math,random,subprocess
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_cross_generator_v17 import LabWorld,done,lab_step
from bpc_cross_task_v07 import bit
from bpc_direct_composition_v09 import choose
from bpc_stochastic_interface_v20 import StochasticGaugePolicy,sample
from bpc_temporal_interface_v19 import temporal_observation
from bpc_three_factor_v12 import train

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v20stochastic';VIDEO=OUT/'bpc_stochastic_channel_v20_12_unseen_worlds.mp4';POSTER=OUT/'poster_v20_stochastic_channel.png'
FPS=30;BG=(7,16,30);PANEL=(13,26,45);LINE=(34,55,85);INK=(232,240,255);MUTED=(136,157,189);CYAN=(73,219,232);GOLD=(255,199,87);GREEN=(89,225,159);RED=(255,105,123);VIOLET=(177,137,255)


def font(size,bold=False):return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{"Arial Bold.ttf" if bold else "Arial.ttf"}',size)
def label(draw,xy,value,size,color=INK,bold=False):draw.text(xy,value,font=font(size,bold),fill=color)
def numbers(values):return ' '.join('×' if x is None else str(x) for x in values)


def board(draw,world,x,y,cell=25):
    for yy in range(world.h):
        for xx in range(world.w):
            i=yy*world.w+xx;x0,y0=x+xx*cell,y+yy*cell;wall=bit(world.walls,i);gate=bit(world.gates,i);mark=bit(world.marks,i);obj=bit(world.objects,i);switch=bit(world.switches,i)
            fill=(50,66,90) if wall else (89,48,62) if gate else (18,42,67);draw.rounded_rectangle((x0,y0,x0+cell-3,y0+cell-3),3,fill=fill)
            if switch and not wall:draw.rectangle((x0+6,y0+9,x0+cell-9,y0+cell-12),fill=VIOLET)
            if mark and not wall:draw.ellipse((x0+5,y0+5,x0+cell-8,y0+cell-8),outline=GOLD,width=3)
            if obj:draw.rounded_rectangle((x0+6,y0+6,x0+cell-9,y0+cell-9),3,fill=GREEN if mark else RED)
            if i==world.agent:draw.ellipse((x0+7,y0+7,x0+cell-10,y0+cell-10),fill=CYAN)


def step(world,phase,queue,issued,channels,rng,delay):
    queue.append(issued)
    if len(queue)<=delay:return world,phase,None,None
    executed=queue.pop(0);row=channels[executed]
    if row is None:
        mode=sum(x is None for x in channels[:executed]);return world,phase^(1<<mode),executed,None
    effect=sample(row,rng);return lab_step(world,effect),phase,executed,effect


def find_trace(policy,family,initial,index,sensors,channels,kinds,spatial,sensor_delay,actuator_delay,seed,episodes,steps):
    for episode in range(episodes):
        base=seed+index*100000+episode;action_rng=random.Random(base);effect_rng=random.Random(base+900000001);world=initial;phase=0;queue=[];history=[(world,phase)];events=[]
        for _ in range(steps):
            observed=temporal_observation(history,sensor_delay,sensors,kinds,spatial);probability=policy.probabilities(observed);issued=choose(probability,action_rng)
            world,phase,executed,effect=step(world,phase,queue,issued,channels,effect_rng,actuator_delay);history.append((world,phase));events.append({'world':world,'probability':probability,'issued':issued,'executed':executed,'effect':effect})
            if done(family,initial,world):return events
    return None


def panel(draw,rect,item,turn):
    interface,index,sensors,channels,kinds,spatial,sensor_delay,actuator_delay,lag,initial,events,learned_rows=item;x0,y0,x1,y1=rect
    world=initial if turn==0 else events[min(turn,len(events))-1]['world'];event=events[turn] if turn<len(events) else None
    draw.rounded_rectangle(rect,11,fill=PANEL,outline=LINE);label(draw,(x0+14,y0+10),f'WORLD {index:02d} · L{lag}=S{sensor_delay}+A{actuator_delay} · D4 T{spatial} · I/O {interface+1}',12,CYAN,True);board(draw,world,x0+14,y0+43)
    sx=x0+210;label(draw,(sx,y0+42),f'SENSOR {len(sensors)}  O→C  '+numbers(sensors),9,MUTED,True);label(draw,(sx,y0+60),f'ACTUATOR {len(channels)} · LEARNED STOCHASTIC ROWS',9,GREEN,True)
    for slot,row in enumerate(learned_rows):
        yy=y0+70+slot*13;dominant=max(range(5),key=lambda i:row[i]);text='NUISANCE' if dominant==4 else ' '.join(f'{x:.2f}' for x in row[:4]);label(draw,(sx,yy),f'O{slot}  {text}',8,VIOLET if dominant==4 else MUTED,dominant<4)
    if event:
        effect='WAIT' if event['executed'] is None else 'NUISANCE' if event['effect'] is None else f'C{event["effect"]}'
        status=f'ISSUE O{event["issued"]} · EXEC {effect}'
    else:status='SUCCESS'
    label(draw,(sx,y0+177),status,10,GREEN if status=='SUCCESS' else GOLD,True)
    probability=event['probability'] if event else events[-1]['probability']
    for slot,value in enumerate(probability):
        yy=y0+198+slot*8;label(draw,(sx,yy),f'O{slot}',7,INK,True);draw.rounded_rectangle((sx+24,yy,sx+24+int(value*130),yy+5),2,fill=CYAN);label(draw,(sx+162,yy-2),f'{value:.2f}',7,MUTED)


def frame(group,turn):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image);label(draw,(22,16),'BPC STOCHASTIC ACTUATOR GAUGE TRANSFER v0.20',26,INK,True);label(draw,(22,52),'Unknown probability channel + delay + D4 + anonymous I/O · direct control · no search',14,MUTED)
    rects=((18,82,620,338),(640,82,1262,338),(18,354,620,610),(640,354,1262,610))
    for slot,item in enumerate(group):panel(draw,rects[slot],item,turn)
    cards=(('LEARNED','3,875'),('ORACLE','3,871'),('ARGMAX','4,179'),('IDENTITY','2,480'),('SHUFFLED','1,569'))
    for i,(name,value) in enumerate(cards):
        x=18+i*248;draw.rounded_rectangle((x,626,x+235,680),8,fill=PANEL,outline=LINE);label(draw,(x+9,635),name,9,MUTED,True);label(draw,(x+9,652),value+' / 4,608',12,GREEN if i<3 else RED,True)
    label(draw,(18,698),'BOUNDARY: supplied 4-effect channel + lag 0–4 + D4 families · frozen synthetic evidence · not AGI',11,MUTED);return image


def splash(title,subtitle,color=CYAN):
    image=Image.new('RGB',(1280,720),BG);draw=ImageDraw.Draw(image);label(draw,(76,105),title,35,INK,True);label(draw,(79,164),subtitle,19,MUTED);draw.rounded_rectangle((79,225,1201,548),15,fill=PANEL,outline=LINE)
    rows=('4 / 4 UNSEEN TOTAL LAGS · 12 / 12 STREAM LAGS','MAX CHANNEL ERROR  2.58% · STREAM  4.15%','LEARNED  3,875 / 4,608  (84.1%)','ORACLE  3,871 · IDENTITY  2,480 · SHUFFLED  1,569','ARGMAX CONTROL  4,179 — FULL CHANNEL DID NOT WIN')
    for i,row in enumerate(rows):label(draw,(112,252+i*53),row,17,color if i<4 else GOLD,True)
    label(draw,(79,650),'48 unseen worlds · 2 action/effect seeds · 0 overlap · 0 evaluation writes · all 13 gates passed',15,MUTED);return image


def main():
    result=json.loads((OUT/'result.json').read_text());assert result['adopted'];protocol=json.loads((ROOT/'protocol_v20_stochastic.json').read_text());config=protocol['config'];learner,events=train(config['train_seed']);assert events==result['training'] and learner.digest()==result['factor_digest'];suite=[]
    for row in json.loads((ROOT/'holdout_v20.json').read_text())['worlds']:suite.append((row['family'],LabWorld(row['h'],row['w'],row['walls'],row['agent'],row['objects'],row['marks'],row['switches'],row['gates']),row['shortest']))
    items=[];seed=config['eval_seeds'][0]
    for interface,(sensors,channels,kinds,spatial,delays,binding) in enumerate(zip(config['sensor_routes'],config['stochastic_channels'],config['distractor_kinds'],config['spatial_transforms'],config['temporal_delays'],result['calibration']['interfaces'])):
        sensors=tuple(sensors);channels=tuple(tuple(x) if x else None for x in channels);kinds=tuple(kinds);sensor_delay,actuator_delay=delays;gauges=binding['stochastic_binding']['gauges'];policy=StochasticGaugePolicy(learner,binding['sensor_binding']['mapping'],len(sensors),gauges,len(channels));actual_rows=next(x['rows'] for x in gauges if x['transform']==spatial);found=[]
        for index,(family,initial,_) in enumerate(suite):
            if family!='joint':continue
            events=find_trace(policy,family,initial,index,sensors,channels,kinds,spatial,sensor_delay,actuator_delay,seed,config['episodes_per_map'],config['step_budget'])
            if events:found.append((interface,index+1,sensors,channels,kinds,spatial,sensor_delay,actuator_delay,binding['stochastic_binding']['lag'],initial,events,actual_rows))
            if len(found)==3:break
        assert len(found)==3;items.extend(found)
    items=[items[i*3+group] for group in range(3) for i in range(4)]
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO)],stdin=subprocess.PIPE)
    intro=splash('BPC LEARNS A STOCHASTIC ACTUATOR CHANNEL','Unseen probability matrix + temporal/D4 gauge + anonymous I/O · unlabeled transitions')
    for _ in range(55):process.stdin.write(intro.tobytes())
    for start in range(0,12,4):
        group=items[start:start+4];longest=max(len(x[10]) for x in group)
        for turn in range(longest+1):
            image=frame(group,turn)
            for _ in range(2):process.stdin.write(image.tobytes())
        for _ in range(18):process.stdin.write(image.tobytes())
    outro=splash('FROZEN v0.20 RESULT: ADOPTED','Probability-channel recovery + preserved direct control · zero evaluation writes',GREEN);outro.save(POSTER)
    for _ in range(60):process.stdin.write(outro.tobytes())
    process.stdin.close();code=process.wait()
    if code:raise SystemExit(code)
    print(VIDEO);print(POSTER)


if __name__=='__main__':main()
