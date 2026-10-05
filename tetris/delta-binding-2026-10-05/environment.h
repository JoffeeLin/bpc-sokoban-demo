#ifndef BPC_TETRIS_ENVIRONMENT_H
#define BPC_TETRIS_ENVIRONMENT_H
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define W 10
#define H 20
#define N (W*H)
#define PREV 16
enum{ACT_LEFT=0,ACT_RIGHT=1,ACT_DOWN=2,ACT_ROT=3,ACT_DROP=4,ACTS=5};
typedef struct{uint64_t s;}RNG;
typedef struct{uint8_t active[N],world[N],preview[PREV],gameover;}State;
static const int MDX[3]={-1,1,0},MDY[3]={0,0,1};
static const uint16_t BASE[7]={0x00F0,0x0660,0x0270,0x0360,0x0630,0x0710,0x0740};
static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return(uint32_t)((r->s*2685821657736338717ULL)>>32);}
static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}
static int eq(const uint8_t*a,const uint8_t*b,int n){return memcmp(a,b,(size_t)n)==0;}
static void visible_rotate_reality(const uint8_t*a,const uint8_t*w,uint8_t*out){int minx=W,miny=H,maxx=-1,maxy=-1,n=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(a[y*W+x]){if(x<minx)minx=x;if(x>maxx)maxx=x;if(y<miny)miny=y;if(y>maxy)maxy=y;n++;}if(!n){memset(out,0,N);return;}int bh=maxy-miny+1;uint8_t q[N]={0};int blocked=0;for(int y=miny;y<=maxy;y++)for(int x=minx;x<=maxx;x++)if(a[y*W+x]){int rx=x-minx,ry=y-miny,tx=minx+(bh-1-ry),ty=miny+rx;if(tx<0||tx>=W||ty<0||ty>=H||w[ty*W+tx]){blocked=1;continue;}q[ty*W+tx]=1;}if(blocked)memcpy(out,a,N);else memcpy(out,q,N);}
static void real_clear(uint8_t*b){for(int y=H-1;y>=0;y--){int full=1;for(int x=0;x<W;x++)full&=b[y*W+x];if(full){for(int yy=y;yy>0;yy--)memcpy(b+yy*W,b+(yy-1)*W,W);memset(b,0,W);y++;}}}
static void real_spawn(State*s){uint8_t cand[N]={0};int blocked=0;for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(s->preview[sy*4+sx]){int x=3+sx,y=-1+sy;if(y>=0&&y<H){cand[y*W+x]=1;if(s->world[y*W+x])blocked=1;}}memset(s->active,0,N);s->gameover=(uint8_t)blocked;if(!blocked)memcpy(s->active,cand,N);}
static int real_move(State*s,int dir,int lock_on_fail){int blocked=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x]){int tx=x+MDX[dir],ty=y+MDY[dir];if(tx<0||tx>=W||ty<0||ty>=H||s->world[ty*W+tx])blocked=1;}if(blocked){if(lock_on_fail){for(int i=0;i<N;i++)if(s->active[i])s->world[i]=1;memset(s->active,0,N);real_clear(s->world);real_spawn(s);return 1;}return 0;}uint8_t a[N]={0};for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x])a[(y+MDY[dir])*W+x+MDX[dir]]=1;memcpy(s->active,a,N);return 0;}
static int real_rot(State*s){uint8_t a[N];visible_rotate_reality(s->active,s->world,a);memcpy(s->active,a,N);return 0;}
static int real_step(State*s,int act){if(s->gameover)return 0;if(act==ACT_LEFT)return real_move(s,0,0);if(act==ACT_RIGHT)return real_move(s,1,0);if(act==ACT_DOWN)return real_move(s,2,1);if(act==ACT_ROT)return real_rot(s);if(act==ACT_DROP){for(int k=0;k<64;k++)if(real_move(s,2,1))return 1;}return 0;}
static void preview_shape(int ty,uint8_t p[PREV]){for(int i=0;i<PREV;i++)p[i]=(uint8_t)((BASE[ty]>>i)&1);}
static void init_episode(RNG*r,State*s){
    memset(s,0,sizeof(*s));uint8_t cur[PREV];preview_shape(ri(r,7),cur);
    for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(cur[sy*4+sx]){int x=3+sx,y=-1+sy;if(y>=0&&y<H)s->active[y*W+x]=1;}
    preview_shape(ri(r,7),s->preview);
}
#endif
