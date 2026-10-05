/* This checks a carrier invariant on executed worlds; it teaches no field. */
#define main archived_main
#include "audit.c"
#undef main
static void check(const Medium *m, unsigned long long *bits) {
    for(int i=0;i<RN;i++){
        uint8_t q=0;for(int p=0;p<PORTS;p++)q^=m->memory[p][i];
        require(q==m->past[0].q[i],"port XOR does not reconstruct current");
        (*bits)++;
    }
}
int main(void){
    RNG rng={4899039ULL};unsigned long long bits=0,steps=0,inputs=0;
    for(int ep=0;ep<100;ep++){
        State s;init_episode(&rng,&s);Raw initial;render(&s,&initial);
        Medium m;medium_reset(&m,&initial,1);check(&m,&bits);
        for(int t=0;t<120;t++){
            int u=ri(&rng,100),a=u<18?0:u<36?1:u<50?3:u<70?2:4;
            int lock=real_step(&s,a);Raw truth;render(&s,&truth);
            medium_accept(&m,a,&truth);check(&m,&bits);steps++;
            if(lock){if(s.gameover)break;refresh(&rng,&s,&m);check(&m,&bits);inputs++;}
        }
    }
    printf("PORT_XOR_INVARIANT exact=1 bits=%llu real_steps=%llu external_inputs=%llu episodes=100\n",bits,steps,inputs);
    return 0;
}
