/* Post-failure diagnostics, not a tuning loop. Count raw changed/unchanged
   bit errors with actual history. MODE 2 also reverses residual phase and
   rotates residuals across physical addresses; each frozen test uses one field. */
#define main archived_main
#include "audit.c"
#undef main
static void rotate_residuals(Field*f,int reverse){
 double carry=0;size_t end=0;int seen=0;
 for(size_t k=0;k<f->capacity;k++){
  size_t i=reverse?f->capacity-1-k:k;if(!f->table[i].total)continue;
  double value=f->table[i].residual;
  if(seen)f->table[i].residual=carry;else{end=i;seen=1;}
  carry=value;
 }
 if(seen)f->table[end].residual=carry;
}
static void causal_test(Field*f,int memory,const char*label){
 uint64_t h=field_bytes_digest(f);
 Stats z=random_games(f,memory,100,120,20261131ULL,0,0);
 stats_print(&z,label,memory,20261131ULL,0);
 require(h==field_bytes_digest(f),"causal field changed during test");
}
int main(int argc,char**argv){
 require(argc==2,"diagnose FIELD");Field f;int memory;field_load(&f,argv[1],&memory);
 uint64_t clean=field_bytes_digest(&f);RNG rng={4898837ULL};
 unsigned long long n[5]={0},ok[5]={0},changed[5]={0},wrong_changed[5]={0},wrong_still[5]={0};
 for(int ep=0;ep<100;ep++){
  State s;init_episode(&rng,&s);Raw initial;render(&s,&initial);Medium m;medium_reset(&m,&initial,memory);
  for(int t=0;t<120;t++){
   int u=ri(&rng,100),a=u<18?0:u<36?1:u<50?3:u<70?2:4;
   int lock=real_step(&s,a);Raw truth,pred;render(&s,&truth);field_predict(&f,&m,a,&pred);
   n[a]++;ok[a]+=raw_equal(&truth,&pred);
   for(int i=0;i<RN;i++){
    int different=truth.q[i]!=m.past[0].q[i],wrong=pred.q[i]!=truth.q[i];
    changed[a]+=different;wrong_changed[a]+=different&&wrong;wrong_still[a]+=!different&&wrong;
   }
   medium_accept(&m,a,&truth);if(lock){if(s.gameover)break;refresh(&rng,&s,&m);}
  }
 }
 for(int a=0;a<5;a++)printf("RAW_DIAGNOSTIC mode=%d port=%d frames=%llu/%llu changed=%llu changed_wrong=%llu unchanged_wrong=%llu\n",MODE,a,ok[a],n[a],changed[a],wrong_changed[a],wrong_still[a]);
 require(clean==field_bytes_digest(&f),"diagnostic field changed");
 if(MODE==2){
  causal_test(&f,memory,"RESIDUAL_NORMAL");
  for(size_t i=0;i<f.capacity;i++)f.table[i].residual=-f.table[i].residual;
  causal_test(&f,memory,"RESIDUAL_PHASE_REVERSED");
  for(size_t i=0;i<f.capacity;i++)f.table[i].residual=-f.table[i].residual;
  require(clean==field_bytes_digest(&f),"phase not restored");
  rotate_residuals(&f,0);causal_test(&f,memory,"RESIDUAL_ADDRESSES_ROTATED");rotate_residuals(&f,1);
 }
 printf("DIAGNOSTIC_FIELD_BYTES_RESTORED=%d\n",clean==field_bytes_digest(&f));
 require(clean==field_bytes_digest(&f),"residual addresses not restored");free(f.table);return 0;
}
