#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/*
 BPC Query-Trace v0.5 — Causal Support Focusing
 ------------------------------------------------
 Wide query: 6 simultaneously active raw traces.
 Reality progressively requires 2..6-order conditions.

 No pair/triple/... candidate tables exist.
 New topology can only grow from a function that actually participated in the
 current query. For each participating parent support, the medium accumulates:
   mean unexplained residual when parent participates
   mean unexplained residual when parent + a raw trace participate
 Their contrast is an anonymous local "missing-support" wave.

 A finite growth quantum is shared continuously by all parent/trace extensions
 according to contrast energy. Thus co-occurrence alone cannot create topology.
 Query-error writeback and consequence utility are inherited from v0.4d.
*/

enum { NTOK=12, NOFF=7, ACTIVE_TOK=6, MAX_NODE=512, MAX_DEPTH=12, MAX_FOCUS=128 };
static const int OFFS[NOFF]={-3,-2,-1,0,1,2,3};
static const char *TN[NTOK]={"A0","A1","C0","C1","N1=0","N1=1","N2=0","N2=1","N3=0","N3=1","N4=0","N4=1"};

typedef struct{uint64_t s;}RNG;
static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return(uint32_t)((r->s*2685821657736338717ULL)>>32);}
static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}
static int oi(int off){for(int i=0;i<NOFF;i++)if(OFFS[i]==off)return i;return-1;}
static void sm(const float z[NOFF],float p[NOFF]){float mx=z[0];for(int i=1;i<NOFF;i++)if(z[i]>mx)mx=z[i];double s=0;for(int i=0;i<NOFF;i++){p[i]=expf(z[i]-mx);s+=p[i];}for(int i=0;i<NOFF;i++)p[i]=(float)(p[i]/s);}
static float loss7(const float p[NOFF],int y){return-logf(fmaxf(p[y],1e-12f));}
static int am(const float p[NOFF]){int b=0;for(int i=1;i<NOFF;i++)if(p[i]>p[b])b=i;return b;}
static float clamp01(float x){return x<0?0:(x>1?1:x);}
static int pc16(uint16_t x){int n=0;while(x){x&=(uint16_t)(x-1);n++;}return n;}
static float normv(const float x[NOFF]){double s=0;for(int i=0;i<NOFF;i++)s+=(double)x[i]*x[i];return(float)sqrt(s);}

static int G_ORDER[4]={0,1,2,3};
static int G_REQ[4]={1,1,1,1};
static int G_CREQ=1;
static void schema_set(int seed){
    RNG r={0xA5A50000u+(uint64_t)seed*7919u};
    for(int i=0;i<4;i++){G_ORDER[i]=i;G_REQ[i]=ri(&r,2);}
    G_CREQ=ri(&r,2);
    for(int i=3;i>0;i--){int j=ri(&r,i+1);int q=G_ORDER[i];G_ORDER[i]=G_ORDER[j];G_ORDER[j]=q;}
}
static int rule(int ph,int a,int c,int n1,int n2,int n3,int n4){
    if(a==1)return-1;
    int n[4]={n1,n2,n3,n4};
    if(c!=G_CREQ)return 1;
    int matched=1; /* context condition is level 1 => phase2 target */
    int want=ph-2;if(want<0)want=0;if(want>4)want=4;
    for(int k=0;k<want;k++){if(n[G_ORDER[k]]!=G_REQ[G_ORDER[k]])break;matched++;}
    if(ph<2)return 1;
    if(matched>=5)return -3;
    if(matched==4)return -2;
    if(matched==3)return 0;
    if(matched==2)return 3;
    return 2;
}

typedef struct{uint16_t mask;int tok[ACTIVE_TOK];}Trace;
static void tm(int a,int c,int n1,int n2,int n3,int n4,Trace*t){int v[ACTIVE_TOK]={a,2+c,4+n1,6+n2,8+n3,10+n4};t->mask=0;for(int i=0;i<ACTIVE_TOK;i++){t->tok[i]=v[i];t->mask|=(uint16_t)(1u<<v[i]);}}

typedef struct{
    uint8_t used,depth;
    uint16_t mask;
    float dir[NOFF],utility,strength;
    unsigned evals,born;
}Node;

typedef struct{
    uint8_t used;
    uint16_t parent_mask;
    float parent_mean[NOFF];
    unsigned parent_seen;
    float cond_mean[NTOK][NOFF];
    unsigned cond_seen[NTOK];
    float mass[NTOK];
}Focus;

typedef struct{
    float coarse[2][NOFF];
    Node n[MAX_NODE];
    Focus f[MAX_FOCUS];
    unsigned step,births,deaths;
}Model;

typedef struct{
    float uema,uscale,probe,trlr;
    float focus_ema,grow_quantum,mass_decay,birth_quantum;
}H;

typedef enum{NORMAL=0,FOCUS_OFF=1,FOCUS_SHIFT=2,TRACE_OFF=3}Mode;

static int findn(const Model*m,uint16_t mask){for(int i=0;i<MAX_NODE;i++)if(m->n[i].used&&m->n[i].mask==mask)return i;return-1;}
static int allocn(Model*m,uint16_t mask,const float d[NOFF]){
    int q=findn(m,mask);if(q>=0)return q;
    int slot=-1;for(int i=0;i<MAX_NODE;i++)if(!m->n[i].used){slot=i;break;}
    if(slot<0)return-1;
    Node*n=&m->n[slot];memset(n,0,sizeof(*n));n->used=1;n->mask=mask;n->depth=(uint8_t)pc16(mask);n->born=m->step;
    for(int o=0;o<NOFF;o++)n->dir[o]=.04f*d[o];
    m->births++;return slot;
}
static int focus_find(Model*m,uint16_t parent){for(int i=0;i<MAX_FOCUS;i++)if(m->f[i].used&&m->f[i].parent_mask==parent)return i;for(int i=0;i<MAX_FOCUS;i++)if(!m->f[i].used){memset(&m->f[i],0,sizeof(Focus));m->f[i].used=1;m->f[i].parent_mask=parent;return i;}return-1;}

static void effect(const Model*m,const Trace*t,int rem,int add,float amp,float out[NOFF]){
    for(int o=0;o<NOFF;o++)out[o]=0;
    for(int d=2;d<=MAX_DEPTH;d++){
        float sw=0,tmp[NOFF]={0};
        for(int i=0;i<MAX_NODE;i++){
            const Node*n=&m->n[i];if(!n->used||n->depth!=d||(n->mask&t->mask)!=n->mask)continue;
            float w=n->strength;if(i==rem)w=0;if(i==add)w+=amp;if(w<=0)continue;
            sw+=w;for(int o=0;o<NOFF;o++)tmp[o]+=w*n->dir[o];
        }
        float den=sw>1?sw:1;for(int o=0;o<NOFF;o++)out[o]+=tmp[o]/den;
    }
}
static void logits(const Model*m,int a,const Trace*t,int rem,int add,float amp,float z[NOFF]){float e[NOFF];effect(m,t,rem,add,amp,e);for(int o=0;o<NOFF;o++)z[o]=m->coarse[a][o]+e[o];}
static void pred(const Model*m,int a,const Trace*t,float p[NOFF]){float z[NOFF];logits(m,a,t,-1,-1,0,z);sm(z,p);}
static void coarse(Model*m,int seed){RNG r={0x50100u+(uint64_t)seed*1009u};for(int s=0;s<8000;s++){int a=ri(&r,2),c=ri(&r,2),n1=ri(&r,2),n2=ri(&r,2),n3=ri(&r,2),n4=ri(&r,2);Trace t;tm(a,c,n1,n2,n3,n4,&t);float p[NOFF];pred(m,a,&t,p);int y=oi(rule(1,a,c,n1,n2,n3,n4));for(int o=0;o<NOFF;o++)m->coarse[a][o]+=.3f*((o==y)-p[o]);}}

static void ema_vec(float dst[NOFF],const float src[NOFF],float a){for(int o=0;o<NOFF;o++)dst[o]=(1-a)*dst[o]+a*src[o];}

/* Parents are only functions that actually participated: the coarse action
   function (virtual singleton) and currently effective learned supports. */
static int parents(const Model*m,const Trace*t,uint16_t out[MAX_NODE+1]){
    int n=0;out[n++]=(uint16_t)(1u<<t->tok[0]);
    for(int i=0;i<MAX_NODE;i++)if(m->n[i].used&&m->n[i].strength>.02f&&(m->n[i].mask&t->mask)==m->n[i].mask)out[n++]=m->n[i].mask;
    return n;
}

static void focus_update_and_grow(Model*m,const Trace*t,const float residual[NOFF],int wrong,const H*h,Mode mode){
    uint16_t pp[MAX_NODE+1];int np=parents(m,t,pp);
    /* First update residual statistics for every actually participating parent. */
    for(int k=0;k<np;k++){
        uint16_t pm=pp[k];int fi=focus_find(m,pm);if(fi<0)continue;Focus*f=&m->f[fi];
        ema_vec(f->parent_mean,residual,h->focus_ema);f->parent_seen++;
        for(int q=0;q<ACTIVE_TOK;q++){
            int tok=t->tok[q];uint16_t bit=(uint16_t)(1u<<tok);if(pm&bit)continue;
            ema_vec(f->cond_mean[tok],residual,h->focus_ema);f->cond_seen[tok]++;
        }
    }
    /* A support extension gains birth mass only on unresolved reality. A later
       counterexample under the same parent+trace condition decays that mass.
       Inactive conditions are left untouched; absence is not negative evidence. */
    if(!wrong){
        for(int k=0;k<np;k++){
            uint16_t pm=pp[k];int fi=focus_find(m,pm);if(fi<0)continue;Focus*f=&m->f[fi];
            for(int q=0;q<ACTIVE_TOK;q++){
                int tok=t->tok[q];uint16_t bit=(uint16_t)(1u<<tok);if(pm&bit)continue;
                f->mass[tok]*=h->mass_decay;
            }
        }
        return;
    }

    typedef struct{int fi,tok;float score;}Cand;
    Cand c[MAX_FOCUS*ACTIVE_TOK];int nc=0;float sum=0;
    for(int k=0;k<np;k++){
        uint16_t pm=pp[k];int fi=focus_find(m,pm);if(fi<0)continue;Focus*f=&m->f[fi];
        if(f->parent_seen<12)continue;
        for(int q=0;q<ACTIVE_TOK;q++){
            int tok=t->tok[q];uint16_t bit=(uint16_t)(1u<<tok);if(pm&bit||f->cond_seen[tok]<6)continue;
            uint16_t child=(uint16_t)(pm|bit);if(findn(m,child)>=0)continue;
            float dv[NOFF];for(int o=0;o<NOFF;o++)dv[o]=f->cond_mean[tok][o]-f->parent_mean[o];
            float sc=normv(dv);if(mode==FOCUS_OFF)sc=1.f;
            if(sc<=1e-7f)continue;
            c[nc++]=(Cand){fi,tok,sc};sum+=sc;
        }
    }
    if(nc==0||sum<=0)return;
    /* One conserved topology-growth quantum is shared by all candidate extensions. */
    for(int j=0;j<nc;j++){
        int jj=j;if(mode==FOCUS_SHIFT)jj=(j+1)%nc;
        Focus*f=&m->f[c[j].fi];int tok=c[jj].tok;
        /* wrong-focus control rotates the child address, but keeps the same amount of energy */
        if(mode!=FOCUS_SHIFT)tok=c[j].tok;
        f->mass[tok]+=h->grow_quantum*(c[j].score/sum);
    }
    /* Birth is a binary voxel-existence measurement of accumulated growth mass. */
    for(int k=0;k<np;k++){
        uint16_t pm=pp[k];int fi=focus_find(m,pm);if(fi<0)continue;Focus*f=&m->f[fi];
        for(int q=0;q<ACTIVE_TOK;q++){
            int tok=t->tok[q];uint16_t bit=(uint16_t)(1u<<tok);if(pm&bit)continue;
            if(f->mass[tok]<h->birth_quantum)continue;
            uint16_t child=(uint16_t)(pm|bit);int id=allocn(m,child,residual);if(id>=0)f->mass[tok]=0.f;
        }
    }
}

static void step(Model*m,int ph,int a,int c,int n1,int n2,int n3,int n4,const H*h,Mode mode){
    m->step++;Trace t;tm(a,c,n1,n2,n3,n4,&t);int y=oi(rule(ph,a,c,n1,n2,n3,n4));
    float z[NOFF],p[NOFF];logits(m,a,&t,-1,-1,0,z);sm(z,p);float lf=loss7(p,y);
    int ids[MAX_NODE],nn=0;for(int i=0;i<MAX_NODE;i++)if(m->n[i].used&&(m->n[i].mask&t.mask)==m->n[i].mask)ids[nn++]=i;
    float g[MAX_NODE];memset(g,0,sizeof(g));
    for(int k=0;k<nn;k++){
        int i=ids[k];Node*n=&m->n[i];float zz[NOFF],pp[NOFF];
        if(n->strength>.02f)logits(m,a,&t,i,-1,0,zz);else logits(m,a,&t,-1,i,h->probe,zz);sm(zz,pp);
        if(am(p)!=y)g[i]=(n->strength>.02f)?loss7(pp,y)-lf:lf-loss7(pp,y);else g[i]=(n->strength>.02f&&am(pp)!=y)?1.f:0.f;
        n->evals++;n->utility=(1-h->uema)*n->utility+h->uema*g[i];n->strength=clamp01(h->uscale*fmaxf(0,n->utility));
    }
    float z1[NOFF],p1[NOFF];logits(m,a,&t,-1,-1,0,z1);sm(z1,p1);float ef[NOFF];for(int o=0;o<NOFF;o++)ef[o]=(o==y)-p1[o];
    if(mode!=TRACE_OFF){
        /* Residual reflection follows topology downstream. If an active, more
           specific descendant contains a parent support, that descendant shields
           the parent from the same query error. Multiple incomparable leaves can
           still receive writeback continuously; there is no top-1 route. */
        float sw=0.f;
        int leaf[MAX_NODE];memset(leaf,0,sizeof(leaf));
        for(int k=0;k<nn;k++){
            int i=ids[k];Node*n=&m->n[i];if(n->strength<=0)continue;int shadow=0;
            for(int j=0;j<nn;j++){
                if(j==k) continue;
                Node*d=&m->n[ids[j]];
                if(d->strength<=.02f||d->depth<=n->depth)continue;
                if((d->mask & n->mask)==n->mask){shadow=1;break;}
            }
            if(!shadow){leaf[i]=1;sw+=n->strength;}
        }
        if(sw>0.f){
            for(int k=0;k<nn;k++){
                int i=ids[k];Node*n=&m->n[i];if(!leaf[i])continue;
                float sh=n->strength/sw;
                float plasticity=1.0f/sqrtf(1.0f+(float)n->evals/50.0f);
                for(int o=0;o<NOFF;o++)n->dir[o]+=h->trlr*sh*plasticity*ef[o];
            }
        }
    }
    focus_update_and_grow(m,&t,ef,am(p1)!=y,h,mode);
    for(int i=0;i<MAX_NODE;i++){
        Node*n=&m->n[i];if(!n->used||(n->mask&t.mask)!=n->mask)continue;
        if(n->evals>100&&n->strength<.001f&&n->utility<=0&&m->step-n->born>200){memset(n,0,sizeof(*n));m->deaths++;}
    }
}

typedef struct{unsigned long long n,ok;}Stat;
static double ev(const Model*m,int ph,int seed,int N){RNG r={0x5D000u+(uint64_t)seed*911u};Stat s={0};for(int i=0;i<N;i++){int a=ri(&r,2),c=ri(&r,2),n1=ri(&r,2),n2=ri(&r,2),n3=ri(&r,2),n4=ri(&r,2);Trace t;tm(a,c,n1,n2,n3,n4,&t);float p[NOFF];pred(m,a,&t,p);int y=oi(rule(ph,a,c,n1,n2,n3,n4));s.n++;s.ok+=am(p)==y;}return 100.0*s.ok/s.n;}
static int K(const Model*m){int k=0;for(int i=0;i<MAX_NODE;i++)if(m->n[i].used&&m->n[i].strength>=.05f)k++;return k;}
static int live(const Model*m){int k=0;for(int i=0;i<MAX_NODE;i++)if(m->n[i].used)k++;return k;}
static void mn(uint16_t mask,char*b,size_t n){b[0]=0;int f=1;for(int t=0;t<NTOK;t++)if(mask&(1u<<t)){size_t l=strlen(b);snprintf(b+l,n-l,"%s%s",f?"":"*",TN[t]);f=0;}}
static void top(const Model*m){int id[MAX_NODE],n=0;for(int i=0;i<MAX_NODE;i++)if(m->n[i].used)id[n++]=i;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(m->n[id[j]].strength>m->n[id[i]].strength){int q=id[i];id[i]=id[j];id[j]=q;}printf("top:");for(int k=0;k<n&&k<10;k++){char b[160];mn(m->n[id[k]].mask,b,sizeof(b));printf(" (%s d=%u s=%.3f)",b,(unsigned)m->n[id[k]].depth,m->n[id[k]].strength);}puts("");}
static void phase(Model*m,int ph,int steps,int seed,const H*h,Mode mode){RNG r={0x56000u+(uint64_t)ph*1237u+(uint64_t)seed*811u};for(int s=0;s<steps;s++)step(m,ph,ri(&r,2),ri(&r,2),ri(&r,2),ri(&r,2),ri(&r,2),ri(&r,2),h,mode);}
static void run(int sd,Mode mode,const H*h){schema_set(sd);Model m={0};coarse(&m,sd);printf("=== seed=%d mode=%d schema C=%d order=%d%d%d%d req=%d%d%d%d base=%.3f K=%d ===\n",sd,(int)mode,G_CREQ,G_ORDER[0],G_ORDER[1],G_ORDER[2],G_ORDER[3],G_REQ[0],G_REQ[1],G_REQ[2],G_REQ[3],ev(&m,1,sd,12000),K(&m));for(int ph=2;ph<=6;ph++){phase(&m,ph,ph==2?4500:10000,sd,h,mode);printf("phase%d acc=%.3f K=%d live=%d births=%u deaths=%u\n",ph,ev(&m,ph,sd,12000),K(&m),live(&m),m.births,m.deaths);top(&m);}phase(&m,1,12000,sd,h,mode);printf("restore acc=%.3f K=%d live=%d births=%u deaths=%u\n",ev(&m,1,sd,12000),K(&m),live(&m),m.births,m.deaths);top(&m);}
int main(int argc,char**argv){int seeds=argc>1?atoi(argv[1]):5;H h={.uema=.05f,.uscale=30,.probe=.1f,.trlr=.35f,.focus_ema=.03f,.grow_quantum=.10f,.mass_decay=.985f,.birth_quantum=.80f};if(argc>2)h.grow_quantum=(float)atof(argv[2]);if(argc>3)h.birth_quantum=(float)atof(argv[3]);printf("BPC Query-Trace v0.5 causal support focusing | grow=%.3f birth=%.3f\n",h.grow_quantum,h.birth_quantum);for(int s=0;s<seeds;s++)run(s,NORMAL,&h);return 0;}