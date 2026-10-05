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
static int local_pairs(const uint8_t*b,int present[4][4]){int dx[4],dy[4],nd=physical_dirs(dx,dy),n=0;memset(present,0,16*sizeof(int));for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(b[y*W+x]){int hit[4]={0};for(int d=0;d<nd;d++){int u=x+dx[d],v=y+dy[d];hit[d]=u>=0&&u<W&&v>=0&&v<H&&b[v*W+u];}for(int i=0;i<nd;i++)for(int j=i+1;j<nd;j++)if(hit[i]&&hit[j]&&!present[i][j]){present[i][j]=1;n++;}}return n;}
static void local_observe(SharedField*f,int act,const uint8_t*before,const uint8_t*after,int unit){
  int mx,my,nx,ny,dx[4],dy[4],ip[4][4],op[4][4];gp_minxy(before,&mx,&my);gp_minxy(after,&nx,&ny);int gx=nx-mx,gy=ny-my;
  if(unit){gx=(gx>0)-(gx<0);gy=(gy>0)-(gy<0);}if(abs(gx)>1||abs(gy)>1)return;
  for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)sfcredit(f,kgauge(act,x,y),1.0,x==gx&&y==gy);
  physical_dirs(dx,dy);local_pairs(before,ip);local_pairs(after,op);
  for(int i=0;i<4;i++)for(int j=i+1;j<4;j++)if(ip[i][j])for(int u=0;u<4;u++)for(int v=u+1;v<4;v++)sfcredit(f,kpairmap(act,dx[i],dy[i],dx[j],dy[j],dx[u],dy[u],dx[v],dy[v]),1.0,op[u][v]);
}
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
/* Only executed game transitions enter this observer. No synthetic tiny-shape
   curriculum, hidden pivot, piece catalogue, correspondence label or score. */
static void sf_train_geom(SharedField*f,int events){RNG r={0x440044ULL};State s;init_episode(&r,&s);int direct=0,macro=0;for(int e=0;e<events;e++){if(s.gameover)init_episode(&r,&s);int act=ri(&r,ACTS);State before=s,truth=s;int locked=real_step(&truth,act),na=0,nt=0;for(int i=0;i<N;i++){na+=!!before.active[i];nt+=!!truth.active[i];}if(na>0&&na==nt&&eq(before.world,truth.world,N)&&!eq(before.active,truth.active,N)){local_observe(f,act,before.active,truth.active,0);direct++;}else{uint8_t added[N]={0};int removed=0,count=0;for(int i=0;i<N;i++){added[i]=(uint8_t)(truth.world[i]&&!before.world[i]);count+=added[i];removed+=before.world[i]&&!truth.world[i];}if(!removed&&na>0&&count==na){local_observe(f,act,before.active,added,1);macro++;}}s=truth;if(locked&&!s.gameover){uint8_t p[PREV];preview_shape(ri(&r,7),p);memcpy(s.preview,p,PREV);}}
  printf("LOCAL_GEOMETRY real_events=%d direct=%d macro=%d relations=%d\n",events,direct,macro,f->n);for(int a=0;a<ACTS;a++){double gx=0,gy=0;int ok=local_shift(f,a,&gx,&gy);printf("LOCAL action=%d shift=%.4f,%.4f known=%d",a,gx,gy,ok);int dx[4],dy[4];physical_dirs(dx,dy);for(int d=0;d<4;d++){double x=0,y=0;int k=local_vector(f,a,dx[d],dy[d],&x,&y);printf(" v%d=%.4f,%.4f:%d",d,x,y,k);}putchar('\n');}
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
static int addr_vertical_relation(int sy,int cy){return sy==cy?0:(sy<cy?1:2);}


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
/* v0.23: no LineClear executor / hole propagation.
   A boundary-closure wave is only a relation token.  Each occupied voxel sees
   the relative vertical address to every closure token in its own column.  The
   shared field says whether that relation means persist / +1-down / disappear.
   Multiple closure waves superpose as repeated copies of the already learned
   +1 spatial effect; no row is selected or ordered. */
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
static double participation(const SharedField*f,uint64_t key,double fallback,int centered,uint64_t changed,double forced){if(forced>=0&&key==changed)return forced;double p=sfget(f,key,fallback);return centered?sf_amp(p):p;}
/* A conditional event carries a full displacement and a probability amplitude.
   Multiplying its coordinate by probability would create a different event.
   Correlated proposals at the same physical address merge by maximum amplitude,
   so repeated copies of one uncertain event cannot manufacture certainty. */
static int sf_transport(SharedField*f,uint8_t*b,uint64_t changed,double forced){
  int dx[16],dy[16],nd=state_unit_dirs(b,dx,dy,16);uint8_t seed[N]={0};int any=0;
  for(int d=0;d<nd;d++){if(sf_amp(sfget(f,kclosure(dx[d],dy[d]),.5))<=0)continue;uint8_t q[N];if(generic_boundary_wave(b,dx[d],dy[d],q)){for(int i=0;i<N;i++)seed[i]|=q[i];any=1;}}
  if(!any)return 0;
  uint8_t before[N];double out[N]={0};memcpy(before,b,N);
  for(int sy=0;sy<H;sy++)for(int x=0;x<W;x++)if(before[sy*W+x]){
    double survive=1,shift=0;int rp[3]={0};
    for(int cy=0;cy<H;cy++)if(seed[cy*W+x]){int rel=addr_vertical_relation(sy,cy);rp[rel]=1;double joint=participation(f,kjointeff(rel),.5,1,changed,forced),death=participation(f,kcresp(rel,2),.5,1,changed,forced),birth=participation(f,kcresp(rel,1),.5,1,changed,forced);survive*=1-fmax(death,joint);shift+=fmax(birth,joint);}
    double gate=1;for(int a=0;a<3;a++)for(int d=a+1;d<3;d++)if(rp[a]&&rp[d])gate*=participation(f,kpairgate(a,d,1),1,0,changed,forced);
    double move=fmin(1,shift),stay=survive*(1-move);int i=sy*W+x,oy=sy+(int)llround(shift);if(stay>out[i])out[i]=stay;if(oy>=0&&oy<H&&move*gate>out[oy*W+x])out[oy*W+x]=move*gate;
  }
  for(int i=0;i<N;i++)b[i]=(uint8_t)(out[i]>.5);
  return !eq(before,b,N);
}
static int sf_clear_relation(SharedField*f,uint8_t*b){return sf_transport(f,b,0,-1);}

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

/* v0.21: every learning event writes directly into the same field.  Observers
   may expose candidate physical relations, but there are no family-specific
   learned parameter stores and no export/consolidation step. */
static void sf_train_spawn_rel(SharedField*f,int events){RNG r={0x5A0B1ULL};State s;init_episode(&r,&s);for(int q=0;q<events;q++){if(s.gameover)init_episode(&r,&s);int u=ri(&r,100),act=u<18?ACT_LEFT:u<36?ACT_RIGHT:u<50?ACT_ROT:u<70?ACT_DOWN:ACT_DROP;State truth=s;int locked=real_step(&truth,act);int dxs[128],dys[128],nc=0;for(int si=0;si<PREV;si++)if(s.preview[si]){int sx=si%4,sy=si/4;for(int oi=0;oi<N;oi++)if(truth.active[oi]){int ox=oi%W,oy=oi/W;add_dir(dxs,dys,&nc,128,ox-sx,oy-sy);}}int exact[128]={0},any=0;for(int j=0;j<nc;j++){uint8_t cand[N]={0};for(int si=0;si<PREV;si++)if(s.preview[si]){int sx=si%4,sy=si/4,ox=sx+dxs[j],oy=sy+dys[j];if(ox>=0&&ox<W&&oy>=0&&oy<H)cand[oy*W+ox]=1;}exact[j]=eq(cand,truth.active,N);any|=exact[j];}if(any)for(int j=0;j<nc;j++)sfcredit(f,kspawn(dxs[j],dys[j]),1.0,exact[j]);s=truth;if(locked&&!s.gameover){uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(s.preview,np,PREV);}if(s.gameover)init_episode(&r,&s);}}
/* v0.40: destination compatibility is learned only from ordinary visible play.
   No synthetic single-cell obstacle/boundary curriculum.  Geometry proposes a
   consequence; every destination-state wave that participated receives the
   observed whole-transition success/failure as ordinary residual evidence.
   Ambiguous identity proposals are skipped rather than hand-labeled. */
static void sf_reset_compat_evidence(SharedField*f){
  for(int st=0;st<3;st++){SFCell*e=sffind(f,kcompat(st),1);e->yes=0.0;e->total=0.0;}
}
static void sf_train_compat_from_visible_play(SharedField*f,int events,uint64_t seed){
  RNG r={seed};State s;init_episode(&r,&s);int credited=0,succ=0,fail=0,seen[3]={0},pos[3]={0};
  sf_reset_compat_evidence(f);
  for(int q=0;q<events;q++){
    if(s.gameover)init_episode(&r,&s);
    /* Ordinary stream: side/rotation observations are interleaved with Down so
       terrain grows naturally. Down still updates reality but is not needed for
       compatibility credit because lock may include downstream consequences. */
    int u=ri(&r,100),act=u<22?ACT_LEFT:u<44?ACT_RIGHT:u<64?ACT_ROT:ACT_DOWN;
    State before=s,truth=s;int locked=real_step(&truth,act);
    if(act==ACT_LEFT||act==ACT_RIGHT||act==ACT_ROT){
      int tx[64],ty[64],n=sf_geom_targets(f,act,before.active,tx,ty,64);
      if(n>0){
        uint8_t cand[N]={0};int present[3]={0};
        for(int i=0;i<n;i++){
          int st;
          if(tx[i]<0||tx[i]>=W||ty[i]<0||ty[i]>=H)st=2;
          else{st=before.world[ty[i]*W+tx[i]]?1:0;cand[ty[i]*W+tx[i]]=1;}
          present[st]=1;
        }
        /* If proposal equals source, a blocked identity rotation is visually
           indistinguishable from a successful identity transform: skip it. */
        if(!eq(cand,before.active,N)){
          int success=eq(truth.active,cand,N)&&eq(truth.world,before.world,N)&&truth.gameover==before.gameover;
          if(success){
            for(int st=0;st<3;st++)if(present[st]){sfcredit(f,kcompat(st),1.0,1);seen[st]++;pos[st]++;}
          }else{
            /* Generic responsibility for an AND/product carrier: a failed
               participant receives negative credit in proportion to the
               probability that all other participating waves were valid. */
            for(int st=0;st<3;st++)if(present[st]){
              double w=1.0;
              for(int ot=0;ot<3;ot++)if(ot!=st&&present[ot])w*=sfget(f,kcompat(ot),.5);
              sfcredit(f,kcompat(st),w,0);seen[st]++;
            }
          }
          credited++;succ+=success;fail+=!success;
        }
      }
    }
    s=truth;
    if(locked&&!s.gameover){uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(s.preview,np,PREV);}
    if(s.gameover)init_episode(&r,&s);
  }
  printf("VISIBLE_COMPAT credited=%d success=%d fail=%d empty=%.6f occupied=%.6f boundary=%.6f seen=%d/%d/%d pos=%d/%d/%d\n",
    credited,succ,fail,sfget(f,kcompat(0),.5),sfget(f,kcompat(1),.5),sfget(f,kcompat(2),.5),seen[0],seen[1],seen[2],pos[0],pos[1],pos[2]);
}

/* Bootstrap from actual one-step Down/Lock observations, never generated
   preview/obstacle frames. This still assumes the inherited observer's
   transient/persistent interpretation; it is not a claim of self-born roles. */
static void sf_train_spawn_split_from_play(SharedField*f,int target_locks){
  RNG r={0x5A17ULL};State real;init_episode(&r,&real);int locks=0,steps=0;
  while(locks<target_locks&&steps<target_locks*400){
    if(real.gameover)init_episode(&r,&real);
    int u=ri(&r,100),act=u<15?ACT_LEFT:u<30?ACT_RIGHT:u<42?ACT_ROT:ACT_DOWN;
    State before=real,truth=real;int locked=real_step(&truth,act);steps++;
    if(locked&&act==ACT_DOWN){
      float C=sf_spawn_carrier(f,before.preview,truth.world);int cb=C>.5f;
      sfcredit(f,ksplit(0,cb),1.0,!truth.gameover);
      sfcredit(f,ksplit(1,cb),1.0,!!truth.gameover);locks++;
    }
    real=truth;
    if(locked&&!real.gameover){uint8_t p[PREV];preview_shape(ri(&r,7),p);memcpy(real.preview,p,PREV);}
  }
  printf("VISIBLE_BOOTSTRAP locks=%d steps=%d\n",locks,steps);
}

/* No real_clear() target is exposed to the learner.  Experiences are ordinary
   visible Screen+Operation->Final Screen transitions.  The model first creates
   its own one-micro mid state.  Only the residual mid->final is allowed to give
   closure/address consequence credit. */
static int world_hdist(const uint8_t*a,const uint8_t*b){int n=0;for(int i=0;i<N;i++)n+=a[i]!=b[i];return n;}
/* Factorial hypothesis over two atomic effects: source-death and +1-birth.
   The effect is applied only to source instances that participate in the given
   anonymous address relation to a closure wave. */
/* v0.33: no persist/down/gone labels.  For each anonymous address relation, the
   shared field learns only two atomic consequences.  Credit is the marginal
   reduction of the real visible residual across all four joint hypotheses, so
   two useful effects may both receive positive credit without top-1 selection. */
/* Apply closure dynamics with one anonymous relation-pair birth gate forced to
   0 or 1.  Used only for residual-credit evaluation; no semantic label enters. */
static int sf_clear_relation_pair_override(SharedField*f,uint8_t*b,int a,int d,double value){return sf_transport(f,b,kpairgate(a,d,1),value);}

typedef struct{int a[32];int n;double score;} LearnPlan;
static int lp_append(LearnPlan*p,int a){if(p->n>=32)return 0;p->a[p->n++]=a;return 1;}
static int lp_minx(const State*s){int m=W;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x]&&x<m)m=x;return m==W?-1:m;}
static int lp_maxx(const State*s){int m=-1;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x]&&x>m)m=x;return m;}
static int lp_bits(const uint8_t*b){int n=0;for(int i=0;i<N;i++)n+=!!b[i];return n;}
static double lp_score(const State*s,int clears){if(s->gameover)return 1e12;int h[W]={0},agg=0,holes=0,bump=0,maxh=0;for(int x=0;x<W;x++){int top=-1;for(int y=0;y<H;y++)if(s->world[y*W+x]){top=y;break;}h[x]=top<0?0:H-top;agg+=h[x];if(h[x]>maxh)maxh=h[x];if(top>=0)for(int y=top+1;y<H;y++)if(!s->world[y*W+x])holes++;}for(int x=0;x<W-1;x++){int d=h[x]-h[x+1];if(d<0)d=-d;bump+=d;}return -1200.0*clears+85.0*holes+5.0*agg+4.0*bump+7.0*maxh;}
static LearnPlan lp_choose(const State*src){LearnPlan best={{0},0,1e100};for(int rot=0;rot<4;rot++){State r=*src;LearnPlan pref={{0},0,0};for(int k=0;k<rot;k++){real_step(&r,ACT_ROT);lp_append(&pref,ACT_ROT);}int mn=lp_minx(&r),mx=lp_maxx(&r);if(mn<0||mx<0)continue;int width=mx-mn+1;for(int target=0;target<=W-width;target++){State q=r;LearnPlan p=pref;int cur=lp_minx(&q),dir=target<cur?ACT_LEFT:ACT_RIGHT,steps=target<cur?cur-target:target-cur;for(int k=0;k<steps;k++){State z=q;real_step(&q,dir);lp_append(&p,dir);if(!memcmp(z.active,q.active,N))break;}if(lp_minx(&q)!=target)continue;int wb=lp_bits(q.world),ac=lp_bits(q.active);if(!real_step(&q,ACT_DROP))continue;lp_append(&p,ACT_DROP);int wa=lp_bits(q.world),num=wb+ac-wa,clears=(num>=0&&num%W==0)?num/W:0;double sc=lp_score(&q,clears)+.01*p.n;if(sc<best.score){best=p;best.score=sc;}}}if(best.n==0){best.a[0]=ACT_DROP;best.n=1;best.score=0;}return best;}

/* High-order relation coupling is born only from ordinary external-player
   Screen+Action->Screen experience.  For every relation pair actually present,
   forcing an effect gate open vs closed is compared against the real final frame;
   the lower-residual alternative receives credit. */
static void sf_predict_single_mid_no_downstream(SharedField*f,const State*src,int act,State*mid){
  *mid=*src;uint8_t base[N],cand[N];memcpy(base,mid->active,N);float C=sf_geom_candidate(f,act,base,mid->world,cand);float gc=sf_route(f,act,0,C),gp=sf_route(f,act,1,C),gw=sf_route(f,act,2,C);uint8_t na[N]={0};for(int i=0;i<N;i++){na[i]=(uint8_t)((gc*(float)cand[i]+gp*(float)base[i])>.5f);if(gw*(float)base[i]>.5f)mid->world[i]=1;}memcpy(mid->active,na,N);
}
static int sf_clear_relation_effect_override(SharedField*f,uint8_t*b,int rel,int effect,double value){uint64_t key=effect==0?kcresp(rel,2):effect==1?kcresp(rel,1):kjointeff(rel);return sf_transport(f,b,key,value);}

/* v0.38: whole-world leave-one-coupling-out credit.  No source-instance label
   is used.  Each already participating relation/effect is toggled off/on in the
   complete closure prediction; only the change in final visible residual gives
   credit.  This handles address occlusion where a dead source voxel is replaced
   immediately by another voxel at the same visible address. */
static void sf_credit_closure_global_transition(SharedField*f,const State*mid,const State*truth){
  int ebase=world_hdist(mid->world,truth->world);if(ebase<=0)return;
  int dirs_x[16],dirs_y[16],nd=state_unit_dirs(mid->world,dirs_x,dirs_y,16);int any=0;
  for(int d=0;d<nd;d++){
    uint8_t seed[N];if(!generic_boundary_wave(mid->world,dirs_x[d],dirs_y[d],seed))continue;
    any=1;sfcredit(f,kclosure(dirs_x[d],dirs_y[d]),1.0,1);
  }
  if(!any)return;
  for(int rel=0;rel<3;rel++)for(int eff=0;eff<3;eff++){
    uint8_t p0[N],p1[N];memcpy(p0,mid->world,N);memcpy(p1,mid->world,N);
    (void)sf_clear_relation_effect_override(f,p0,rel,eff,0.0);
    (void)sf_clear_relation_effect_override(f,p1,rel,eff,1.0);
    int e0=world_hdist(p0,truth->world),e1=world_hdist(p1,truth->world);
    uint64_t key=eff==0?kcresp(rel,2):(eff==1?kcresp(rel,1):kjointeff(rel));
    if(e0!=e1){double w=fabs((double)e0-(double)e1)/(double)(ebase+1);sfcredit(f,key,w,e1<e0);}
  }
}
static void sf_credit_pair_transition(SharedField*f,const State*mid,const State*truth){
  if(world_hdist(mid->world,truth->world)<=0)return;
  int dirs_x[16],dirs_y[16],nd=state_unit_dirs(mid->world,dirs_x,dirs_y,16);uint8_t seedmap[N]={0};int any=0;
  for(int d=0;d<nd;d++){uint8_t q[N];if(sf_amp(sfget(f,kclosure(dirs_x[d],dirs_y[d]),.5))>0.f&&generic_boundary_wave(mid->world,dirs_x[d],dirs_y[d],q)){for(int i=0;i<N;i++)seedmap[i]|=q[i];any=1;}}
  if(!any)return;
  int pair_present[3][3]={{0}};
  for(int sy=0;sy<H;sy++)for(int x=0;x<W;x++)if(mid->world[sy*W+x]){int rp[3]={0};for(int cy=0;cy<H;cy++)if(seedmap[cy*W+x])rp[addr_vertical_relation(sy,cy)]=1;for(int a=0;a<3;a++)for(int b=a+1;b<3;b++)if(rp[a]&&rp[b])pair_present[a][b]=1;}
  for(int a=0;a<3;a++)for(int b=a+1;b<3;b++)if(pair_present[a][b]){uint8_t p0[N],p1[N];memcpy(p0,mid->world,N);memcpy(p1,mid->world,N);(void)sf_clear_relation_pair_override(f,p0,a,b,0.0);(void)sf_clear_relation_pair_override(f,p1,a,b,1.0);int e0=world_hdist(p0,truth->world),e1=world_hdist(p1,truth->world);if(e0!=e1)sfcredit(f,kpairgate(a,b,1),1.0,e1<e0);}
}
/* Ordinary external play only. Final descent is emitted as repeated Down pulses,
   so every learning item is literally visible Screen + one Operation -> next Screen. */
static void sf_train_closure_from_slow_play(SharedField*f,int pieces,uint64_t seed,int pair_pass){
  RNG r={seed};State real;init_episode(&r,&real);int residual_events=0;
  for(int pi=0;pi<pieces;pi++){
    if(real.gameover)init_episode(&r,&real);
    LearnPlan p=lp_choose(&real);int locked=0;
    for(int j=0;j<p.n;j++){
      if(p.a[j]==ACT_DROP)break;
      State before=real,truth=real,mid;
      int lk=real_step(&truth,p.a[j]);
      sf_predict_single_mid_no_downstream(f,&before,p.a[j],&mid);
      if(pair_pass)sf_credit_pair_transition(f,&mid,&truth);else sf_credit_closure_global_transition(f,&mid,&truth);
      real=truth;
      if(lk){locked=1;break;}
    }
    while(!locked&&!real.gameover){State before=real,truth=real,mid;int lk=real_step(&truth,ACT_DOWN);sf_predict_single_mid_no_downstream(f,&before,ACT_DOWN,&mid);if(world_hdist(mid.world,truth.world)>0)residual_events++;if(pair_pass)sf_credit_pair_transition(f,&mid,&truth);else sf_credit_closure_global_transition(f,&mid,&truth);real=truth;if(lk)locked=1;}
    if(locked&&!real.gameover){uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(real.preview,np,PREV);}
  }
  printf("SLOW_PLAY pass=%d pieces=%d residual_events=%d pair01=%.6f\n",pair_pass,pieces,residual_events,sfget(f,kpairgate(0,1,1),1.0));
}

static float sf_action_carrier(const SharedField*f,const State*s,int act){uint8_t cand[N];return sf_geom_candidate(f,act,s->active,s->world,cand);}
static void sf_apply_route_hypothesis(SharedField*f,const State*s,int act,int out,State*p){*p=*s;uint8_t cand[N];(void)sf_geom_candidate(f,act,s->active,s->world,cand);if(out==0){memcpy(p->active,cand,N);}else if(out==1){memcpy(p->active,s->active,N);}else{for(int i=0;i<N;i++)if(s->active[i])p->world[i]=1;memset(p->active,0,N);sf_downstream(f,p,1.f);}}
static void sf_train_routes_direct(SharedField*f,int events){RNG r={0xB012ULL};State s;init_episode(&r,&s);for(int q=0;q<events;q++){if(s.gameover)init_episode(&r,&s);int u=ri(&r,100),act=u<18?ACT_LEFT:u<36?ACT_RIGHT:u<50?ACT_ROT:u<70?ACT_DOWN:ACT_DROP;State truth=s;int locked=real_step(&truth,act);uint8_t dummy[N];float C=sf_geom_candidate(f,act,s.active,s.world,dummy);int cb=C>.5f,match[3]={0};for(int out=0;out<3;out++){State p;sf_apply_route_hypothesis(f,&s,act,out,&p);match[out]=eq(p.active,truth.active,N)&&eq(p.world,truth.world,N)&&p.gameover==truth.gameover;}int representable=match[0]||match[1]||match[2];if(representable)for(int out=0;out<3;out++)sfcredit(f,kroute(f,act,out,cb),1.0,match[out]);s=truth;if(locked&&!s.gameover){uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(s.preview,np,PREV);}if(s.gameover)init_episode(&r,&s);}}
static void sf_model_single_micro(SharedField*f,State*s,int act){uint8_t src[N],cand[N];memcpy(src,s->active,N);float C=sf_geom_candidate(f,act,src,s->world,cand);float gc=sf_route(f,act,0,C),gp=sf_route(f,act,1,C),gw=sf_route(f,act,2,C);uint8_t na[N]={0};for(int i=0;i<N;i++){na[i]=(uint8_t)((gc*(float)cand[i]+gp*(float)src[i])>.5f);if(gw*(float)src[i]>.5f)s->world[i]=1;}memcpy(s->active,na,N);sf_downstream(f,s,gw);}
static void sf_train_life_direct(SharedField*f,int events){RNG r={0xA17EULL};State s;init_episode(&r,&s);for(int q=0;q<events;q++){if(s.gameover)init_episode(&r,&s);int u=ri(&r,100),act=u<18?ACT_LEFT:u<36?ACT_RIGHT:u<50?ACT_ROT:u<70?ACT_DOWN:ACT_DROP;State pred=s,truth=s;float C=sf_action_carrier(f,&s,act);sf_model_single_micro(f,&pred,act);int locked=real_step(&truth,act);int cont=!eq(pred.active,truth.active,N)||!eq(pred.world,truth.world,N)||pred.gameover!=truth.gameover;sfcredit(f,klife(act,C>.5f),1.0,cont);s=truth;if(locked&&!s.gameover){uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(s.preview,np,PREV);}if(s.gameover)init_episode(&r,&s);}}
static void sf_train_all_direct(SharedField*f){memset(f,0,sizeof(*f));sf_train_geom(f,180000);sf_train_spawn_rel(f,12000);sf_train_compat_from_visible_play(f,120000,0x400040ULL);sf_train_spawn_split_from_play(f,2500);sf_train_routes_direct(f,60000);}

#define RAW_W 15
#define RAW_H 20
#define RAW_N (RAW_W*RAW_H)
static int ridx(int x,int y){return y*RAW_W+x;}static void render_raw(const State*s,RawFrame*f){memset(f,0,sizeof(*f));for(int y=0;y<H;y++)for(int x=0;x<W;x++)f->px[ridx(x,y)]=(uint8_t)(s->active[y*W+x]|s->world[y*W+x]);for(int y=0;y<4;y++)for(int x=0;x<4;x++)f->px[ridx(11+x,y)]=s->preview[y*4+x];f->px[ridx(14,19)]=s->gameover;}static void trace_birth(const RawFrame*p,const RawFrame*c,uint8_t t[N]){for(int y=0;y<H;y++)for(int x=0;x<W;x++){int k=ridx(x,y);t[y*W+x]=(uint8_t)(c->px[k]&&!p->px[k]);}}static void bin_to_state(const BinaryState*b,State*s){memset(s,0,sizeof(*s));for(int y=0;y<H;y++)for(int x=0;x<W;x++){uint8_t q=b->frame.px[ridx(x,y)];s->active[y*W+x]=(uint8_t)(q&&b->trace[y*W+x]);s->world[y*W+x]=(uint8_t)(q&&!b->trace[y*W+x]);}for(int y=0;y<4;y++)for(int x=0;x<4;x++)s->preview[y*4+x]=b->frame.px[ridx(11+x,y)];s->gameover=b->frame.px[ridx(14,19)];}static void state_to_bin(const State*s,BinaryState*b){render_raw(s,&b->frame);memcpy(b->trace,s->active,N);}static int raw_eq(const RawFrame*a,const RawFrame*b){return !memcmp(a,b,sizeof(*a));}static ActionWave opwave(int a){ActionWave w={{0}};w.v[a]=1;return w;}
static int sf_binary_step(SharedField*f,BinaryState*b,const ActionWave*in){State s;bin_to_state(b,&s);float ac[ACTS];for(int a=0;a<ACTS;a++)ac[a]=in->v[a];int locked=0;for(int micro=0;micro<64;micro++){float total=0;for(int a=0;a<ACTS;a++)total+=ac[a];if(total<1e-6f)break;uint8_t src[N];memcpy(src,s.active,N);double aa[N]={0},wa[N]={0};float next[ACTS]={0},lockamp=0;for(int a=0;a<ACTS;a++){float w=ac[a];if(w<1e-7f)continue;uint8_t cand[N];float C=sf_geom_candidate(f,a,src,s.world,cand);float gc=sf_route(f,a,0,C),gp=sf_route(f,a,1,C),gw=sf_route(f,a,2,C);for(int i=0;i<N;i++){aa[i]+=w*(gc*cand[i]+gp*src[i]);wa[i]+=w*gw*src[i];}lockamp+=w*gw;next[a]=w*sf_life(f,a,C);}for(int i=0;i<N;i++){s.active[i]=(uint8_t)(aa[i]>.5);if(wa[i]>.5)s.world[i]=1;}locked|=(lockamp>.5f);sf_downstream(f,&s,lockamp);for(int a=0;a<ACTS;a++)ac[a]=next[a];if(s.gameover)break;}state_to_bin(&s,b);return locked;}
static void sf_reset_split_evidence(SharedField*f){
  for(int out=0;out<2;out++)for(int cb=0;cb<2;cb++){
    SFCell*e=sffind(f,ksplit(out,cb),1);e->yes=0.0;e->total=0.0;
  }
}
/* v0.39: Spawn/GameOver routing is relearned only from ordinary visible play.
   Credits are emitted only on an actual one-step DOWN lock transition.  The
   model's own lock mid-state and already learned closure relaxation define the
   pre-spawn world; the real final screen supplies only the residual outcome. */
static void sf_train_split_from_visible_play(SharedField*f,int target_locks,uint64_t seed){
  RNG r={seed};State real;init_episode(&r,&real);int locks=0,gos=0,spawns=0,steps=0;
  while(locks<target_locks && steps<target_locks*400){
    if(real.gameover)init_episode(&r,&real);
    int u=ri(&r,100),act=u<15?ACT_LEFT:u<30?ACT_RIGHT:u<42?ACT_ROT:ACT_DOWN;
    State before=real,truth=real,mid;int locked=real_step(&truth,act);steps++;
    if(locked && act==ACT_DOWN){
      sf_predict_single_mid_no_downstream(f,&before,act,&mid);
      int guard=0;while(sf_clear_relation(f,mid.world)&&guard++<H*4){}
      float C=sf_spawn_carrier(f,before.preview,mid.world);int cb=C>.5f;
      int direct=!truth.gameover,complement=!!truth.gameover;
      sfcredit(f,ksplit(0,cb),1.0,direct);sfcredit(f,ksplit(1,cb),1.0,complement);
      locks++;spawns+=direct;gos+=complement;
    }
    real=truth;
    if(locked&&!real.gameover){uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(real.preview,np,PREV);}
    if(real.gameover)init_episode(&r,&real);
  }
  printf("VISIBLE_SPLIT locks=%d spawn=%d gameover=%d steps=%d C1[d=%.6f c=%.6f] C0[d=%.6f c=%.6f]\n",locks,spawns,gos,steps,sfget(f,ksplit(0,1),.5),sfget(f,ksplit(1,1),.5),sfget(f,ksplit(0,0),.5),sfget(f,ksplit(1,0),.5));
}
