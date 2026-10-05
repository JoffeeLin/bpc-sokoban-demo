#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#define main v17_original_main
#include "BPC_Best_WorldFit_v0.17_reality_spawn_split.c"
#undef main

#define RW 15
#define RH 20
#define RN (RW*RH)
#define SFCAP 512

typedef struct{uint64_t key;double yes,total;uint8_t used;}SFCell;
typedef struct{SFCell c[SFCAP];int n;}SharedField;
typedef struct{uint8_t px[RN];}RawFrame;
typedef struct{RawFrame frame;uint8_t trace[N];}BinaryState;
typedef struct{float v[ACTS];}ActionWave;

static uint64_t h64(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static uint64_t tok(int cls,int a,int b,int c,int d){uint64_t x=(uint64_t)(cls&255);x=(x<<8)|(uint64_t)(a&255);x=(x<<8)|(uint64_t)(b&255);x=(x<<8)|(uint64_t)(c&255);x=(x<<8)|(uint64_t)(d&255);return h64(x+0x9e3779b97f4a7c15ULL);}
static SFCell* sffind(SharedField*f,uint64_t k,int create){for(int i=0;i<f->n;i++)if(f->c[i].key==k)return &f->c[i];if(!create)return NULL;if(f->n>=SFCAP){fprintf(stderr,"shared field full\n");exit(5);}SFCell*e=&f->c[f->n++];memset(e,0,sizeof(*e));e->key=k;e->used=1;return e;}
static double sfprob(const SFCell*e){return e?(e->yes+1.0)/(e->total+2.0):.5;}
static double sfget(const SharedField*f0,uint64_t k,double def){SharedField*f=(SharedField*)f0;SFCell*e=sffind(f,k,0);return e?sfprob(e):def;}
static void sfcredit(SharedField*f,uint64_t k,double w,int target){if(w<=0)return;SFCell*e=sffind(f,k,1);e->total+=w;e->yes+=w*(!!target);}

enum{K_GAUGE=1,K_BASIS=2,K_PHASE=3,K_ROUTE=4,K_LIFE=5,K_SPLIT=6,K_SPAWN=7,K_CLOSURE=8,K_CCHILD=9,K_COMPAT=10,K_CRESP=11};
static uint64_t kgauge(int a,int dx,int dy){return tok(K_GAUGE,a,dx+2,dy+2,0);}static uint64_t kbasis(int a,int axis,int out){return tok(K_BASIS,a,axis,out,0);}static uint64_t kphase(int a,int axis){return tok(K_PHASE,a,axis,0,0);}static uint64_t kroute(int a,int out,int c){return tok(K_ROUTE,a,out,c,0);}static uint64_t klife(int a,int c){return tok(K_LIFE,a,c,0,0);}static uint64_t ksplit(int out,int c){return tok(K_SPLIT,out,c,0,0);}static uint64_t kspawn(int dx,int dy){return tok(K_SPAWN,dx+16,dy+16,0,0);}static uint64_t kclosure(int dx,int dy){return tok(K_CLOSURE,dx+2,dy+2,0,0);}static uint64_t kcompat(int state){return tok(K_COMPAT,state,0,0,0);}static uint64_t kcresp(int rdy,int out){return tok(K_CRESP,rdy+32,out,0,0);}

static int sf_geom_gauge(const SharedField*f,int a,int*dx,int*dy){double best=.70;int ok=0;for(int yy=-1;yy<=1;yy++)for(int xx=-1;xx<=1;xx++){double q=sfget(f,kgauge(a,xx,yy),.5);if(q>best){best=q;*dx=xx;*dy=yy;ok=1;}}return ok;}
static int sf_geom_basis(const SharedField*f,int a,int ax){double best=.70;int r=-1;for(int o=0;o<2;o++){double q=sfget(f,kbasis(a,ax,o),.5);if(q>best){best=q;r=o;}}return r;}
static int sf_geom_phase(const SharedField*f,int a,int ax){double q=sfget(f,kphase(a,ax),.5);return q>=.70?1:(q<=.30?-1:0);}
static int sf_geom_targets(const SharedField*f,int act,const uint8_t*a,int tx[],int ty[],int cap){int x[64],y[64],n=gp_collect(a,x,y,64);if(n<=0||n>cap)return-1;int bx=sf_geom_basis(f,act,0),by=sf_geom_basis(f,act,1),sx=sf_geom_phase(f,act,0),sy=sf_geom_phase(f,act,1),gdx,gdy;if(bx<0||by<0||!sx||!sy||!sf_geom_gauge(f,act,&gdx,&gdy))return-1;int bxx=bx==0,bxy=bx==1,byx=by==0,byy=by==1;int rx[64],ry[64];rx[0]=ry[0]=0;for(int i=1;i<n;i++){int dx=x[i]-x[0],dy=y[i]-y[0];rx[i]=dx*sx*bxx+dy*sy*byx;ry[i]=dx*sx*bxy+dy*sy*byy;}int mnx=rx[0],mny=ry[0];for(int i=1;i<n;i++){if(rx[i]<mnx)mnx=rx[i];if(ry[i]<mny)mny=ry[i];}int mx,my;gp_minxy(a,&mx,&my);int baseX=mx+gdx-mnx,baseY=my+gdy-mny;for(int i=0;i<n;i++){tx[i]=baseX+rx[i];ty[i]=baseY+ry[i];}return n;}
static float sf_amp(double q){double a=2.0*q-1.0;if(a<0)a=0;if(a>1)a=1;return(float)a;}
static float sf_compat(const SharedField*f,int state){return sf_amp(sfget(f,kcompat(state),.5));}
/* v0.22: geometry only proposes destinations.  Compatibility is not hard-coded.
   A proposal wave collides with a destination-state token (empty/occupied/boundary),
   and the learned compatibility amplitude from the same shared field determines
   whether the multi-voxel carrier survives. */
static float sf_geom_candidate(const SharedField*f,int act,const uint8_t*a,const uint8_t*w,uint8_t*out){
  memset(out,0,N);int tx[64],ty[64],n=sf_geom_targets(f,act,a,tx,ty,64);if(n<0)return 0.f;
  float C=1.f;
  for(int i=0;i<n;i++){
    int state;
    if(tx[i]<0||tx[i]>=W||ty[i]<0||ty[i]>=H)state=2;
    else{state=w[ty[i]*W+tx[i]]?1:0;out[ty[i]*W+tx[i]]=1;}
    C*=sf_compat(f,state);
  }
  return C;
}
static float lerp01(double q0,double q1,float C){double q=q1*C+q0*(1.0-C);if(q<0)q=0;if(q>1)q=1;return(float)q;}
static float sf_route(const SharedField*f,int a,int out,float C){return lerp01(sfget(f,kroute(a,out,0),.5),sfget(f,kroute(a,out,1),.5),C);}static float sf_life(const SharedField*f,int a,float C){return sf_amp(lerp01(sfget(f,klife(a,0),.5),sfget(f,klife(a,1),.5),C));}static float sf_split(const SharedField*f,int out,float C){return lerp01(sfget(f,ksplit(out,0),.5),sfget(f,ksplit(out,1),.5),C);}
static void sf_spawn_field(const SharedField*f,const uint8_t prev[PREV],float out[N]){for(int i=0;i<N;i++)out[i]=0.f;for(int si=0;si<PREV;si++)if(prev[si]){int sx=si%4,sy=si/4;for(int dy=-8;dy<=8;dy++)for(int dx=-8;dx<=8;dx++){double q=sfget(f,kspawn(dx,dy),0.0);if(q<=.5)continue;int ox=sx+dx,oy=sy+dy;if(ox>=0&&ox<W&&oy>=0&&oy<H&&q>out[oy*W+ox])out[oy*W+ox]=(float)q;}}}
static float sf_spawn_carrier(const SharedField*f,const uint8_t prev[PREV],const uint8_t world[N]){
  double C=1.;
  for(int si=0;si<PREV;si++)if(prev[si]){int sx=si%4,sy=si/4;
    for(int dy=-8;dy<=8;dy++)for(int dx=-8;dx<=8;dx++){double q=sfget(f,kspawn(dx,dy),0.0);if(q<=.5)continue;int ox=sx+dx,oy=sy+dy;
      int state=(ox<0||ox>=W||oy<0||oy>=H)?2:(world[oy*W+ox]?1:0);
      C*=sf_compat(f,state);
    }
  }
  return(float)C;
}
static void sf_spawn(const SharedField*f,const uint8_t prev[PREV],const uint8_t*world,uint8_t*a,float g,uint8_t*go){float field[N];sf_spawn_field(f,prev,field);float C=sf_spawn_carrier(f,prev,world),gs=sf_split(f,0,C),gg=sf_split(f,1,C),gain=g*gs;*go=(uint8_t)(g*gg>.5f);for(int i=0;i<N;i++)if(gain*field[i]>.5f)a[i]=1;}
/* v0.23: no LineClear executor / hole propagation.
   A boundary-closure wave is only a relation token.  Each occupied voxel sees
   the relative vertical address to every closure token in its own column.  The
   shared field says whether that relation means persist / +1-down / disappear.
   Multiple closure waves superpose as repeated copies of the already learned
   +1 spatial effect; no row is selected or ordered. */
static float sf_cresp(const SharedField*f,int rdy,int out){return sf_amp(sfget(f,kcresp(rdy,out),.5));}
static int sf_clear_relation(SharedField*f,uint8_t*b){
  int dx[16],dy[16],nd=state_unit_dirs(b,dx,dy,16);uint8_t seed[N]={0};int any=0;
  for(int d=0;d<nd;d++){
    if(sf_amp(sfget(f,kclosure(dx[d],dy[d]),.5))<=0.f)continue;
    uint8_t q[N];if(!boundary_seed_dir(b,dx[d],dy[d],q))continue;
    for(int i=0;i<N;i++)seed[i]|=q[i];
    any=1;
  }
  if(!any)return 0;
  uint8_t before[N],out[N]={0};memcpy(before,b,N);
  for(int sy=0;sy<H;sy++)for(int x=0;x<W;x++)if(before[sy*W+x]){
    double survive=1.0,shift=0.0;
    for(int cy=0;cy<H;cy++)if(seed[cy*W+x]){
      int rdy=sy-cy;
      survive*=1.0-(double)sf_cresp(f,rdy,2);
      shift+=(double)sf_cresp(f,rdy,1);
    }
    if(survive<=.5)continue;
    int oy=sy+(int)llround(shift);
    if(oy>=0&&oy<H)out[oy*W+x]=1;
  }
  memcpy(b,out,N);return !eq(before,b,N);
}
static void sf_downstream(SharedField*f,State*s,float pending){for(int micro=0;micro<H+8;micro++){uint8_t ba[N],bw[N],bg=s->gameover;memcpy(ba,s->active,N);memcpy(bw,s->world,N);sf_spawn(f,s->preview,s->world,s->active,pending,&s->gameover);(void)sf_clear_relation(f,s->world);if(eq(ba,s->active,N)&&eq(bw,s->world,N)&&bg==s->gameover)break;}}



/* v0.21: every learning event writes directly into the same field.  Observers
   may expose candidate physical relations, but there are no family-specific
   learned parameter stores and no export/consolidation step. */
static int sf_geom_reconstruct_hyp(const SharedField*f,int act,const uint8_t*a,int sx,int sy,uint8_t*out){
  int x[64],y[64],n=gp_collect(a,x,y,64);memset(out,0,N);if(n<=0||n>64)return 0;
  int bx=sf_geom_basis(f,act,0),by=sf_geom_basis(f,act,1),gdx,gdy;if(bx<0||by<0||!sf_geom_gauge(f,act,&gdx,&gdy))return 0;
  int bxx=bx==0,bxy=bx==1,byx=by==0,byy=by==1,rx[64],ry[64];rx[0]=ry[0]=0;
  for(int i=1;i<n;i++){int dx=x[i]-x[0],dy=y[i]-y[0];rx[i]=dx*sx*bxx+dy*sy*byx;ry[i]=dx*sx*bxy+dy*sy*byy;}
  int mnx=rx[0],mny=ry[0];for(int i=1;i<n;i++){if(rx[i]<mnx)mnx=rx[i];if(ry[i]<mny)mny=ry[i];}
  int mx,my;gp_minxy(a,&mx,&my);int baseX=mx+gdx-mnx,baseY=my+gdy-mny;
  for(int i=0;i<n;i++){int tx=baseX+rx[i],ty=baseY+ry[i];if(tx<0||tx>=W||ty<0||ty>=H)return 0;out[ty*W+tx]=1;}return 1;
}
static void sf_observe_geom(SharedField*f,int act,const uint8_t*a,const uint8_t*t){
  int n=0,nt=0;for(int i=0;i<N;i++){n+=a[i];nt+=t[i];}if(n<=0||n!=nt)return;
  if(n==1){int x[2],y[2],u[2],v[2];gp_collect(a,x,y,2);gp_collect(t,u,v,2);int dx=u[0]-x[0],dy=v[0]-y[0];if(abs(dx)<=1&&abs(dy)<=1)for(int yy=-1;yy<=1;yy++)for(int xx=-1;xx<=1;xx++)sfcredit(f,kgauge(act,xx,yy),1.0,xx==dx&&yy==dy);}
  if(n==2){int ia=gp_axis_domino(a),oa=gp_axis_domino(t);if(ia>=0&&oa>=0)for(int j=0;j<2;j++)sfcredit(f,kbasis(act,ia,j),1.0,j==oa);}
  if(n>=3&&!eq(a,t,N)){
    uint8_t c[2][2][N];double L[2][2];for(int ix=0;ix<2;ix++)for(int iy=0;iy<2;iy++){int sx=ix?1:-1,sy=iy?1:-1;if(!sf_geom_reconstruct_hyp(f,act,a,sx,sy,c[ix][iy]))L[ix][iy]=1000.;else L[ix][iy]=(double)gp_hamming(c[ix][iy],t);}
    double px=sfget(f,kphase(act,0),.5),py=sfget(f,kphase(act,1),.5);double xp=py*L[1][1]+(1-py)*L[1][0],xm=py*L[0][1]+(1-py)*L[0][0];double yp=px*L[1][1]+(1-px)*L[0][1],ym=px*L[1][0]+(1-px)*L[0][0];double wx=fabs(xp-xm),wy=fabs(yp-ym);if(wx>0)sfcredit(f,kphase(act,0),wx,xp<xm);if(wy>0)sfcredit(f,kphase(act,1),wy,yp<ym);
  }
}
static void sf_train_geom(SharedField*f,int events){RNG r={0x611ULL};for(int q=0;q<events;q++){int z=ri(&r,100),cells=z<30?1:(z<65?2:3),act=ri(&r,ACTS);uint8_t a[N],t[N];geom_make_connected(&r,a,cells);env_geom_micro(act,a,t);sf_observe_geom(f,act,a,t);}}
static void sf_train_spawn_rel(SharedField*f,int ep){for(int e=0;e<ep;e++)for(int si=0;si<PREV;si++){uint8_t prev[PREV]={0},active[N];prev[si]=1;env_spawn_visible_micro(prev,active);int sx=si%4,sy=si/4;for(int oi=0;oi<N;oi++)if(active[oi]){int ox=oi%W,oy=oi/W;sfcredit(f,kspawn(ox-sx,oy-sy),1.0,1);}}}
static void sf_train_compat_direct(SharedField*f,int events){
  RNG r={0xC0111DEULL};
  for(int q=0;q<events;q++){
    State s,t;memset(&s,0,sizeof(s));
    int act=ri(&r,3); /* anonymous translation carriers are enough; relation is reused by rotation/spawn */
    int x=1+ri(&r,W-2),y=1+ri(&r,H-2);
    if(act==0&&ri(&r,3)==0)x=0;
    if(act==1&&ri(&r,3)==0)x=W-1;
    if(act==2&&ri(&r,3)==0)y=H-1;
    s.active[y*W+x]=1;
    int dx=act==0?-1:act==1?1:0,dy=act==2?1:0,tx=x+dx,ty=y+dy;
    int state=(tx<0||tx>=W||ty<0||ty>=H)?2:0;
    if(state==0 && ri(&r,2)){s.world[ty*W+tx]=1;state=1;}
    uint8_t cand[N];int gx[64],gy[64],n=sf_geom_targets(f,act,s.active,gx,gy,64);if(n!=1)continue;
    memset(cand,0,N);if(gx[0]>=0&&gx[0]<W&&gy[0]>=0&&gy[0]<H)cand[gy[0]*W+gx[0]]=1;
    t=s; (void)real_micro_step(&t,act);
    int success=eq(t.active,cand,N);
    sfcredit(f,kcompat(state),1.0,success);
  }
}
static void sf_train_spawn_split_direct(SharedField*f,int events){RNG r={0x5A17ULL};for(int q=0;q<events;q++){uint8_t prev[PREV]={0},world[N]={0},cand[N];int cells=1+ri(&r,8);for(int k=0;k<cells;k++)prev[ri(&r,PREV)]=1;if(!memcmp(prev,(uint8_t[PREV]){0},PREV))prev[5]=1;env_spawn_visible_micro(prev,cand);for(int k=0;k<18;k++){int x=ri(&r,W),y=ri(&r,6);world[y*W+x]=1;}int blocked=0;for(int i=0;i<N;i++)if(cand[i]&&world[i]){blocked=1;break;}float C=sf_spawn_carrier(f,prev,world);int cb=C>.5f;sfcredit(f,ksplit(0,cb),1.0,!blocked);sfcredit(f,ksplit(1,cb),1.0,blocked);}}
static void sf_train_closure_direct(SharedField*f,int ep){
  RNG r={0xC105EULL};
  for(int e=0;e<ep;e++)for(int made=0;made<4;made++){
    uint8_t before[N]={0},truth[N];for(int i=0;i<N;i++)before[i]=(uint8_t)(ri(&r,100)<8);
    int horizontal=ri(&r,2);
    if(horizontal){int y=ri(&r,H);for(int x=0;x<W;x++)before[y*W+x]=1;}
    else{int x=ri(&r,W);for(int y=0;y<H;y++)before[y*W+x]=1;}
    memcpy(truth,before,N);real_clear(truth);int changed=!eq(before,truth,N);
    int dx[16],dy[16],nd=state_unit_dirs(before,dx,dy,16);
    for(int d=0;d<nd;d++){uint8_t seed[N];if(boundary_seed_dir(before,dx[d],dy[d],seed))sfcredit(f,kclosure(dx[d],dy[d]),1.0,changed);}
  }
}
/* Raw closure-consequence micro-reality.  There is no clear-row label and no
   propagation target.  A marker voxel and a closure wave are observed before,
   then the real next screen directly credits persist/down/disappear relations. */
static void sf_train_clear_response(SharedField*f,int events){
  RNG r={0xC1EA23ULL};
  for(int q=0;q<events;q++){
    uint8_t before[N]={0},truth[N];int cy=1+ri(&r,H-2),x=ri(&r,W);
    for(int xx=0;xx<W;xx++)before[cy*W+xx]=1;
    int mode=ri(&r,3);int sy=cy;
    if(mode==0){sy=ri(&r,cy);before[sy*W+x]=1;} /* marker above */
    else if(mode==1){sy=cy+1+ri(&r,H-cy-1);before[sy*W+x]=1;} /* below */
    memcpy(truth,before,N);real_clear(truth);
    int rdy=sy-cy;
    int persist=(sy>=0&&sy<H)&&truth[sy*W+x];
    int down=(sy+1<H)&&truth[(sy+1)*W+x]&&!truth[sy*W+x];
    int gone=!persist&&!down;
    sfcredit(f,kcresp(rdy,0),1.0,persist);
    sfcredit(f,kcresp(rdy,1),1.0,down);
    sfcredit(f,kcresp(rdy,2),1.0,gone);
  }
}
static float sf_action_carrier(const SharedField*f,const State*s,int act){uint8_t cand[N];return sf_geom_candidate(f,act,s->active,s->world,cand);}
static void sf_train_routes_direct(SharedField*f,int events){RNG r={0xB012ULL};for(int q=0;q<events;q++){State s,t;make_life_state(&r,&s);int act=ri(&r,ACTS);uint8_t cand[N];float C=sf_geom_candidate(f,act,s.active,s.world,cand);env_route_micro(&s,act,&t);int worldchg=!eq(s.world,t.world,N);int tc=!worldchg&&eq(t.active,cand,N),tp=!worldchg&&eq(t.active,s.active,N),tw=worldchg,cb=C>.5f;sfcredit(f,kroute(act,0,cb),1.0,tc);sfcredit(f,kroute(act,1,cb),1.0,tp);sfcredit(f,kroute(act,2,cb),1.0,tw);}}
static void sf_train_life_direct(SharedField*f,int events){RNG r={0xA17EULL};for(int q=0;q<events;q++){State s,one,fin;make_life_state(&r,&s);int act=ri(&r,ACTS);one=s;fin=s;float C=sf_action_carrier(f,&s,act);(void)real_micro_step(&one,act);(void)real_step(&fin,act);int cont=!eq(one.active,fin.active,N)||!eq(one.world,fin.world,N)||one.gameover!=fin.gameover;sfcredit(f,klife(act,C>.5f),1.0,cont);}}
static void sf_train_all_direct(SharedField*f){memset(f,0,sizeof(*f));sf_train_geom(f,100000);sf_train_spawn_rel(f,1000);sf_train_compat_direct(f,30000);sf_train_spawn_split_direct(f,30000);sf_train_closure_direct(f,300);sf_train_clear_response(f,30000);sf_train_routes_direct(f,60000);sf_train_life_direct(f,40000);}

#define RAW_W 15
#define RAW_H 20
#define RAW_N (RAW_W*RAW_H)
static int ridx(int x,int y){return y*RAW_W+x;}static void render_raw(const State*s,RawFrame*f){memset(f,0,sizeof(*f));for(int y=0;y<H;y++)for(int x=0;x<W;x++)f->px[ridx(x,y)]=(uint8_t)(s->active[y*W+x]|s->world[y*W+x]);for(int y=0;y<4;y++)for(int x=0;x<4;x++)f->px[ridx(11+x,y)]=s->preview[y*4+x];f->px[ridx(14,19)]=s->gameover;}static void trace_birth(const RawFrame*p,const RawFrame*c,uint8_t t[N]){for(int y=0;y<H;y++)for(int x=0;x<W;x++){int k=ridx(x,y);t[y*W+x]=(uint8_t)(c->px[k]&&!p->px[k]);}}static void bin_to_state(const BinaryState*b,State*s){memset(s,0,sizeof(*s));for(int y=0;y<H;y++)for(int x=0;x<W;x++){uint8_t q=b->frame.px[ridx(x,y)];s->active[y*W+x]=(uint8_t)(q&&b->trace[y*W+x]);s->world[y*W+x]=(uint8_t)(q&&!b->trace[y*W+x]);}for(int y=0;y<4;y++)for(int x=0;x<4;x++)s->preview[y*4+x]=b->frame.px[ridx(11+x,y)];s->gameover=b->frame.px[ridx(14,19)];}static void state_to_bin(const State*s,BinaryState*b){render_raw(s,&b->frame);memcpy(b->trace,s->active,N);}static int raw_eq(const RawFrame*a,const RawFrame*b){return !memcmp(a,b,sizeof(*a));}static ActionWave opwave(int a){ActionWave w={{0}};w.v[a]=1;return w;}
static int sf_binary_step(SharedField*f,BinaryState*b,const ActionWave*in){State s;bin_to_state(b,&s);float ac[ACTS];for(int a=0;a<ACTS;a++)ac[a]=in->v[a];int locked=0;for(int micro=0;micro<64;micro++){float total=0;for(int a=0;a<ACTS;a++)total+=ac[a];if(total<1e-6f)break;uint8_t src[N];memcpy(src,s.active,N);double aa[N]={0},wa[N]={0};float next[ACTS]={0},lockamp=0;for(int a=0;a<ACTS;a++){float w=ac[a];if(w<1e-7f)continue;uint8_t cand[N];float C=sf_geom_candidate(f,a,src,s.world,cand);float gc=sf_route(f,a,0,C),gp=sf_route(f,a,1,C),gw=sf_route(f,a,2,C);for(int i=0;i<N;i++){aa[i]+=w*(gc*cand[i]+gp*src[i]);wa[i]+=w*gw*src[i];}lockamp+=w*gw;next[a]=w*sf_life(f,a,C);}for(int i=0;i<N;i++){s.active[i]=(uint8_t)(aa[i]>.5);if(wa[i]>.5)s.world[i]=1;}if(lockamp>.5){locked=1;sf_downstream(f,&s,lockamp);}for(int a=0;a<ACTS;a++)ac[a]=next[a];if(s.gameover)break;}state_to_bin(&s,b);return locked;}
typedef struct{unsigned long long n,ok,locks;int epok,fe,ft;}SStat;static SStat run_shared(SharedField*f,int eps,int horizon,uint64_t seed,int zero_field){RNG r={seed};SStat st={0};st.fe=st.ft=-1;SharedField bak=*f;if(zero_field)memset(f,0,sizeof(*f));for(int ep=0;ep<eps;ep++){State real;init_episode(&r,&real);RawFrame z={{0}},cur;render_raw(&real,&cur);BinaryState mod;mod.frame=cur;trace_birth(&z,&cur,mod.trace);int good=1;for(int t=0;t<horizon;t++){int u=ri(&r,100),a=u<18?0:u<36?1:u<50?3:u<70?2:4;int lr=real_step(&real,a);RawFrame truth;render_raw(&real,&truth);ActionWave w=opwave(a);int lm=sf_binary_step(f,&mod,&w);int ok=(lr==lm)&&raw_eq(&truth,&mod.frame);st.n++;st.ok+=ok;if(lr)st.locks++;if(!ok){good=0;if(st.fe<0){st.fe=ep;st.ft=t;}break;}if(lr){if(real.gameover)break;uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(real.preview,np,PREV);render_raw(&real,&truth);mod.frame=truth;}}st.epok+=good;}if(zero_field)*f=bak;return st;}
int main(void){SharedField f;sf_train_all_direct(&f);printf("BPC Binary WorldFit v0.23 | relation-superposition closure consequence | no hole propagation | relations=%d\n",f.n);unsigned long long ok=0,n=0;for(int s=0;s<8;s++){SStat x=run_shared(&f,1000,120,98765ULL+200003ULL*(uint64_t)s,0);printf("NORMAL %llu/%llu=%.6f%% epok=%d locks=%llu first=%d:%d\n",x.ok,x.n,x.n?100.0*(double)x.ok/x.n:0.0,x.epok,x.locks,x.fe,x.ft);ok+=x.ok;n+=x.n;}printf("NORMAL_TOTAL %llu/%llu=%.6f%%\n",ok,n,100.0*(double)ok/n);SStat off=run_shared(&f,100,120,999001ULL,1);printf("FIELD_OFF %llu/%llu=%.6f%%\n",off.ok,off.n,off.n?100.0*(double)off.ok/off.n:0.0);printf("COMPAT empty=%.6f occupied=%.6f boundary=%.6f\n",sfget(&f,kcompat(0),.5),sfget(&f,kcompat(1),.5),sfget(&f,kcompat(2),.5));return 0;}