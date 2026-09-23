#!/usr/bin/env python3
"""Render ten real frozen v0.49 carry traces with English UI."""
import subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

from carry_probe_v49 import suite
from experiment_v49_residual_activity_dev import choose,pilots,train

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v49activity';W,H=1280,720
FONT='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf';NAMES=('LEFT','RIGHT','UP','DOWN')
def font(n,bold=False):return ImageFont.truetype(BOLD if bold else FONT,n)
def grid(draw,state,x,y,size):
    data=state.image();unit=size/7
    for yy in range(7):
        for xx in range(7):
            value=data[yy*8+xx];box=(int(x+xx*unit),int(y+yy*unit),int(x+(xx+1)*unit-2),int(y+(yy+1)*unit-2));draw.rounded_rectangle(box,3,fill='#26334a' if value&1 else '#101722')
            if value&8:draw.ellipse((box[0]+unit*.34,box[1]+unit*.34,box[0]+unit*.66,box[1]+unit*.66),fill='#f6c85f')
            if value&16:draw.rectangle((box[0]+unit*.28,box[1]+unit*.28,box[0]+unit*.72,box[1]+unit*.72),outline='#a78bfa',width=2)
            if value&32:draw.line((box[0]+5,box[1]+5,box[2]-5,box[3]-5),fill='#38bdf8',width=3)
            if value&4:draw.rounded_rectangle((box[0]+unit*.2,box[1]+unit*.2,box[0]+unit*.8,box[1]+unit*.8),3,fill='#f59e0b')
            if value&2:draw.ellipse((box[0]+unit*.18,box[1]+unit*.18,box[0]+unit*.82,box[1]+unit*.82),fill='#34d399')
def title(outro=False):
    image=Image.new('RGB',(W,H),'#070b12');draw=ImageDraw.Draw(image);draw.rounded_rectangle((105,80,1175,640),28,fill='#0d1422',outline='#2b466b',width=3)
    draw.text((W//2,145),'PURE BPC v0.49',anchor='mm',font=font(57,True),fill='#f8fafc');draw.text((W//2,218),'Residual-born activity carries a vanished cue',anchor='mm',font=font(30),fill='#93c5fd')
    if outro:draw.text((W//2,345),'Code • preregistration • raw evidence',anchor='mm',font=font(30,True),fill='#34d399');draw.text((W//2,410),'github.com/JoffeeLin/bpc-sokoban-demo',anchor='mm',font=font(26),fill='#bfdbfe')
    else:draw.text((W//2,325),'Frozen: 232 / 256  •  90.63%',anchor='mm',font=font(31,True),fill='#34d399');draw.text((W//2,388),'Zero activity: 23.44%  •  Flip: 32.03%',anchor='mm',font=font(25),fill='#fda4af')
    draw.text((W//2,530),'No neural net  •  No reward  •  No history slot  •  No planner',anchor='mm',font=font(20,True),fill='#a7f3d0');return image
def frame(state,model,index,step,action,values,closed=False):
    image=Image.new('RGB',(W,H),'#070b12');draw=ImageDraw.Draw(image);draw.text((38,25),'Pure BPC v0.49  •  Frozen Unseen Carry',font=font(32,True),fill='#f8fafc');draw.text((1045,35),'CLOSED' if closed else 'E = OPEN',font=font(20,True),fill='#34d399' if closed else '#f6c85f')
    draw.rounded_rectangle((28,88,700,620),20,fill='#0d1422',outline='#26364f',width=2);draw.text((65,118),'RAW PHYSICAL FIELD',font=font(18,True),fill='#94a3b8');grid(draw,state,180,155,330)
    draw.text((65,510),f'Unseen process {index+1:02d}/10  •  required length {state.length}',font=font(22,True),fill='#e2e8f0');draw.text((65,552),'Cue visible' if state.visible else 'Cue vanished — only internal activity persists',font=font(19,True),fill='#fcd34d' if state.visible else '#a7f3d0')
    draw.rounded_rectangle((730,88,1250,620),20,fill='#0d1422',outline='#26364f',width=2);draw.text((770,122),'P(boundary remains)',font=font(22,True),fill='#93c5fd')
    for a,(name,value) in enumerate(zip(NAMES,values)):
        y=170+a*68;draw.rounded_rectangle((770,y,1210,y+48),9,fill='#123329' if a==action and not closed else '#172033');draw.text((792,y+13),name,font=font(18,True),fill='#a7f3d0' if a==action and not closed else '#cbd5e1');draw.text((1185,y+13),f'{value:.3f}',anchor='ra',font=font(18,True),fill='#34d399' if a==action and not closed else '#e2e8f0')
    draw.text((770,475),f'Physical steps: {step}/{state.length}',font=font(19,True),fill='#e2e8f0');draw.text((770,515),f'Active hashed addresses: {len(model.activity):,}',font=font(18),fill='#cbd5e1');draw.text((770,552),'Evaluation writes: 0',font=font(18),fill='#cbd5e1');draw.text((W//2,680),'Cross-length carry probe — not yet general Sokoban control, planning, or AGI',anchor='mm',font=font(18,True),fill='#cbd5e1');return image
def frozen():
    old=pilots();_,dev,_=suite(491010,800,(3,4,5,6),old);old|=dev;_,dev_holdout,_=suite(491110,256,(7,8,9,10),old);old|=dev_holdout;model,_,training,_,_,_,_=train(492010,old);worlds,_,_=suite(492110,256,(7,8,9,10),old|training);return model,worlds[:10]
def main():
    OUT.mkdir(parents=True,exist_ok=True);model,worlds=frozen();stills=[title()]
    for index,initial in enumerate(worlds):
        state=initial;model.begin();step=0
        while not state.closed and step<state.length+5:
            values=[model.probability(state.image(),a,63,0) for a in range(4)];action=choose(values);stills.append(frame(state,model,index,step,action,values));before=state.image();state=state.step(action);model.advance(before,action,state.image());step+=1
        values=[model.probability(state.image(),a,63,0) for a in range(4)];stills.append(frame(state,model,index,step,0,values,True))
    stills.append(title(True));stills[len(stills)//2].save(OUT/'poster_v49_residual_activity.png')
    with tempfile.TemporaryDirectory(prefix='bpc-v49-video-') as folder:
        folder=Path(folder);n=0
        for i,still in enumerate(stills):
            repeat=42 if i in (0,len(stills)-1) else 2
            for _ in range(repeat):still.save(folder/f'{n:05d}.png');n+=1
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(folder/'%05d.png'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'bpc_v49_residual_activity.mp4')],check=True)
    print(OUT/'poster_v49_residual_activity.png');print(OUT/'bpc_v49_residual_activity.mp4')
if __name__=='__main__':main()
