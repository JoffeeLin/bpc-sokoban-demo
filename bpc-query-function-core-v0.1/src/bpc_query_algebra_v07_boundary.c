#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

enum { NOFF=7, NCUR=4, NTOK=21, ACTIVE=5, MAX_NODE=512, MAX_FOCUS=256, MAX_DEPTH=10 };
static const int OFFS[NOFF]={-3,-2,-1,0,1,2,3};

typedef struct{uint64_t s;}RNG;
static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return(uint32_t)((r->s*2685821657736338717ULL)>>32);}
static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}
static int oi(int off){for(int i=0;i<NOFF;i++)if(OFFS[i]==off)return i;return-1;}
static void sm(const float z[NOFF],float p[NOFF]){float mx=z[0];for(int i=1;i<NOFF;i++)if(z[i]>mx)mx=z[i];double s=0;for(int i=0;i<NOFF;i++){p[i]=expf(z[i]-mx);s+=p[i];}for(int i=0;i<NOFF;i++)p[i]=(float)(p[i]/s);}
static float loss7(const float p[NOFF],int y){return-logf(fmaxf(p[y],1e-12f));}
static int am(const float p[NOFF]){int b=0;for(int i=1;i<NOFF;i++)if(p[i]>p[b])b=i;return b;}
static float clamp01(float x){return x<0?0:(x>1?1:x);}
static int pc32(uint32_t x){int n=0;while(x){x&=x-1;n++;}return n;}
static float normv(const float x[NOFF]){double s=0;for(int i=0;i<NOFF;i++)s+=(double)x[i]*x[i];return(float)sqrt(s);}

/* token layout: current 0..3, previous-current 4..8 (8=start), previous-output 9..16 (16=start), nuisance one-hot 17..20 */
typedef struct{uint32_t mask;int tok[ACTIVE];}Trace;
static int outtok(int prev_y){return prev_y==99?16:9+oi(prev_y);}
static void trace_make(int cur,int prev_cur,int prev_y,int n1,int n2,Trace*t){
    int pcur=prev_cur<0?8:4+prev_cur;
    int po=outtok(prev_y);
    int v[ACTIVE]={cur,pcur,po,17+n1,19+n2};
    t->mask=0;for(int i=0;i<ACTIVE;i++){t->tok[i]=v[i];t->mask|=(uint32_t)(1u<<v[i]);}
}

typedef struct{uint8_t used,depth;uint32_t mask;float dir[NOFF],utility,strength;unsigned evals,born;}Node;
typedef struct{uint8_t used;uint32_t parent_mask;float parent_mean[NOFF];unsigned parent_seen;float cond_mean[NTOK][NOFF];unsigned cond_seen[NTOK];float mass[NTOK];}Focus;
typedef struct{float coarse[NCUR][NOFF];Node n[MAX_NODE];Focus f[MAX_FOCUS];unsigned step,births,deaths;}Model;
typedef struct{float uema,uscale,probe,trlr,focus_ema,grow_quantum,mass_decay,birth_quantum,stable_tau;}H;
typedef enum{NORMAL=0,CARRIER_OFF=1,FOCUS_OFF=2,TRACE_OFF=3}Mode;

static int findn(const Model*m,uint32_t mask){for(int i=0;i<MAX_NODE;i++)if(m->n[i].used&&m->n[i].mask==mask)return i;return-1;}
static int allocn(Model*m,uint32_t mask,const float d[NOFF]){int q=findn(m,mask);if(q>=0)return q;int s=-1;for(int i=0;i<MAX_NODE;i++)if(!m->n[i].used){s=i;break;}if(s<0)return-1;Node*n=&m->n[s];memset(n,0,sizeof(*n));n->used=1;n->mask=mask;n->depth=(uint8_t)pc32(mask);n->born=m->step;for(int o=0;o<NOFF;o++)n->dir[o]=.04f*d[o];m->births++;return s;}
static int focus_find(Model*m,uint32_t pm){for(int i=0;i<MAX_FOCUS;i++)if(m->f[i].used&&m->f[i].parent_mask==pm)return i;for(int i=0;i<MAX_FOCUS;i++)if(!m->f[i].used){memset(&m->f[i],0,sizeof(Focus));m->f[i].used=1;m->f[i].parent_mask=pm;return i;}return-1;}
static void effect(const Model*m,const Trace*t,int rem,int add,float amp,float out[NOFF]){for(int o=0;o<NOFF;o++)out[o]=0;for(int d=2;d<=MAX_DEPTH;d++){float sw=0,tmp[NOFF]={0};for(int i=0;i<MAX_NODE;i++){const Node*n=&m->n[i];if(!n->used||n->depth!=d||(n->mask&t->mask)!=n->mask)continue;float w=n->strength;if(i==rem)w=0;if(i==add)w+=amp;if(w<=0)continue;sw+=w;for(int o=0;o<NOFF;o++)tmp[o]+=w*n->dir[o];}float den=sw>1?sw:1;for(int o=0;o<NOFF;o++)out[o]+=tmp[o]/den;}}
static void logits(const Model*m,int cur,const Trace*t,int rem,int add,float amp,float z[NOFF]){float e[NOFF];effect(m,t,rem,add,amp,e);for(int o=0;o<NOFF;o++)z[o]=m->coarse[cur][o]+e[o];}
static void pred(const Model*m,int cur,const Trace*t,float p[NOFF]){float z[NOFF];logits(m,cur,t,-1,-1,0,z);sm(z,p);}
static void ema_vec(float dst[NOFF],const float src[NOFF],float a){for(int o=0;o<NOFF;o++)dst[o]=(1-a)*dst[o]+a*src[o];}
static int parents(const Model*m,const Trace*t,uint32_t out[MAX_NODE+1]){int n=0;out[n++]=(uint32_t)(1u<<t->tok[0]);for(int i=0;i<MAX_NODE;i++)if(m->n[i].used&&m->n[i].strength>.02f&&(m->n[i].mask&t->mask)==m->n[i].mask)out[n++]=m->n[i].mask;return n;}

static void focus_update(Model*m,const Trace*t,const float residual[NOFF],int wrong,const H*h,Mode mode){
    uint32_t pp[MAX_NODE+1];int np=parents(m,t,pp);
    for(int k=0;k<np;k++){int fi=focus_find(m,pp[k]);if(fi<0)continue;Focus*f=&m->f[fi];ema_vec(f->parent_mean,residual,h->focus_ema);f->parent_seen++;for(int q=0;q<ACTIVE;q++){int tok=t->tok[q];uint32_t bit=(uint32_t)(1u<<tok);if(pp[k]&bit)continue;ema_vec(f->cond_mean[tok],residual,h->focus_ema);f->cond_seen[tok]++;}}
    if(!wrong){for(int k=0;k<np;k++){int fi=focus_find(m,pp[k]);if(fi<0)continue;Focus*f=&m->f[fi];for(int q=0;q<ACTIVE;q++){int tok=t->tok[q];uint32_t bit=(uint32_t)(1u<<tok);if(pp[k]&bit)continue;f->mass[tok]*=h->mass_decay;}}return;}
    typedef struct{int fi,tok;float score;}Cand;Cand c[MAX_FOCUS*ACTIVE];int nc=0;float sum=0;
    for(int k=0;k<np;k++){uint32_t pm=pp[k];int fi=focus_find(m,pm);if(fi<0)continue;Focus*f=&m->f[fi];if(f->parent_seen<12)continue;for(int q=0;q<ACTIVE;q++){int tok=t->tok[q];uint32_t bit=(uint32_t)(1u<<tok);if(pm&bit||f->cond_seen[tok]<6)continue;uint32_t child=pm|bit;if(findn(m,child)>=0)continue;float dv[NOFF];for(int o=0;o<NOFF;o++)dv[o]=f->cond_mean[tok][o]-f->parent_mean[o];float sc=mode==FOCUS_OFF?1.f:normv(dv);if(sc<=1e-7f)continue;c[nc++]=(Cand){fi,tok,sc};sum+=sc;}}
    if(nc==0||sum<=0){ return; }
    for(int j=0;j<nc;j++){ Focus*f=&m->f[c[j].fi]; f->mass[c[j].tok]+=h->grow_quantum*(c[j].score/sum); }
    for(int k=0;k<np;k++){uint32_t pm=pp[k];int fi=focus_find(m,pm);if(fi<0)continue;Focus*f=&m->f[fi];for(int q=0;q<ACTIVE;q++){int tok=t->tok[q];uint32_t bit=(uint32_t)(1u<<tok);if(pm&bit)continue;if(f->mass[tok]<h->birth_quantum)continue;uint32_t child=pm|bit;if(allocn(m,child,residual)>=0)f->mass[tok]=0;}}
}

static void learn_step(Model*m,int cur,const Trace*t,int target,const H*h,Mode mode){
    m->step++;int y=oi(target);float z[NOFF],p[NOFF];logits(m,cur,t,-1,-1,0,z);sm(z,p);float lf=loss7(p,y);
    int ids[MAX_NODE],nn=0;for(int i=0;i<MAX_NODE;i++)if(m->n[i].used&&(m->n[i].mask&t->mask)==m->n[i].mask)ids[nn++]=i;
    for(int k=0;k<nn;k++){int i=ids[k];Node*n=&m->n[i];float zz[NOFF],pp[NOFF];if(n->strength>.02f)logits(m,cur,t,i,-1,0,zz);else logits(m,cur,t,-1,i,h->probe,zz);sm(zz,pp);float g;if(am(p)!=y)g=(n->strength>.02f)?loss7(pp,y)-lf:lf-loss7(pp,y);else g=(n->strength>.02f&&am(pp)!=y)?1.f:0.f;n->evals++;n->utility=(1-h->uema)*n->utility+h->uema*g;n->strength=clamp01(h->uscale*fmaxf(0,n->utility));}
    float z1[NOFF],p1[NOFF];logits(m,cur,t,-1,-1,0,z1);sm(z1,p1);float ef[NOFF];for(int o=0;o<NOFF;o++)ef[o]=(o==y)-p1[o];
    if(mode!=TRACE_OFF){float sw=0;int leaf[MAX_NODE];memset(leaf,0,sizeof(leaf));for(int k=0;k<nn;k++){int i=ids[k];Node*n=&m->n[i];if(n->strength<=0)continue;int shadow=0;for(int j=0;j<nn;j++){if(j==k)continue;Node*d=&m->n[ids[j]];if(d->strength<=.02f||d->depth<=n->depth)continue;if((d->mask&n->mask)==n->mask){shadow=1;break;}}if(!shadow){leaf[i]=1;sw+=n->strength;}}if(sw>0){for(int k=0;k<nn;k++){int i=ids[k];Node*n=&m->n[i];if(!leaf[i])continue;float sh=n->strength/sw;float pl=1.0f/sqrtf(1.0f+(float)n->evals/h->stable_tau);for(int o=0;o<NOFF;o++)n->dir[o]+=h->trlr*sh*pl*ef[o];}}}
    focus_update(m,t,ef,am(p1)!=y,h,mode);
    for(int i=0;i<MAX_NODE;i++){Node*n=&m->n[i];if(!n->used||(n->mask&t->mask)!=n->mask)continue;if(n->evals>100&&n->strength<.001f&&n->utility<=0&&m->step-n->born>200){memset(n,0,sizeof(*n));m->deaths++;}}
}

static int base_target(int cur){static const int B[NCUR]={1,-1,0,2};return B[cur];}
static void train_base(Model*m,int seed){RNG r={0x61000u+(uint64_t)seed*1009u};int prev=-1,py=99;for(int s=0;s<10000;s++){int cur=ri(&r,NCUR),n1=ri(&r,2),n2=ri(&r,2);Trace t;trace_make(cur,prev,py,n1,n2,&t);float p[NOFF];pred(m,cur,&t,p);int y=oi(base_target(cur));for(int o=0;o<NOFF;o++)m->coarse[cur][o]+=.30f*((o==y)-p[o]);prev=cur;py=base_target(cur);}}


enum{W_CONJ=0,W_ORDER=1,W_CYCLE=2,W_RING=3,W_ORDER3=4,W_HCYCLE=5};
static int world_target(int w,int cur,int prev,int pprev,int py,int n1,int n2,int step){
    (void)n2;
    if(w==W_CONJ){ if(cur==0&&n1==1)return 3; return base_target(cur); }
    if(w==W_ORDER){ if(prev==1&&cur==0)return 3; if(prev==0&&cur==1)return-3; return base_target(cur); }
    if(w==W_CYCLE){ if(cur!=2)return base_target(cur); if(py==99)return 0; if(py==-1)return 0; if(py==0)return 1; if(py==1)return-1; return 0; }
    if(w==W_ORDER3){ if(pprev==0&&prev==1&&cur==0)return 3; if(pprev==1&&prev==0&&cur==1)return-3; return base_target(cur); }
    if(w==W_HCYCLE){ (void)prev;(void)pprev;(void)py;(void)n1; return (step%3)==2?1:0; }
    if(cur>1)return base_target(cur);
    int ss=(py==99?0:py);int q=ss+(cur==0?1:-1);if(q>2)q=-2;if(q<-2)q=2;return q;
}

typedef struct{double acc,off,prev_off,out_off;int K;unsigned births,deaths;}Res;
static int K(const Model*m){int k=0;for(int i=0;i<MAX_NODE;i++)if(m->n[i].used&&m->n[i].strength>=.05f)k++;return k;}
static double eval_stream(const Model*m,int w,int seed,int N,int ablate){
    RNG r={0xD0000u+(uint64_t)w*7919u+(uint64_t)seed*313u};int pprev=-1,prev=-1,py=99,ok=0;
    for(int st=0;st<N;st++){
        int cur;
        if(w==W_CYCLE||w==W_HCYCLE)cur=2;
        else if(w==W_RING)cur=ri(&r,2);
        else if(w==W_ORDER3)cur=ri(&r,2);
        else cur=ri(&r,NCUR);
        int n1=ri(&r,2),n2=ri(&r,2);int qp=prev,qy=py;
        if(ablate==1||ablate==2)qp=-1;
        if(ablate==1||ablate==3)qy=99;
        Trace t;trace_make(cur,qp,qy,n1,n2,&t);float p[NOFF];pred(m,cur,&t,p);
        int y=world_target(w,cur,prev,pprev,py,n1,n2,st);ok+=OFFS[am(p)]==y;
        pprev=prev;prev=cur;py=y;
    }
    return 100.0*ok/N;
}
static Res run_world(int w,int seed,Mode mode,int steps,const H*h){
    Model m={0};train_base(&m,seed);RNG r={0xA0000u+(uint64_t)w*12347u+(uint64_t)seed*733u};int pprev=-1,prev=-1,py=99;
    for(int st=0;st<steps;st++){
        int cur;
        if(w==W_CYCLE||w==W_HCYCLE)cur=2;
        else if(w==W_RING)cur=ri(&r,2);
        else if(w==W_ORDER3)cur=ri(&r,2);
        else cur=ri(&r,NCUR);
        int n1=ri(&r,2),n2=ri(&r,2);Trace t;trace_make(cur,prev,py,n1,n2,&t);
        int y=world_target(w,cur,prev,pprev,py,n1,n2,st);learn_step(&m,cur,&t,y,h,mode);
        pprev=prev;prev=cur;py=y;
    }
    Res z={eval_stream(&m,w,seed,12000,0),eval_stream(&m,w,seed,12000,1),eval_stream(&m,w,seed,12000,2),eval_stream(&m,w,seed,12000,3),K(&m),m.births,m.deaths};return z;
}
int main(int argc,char**argv){
    int seeds=argc>1?atoi(argv[1]):5;
    H h={.uema=.05f,.uscale=30,.probe=.10f,.trlr=.35f,.focus_ema=.03f,.grow_quantum=.10f,.mass_decay=.985f,.birth_quantum=.80f,.stable_tau=50.f};
    const char*wn[6]={"conjunction","order2","visible-cycle","reversible-ring","order3-hidden","hidden-cycle3"};
    for(int w=0;w<6;w++){
        printf("WORLD %s\n",wn[w]);
        for(int sd=0;sd<seeds;sd++){
            int st=(w==W_CONJ?7000:(w==W_ORDER?12000:(w==W_CYCLE?10000:20000)));
            Res r=run_world(w,sd,NORMAL,st,&h);
            printf("seed=%d acc=%.3f bothOff=%.3f prevOff=%.3f outOff=%.3f K=%d births=%u deaths=%u\n",sd,r.acc,r.off,r.prev_off,r.out_off,r.K,r.births,r.deaths);
        }
        puts("");
    }
    return 0;
}