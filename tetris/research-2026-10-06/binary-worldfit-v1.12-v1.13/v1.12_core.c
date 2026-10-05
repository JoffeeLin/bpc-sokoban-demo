#include "BPC_Binary_WorldFit_v1.12_API.h"
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#define ACTS BPC_ACTIONS
#define RW 15
#define RH 20
#define RN (RW*RH)
#define SFCAP 2048

typedef struct{uint64_t key;double yes,total;uint8_t used;}SFCell;
typedef struct{SFCell c[SFCAP];int n;}SharedField;
typedef struct{BPCFrame frame;uint8_t trace[RN];} BinaryState;
typedef BPCActionWave ActionWave;

static uint64_t h64(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static SFCell* sffind(SharedField*f,uint64_t k,int create){uint32_t j=(uint32_t)(k^(k>>32))&(SFCAP-1u);for(int n=0;n<SFCAP;n++,j=(j+1u)&(SFCAP-1u)){SFCell*e=&f->c[j];if(e->used){if(e->key==k)return e;continue;}if(!create)return NULL;if(f->n>=SFCAP){fprintf(stderr,"shared field full\n");exit(5);}memset(e,0,sizeof(*e));e->key=k;e->used=1;f->n++;return e;}return NULL;}
static double sfprob(const SFCell*e){return e?(e->yes+1.0)/(e->total+2.0):.5;}
static double sfget(const SharedField*f0,uint64_t k,double def){SharedField*f=(SharedField*)f0;SFCell*e=sffind(f,k,0);return e?sfprob(e):def;}
/* Structural support is not a predictive probability: unobserved relation=0,
   observed positive-only topology uses its direct evidence frequency. */
static double sfsupport(const SharedField*f0,uint64_t k){SharedField*f=(SharedField*)f0;SFCell*e=sffind(f,k,0);return(e&&e->total>0.0)?e->yes/e->total:0.0;}


/* v0.71: dead historical primitive vocabulary removed.  Numeric identities of
   surviving physical token types remain frozen, so no field migration is needed. */
enum{PT_REL=3,PT_BIT=21};
static uint64_t primtok(int kind,int a,int b,int c){return h64(((uint64_t)(kind&255)<<48)|((uint64_t)(a&255)<<32)|((uint64_t)(b&255)<<16)|(uint64_t)(c&255));}
static uint64_t wavecollide(uint64_t a,uint64_t b){return h64(a^(h64(b)+0x9e3779b97f4a7c15ULL));}
static uint64_t w3(uint64_t a,uint64_t b,uint64_t c){return wavecollide(a,wavecollide(b,c));}
static uint64_t trel(int dx,int dy){return primtok(PT_REL,dx+32,dy+32,0);}
/* v0.80: B/T/outside are not different token types.  They are the same BIT
   wave placed at three ordinary relation slots in the local input structure. */
static uint64_t tbit(int b){return primtok(PT_BIT,b,0,0);}
/* v0.81: Operation has no token type.  Each external action is the same BIT=1
   wave presented at a different physical action-port relation coordinate. */
static uint64_t ta(int a){return wavecollide(trel(64+a,0),tbit(1));}
static uint64_t slotbit(int slot,int b){return wavecollide(trel(0,slot),tbit(b));}
static uint64_t cellwave(int B,int T,int outside){return w3(slotbit(0,B),slotbit(1,T),slotbit(2,outside));}
static uint64_t w_empty(void){return cellwave(0,0,0);}
static uint64_t w_persist(void){return cellwave(1,0,0);}
static uint64_t w_process(void){return cellwave(1,1,0);}
/* v0.82: the core has no distinguished terminal coordinate.  Any visible
   screen B=1 consequence is addressed by the same relation x BIT wave. */
static uint64_t screen_bit_wave(int x,int y){return wavecollide(trel(x,y),slotbit(0,1));}
static float sf_amp(double q);
/* v0.93: no hard-coded Spawn source region. Action-coupled screen scope is a
   learned relation from ordinary visible Screen+Action transitions. */
static uint64_t kscope(int a,int x,int y){return w3(ta(a),screen_bit_wave(x,y),tbit(1));}
/* v0.98: learned action scope remains a continuous field amplitude.  There is no
   cached boolean mask or winner threshold; amplitudes are gauge-normalized so
   only true zero-support addresses are absent. */
typedef struct{const SharedField*f;double amp[RN];}ScopeCache;static ScopeCache g_scope_cache;
static void scope_cache_ready(const SharedField*f){if(g_scope_cache.f==f)return;memset(&g_scope_cache,0,sizeof(g_scope_cache));g_scope_cache.f=f;for(int y=0;y<RH;y++)for(int x=0;x<RW;x++){double miss=1.0;for(int a=0;a<ACTS;a++){double q=sfsupport(f,kscope(a,x,y));if(q<0)q=0;if(q>1)q=1;miss*=1.0-q;}g_scope_cache.amp[y*RW+x]=1.0-miss;}}
static double sf_scope_amp(const SharedField*f,int x,int y){if(x<0||x>=RW||y<0||y>=RH)return 0.0;scope_cache_ready(f);return g_scope_cache.amp[y*RW+x];}

/* v0.44: geometry has no basis/phase vocabulary.  An Action wave collides only
   with ordinary one-hop spatial relation waves.  Pairs of local relations are
   used as anonymous context so chirality can be learned without a global phase
   selector. */
static uint64_t kgauge(int a,int dx,int dy){return wavecollide(ta(a),trel(dx,dy));}
/* v0.83: no four named/cardinal relation slots.  A geometry map is addressed
   directly by input and output local relation vectors. */
static uint64_t kdirv(int a,int idx,int idy,int odx,int ody){return w3(ta(a),trel(idx,idy),trel(odx,ody));}
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
static int sf_geom_mapped_vec(const SharedField*f,int a,int idx,int idy,double*outx,double*outy){
  double sx=0,sy=0,z=0;
  for(int ody=-1;ody<=1;ody++)for(int odx=-1;odx<=1;odx++){
    if(odx==0&&ody==0)continue;
    double w=2.0*sfget(f,kdirv(a,idx,idy,odx,ody),.5)-1.0;if(w<=0)continue;
    sx+=w*(double)odx;sy+=w*(double)ody;z+=w;
  }
  if(z<=1e-12)return 0;
  sx/=z;sy/=z;double mag=hypot(sx,sy);if(mag<=1e-9)return 0;
  *outx=sx/mag;*outy=sy/mag;return 1;
}
/* v0.88: no consequence index.  A consequence is addressed only by the actual
   physical output wave that participates in the field. */
static uint64_t kconsequence(int a,uint64_t branch,uint64_t effect){return w3(ta(a),branch,effect);}
static uint64_t klife_wave(int a,uint64_t branch){return wavecollide(ta(a),branch);}
static uint64_t kdirect_wave(uint64_t branch){return wavecollide(branch,w_process());}
static uint64_t kscreenemit_wave(uint64_t branch,int x,int y){return wavecollide(branch,screen_bit_wave(x,y));}
/* v0.68: Spawn has no Preview/channel namespace.  A visible side-screen bit and
   a board destination are coupled only by their ordinary raw-screen displacement. */
/* v0.85: Spawn source identity is not a loop region.  Every screen bit may
   participate; source inside/outside is just the same outside BIT slot. */
/* v0.85b: ordered collision topology distinguishes roles without a label.
   Spawn is relation -> source-outside; Closure remains outside -> relation. */
static uint64_t kspawn(int outside,int dx,int dy){return wavecollide(trel(dx,dy),slotbit(2,outside));}
/* v0.78: no Boundary token. A closure candidate is an ordinary spatial relation
   whose continuation meets the physical outside bit. */
static uint64_t kclosure(int dx,int dy){return wavecollide(slotbit(2,1),trel(dx,dy));}
/* v0.87: no empty/occupied/boundary state enumeration. Compatibility is
   addressed directly by the raw local B,T,outside bits. */
static uint64_t kcompat_bits(int B,int T,int outside){return wavecollide(w_process(),cellwave(B,T,outside));}
/* v0.70: Closure consequence uses the same ordinary spatial-relation token as
   every other geometry relation.  There is no PT_ADDRREL / same-below-above
   namespace.  dy is simply the sign of closure address relative to source. */
/* v0.73: no PT_EFFECT / death-birth vocabulary.  Closure consequences are
   ordinary visible-state transitions: source -> empty, or +1 address -> B=1,T=0. */
static uint64_t closure_birth_wave(void){return wavecollide(trel(0,1),w_persist());}
static uint64_t closure_death_wave(void){return wavecollide(trel(0,0),w_empty());}
static uint64_t kcresp_relation(uint64_t relation,uint64_t effect){return wavecollide(relation,effect);}
static uint64_t kpairgate_relation(uint64_t a,uint64_t b){uint64_t e=closure_birth_wave();if(a>b){uint64_t t=a;a=b;b=t;}return wavecollide(w3(a,b,e),e);}
static uint64_t kjointeff_relation(uint64_t relation){return w3(relation,closure_death_wave(),closure_birth_wave());}

/* Synchronous local relation relaxation.  There is no path, queue, visited set,
   privileged pivot, global basis, or global phase. */
static int gp_collect_screen(const uint8_t*a,int x[],int y[],int cap){int n=0;for(int yy=0;yy<RH;yy++)for(int xx=0;xx<RW;xx++)if(a[yy*RW+xx]){if(n<cap){x[n]=xx;y[n]=yy;}n++;}return n;}
/* v0.95: Action geometry lives on the full visible screen lattice. The learned
   action-scope wave, not a 10x20 array type, decides which addresses participate. */
static int sf_geom_targets_screen(const SharedField*f,int act,const uint8_t*a,int tx[],int ty[],int cap){
  int x[64],y[64],n=gp_collect_screen(a,x,y,64);if(n<=0||n>cap)return-1;
  int gdx,gdy;if(!sf_geom_gauge(f,act,&gdx,&gdy))return-1;
  int idx[RN];for(int i=0;i<RN;i++)idx[i]=-1;for(int i=0;i<n;i++)idx[y[i]*RW+x[i]]=i;
  double mapx[3][3]={{0}},mapy[3][3]={{0}};uint8_t mapok[3][3]={{0}};
  for(int rdy=-1;rdy<=1;rdy++)for(int rdx=-1;rdx<=1;rdx++)if(rdx||rdy)mapok[rdy+1][rdx+1]=(uint8_t)sf_geom_mapped_vec(f,act,rdx,rdy,&mapx[rdy+1][rdx+1],&mapy[rdy+1][rdx+1]);
  double ox[64]={0},oy[64]={0},nxv[64],nyv[64];
  for(int pass=0;pass<256;pass++){
    double maxd=0;
    for(int i=0;i<n;i++){
      double sx=0,sy=0,z=0;
      for(int rdy=-1;rdy<=1;rdy++)for(int rdx=-1;rdx<=1;rdx++){
        if(rdx==0&&rdy==0)continue;
        int xx=x[i]+rdx,yy=y[i]+rdy;
        if(xx<0||xx>=RW||yy<0||yy>=RH)continue;
        int j=idx[yy*RW+xx];
        if(j<0||!mapok[rdy+1][rdx+1])continue;
        sx+=ox[j]-mapx[rdy+1][rdx+1];sy+=oy[j]-mapy[rdy+1][rdx+1];z+=1.0;
      }
      if(z>0){double qx=sx/z,qy=sy/z;nxv[i]=0.5*ox[i]+0.5*qx;nyv[i]=0.5*oy[i]+0.5*qy;}else{nxv[i]=ox[i];nyv[i]=oy[i];}
    }
    double mx=0,my=0;for(int i=0;i<n;i++){mx+=nxv[i];my+=nyv[i];}mx/=n;my/=n;
    for(int i=0;i<n;i++){nxv[i]-=mx;nyv[i]-=my;double d=fabs(nxv[i]-ox[i])+fabs(nyv[i]-oy[i]);if(d>maxd)maxd=d;ox[i]=nxv[i];oy[i]=nyv[i];}if(maxd<1e-8)break;
  }
  double mnx=ox[0],mny=oy[0];for(int i=1;i<n;i++){if(ox[i]<mnx)mnx=ox[i];if(oy[i]<mny)mny=oy[i];}
  int ax=RW,ay=RH;for(int i=0;i<n;i++){if(x[i]<ax)ax=x[i];if(y[i]<ay)ay=y[i];}
  for(int i=0;i<n;i++){tx[i]=ax+gdx+(int)lround(ox[i]-mnx);ty[i]=ay+gdy+(int)lround(oy[i]-mny);}return n;
}
static float sf_amp(double q){double a=2.0*q-1.0;if(a<0)a=0;if(a>1)a=1;return(float)a;}
static float sf_compat_scope(const SharedField*f,int B,int T,double scope){if(scope<0)scope=0;if(scope>1)scope=1;double inside=sf_amp(sfget(f,kcompat_bits(B,T,0),.5));double outside=sf_amp(sfget(f,kcompat_bits(0,0,1),.5));return(float)(scope*inside+(1.0-scope)*outside);}
static float sf_geom_candidate_screen(const SharedField*f,int act,const uint8_t*a,const uint8_t*w,uint8_t*out){
  memset(out,0,RN);int tx[64],ty[64],n=sf_geom_targets_screen(f,act,a,tx,ty,64);if(n<0)return 0.f;float C=1.f;
  for(int i=0;i<n;i++){double scope=sf_scope_amp(f,tx[i],ty[i]);int B=0,T=0;if(scope>0.0){int k=ty[i]*RW+tx[i];B=w[k]?1:0;out[k]=1;}C*=sf_compat_scope(f,B,T,scope);}return C;
}
static float lerp01(double q0,double q1,float C){double q=q1*C+q0*(1.0-C);if(q<0)q=0;if(q>1)q=1;return(float)q;}
static float sf_consequence(const SharedField*f,int a,uint64_t effect,float C){return lerp01(sfget(f,kconsequence(a,w_empty(),effect),.5),sfget(f,kconsequence(a,w_process(),effect),.5),C);}static float sf_life(const SharedField*f,int a,float C){return sf_amp(lerp01(sfget(f,klife_wave(a,w_empty()),.5),sfget(f,klife_wave(a,w_process()),.5),C));}
static float sf_direct(const SharedField*f,float C){return lerp01(sfget(f,kdirect_wave(w_empty()),.5),sfget(f,kdirect_wave(w_process()),.5),C);}
static float sf_screen_emit(const SharedField*f,float C,int x,int y){return lerp01(sfget(f,kscreenemit_wave(w_empty(),x,y),.5),sfget(f,kscreenemit_wave(w_process(),x,y),.5),C);}
typedef struct{const SharedField*f;int rdx[256],rdy[256],rn;double ain[256],aout[256];}SpawnRelCache;
static SpawnRelCache g_spawn_cache;
static void spawn_rel_cache_ready(const SharedField*f){if(g_spawn_cache.f==f)return;memset(&g_spawn_cache,0,sizeof(g_spawn_cache));g_spawn_cache.f=f;for(int dy=-RH;dy<=RH;dy++)for(int dx=-RW;dx<=RW;dx++){double ai=(double)sf_amp(sfget(f,kspawn(0,dx,dy),.5)),ao=(double)sf_amp(sfget(f,kspawn(1,dx,dy),.5));if((ai>0.0||ao>0.0)&&g_spawn_cache.rn<256){int n=g_spawn_cache.rn++;g_spawn_cache.rdx[n]=dx;g_spawn_cache.rdy[n]=dy;g_spawn_cache.ain[n]=ai;g_spawn_cache.aout[n]=ao;}}}
static uint8_t screen_proc(const BinaryState*b,int k){return (uint8_t)(b->frame.px[k]&&b->trace[k]);}
static uint8_t screen_rest(const BinaryState*b,int k){return (uint8_t)(b->frame.px[k]&&!b->trace[k]);}
static void screen_set(BinaryState*b,int k,uint8_t occ,uint8_t trace){b->frame.px[k]=(uint8_t)!!occ;b->trace[k]=(uint8_t)(!!occ&&!!trace);}
static void sf_spawn_field_screen(const SharedField*f,const BinaryState*vis,float out[RN]){
  double miss[RN];for(int i=0;i<RN;i++)miss[i]=1.0;spawn_rel_cache_ready(f);
  for(int sy=0;sy<RH;sy++)for(int sx=0;sx<RW;sx++)if(vis->frame.px[sy*RW+sx]){
    double scope=sf_scope_amp(f,sx,sy);for(int r=0;r<g_spawn_cache.rn;r++){double rel=scope*g_spawn_cache.ain[r]+(1.0-scope)*g_spawn_cache.aout[r];if(rel<=0.0)continue;int ox=sx+g_spawn_cache.rdx[r],oy=sy+g_spawn_cache.rdy[r];if(ox>=0&&ox<RW&&oy>=0&&oy<RH)miss[oy*RW+ox]*=1.0-rel;}
  }
  for(int i=0;i<RN;i++)out[i]=(float)(1.0-miss[i]);
}
static float sf_spawn_carrier_screen(const SharedField*f,const BinaryState*vis,const uint8_t world[RN]){
  double C=1.0;spawn_rel_cache_ready(f);
  for(int sy=0;sy<RH;sy++)for(int sx=0;sx<RW;sx++)if(vis->frame.px[sy*RW+sx]){
    double scope=sf_scope_amp(f,sx,sy);for(int r=0;r<g_spawn_cache.rn;r++){double rel=scope*g_spawn_cache.ain[r]+(1.0-scope)*g_spawn_cache.aout[r];if(rel<=0.0)continue;int ox=sx+g_spawn_cache.rdx[r],oy=sy+g_spawn_cache.rdy[r];double dst_scope=sf_scope_amp(f,ox,oy);int B=(dst_scope>0.0)?(world[oy*RW+ox]?1:0):0,T=0;C*=1.0-rel*(1.0-(double)sf_compat_scope(f,B,T,dst_scope));}
  }
  return(float)C;
}
static void sf_spawn_screen(SharedField*f,BinaryState*vis,const uint8_t world[RN],uint8_t process[RN],float g){
  float field[RN];sf_spawn_field_screen(f,vis,field);float C=sf_spawn_carrier_screen(f,vis,world),gain=g*sf_direct(f,C);
  for(int k=0;k<RN;k++)if(gain*field[k]>.5f)process[k]=1;
  for(int y=0;y<RH;y++)for(int x=0;x<RW;x++)if(g*sf_screen_emit(f,C,x,y)>.5f)vis->frame.px[y*RW+x]=1;
}
static float sf_cresp_relation(const SharedField*f,uint64_t relation,uint64_t effect){return sf_amp(sfget(f,kcresp_relation(relation,effect),.5));}
static void boundary_reach_one_side_screen(const SharedField*f,const uint8_t*b,int dx,int dy,uint8_t wave[RN]){
  memset(wave,0,RN);
  for(int y=0;y<RH;y++)for(int x=0;x<RW;x++){int k=y*RW+x;if(sf_scope_amp(f,x,y)<=0.0||!b[k])continue;int px=x-dx,py=y-dy;if(sf_scope_amp(f,px,py)<=0.0)wave[k]=1;}
  for(int step=0;step<RN;step++){uint8_t next[RN];memcpy(next,wave,RN);int changed=0;for(int y=0;y<RH;y++)for(int x=0;x<RW;x++){int k=y*RW+x;if(!wave[k])continue;int nx=x+dx,ny=y+dy;if(sf_scope_amp(f,nx,ny)>0.0){int nk=ny*RW+nx;if(b[nk]&&!next[nk]){next[nk]=1;changed=1;}}}memcpy(wave,next,RN);if(!changed)break;}
}
static int generic_boundary_wave_screen(const SharedField*f,const uint8_t*b,int dx,int dy,uint8_t reached[RN]){uint8_t a[RN],z[RN];boundary_reach_one_side_screen(f,b,dx,dy,a);boundary_reach_one_side_screen(f,b,-dx,-dy,z);int any=0;for(int i=0;i<RN;i++){reached[i]=(uint8_t)(a[i]&&z[i]);any|=reached[i];}return any;}
static int sf_clear_relation_amp_screen(SharedField*f,uint8_t*b,double carrier){
  if(carrier<0)carrier=0;
  if(carrier>1)carrier=1;
  double seed[RN]={0};int any=0;
  for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){if(dx==0&&dy==0)continue;double ca=carrier*(double)sf_amp(sfget(f,kclosure(dx,dy),.5));if(ca<=0.0)continue;uint8_t q[RN];if(!generic_boundary_wave_screen(f,b,dx,dy,q))continue;for(int i=0;i<RN;i++)if(q[i])seed[i]=1.0-(1.0-seed[i])*(1.0-ca);any=1;}
  if(!any)return 0;
  uint8_t before[RN],out[RN]={0};memcpy(before,b,RN);
  for(int sy=0;sy<RH;sy++)for(int x=0;x<RW;x++){int sk=sy*RW+x;if(sf_scope_amp(f,x,sy)<=0.0||!before[sk])continue;double survive=1.0,shift=0.0;uint64_t rels[3]={0};double relamp[3]={0};int nrel=0;
    if(seed[sk]>0.0){double sa=seed[sk];uint64_t relation=trel(0,0);rels[nrel]=relation;relamp[nrel]=sa;nrel++;double joint=carrier*sa*(double)sf_amp(sfget(f,kjointeff_relation(relation),.5));double death=carrier*sa*(double)sf_cresp_relation(f,relation,closure_death_wave());if(joint>death)death=joint;double birth=carrier*sa*(double)sf_cresp_relation(f,relation,closure_birth_wave());if(joint>birth)birth=joint;survive*=1.0-death;shift+=birth;}
    for(int dir=-1;dir<=1;dir+=2){uint64_t relation=trel(0,dir);int seen=0;for(int q=0;q<nrel;q++)seen|=(rels[q]==relation);for(int cy=sy+dir;cy>=0&&cy<RH&&sf_scope_amp(f,x,cy)>0.0;cy+=dir){int ck=cy*RW+x;if(seed[ck]<=0.0)continue;double sa=seed[ck];if(!seen&&nrel<3){rels[nrel]=relation;relamp[nrel]=sa;nrel++;seen=1;}else if(seen){for(int q=0;q<nrel;q++)if(rels[q]==relation)relamp[q]=1.0-(1.0-relamp[q])*(1.0-sa);}double joint=carrier*sa*(double)sf_amp(sfget(f,kjointeff_relation(relation),.5));double death=carrier*sa*(double)sf_cresp_relation(f,relation,closure_death_wave());if(joint>death)death=joint;double birth=carrier*sa*(double)sf_cresp_relation(f,relation,closure_birth_wave());if(joint>birth)birth=joint;survive*=1.0-death;shift+=birth;}}
    double birth_gate=1.0;for(int i1=0;i1<nrel;i1++)for(int i2=i1+1;i2<nrel;i2++){double ps=relamp[i1]*relamp[i2];double g=sfget(f,kpairgate_relation(rels[i1],rels[i2]),1.0);birth_gate*=1.0-ps*(1.0-g);}shift*=birth_gate;
    if(survive>.5)out[sk]=1;
    if(shift>.5){int oy=sy+(int)llround(shift);if(sf_scope_amp(f,x,oy)>0.0)out[oy*RW+x]=1;}
  }
  memcpy(b,out,RN);return memcmp(before,b,RN)!=0;
}
static void sf_downstream_state(SharedField*f,BinaryState*b,float carrier){
  for(;;){
    BinaryState before=*b,emitted=before;
    uint8_t persistent[RN]={0},process[RN]={0};
    for(int k=0;k<RN;k++)if(sf_scope_amp(f,k%RW,k/RW)>0.0){persistent[k]=screen_rest(&before,k);process[k]=screen_proc(&before,k);}
    sf_spawn_screen(f,&emitted,persistent,process,carrier);
    (void)sf_clear_relation_amp_screen(f,persistent,(double)carrier);
    for(int k=0;k<RN;k++){
      if(sf_scope_amp(f,k%RW,k/RW)>0.0)screen_set(b,k,(uint8_t)(process[k]||persistent[k]),process[k]);
      else{b->frame.px[k]=emitted.frame.px[k];b->trace[k]=emitted.trace[k];}
    }
    if(!memcmp(&before,b,sizeof(*b)))break;
  }
}
static void sf_binary_step(SharedField*f,BinaryState*b,const ActionWave*in){
  float ac[ACTS];for(int a=0;a<ACTS;a++)ac[a]=in->v[a];scope_cache_ready(f);
  for(;;){
    float total=0;for(int a=0;a<ACTS;a++)total+=ac[a];if(total<1e-6f)break;
    uint8_t src[RN]={0},world[RN]={0};for(int y=0;y<RH;y++)for(int x=0;x<RW;x++){int k=y*RW+x;if(g_scope_cache.amp[k]<=0.0)continue;uint8_t B=b->frame.px[k];src[k]=(uint8_t)(B&&b->trace[k]);world[k]=(uint8_t)(B&&!b->trace[k]);}
    double aa[RN]={0},wa[RN]={0};float next[ACTS]={0},lockamp=0;
    for(int a=0;a<ACTS;a++){
      float w=ac[a];if(w<1e-7f)continue;uint8_t cand[RN];float C=sf_geom_candidate_screen(f,a,src,world,cand);
      uint64_t target_effect=w_process(),source_effect=wavecollide(trel(0,0),w_process()),persistent_effect=wavecollide(trel(0,0),w_persist());
      float gc=sf_consequence(f,a,target_effect,C),gp=sf_consequence(f,a,source_effect,C),gw=sf_consequence(f,a,persistent_effect,C);
      for(int k=0;k<RN;k++)if(g_scope_cache.amp[k]>0.0){aa[k]+=w*(gc*cand[k]+gp*src[k]);wa[k]+=w*gw*src[k];}
      lockamp+=w*gw;next[a]=w*sf_life(f,a,C);
    }
    for(int k=0;k<RN;k++)if(g_scope_cache.amp[k]>0.0){uint8_t np=(uint8_t)(aa[k]>.5),nr=(uint8_t)(world[k]||(wa[k]>.5));b->frame.px[k]=(uint8_t)(np||nr);b->trace[k]=(uint8_t)(np&&(np||nr));}
    sf_downstream_state(f,b,lockamp);for(int a=0;a<ACTS;a++)ac[a]=next[a];
  }
}

struct BPCModel{SharedField f;uint8_t trace[RN];BPCFrame last_visible;};
BPCModel* bpc_model_load(const char*path){FILE*in=fopen(path,"rb");if(!in)return NULL;BPCModel*m=(BPCModel*)calloc(1,sizeof(*m));if(!m){fclose(in);return NULL;}if(fread(&m->f,sizeof(m->f),1,in)!=1){fclose(in);free(m);return NULL;}fclose(in);return m;}
void bpc_model_free(BPCModel*m){free(m);}
void bpc_model_reset(BPCModel*m,const BPCFrame*visible){if(!m||!visible)return;for(int k=0;k<RN;k++)m->trace[k]=visible->px[k]?1u:0u;m->last_visible=*visible;}
void bpc_model_step(BPCModel*m,BPCFrame*visible,const BPCActionWave*a){
  if(!m||!visible||!a)return;
  for(int k=0;k<RN;k++)if(visible->px[k]!=m->last_visible.px[k])m->trace[k]=visible->px[k]?1u:0u;
  BinaryState s;memset(&s,0,sizeof(s));s.frame=*visible;memcpy(s.trace,m->trace,RN);
  sf_binary_step(&m->f,&s,a);*visible=s.frame;memcpy(m->trace,s.trace,RN);m->last_visible=*visible;
}
int bpc_model_relation_count(const BPCModel*m){return m?m->f.n:0;}