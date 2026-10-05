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
/* ---------- learned translation primitive ---------- */
typedef struct{uint32_t z[3][3][3],o[3][3][3];}Move;typedef struct{float sum[3][9][9];uint32_t n[3][9][9];}MoveBlock;
static void train_move(Move*m,int ep){for(int e=0;e<ep;e++)for(int a=0;a<3;a++)for(int y=0;y<3;y++)for(int x=0;x<3;x++){int nx=x+MDX[a],ny=y+MDY[a];if(nx<0||nx>=3||ny<0||ny>=3)continue;for(int oy=0;oy<3;oy++)for(int ox=0;ox<3;ox++){int dx=x-ox,dy=y-oy;if(dx<-1||dx>1||dy<-1||dy>1)continue;uint32_t*p=(ox==nx&&oy==ny)?&m->o[a][dy+1][dx+1]:&m->z[a][dy+1][dx+1];(*p)++;}}}
static float mp(const Move*m,int a,int dy,int dx){uint32_t z=m->z[a][dy+1][dx+1],o=m->o[a][dy+1][dx+1];return((float)o+.5f)/((float)(z+o)+1.f);}
static void train_mblock(const Move*m,MoveBlock*b,int ep){RNG r={17};for(int e=0;e<ep;e++)for(int a=0;a<3;a++)for(int k=0;k<200;k++){int sx=ri(&r,3),sy=ri(&r,3),tx=sx+MDX[a],ty=sy+MDY[a];if(tx<0||tx>=3||ty<0||ty>=3){k--;continue;}int blocked=ri(&r,2),wx=tx,wy=ty;if(!blocked){int tries=0;do{int dx=ri(&r,3)-1,dy=ri(&r,3)-1;wx=tx+dx;wy=ty+dy;tries++;}while((wx<0||wx>=3||wy<0||wy>=3||(wx==tx&&wy==ty))&&tries<32);if(wx<0||wx>=3||wy<0||wy>=3||(wx==tx&&wy==ty)){k--;continue;}}int mi=(sy-ty+1)*3+(sx-tx+1),wi=(wy-ty+1)*3+(wx-tx+1);float base=mp(m,a,sy-ty,sx-tx),target=blocked?0.f:1.f;b->sum[a][mi][wi]+=target-base;b->n[a][mi][wi]++;}}
static float move_basep(const Move*m,const uint8_t*src,int a,int ox,int oy){double miss=1;int any=0;for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){int x=ox+dx,y=oy+dy;if(x<0||x>=W||y<0||y>=H||!src[y*W+x])continue;any=1;miss*=1.0-mp(m,a,dy,dx);}return any?(float)(1.0-miss):0.f;}
/* v1.5: no oracle target coordinate at inference.  The learned move table itself
   emits probability mass over every relative destination.  Collision feasibility
   is the interference between that learned destination distribution and raw world. */
static float move_go(const Move*m,const MoveBlock*b,const uint8_t*world,int a,int x,int y){
  (void)b;
  double C=1.0, mass=0.0;
  for(int ddy=-1;ddy<=1;ddy++)for(int ddx=-1;ddx<=1;ddx++){
    /* source relative to output = (-ddx,-ddy) */
    float q=mp(m,a,-ddy,-ddx);
    mass+=q;
    int tx=x+ddx,ty=y+ddy;
    int blocked=(tx<0||tx>=W||ty<0||ty>=H)?1:world[ty*W+tx];
    if(blocked) C*=1.0-(double)q;
  }
  if(mass<0.5) return 0.f;
  if(C<0) C=0;
  if(C>1) C=1;
  return (float)C;
}
static float move_carrier(const Move*m,const MoveBlock*b,const uint8_t*a,const uint8_t*w,int dir){float C=1.f;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(a[y*W+x])C*=move_go(m,b,w,dir,x,y);return C;}
static void shifted_probs(const Move*m,const uint8_t*src,int dir,float*out){for(int y=0;y<H;y++)for(int x=0;x<W;x++)out[y*W+x]=move_basep(m,src,dir,x,y);}
/* ---------- v2.1 exact-address visible rotation primitive ---------- */
#define VR 3
#define VTSZ (1u<<20)
#define VTM (VTSZ-1u)
typedef struct{uint64_t lo,hi;uint32_t z,o;uint8_t used;}VREntry;
typedef struct{VREntry*t;}RotMem;
static uint64_t vrmix(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static int vrkey(const uint8_t*a,int ox,int oy,uint64_t*lo,uint64_t*hi){*lo=*hi=0;int any=0,k=0;for(int dy=-VR;dy<=VR;dy++)for(int dx=-VR;dx<=VR;dx++,k++){int x=ox+dx,y=oy+dy;uint64_t v=(x<0||x>=W||y<0||y>=H)?2u:(uint64_t)(a[y*W+x]?1:0);if(v==1)any=1;if(k<32)*lo|=v<<(2*k);else *hi|=v<<(2*(k-32));}return any;}
static uint32_t vrslot(uint64_t lo,uint64_t hi){return(uint32_t)vrmix(lo^vrmix(hi+0x9e3779b97f4a7c15ULL))&VTM;}
static VREntry* vrfind(RotMem*m,uint64_t lo,uint64_t hi,int create){uint32_t j=vrslot(lo,hi);for(uint32_t n=0;n<VTSZ;n++,j=(j+1)&VTM){VREntry*e=&m->t[j];if(!e->used){if(!create)return NULL;e->used=1;e->lo=lo;e->hi=hi;return e;}if(e->lo==lo&&e->hi==hi)return e;}fprintf(stderr,"rotation table full\n");exit(3);}
static void vrinit(RotMem*m){m->t=calloc(VTSZ,sizeof(VREntry));if(!m->t){fprintf(stderr,"rotation alloc\n");exit(2);}}
static void vrfree(RotMem*m){free(m->t);m->t=NULL;}
static float vrp(const RotMem*m0,const uint8_t*a,int x,int y){uint64_t lo,hi;if(!vrkey(a,x,y,&lo,&hi))return 0.f;RotMem*m=(RotMem*)m0;VREntry*e=vrfind(m,lo,hi,0);return e?(e->o?(float)e->o/(float)(e->z+e->o):0.f):0.f;}
static void vrobserve(RotMem*m,const uint8_t*a,const uint8_t*t){for(int y=0;y<H;y++)for(int x=0;x<W;x++){uint64_t lo,hi;if(!vrkey(a,x,y,&lo,&hi))continue;VREntry*e=vrfind(m,lo,hi,1);if(t[y*W+x])e->o++;else e->z++;}}
static void visible_rotate_reality(const uint8_t*a,const uint8_t*w,uint8_t*out){int minx=W,miny=H,maxx=-1,maxy=-1,n=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(a[y*W+x]){if(x<minx)minx=x;if(x>maxx)maxx=x;if(y<miny)miny=y;if(y>maxy)maxy=y;n++;}if(!n){memset(out,0,N);return;}int bh=maxy-miny+1;uint8_t q[N]={0};int blocked=0;for(int y=miny;y<=maxy;y++)for(int x=minx;x<=maxx;x++)if(a[y*W+x]){int rx=x-minx,ry=y-miny,tx=minx+(bh-1-ry),ty=miny+rx;if(tx<0||tx>=W||ty<0||ty>=H||w[ty*W+tx]){blocked=1;continue;}q[ty*W+tx]=1;}if(blocked)memcpy(out,a,N);else memcpy(out,q,N);}
static void train_visible_rot(RotMem*m,int epochs){static const uint16_t bb[7]={0x00F0,0x0660,0x0270,0x0360,0x0630,0x0710,0x0740};uint8_t w[N]={0};for(int e=0;e<epochs;e++)for(int ty=0;ty<7;ty++)for(int rr=0;rr<4;rr++){uint8_t p[PREV]={0};for(int i=0;i<PREV;i++)p[i]=(uint8_t)((bb[ty]>>i)&1u);for(int k=0;k<rr;k++){uint8_t q[PREV]={0};for(int y=0;y<4;y++)for(int x=0;x<4;x++)if(p[y*4+x]){int dx=x-1,dy=y-1,nx=1-dy,ny=1+dx;if(nx>=0&&nx<4&&ny>=0&&ny<4)q[ny*4+nx]=1;}memcpy(p,q,PREV);}int minx=4,miny=4,maxx=-1,maxy=-1;for(int y=0;y<4;y++)for(int x=0;x<4;x++)if(p[y*4+x]){if(x<minx)minx=x;if(x>maxx)maxx=x;if(y<miny)miny=y;if(y>maxy)maxy=y;}int bw=maxx-minx+1,bh=maxy-miny+1;for(int y0=0;y0<=H-bh;y0++)for(int x0=0;x0<=W-bw;x0++){uint8_t a[N]={0},t[N];for(int y=miny;y<=maxy;y++)for(int x=minx;x<=maxx;x++)if(p[y*4+x])a[(y0+y-miny)*W+(x0+x-minx)]=1;visible_rotate_reality(a,w,t);vrobserve(m,a,t);}}}
static void visible_rot_predict(const RotMem*m,const uint8_t*a,const uint8_t*w,uint8_t*out){float p[N];double C=1.0;for(int y=0;y<H;y++)for(int x=0;x<W;x++){p[y*W+x]=vrp(m,a,x,y);if(w[y*W+x])C*=1.0-(double)p[y*W+x];}if(C<0)C=0;if(C>1)C=1;for(int i=0;i<N;i++)out[i]=(uint8_t)((C*p[i]+(1-C)*(float)a[i])>.5f);}
/* ---------- learned lock channel coupling ---------- */
typedef struct{float w[2][2];}Couple;static void train_couple(Couple*c,int ep){float lr=.05f;for(int e=0;e<ep;e++)for(int blocked=0;blocked<2;blocked++){float C=blocked?0.f:1.f,f[2]={C,1.f-C},t[2]={blocked?0.f:1.f,blocked?1.f:0.f};for(int o=0;o<2;o++){float y=c->w[o][0]*f[0]+c->w[o][1]*f[1],er=t[o]-y;for(int k=0;k<2;k++)c->w[o][k]+=lr*er*f[k];}}}static void cg(const Couple*c,float C,float*gm,float*gl){*gm=c->w[0][0]*C+c->w[0][1]*(1-C);*gl=c->w[1][0]*C+c->w[1][1]*(1-C);if(*gm<0)*gm=0;if(*gm>1)*gm=1;if(*gl<0)*gl=0;if(*gl>1)*gl=1;}
/* ---------- v1.6 learned preview -> full-board active field ---------- */
typedef struct{uint32_t z[PREV][N],o[PREV][N];}Spawn;
static void train_spawn(Spawn*s,int ep){
  for(int e=0;e<ep;e++)for(int si=0;si<PREV;si++){
    int sx=si%4,sy=si/4;
    int tx=3+sx,ty=-1+sy;
    int target=(ty>=0&&ty<H&&tx>=0&&tx<W)?ty*W+tx:-1;
    for(int oi=0;oi<N;oi++){
      uint32_t*p=(oi==target)?&s->o[si][oi]:&s->z[si][oi];
      (*p)++;
    }
  }
}
static float sp(const Spawn*s,int si,int oi){uint32_t z=s->z[si][oi],o=s->o[si][oi];return((float)o+.5f)/((float)(z+o)+1.f);}
static void spawn_field(const Spawn*s,const uint8_t prev[PREV],float out[N]){
  for(int oi=0;oi<N;oi++){
    double miss=1.0;int any=0;
    for(int si=0;si<PREV;si++)if(prev[si]){any=1;miss*=1.0-sp(s,si,oi);}
    out[oi]=any?(float)(1.0-miss):0.f;
  }
}
static float spawn_carrier(const Spawn*s,const uint8_t prev[PREV],const uint8_t world[N]){
  double C=1.0;
  for(int si=0;si<PREV;si++)if(prev[si]){
    for(int oi=0;oi<N;oi++)if(world[oi]) C*=1.0-(double)sp(s,si,oi);
  }
  if(C<0) C=0;
  if(C>1) C=1;
  return (float)C;
}
/* ---------- learned line-clear carrier; row motion reuses learned DOWN ---------- */
typedef struct{uint32_t z[2],o[2];}CellWave;
static void train_cell(CellWave*m,int ep){for(int e=0;e<ep;e++)for(int x=0;x<2;x++){uint32_t*p=x?&m->o[x]:&m->z[x];(*p)++;}}
static float cp(const CellWave*m,int x){uint32_t z=m->z[x],o=m->o[x];return((float)o+.5f)/((float)(z+o)+1.f);}
static float rowc(const CellWave*m,const uint8_t*b,int y){float C=1.f;for(int x=0;x<W;x++)C*=cp(m,b[y*W+x]?1:0);return C;}
/* v0.3: no detectrow()/top-1 selection. Every row emits the same learned
   carrier from one snapshot. Every mature carrier participates; its relocation
   reuses the already learned DOWN spatial function. The fixed scan order is
   audited in both directions and is not used to choose a winning row. */
#ifndef CLEAR_REVERSE
#define CLEAR_REVERSE 0
#endif
static void clear_row_downreuse(const Move*mv,uint8_t*b,int row,float C){
  uint8_t src[N]={0};float moved[N];
  for(int yy=0;yy<row;yy++)memcpy(src+yy*W,b+yy*W,W);
  shifted_probs(mv,src,2,moved);
  for(int yy=0;yy<=row;yy++)for(int x=0;x<W;x++){
    int i=yy*W+x;
    b[i]=(uint8_t)((C*moved[i]+(1.f-C)*(float)b[i])>.5f);
  }
}
static int clear_all_model(const CellWave*c,const Move*mv,uint8_t*b){
  float born[H];int any=0;
  for(int y=0;y<H;y++){born[y]=rowc(c,b,y);any|=born[y]>.5f;}
  if(!any)return 0;
#if CLEAR_REVERSE
  for(int row=H-1;row>=0;row--)if(born[row]>.5f)clear_row_downreuse(mv,b,row,born[row]);
#else
  for(int row=0;row<H;row++)if(born[row]>.5f)clear_row_downreuse(mv,b,row,born[row]);
#endif
  return 1;
}
/* ---------- state + fully observable physical reality ---------- */
typedef struct{uint8_t active[N],world[N],preview[PREV],gameover;}State;
static void real_clear(uint8_t*b){for(int y=H-1;y>=0;y--){int full=1;for(int x=0;x<W;x++)full&=b[y*W+x];if(full){for(int yy=y;yy>0;yy--)memcpy(b+yy*W,b+(yy-1)*W,W);memset(b,0,W);y++;}}}
static void real_spawn(State*s){uint8_t cand[N]={0};int blocked=0;for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(s->preview[sy*4+sx]){int x=3+sx,y=-1+sy;if(y>=0&&y<H){cand[y*W+x]=1;if(s->world[y*W+x])blocked=1;}}memset(s->active,0,N);s->gameover=(uint8_t)blocked;if(!blocked)memcpy(s->active,cand,N);}
static int real_move(State*s,int dir,int lock_on_fail){int blocked=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x]){int tx=x+MDX[dir],ty=y+MDY[dir];if(tx<0||tx>=W||ty<0||ty>=H||s->world[ty*W+tx])blocked=1;}if(blocked){if(lock_on_fail){for(int i=0;i<N;i++)if(s->active[i])s->world[i]=1;memset(s->active,0,N);real_clear(s->world);real_spawn(s);return 1;}return 0;}uint8_t a[N]={0};for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x])a[(y+MDY[dir])*W+x+MDX[dir]]=1;memcpy(s->active,a,N);return 0;}
static int real_rot(State*s){uint8_t a[N];visible_rotate_reality(s->active,s->world,a);memcpy(s->active,a,N);return 0;}
static int real_step(State*s,int act){if(s->gameover)return 0;if(act==ACT_LEFT)return real_move(s,0,0);if(act==ACT_RIGHT)return real_move(s,1,0);if(act==ACT_DOWN)return real_move(s,2,1);if(act==ACT_ROT)return real_rot(s);if(act==ACT_DROP){for(int k=0;k<64;k++)if(real_move(s,2,1))return 1;}return 0;}
/* ---------- composed learned model tick ---------- */
typedef struct{Move mv;MoveBlock mb;RotMem rm;Couple cp;Spawn sp;Couple sc;CellWave cw;}Model;
static void model_init(Model*m){memset(m,0,sizeof(*m));vrinit(&m->rm);train_visible_rot(&m->rm,1);train_move(&m->mv,30);train_mblock(&m->mv,&m->mb,100);train_couple(&m->cp,300);train_spawn(&m->sp,1000);train_couple(&m->sc,300);train_cell(&m->cw,30);}
static void learned_spawn(const Model*m,const uint8_t prev[PREV],const uint8_t*world,uint8_t*a,float g,uint8_t*gameover){
    float field[N];spawn_field(&m->sp,prev,field);
    float C=spawn_carrier(&m->sp,prev,world);
    float f0=C,f1=1.f-C;
    float gs=m->sc.w[0][0]*f0+m->sc.w[0][1]*f1;
    float gg=m->sc.w[1][0]*f0+m->sc.w[1][1]*f1;
    float spawn_gain=g*gs;
    *gameover=(uint8_t)(g*gg>.5f);
    for(int i=0;i<N;i++){
      if(spawn_gain*field[i]>.5f)a[i]=1;
    }
}
/* v1.7: after the external one-step relation, downstream learned relations are
   repeatedly allowed to act until the field is quiescent.  No explicit
   Lock->Clear->Spawn call chain is used. */
static float model_down_once(const Model*m,State*s){
    if(s->gameover)return 0.f;
    float C=move_carrier(&m->mv,&m->mb,s->active,s->world,2),gm,gl;
    cg(&m->cp,C,&gm,&gl);
    float ma[N];shifted_probs(&m->mv,s->active,2,ma);
    uint8_t na[N]={0};
    for(int i=0;i<N;i++){
      na[i]=(uint8_t)(gm*ma[i]>.5f);
      
      if(gl*(float)s->active[i]>.5f)s->world[i]=1;
    }
    memcpy(s->active,na,N);
    float pending=gl;
    /* Pure relaxation: no quiescence gate and no fixed Lock->Clear->Spawn schedule.
       Spawn and closure are ordinary learned consequences that remain eligible on
       every microstep; the state is read only after the joint field reaches a fixed point. */
    for(int micro=0;micro<H+8;micro++){
      uint8_t beforeA[N],beforeW[N],beforeG=s->gameover;
      memcpy(beforeA,s->active,N);memcpy(beforeW,s->world,N);
      learned_spawn(m,s->preview,s->world,s->active,pending,&s->gameover);
      (void)clear_all_model(&m->cw,&m->mv,s->world);
      int changed=!eq(beforeA,s->active,N)||!eq(beforeW,s->world,N)||beforeG!=s->gameover;
      if(!changed)break;
    }
    return gl;
}
static void model_move_lr(const Model*m,State*s,int dir){float C=move_carrier(&m->mv,&m->mb,s->active,s->world,dir);float ma[N];shifted_probs(&m->mv,s->active,dir,ma);for(int i=0;i<N;i++)s->active[i]=(uint8_t)((C*ma[i]+(1-C)*s->active[i])>.5f);}
static void model_rot(const Model*m,State*s){uint8_t a[N];visible_rot_predict(&m->rm,s->active,s->world,a);memcpy(s->active,a,N);}
static int model_step(const Model*m,State*s,int act){if(s->gameover)return 0;if(act==ACT_LEFT){model_move_lr(m,s,0);return 0;}if(act==ACT_RIGHT){model_move_lr(m,s,1);return 0;}if(act==ACT_DOWN)return model_down_once(m,s)>.5f;if(act==ACT_ROT){model_rot(m,s);return 0;}if(act==ACT_DROP){for(int k=0;k<64;k++)if(model_down_once(m,s)>.5f)return 1;}return 0;}
/* ---------- test generation ---------- */
static const uint16_t BASE[7]={0x00F0,0x0660,0x0270,0x0360,0x0630,0x0710,0x0740};static void preview_shape(int ty,uint8_t p[PREV]){for(int i=0;i<PREV;i++)p[i]=(uint8_t)((BASE[ty]>>i)&1);}
static void local_rotate_bits(uint8_t p[PREV]){uint8_t q[PREV]={0};/* embed 4x4 with pivot at local (1,1), geometric rotate and crop */for(int y=0;y<4;y++)for(int x=0;x<4;x++)if(p[y*4+x]){int dx=x-1,dy=y-1,nx=1-dy,ny=1+dx;if(nx>=0&&nx<4&&ny>=0&&ny<4)q[ny*4+nx]=1;}memcpy(p,q,PREV);}
static int place_piece(RNG*r,State*s,int action,int force_event){memset(s,0,sizeof(*s));preview_shape(ri(r,7),s->preview);uint8_t p[PREV];preview_shape(ri(r,7),p);int rrn=ri(r,4);for(int k=0;k<rrn;k++)local_rotate_bits(p);for(int tries=0;tries<200;tries++){int cx=2+ri(r,W-4),cy=3+ri(r,H-8);memset(s->active,0,N);int ok=1,cells=0;for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(p[sy*4+sx]){int x=cx+sx-1,y=cy+sy-1;if(x<0||x>=W||y<0||y>=H){ok=0;continue;}s->active[y*W+x]=1;cells++;}if(!ok||cells!=4)continue;/* sparse static terrain, keep top clean */for(int k=0;k<15;k++){int x=ri(r,W),y=6+ri(r,H-6);if(!s->active[y*W+x])s->world[y*W+x]=1;}if(force_event){if(action==ACT_DOWN||action==ACT_DROP){/* force a blocking cell below and often make a line complete on lock */int cand[N],n=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x]&&y+1<H)cand[n++]=y*W+x;if(!n)continue;int ci=cand[ri(r,n)],x=ci%W,y=ci/W;s->world[(y+1)*W+x]=1;if(ri(r,2)){for(int xx=0;xx<W;xx++)if(!s->active[y*W+xx])s->world[y*W+xx]=1;}}else if(action==ACT_LEFT||action==ACT_RIGHT){int dir=action==ACT_LEFT?0:1,cand[N],n=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x]){int tx=x+MDX[dir];if(tx>=0&&tx<W)cand[n++]=y*W+x;}if(n){int ci=cand[ri(r,n)],x=ci%W,y=ci/W;s->world[y*W+x+MDX[dir]]=1;}}else if(action==ACT_ROT){uint8_t empty[N]={0},q[N];visible_rotate_reality(s->active,empty,q);int cand[N],n=0;for(int i=0;i<N;i++)if(q[i]&&!s->active[i])cand[n++]=i;if(n)s->world[cand[ri(r,n)]]=1;}}/* remove accidental overlaps */for(int i=0;i<N;i++)if(s->active[i]&&s->world[i])s->world[i]=0;/* ensure spawn zone clear for lock cases */for(int y=0;y<4;y++)for(int x=2;x<8;x++)if(!s->active[y*W+x])s->world[y*W+x]=0;return 1;}return 0;}
typedef struct{unsigned long long n,full,byact[ACTS],okact[ACTS],lockn,lockok;}Stat;
static void audit(const Model*m,int samples,uint64_t seed){RNG r={seed};Stat st={0};for(int i=0;i<samples;i++){int act=ri(&r,ACTS),force=ri(&r,2);State a,b;if(!place_piece(&r,&a,act,force)){i--;continue;}b=a;int lr=real_step(&a,act),lm=model_step(m,&b,act);(void)lm;int ok=eq(a.active,b.active,N)&&eq(a.world,b.world,N)&&a.gameover==b.gameover;st.n++;st.full+=ok;st.byact[act]++;st.okact[act]+=ok;if(lr){st.lockn++;st.lockok+=ok;}}
const char*nm[ACTS]={"left","right","down","rot","drop"};printf("integrated n=%llu exact=%7.3f%% lock_events=%llu lock_exact=%7.3f%%\n",st.n,100.0*st.full/st.n,st.lockn,st.lockn?100.0*st.lockok/st.lockn:0);for(int a=0;a<ACTS;a++)printf("  %-5s %llu/%llu = %7.3f%%\n",nm[a],st.okact[a],st.byact[a],100.0*st.okact[a]/st.byact[a]);}

static void init_episode(RNG*r,State*s){
    memset(s,0,sizeof(*s));uint8_t cur[PREV];preview_shape(ri(r,7),cur);
    for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(cur[sy*4+sx]){int x=3+sx,y=-1+sy;if(y>=0&&y<H)s->active[y*W+x]=1;}
    preview_shape(ri(r,7),s->preview);
}
static void audit_rollout(const Model*m,int episodes,int maxsteps,uint64_t seed){
    RNG r={seed};unsigned long long steps=0,exact=0,locks=0,gameovers=0,failact[ACTS]={0};int completed=0;int first_fail_ep=-1,first_fail_t=-1,first_fail_act=-1,first_lr=0,first_lm=0,first_da=0,first_dw=0,first_dp=0;float first_rotC=-1.f;int first_localW=0,first_rotBlocked=-1;
    for(int ep=0;ep<episodes;ep++){
        State real,mod;init_episode(&r,&real);mod=real;
        for(int t=0;t<maxsteps;t++){
            int act;
            int u=ri(&r,100);if(u<18)act=ACT_LEFT;else if(u<36)act=ACT_RIGHT;else if(u<50)act=ACT_ROT;else if(u<70)act=ACT_DOWN;else act=ACT_DROP;
            float preC=-1.f;int preW=0,preBlocked=-1;int lr=real_step(&real,act),lm=model_step(m,&mod,act);
            int ok=(lr==lm)&&eq(real.active,mod.active,N)&&eq(real.world,mod.world,N)&&real.gameover==mod.gameover;
            steps++;exact+=ok;if(lr)locks++;if(real.gameover)gameovers++;
            if(!ok){failact[act]++;if(first_fail_ep<0){first_fail_ep=ep;first_fail_t=t;first_fail_act=act;first_lr=lr;first_lm=lm;for(int q=0;q<N;q++){first_da+=(real.active[q]!=mod.active[q]);first_dw+=(real.world[q]!=mod.world[q]);first_dp+=0;}first_rotC=preC;first_localW=preW;first_rotBlocked=preBlocked;}break;}
            if(lr){if(real.gameover||mod.gameover)break;uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(real.preview,np,PREV);memcpy(mod.preview,np,PREV);}
            if(t==maxsteps-1)completed++;
        }
    }
    printf("rollout episodes=%d maxsteps=%d compared_steps=%llu exact=%llu/%llu=%7.3f%% locks=%llu gameovers=%llu full_horizon=%d first_fail=%d:%d act=%d lr/lm=%d/%d diffA/W/P=%d/%d/%d rotC=%.4f localW=%d actualBlocked=%d\n",episodes,maxsteps,steps,exact,steps,100.0*exact/steps,locks,gameovers,completed,first_fail_ep,first_fail_t,first_fail_act,first_lr,first_lm,first_da,first_dw,first_dp,first_rotC,first_localW,first_rotBlocked);printf("rollout failures by action: L=%llu R=%llu D=%llu Rot=%llu Drop=%llu\n",failact[0],failact[1],failact[2],failact[3],failact[4]);
}

static void audit_lineclear_downreuse(const Model*m,int per_k,uint64_t seed){
    RNG r={seed};
    unsigned long long total=0,ok=0,byk[5]={0},okbyk[5]={0};
    for(int k=1;k<=4;k++)for(int q=0;q<per_k;q++){
        uint8_t a[N]={0},b[N]={0};
        for(int y=0;y<H-k;y++){
            int ones=0;
            for(int x=0;x<W;x++){int v=ri(&r,100)<28;a[y*W+x]=(uint8_t)v;ones+=v;}
            if(ones==W)a[y*W+ri(&r,W)]=0;
        }
        for(int y=H-k;y<H;y++)for(int x=0;x<W;x++)a[y*W+x]=1;
        memcpy(b,a,N);real_clear(a);
        int guard=0;while(clear_all_model(&m->cw,&m->mv,b) && guard++<H*4){}
        int yes=eq(a,b,N);total++;ok+=yes;byk[k]++;okbyk[k]+=yes;
    }
    printf("DOWN_REUSE_LINECLEAR total=%llu/%llu=%.6f%%",ok,total,total?100.0*(double)ok/(double)total:0.0);
    for(int k=1;k<=4;k++)printf(" k%d=%llu/%llu",k,okbyk[k],byk[k]);
    putchar('\n');
}
int main(){Model m;model_init(&m);puts("BPC Best WorldFit v0.3 | no LineClear top-1 | all row carriers + DOWN reuse");audit_lineclear_downreuse(&m,2500,0xC1EAULL);puts("FORMAL | screen+action only | 8 frozen seeds");for(int s=0;s<8;s++){printf("=== seed %d ===\n",s);audit(&m,5000,12345ULL+100003ULL*(uint64_t)s);audit_rollout(&m,1000,120,98765ULL+200003ULL*(uint64_t)s);}vrfree(&m.rm);return 0;}