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

static int ridx(int x,int y){ return y*RW+x; }
static void render_raw(const State*s, RawFrame*f){
  memset(f,0,sizeof(*f));
  for(int y=0;y<H;y++)for(int x=0;x<W;x++) f->px[ridx(x,y)] = (uint8_t)(s->active[y*W+x] | s->world[y*W+x]);
  /* Preview is physically visible at a fixed side-screen location, but remains only 0/1 pixels. */
  for(int y=0;y<4;y++)for(int x=0;x<4;x++) f->px[ridx(11+x,y)] = s->preview[y*4+x];
  f->px[ridx(14,19)] = s->gameover;
}
static void raw_extract_visible(const RawFrame*f,uint8_t board[N],uint8_t prev[PREV],uint8_t*go){
  for(int y=0;y<H;y++)for(int x=0;x<W;x++) board[y*W+x]=f->px[ridx(x,y)];
  for(int y=0;y<4;y++)for(int x=0;x<4;x++) prev[y*4+x]=f->px[ridx(11+x,y)];
  *go=f->px[ridx(14,19)];
}
static void trace_birth_from_temporal_change(const RawFrame*prev,const RawFrame*cur,uint8_t trace[N]){
  /* No Active/World label: a newly appeared board bit is just an anonymous temporal trace seed. */
  for(int y=0;y<H;y++)for(int x=0;x<W;x++){
    int k=ridx(x,y),i=y*W+x;
    trace[i]=(uint8_t)(cur->px[k] && !prev->px[k]);
  }
}
static void binary_to_internal(const BinaryState*b,State*s){
  uint8_t board[N]; raw_extract_visible(&b->frame,board,s->preview,&s->gameover);
  for(int i=0;i<N;i++){
    /* anonymous process trace vs persistent visible bit; semantic names are not externally supplied */
    s->active[i]=(uint8_t)(board[i] && b->trace[i]);
    s->world[i]=(uint8_t)(board[i] && !b->trace[i]);
  }
}
static void internal_to_binary(const State*s,BinaryState*b){
  render_raw(s,&b->frame);
  memcpy(b->trace,s->active,N);
}
static int raw_eq(const RawFrame*a,const RawFrame*b){return memcmp(a,b,sizeof(*a))==0;}

typedef enum {BIN_NORMAL=0,BIN_TRACE_OFF=1,BIN_TRACE_SHIFT=2} BinMode;
typedef struct { unsigned long long steps,exact,locks,byact[ACTS],okact[ACTS]; int episodes_ok,first_ep,first_t,first_act; } BStat;

static void shift_trace(uint8_t t[N]){
  uint8_t q[N]={0};
  for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(t[y*W+x] && x+1<W)q[y*W+x+1]=1;
  memcpy(t,q,N);
}
static int binary_model_step(const Model*m,BinaryState*b,int act,BinMode mode){
  State s;
  BinaryState w=*b;
  if(mode==BIN_TRACE_OFF)memset(w.trace,0,N);
  else if(mode==BIN_TRACE_SHIFT)shift_trace(w.trace);
  binary_to_internal(&w,&s);
  int lock=model_step(m,&s,act);
  internal_to_binary(&s,b);
  return lock;
}
static BStat raw_rollout(const Model*m,int episodes,int maxsteps,uint64_t seed,BinMode mode){
  RNG r={seed};BStat st={0};st.first_ep=st.first_t=st.first_act=-1;
  for(int ep=0;ep<episodes;ep++){
    State real;init_episode(&r,&real);
    RawFrame blank={{0}},cur;render_raw(&real,&cur);
    BinaryState mod;mod.frame=cur;trace_birth_from_temporal_change(&blank,&cur,mod.trace);
    int epok=1;
    for(int t=0;t<maxsteps;t++){
      int u=ri(&r,100),act=u<18?ACT_LEFT:u<36?ACT_RIGHT:u<50?ACT_ROT:u<70?ACT_DOWN:ACT_DROP;
      int lr=real_step(&real,act);RawFrame truth;render_raw(&real,&truth);
      int lm=binary_model_step(m,&mod,act,mode);(void)lm;
      int ok=(lr==lm)&&raw_eq(&truth,&mod.frame);
      st.steps++;st.exact+=ok;st.byact[act]++;st.okact[act]+=ok;if(lr)st.locks++;
      if(!ok){epok=0;if(st.first_ep<0){st.first_ep=ep;st.first_t=t;st.first_act=act;}break;}
      if(lr){if(real.gameover)break;uint8_t np[PREV];preview_shape(ri(&r,7),np);memcpy(real.preview,np,PREV);
        /* the new preview is an external visible reality update, applied to the same raw screen */
        render_raw(&real,&truth);mod.frame=truth;
      }
    }
    st.episodes_ok+=epok;
  }
  return st;
}
static void print_bs(const char*name,const BStat*s){
  printf("%s steps=%llu exact=%llu/%llu=%.6f%% episodes_ok=%d locks=%llu first_fail=%d:%d act=%d\n",name,s->steps,s->exact,s->steps,s->steps?100.0*(double)s->exact/(double)s->steps:0.0,s->episodes_ok,s->locks,s->first_ep,s->first_t,s->first_act);
  const char*nm[ACTS]={"L","R","D","Rot","Drop"};
  for(int a=0;a<ACTS;a++){printf(" %s=%llu/%llu",nm[a],s->okact[a],s->byact[a]);}
  putchar('\n');
}

/* Constructive information-closure counterexample: same black/white board + same action, different hidden mobile subset -> different next black/white board. */
static void alias_audit(void){
  State a={0},b={0};
  /* identical merged occupancy: two adjacent horizontal 4-runs. In A upper run is mobile; in B lower run is mobile. */
  for(int x=2;x<6;x++){a.active[5*W+x]=1;a.world[10*W+x]=1;b.world[5*W+x]=1;b.active[10*W+x]=1;}
  a.preview[5]=b.preview[5]=1;
  RawFrame ra,rb;render_raw(&a,&ra);render_raw(&b,&rb);
  State an=a,bn=b;real_step(&an,ACT_LEFT);real_step(&bn,ACT_LEFT);RawFrame rna,rnb;render_raw(&an,&rna);render_raw(&bn,&rnb);
  printf("SINGLE_FRAME_ALIAS same_input=%d same_next=%d (expected 1,0)\n",raw_eq(&ra,&rb),raw_eq(&rna,&rnb));
}

int main(void){
  Model m;model_init(&m);train_raw_routes(&m,60000);train_action_life(&m,40000);
  puts("BPC Binary WorldFit v0.18 | external input = one 0/1 screen + operation; anonymous temporal trace born from frame change");
  alias_audit();
  unsigned long long all=0,ok=0;
  for(int s=0;s<8;s++){BStat x=raw_rollout(&m,1000,120,98765ULL+200003ULL*(uint64_t)s,BIN_NORMAL);print_bs("NORMAL",&x);all+=x.steps;ok+=x.exact;}
  printf("NORMAL_TOTAL %llu/%llu=%.6f%%\n",ok,all,100.0*(double)ok/(double)all);
  BStat off=raw_rollout(&m,200,120,777001ULL,BIN_TRACE_OFF);print_bs("TRACE_OFF",&off);
  BStat sh=raw_rollout(&m,200,120,777002ULL,BIN_TRACE_SHIFT);print_bs("TRACE_SHIFT",&sh);
  return 0;
}