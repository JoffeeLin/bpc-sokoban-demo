/* Real experience only. Raw predictions, not delta bits, reenter the medium. */
#define main archived_main
#include "audit.c"
#undef main
static uint64_t prediction_trace(Field *f, uint64_t seed) {
    RNG rng={seed}; uint64_t h=UINT64_C(1469598103934665603);
    for(int ep=0;ep<100;ep++){
        State s;init_episode(&rng,&s);Raw initial;render(&s,&initial);
        Medium m;medium_reset(&m,&initial,1);
        for(int t=0;t<120;t++){
            int u=ri(&rng,100),a=u<18?0:u<36?1:u<50?3:u<70?2:4;
            int lock=real_step(&s,a);Raw truth,pred;render(&s,&truth);
            field_predict(f,&m,a,&pred);
            for(int i=0;i<RN;i++){h^=pred.q[i];h*=UINT64_C(1099511628211);}
            medium_accept(&m,a,&truth);
            if(lock){if(s.gameover)break;refresh(&rng,&s,&m);}
        }
    }
    return h;
}
int main(void){
    setbuf(stdout,NULL);
    for(int k=0;k<3;k++){
        Field f;field_init(&f,65536);learn(&f,1,2000,55971ULL+(uint64_t)k);
        pair_fit(&f,1,100);uint64_t hash=field_bytes_digest(&f),trace=0;
        Stats tf={0},self={0};
        for(int j=0;j<3;j++){
            uint64_t seed=20261171ULL+(uint64_t)j;
            Stats a=random_games(&f,1,100,120,seed,1,0);
            Stats b=random_games(&f,1,100,120,seed,0,0);
            require(a.real_steps==b.real_steps,"different real trajectories");
            trace^=mix64(prediction_trace(&f,seed)+(uint64_t)j);
            tf.exact+=a.exact;tf.n+=a.n;self.exact+=b.exact;self.n+=b.n;
            self.failed+=b.failed;self.episodes+=b.episodes;
        }
        printf("RESULT mode=%d delta=%d bind=%d seed=%d cells=%zu teacher=%llu/%llu self_prefix=%llu/%llu whole_episodes=%llu/%llu trace=%016llx frozen=%d\n",
            MODE,DELTA,BIND_CURRENT,55971+k,f.used,tf.exact,tf.n,self.exact,self.n,
            self.episodes-self.failed,self.episodes,(unsigned long long)trace,
            hash==field_bytes_digest(&f));
        require(hash==field_bytes_digest(&f),"field changed during test");
        free(f.table);
    }
    return 0;
}
