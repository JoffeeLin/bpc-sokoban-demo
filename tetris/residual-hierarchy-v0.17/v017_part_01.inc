/* BEGIN INLINE direct_f2_query_v016_lib.c */
/* BEGIN INLINE v016_f2_wave_lib.c */
/* BEGIN INLINE direct_residual_wavegate_v014_lib.c */
/* BEGIN INLINE direct_residual_factor_v013_lib.c */
#define main direct_v011_main
/* BEGIN INLINE direct_errorwrite_cube1.c */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#define W 10
#define H 20
#define CELLS 200
#define PREVIEW 16
#define FRAME 417
#define ACTS 4
#define FD 52
#define BR 3
#define TBITS 19
#define TSZ (1u<<TBITS)
#define MASK (TSZ-1u)
enum{ACT_NONE=0,ACT_LEFT,ACT_RIGHT,ACT_ROT};enum{EV_MOVE=1,EV_ROT=2,EV_LOCK=8,EV_CLEAR=16,EV_GAMEOVER=32};
typedef struct{uint64_t s;}RNG;static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return(uint32_t)((r->s*2685821657736338717ULL)>>32);}static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}static float rf(RNG*r){return(ru(r)+.5f)/4294967296.f;}static uint32_t mix(uint32_t x){x^=x>>16;x*=0x7feb352dU;x^=x>>15;x*=0x846ca68bU;x^=x>>16;return x;}
static const uint16_t SH[7][4]={{0x00F0,0x4444,0x00F0,0x4444},{0x0660,0x0660,0x0660,0x0660},{0x0270,0x0262,0x0720,0x0232},{0x0360,0x0462,0x0360,0x0462},{0x0630,0x0264,0x0630,0x0264},{0x0710,0x0226,0x0470,0x0322},{0x0740,0x0622,0x0170,0x0223}};static int oc(uint16_t m,int x,int y){return(m>>(y*4+x))&1;}
typedef struct{uint16_t row[H];int type,rot,x,y,next_type,game_over,lines,pieces;}Game;static int col(const Game*g,int type,int rot,int x,int y){uint16_t m=SH[type][rot&3];for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(oc(m,sx,sy)){int bx=x+sx,by=y+sy;if(bx<0||bx>=W||by>=H)return 1;if(by>=0&&(g->row[by]&(1u<<bx)))return 1;}return 0;}static int spawn(Game*g){g->type=g->next_type;g->next_type=(g->next_type+1)%7;g->rot=0;g->x=3;g->y=-1;g->pieces++;if(col(g,g->type,g->rot,g->x,g->y)){g->game_over=1;return 0;}return 1;}static void init(Game*g,int s){memset(g,0,sizeof(*g));g->next_type=s%7;spawn(g);}static int clr(Game*g){int n=0;for(int y=H-1;y>=0;y--)if((g->row[y]&1023u)==1023u){for(int z=y;z>0;z--)g->row[z]=g->row[z-1];g->row[0]=0;n++;y++;}g->lines+=n;return n;}static int lockp(Game*g){uint16_t m=SH[g->type][g->rot&3];for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(oc(m,sx,sy)){int x=g->x+sx,y=g->y+sy;if(y<0){g->game_over=1;return EV_LOCK|EV_GAMEOVER;}if(x>=0&&x<W&&y<H)g->row[y]|=1u<<x;}int e=EV_LOCK;if(clr(g))e|=EV_CLEAR;if(!spawn(g))e|=EV_GAMEOVER;return e;}static int step(Game*g,int a){if(g->game_over)return EV_GAMEOVER;int e=0;if(a==ACT_LEFT&&!col(g,g->type,g->rot,g->x-1,g->y)){g->x--;e|=EV_MOVE;}else if(a==ACT_RIGHT&&!col(g,g->type,g->rot,g->x+1,g->y)){g->x++;e|=EV_MOVE;}else if(a==ACT_ROT&&!col(g,g->type,(g->rot+1)&3,g->x,g->y)){g->rot=(g->rot+1)&3;e|=EV_ROT;}if(!col(g,g->type,g->rot,g->x,g->y+1))g->y++;else e|=lockp(g);return e;}static void render(const Game*g,uint8_t f[FRAME]){memset(f,0,FRAME);for(int y=0;y<H;y++)for(int x=0;x<W;x++)f[y*W+x]=(g->row[y]>>x)&1;if(!g->game_over){uint16_t m=SH[g->type][g->rot&3];for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(oc(m,sx,sy)){int x=g->x+sx,y=g->y+sy;if(x>=0&&x<W&&y>=0&&y<H)f[CELLS+y*W+x]=1;}}uint16_t p=SH[g->next_type][0];for(int y=0;y<4;y++)for(int x=0;x<4;x++)f[400+y*4+x]=oc(p,x,y);f[416]=(uint8_t)g->game_over;}
typedef struct{int tr,tx,v,last;}Pilot;static int holes(const Game*g){int h=0;for(int x=0;x<W;x++){int seen=0;for(int y=0;y<H;y++){if(g->row[y]&(1u<<x))seen=1;else if(seen)h++;}}return h;}static int hei(const Game*g){int s=0;for(int x=0;x<W;x++){int h=0;for(int y=0;y<H;y++)if(g->row[y]&(1u<<x)){h=H-y;break;}s+=h;}return s;}static int land(const Game*g,int t,int r,int x){int y=-2;if(col(g,t,r,x,y))return 999;while(!col(g,t,r,x,y+1))y++;return y;}static void choose(const Game*g,Pilot*p,RNG*r){float best=-1e30f;int br=0,bx=3;for(int ro=0;ro<4;ro++)for(int x=-2;x<W;x++){int y=land(g,g->type,ro,x);if(y==999)continue;Game q=*g;q.rot=ro;q.x=x;q.y=y;q.game_over=0;int b=q.lines;lockp(&q);float sc=120.f*(q.lines-b)-8.f*holes(&q)-.6f*hei(&q)+(rf(r)-.5f)*10;if(sc>best){best=sc;br=ro;bx=x;}}p->tr=br;p->tx=bx;p->v=1;p->last=g->pieces;}static int pol(const Game*g,Pilot*p,RNG*r,int ex){if(g->game_over)return 0;if(!p->v||p->last!=g->pieces)choose(g,p,r);if(ex&&ri(r,100)<22)return ri(r,ACTS);if(g->rot!=p->tr)return ACT_ROT;if(g->x<p->tx)return ACT_RIGHT;if(g->x>p->tx)return ACT_LEFT;return ACT_NONE;}
/* Cube 1: genuine prediction -> reality residual -> writeback.
   52 physical future-effect coordinates: 25 active-relative, 25 locked-relative,
   preview-change, game-over. No accumulated count table is used. */
typedef struct{float w[ACTS][FD];unsigned long long writes;}FC;
static float fsig(float x){if(x>12.f)return .999994f;if(x<-12.f)return .000006f;return 1.f/(1.f+expf(-x));}
static void ftarget(const uint8_t*a,const uint8_t*b,float t[FD]){
  for(int k=0;k<FD;k++)t[k]=0.f;
  int s=0;
  for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(a[CELLS+y*W+x]){
    s++;
    for(int dy=-2;dy<=2;dy++)for(int dx=-2;dx<=2;dx++){
      int xx=x+dx,yy=y+dy,k=(dy+2)*5+dx+2;
      if(xx>=0&&xx<W&&yy>=0&&yy<H){t[k]+=b[CELLS+yy*W+xx];t[25+k]+=b[yy*W+xx];}
    }
  }
  if(s<1)s=1;
  for(int k=0;k<50;k++)t[k]/=(float)s;
  int pc=0;for(int k=0;k<16;k++)pc+=a[400+k]!=b[400+k];
  t[50]=pc>0?1.f:0.f;
  t[51]=b[416]?1.f:0.f;
}
static void fpred(const FC*c,int ac,float p[FD]){for(int k=0;k<FD;k++)p[k]=fsig(c->w[ac][k]);}
static void fobs(FC*c,const uint8_t*a,int ac,const uint8_t*b){
  float t[FD],p[FD];ftarget(a,b,t);fpred(c,ac,p);
  const float lr=.42f;
