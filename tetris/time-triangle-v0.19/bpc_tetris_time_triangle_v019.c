#define main v011_hidden_main
#include "../d1-function-v0.14b/base_v011.c"
#undef main

#define ZDEPTH 6
#define TBITS2 18
#define TSZ2 (1u<<TBITS2)
#define TMASK2 (TSZ2-1u)
#define TLR 0.24f

typedef struct { float *w[ZDEPTH][BR]; unsigned long long writes; } TriCube;

static void tri_init(TriCube *t){
  memset(t,0,sizeof(*t));
  for(int z=0;z<ZDEPTH;z++) for(int b=0;b<BR;b++){
    t->w[z][b]=(float*)calloc(TSZ2,sizeof(float));
    if(!t->w[z][b]){fprintf(stderr,"tri alloc failed\n");exit(2);}
  }
}
static void tri_free(TriCube *t){
  for(int z=0;z<ZDEPTH;z++)for(int b=0;b<BR;b++)free(t->w[z][b]);
  memset(t,0,sizeof(*t));
}
static inline uint32_t ta(uint32_t a){return a & TMASK2;}

static void tri_predict(const FC *fc,const TriCube *tc,
                        uint8_t frames[ZDEPTH+1][FRAME],int actions[ZDEPTH],int k,
                        int mode,float p[FRAME]){
  float latest_fun[FD];
  fw(fc,actions[k-1],latest_fun);
  funcbase(frames[k-1],latest_fun,p);
  const float norm=1.0f/sqrtf((float)k);
  Cache c;
  for(int i=0;i<k;i++){
    int zi=i;
    if(mode==2) zi=(i*5+1)%k;
    float fun[FD];
    fw(fc,actions[i],fun);
    cache(frames[i],fun,&c);
    for(int j=0;j<FRAME;j++){
      float r=0.f;
      for(int b=0;b<BR;b++) r += tc->w[zi][b][ta(c.a[b][j])];
      p[j] += norm*(r/BR);
    }
  }
  for(int j=0;j<FRAME;j++){
    if(p[j]<.001f)p[j]=.001f;
    if(p[j]>.999f)p[j]=.999f;
  }
}

static void tri_train_target(const FC *fc,TriCube *tc,
                             uint8_t frames[ZDEPTH+1][FRAME],int actions[ZDEPTH],int k,
                             int last_only_write){
  float p[FRAME];
  tri_predict(fc,tc,frames,actions,k,0,p);
  const float norm=1.0f/sqrtf((float)k);
  for(int i=0;i<k;i++){
    if(last_only_write && i!=k-1) continue;
    float fun[FD];
    Cache c;
    fw(fc,actions[i],fun);
    cache(frames[i],fun,&c);
    for(int j=0;j<FRAME;j++){
      float e=(float)frames[k][j]-p[j];
      float d=TLR*e*norm/BR;
      for(int b=0;b<BR;b++){
        float *w=&tc->w[i][b][ta(c.a[b][j])];
        *w += d;
        if(*w>1.5f)*w=1.5f;
        if(*w<-1.5f)*w=-1.5f;
        tc->writes++;
      }
    }
  }
}

typedef struct {
  unsigned long long n,exact;
  unsigned long long evn[5],eve[5];
  unsigned long long bits,cor,tp,fp,fn;
} TM;

static void tm_add(TM*m,const uint8_t*in,const uint8_t*t,const float*p,int ev){
  int ex=1;
  for(int j=0;j<FRAME;j++){
    int q=p[j]>=.5f,y=t[j];
    m->bits++;m->cor+=(q==y);
    if(q!=y)ex=0;
    int tc=t[j]!=in[j],pc=q!=in[j];
    if(pc&&tc)m->tp++;
    else if(pc&&!tc)m->fp++;
    else if(!pc&&tc)m->fn++;
  }
  m->n++;m->exact+=ex;
  int fl[5]={EV_MOVE,EV_ROT,EV_LOCK,EV_CLEAR,EV_GAMEOVER};
  for(int z=0;z<5;z++)if(ev&fl[z]){m->evn[z]++;m->eve[z]+=ex;}
}
static void tm_print(const char*tag,const TM*m){
  double pr=(m->tp+m->fp)?(double)m->tp/(m->tp+m->fp):0;
  double re=(m->tp+m->fn)?(double)m->tp/(m->tp+m->fn):0;
  double f=(pr+re)?2*pr*re/(pr+re):0;
  printf("[%s] frame=%.3f bit=%.3f f1=%.3f",
    tag,100.0*m->exact/(m->n?m->n:1),100.0*m->cor/(m->bits?m->bits:1),f);
  const char*nm[5]={"move","rot","lock","clear","over"};
  for(int z=0;z<5;z++)if(m->evn[z])
    printf(" %s=%.2f(%llu)",nm[z],100.0*m->eve[z]/m->evn[z],
           (unsigned long long)m->evn[z]);
  puts("");
}

static void collect_block(Game*g,Pilot*po,RNG*r,
                          uint8_t frames[ZDEPTH+1][FRAME],
                          int actions[ZDEPTH],int events[ZDEPTH]){
  if(g->game_over){init(g,ri(r,7));memset(po,0,sizeof(*po));}
  render(g,frames[0]);
  for(int k=0;k<ZDEPTH;k++){
    if(g->game_over){
      init(g,ri(r,7));memset(po,0,sizeof(*po));render(g,frames[k]);
    }
    actions[k]=pol(g,po,r,1);
    events[k]=step(g,actions[k]);
    render(g,frames[k+1]);
  }
}

static void warm_fc(TriCube *unused, FC*fc,int steps,uint64_t seed){
  (void)unused;
  RNG r={seed};
  Game g;init(&g,ri(&r,7));
  Pilot po={0};
  uint8_t a[FRAME],t[FRAME];
  for(int i=0;i<steps;i++){
    if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}
    render(&g,a);
    int ac=pol(&g,&po,&r,1);
    step(&g,ac);
    render(&g,t);
    fobs(fc,a,ac,t);
  }
}

static void train_tri(const FC*fc,TriCube*tc,int blocks,uint64_t seed,int last_only_write){
  RNG r={seed};
  Game g;init(&g,ri(&r,7));
  Pilot po={0};
  uint8_t f[ZDEPTH+1][FRAME];
  int a[ZDEPTH],ev[ZDEPTH];
  for(int n=0;n<blocks;n++){
    collect_block(&g,&po,&r,f,a,ev);
    for(int k=1;k<=ZDEPTH;k++)
      tri_train_target(fc,tc,f,a,k,last_only_write);
  }
}

static void eval_tri(const FC*fc,const TriCube*tc,int blocks,uint64_t seed,int mode,const char*tag){
  RNG r={seed};
  Game g;init(&g,ri(&r,7));
  Pilot po={0};
  uint8_t f[ZDEPTH+1][FRAME];
  int a[ZDEPTH],ev[ZDEPTH];
  TM m={0};
  for(int n=0;n<blocks;n++){
    collect_block(&g,&po,&r,f,a,ev);
    for(int k=1;k<=ZDEPTH;k++){
      float p[FRAME];
      if(mode==1){
        float fun[FD];
        Cache c;
        fw(fc,a[k-1],fun);
        funcbase(f[k-1],fun,p);
        cache(f[k-1],fun,&c);
        for(int j=0;j<FRAME;j++){
          float rr=0;
          for(int b=0;b<BR;b++)rr+=tc->w[k-1][b][ta(c.a[b][j])];
          p[j]+=rr/BR;
          if(p[j]<.001f)p[j]=.001f;
          if(p[j]>.999f)p[j]=.999f;
        }
      }else{
        tri_predict(fc,tc,f,a,k,mode,p);
      }
      tm_add(&m,f[k-1],f[k],p,ev[k-1]);
    }
  }
  tm_print(tag,&m);
}

int main(int argc,char**argv){
  int warm=argc>1?atoi(argv[1]):12000;
  int blocks=argc>2?atoi(argv[2]):12000;
  int evalb=argc>3?atoi(argv[3]):1200;
  int seed=argc>4?atoi(argv[4]):0;
  uint64_t so=(uint64_t)(seed+1)*0x9e3779b97f4a7c15ULL;
  FC fc={0};
  TriCube tri,last;
  tri_init(&tri);
  tri_init(&last);
  warm_fc(&tri,&fc,warm,0x190001ULL^so);
  train_tri(&fc,&tri,blocks,0x190101ULL^so,0);
  train_tri(&fc,&last,blocks,0x190101ULL^so,1);
  printf("BPC Tetris v0.19 temporal-triangle Z=%d warm=%d blocks=%d seed=%d\n",
         ZDEPTH,warm,blocks,seed);
  printf("writes triangle=%llu lastwrite=%llu\n",tri.writes,last.writes);
  eval_tri(&fc,&tri,evalb,0x19EE01ULL^so,0,"triangle");
  eval_tri(&fc,&tri,evalb,0x19EE01ULL^so,1,"last-only-read");
  eval_tri(&fc,&tri,evalb,0x19EE01ULL^so,2,"z-shuffle");
  eval_tri(&fc,&last,evalb,0x19EE01ULL^so,0,"no-old-writeback");
  tri_free(&last);
  tri_free(&tri);
  return 0;
}
