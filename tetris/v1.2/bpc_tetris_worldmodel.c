#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define W 10
#define H 20
#define CELLS (W*H)
#define PREVIEW 16
#define FRAME_BITS (CELLS*2 + PREVIEW + 1)
#define ACTIONS 5
#define G_BRANCHES 6
#define G_BUCKETS 2048
#define G_PROBES 10
#define L_BRANCHES 4
#define L_BUCKETS 65536
#define L_PROBES 10
#define LR 0.60f
#define GAIN_G 0.25f
#define GAIN_L 0.75f
#define TRAIN_STEPS 60000
#define EVAL_STEPS 5000
#define ROLLOUT_WINDOWS 120
#define ROLLOUT_HORIZON 20

enum { ACT_NONE=0, ACT_LEFT, ACT_RIGHT, ACT_ROT, ACT_DROP };
enum { EV_MOVE=1, EV_ROT=2, EV_DROP=4, EV_LOCK=8, EV_CLEAR=16, EV_GAMEOVER=32 };

typedef struct { uint64_t s; } RNG;
static uint32_t rng_u32(RNG *r){ r->s ^= r->s>>12; r->s ^= r->s<<25; r->s ^= r->s>>27; return (uint32_t)((r->s*2685821657736338717ULL)>>32); }
static int rng_i(RNG *r,int n){ return n? (int)(rng_u32(r)%(uint32_t)n):0; }
static float rng_f(RNG *r){ return (rng_u32(r)+0.5f)/4294967296.0f; }

static const uint16_t SHAPE[7][4] = {
  {0x00F0,0x4444,0x00F0,0x4444},
  {0x0660,0x0660,0x0660,0x0660},
  {0x0270,0x0262,0x0720,0x0232},
  {0x0360,0x0462,0x0360,0x0462},
  {0x0630,0x0264,0x0630,0x0264},
  {0x0710,0x0226,0x0470,0x0322},
  {0x0740,0x0622,0x0170,0x0223}
};

typedef struct {
  uint16_t row[H];
  int type, rot, x, y, next_type;
  int game_over, lines, pieces;
} Game;

static int occupied_mask(uint16_t m,int sx,int sy){ return (m >> (sy*4+sx)) & 1; }
static int collides(const Game *g,int type,int rot,int x,int y){
  uint16_t m=SHAPE[type][rot&3];
  for(int sy=0;sy<4;sy++) for(int sx=0;sx<4;sx++) if(occupied_mask(m,sx,sy)){
    int bx=x+sx, by=y+sy;
    if(bx<0||bx>=W||by>=H) return 1;
    if(by>=0 && (g->row[by]&(1u<<bx))) return 1;
  }
  return 0;
}
static int spawn(Game *g){
  g->type=g->next_type;
  g->next_type=(g->next_type+1)%7;
  g->rot=0; g->x=3; g->y=-1; g->pieces++;
  if(collides(g,g->type,g->rot,g->x,g->y)){ g->game_over=1; return 0; }
  return 1;
}
static void game_init(Game *g,int start_type){ memset(g,0,sizeof(*g)); g->next_type=start_type%7; spawn(g); }
static int clear_lines(Game *g){
  int n=0;
  for(int y=H-1;y>=0;y--){
    if((g->row[y]&((1u<<W)-1))==((1u<<W)-1)){
      for(int yy=y;yy>0;yy--) g->row[yy]=g->row[yy-1];
      g->row[0]=0; n++; y++;
    }
  }
  g->lines+=n; return n;
}
static int lock_piece(Game *g){
  uint16_t m=SHAPE[g->type][g->rot&3];
  for(int sy=0;sy<4;sy++) for(int sx=0;sx<4;sx++) if(occupied_mask(m,sx,sy)){
    int bx=g->x+sx, by=g->y+sy;
    if(by<0){ g->game_over=1; return EV_LOCK|EV_GAMEOVER; }
    if(bx>=0&&bx<W&&by<H) g->row[by]|=(uint16_t)(1u<<bx);
  }
  int ev=EV_LOCK;
  if(clear_lines(g)) ev|=EV_CLEAR;
  if(!spawn(g)) ev|=EV_GAMEOVER;
  return ev;
}
static int game_step(Game *g,int a){
  if(g->game_over) return EV_GAMEOVER;
  int ev=0;
  if(a==ACT_LEFT && !collides(g,g->type,g->rot,g->x-1,g->y)){ g->x--; ev|=EV_MOVE; }
  else if(a==ACT_RIGHT && !collides(g,g->type,g->rot,g->x+1,g->y)){ g->x++; ev|=EV_MOVE; }
  else if(a==ACT_ROT && !collides(g,g->type,(g->rot+1)&3,g->x,g->y)){ g->rot=(g->rot+1)&3; ev|=EV_ROT; }
  else if(a==ACT_DROP){
    while(!collides(g,g->type,g->rot,g->x,g->y+1)) g->y++;
    ev|=EV_DROP;
    return ev|lock_piece(g);
  }
  if(!collides(g,g->type,g->rot,g->x,g->y+1)) g->y++;
  else ev|=lock_piece(g);
  return ev;
}
static void render_bits(const Game *g,uint8_t out[FRAME_BITS]){
  memset(out,0,FRAME_BITS);
  for(int y=0;y<H;y++) for(int x=0;x<W;x++) out[y*W+x]=(g->row[y]>>x)&1u;
  if(!g->game_over){
    uint16_t m=SHAPE[g->type][g->rot&3];
    for(int sy=0;sy<4;sy++) for(int sx=0;sx<4;sx++) if(occupied_mask(m,sx,sy)){
      int x=g->x+sx,y=g->y+sy;
      if(x>=0&&x<W&&y>=0&&y<H) out[CELLS+y*W+x]=1;
    }
  }
  uint16_t pm=SHAPE[g->next_type][0];
  for(int y=0;y<4;y++) for(int x=0;x<4;x++) out[CELLS*2+y*4+x]=occupied_mask(pm,x,y);
  out[FRAME_BITS-1]=(uint8_t)(g->game_over?1:0);
}
static void print_game(const Game *g){
  uint8_t f[FRAME_BITS]; render_bits(g,f);
  printf("\x1b[2J\x1b[H");
  printf("BPC Tetris  lines=%d  pieces=%d  next=%d\n",g->lines,g->pieces,g->next_type);
  printf("+----------+\n");
  for(int y=0;y<H;y++){ putchar('|'); for(int x=0;x<W;x++){ int l=f[y*W+x], a=f[CELLS+y*W+x]; putchar(a?'@':(l?'#':' ')); } puts("|"); }
  puts("+----------+");
  puts("a=left d=right w=rotate s=wait x=hard-drop q=quit (press Enter)");
  if(g->game_over) puts("GAME OVER");
}

typedef struct {
  float *gw;
  float *lw;
  uint16_t gprobe[G_BRANCHES][G_PROBES];
  int8_t ldx[L_BRANCHES][L_PROBES], ldy[L_BRANCHES][L_PROBES], lplane[L_BRANCHES][L_PROBES];
} BPC;

static inline float clampf1(float x,float a,float b){ return x<a?a:(x>b?b:x); }
static uint32_t mix32(uint32_t x){ x^=x>>16; x*=0x7feb352dU; x^=x>>15; x*=0x846ca68bU; x^=x>>16; return x; }
static int action_code(int a){ return a<0?0:(a>=ACTIONS?0:a); }

static void bpc_init(BPC *m,uint32_t seed){
  memset(m,0,sizeof(*m));
  m->gw=(float*)calloc((size_t)G_BRANCHES*G_BUCKETS*FRAME_BITS,sizeof(float));
  m->lw=(float*)calloc((size_t)L_BRANCHES*L_BUCKETS*2,sizeof(float));
  if(!m->gw||!m->lw){ fprintf(stderr,"alloc failed\n"); exit(2); }
  uint32_t s=seed;
  for(int b=0;b<G_BRANCHES;b++) for(int k=0;k<G_PROBES;k++){ s=mix32(s+0x9e3779b9U+b*97+k*131); m->gprobe[b][k]=(uint16_t)(s%FRAME_BITS); }
  for(int b=0;b<L_BRANCHES;b++) for(int k=0;k<L_PROBES;k++){
    s=mix32(s+0x85ebca6bU+b*113+k*197);
    int r=(k<7)?2:5;
    m->ldx[b][k]=(int8_t)((int)(s%(2*r+1))-r);
    s=mix32(s+17); m->ldy[b][k]=(int8_t)((int)(s%(2*r+1))-r);
    s=mix32(s+29); m->lplane[b][k]=(int8_t)(s&1u);
  }
}
static void bpc_free(BPC *m){ free(m->gw); free(m->lw); memset(m,0,sizeof(*m)); }
static int gaddr(const BPC *m,const uint8_t *f,int a,int b){
  uint32_t h=(uint32_t)(action_code(a)+1)*0x9e3779b1U ^ (uint32_t)(b+7)*0x85ebca6bU;
  for(int k=0;k<G_PROBES;k++) h=mix32(h ^ ((uint32_t)f[m->gprobe[b][k]] + 0x100u*(uint32_t)(k+1)));
  return (int)(h&(G_BUCKETS-1));
}
static int laddr(const BPC *m,const uint8_t *f,int a,int b,int x,int y){
  (void)m;
  uint32_t h=(uint32_t)(action_code(a)+3)*0x27d4eb2dU ^ (uint32_t)(b+1)*0x165667b1U;
  if(b==0){
    for(int pl=0;pl<2;pl++) for(int dy=-1;dy<=1;dy++) for(int dx=-1;dx<=1;dx++){
      int xx=x+dx,yy=y+dy,bit=(xx<0||xx>=W||yy<0||yy>=H)?1:f[pl*CELLS+yy*W+xx];
      h=mix32(h ^ (uint32_t)(bit + 7*(pl+1)+13*(dx+2)+31*(dy+2)));
    }
  }else if(b==1){
    for(int pl=0;pl<2;pl++) for(int dy=-2;dy<=2;dy++) for(int dx=-2;dx<=2;dx++) if(((dx+dy)&1)==0){
      int xx=x+dx,yy=y+dy,bit=(xx<0||xx>=W||yy<0||yy>=H)?1:f[pl*CELLS+yy*W+xx];
      h=mix32(h ^ (uint32_t)(bit + 11*(pl+1)+17*(dx+3)+37*(dy+3)));
    }
  }else if(b==2){
    for(int pl=0;pl<2;pl++) for(int xx=0;xx<W;xx++) h=mix32(h ^ (uint32_t)(f[pl*CELLS+y*W+xx]+19*pl+41*xx));
  }else{
    for(int pl=0;pl<2;pl++) for(int yy=0;yy<H;yy++) h=mix32(h ^ (uint32_t)(f[pl*CELLS+yy*W+x]+23*pl+43*yy));
  }
  return (int)(h&(L_BUCKETS-1));
}
static void bpc_predict(const BPC *m,const uint8_t *f,int a,float out[FRAME_BITS]){
  int ga[G_BRANCHES]; for(int b=0;b<G_BRANCHES;b++) ga[b]=gaddr(m,f,a,b);
  for(int j=0;j<FRAME_BITS;j++){
    float rg=0.0f;
    for(int b=0;b<G_BRANCHES;b++) rg += m->gw[((size_t)b*G_BUCKETS+ga[b])*FRAME_BITS+j];
    rg/=G_BRANCHES;
    float rl=0.0f;
    if(j<CELLS*2){
      int plane=j/CELLS, q=j%CELLS, x=q%W, y=q/W;
      for(int b=0;b<L_BRANCHES;b++){ int la=laddr(m,f,a,b,x,y); rl += m->lw[((size_t)b*L_BUCKETS+la)*2+plane]; }
      rl/=L_BRANCHES;
    }
    float base = (float)f[j];
    out[j]=clampf1(base + GAIN_G*rg + GAIN_L*rl,0.001f,0.999f);
  }
}
static float bpc_train(BPC *m,const uint8_t *f,int a,const uint8_t *target){
  float p[FRAME_BITS]; bpc_predict(m,f,a,p);
  int ga[G_BRANCHES]; for(int b=0;b<G_BRANCHES;b++) ga[b]=gaddr(m,f,a,b);
  double mse=0.0;
  for(int j=0;j<FRAME_BITS;j++){
    float e=(float)target[j]-p[j]; mse+=e*e;
    float dg=LR*GAIN_G*e/G_BRANCHES;
    for(int b=0;b<G_BRANCHES;b++){ float *w=&m->gw[((size_t)b*G_BUCKETS+ga[b])*FRAME_BITS+j]; *w=clampf1(*w+dg,-1.5f,1.5f); }
    if(j<CELLS*2){
      int plane=j/CELLS, q=j%CELLS, x=q%W, y=q/W;
      float dl=LR*GAIN_L*e/L_BRANCHES;
      for(int b=0;b<L_BRANCHES;b++){ int la=laddr(m,f,a,b,x,y); float *w=&m->lw[((size_t)b*L_BUCKETS+la)*2+plane]; *w=clampf1(*w+dl,-1.5f,1.5f); }
    }
  }
  return (float)(mse/FRAME_BITS);
}

typedef struct { int target_rot,target_x,valid,last_pieces; } Pilot;
static int board_holes(const Game *g){ int holes=0; for(int x=0;x<W;x++){ int seen=0; for(int y=0;y<H;y++){ if(g->row[y]&(1u<<x)) seen=1; else if(seen) holes++; }} return holes; }
static int board_height(const Game *g){ int sum=0; for(int x=0;x<W;x++){ int h=0; for(int y=0;y<H;y++) if(g->row[y]&(1u<<x)){ h=H-y; break; } sum+=h; } return sum; }
static int landing_y(const Game *g,int type,int rot,int x){ int y=-2; if(collides(g,type,rot,x,y)) return 999; while(!collides(g,type,rot,x,y+1)) y++; return y; }
static void choose_target(const Game *g,Pilot *p,RNG *r){
  float best=-1e30f; int br=0,bx=3;
  for(int rot=0;rot<4;rot++) for(int x=-2;x<W;x++){
    int y=landing_y(g,g->type,rot,x); if(y==999) continue;
    Game q=*g; q.rot=rot; q.x=x; q.y=y; q.game_over=0;
    int before=q.lines; int ev=lock_piece(&q); (void)ev;
    int lc=q.lines-before, holes=board_holes(&q), ht=board_height(&q);
    float jitter=(rng_f(r)-0.5f)*12.0f;
    float sc=120.0f*lc-8.0f*holes-0.6f*ht+jitter;
    if(sc>best){ best=sc;br=rot;bx=x; }
  }
  p->target_rot=br; p->target_x=bx; p->valid=1; p->last_pieces=g->pieces;
}
static int pilot_action(const Game *g,Pilot *p,RNG *r,int explore){
  if(g->game_over) return ACT_NONE;
  if(!p->valid||p->last_pieces!=g->pieces) choose_target(g,p,r);
  if(explore && rng_i(r,100)<18) return rng_i(r,ACTIONS);
  if(g->rot!=p->target_rot) return ACT_ROT;
  if(g->x<p->target_x) return ACT_RIGHT;
  if(g->x>p->target_x) return ACT_LEFT;
  return (rng_i(r,100)<75)?ACT_DROP:ACT_NONE;
}

typedef struct { uint64_t bits, correct, frames, exact; uint64_t ch_tp,ch_fp,ch_fn; double mse; uint64_t ev_n[6], ev_exact[6]; } Metrics;
static void metrics_add(Metrics *m,const uint8_t *in,const uint8_t *t,const float *p,int ev){
  int exact=1;
  for(int j=0;j<FRAME_BITS;j++){
    int q=p[j]>=0.5f, y=t[j]; m->bits++; m->correct+=(q==y); if(q!=y) exact=0;
    double e=(double)y-p[j]; m->mse+=e*e;
    int tc=(t[j]!=in[j]), pc=(q!=in[j]); if(pc&&tc) m->ch_tp++; else if(pc&&!tc) m->ch_fp++; else if(!pc&&tc) m->ch_fn++;
  }
  m->frames++; m->exact+=exact;
  int flags[6]={EV_MOVE,EV_ROT,EV_DROP,EV_LOCK,EV_CLEAR,EV_GAMEOVER};
  for(int i=0;i<6;i++) if(ev&flags[i]){m->ev_n[i]++;m->ev_exact[i]+=exact;}
}
static void print_metrics(const char *tag,const Metrics *m){
  double acc=m->bits?100.0*m->correct/m->bits:0, ex=m->frames?100.0*m->exact/m->frames:0;
  double pr=(m->ch_tp+m->ch_fp)?(double)m->ch_tp/(m->ch_tp+m->ch_fp):0, re=(m->ch_tp+m->ch_fn)?(double)m->ch_tp/(m->ch_tp+m->ch_fn):0;
  double f1=(pr+re)?2*pr*re/(pr+re):0;
  printf("[%s] bit=%.3f%% frame_exact=%.3f%% changed_F1=%.3f mse=%.5f",tag,acc,ex,f1,m->bits?m->mse/m->bits:0);
  const char *nm[6]={"move","rot","drop","lock","clear","gameover"};
  for(int i=0;i<6;i++) if(m->ev_n[i]) printf(" %s_exact=%.1f%%(%llu)",nm[i],100.0*m->ev_exact[i]/m->ev_n[i],(unsigned long long)m->ev_n[i]);
  putchar('\n');
}
static void eval_stream(const BPC *m,int steps,uint64_t seed,int action_blind,Metrics *met){
  memset(met,0,sizeof(*met)); RNG r={seed?seed:1}; Game g; game_init(&g,rng_i(&r,7)); Pilot p={0};
  uint8_t a[FRAME_BITS],b[FRAME_BITS]; float pred[FRAME_BITS];
  for(int i=0;i<steps;i++){ if(g.game_over){ game_init(&g,rng_i(&r,7)); memset(&p,0,sizeof(p)); } render_bits(&g,a); int act=pilot_action(&g,&p,&r,1); int ev=game_step(&g,act); render_bits(&g,b); bpc_predict(m,a,action_blind?ACT_NONE:act,pred); metrics_add(met,a,b,pred,ev); }
}
static void rollout_eval(const BPC *m,uint64_t seed){
  RNG r={seed}; double acc[ROLLOUT_HORIZON+1]={0}; int cnt[ROLLOUT_HORIZON+1]={0}, ex[ROLLOUT_HORIZON+1]={0};
  for(int w=0;w<ROLLOUT_WINDOWS;w++){
    Game g; game_init(&g,rng_i(&r,7)); Pilot p={0}; int warm=20+rng_i(&r,60);
    for(int i=0;i<warm && !g.game_over;i++){ int a=pilot_action(&g,&p,&r,1); game_step(&g,a); }
    if(g.game_over){w--;continue;}
    uint8_t pf[FRAME_BITS], tf[FRAME_BITS]; render_bits(&g,pf); Game gt=g; Pilot pt=p;
    for(int h=1;h<=ROLLOUT_HORIZON;h++){
      int act=pilot_action(&gt,&pt,&r,1); game_step(&gt,act); render_bits(&gt,tf); float pp[FRAME_BITS]; bpc_predict(m,pf,act,pp);
      int ok=0; for(int j=0;j<FRAME_BITS;j++){ pf[j]=(uint8_t)(pp[j]>=0.5f); ok+=(pf[j]==tf[j]); }
      acc[h]+=(double)ok/FRAME_BITS; cnt[h]++; ex[h]+=(ok==FRAME_BITS); if(gt.game_over) break;
    }
  }
  printf("[rollout] autonomous predicted-frame re-entry:"); int hs[]={1,2,5,10,20};
  for(size_t i=0;i<sizeof(hs)/sizeof(hs[0]);i++){int h=hs[i]; if(cnt[h]) printf(" h%d=%.2f%%/exact%.2f%%",h,100.0*acc[h]/cnt[h],100.0*ex[h]/cnt[h]);}
  putchar('\n');
}
static int save_model(const BPC *m,const char *fn){
  FILE *f=fopen(fn,"wb"); if(!f)return 0; uint32_t magic=0x42505454u, ver=1; fwrite(&magic,4,1,f); fwrite(&ver,4,1,f);
  fwrite(m->gprobe,sizeof(m->gprobe),1,f); fwrite(m->ldx,sizeof(m->ldx),1,f); fwrite(m->ldy,sizeof(m->ldy),1,f); fwrite(m->lplane,sizeof(m->lplane),1,f);
  fwrite(m->gw,sizeof(float),(size_t)G_BRANCHES*G_BUCKETS*FRAME_BITS,f); fwrite(m->lw,sizeof(float),(size_t)L_BRANCHES*L_BUCKETS*2,f); fclose(f); return 1;
}
static void run_experiment(int train_steps){
  BPC m; bpc_init(&m,0xB0C12345u); RNG r={0x123456789abcdefULL}; Game g; game_init(&g,rng_i(&r,7)); Pilot pilot={0};
  uint8_t f0[FRAME_BITS],f1[FRAME_BITS]; int checkpoints[]={0,1000,3000,10000,30000,60000}; int nc=(int)(sizeof(checkpoints)/sizeof(checkpoints[0])),ci=0;
  printf("BPC-Tetris v0.4.1 frame_bits=%d train_steps=%d\n",FRAME_BITS,train_steps);
  while(ci<nc && checkpoints[ci]==0){ Metrics mm; eval_stream(&m,2500,0xA11CEULL,0,&mm); print_metrics("holdout@0",&mm); ci++; }
  double train_mse=0; uint64_t events[6]={0}; int flags[6]={EV_MOVE,EV_ROT,EV_DROP,EV_LOCK,EV_CLEAR,EV_GAMEOVER};
  for(int t=1;t<=train_steps;t++){
    if(g.game_over){ game_init(&g,rng_i(&r,7)); memset(&pilot,0,sizeof(pilot)); }
    render_bits(&g,f0); int a=pilot_action(&g,&pilot,&r,1); int ev=game_step(&g,a); render_bits(&g,f1); train_mse+=bpc_train(&m,f0,a,f1);
    for(int i=0;i<6;i++) if(ev&flags[i]) events[i]++;
    if(t%5000==0){ printf("[train] step=%d avg_mse=%.5f lines=%d pieces=%d clears=%llu\n",t,train_mse/5000.0,g.lines,g.pieces,(unsigned long long)events[4]); train_mse=0; }
    while(ci<nc && t>=checkpoints[ci] && checkpoints[ci]<=train_steps){ char tag[64]; Metrics mm; eval_stream(&m,2500,0xA11CEULL,0,&mm); snprintf(tag,sizeof(tag),"holdout@%d",checkpoints[ci]); print_metrics(tag,&mm); ci++; }
  }
  Metrics good,blind; eval_stream(&m,EVAL_STEPS,0xDEADBEEF123ULL,0,&good); eval_stream(&m,EVAL_STEPS,0xDEADBEEF123ULL,1,&blind);
  print_metrics("final-holdout",&good); print_metrics("action-blind-ablation",&blind); rollout_eval(&m,0xF00DBAADULL);
  printf("[train-events] move=%llu rot=%llu drop=%llu lock=%llu clear=%llu gameover=%llu\n",(unsigned long long)events[0],(unsigned long long)events[1],(unsigned long long)events[2],(unsigned long long)events[3],(unsigned long long)events[4],(unsigned long long)events[5]);
  if(save_model(&m,"bpc_tetris_model.bin")) puts("saved bpc_tetris_model.bin"); bpc_free(&m);
}
static void play(void){
  Game g; game_init(&g,0); char line[64];
  while(1){ print_game(&g); if(g.game_over){ puts("r=restart q=quit"); } if(!fgets(line,sizeof(line),stdin)) break; char c=line[0]; if(c=='q')break; if(g.game_over){ if(c=='r') game_init(&g,0); continue; } int a=ACT_NONE; if(c=='a')a=ACT_LEFT; else if(c=='d')a=ACT_RIGHT; else if(c=='w')a=ACT_ROT; else if(c=='x'||c==' ')a=ACT_DROP; game_step(&g,a); }
}
int main(int argc,char **argv){ if(argc>1 && !strcmp(argv[1],"--play")){ play(); return 0; } int n=TRAIN_STEPS; if(argc>2 && !strcmp(argv[1],"--train")) n=atoi(argv[2]); if(n<1) n=1; run_experiment(n); return 0; }
