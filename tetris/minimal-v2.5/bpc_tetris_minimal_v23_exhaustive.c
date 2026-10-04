#define main v22_embedded_main
#include "bpc_tetris_minimal_v22_core.c"
#undef main

static int popu(unsigned x){ return __builtin_popcount(x); }

static void true_translate_sparse(const uint8_t *src,const uint8_t *world,uint8_t *out,int dir){
  int blocked=0;
  for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(src[y*W+x]){
    int tx=x+MDX[dir],ty=y+MDY[dir];
    if(tx<0||tx>=W||ty<0||ty>=H||world[ty*W+tx]) blocked=1;
  }
  if(blocked){ memcpy(out,src,N); return; }
  memset(out,0,N);
  for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(src[y*W+x]) out[(y+MDY[dir])*W+x+MDX[dir]]=1;
}

static void model_translate_sparse(const Model*m,const uint8_t*src,const uint8_t*world,uint8_t*out,int dir){
  float C=1.f;
  for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(src[y*W+x]) C*=move_go(&m->mv,&m->mb,world,dir,x,y);
  memset(out,0,N);uint8_t mark[N]={0};
  for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(src[y*W+x]){
    for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){
      int ox=x+dx,oy=y+dy;if(ox>=0&&ox<W&&oy>=0&&oy<H)mark[oy*W+ox]=1;
    }
  }
  for(int i=0;i<N;i++)if(mark[i]){
    int x=i%W,y=i/W;float q=C*move_basep(&m->mv,src,dir,x,y)+(1.f-C)*(float)src[i];out[i]=(uint8_t)(q>.5f);
  }
}

static void audit_translate_exhaustive(const Model*m){
  unsigned long long n=0,ok=0,blockedn=0,blockedok=0;const int bx=3,by=8;uint8_t a[N],w[N],t[N],p[N];
  for(unsigned am=1;am<512;am++){if(popu(am)>4)continue;for(unsigned wm=0;wm<512;wm++){if(am&wm)continue;
    memset(a,0,N);memset(w,0,N);
    for(int k=0;k<9;k++){int x=bx+k%3,y=by+k/3;if((am>>k)&1u)a[y*W+x]=1;if((wm>>k)&1u)w[y*W+x]=1;}
    for(int dir=0;dir<3;dir++){true_translate_sparse(a,w,t,dir);model_translate_sparse(m,a,w,p,dir);n++;ok+=eq(t,p,N);if(eq(t,a,N)){blockedn++;blockedok+=eq(t,p,N);}}
  }}
  printf("EXHAUST translate<=4cell+3x3world n=%llu exact=%llu/%llu=%.6f%% blocked=%llu/%llu=%.6f%%\n",n,ok,n,100.0*(double)ok/n,blockedok,blockedn,100.0*(double)blockedok/blockedn);
}

static void true_rot_local(const uint8_t in[SLOTS],const uint8_t world[SLOTS],uint8_t out[SLOTS]){
  uint8_t cand[SLOTS]={0};int blocked=0;
  for(int si=0;si<SLOTS;si++)if(in[si]){int sx,sy,ox,oy;lunidx(si,&sx,&sy);rr(sx,sy,&ox,&oy);int oi=lidx(ox,oy);if(world[oi])blocked=1;cand[oi]=1;}
  if(blocked)memcpy(out,in,SLOTS);else memcpy(out,cand,SLOTS);
}
static void model_rot_local_exact(const Model*m,const uint8_t in[SLOTS],const uint8_t world[SLOTS],uint8_t out[SLOTS]){
  float C=1.f;for(int si=0;si<SLOTS;si++)if(in[si])C*=rot_go(&m->rot,&m->rb,si,world);
  float rb[SLOTS];rot_local_base(&m->rot,in,rb);
  for(int i=0;i<SLOTS;i++)out[i]=(uint8_t)((C*rb[i]+(1.f-C)*(float)in[i])>.5f);
}
static void audit_rotation_exhaustive(const Model*m){
  unsigned long long n=0,ok=0,blockedn=0,blockedok=0;uint8_t in[SLOTS],w[SLOTS],t[SLOTS],p[SLOTS];
  const unsigned limit=1u<<SLOTS;
  for(unsigned mask=1;mask<limit;mask++){if(popu(mask)>4)continue;memset(in,0,SLOTS);for(int i=0;i<SLOTS;i++)if((mask>>i)&1u)in[i]=1;
    memset(w,0,SLOTS);true_rot_local(in,w,t);model_rot_local_exact(m,in,w,p);n++;ok+=eq(t,p,SLOTS);
    for(int oi=0;oi<SLOTS;oi++)if(!in[oi]){memset(w,0,SLOTS);w[oi]=1;true_rot_local(in,w,t);model_rot_local_exact(m,in,w,p);n++;ok+=eq(t,p,SLOTS);if(eq(t,in,SLOTS)){blockedn++;blockedok+=eq(t,p,SLOTS);}}
  }
  printf("EXHAUST rotate<=4cell+singleObstacle n=%llu exact=%llu/%llu=%.6f%% blocked=%llu/%llu=%.6f%%\n",n,ok,n,100.0*(double)ok/n,blockedok,blockedn,100.0*(double)blockedok/blockedn);
}

static void audit_spawn_exhaustive(const Model*m){
  unsigned long long n=0,ok=0,blockedn=0,blockedok=0;uint8_t prev[PREV],ta[N],tpiv[N],ma[N],mp[N],world[N];
  for(unsigned mask=1;mask<(1u<<PREV);mask++){for(int i=0;i<PREV;i++)prev[i]=(uint8_t)((mask>>i)&1u);env_spawn_from_preview(prev,ta,tpiv);
    memset(world,0,N);memset(ma,0,N);memset(mp,0,N);uint8_t go=0;learned_spawn(m,prev,world,ma,mp,1.f,&go);n++;ok+=(eq(ta,ma,N)&&eq(tpiv,mp,N)&&go==0);
    int bi=-1;for(int i=0;i<N;i++)if(ta[i]){bi=i;break;}if(bi>=0){memset(world,0,N);world[bi]=1;memset(ma,0,N);memset(mp,0,N);go=0;learned_spawn(m,prev,world,ma,mp,1.f,&go);blockedn++;blockedok+=(go==1&&eq(ma,(uint8_t[N]){0},N));}
  }
  printf("EXHAUST spawn all-nonempty-preview clear=%llu/%llu=%.6f%% blocked=%llu/%llu=%.6f%%\n",ok,n,100.0*(double)ok/n,blockedok,blockedn,100.0*(double)blockedok/blockedn);
}

static void audit_line_primitives(const Model*m){
  unsigned rowok=0;for(unsigned mask=0;mask<1024;mask++){uint8_t b[N]={0};for(int x=0;x<W;x++)b[5*W+x]=(uint8_t)((mask>>x)&1u);int pred=rowc(&m->cw,b,5)>.5f;rowok+=(pred==(mask==1023));}
  unsigned propok=0;for(unsigned mask=0;mask<1024;mask++){uint8_t b[N]={0};for(int x=0;x<W;x++)b[4*W+x]=(uint8_t)((mask>>x)&1u);for(int x=0;x<W;x++)b[5*W+x]=1;float car[H]={0};car[5]=1.f;prop_step(&m->prop,b,car,5);int good=1;for(int x=0;x<W;x++){good&=(b[5*W+x]==((mask>>x)&1u));good&=(b[4*W+x]==0);}propok+=good;}
  printf("EXHAUST row-carrier 1024 patterns exact=%u/1024=%.6f%%\n",rowok,100.0*rowok/1024.0);
  printf("EXHAUST row-propagation 1024 source rows exact=%u/1024=%.6f%%\n",propok,100.0*propok/1024.0);
}
int main(void){Model m;model_init(&m);puts("BPC Tetris Minimal v2.3 exhaustive compositional audit");audit_translate_exhaustive(&m);audit_rotation_exhaustive(&m);audit_spawn_exhaustive(&m);audit_line_primitives(&m);return 0;}
