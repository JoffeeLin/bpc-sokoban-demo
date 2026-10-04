#define main v22_embedded_main
#include "../minimal-v2.2/bpc_tetris_minimal_v22.c"
#undef main

static void random_preview_mask(RNG*r,uint8_t p[PREV]){
  /* Keep the physical rotation anchor itself occupied (local 1,1 = index 5).
     Other cells are arbitrary; no tetromino catalogue is used. */
  memset(p,0,PREV);p[5]=1;int n=1+ri(r,8),placed=1;
  while(placed<n){int i=ri(r,PREV);if(!p[i]){p[i]=1;placed++;}}
}
static int init_poly_episode(const Model*m,RNG*r,State*real,State*mod){
  uint8_t cur[PREV],nxt[PREV];random_preview_mask(r,cur);random_preview_mask(r,nxt);
  memset(real,0,sizeof(*real));memcpy(real->preview,cur,PREV);real_spawn(real);
  if(real->gameover||!memcmp(real->active,(uint8_t[N]){0},N))return 0;
  memcpy(real->preview,nxt,PREV);
  memset(mod,0,sizeof(*mod));uint8_t go=0;learned_spawn(m,cur,mod->world,mod->active,mod->pivot,1.f,&go);mod->gameover=go;memcpy(mod->preview,nxt,PREV);
  return !go;
}
typedef struct{unsigned long long steps,exact,locks,gameovers;unsigned long long byact[ACTS],okact[ACTS];int full_ep;}PStat;
static void rollout_poly(const Model*m,int episodes,int maxsteps,uint64_t seed){
  RNG r={seed};PStat st={0};int first_ep=-1,first_t=-1,first_act=-1,da=0,dw=0,dp=0,dg=0;
  for(int ep=0;ep<episodes;ep++){
    State real,mod;if(!init_poly_episode(m,&r,&real,&mod)){ep--;continue;}int epok=1;
    for(int t=0;t<maxsteps;t++){
      int u=ri(&r,100),act=u<18?ACT_LEFT:u<36?ACT_RIGHT:u<50?ACT_ROT:u<70?ACT_DOWN:ACT_DROP;
      int lr=real_step(&real,act),lm=model_step(m,&mod,act);
      int ok=(lr==lm)&&eq(real.active,mod.active,N)&&eq(real.world,mod.world,N)&&eq(real.pivot,mod.pivot,N)&&real.gameover==mod.gameover;
      st.steps++;st.exact+=ok;st.byact[act]++;st.okact[act]+=ok;if(lr)st.locks++;if(real.gameover)st.gameovers++;
      if(!ok){epok=0;if(first_ep<0){first_ep=ep;first_t=t;first_act=act;for(int i=0;i<N;i++){da+=real.active[i]!=mod.active[i];dw+=real.world[i]!=mod.world[i];dp+=real.pivot[i]!=mod.pivot[i];}dg=real.gameover!=mod.gameover;}break;}
      if(lr){if(real.gameover||mod.gameover)break;uint8_t np[PREV];random_preview_mask(&r,np);memcpy(real.preview,np,PREV);memcpy(mod.preview,np,PREV);}
    }
    st.full_ep+=epok;
  }
  const char*nm[ACTS]={"left","right","down","rot","drop"};
  printf("poly-rollout episodes=%d maxsteps=%d steps=%llu exact=%llu/%llu=%.6f%% full_ep=%d locks=%llu gameovers=%llu first_fail=%d:%d act=%d diffA/W/P/G=%d/%d/%d/%d\n",episodes,maxsteps,st.steps,st.exact,st.steps,100.0*(double)st.exact/st.steps,st.full_ep,st.locks,st.gameovers,first_ep,first_t,first_act,da,dw,dp,dg);
  for(int a=0;a<ACTS;a++)printf("  %-5s %llu/%llu=%.6f%%\n",nm[a],st.okact[a],st.byact[a],st.byact[a]?100.0*(double)st.okact[a]/st.byact[a]:0.0);
}
int main(int argc,char**argv){int ep=argc>1?atoi(argv[1]):5000,steps=argc>2?atoi(argv[2]):150;uint64_t seed=argc>3?(uint64_t)strtoull(argv[3],NULL,10):24681357ULL;Model m;model_init(&m);puts("BPC Tetris Minimal v2.4 | zero-shot arbitrary 1..8-cell preview/polyomino rollout");puts("training unchanged: only prior single-cell micro-experiences; no polyomino training");rollout_poly(&m,ep,steps,seed);return 0;}
