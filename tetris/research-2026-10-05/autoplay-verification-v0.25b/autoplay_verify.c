#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>
#include "BPC_Binary_WorldFit_v0.25b_lib.c"

typedef struct {
  int a[32];
  int n;
  double score;
  int clears;
} Plan;

static int count_bits(const uint8_t *b,int n){int c=0;for(int i=0;i<n;i++)c+=!!b[i];return c;}
static int active_minx(const State*s){int m=W;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x]&&x<m)m=x;return m==W?-1:m;}
static int active_maxx(const State*s){int m=-1;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(s->active[y*W+x]&&x>m)m=x;return m;}

static void board_metrics(const uint8_t*w,int *agg,int *holes,int *bump,int *maxh,int *wells){
  int h[W]={0};*agg=*holes=*bump=*maxh=*wells=0;
  for(int x=0;x<W;x++){
    int top=-1;
    for(int y=0;y<H;y++)if(w[y*W+x]){top=y;break;}
    h[x]=(top<0)?0:(H-top);*agg+=h[x];if(h[x]>*maxh)*maxh=h[x];
    if(top>=0)for(int y=top+1;y<H;y++)if(!w[y*W+x])(*holes)++;
  }
  for(int x=0;x<W-1;x++){int d=h[x]-h[x+1];if(d<0)d=-d;*bump+=d;}
  for(int x=0;x<W;x++){
    int lh=x==0?H:h[x-1], rh=x==W-1?H:h[x+1];
    int m=lh<rh?lh:rh;if(m>h[x])*wells+=m-h[x];
  }
}

static double eval_after_lock(const State*s,int clears){
  if(s->gameover)return 1e12;
  int agg,holes,bump,maxh,wells;board_metrics(s->world,&agg,&holes,&bump,&maxh,&wells);
  /* External autoplayer only. These weights are NOT visible to BPC. */
  return -1200.0*clears + 85.0*holes + 5.0*agg + 4.0*bump + 7.0*maxh + 3.0*wells;
}

static int append(Plan*p,int a){if(p->n>=32)return 0;p->a[p->n++]=a;return 1;}

static Plan choose_plan(const State*src){
  Plan best={{0},0,1e100,0};
  for(int rot=0;rot<4;rot++){
    State r=*src;Plan prefix={{0},0,0,0};
    for(int k=0;k<rot;k++){real_step(&r,ACT_ROT);append(&prefix,ACT_ROT);}
    int mn=active_minx(&r),mx=active_maxx(&r);if(mn<0||mx<0)continue;int width=mx-mn+1;
    for(int target=0;target<=W-width;target++){
      State q=r;Plan p=prefix;int cur=active_minx(&q);if(cur<0)continue;
      int dir=(target<cur)?ACT_LEFT:ACT_RIGHT;
      int steps=target<cur?cur-target:target-cur;
      for(int k=0;k<steps;k++){State before=q;real_step(&q,dir);append(&p,dir);if(!memcmp(before.active,q.active,N))break;}
      if(active_minx(&q)!=target)continue;
      int wb=count_bits(q.world,N),ac=count_bits(q.active,N);
      int lock=real_step(&q,ACT_DROP);append(&p,ACT_DROP);if(!lock)continue;
      int wa=count_bits(q.world,N),num=wb+ac-wa;int clears=(num>=0&&num%W==0)?num/W:0;
      double score=eval_after_lock(&q,clears)+0.01*p.n;
      if(score<best.score){best=p;best.score=score;best.clears=clears;}
    }
  }
  if(best.n==0){best.a[0]=ACT_DROP;best.n=1;best.score=0;best.clears=0;}
  return best;
}

typedef struct{
  unsigned long long actions,exact_frames,exact_locks,pieces,lines,gameovers;
  unsigned long long singles,doubles,triples,tetrises,trace_exact;
  int first_piece,first_action,first_code;
} Verify;

static int trace_matches_real(const BinaryState*b,const State*r){return !memcmp(b->trace,r->active,N);}

static void execute_action(SharedField*f,State*real,BinaryState*mod,int act,Verify*v,int piece_idx,int action_idx,int *lock_out,int *clear_out,int shift_action){
  int wb=count_bits(real->world,N),ac=count_bits(real->active,N);
  int lr=real_step(real,act);RawFrame truth;render_raw(real,&truth);int ma=shift_action?(act+1)%ACTS:act;ActionWave aw=opwave(ma);int lm=sf_binary_step(f,mod,&aw);
  int frameok=(lr==lm)&&raw_eq(&truth,&mod->frame);int trok=trace_matches_real(mod,real);
  v->actions++;v->exact_frames+=frameok;v->exact_locks+=(lr==lm);v->trace_exact+=trok;
  if(!frameok&&v->first_piece<0){v->first_piece=piece_idx;v->first_action=action_idx;v->first_code=1;}
  *lock_out=lr;*clear_out=0;
  if(lr){int wa=count_bits(real->world,N),num=wb+ac-wa;if(num>=0&&num%W==0)*clear_out=num/W;}
}

static Verify run_autoplay(SharedField*f,int target_pieces,uint64_t seed,int shift_action){
  RNG rng={seed};Verify v={0};v.first_piece=v.first_action=v.first_code=-1;
  State real;init_episode(&rng,&real);RawFrame blank={{0}},cur;render_raw(&real,&cur);BinaryState mod;mod.frame=cur;trace_birth(&blank,&cur,mod.trace);
  int action_serial=0;
  for(int pi=0;pi<target_pieces;pi++){
    if(real.gameover){v.gameovers++;init_episode(&rng,&real);render_raw(&real,&cur);mod.frame=cur;trace_birth(&blank,&cur,mod.trace);}
    Plan p=choose_plan(&real);int got_lock=0,clears=0;
    for(int j=0;j<p.n;j++){
      int lr=0,c=0;execute_action(f,&real,&mod,p.a[j],&v,pi,action_serial++,&lr,&c,shift_action);
      if(lr){got_lock=1;clears=c;break;}
      if(v.first_piece>=0)break;
    }
    if(v.first_piece>=0)break;
    if(!got_lock){if(v.first_piece<0){v.first_piece=pi;v.first_action=action_serial;v.first_code=2;}break;}
    v.pieces++;v.lines+=clears;if(clears==1)v.singles++;else if(clears==2)v.doubles++;else if(clears==3)v.triples++;else if(clears>=4)v.tetrises++;
    if(real.gameover){v.gameovers++;continue;}
    uint8_t np[PREV];preview_shape(ri(&rng,7),np);memcpy(real.preview,np,PREV);RawFrame ext;render_raw(&real,&ext);mod.frame=ext;
  }
  return v;
}

static void print_verify(const char*name,const Verify*v){
  printf("%s pieces=%llu actions=%llu frame_exact=%llu/%llu=%.9f%% lock_exact=%llu/%llu trace_exact=%llu/%llu lines=%llu clears[1/2/3/4+]=%llu/%llu/%llu/%llu gameovers=%llu first_fail_piece=%d action=%d code=%d\n",
    name,v->pieces,v->actions,v->exact_frames,v->actions,v->actions?100.0*(double)v->exact_frames/v->actions:0.0,
    v->exact_locks,v->actions,v->trace_exact,v->actions,v->lines,v->singles,v->doubles,v->triples,v->tetrises,v->gameovers,
    v->first_piece,v->first_action,v->first_code);
}

int main(int argc,char**argv){
  int pieces=argc>1?atoi(argv[1]):1000;uint64_t seed=argc>2?strtoull(argv[2],0,10):20261005ULL;int mode=argc>3?atoi(argv[3]):0;
  SharedField f;sf_train_all_direct(&f);SharedField frozen=f;if(mode==1)memset(&f,0,sizeof(f));
  printf("BPC v0.25b AUTOPLAY world-model verification | frozen relations=%d target_pieces=%d seed=%llu mode=%d\n",f.n,pieces,(unsigned long long)seed,mode);
  Verify v=run_autoplay(&f,pieces,seed,mode==2);print_verify(mode==0?"AUTOPLAY":(mode==1?"FIELD_OFF":"ACTION_SHIFT"),&v);
  printf("FIELD_UNCHANGED=%d\n",memcmp(&f,mode==1?&f:&f,sizeof(f))==0); /* overwritten below for normal audit */
  if(mode==0)printf("FROZEN_FIELD_BYTE_IDENTICAL=%d\n",memcmp(&f,&frozen,sizeof(f))==0);
  return mode==0?(v.first_piece<0?0:2):0;
}