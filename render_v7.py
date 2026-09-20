#!/usr/bin/env python3
"""Render the ten pre-registered first-success traces to an English MP4."""
from __future__ import annotations

import json, subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import bpc_sokoban as game

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'artifacts'/'v7'
W,H,FPS=1280,720,30
BG=(7,15,29); PANEL=(13,27,47); WHITE=(232,240,252); MUTED=(142,164,192)
CYAN=(55,214,228); GREEN=(75,222,150); GOLD=(255,197,80); RED=(255,99,119)
ACTIONS=('UP','RIGHT','DOWN','LEFT')


def font(size,bold=False):
    name='Arial Bold.ttf' if bold else 'Arial.ttf'
    return ImageFont.truetype(f'/System/Library/Fonts/Supplemental/{name}',size)


def label(draw,xy,value,size,color=WHITE,bold=False): draw.text(xy,value,font=font(size,bold),fill=color)


def base_frame(): return Image.new('RGB',(W,H),BG)


def board(draw,level,player,box):
    ox,oy,cell=52,102,58
    for y,row in enumerate(level):
        for x,value in enumerate(row):
            p=(ox+x*cell,oy+y*cell,ox+(x+1)*cell-3,oy+(y+1)*cell-3)
            wall=value=='#'; draw.rounded_rectangle(p,8,fill=(28,48,74) if wall else (12,28,48))
            if value=='G':
                cx,cy=ox+x*cell+cell//2,oy+y*cell+cell//2
                draw.ellipse((cx-10,cy-10,cx+10,cy+10),outline=GOLD,width=4)
    gx=next((x,y) for y,row in enumerate(level) for x,v in enumerate(row) if v=='G')
    bx,by=box; px,py=player
    color=GREEN if box==gx else RED
    draw.rounded_rectangle((ox+bx*cell+10,oy+by*cell+10,ox+(bx+1)*cell-13,oy+(by+1)*cell-13),8,fill=color)
    cx,cy=ox+px*cell+cell//2-2,oy+py*cell+cell//2-2
    draw.ellipse((cx-16,cy-16,cx+16,cy+16),fill=CYAN)


def bar(draw,y,name,value,selected=False,color=CYAN):
    label(draw,(700,y),name,22,GOLD if selected else WHITE,selected)
    draw.rounded_rectangle((790,y+3,1125,y+23),10,fill=(29,48,72))
    draw.rounded_rectangle((790,y+3,790+335*value,y+23),10,fill=color)
    label(draw,(1142,y-1),f'{value:5.1%}',20,MUTED)


def trace_frame(level,level_index,frame,episode,step,total,result,after=False):
    image=base_frame(); draw=ImageDraw.Draw(image)
    label(draw,(48,30),'BPC SOKOBAN  •  FROZEN UNSEEN LAYOUT',24,CYAN,True)
    label(draw,(995,30),f'LEVEL {level_index}/10',24,WHITE,True)
    board(draw,level,tuple(frame['after_player'] if after else frame['player']),
          tuple(frame['after_box'] if after else frame['box']))
    label(draw,(700,100),'TYPED CHOICE',18,CYAN,True)
    for action,value in enumerate(frame['choice']):
        bar(draw,140+action*45,ACTIONS[action],value,action==frame['action'])
    label(draw,(700,345),'INDEPENDENT P(FRAME CHANGES)',18,CYAN,True)
    for action,value in enumerate(frame['change_probability']):
        bar(draw,385+action*35,ACTIONS[action],value,False,GREEN)
    label(draw,(700,550),f"Decision confidence  {frame['confidence']:.1%}",22,WHITE,True)
    label(draw,(700,590),f'Action {step+1}/{total}  •  fixed eval episode #{episode+1}',19,MUTED)
    if frame['success'] and after: label(draw,(700,625),'SOLVED',28,GREEN,True)
    elif frame['pushed']: label(draw,(700,625),'BOX PUSH',22,GOLD,True)
    label(draw,(48,670),'NO NEURAL NETWORK',17,MUTED,True)
    label(draw,(270,670),'NO RUNTIME SEARCH',17,MUTED,True)
    label(draw,(520,670),'FROZEN WRITES: 0',17,MUTED,True)
    label(draw,(970,670),f"10-map rate: {result['primary']['rate']:.1%}",17,MUTED,True)
    return image


def title_frame(result):
    image=base_frame(); draw=ImageDraw.Draw(image)
    label(draw,(72,115),'BPC × JEV-INSPIRED',30,CYAN,True)
    label(draw,(72,168),'CALIBRATED DECISIONS',58,WHITE,True)
    label(draw,(74,260),'Can one probability-cube controller transfer to',28,MUTED)
    label(draw,(74,300),'10 structurally different, unseen Sokoban layouts?',28,MUTED)
    label(draw,(74,390),'Raw 9×9×6 binary input  •  Four anonymous actions',24,WHITE)
    label(draw,(74,432),'Exact probability counts  •  No neural network  •  No planner',24,WHITE)
    label(draw,(74,515),'Developer-frozen local holdout',21,GOLD,True)
    label(draw,(74,555),'Jev ideas: typed Choice + independent calibrated questions',21,CYAN)
    return image


def summary_frame(result):
    image=base_frame(); draw=ImageDraw.Draw(image); total=result['episodes_per_condition']
    label(draw,(70,70),'FROZEN 10-LEVEL RESULT',45,WHITE,True)
    label(draw,(70,145),f"BPC  {result['totals']['primary']}/{total}  ({result['primary']['rate']:.1%})",35,GREEN,True)
    rows=(('Uniform random',result['totals']['uniform']),('Action channels rotated',result['totals']['action_rotated']),
          ('Remove joint relations',result['totals']['no_joint']),('Force change fusion',result['totals']['change_fused']))
    for i,(name,value) in enumerate(rows):
        y=225+i*65; label(draw,(75,y),name,25,WHITE); label(draw,(500,y),f'{value}/{total}  ({value/total:.1%})',25,MUTED,True)
    passed=sum(result['gate'].values()); count=len(result['gate'])
    label(draw,(75,530),f'PRE-REGISTERED GATE: {passed}/{count}  '+('PASS' if result['adopted'] else 'FAIL'),30,
          GREEN if result['adopted'] else RED,True)
    label(draw,(75,600),'Boundary: limited same-distribution cross-layout transfer — not arbitrary Sokoban or AGI.',20,MUTED)
    return image


def main():
    result=json.loads((OUT/'result.json').read_text()); traces=json.loads((OUT/'traces.json').read_text())
    holdout=json.loads((ROOT/'holdout_v7.json').read_text())
    assert result['adopted'] and len(traces)==10
    video=OUT/'bpc_sokoban_v7_10_unseen_levels.mp4'; poster=OUT/'poster_v7.png'
    command=['ffmpeg','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}',
             '-framerate',str(FPS),'-i','-','-f','lavfi','-i','anullsrc=r=48000:cl=stereo',
             '-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-crf','20','-preset','medium',
             '-c:a','aac','-b:a','96k','-shortest','-movflags','+faststart',str(video)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    def emit(image,count):
        data=image.tobytes()
        for _ in range(count): process.stdin.write(data)
    emit(title_frame(result),75)
    for i in range(1,11):
        frames=traces[str(i)]; episode=result['first_success_episode_zero_based'][str(i)]
        for step,frame in enumerate(frames): emit(trace_frame(holdout[i-1],i,frame,episode,step,len(frames),result),2)
        emit(trace_frame(holdout[i-1],i,frames[-1],episode,len(frames)-1,len(frames),result,True),18)
    summary=summary_frame(result); summary.save(poster); emit(summary,120)
    process.stdin.close(); code=process.wait(); assert code==0
    print(video); print(poster)


if __name__=='__main__': main()
