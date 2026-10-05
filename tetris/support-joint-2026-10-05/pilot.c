/* Three identical real training streams per independent readout. Frozen new
   streams are common to all variants; truth-fed accuracy is diagnostic only. */
#define main archived_main
#include "audit.c"
#undef main
int main(void){
 setbuf(stdout,NULL);
 for(int k=0;k<3;k++){
  Field f;field_init(&f,65536);learn(&f,1,2000,55941ULL+(uint64_t)k);pair_fit(&f,1,100);
  uint64_t hash=field_bytes_digest(&f);Stats tf={0},self={0};
  for(int j=0;j<3;j++){
   uint64_t seed=20261111ULL+(uint64_t)j;
   Stats a=random_games(&f,1,100,120,seed,1,0),b=random_games(&f,1,100,120,seed,0,0);
   require(a.real_steps==b.real_steps,"different real trajectories");
   tf.exact+=a.exact;tf.n+=a.n;self.exact+=b.exact;self.n+=b.n;self.failed+=b.failed;self.episodes+=b.episodes;
  }
  printf("RESULT mode=%d seed=%d cells=%zu teacher=%llu/%llu self_prefix=%llu/%llu whole_episodes=%llu/%llu frozen=%d\n",MODE,55941+k,f.used,tf.exact,tf.n,self.exact,self.n,self.episodes-self.failed,self.episodes,hash==field_bytes_digest(&f));
  require(hash==field_bytes_digest(&f),"field changed during test");free(f.table);
 }
 return 0;
}
