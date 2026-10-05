#include "BPC_Binary_WorldFit_v0.59_API.h"
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#define W 10
#define H 20
#define N (W*H)
#define ACTS BPC_ACTIONS
static int eq(const uint8_t*a,const uint8_t*b,int n){return memcmp(a,b,(size_t)n)==0;}
static int gp_collect(const uint8_t*a,int x[],int y[],int cap){int n=0;for(int yy=0;yy<H;yy++)for(int xx=0;xx<W;xx++)if(a[yy*W+xx]){if(n<cap){x[n]=xx;y[n]=yy;}n++;}return n;}
static int add_dir(int dx[],int dy[],int*n,int cap,int x,int y){for(int i=0;i<*n;i++)if(dx[i]==x&&dy[i]==y)return 1;if(*n>=cap)return 0;dx[*n]=x;dy[*n]=y;(*n)++;return 1;}
static int state_unit_dirs(const uint8_t*b,int dx[],int dy[],int cap){int n=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(b[y*W+x])for(int oy=-1;oy<=1;oy++)for(int ox=-1;ox<=1;ox++){if(abs(ox)+abs(oy)!=1)continue;int nx=x+ox,ny=y+oy;if(nx>=0&&nx<W&&ny>=0&&ny<H&&b[ny*W+nx])add_dir(dx,dy,&n,cap,ox,oy);}return n;}
#define RW 15
#define RH 20
#define RN (RW*RH)
#define SFCAP 2048

typedef struct{uint64_t key;double yes,total;uint8_t used;}SFCell;
typedef struct{SFCell c[SFCAP];int n;}SharedField;
typedef BPCVisibleState BinaryState;
typedef BPCActionWave ActionWave;

static uint64_t h64(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static SFCell* sffind(SharedField*f,uint64_t k,int create){uint32_t j=(uint32_t)(k^(k>>32))&(SFCAP-1u);for(int n=0;n<SFCAP;n++,j=(j+1u)&(SFCAP-1u)){SFCell*e=&f->c[j];if(e->used){if(e->key==k)return e;continue;}if(!create)return NULL;if(f->n>=SFCAP){fprintf(stderr,"shared field full\n");exit(5);}memset(e,0,sizeof(*e));e->key=k;e->used=1;f->n++;return e;}return NULL;}
static double sfprob(const SFCell*e){return e?(e->yes+1.0)/(e->total+2.0):.5;}
static double sfget(const SharedField*f0,uint64_t k,double def){SharedField*f=(SharedField*)f0;SFCell*e=sffind(f,k,0);return e?sfprob(e):def;}

enum{PT_ACTION=1,PT_ACTION_NEXT=2,PT_REL=3,PT_AXIS=4,PT_PHASE=5,PT_FEAS=6,PT_ROUTE=7,PT_CHANNEL=8,PT_BOUNDARY=9,PT_PROPOSAL=10,PT_DESTSTATE=11,PT_ADDRREL=12,PT_EFFECT=13,PT_GEOMEFFECT=14};
static uint64_t primtok(int kind,int a,int b,int c){return h64(((uint64_t)(kind&255)<<48)|((uint64_t)(a&255)<<32)|((uint64_t)(b&255)<<16)|(uint64_t)(c&255));}
static uint64_t wavecollide(uint64_t a,uint64_t b){return h64(a^(h64(b)+0x9e3779b97f4a7c15ULL));}
static uint64_t w3(uint64_t a,uint64_t b,uint64_t c){return wavecollide(a,wavecollide(b,c));}
static uint64_t ta(int a){return primtok(PT_ACTION,a,0,0);}
static uint64_t tanext(int a){return primtok(PT_ACTION_NEXT,a,0,1);}
static uint64_t trel(int dx,int dy){return primtok(PT_REL,dx+32,dy+32,0);}
static uint64_t tfeas(int c){return primtok(PT_FEAS,c,0,0);}
static uint64_t troute(int o){return primtok(PT_ROUTE,o,0,0);}
static uint64_t tboundary(int dx,int dy){return primtok(PT_BOUNDARY,dx+2,dy+2,0);}
static uint64_t tproposal(void){return primtok(PT_PROPOSAL,0,0,0);}
static uint64_t tdest(int s){return primtok(PT_DESTSTATE,s,0,0);}
static uint64_t taddrrel(int r){return primtok(PT_ADDRREL,r,0,0);}
static uint64_t teffect(int e){return primtok(PT_EFFECT,e,0,0);}
/* v0.44: geometry has no basis/phase vocabulary.  An Action wave collides only
   with ordinary one-hop spatial relation waves.  Pairs of local relations are
   used as anonymous context so chirality can be learned without a global phase
   selector. */
static const int GDX[4]={1,-1,0,0},GDY[4]={0,0,1,-1};
static uint64_t kgauge(int a,int dx,int dy){return wavecollide(ta(a),trel(dx,dy));}
static uint64_t kdir(int a,int rin,int rout){return w3(ta(a),trel(GDX[rin],GDY[rin]),trel(GDX[rout],GDY[rout]));}
static int sf_geom_gauge(const SharedField*f,int a,int*dx,int*dy){
  double sx=0.0,sy=0.0,z=0.0;
  for(int yy=-1;yy<=1;yy++)for(int xx=-1;xx<=1;xx++){
    double w=2.0*sfget(f,kgauge(a,xx,yy),.5)-1.0;if(w<=0.0)continue;
    sx+=w*(double)xx;sy+=w*(double)yy;z+=w;
  }
  if(z<=1e-12)return 0;
  *dx=(int)lround(sx/z);
  *dy=(int)lround(sy/z);
  return 1;
}
/* v0.55: one input one-hop relation maps directly to ordinary output one-hop
   relation waves.  No pair-presence feature or global pair->pair observer. */
static int sf_geom_mapped_vec(const SharedField*f,int a,int rin,double*outx,double*outy){
  double sx=0,sy=0,z=0;
  for(int u=0;u<4;u++){
    double w=2.0*sfget(f,kdir(a,rin,u),.5)-1.0;
    if(w<=0)continue;
    sx+=w*(double)GDX[u];sy+=w*(double)GDY[u];z+=w;
  }
  if(z<=1e-12)return 0;
  sx/=z;sy/=z;double mag=hypot(sx,sy);if(mag<=1e-9)return 0;
  *outx=sx/mag;*outy=sy/mag;return 1;
}
static int sf_geom_dir_code(const SharedField*f,int a){
  int code=0;for(int r=0;r<4;r++){double x,y;if(!sf_geom_mapped_vec(f,a,r,&x,&y))return 255;int d=(fabs(x)>=fabs(y))?(x>=0?0:1):(y>=0?2:3);code|=(d&3)<<(2*r);}return code;
}
/* v0.53: Route consequence is tied to physical effect equivalence, not signed
   action direction.  Mirrored horizontal translations share one consequence
   relation; vertical translations already share one; rotation remains distinct. */
static uint64_t route_effect_wave(const SharedField*f,int a){int gx=9,gy=9;int ok=sf_geom_gauge(f,a,&gx,&gy);int code=sf_geom_dir_code(f,a);if(!ok){gx=gy=9;}if(gx!=9)gx=abs(gx);if(gy!=9)gy=abs(gy);return primtok(PT_GEOMEFFECT,gx+8,gy+8,code);}
static uint64_t kroute(const SharedField*f,int a,int out,int c){return w3(route_effect_wave(f,a),tfeas(c),troute(out));}
static uint64_t klife(int a,int c){return w3(ta(a),tfeas(c),tanext(a));}
static uint64_t ksplit(int out,int c){return wavecollide(tfeas(c),troute(out));}
/* v0.68: Spawn has no Preview/channel namespace.  A visible side-screen bit and
   a board destination are coupled only by their ordinary raw-screen displacement. */
static uint64_t kspawn(int dx,int dy){return trel(dx,dy);}
static uint64_t kclosure(int dx,int dy){return wavecollide(tboundary(dx,dy),trel(dx,dy));}
static uint64_t kcompat(int state){return wavecollide(tproposal(),tdest(state));}
static uint64_t kcresp(int rel,int out){return wavecollide(taddrrel(rel),teffect(out));}
static uint64_t kpairgate(int r1,int r2,int effect){if(r1>r2){int t=r1;r1=r2;r2=t;}return wavecollide(w3(taddrrel(r1),taddrrel(r2),teffect(effect)),teffect(effect));}
static uint64_t kjointeff(int rel){return w3(taddrrel(rel),teffect(2),teffect(1));}
static int addr_vertical_relation(int sy,int cy){return sy==cy?0:(sy<cy?1:2);}

/* Synchronous local relation relaxation.  There is no path, queue, visited set,
   privileged pivot, global basis, or global phase. */
static int sf_geom_targets(const SharedField*f,int act,const uint8_t*a,int tx[],int ty[],int cap){
  int x[64],y[64],n=gp_collect(a,x,y,64);if(n<=0||n>cap)return-1;
  int gdx,gdy;if(!sf_geom_gauge(f,act,&gdx,&gdy))return-1;
  double mdx[4],mdy[4];for(int r=0;r<4;r++)if(!sf_geom_mapped_vec(f,act,r,&mdx[r],&mdy[r]))return-1;
  int idx[N];for(int i=0;i<N;i++)idx[i]=-1;for(int i=0;i<n;i++)idx[y[i]*W+x[i]]=i;
  double ox[64]={0},oy[64]={0},nxv[64],nyv[64];
  for(int pass=0;pass<256;pass++){
    double maxd=0;
    for(int i=0;i<n;i++){
      double sx=0,sy=0,z=0;
      for(int r=0;r<4;r++){
        int xx=x[i]+GDX[r],yy=y[i]+GDY[r];if(xx<0||xx>=W||yy<0||yy>=H)continue;int j=idx[yy*W+xx];if(j<0)continue;
        sx+=ox[j]-mdx[r];sy+=oy[j]-mdy[r];z+=1.0;
      }
      if(z>0){double qx=sx/z,qy=sy/z;nxv[i]=0.5*ox[i]+0.5*qx;nyv[i]=0.5*oy[i]+0.5*qy;}else{nxv[i]=ox[i];nyv[i]=oy[i];}
    }
    double mx=0,my=0;for(int i=0;i<n;i++){mx+=nxv[i];my+=nyv[i];}mx/=n;my/=n;
    for(int i=0;i<n;i++){nxv[i]-=mx;nyv[i]-=my;double d=fabs(nxv[i]-ox[i])+fabs(nyv[i]-oy[i]);if(d>maxd)maxd=d;ox[i]=nxv[i];oy[i]=nyv[i];}
    if(maxd<1e-8)break;
  }
  double mnx=ox[0],mny=oy[0];for(int i=1;i<n;i++){if(ox[i]<mnx)mnx=ox[i];if(oy[i]<mny)mny=oy[i];}
  int ax=W,ay=H;for(int i=0;i<n;i++){if(x[i]<ax)ax=x[i];if(y[i]<ay)ay=y[i];}
  for(int i=0;i<n;i++){tx[i]=ax+gdx+(int)lround(ox[i]-mnx);ty[i]=ay+gdy+(int)lround(oy[i]-mny);}return n;
}
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
static int preview_pixel(const BinaryState*vis,int sx,int sy){return vis->frame.px[sy*RW+(11+sx)]!=0;}
static void sf_spawn_field(const SharedField*f,const BinaryState*vis,float out[N]){
  double miss[N];for(int i=0;i<N;i++)miss[i]=1.0;
  for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(preview_pixel(vis,sx,sy)){
    int screen_x=11+sx;
    for(int dy=-8;dy<=8;dy++)for(int dx=-16;dx<=16;dx++){
      double a=(double)sf_amp(sfget(f,kspawn(dx,dy),.5));if(a<=0.0)continue;
      int ox=screen_x+dx,oy=sy+dy;if(ox>=0&&ox<W&&oy>=0&&oy<H)miss[oy*W+ox]*=1.0-a;
    }
  }
  for(int i=0;i<N;i++)out[i]=(float)(1.0-miss[i]);
}
static float sf_spawn_carrier(const SharedField*f,const BinaryState*vis,const uint8_t world[N]){
  double C=1.0;
  for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(preview_pixel(vis,sx,sy)){
    int screen_x=11+sx;
    for(int dy=-8;dy<=8;dy++)for(int dx=-16;dx<=16;dx++){
      double a=(double)sf_amp(sfget(f,kspawn(dx,dy),.5));if(a<=0.0)continue;
      int ox=screen_x+dx,oy=sy+dy;int state=(ox<0||ox>=W||oy<0||oy>=H)?2:(world[oy*W+ox]?1:0);
      C*=1.0-a*(1.0-(double)sf_compat(f,state));
    }
  }
  return(float)C;
}
static void sf_spawn(const SharedField*f,const BinaryState*vis,const uint8_t*world,uint8_t*a,float g,uint8_t*terminal){float field[N];sf_spawn_field(f,vis,field);float C=sf_spawn_carrier(f,vis,world),gs=sf_split(f,0,C),gg=sf_split(f,1,C),gain=g*gs;*terminal=(uint8_t)(g*gg>.5f);for(int i=0;i<N;i++)if(gain*field[i]>.5f)a[i]=1;}
/* v0.23: no LineClear executor / hole propagation.
   A boundary-closure wave is only a relation token.  Each occupied voxel sees
   the relative vertical address to every closure token in its own column.  The
   shared field says whether that relation means persist / +1-down / disappear.
   Multiple closure waves superpose as repeated copies of the already learned
   +1 spatial effect; no row is selected or ordered. */
static float sf_cresp(const SharedField*f,int rel,int out){return sf_amp(sfget(f,kcresp(rel,out),.5));}
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
static int sf_clear_relation_amp(SharedField*f,uint8_t*b,double carrier){
  if(carrier<0)carrier=0;
  if(carrier>1)carrier=1;
  int dx[16],dy[16],nd=state_unit_dirs(b,dx,dy,16);uint8_t seed[N]={0};int any=0;
  for(int d=0;d<nd;d++){
    double ca=carrier*(double)sf_amp(sfget(f,kclosure(dx[d],dy[d]),.5));
    if(ca<=0.0)continue;
    uint8_t q[N];if(!generic_boundary_wave(b,dx[d],dy[d],q))continue;
    for(int i=0;i<N;i++)seed[i]|=q[i];
    any=1;
  }
  if(!any)return 0;
  uint8_t before[N],out[N]={0};memcpy(before,b,N);
  for(int sy=0;sy<H;sy++)for(int x=0;x<W;x++)if(before[sy*W+x]){
    double survive=1.0,shift=0.0;int rp[3]={0,0,0};
    for(int cy=0;cy<H;cy++)if(seed[cy*W+x]){
      int rel=addr_vertical_relation(sy,cy);rp[rel]=1;
      double joint=carrier*(double)sf_amp(sfget(f,kjointeff(rel),.5));
      double death=carrier*(double)sf_cresp(f,rel,2);if(joint>death)death=joint;
      double birth=carrier*(double)sf_cresp(f,rel,1);if(joint>birth)birth=joint;
      survive*=1.0-death;shift+=birth;
    }
    double birth_gate=1.0;
    for(int r1=0;r1<3;r1++)for(int r2=r1+1;r2<3;r2++)if(rp[r1]&&rp[r2])birth_gate*=sfget(f,kpairgate(r1,r2,1),1.0);
    shift*=birth_gate;
    if(shift>.5){int oy=sy+(int)llround(shift);if(oy>=0&&oy<H)out[oy*W+x]=1;}
    else if(survive>.5)out[sy*W+x]=1;
  }
  memcpy(b,out,N);return !eq(before,b,N);
}
#define RAW_W 15
#define RAW_H 20
#define RAW_N (RAW_W*RAW_H)
static int ridx(int x,int y){return y*RAW_W+x;}
/* v0.67b: no persistent proc/rest state decomposition.  The only model state is
   raw visible occupancy B plus self-born temporal trace T.  Process/persistent
   participation is derived locally from B*T and B*(1-T) only while a relation
   is being evaluated; it is never stored as a second semantic world state. */
static uint8_t bt_occ(const BinaryState*b,int i){int x=i%W,y=i/W;return b->frame.px[ridx(x,y)];}
static uint8_t bt_proc(const BinaryState*b,int i){return (uint8_t)(bt_occ(b,i)&&b->trace[i]);}
static uint8_t bt_rest(const BinaryState*b,int i){return (uint8_t)(bt_occ(b,i)&&!b->trace[i]);}
static void bt_set(BinaryState*b,int i,uint8_t occ,uint8_t trace){int x=i%W,y=i/W;b->frame.px[ridx(x,y)]=(uint8_t)!!occ;b->trace[i]=(uint8_t)(!!occ&&!!trace);}
static void bt_masks(const BinaryState*b,uint8_t src[N],uint8_t world[N]){for(int i=0;i<N;i++){src[i]=bt_proc(b,i);world[i]=bt_rest(b,i);}}

static int sf_clear_state(SharedField*f,BinaryState*b,float carrier){
  uint8_t persistent[N],before[N];for(int i=0;i<N;i++)persistent[i]=bt_rest(b,i);memcpy(before,persistent,N);
  int changed=sf_clear_relation_amp(f,persistent,(double)carrier);if(!changed)return 0;
  for(int i=0;i<N;i++){uint8_t p=bt_proc(b,i);bt_set(b,i,(uint8_t)(p||persistent[i]),p);}return !eq(before,persistent,N);
}
static void sf_spawn_state(SharedField*f,BinaryState*b,float carrier){
  uint8_t persistent[N],process[N];for(int i=0;i<N;i++){persistent[i]=bt_rest(b,i);process[i]=bt_proc(b,i);}
  uint8_t*terminal=&b->frame.px[ridx(14,19)];
  sf_spawn(f,b,persistent,process,carrier,terminal);
  for(int i=0;i<N;i++){uint8_t r=bt_rest(b,i);bt_set(b,i,(uint8_t)(process[i]||r),process[i]);}
}
static void sf_downstream_state(SharedField*f,BinaryState*b,float carrier){
  /* Spawn and Closure read the same pre-microstep B,T state and are committed
     together.  Neither receives a stage/Lock boolean. */
  for(int micro=0;micro<H+8;micro++){
    BinaryState before=*b,spawned=before,cleared=before;
    sf_spawn_state(f,&spawned,carrier);
    (void)sf_clear_state(f,&cleared,carrier);
    for(int i=0;i<N;i++){
      uint8_t p=bt_proc(&spawned,i),r=bt_rest(&cleared,i);
      bt_set(b,i,(uint8_t)(p||r),p);
    }
    b->frame.px[ridx(14,19)]=spawned.frame.px[ridx(14,19)];
    if(!memcmp(&before,b,sizeof(*b)))break;
  }
}
static void sf_binary_step(SharedField*f,BinaryState*b,const ActionWave*in){
  float ac[ACTS];for(int a=0;a<ACTS;a++)ac[a]=in->v[a];
  for(int micro=0;micro<64;micro++){
    float total=0;for(int a=0;a<ACTS;a++)total+=ac[a];if(total<1e-6f)break;
    uint8_t src[N],world[N];bt_masks(b,src,world);double aa[N]={0},wa[N]={0};float next[ACTS]={0},lockamp=0;
    for(int a=0;a<ACTS;a++){
      float w=ac[a];if(w<1e-7f)continue;uint8_t cand[N];float C=sf_geom_candidate(f,a,src,world,cand);
      float gc=sf_route(f,a,0,C),gp=sf_route(f,a,1,C),gw=sf_route(f,a,2,C);
      for(int i=0;i<N;i++){aa[i]+=w*(gc*cand[i]+gp*src[i]);wa[i]+=w*gw*src[i];}
      lockamp+=w*gw;next[a]=w*sf_life(f,a,C);
    }
    for(int i=0;i<N;i++){
      uint8_t np=(uint8_t)(aa[i]>.5),nr=(uint8_t)(world[i]||(wa[i]>.5));
      bt_set(b,i,(uint8_t)(np||nr),np);
    }
    sf_downstream_state(f,b,lockamp);
    for(int a=0;a<ACTS;a++)ac[a]=next[a];
  }
}

struct BPCModel{SharedField f;};
BPCModel* bpc_model_load(const char*path){FILE*in=fopen(path,"rb");if(!in)return NULL;BPCModel*m=(BPCModel*)calloc(1,sizeof(*m));if(!m){fclose(in);return NULL;}if(fread(&m->f,sizeof(m->f),1,in)!=1){fclose(in);free(m);return NULL;}fclose(in);return m;}
void bpc_model_free(BPCModel*m){free(m);}
void bpc_model_step(BPCModel*m,BPCVisibleState*s,const BPCActionWave*a){if(m&&s&&a)sf_binary_step(&m->f,s,a);}
int bpc_model_relation_count(const BPCModel*m){return m?m->f.n:0;}