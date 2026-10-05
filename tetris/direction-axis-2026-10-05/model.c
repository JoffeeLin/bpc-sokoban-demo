#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "environment.h"

#define RW 15
#define RH 20
#define RN (RW*RH)
#define SFCAP 512

typedef struct{uint64_t key;double yes,total;uint8_t used;}SFCell;
/* The index accelerates ordinary field-address lookup; it stores no learned
   value, role, action rule or state prediction. Entries remain the same cells. */
typedef struct{SFCell c[SFCAP];int n;uint16_t slot[SFCAP*2];}SharedField;
typedef struct{uint8_t px[RN];}RawFrame;
typedef struct{RawFrame frame;uint8_t trace[N];}BinaryState;
typedef struct{float v[ACTS];}ActionWave;

static uint64_t h64(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static SFCell* sffind(SharedField*f,uint64_t k,int create){unsigned i=(unsigned)k&(SFCAP*2-1);while(f->slot[i]){SFCell*e=&f->c[f->slot[i]-1];if(e->key==k)return e;i=(i+1)&(SFCAP*2-1);}if(!create)return NULL;if(f->n>=SFCAP){fprintf(stderr,"shared field full\n");exit(5);}f->slot[i]=(uint16_t)(f->n+1);SFCell*e=&f->c[f->n++];memset(e,0,sizeof(*e));e->key=k;e->used=1;return e;}
static double sfprob(const SFCell*e){return e?(e->yes+1.0)/(e->total+2.0):.5;}
static double sfget(const SharedField*f0,uint64_t k,double def){SharedField*f=(SharedField*)f0;SFCell*e=sffind(f,k,0);return e?sfprob(e):def;}
static void sfcredit(SharedField*f,uint64_t k,double w,int target){if(w<=0)return;SFCell*e=sffind(f,k,1);e->total+=w;e->yes+=w*(!!target);}

enum{PT_ACTION=1,PT_ACTION_NEXT=2,PT_REL=3,PT_FEAS=6,PT_ROUTE=7,PT_CHANNEL=8,PT_BOUNDARY=9,PT_PROPOSAL=10,PT_DESTSTATE=11,PT_ADDRREL=12,PT_EFFECT=13};
static uint64_t primtok(int kind,int a,int b,int c){return h64(((uint64_t)(kind&255)<<48)|((uint64_t)(a&255)<<32)|((uint64_t)(b&255)<<16)|(uint64_t)(c&255));}
static uint64_t wavecollide(uint64_t a,uint64_t b){return h64(a^(h64(b)+0x9e3779b97f4a7c15ULL));}
static uint64_t w3(uint64_t a,uint64_t b,uint64_t c){return wavecollide(a,wavecollide(b,c));}
static uint64_t ta(int a){return primtok(PT_ACTION,a,0,0);}static uint64_t tanext(int a){return primtok(PT_ACTION_NEXT,a,0,1);}static uint64_t trel(int dx,int dy){return primtok(PT_REL,dx+32,dy+32,0);}static uint64_t tfeas(int c){return primtok(PT_FEAS,c,0,0);}static uint64_t troute(int o){return primtok(PT_ROUTE,o,0,0);}static uint64_t tchan(int a,int b){return primtok(PT_CHANNEL,a,b,0);}static uint64_t tboundary(int dx,int dy){return primtok(PT_BOUNDARY,dx+2,dy+2,0);}static uint64_t tproposal(void){return primtok(PT_PROPOSAL,0,0,0);}static uint64_t tdest(int s){return primtok(PT_DESTSTATE,s,0,0);}static uint64_t taddrrel(int r){return primtok(PT_ADDRREL,r,0,0);}static uint64_t teffect(int e){return primtok(PT_EFFECT,e,0,0);}
/* No function-family namespace: keys are collisions of the primitive waves that
   actually participate in the relation. */
static uint64_t kgauge(int a,int dx,int dy){return wavecollide(ta(a),trel(dx,dy));}
/* Spatial vocabulary is the physical one-hop lattice, shared by every action.
   Ordinary visible transitions write co-occurrence probabilities of unordered
   local relation pairs; there is no old global basis/phase observer or transform
   candidate winner. The physical minimum-address anchor is still provided.  Runtime reads every supported relation simultaneously. */
static uint64_t pair_id(int ax,int ay,int bx,int by){uint64_t a=trel(ax,ay),b=trel(bx,by);return a<b?wavecollide(a,b):wavecollide(b,a);}
static uint64_t kpairmap(int act,int ax,int ay,int bx,int by,int cx,int cy,int dx,int dy){return w3(ta(act),pair_id(ax,ay,bx,by),pair_id(cx,cy,dx,dy));}
static int physical_dirs(int dx[],int dy[]){int n=0;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)if(abs(x)+abs(y)==1){dx[n]=x;dy[n++]=y;}return n;}
static int local_shift(const SharedField*f,int act,double*ox,double*oy){double z=0,x=0,y=0;for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){double w=fmax(0,2*sfget(f,kgauge(act,dx,dy),.5)-1);z+=w;x+=w*dx;y+=w*dy;}if(z<=0)return 0;*ox=x/z;*oy=y/z;return 1;}
static int local_vector(const SharedField*f,int act,int rx,int ry,double*ox,double*oy){int dx[4],dy[4];physical_dirs(dx,dy);double sx=0,sy=0;int evidence=0;for(int q=0;q<4;q++){if(dx[q]==rx&&dy[q]==ry)continue;double x=0,y=0,z=0;for(int i=0;i<4;i++)for(int j=i+1;j<4;j++){double w=fmax(0,2*sfget(f,kpairmap(act,rx,ry,dx[q],dy[q],dx[i],dy[i],dx[j],dy[j]),.5)-1);x+=w*(dx[i]+dx[j]);y+=w*(dy[i]+dy[j]);z+=w;}if(z>0){sx+=x/z;sy+=y/z;evidence++;}}double mag=hypot(sx,sy);if(!evidence||mag<1e-9)return 0;*ox=sx/mag;*oy=sy/mag;return 1;}
static uint64_t geom_effect_wave(const SharedField*f,int act){double gx=0,gy=0,x=0,y=0;int dx[4],dy[4];physical_dirs(dx,dy);(void)local_shift(f,act,&gx,&gy);uint64_t w=trel((int)lround(gx),(int)lround(gy));for(int d=0;d<4;d++){x=y=0;(void)local_vector(f,act,dx[d],dy[d],&x,&y);w=wavecollide(w,wavecollide(trel(dx[d],dy[d]),trel((int)lround(x),(int)lround(y))));}return w;}
static int sf_geom_targets(const SharedField*f,int act,const uint8_t*a,int tx[],int ty[],int cap){
  int x[64],y[64],n=gp_collect(a,x,y,64),ix[N],dx[4],dy[4],mx,my;double gx,gy,vx[4],vy[4],ox[64]={0},oy[64]={0},px[64],py[64];
  if(n<=0||n>64||n>cap||!local_shift(f,act,&gx,&gy)){return -1;}
  physical_dirs(dx,dy);gp_minxy(a,&mx,&my);for(int i=0;i<N;i++)ix[i]=-1;for(int i=0;i<n;i++)ix[y[i]*W+x[i]]=i;
  for(int d=0;d<4;d++)if(!local_vector(f,act,dx[d],dy[d],&vx[d],&vy[d]))return -1;
  for(int pass=0;pass<N*8;pass++){double cx=0,cy=0,delta=0;for(int i=0;i<n;i++){double sx=0,sy=0,z=0;for(int d=0;d<4;d++){int u=x[i]+dx[d],v=y[i]+dy[d];if(u<0||u>=W||v<0||v>=H)continue;int j=ix[v*W+u];if(j<0)continue;sx+=ox[j]-vx[d];sy+=oy[j]-vy[d];z++;}px[i]=z?.5*(ox[i]+sx/z):ox[i];py[i]=z?.5*(oy[i]+sy/z):oy[i];cx+=px[i];cy+=py[i];}cx/=n;cy/=n;for(int i=0;i<n;i++){px[i]-=cx;py[i]-=cy;double d=fabs(px[i]-ox[i])+fabs(py[i]-oy[i]);if(d>delta)delta=d;ox[i]=px[i];oy[i]=py[i];}if(delta<1e-8)break;}
  double ax=ox[0],ay=oy[0];for(int i=1;i<n;i++){if(ox[i]<ax)ax=ox[i];if(oy[i]<ay)ay=oy[i];}for(int i=0;i<n;i++){tx[i]=mx+(int)lround(gx+ox[i]-ax);ty[i]=my+(int)lround(gy+oy[i]-ay);}return n;
}
static uint64_t kroute(const SharedField*f,int a,int out,int c){return w3(geom_effect_wave(f,a),tfeas(c),troute(out));}
static uint64_t klife(int a,int c){return w3(ta(a),tfeas(c),tanext(a));}
static uint64_t ksplit(int out,int c){return wavecollide(tfeas(c),troute(out));}
static uint64_t kspawn(int dx,int dy){return wavecollide(tchan(2,0),trel(dx,dy));}
static uint64_t kclosure(int dx,int dy){return wavecollide(tboundary(dx,dy),trel(dx,dy));}
static uint64_t kcompat(int state){return wavecollide(tproposal(),tdest(state));}
static uint64_t kcresp(int rel,int out){return wavecollide(taddrrel(rel),teffect(out));}
static uint64_t kpairgate(int r1,int r2,int effect){if(r1>r2){int t=r1;r1=r2;r2=t;}return wavecollide(w3(taddrrel(r1),taddrrel(r2),teffect(effect)),teffect(effect));}
static uint64_t kjointeff(int rel){return w3(taddrrel(rel),teffect(2),teffect(1));}
/* The ordering and collinearity are physical projections along the learned
   displacement wave, with no preferred screen axis. The three ordinal states
   remain inherited vocabulary; they are not claimed to have self-generated. */
static int address_projection(int sx,int sy,int cx,int cy,double vx,double vy){double t=(sx-cx)*vx+(sy-cy)*vy;return fabs(t)<1e-9?0:t<0?1:2;}
static uint64_t kdrift(int dx,int dy){return wavecollide(teffect(1),trel(dx,dy));}


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
static float sf_route(const SharedField*f,int a,int out,float C){return lerp01(sfget(f,kroute(f,a,out,0),.5),sfget(f,kroute(f,a,out,1),.5),C);}static float sf_life(const SharedField*f,int a,float C){return sf_amp(lerp01(sfget(f,klife(a,0),.5),sfget(f,klife(a,1),.5),C));}static float sf_split(const SharedField*f,int out,float C){return lerp01(sfget(f,ksplit(out,0),.5),sfget(f,ksplit(out,1),.5),C);}
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
/* Boundary contact propagates over occupied lattice neighbours. Its learned
   coupling is inherited. No row-count or special three-line repair is here. */
static void boundary_reach_one_side(const uint8_t*b,int dx,int dy,uint8_t wave[N]){
  memset(wave,0,N);
  for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(b[y*W+x]){
    int px=x-dx,py=y-dy;
    if(px<0||px>=W||py<0||py>=H)wave[y*W+x]=1;
  }
  for(int step=0;step<N;step++){
    uint8_t next[N];memcpy(next,wave,N);int changed=0;
    for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(wave[y*W+x]){
      int nx=x+dx,ny=y+dy;
      if(nx>=0&&nx<W&&ny>=0&&ny<H&&b[ny*W+nx]&&!next[ny*W+nx]){next[ny*W+nx]=1;changed=1;}
    }
    memcpy(wave,next,N);if(!changed)break;
  }
}
static int generic_boundary_wave(const uint8_t*b,int dx,int dy,uint8_t reached[N]){
  uint8_t a[N],z[N];boundary_reach_one_side(b,dx,dy,a);boundary_reach_one_side(b,-dx,-dy,z);
  int any=0;for(int i=0;i<N;i++){reached[i]=(uint8_t)(a[i]&&z[i]);any|=reached[i];}
  return any;
}
/* All positive direction evidence participates. This is a normalized
   physical wave, not a largest-probability candidate selection. With no
   evidence there is no displacement; no downward fallback is supplied. */
static void sf_drift(const SharedField*f,double*vx,double*vy){int dx[4],dy[4];physical_dirs(dx,dy);*vx=*vy=0;for(int d=0;d<4;d++){double p=sf_amp(sfget(f,kdrift(dx[d],dy[d]),.5));*vx+=p*dx[d];*vy+=p*dy[d];}double n=hypot(*vx,*vy);if(n>0){*vx/=n;*vy/=n;}}
/* Exactly this propagator is used for prediction and for each physical
   intervention during learning. Direction hypotheses carry probability,
   never an action score. Coordinates and participation amplitude are separate. */
static int sf_transport_vector(SharedField*f,uint8_t*b,double vx,double vy){
  if(hypot(vx,vy)<1e-9)return 0;
  int dx[16],dy[16],nd=state_unit_dirs(b,dx,dy,16);uint8_t seed[N]={0};int any=0;
  for(int d=0;d<nd;d++){if(sf_amp(sfget(f,kclosure(dx[d],dy[d]),.5))<=0)continue;uint8_t q[N];if(generic_boundary_wave(b,dx[d],dy[d],q)){for(int i=0;i<N;i++)seed[i]|=q[i];any=1;}}
  if(!any)return 0;
  uint8_t before[N];double out[N]={0};memcpy(before,b,N);
  for(int sy=0;sy<H;sy++)for(int sx=0;sx<W;sx++)if(before[sy*W+sx]){
    double survive=1,shift=0;int rp[3]={0};
    for(int j=0;j<N;j++)if(seed[j]){int cx=j%W,cy=j/W;if(fabs((sx-cx)*vy-(sy-cy)*vx)>1e-9)continue;int rel=address_projection(sx,sy,cx,cy,vx,vy);rp[rel]=1;double joint=sf_amp(sfget(f,kjointeff(rel),.5)),death=sf_amp(sfget(f,kcresp(rel,2),.5)),birth=sf_amp(sfget(f,kcresp(rel,1),.5));survive*=1-fmax(death,joint);shift+=fmax(birth,joint);}
    double gate=1;for(int a=0;a<3;a++)for(int d=a+1;d<3;d++)if(rp[a]&&rp[d])gate*=sfget(f,kpairgate(a,d,1),1);
    double move=fmin(1,shift),stay=survive*(1-move);int i=sy*W+sx,ox=sx+(int)llround(shift*vx),oy=sy+(int)llround(shift*vy);if(stay>out[i])out[i]=stay;if(ox>=0&&ox<W&&oy>=0&&oy<H&&move*gate>out[oy*W+ox])out[oy*W+ox]=move*gate;
  }
  for(int i=0;i<N;i++)b[i]=(uint8_t)(out[i]>.5);
  return !eq(before,b,N);
}
static int sf_clear_relation(SharedField*f,uint8_t*b){double vx,vy;sf_drift(f,&vx,&vy);return sf_transport_vector(f,b,vx,vy);}

/* Every downstream relation is evaluated on every microstep. The event
   carrier scales a proposed state change continuously; it never selects which
   solver to run. Discrete conversion is only at voxel/event measurement. */
static void sf_downstream(SharedField*f,State*s,float carrier){
  for(int micro=0;micro<H+8;micro++){
    uint8_t ba[N],bw[N],proposal[N],bg=s->gameover;memcpy(ba,s->active,N);memcpy(bw,s->world,N);memcpy(proposal,s->world,N);
    sf_spawn(f,s->preview,s->world,s->active,carrier,&s->gameover);
    (void)sf_clear_relation(f,proposal);
    for(int i=0;i<N;i++)s->world[i]=(uint8_t)(((1.0f-carrier)*bw[i]+carrier*proposal[i])>.5f);
    if(eq(ba,s->active,N)&&eq(bw,s->world,N)&&bg==s->gameover)break;
  }
}

#define RAW_W 15
#define RAW_H 20
#define RAW_N (RAW_W*RAW_H)
static int ridx(int x,int y){return y*RAW_W+x;}static void render_raw(const State*s,RawFrame*f){memset(f,0,sizeof(*f));for(int y=0;y<H;y++)for(int x=0;x<W;x++)f->px[ridx(x,y)]=(uint8_t)(s->active[y*W+x]|s->world[y*W+x]);for(int y=0;y<4;y++)for(int x=0;x<4;x++)f->px[ridx(11+x,y)]=s->preview[y*4+x];f->px[ridx(14,19)]=s->gameover;}static void trace_birth(const RawFrame*p,const RawFrame*c,uint8_t t[N]){for(int y=0;y<H;y++)for(int x=0;x<W;x++){int k=ridx(x,y);t[y*W+x]=(uint8_t)(c->px[k]&&!p->px[k]);}}static void bin_to_state(const BinaryState*b,State*s){memset(s,0,sizeof(*s));for(int y=0;y<H;y++)for(int x=0;x<W;x++){uint8_t q=b->frame.px[ridx(x,y)];s->active[y*W+x]=(uint8_t)(q&&b->trace[y*W+x]);s->world[y*W+x]=(uint8_t)(q&&!b->trace[y*W+x]);}for(int y=0;y<4;y++)for(int x=0;x<4;x++)s->preview[y*4+x]=b->frame.px[ridx(11+x,y)];s->gameover=b->frame.px[ridx(14,19)];}static void state_to_bin(const State*s,BinaryState*b){render_raw(s,&b->frame);memcpy(b->trace,s->active,N);}static int raw_eq(const RawFrame*a,const RawFrame*b){return !memcmp(a,b,sizeof(*a));}static ActionWave opwave(int a){ActionWave w={{0}};w.v[a]=1;return w;}
static int sf_binary_step(SharedField*f,BinaryState*b,const ActionWave*in){State s;bin_to_state(b,&s);float ac[ACTS];for(int a=0;a<ACTS;a++)ac[a]=in->v[a];int locked=0;for(int micro=0;micro<64;micro++){float total=0;for(int a=0;a<ACTS;a++)total+=ac[a];if(total<1e-6f)break;uint8_t src[N];memcpy(src,s.active,N);double aa[N]={0},wa[N]={0};float next[ACTS]={0},lockamp=0;for(int a=0;a<ACTS;a++){float w=ac[a];if(w<1e-7f)continue;uint8_t cand[N];float C=sf_geom_candidate(f,a,src,s.world,cand);float gc=sf_route(f,a,0,C),gp=sf_route(f,a,1,C),gw=sf_route(f,a,2,C);for(int i=0;i<N;i++){aa[i]+=w*(gc*cand[i]+gp*src[i]);wa[i]+=w*gw*src[i];}lockamp+=w*gw;next[a]=w*sf_life(f,a,C);}for(int i=0;i<N;i++){s.active[i]=(uint8_t)(aa[i]>.5);if(wa[i]>.5)s.world[i]=1;}locked|=(lockamp>.5f);sf_downstream(f,&s,lockamp);for(int a=0;a<ACTS;a++)ac[a]=next[a];if(s.gameover)break;}state_to_bin(&s,b);return locked;}

static void sf_mid(SharedField*f,const State*src,int act,State*mid){*mid=*src;uint8_t base[N],cand[N];memcpy(base,mid->active,N);float C=sf_geom_candidate(f,act,base,mid->world,cand),gc=sf_route(f,act,0,C),gp=sf_route(f,act,1,C),gw=sf_route(f,act,2,C);for(int i=0;i<N;i++){mid->active[i]=(uint8_t)((gc*cand[i]+gp*base[i])>.5f);if(gw*base[i]>.5f)mid->world[i]=1;}}
