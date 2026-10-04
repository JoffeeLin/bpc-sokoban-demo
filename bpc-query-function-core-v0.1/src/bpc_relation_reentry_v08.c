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


#define MAX_TNODE 128
typedef struct{uint8_t used;int parent,cur;float dir[NOFF],u,s;unsigned evals;}TNode;
typedef struct{TNode n[MAX_TNODE];unsigned births,deaths;}Temporal;
static int tk_find(const Temporal*t,int parent,int cur){for(int i=0;i<MAX_TNODE;i++)if(t->n[i].used&&t->n[i].parent==parent&&t->n[i].cur==cur)return i;return-1;}
static int tk_alloc(Temporal*t,int parent,int cur,const float e[NOFF]){int q=tk_find(t,parent,cur);if(q>=0)return q;for(int i=0;i<MAX_TNODE;i++)if(!t->n[i].used){TNode*n=&t->n[i];memset(n,0,sizeof(*n));n->used=1;n->parent=parent;n->cur=cur;for(int o=0;o<NOFF;o++)n->dir[o]=.04f*e[o];t->births++;return i;}return-1;}
static int base_active(const Model*m,const Trace*tr,int out[32]){int n=0;for(int i=0;i<MAX_NODE&&n<32;i++)if(m->n[i].used&&m->n[i].strength>.05f&&(m->n[i].mask&tr->mask)==m->n[i].mask)out[n++]=i;return n;}
static void temporal_effect(const Temporal*t,const int prev_rel[32],int nr,int cur,int rem,int add,float amp,float out[NOFF]){for(int o=0;o<NOFF;o++)out[o]=0;float sw=0;for(int k=0;k<nr;k++){int id=tk_find(t,prev_rel[k],cur);if(id<0)continue;const TNode*n=&t->n[id];float w=n->s;if(id==rem)w=0;if(id==add)w+=amp;if(w<=0)continue;sw+=w;for(int o=0;o<NOFF;o++)out[o]+=w*n->dir[o];}float den=sw>1?sw:1;for(int o=0;o<NOFF;o++)out[o]/=den;}
static void full_pred(const Model*m,const Temporal*t,const Trace*tr,const int prev_rel[32],int nr,int cur,float p[NOFF]){float z[NOFF],te[NOFF];logits(m,cur,tr,-1,-1,0,z);temporal_effect(t,prev_rel,nr,cur,-1,-1,0,te);for(int o=0;o<NOFF;o++)z[o]+=te[o];sm(z,p);}
static int pair_target(int cur,int prev){if(prev==1&&cur==0)return 2;if(prev==0&&cur==1)return-2;return base_target(cur);}
static int triple_target(int cur,int prev,int pprev){if(pprev==0&&prev==1&&cur==0)return 3;if(pprev==1&&prev==0&&cur==1)return-3;return pair_target(cur,prev);}
static void train_pair_world(Model*m,int seed,const H*h){RNG r={0xEE100u+(uint64_t)seed*1009u};int prev=-1,py=99;for(int st=0;st<14000;st++){int cur=ri(&r,2),n1=ri(&r,2),n2=ri(&r,2);Trace tr;trace_make(cur,prev,py,n1,n2,&tr);int y=pair_target(cur,prev);learn_step(m,cur,&tr,y,h,NORMAL);prev=cur;py=y;}}
static int temporal_K(const Temporal*t){int k=0;for(int i=0;i<MAX_TNODE;i++)if(t->n[i].used&&t->n[i].s>=.05f)k++;return k;}
static void temporal_step(const Model*m,Temporal*t,const Trace*tr,const int prev_rel[32],int nr,int cur,int y,int trace_on){
    float p[NOFF];full_pred(m,t,tr,prev_rel,nr,cur,p);int yi=oi(y);float lf=loss7(p,yi);
    int ids[32],ni=0;for(int k=0;k<nr;k++){int id=tk_find(t,prev_rel[k],cur);if(id>=0)ids[ni++]=id;}
    for(int k=0;k<ni;k++){int id=ids[k];TNode*n=&t->n[id];float bz[NOFF],te[NOFF],pp[NOFF];logits(m,cur,tr,-1,-1,0,bz);temporal_effect(t,prev_rel,nr,cur,id,-1,0,te);for(int o=0;o<NOFF;o++)bz[o]+=te[o];sm(bz,pp);float g=(n->s>.02f)?loss7(pp,yi)-lf:0;n->evals++;n->u=.95f*n->u+.05f*g;n->s=clamp01(30.f*fmaxf(0,n->u));}
    float ef[NOFF];for(int o=0;o<NOFF;o++)ef[o]=(o==yi)-p[o];
    if(am(p)!=yi){for(int k=0;k<nr;k++){int id=tk_find(t,prev_rel[k],cur);if(id<0)id=tk_alloc(t,prev_rel[k],cur,ef);if(id>=0&&t->n[id].s<.02f)t->n[id].s=.05f;}}
    full_pred(m,t,tr,prev_rel,nr,cur,p);for(int o=0;o<NOFF;o++)ef[o]=(o==yi)-p[o];
    if(trace_on){float sw=0;for(int k=0;k<nr;k++){int id=tk_find(t,prev_rel[k],cur);if(id>=0&&t->n[id].s>0)sw+=t->n[id].s;}if(sw<=0)sw=1;for(int k=0;k<nr;k++){int id=tk_find(t,prev_rel[k],cur);if(id<0)continue;TNode*n=&t->n[id];if(n->s<=0)continue;float pl=1.0f/sqrtf(1.0f+n->evals/50.0f);for(int o=0;o<NOFF;o++)n->dir[o]+=.35f*(n->s/sw)*pl*ef[o];}}
}
static double eval_triple(const Model*m,const Temporal*t,int seed,int carrier_off){RNG r={0xEF000u+(uint64_t)seed*733u};int pprev=-1,prev=-1,py=99,ok=0;int prev_rel[32],nr_prev=0;for(int st=0;st<16000;st++){int cur=ri(&r,2),n1=ri(&r,2),n2=ri(&r,2);Trace tr;trace_make(cur,prev,py,n1,n2,&tr);float p[NOFF];int none[32]={0};full_pred(m,t,&tr,carrier_off?none:prev_rel,carrier_off?0:nr_prev,cur,p);int y=triple_target(cur,prev,pprev);ok+=OFFS[am(p)]==y;int now[32],nr=base_active(m,&tr,now);memcpy(prev_rel,now,sizeof(int)*nr);nr_prev=nr;pprev=prev;prev=cur;py=y;}return 100.0*ok/16000;}
static void run(int seed,int trace_on){H h={.uema=.05f,.uscale=30,.probe=.10f,.trlr=.35f,.focus_ema=.03f,.grow_quantum=.10f,.mass_decay=.985f,.birth_quantum=.80f,.stable_tau=50.f};Model m={0};train_base(&m,seed);train_pair_world(&m,seed,&h);Temporal t={0};RNG r={0xEA000u+(uint64_t)seed*1301u};int pprev=-1,prev=-1,py=99,prev_rel[32],nr_prev=0;for(int st=0;st<20000;st++){int cur=ri(&r,2),n1=ri(&r,2),n2=ri(&r,2);Trace tr;trace_make(cur,prev,py,n1,n2,&tr);int y=triple_target(cur,prev,pprev);temporal_step(&m,&t,&tr,prev_rel,nr_prev,cur,y,trace_on);int now[32],nr=base_active(&m,&tr,now);memcpy(prev_rel,now,sizeof(int)*nr);nr_prev=nr;pprev=prev;prev=cur;py=y;}int base_k=0;for(int i=0;i<MAX_NODE;i++)if(m.n[i].used&&m.n[i].strength>=.05f)base_k++;printf("seed=%d trace=%d acc=%.3f carrierOff=%.3f baseK=%d temporalK=%d births=%u deaths=%u\n",seed,trace_on,eval_triple(&m,&t,seed,0),eval_triple(&m,&t,seed,1),base_k,temporal_K(&t),t.births,t.deaths);}
int main(int argc,char**argv){int seeds=argc>1?atoi(argv[1]):5;puts("BPC relation-state re-entry v0.8 | order2 functions emit anonymous carrier into order3 query");for(int s=0;s<seeds;s++)run(s,1);puts("-- trace-off --");for(int s=0;s<seeds;s++)run(s,0);return 0;}