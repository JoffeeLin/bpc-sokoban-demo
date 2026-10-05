#include <stdio.h>
#include <stdint.h>
#include <string.h>
#define main v17_original_main
#include "BPC_Best_WorldFit_v0.17_reality_spawn_split.c"
#undef main

#define RW 15
#define RH 20
#define RN (RW*RH)
typedef struct { uint8_t px[RN]; } RawFrame;
typedef struct { RawFrame frame; uint8_t trace[N]; } BinaryState;
typedef struct { float v[ACTS]; } ActionWave;
static int ridx(int x,int y){return y*RW+x;}
static void render_raw(const State*s,RawFrame*f){memset(f,0,sizeof(*f));for(int y=0;y<H;y++)for(int x=0;x<W;x++)f->px[ridx(x,y)]=(uint8_t)(s->active[y*W+x]|s->world[y*W+x]);for(int y=0;y<4;y++)for(int x=0;x<4;x++)f->px[ridx(11+x,y)]=s->preview[y*4+x];f->px[ridx(14,19)]=s->gameover;}
static void raw_extract_visible(const RawFrame*f,uint8_t board[N],uint8_t prev[PREV],uint8_t*go){for(int y=0;y<H;y++)for(int x=0;x<W;x++)board[y*W+x]=f->px[ridx(x,y)];for(int y=0;y<4;y++)for(int x=0;x<4;x++)prev[y*4+x]=f->px[ridx(11+x,y)];*go=f->px[ridx(14,19)];}
static void trace_birth_from_temporal_change(const RawFrame*prev,const RawFrame*cur,uint8_t trace[N]){for(int y=0;y<H;y++)for(int x=0;x<W;x++){int k=ridx(x,y),i=y*W+x;trace[i]=(uint8_t)(cur->px[k]&&!prev->px[k]);}}
static void binary_to_internal(const BinaryState*b,State*s){uint8_t board[N];raw_extract_visible(&b->frame,board,s->preview,&s->gameover);for(int i=0;i<N;i++){s->active[i]=(uint8_t)(board[i]&&b->trace[i]);s->world[i]=(uint8_t)(board[i]&&!b->trace[i]);}}
static void internal_to_binary(const State*s,BinaryState*b){render_raw(s,&b->frame);memcpy(b->trace,s->active,N);}
static int raw_eq(const RawFrame*a,const RawFrame*b){return memcmp(a,b,sizeof(*a))==0;}
static ActionWave external_operation_wave(int physical){ActionWave w={{0}};w.v[physical]=1.f;return w;}

/* No action dispatcher. Every operation carrier participates through the same
   geometry -> consequence-route -> lifetime equations. External action encoding
   is only an amplitude vector at the physical boundary. */
static int binary_model_step_wave(const Model*m,BinaryState*b,const ActionWave*in){
  State s;binary_to_internal(b,&s);float ac[ACTS];for(int a=0;a<ACTS;a++)ac[a]=in->v[a];int locked_any=0;
  for(int micro=0;micro<64;micro++){
    float total=0.f;for(int a=0;a<ACTS;a++)total+=ac[a];if(total<1e-6f)break;
    uint8_t src[N];memcpy(src,s.active,N);double active_acc[N]={0},world_add[N]={0};float nextac[ACTS]={0};float lock_amp=0.f;
    for(int a=0;a<ACTS;a++){
      float w=ac[a];if(w<=1e-7f)continue;uint8_t cand[N];float C=geom_candidate(&m->geom,a,src,s.world,cand);
      float gc=route_q(&m->route,a,0,C),gp=route_q(&m->route,a,1,C),gw=route_q(&m->route,a,2,C);
      for(int i=0;i<N;i++){active_acc[i]+=w*(gc*(double)cand[i]+gp*(double)src[i]);world_add[i]+=w*gw*(double)src[i];}
      lock_amp+=w*gw;nextac[a]=w*life_q(&m->life,a,C);
    }
    for(int i=0;i<N;i++){s.active[i]=(uint8_t)(active_acc[i]>.5);if(world_add[i]>.5)s.world[i]=1;}
    if(lock_amp>.5f){locked_any=1;downstream_relax(m,&s,lock_amp);}
    for(int a=0;a<ACTS;a++){ac[a]=nextac[a];}
    if(s.gameover)break;
  }
  internal_to_binary(&s,b);return locked_any;
}

typedef struct{unsigned long long steps,exact,locks;int episodes_ok,first_ep,first_t;}AWStat;
static AWStat wave_rollout(const Model*m,int episodes,int maxsteps,uint64_t seed,int shift_wave){RNG r={seed};AWStat st={0};st.first_ep=st.first_t=-1;for(int ep=0;ep<episodes;ep++){State real;init_episode(&r,&real);RawFrame blank={{0}},cur;render_raw(&real,&cur);BinaryState mod;mod.frame=cur;trace_birth_from_temporal_change(&blank,&cur,mod.trace);int epok=1;for(int t=0;t<maxsteps;t++){int u=ri(&r,100),act=u<18?ACT_LEFT:u<36?ACT_RIGHT:u<50?ACT_ROT:u<70?ACT_DOWN:ACT_DROP;int lr=real_step(&real,act);RawFrame truth;render_raw(&real,&truth);int carrier=shift_wave?(act+1)%ACTS:act;ActionWave aw=external_operation_wave(carrier);int lm=binary_model_step_wave(m,&mod,&aw);int ok=(lr==lm)&&raw_eq(&truth,&mod.frame);st.steps++;st.exact+=ok;if(lr)st.locks++;if(!ok){epok=0;if(st.first_ep<0){st.first_ep=ep;st.first_t=t;}break;}if(lr){if(real.gameover)break;uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(real.preview,np,PREV);render_raw(&real,&truth);mod.frame=truth;}}st.episodes_ok+=epok;}return st;}
static void paw(const char*n,const AWStat*s){printf("%s %llu/%llu=%.6f%% episodes_ok=%d locks=%llu first_fail=%d:%d\n",n,s->exact,s->steps,s->steps?100.0*(double)s->exact/s->steps:0.0,s->episodes_ok,s->locks,s->first_ep,s->first_t);}
int main(void){Model m;model_init(&m);train_raw_routes(&m,60000);train_action_life(&m,40000);puts("BPC Binary WorldFit v0.19 | 0/1 screen + self-born temporal trace + anonymous action wave; no action dispatcher");unsigned long long ok=0,n=0;for(int s=0;s<8;s++){AWStat x=wave_rollout(&m,1000,120,98765ULL+200003ULL*(uint64_t)s,0);paw("NORMAL",&x);ok+=x.exact;n+=x.steps;}printf("NORMAL_TOTAL %llu/%llu=%.6f%%\n",ok,n,100.0*(double)ok/n);AWStat sh=wave_rollout(&m,200,120,880001ULL,1);paw("ACTION_WAVE_SHIFT",&sh);return 0;}