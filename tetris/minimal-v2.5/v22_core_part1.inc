#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define W 10
#define H 20
#define N (W*H)
#define R 2
#define D 5
#define SLOTS 25
#define PREV 16
enum{ACT_LEFT=0,ACT_RIGHT=1,ACT_DOWN=2,ACT_ROT=3,ACT_DROP=4,ACTS=5};
static const int MDX[3]={-1,1,0},MDY[3]={0,0,1};
typedef struct{uint64_t s;}RNG;static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return(uint32_t)((r->s*2685821657736338717ULL)>>32);}static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}
static int eq(const uint8_t*a,const uint8_t*b,int n){return memcmp(a,b,(size_t)n)==0;}
typedef struct{uint32_t z[3][3][3],o[3][3][3];}Move;typedef struct{float sum[3][9][9];uint32_t n[3][9][9];}MoveBlock;
static int env_move3(const uint8_t in[9],uint8_t out[9],int a){
  memset(out,0,9);int found=0;
  for(int y=0;y<3;y++)for(int x=0;x<3;x++)if(in[y*3+x]){
    int nx=x+MDX[a],ny=y+MDY[a];if(nx<0||nx>=3||ny<0||ny>=3)return 0;
    out[ny*3+nx]=1;found=1;
  }
  return found;
}
static void observe_move(Move*m,const uint8_t in[9],const uint8_t out[9],int a){
  for(int oy=0;oy<3;oy++)for(int ox=0;ox<3;ox++)
    for(int sy=0;sy<3;sy++)for(int sx=0;sx<3;sx++)if(in[sy*3+sx]){
      int dx=sx-ox,dy=sy-oy;if(dx<-1||dx>1||dy<-1||dy>1)continue;
      uint32_t*p=out[oy*3+ox]?&m->o[a][dy+1][dx+1]:&m->z[a][dy+1][dx+1];(*p)++;
    }
}
static void train_move(Move*m,int ep){
  uint8_t in[9],out[9];
  for(int e=0;e<ep;e++)for(int a=0;a<3;a++)for(int pos=0;pos<9;pos++){
    memset(in,0,9);in[pos]=1;if(env_move3(in,out,a))observe_move(m,in,out,a);
  }
}
static float mp(const Move*m,int a,int dy,int dx){uint32_t z=m->z[a][dy+1][dx+1],o=m->o[a][dy+1][dx+1];return((float)o+.5f)/((float)(z+o)+1.f);}
static void train_mblock(const Move*m,MoveBlock*b,int ep){(void)m;(void)b;(void)ep;}
static float move_basep(const Move*m,const uint8_t*src,int a,int ox,int oy){double miss=1;int any=0;for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){int x=ox+dx,y=oy+dy;if(x<0||x>=W||y<0||y>=H||!src[y*W+x])continue;any=1;miss*=1.0-mp(m,a,dy,dx);}return any?(float)(1.0-miss):0.f;}
static float move_go(const Move*m,const MoveBlock*b,const uint8_t*world,int a,int x,int y){
  (void)b;double C=1.0,mass=0.0;
  for(int ddy=-1;ddy<=1;ddy++)for(int ddx=-1;ddx<=1;ddx++){
    float q=mp(m,a,-ddy,-ddx);mass+=q;int tx=x+ddx,ty=y+ddy;
    int blocked=(tx<0||tx>=W||ty<0||ty>=H)?1:world[ty*W+tx];if(blocked)C*=1.0-(double)q;
  }
  if(mass<0.5)return 0.f;if(C<0)C=0;if(C>1)C=1;return(float)C;
}
static float move_carrier(const Move*m,const MoveBlock*b,const uint8_t*a,const uint8_t*w,int dir){float C=1.f;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(a[y*W+x])C*=move_go(m,b,w,dir,x,y);return C;}
static void shifted_probs(const Move*m,const uint8_t*src,int dir,float*out){for(int y=0;y<H;y++)for(int x=0;x<W;x++)out[y*W+x]=move_basep(m,src,dir,x,y);}
typedef struct{uint32_t z[SLOTS][SLOTS],o[SLOTS][SLOTS];}Rot;typedef struct{uint32_t z[SLOTS][SLOTS],o[SLOTS][SLOTS];}RotBlock;
static int lidx(int dx,int dy){return(dy+R)*D+dx+R;}static void lunidx(int i,int*dx,int*dy){*dy=i/D-R;*dx=i%D-R;}static void rr(int sx,int sy,int*ox,int*oy){*ox=-sy;*oy=sx;}
