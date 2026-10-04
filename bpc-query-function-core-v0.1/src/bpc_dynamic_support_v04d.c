#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/*
BPC Query-Trace Dynamic Support Topology v0.4d
------------------------------------------------
Goal: remove the globally predeclared pair/triple/quad candidate library.

Raw query traces contain four currently active tokens (one action token,
one context token, and two raw nuisance/value tokens). Fine support topology
starts empty. When the current prediction is physically wrong, support nodes
are born only from traces that actually participated in that query:

  no support -> locally co-active 2-token supports
  active support -> support + another currently active raw trace token

There is no global table enumerating all pairs/triples/quads and no fixed
maximum semantic order. Support identity is simply the set of raw traces that
co-participated. Future consequence utility controls continuous participation;
query error is written only through actually participating supports.
*/

enum { NTOK=8, NOFF=5, ACTIVE_TOK=4, MAX_NODE=256, MAX_DEPTH=8 };
static const int OFFS[NOFF]={-2,-1,0,1,2};
static const char *TN[NTOK]={"A0","A1","C0","C1","N1=0","N1=1","N2=0","N2=1"};

typedef struct { uint64_t s; } RNG;
static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return (uint32_t)((r->s*2685821657736338717ULL)>>32);}
static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}

static int oi(int off){for(int i=0;i<NOFF;i++)if(OFFS[i]==off)return i;return -1;}
static void sm(const float z[NOFF],float p[NOFF]){float mx=z[0];for(int i=1;i<NOFF;i++)if(z[i]>mx)mx=z[i];double s=0;for(int i=0;i<NOFF;i++){p[i]=expf(z[i]-mx);s+=p[i];}for(int i=0;i<NOFF;i++)p[i]=(float)(p[i]/s);}
static float loss5(const float p[NOFF],int y){return -logf(fmaxf(p[y],1e-12f));}
static int am(const float p[NOFF]){int b=0;for(int i=1;i<NOFF;i++)if(p[i]>p[b])b=i;return b;}
static float clamp01(float x){return x<0?0:(x>1?1:x);}
static int pc16(uint16_t x){int n=0;while(x){x&=(uint16_t)(x-1);n++;}return n;}

/* Staged world: each later phase adds one deeper exception. */
static int rule(int phase,int a,int c,int n1,int n2){
    if(a==1) return -1;
    if(phase>=4 && c==1 && n1==1 && n2==1) return 0;
    if(phase>=3 && c==1 && n1==1) return -2;
    if(phase>=2 && c==1) return 2;
    return 1;
}

typedef struct { uint16_t mask; int tok[ACTIVE_TOK]; } Trace;
static void trace_make(int a,int c,int n1,int n2,Trace*t){
    t->tok[0]=a; t->tok[1]=2+c; t->tok[2]=4+n1; t->tok[3]=6+n2;
    t->mask=0; for(int i=0;i<ACTIVE_TOK;i++) t->mask|=(uint16_t)(1u<<t->tok[i]);
}

typedef struct {
    uint8_t used;
    uint16_t mask;
    uint8_t depth;
    float dir[NOFF];
    float utility;
    float strength;
    unsigned evals;
    unsigned reuse;
    unsigned born_step;
} Node;

typedef struct {
    float coarse[2][NOFF];
    Node node[MAX_NODE];
    unsigned step;
    unsigned births;
    unsigned deaths;
} Model;

typedef struct {
    float dir_lr;
    float u_ema;
    float u_scale;
    float probe;
    float trace_lr;
    float death_decay;
    float death_eps;
    unsigned death_min_evals;
} Hyper;

typedef enum { NORMAL=0, UTILITY_OFF=1, UTILITY_SHIFT=2, TRACE_SHIFT=3, TRACE_OFF=4 } Mode;

static int node_find(const Model*m,uint16_t mask){for(int i=0;i<MAX_NODE;i++)if(m->node[i].used&&m->node[i].mask==mask)return i;return -1;}
static int node_alloc(Model*m,uint16_t mask,const float init_dir[NOFF]){
    int old=node_find(m,mask); if(old>=0)return old;
    int slot=-1;
    for(int i=0;i<MAX_NODE;i++) if(!m->node[i].used){slot=i;break;}
    if(slot<0){
        /* Reuse the weakest inactive slot. This is physical capacity competition, not semantic selection. */
        float bs=1e9f;
        for(int i=0;i<MAX_NODE;i++) if(m->node[i].strength<bs){bs=m->node[i].strength;slot=i;}
        if(slot>=0){m->deaths++;memset(&m->node[slot],0,sizeof(Node));}
    }
    if(slot<0)return -1;
    Node*n=&m->node[slot]; memset(n,0,sizeof(*n)); n->used=1;n->mask=mask;n->depth=(uint8_t)pc16(mask);n->born_step=m->step;
    for(int o=0;o<NOFF;o++)n->dir[o]=0.08f*init_dir[o];
    m->births++; return slot;
}

static int active_nodes(const Model*m,const Trace*t,int idx[MAX_NODE]){
    int n=0;for(int i=0;i<MAX_NODE;i++)if(m->node[i].used && (m->node[i].mask&t->mask)==m->node[i].mask)idx[n++]=i;return n;
}

/* One continuous effect pool per self-grown topological depth. Deeper functions
   therefore correct the residual left by shallower functions without a semantic router. */
static void relation_effect(const Model*m,const Trace*t,int remove_i,int add_i,float add_amp,float out[NOFF]){
    for(int o=0;o<NOFF;o++)out[o]=0.f;
    for(int d=2;d<=MAX_DEPTH;d++){
        float sumw=0.f,tmp[NOFF]={0};
        for(int i=0;i<MAX_NODE;i++){
            const Node*n=&m->node[i]; if(!n->used||n->depth!=d||(n->mask&t->mask)!=n->mask)continue;
            float w=n->strength; if(i==remove_i)w=0.f; if(i==add_i)w+=add_amp; if(w<=0)continue;
            sumw+=w; for(int o=0;o<NOFF;o++)tmp[o]+=w*n->dir[o];
        }
        float den=sumw>1.f?sumw:1.f;
        for(int o=0;o<NOFF;o++)out[o]+=tmp[o]/den;
    }
}
static void logits_variant(const Model*m,int a,const Trace*t,int remove_i,int add_i,float add_amp,float z[NOFF]){
    float e[NOFF]; relation_effect(m,t,remove_i,add_i,add_amp,e);for(int o=0;o<NOFF;o++)z[o]=m->coarse[a][o]+e[o];
}
static void predict(const Model*m,int a,const Trace*t,float p[NOFF]){float z[NOFF];logits_variant(m,a,t,-1,-1,0,z);sm(z,p);}

static void train_coarse(Model*m,int seed){
    RNG r={0x10100u+(uint64_t)seed*1009u};
    for(int s=0;s<6000;s++){
        int a=ri(&r,2),c=ri(&r,2),n1=ri(&r,2),n2=ri(&r,2); Trace t;trace_make(a,c,n1,n2,&t);float p[NOFF];predict(m,a,&t,p);int y=oi(rule(1,a,c,n1,n2));
        for(int o=0;o<NOFF;o++)m->coarse[a][o]+=.30f*((o==y)-p[o]);
    }
}

static void maybe_grow(Model*m,const Trace*t,const float residual[NOFF]){
    /* One universal support-growth law:
         current support + one currently participating raw trace -> extended support.
       Raw traces are simply virtual depth-1 supports; learned supports use the exact
       same extension rule. There is no pair/triple/quad-specific branch or table. */
    uint16_t parent[MAX_NODE+ACTIVE_TOK];int np=0;
    for(int q=0;q<ACTIVE_TOK;q++) parent[np++]=(uint16_t)(1u<<t->tok[q]);
    for(int i=0;i<MAX_NODE;i++){
        const Node*n=&m->node[i];
        if(!n->used || n->strength<=1e-6f || (n->mask&t->mask)!=n->mask)continue;
        parent[np++]=n->mask;
    }
    for(int k=0;k<np;k++){
        uint16_t pm=parent[k];
        if(pc16(pm)>=ACTIVE_TOK)continue;
        for(int q=0;q<ACTIVE_TOK;q++){
            uint16_t bit=(uint16_t)(1u<<t->tok[q]);
            if(pm&bit)continue;
            uint16_t child=(uint16_t)(pm|bit);
            node_alloc(m,child,residual);
        }
    }
}

static void lifecycle_decay(Model*m,const Trace*t,const Hyper*h){
    /* Only supports that are actually query-applicable receive zero-utility decay.
       Absent supports are not forgotten merely because their condition is absent. */
    for(int i=0;i<MAX_NODE;i++){
        Node*n=&m->node[i]; if(!n->used || (n->mask&t->mask)!=n->mask)continue;
        if(n->evals>=h->death_min_evals && n->strength<h->death_eps && n->utility<=0.f){
            n->strength*=h->death_decay;
            if(n->strength<1e-6f && m->step-n->born_step>100){memset(n,0,sizeof(*n));m->deaths++;}
        }
    }
}

static void step(Model*m,int phase,int a,int c,int n1,int n2,const Hyper*h,Mode mode){
    m->step++;
    Trace t;trace_make(a,c,n1,n2,&t);int y=oi(rule(phase,a,c,n1,n2));
    float z[NOFF],p[NOFF];logits_variant(m,a,&t,-1,-1,0,z);sm(z,p);float lf=loss5(p,y);

    int ids[MAX_NODE],n=active_nodes(m,&t,ids);float gain[MAX_NODE];memset(gain,0,sizeof(gain));
    for(int k=0;k<n;k++){
        int i=ids[k];Node*nd=&m->node[i];float zv[NOFF],pv[NOFF];
        if(nd->strength>.02f)logits_variant(m,a,&t,i,-1,0,zv);else logits_variant(m,a,&t,-1,i,h->probe,zv);
        sm(zv,pv);
        /* While reality is still wrong, continuous residual improvement can grow a support.
           Once the measured future is already correct, only an irreplaceable support
           (removing it makes the future wrong) keeps positive consequence utility.
           Confidence-only redundancy therefore receives zero utility and decays. */
        if(am(p)!=y){
            gain[i]=(nd->strength>.02f)?loss5(pv,y)-lf:lf-loss5(pv,y);
        }else{
            gain[i]=(nd->strength>.02f && am(pv)!=y)?1.0f:0.0f;
        }
        nd->evals++;nd->reuse++;
    }

    /* Consequence-grounded utility. Wrong-address control rotates utility across the
       actually existing applicable topology; no semantic target is known. */
    for(int k=0;k<n;k++){
        int i=ids[k],src=i;float g=gain[i];
        if(mode==UTILITY_OFF)g=0.f;
        else if(mode==UTILITY_SHIFT && n>1){src=ids[(k+1)%n];g=gain[src];}
        (void)src;
        Node*nd=&m->node[i];nd->utility=(1-h->u_ema)*nd->utility+h->u_ema*g;nd->strength=clamp01(h->u_scale*fmaxf(0.f,nd->utility));
    }

    /* Query-error writeback only through functions that actually participate. */
    float z1[NOFF],p1[NOFF];logits_variant(m,a,&t,-1,-1,0,z1);sm(z1,p1);float ef[NOFF];for(int o=0;o<NOFF;o++)ef[o]=(o==y)-p1[o];
    if(mode!=TRACE_OFF){
        for(int d=2;d<=MAX_DEPTH;d++){
            float sumw=0.f;for(int k=0;k<n;k++){Node*nd=&m->node[ids[k]];if(nd->depth==d)sumw+=nd->strength;}
            if(sumw<=0)continue;
            for(int k=0;k<n;k++){
                int i=ids[k],dst=i;Node*nd=&m->node[i];if(nd->depth!=d||nd->strength<=0)continue;
                if(mode==TRACE_SHIFT && n>1)dst=ids[(k+1)%n];
                Node*wr=&m->node[dst];float share=nd->strength/sumw;
                for(int o=0;o<NOFF;o++)wr->dir[o]+=h->trace_lr*share*ef[o];
            }
        }
    }

    /* Only a real prediction mismatch can open new support topology. New support
       starts weak and must prove future consequence utility before affecting queries. */
    if(am(p1)!=y){
        float z0[NOFF],p0[NOFF],res[NOFF];for(int o=0;o<NOFF;o++)z0[o]=m->coarse[a][o];sm(z0,p0);for(int o=0;o<NOFF;o++)res[o]=(o==y)-p0[o];
        maybe_grow(m,&t,res);
    }
    lifecycle_decay(m,&t,h);
}

typedef struct{unsigned long long n,ok;}Stat;
static void eval(const Model*m,int phase,int seed,int N,Stat s[16]){
    memset(s,0,sizeof(Stat)*16);RNG r={0xD000u+(uint64_t)seed*911u};
    for(int i=0;i<N;i++){
        int a=ri(&r,2),c=ri(&r,2),n1=ri(&r,2),n2=ri(&r,2);Trace t;trace_make(a,c,n1,n2,&t);float p[NOFF];predict(m,a,&t,p);int y=oi(rule(phase,a,c,n1,n2));int ix=(a<<3)|(c<<2)|(n1<<1)|n2;s[ix].n++;s[ix].ok+=am(p)==y;
    }
}
static double allacc(const Stat s[16]){unsigned long long n=0,k=0;for(int i=0;i<16;i++){n+=s[i].n;k+=s[i].ok;}return n?100.0*k/n:0.0;}
static int K(const Model*m,float cut){int k=0;for(int i=0;i<MAX_NODE;i++)if(m->node[i].used&&m->node[i].strength>=cut)k++;return k;}
static int live_nodes(const Model*m){int k=0;for(int i=0;i<MAX_NODE;i++)if(m->node[i].used)k++;return k;}
static void mask_name(uint16_t mask,char *buf,size_t n){buf[0]=0;int first=1;for(int t=0;t<NTOK;t++)if(mask&(1u<<t)){size_t len=strlen(buf);snprintf(buf+len,n-len,"%s%s",first?"":"*",TN[t]);first=0;}}
static void print_top(const Model*m){int ids[MAX_NODE],n=0;for(int i=0;i<MAX_NODE;i++)if(m->node[i].used)ids[n++]=i;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(m->node[ids[j]].strength>m->node[ids[i]].strength){int q=ids[i];ids[i]=ids[j];ids[j]=q;}printf("top:");for(int k=0;k<n&&k<10;k++){Node*nd=(Node*)&m->node[ids[k]];char b[128];mask_name(nd->mask,b,sizeof(b));printf(" (%s d=%u s=%.3f u=%.5f)",b,(unsigned)nd->depth,nd->strength,nd->utility);}puts("");}
static void pe(const char*tag,const Model*m,int phase,int seed){Stat s[16];eval(m,phase,seed,8000,s);printf("%-18s phase=%d acc=%7.3f%% K05=%d K20=%d live=%d births=%u deaths=%u\n",tag,phase,allacc(s),K(m,.05f),K(m,.20f),live_nodes(m),m->births,m->deaths);}

static void train_phase(Model*m,int phase,int steps,int seed,const Hyper*h,Mode mode,int verbose){
    RNG r={0x33000u+(uint64_t)phase*7001u+(uint64_t)seed*1301u};int marks[]={50,100,250,500,1000,2000,4000};int mi=0;
    for(int st=1;st<=steps;st++){
        int a=ri(&r,2),c=ri(&r,2),n1=ri(&r,2),n2=ri(&r,2);step(m,phase,a,c,n1,n2,h,mode);
        if(verbose&&mi<7&&st==marks[mi]){char tag[32];snprintf(tag,sizeof(tag),"p%d@%d",phase,st);pe(tag,m,phase,seed);mi++;}
    }
}

static void run(int seed,Mode mode,const Hyper*h,int verbose){
    Model m={0};train_coarse(&m,seed);
    if(verbose){printf("\n=== seed=%d mode=%d ===\n",seed,(int)mode);pe("base",&m,1,seed);}
    train_phase(&m,2,2500,seed,h,mode,verbose);pe("phase2-final",&m,2,seed);if(verbose)print_top(&m);
    train_phase(&m,3,3500,seed,h,mode,verbose);pe("phase3-final",&m,3,seed);if(verbose)print_top(&m);
    train_phase(&m,4,4500,seed,h,mode,verbose);pe("phase4-final",&m,4,seed);if(verbose)print_top(&m);
    train_phase(&m,1,5000,seed,h,mode,verbose);pe("restore-final",&m,1,seed);if(verbose)print_top(&m);
    printf("SUMMARY seed=%d mode=%d K05=%d K20=%d live=%d births=%u deaths=%u\n",seed,(int)mode,K(&m,.05f),K(&m,.20f),live_nodes(&m),m.births,m.deaths);
}

int main(int argc,char**argv){
    int seeds=argc>1?atoi(argv[1]):5;
    Hyper h={.dir_lr=.05f,.u_ema=.05f,.u_scale=30.f,.probe=.10f,.trace_lr=.35f,.death_decay=.90f,.death_eps=.01f,.death_min_evals=80};
    if(argc>2)h.u_scale=(float)atof(argv[2]);
    if(argc>3)h.trace_lr=(float)atof(argv[3]);
    printf("BPC Query-Trace v0.4d universal support-growth topology | no predeclared pair/triple/quad table | scale=%.2f trace_lr=%.2f\n",h.u_scale,h.trace_lr);
    for(int s=0;s<seeds;s++)run(s,NORMAL,&h,1);
    puts("\n--- controls ---");
    for(int s=0;s<seeds;s++){run(s,UTILITY_OFF,&h,0);run(s,UTILITY_SHIFT,&h,0);run(s,TRACE_SHIFT,&h,0);run(s,TRACE_OFF,&h,0);}
    return 0;
}