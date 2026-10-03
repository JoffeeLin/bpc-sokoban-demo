#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

enum {UP=0,DOWN=1,LEFT=2,RIGHT=3,NA=4};
static const int DX[NA]={0,0,-1,1}, DY[NA]={-1,1,0,0};
typedef struct{uint64_t s;}RNG;static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return(uint32_t)((r->s*2685821657736338717ULL)>>32);}static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}
static float clamp01(float x){return x<0?0:(x>1?1:x);}

/* Cube-1: accumulates a continuous future-effect function wave. */
typedef struct{uint32_t z[NA][9],o[NA][9];unsigned long long writes;}FuncCube;
static int local_reality(const uint8_t in[9],int a,uint8_t tar[9]){
  memset(tar,0,9);int src=-1;for(int i=0;i<9;i++)if(in[i]){src=i;break;}if(src<0)return 0;
  int x=src%3,y=src/3,nx=x+DX[a],ny=y+DY[a];if(nx<0||nx>=3||ny<0||ny>=3)return 0;tar[ny*3+nx]=1;return 1;
}
static void f_train(FuncCube*c,int epochs){
  for(int e=0;e<epochs;e++)for(int a=0;a<NA;a++)for(int pos=0;pos<9;pos++){
    uint8_t in[9]={0},tar[9];in[pos]=1;if(!local_reality(in,a,tar))continue;
    int src=-1;for(int i=0;i<9;i++)if(in[i]){src=i;break;}int sx=src%3,sy=src/3;
    for(int oy=0;oy<3;oy++)for(int ox=0;ox<3;ox++){
      int dx=ox-sx,dy=oy-sy;if(dx<-1||dx>1||dy<-1||dy>1)continue;int k=(dy+1)*3+dx+1;
      uint32_t*p=tar[oy*3+ox]?&c->o[a][k]:&c->z[a][k];(*p)++;c->writes++;
    }
  }
}
static void f_wave(const FuncCube*c,int a,float q[9]){double n=0;for(int k=0;k<9;k++){uint32_t z=c->z[a][k],o=c->o[a][k];q[k]=((float)o+.5f)/((float)(z+o)+1.f);n+=q[k]*q[k];}n=sqrt(n);if(n<1e-9)n=1;for(int k=0;k<9;k++)q[k]/=(float)n;}

/* Cube-2: queried only by function wave + raw local reality. No action index exists. */
typedef struct{float move[9][9];float gate[9][9];unsigned long long writes;}QueryCube;
static void q_kernel(const QueryCube*c,const float f[9],float k[9]){for(int d=0;d<9;d++){float v=0;for(int j=0;j<9;j++)v+=f[j]*c->move[j][d];k[d]=v;}}
static void train_move_bridge(QueryCube*c,const FuncCube*f,int epochs){
  for(int e=0;e<epochs;e++)for(int a=0;a<NA;a++)for(int pos=0;pos<9;pos++){
    uint8_t in[9]={0},tar[9];in[pos]=1;if(!local_reality(in,a,tar))continue;
    float fw[9],pred[9];f_wave(f,a,fw);q_kernel(c,fw,pred);
    float den=1e-6f;for(int k=0;k<9;k++)den+=fw[k]*fw[k];
    int src=-1;for(int ii=0;ii<9;ii++)if(in[ii]){src=ii;break;}int sx=src%3,sy=src/3;
    for(int oy=0;oy<3;oy++)for(int ox=0;ox<3;ox++){
      int dx=ox-sx,dy=oy-sy;if(dx<-1||dx>1||dy<-1||dy>1)continue;
      int d=(dy+1)*3+dx+1;float er=(float)tar[oy*3+ox]-pred[d];
      for(int k=0;k<9;k++){c->move[k][d]+=0.35f*er*fw[k]/den;c->writes++;}
    }
  }
}
/* Continuous relation gate: function-wave component x raw obstacle-relative position.
   No action ID and no chosen destination enter this field. */
static float q_gate(const QueryCube*c,const float f[9],const uint8_t obst[9]){
  float stop=0;for(int r=0;r<9;r++)if(obst[r])for(int k=0;k<9;k++)stop+=f[k]*c->gate[k][r];
  return clamp01(1.f-stop);
}
static void q_train_gate(QueryCube*c,const float f[9],const uint8_t obst[9],float target_go,int iters){
  float den=1e-6f;for(int k=0;k<9;k++)den+=f[k]*f[k];
  for(int e=0;e<iters;e++){float pg=q_gate(c,f,obst),er=target_go-pg;int nr=0;for(int r=0;r<9;r++)nr+=obst[r]?1:0;if(!nr)continue;
    for(int r=0;r<9;r++)if(obst[r])for(int k=0;k<9;k++){c->gate[k][r]-=0.18f*er*f[k]/(den*nr);c->gate[k][r]=c->gate[k][r]<-2?-2:(c->gate[k][r]>2?2:c->gate[k][r]);c->writes++;}
  }
}
static void train_gate_bridge(QueryCube*c,const FuncCube*f,int epochs){
  RNG r={77123};
  for(int e=0;e<epochs;e++)for(int a=0;a<NA;a++)for(int n=0;n<128;n++){
    int pos=ri(&r,9);uint8_t in[9]={0},free_tar[9],wall[9]={0},tar[9]={0},ob[9]={0};in[pos]=1;
    if(!local_reality(in,a,free_tar)){n--;continue;}
    if(ri(&r,4)!=0){int wr=ri(&r,9);if(wr==pos)wr=(wr+1)%9;wall[wr]=1;}
    int dst=-1;for(int i=0;i<9;i++)if(free_tar[i]){dst=i;break;}
    if(dst>=0&&wall[dst])memcpy(tar,in,9);else memcpy(tar,free_tar,9);
    int sx=pos%3,sy=pos/3;
    for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){int xx=sx+dx,yy=sy+dy;ob[(dy+1)*3+dx+1]=(xx<0||xx>=3||yy<0||yy>=3)?1:wall[yy*3+xx];}
    float fw[9];f_wave(f,a,fw);float target_go=(memcmp(in,tar,9)!=0)?1.f:0.f;q_train_gate(c,fw,ob,target_go,1);
  }
}

static void move_kernel_apply(const float k[9],const uint8_t*in,float*out,int W,int H){for(int i=0;i<W*H;i++)out[i]=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(in[y*W+x])for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){int xx=x+dx,yy=y+dy;if(xx<0||xx>=W||yy<0||yy>=H)continue;float v=k[(dy+1)*3+dx+1];if(v>0)out[yy*W+xx]=1.f-(1.f-out[yy*W+xx])*(1.f-clamp01(v));}}
static float cell_go(const QueryCube*c,const float fw[9],const uint8_t*wall,int W,int H,int x,int y){uint8_t ob[9]={0};for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){int xx=x+dx,yy=y+dy;ob[(dy+1)*3+dx+1]=(xx<0||xx>=W||yy<0||yy>=H)?1:wall[yy*W+xx];}return q_gate(c,fw,ob);}
static void q_step(const QueryCube*c,const float fw[9],const uint8_t*in,const uint8_t*wall,uint8_t*out,int W,int H,int ablate){float ker[9];q_kernel(c,fw,ker);float *mv=calloc((size_t)W*H,sizeof(float));move_kernel_apply(ker,in,mv,W,H);float C=1.f;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(in[y*W+x])C*=cell_go(c,fw,wall,W,H,x,y);if(ablate==1)C=1;else if(ablate==2)C=1-C;for(int i=0;i<W*H;i++){float q=C*mv[i]+(1-C)*in[i];out[i]=(uint8_t)(q>.5f);}free(mv);}

static const uint16_t TS[7][4]={{0x00F0,0x4444,0x00F0,0x4444},{0x0660,0x0660,0x0660,0x0660},{0x0270,0x0262,0x0720,0x0232},{0x0360,0x0462,0x0360,0x0462},{0x0630,0x0264,0x0630,0x0264},{0x0710,0x0226,0x0470,0x0322},{0x0740,0x0622,0x0170,0x0223}};
static int bit4(uint16_t m,int x,int y){return(m>>(y*4+x))&1;}
static int make_world(RNG*r,uint8_t*m,uint8_t*w,int W,int H,int random_terrain){memset(m,0,(size_t)W*H);memset(w,0,(size_t)W*H);for(int x=0;x<W;x++)w[(H-1)*W+x]=1;if(random_terrain)for(int z=0;z<25;z++){int x=ri(r,W),y=H-2-ri(r,7);w[y*W+x]=1;}for(int q=0;q<500;q++){int ty=ri(r,7),rot=ri(r,4),ox=ri(r,W+4)-2,oy=ri(r,4)-2;uint16_t mm=TS[ty][rot];int ok=1,n=0,cells[4][2];for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(bit4(mm,sx,sy)){int x=ox+sx,y=oy+sy;if(x<0||x>=W||y<0||y>=H||w[y*W+x])ok=0;if(n<4){cells[n][0]=x;cells[n][1]=y;}n++;}if(!ok||n!=4)continue;for(int k=0;k<4;k++)m[cells[k][1]*W+cells[k][0]]=1;return 1;}return 0;}
static int reality_step_down(const uint8_t*in,const uint8_t*wall,uint8_t*out,int W,int H){int blocked=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(in[y*W+x]){int ny=y+1;if(ny>=H||wall[ny*W+x])blocked=1;}if(blocked){memcpy(out,in,(size_t)W*H);return 0;}memset(out,0,(size_t)W*H);for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(in[y*W+x])out[(y+1)*W+x]=1;return 1;}
static int exact(const uint8_t*a,const uint8_t*b,int n){return memcmp(a,b,(size_t)n)==0;}
static int hard_real(const uint8_t*in,const uint8_t*w,uint8_t*out,int W,int H){uint8_t*a=malloc(W*H),*b=malloc(W*H);memcpy(a,in,(size_t)W*H);int n=0;for(;n<64;n++){reality_step_down(a,w,b,W,H);if(exact(a,b,W*H))break;memcpy(a,b,(size_t)W*H);}memcpy(out,a,(size_t)W*H);free(a);free(b);return n;}
static int hard_model(const QueryCube*q,const float fw[9],const uint8_t*in,const uint8_t*w,uint8_t*out,int W,int H,int ablate){uint8_t*a=malloc(W*H),*b=malloc(W*H);memcpy(a,in,(size_t)W*H);int n=0;for(;n<64;n++){q_step(q,fw,a,w,b,W,H,ablate);if(exact(a,b,W*H))break;memcpy(a,b,(size_t)W*H);}memcpy(out,a,(size_t)W*H);free(a);free(b);return n;}
static void audit(const FuncCube*f,const QueryCube*q,int N,int terrain,int mode,uint64_t seed){int W=10,H=20;RNG r={seed};uint8_t*in=malloc(W*H),*w=malloc(W*H),*tr=malloc(W*H),*pm=malloc(W*H);unsigned long long ex=0,step=0;double th=0,mh=0;float fw[9];f_wave(f,DOWN,fw);if(mode==3){float tmp=fw[0];for(int k=0;k<8;k++)fw[k]=fw[k+1];fw[8]=tmp;}else if(mode==4)for(int k=0;k<9;k++)fw[k]=-fw[k];else if(mode==5)for(int k=0;k<9;k++)fw[k]=0;for(int i=0;i<N;i++){if(!make_world(&r,in,w,W,H,terrain)){i--;continue;}int a=hard_real(in,w,tr,W,H),b=hard_model(q,fw,in,w,pm,W,H,mode==1?1:mode==2?2:0);ex+=exact(tr,pm,W*H);step+=(a==b);th+=a;mh+=b;}const char*nm=mode==0?"normal":mode==1?"carrier forced-open":mode==2?"carrier reflected":mode==3?"function-wave shift":mode==4?"function-wave phase flip":"function-wave zero";printf("%-23s terrain=%d final=%llu/%d %.3f%% steps=%.3f%% true_h=%.2f model_h=%.2f\n",nm,terrain,ex,N,100.0*ex/N,100.0*step/N,th/N,mh/N);free(in);free(w);free(tr);free(pm);}

static int make_step_world(RNG*r,uint8_t*m,uint8_t*w,int W,int H){memset(m,0,(size_t)W*H);memset(w,0,(size_t)W*H);for(int z=0;z<30;z++){int x=ri(r,W),y=ri(r,H);w[y*W+x]=1;}for(int q=0;q<500;q++){int ty=ri(r,7),rot=ri(r,4),ox=ri(r,W+4)-2,oy=ri(r,H+4)-2;uint16_t mm=TS[ty][rot];int ok=1,n=0,cells[4][2];for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(bit4(mm,sx,sy)){int x=ox+sx,y=oy+sy;if(x<0||x>=W||y<0||y>=H||w[y*W+x])ok=0;if(n<4){cells[n][0]=x;cells[n][1]=y;}n++;}if(!ok||n!=4)continue;for(int k=0;k<4;k++)m[cells[k][1]*W+cells[k][0]]=1;return 1;}return 0;}
static void truth_rigid_step(const uint8_t*in,const uint8_t*w,uint8_t*out,int W,int H,int a){int blocked=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(in[y*W+x]){int nx=x+DX[a],ny=y+DY[a];if(nx<0||nx>=W||ny<0||ny>=H||w[ny*W+nx])blocked=1;}if(blocked){memcpy(out,in,(size_t)W*H);return;}memset(out,0,(size_t)W*H);for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(in[y*W+x])out[(y+DY[a])*W+x+DX[a]]=1;}
static void audit_random_steps(const FuncCube*f,const QueryCube*q,int N,uint64_t seed,int mode){int W=10,H=20;RNG r={seed};uint8_t*in=malloc(W*H),*w=malloc(W*H),*t=malloc(W*H),*p=malloc(W*H);unsigned long long ex=0;for(int i=0;i<N;i++){int a=ri(&r,NA);if(!make_step_world(&r,in,w,W,H)){i--;continue;}truth_rigid_step(in,w,t,W,H,a);float fw[9];f_wave(f,a,fw);if(mode==1)for(int k=0;k<9;k++)fw[k]=0;else if(mode==2){float tmp=fw[0];for(int k=0;k<8;k++)fw[k]=fw[k+1];fw[8]=tmp;}q_step(q,fw,in,w,p,W,H,0);ex+=exact(t,p,W*H);}const char*nm=mode==0?"random-step normal":mode==1?"random-step F-zero":"random-step F-shift";printf("%-23s exact=%llu/%d %.3f%%\n",nm,ex,N,100.0*ex/N);free(in);free(w);free(t);free(p);}

int main(int argc,char**argv){int fe=argc>1?atoi(argv[1]):30,qe=argc>2?atoi(argv[2]):80,ge=argc>3?atoi(argv[3]):120;FuncCube f={0};QueryCube q={0};f_train(&f,fe);train_move_bridge(&q,&f,qe);train_gate_bridge(&q,&f,ge);printf("BPC FunctionCube Tetris v0.10 | aligned continuous relation gate: Cube1 function wave queries Cube2 | Cube2 has no action ID | no HardDrop training\n");printf("Cube1 writes=%llu Cube2 writes=%llu\n",f.writes,q.writes);audit_random_steps(&f,&q,20000,0xABCD,0);audit_random_steps(&f,&q,20000,0xABCD,1);audit_random_steps(&f,&q,20000,0xABCD,2);for(int s=0;s<4;s++){uint64_t seed=0x5555ULL+0x10001ULL*(uint64_t)s;printf("-- world-seed %d --\n",s);audit(&f,&q,5000,1,0,seed);}audit(&f,&q,10000,0,0,0x4444);audit(&f,&q,10000,1,0,0x5555);audit(&f,&q,10000,1,1,0x5555);audit(&f,&q,10000,1,2,0x5555);audit(&f,&q,10000,1,3,0x5555);audit(&f,&q,10000,1,4,0x5555);audit(&f,&q,10000,1,5,0x5555);return 0;}
