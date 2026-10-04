#define main v22_embedded_main
#include "../minimal-v2.2/bpc_tetris_minimal_v22.c"
#undef main

static void preview_exact_k(RNG*r,uint8_t p[PREV],int k){
  memset(p,0,PREV);p[5]=1;int placed=1;if(k<1)k=1;if(k>12)k=12;
  while(placed<k){int i=4+ri(r,12);if(!p[i]){p[i]=1;placed++;}}
}
static int init_ep_k(const Model*m,RNG*r,State*real,State*mod,int k){
  uint8_t cur[PREV],nxt[PREV];preview_exact_k(r,cur,k);preview_exact_k(r,nxt,k);
  memset(real,0,sizeof(*real));memcpy(real->preview,cur,PREV);real_spawn(real);if(real->gameover)return 0;memcpy(real->preview,nxt,PREV);
  memset(mod,0,sizeof(*mod));uint8_t go=0;learned_spawn(m,cur,mod->world,mod->active,mod->pivot,1.f,&go);mod->gameover=go;memcpy(mod->preview,nxt,PREV);return !go;
}
static void ladder(const Model*m,int k,int episodes,int maxsteps,uint64_t seed){
  RNG r={seed};unsigned long long steps=0,okn=0,locks=0;int full=0,first=-1;
  for(int ep=0;ep<episodes;ep++){
    State a,b;if(!init_ep_k(m,&r,&a,&b,k)){ep--;continue;}int epok=1;
    for(int t=0;t<maxsteps;t++){
      int u=ri(&r,100),act=u<18?ACT_LEFT:u<36?ACT_RIGHT:u<50?ACT_ROT:u<70?ACT_DOWN:ACT_DROP;
      int ra=real_step(&a,act),rb=model_step(m,&b,act);int q=(ra==rb)&&eq(a.active,b.active,N)&&eq(a.world,b.world,N)&&eq(a.pivot,b.pivot,N)&&a.gameover==b.gameover;
      steps++;okn+=q;if(ra)locks++;if(!q){epok=0;if(first<0)first=ep;break;}
      if(ra){if(a.gameover||b.gameover)break;uint8_t np[PREV];preview_exact_k(&r,np,k);memcpy(a.preview,np,PREV);memcpy(b.preview,np,PREV);}
    }
    full+=epok;
  }
  printf("k=%2d episodes=%d steps=%llu exact=%llu/%llu=%9.6f%% full_ep=%d locks=%llu first_fail=%d\n",k,episodes,steps,okn,steps,100.0*(double)okn/steps,full,locks,first);
}
int main(int argc,char**argv){int ep=argc>1?atoi(argv[1]):300,ms=argc>2?atoi(argv[2]):100;Model m;model_init(&m);puts("BPC Tetris Minimal v2.5 | zero-shot entity-count ladder 1..12 cells");for(int k=1;k<=12;k++)ladder(&m,k,ep,ms,0x250000ULL+1009u*(unsigned)k);return 0;}
