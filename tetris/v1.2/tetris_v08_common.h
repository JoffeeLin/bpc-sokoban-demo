#define main bpc_orig_main
#include "bpc_tetris_worldmodel.c"
#undef main

/* v0.8: GitHub-pure-line style local Beta residual medium on raw Tetris pixels.
   No Tetris object/landing/collision/distance/HardDrop/Lock rule is exposed.
   Train ONLY real one-cell, non-locking gravity transitions. Then freeze and
   recursively feed predictions for unseen distances. */

#define SIDE_W W
#define SIDE_H H
#define BITS 2
#define POWER 20
#define MSIZE (1u<<POWER)
#define MMASK (MSIZE-1u)
#define PHASES 4

typedef struct { uint8_t *z,*o; unsigned long long writes; } Medium;
static uint64_t fnv_mix(uint64_t v,uint8_t b){ return (v^(uint64_t)(b+1))*1099511628211ULL; }
static uint32_t addr_ctx(int phase,const uint8_t *ctx,int n,int bit){
  uint64_t v=1469598103934665603ULL;
  v=fnv_mix(v,(uint8_t)phase); v=fnv_mix(v,(uint8_t)bit);
  for(int i=0;i<n;i++) v=fnv_mix(v,ctx[i]);
  return (uint32_t)v & MMASK;
}
static void med_init(Medium*m){ memset(m,0,sizeof(*m)); m->z=calloc(MSIZE,1);m->o=calloc(MSIZE,1);if(!m->z||!m->o){fprintf(stderr,"alloc\n");exit(2);} }
static void med_free(Medium*m){free(m->z);free(m->o);memset(m,0,sizeof(*m));}

static void canvas2(const Game*g,uint8_t out[CELLS]){
  memset(out,0,CELLS);
  for(int y=0;y<H;y++)for(int x=0;x<W;x++) if((g->row[y]>>x)&1u) out[y*W+x]|=1u;
  if(!g->game_over){uint16_t m=SHAPE[g->type][g->rot&3];for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(occupied_mask(m,sx,sy)){
    int x=g->x+sx,y=g->y+sy;if(x>=0&&x<W&&y>=0&&y<H) out[y*W+x]|=2u;
  }}
}
static int can_fall(const Game*g){return !g->game_over&&!collides(g,g->type,g->rot,g->x,g->y+1);}
static void gravity_one(Game*g){ if(can_fall(g))g->y++; }
static int drop_distance(const Game*g){Game q=*g;int n=0;while(can_fall(&q)){q.y++;n++;}return n;}
static int exact(const uint8_t*a,const uint8_t*b){return memcmp(a,b,CELLS)==0;}
static int exact_active(const uint8_t*a,const uint8_t*b){for(int i=0;i<CELLS;i++)if((a[i]&2)!=(b[i]&2))return 0;return 1;}

/* Same task-independent projection family as GitHub pure medium:
   center, horizontal 3, vertical 3, 3x3. Outside physical canvas is sentinel 64. */
static int context(const uint8_t*f,int cell,int phase,uint8_t out[9]){
  int y=cell/W,x=cell%W,n=0;
  if(phase==0){out[n++]=f[cell];}
  else if(phase==1){for(int dx=-1;dx<=1;dx++){int xx=x+dx;out[n++]=(xx<0||xx>=W)?64:f[y*W+xx];}}
  else if(phase==2){for(int dy=-1;dy<=1;dy++){int yy=y+dy;out[n++]=(yy<0||yy>=H)?64:f[yy*W+x];}}
  else {for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){int xx=x+dx,yy=y+dy;out[n++]=(xx<0||xx>=W||yy<0||yy>=H)?64:f[yy*W+xx];}}
  return n;
}
static float prob(const Medium*m,const uint8_t*f,int cell,int bit){
  unsigned z=0,o=0;uint8_t c[9];
  for(int ph=0;ph<PHASES;ph++){int n=context(f,cell,ph,c);uint32_t a=addr_ctx(ph,c,n,bit);z+=m->z[a];o+=m->o[a];}
  return ((float)o+.5f)/((float)z+(float)o+1.f);
}
static void predict(const Medium*m,const uint8_t*f,float out[CELLS][BITS]){for(int i=0;i<CELLS;i++)for(int b=0;b<BITS;b++)out[i][b]=prob(m,f,i,b);}
static void measure(const float p[CELLS][BITS],uint8_t out[CELLS]){for(int i=0;i<CELLS;i++){out[i]=0;for(int b=0;b<BITS;b++)if(p[i][b]>=.5f)out[i]|=(uint8_t)(1u<<b);}}
static void observe(Medium*m,const uint8_t*f,const uint8_t*t){uint8_t c[9];for(int cell=0;cell<CELLS;cell++)for(int bit=0;bit<BITS;bit++){int v=(t[cell]>>bit)&1;for(int ph=0;ph<PHASES;ph++){int n=context(f,cell,ph,c);uint32_t a=addr_ctx(ph,c,n,bit);uint8_t *row=v?m->o:m->z;if(row[a]<255)row[a]++;m->writes++;}}}

static int sample_state(RNG*r,Game*g,Pilot*p,int mind){for(int q=0;q<3000;q++){if(g->game_over){game_init(g,rng_i(r,7));memset(p,0,sizeof(*p));}int n=1+rng_i(r,6);for(int k=0;k<n;k++){int a=pilot_action(g,p,r,1);game_step(g,a);if(g->game_over)break;}if(!g->game_over&&drop_distance(g)>=mind)return 1;if(!g->game_over)game_step(g,ACT_NONE);}return 0;}

static void train(Medium*m,int n,uint64_t seed){RNG r={seed};Game g;game_init(&g,rng_i(&r,7));Pilot p={0};for(int t=0;t<n;t++){
  if(!sample_state(&r,&g,&p,2)){t--;continue;}Game q=g;int d=drop_distance(&q);int k=rng_i(&r,d);for(int s=0;s<k;s++)gravity_one(&q);if(!can_fall(&q)){t--;continue;}
  uint8_t in[CELLS],tar[CELLS];canvas2(&q,in);Game nq=q;gravity_one(&nq);canvas2(&nq,tar);observe(m,in,tar);
}}

typedef struct{unsigned long long n,full,active;double bit;} Stat;
static void add(Stat*s,const uint8_t*p,const uint8_t*t){s->n++;s->full+=exact(p,t);s->active+=exact_active(p,t);int c=0;for(int i=0;i<CELLS;i++)for(int b=0;b<BITS;b++)c+=(((p[i]>>b)&1)==((t[i]>>b)&1));s->bit+=(double)c/(CELLS*BITS);}
static void printstat(const char*tag,const Stat*s){printf("%s n=%llu full=%.2f active=%.2f bit=%.4f\n",tag,s->n,100.0*s->full/s->n,100.0*s->active/s->n,100.0*s->bit/s->n);}
static void eval(Medium*m,int n,uint64_t seed){const int hs[]={1,2,3,5,8,12,16,20};enum{NH=8};Stat one={0},rec[NH];memset(rec,0,sizeof(rec));RNG r={seed};Game g;game_init(&g,rng_i(&r,7));Pilot p={0};
  for(int i=0;i<n;i++){
    if(!sample_state(&r,&g,&p,1)){i--;continue;}int d=drop_distance(&g);if(d<1){i--;continue;}
    uint8_t st[CELLS],t1[CELLS],p1[CELLS];canvas2(&g,st);Game q1=g;gravity_one(&q1);canvas2(&q1,t1);float pr1[CELLS][BITS];predict(m,st,pr1);measure(pr1,p1);add(&one,p1,t1);
    for(int hi=0;hi<NH;hi++){int h=hs[hi];if(d<h)continue;uint8_t cur[CELLS];memcpy(cur,st,CELLS);Game qt=g;for(int z=0;z<h;z++)gravity_one(&qt);uint8_t tar[CELLS];canvas2(&qt,tar);for(int z=0;z<h;z++){float pp[CELLS][BITS];uint8_t nx[CELLS];predict(m,cur,pp);measure(pp,nx);memcpy(cur,nx,CELLS);}add(&rec[hi],cur,tar);}
  }
  printstat("one",&one);for(int hi=0;hi<NH;hi++)if(rec[hi].n){char tag[32];snprintf(tag,sizeof(tag),"h=%d",hs[hi]);printstat(tag,&rec[hi]);}
}
