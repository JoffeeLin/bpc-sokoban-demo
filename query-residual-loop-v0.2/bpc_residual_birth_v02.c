#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/*
BPC Residual-Born Support v0.2
------------------------------
Tests the missing step revealed by v0.1:
  mature coarse function explains first;
  persistent unexplained query residual accumulates in anonymous pair supports;
  only a repeatedly coherent residual direction is allowed to mature;
  the new mature relation then enters the same query wave and receives trace writeback.

No semantic "A0&C1 exception" is programmed. All unordered pairs among the four
currently participating raw tokens are equally eligible candidates.
*/

enum { NTOK=8, NOFF=5, NPAIR=28 };
static const int OFFS[NOFF]={-2,-1,0,1,2};
static const char *TN[NTOK]={"A0","A1","C0","C1","N1=0","N1=1","N2=0","N2=1"};

typedef struct{uint64_t s;}RNG;
static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return(uint32_t)((r->s*2685821657736338717ULL)>>32);}static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}

typedef struct{int a,b;}PairID;
static PairID PID[NPAIR];
static int pair_index[NTOK][NTOK];
static void init_pairs(void){int k=0;for(int i=0;i<NTOK;i++)for(int j=i+1;j<NTOK;j++){PID[k]=(PairID){i,j};pair_index[i][j]=pair_index[j][i]=k++;}}

typedef struct{
    float coarse[2][NOFF];
    float pair_w[NPAIR][NOFF];
    float evidence[NPAIR][NOFF];
    unsigned hits[NPAIR];
    unsigned char mature[NPAIR];
    int births;
}Model;

typedef struct{int tok[4],n;}Trace;
static void toks(int a,int c,int n1,int n2,Trace*tr){tr->n=4;tr->tok[0]=a;tr->tok[1]=2+c;tr->tok[2]=4+n1;tr->tok[3]=6+n2;}
static int oi(int off){for(int i=0;i<NOFF;i++)if(OFFS[i]==off)return i;return -1;}
static void sm(const float z[NOFF],float p[NOFF]){float mx=z[0];for(int i=1;i<NOFF;i++)if(z[i]>mx)mx=z[i];double s=0;for(int i=0;i<NOFF;i++){p[i]=expf(z[i]-mx);s+=p[i];}for(int i=0;i<NOFF;i++)p[i]=(float)(p[i]/s);}
static int rule(int phase,int a,int c){if(phase==2&&a==0&&c==1)return 2;return a==0?1:-1;}
static int am(const float p[NOFF]){int b=0;for(int i=1;i<NOFF;i++)if(p[i]>p[b])b=i;return b;}
static float norm5(const float x[NOFF]){double s=0;for(int i=0;i<NOFF;i++)s+=(double)x[i]*x[i];return(float)sqrt(s);}

static int active_pairs(const Trace*tr,int out[6]){int n=0;for(int i=0;i<tr->n;i++)for(int j=i+1;j<tr->n;j++)out[n++]=pair_index[tr->tok[i]][tr->tok[j]];return n;}
static void predict(const Model*m,int a,const Trace*tr,int shifted,float p[NOFF]){
    float z[NOFF];for(int o=0;o<NOFF;o++)z[o]=m->coarse[a][o];
    int pp[6],n=active_pairs(tr,pp);
    for(int k=0;k<n;k++){
        int q=pp[k]; if(shifted)q=(q+1)%NPAIR;
        if(!m->mature[q])continue;
        for(int o=0;o<NOFF;o++)z[o]+=m->pair_w[q][o];
    }
    sm(z,p);
}
static void train_coarse(Model*m,int seed){RNG r={0x1100u+(uint64_t)seed*1009u};for(int s=0;s<5000;s++){int a=ri(&r,2),c=ri(&r,2);(void)c;float p[NOFF];Trace tr;toks(a,c,ri(&r,2),ri(&r,2),&tr);predict(m,a,&tr,0,p);int y=oi(a==0?1:-1);for(int o=0;o<NOFF;o++)m->coarse[a][o]+=.30f*((o==y?1.f:0.f)-p[o]);}}

static void phase2_step(Model*m,int a,int c,int n1,int n2,float birth_threshold,int allow_birth){
    Trace tr;toks(a,c,n1,n2,&tr);float p[NOFF];predict(m,a,&tr,0,p);int y=oi(rule(2,a,c));float e[NOFF];for(int o=0;o<NOFF;o++)e[o]=(o==y?1.f:0.f)-p[o];
    int pp[6],n=active_pairs(&tr,pp),nm=0;for(int k=0;k<n;k++)if(m->mature[pp[k]])nm++;
    if(nm){for(int k=0;k<n;k++){int q=pp[k];if(!m->mature[q])continue;for(int o=0;o<NOFF;o++)m->pair_w[q][o]+=.30f*e[o]/nm;}}
    if(!allow_birth)return;
    for(int k=0;k<n;k++){
        int q=pp[k];if(m->mature[q])continue;
        for(int o=0;o<NOFF;o++) m->evidence[q][o]+=e[o];
        m->hits[q]++;
        if(m->hits[q]>=30){float avg[NOFF];for(int o=0;o<NOFF;o++)avg[o]=m->evidence[q][o]/m->hits[q];if(norm5(avg)>birth_threshold){m->mature[q]=1;m->births++;for(int o=0;o<NOFF;o++)m->pair_w[q][o]=1.5f*avg[o];}}
    }
}

typedef struct{unsigned long long n,ok;double loss;}Stat;
static void eval(const Model*m,int phase,int seed,int n,int shifted,Stat cat[4]){memset(cat,0,sizeof(Stat)*4);RNG r={0x9000u+(uint64_t)seed*911u};for(int i=0;i<n;i++){int a=ri(&r,2),c=ri(&r,2);Trace tr;toks(a,c,ri(&r,2),ri(&r,2),&tr);float p[NOFF];predict(m,a,&tr,shifted,p);int y=oi(rule(phase,a,c)),ix=a*2+c;cat[ix].n++;cat[ix].ok+=am(p)==y;cat[ix].loss+=-log(fmax(p[y],1e-12));}}
static double allacc(const Stat s[4]){unsigned long long n=0,k=0;for(int i=0;i<4;i++){n+=s[i].n;k+=s[i].ok;}return 100.0*k/n;}
static void print_eval(const char*tag,const Model*m,int seed,int shifted){Stat s[4];eval(m,2,seed,4000,shifted,s);printf("%-16s acc=%7.3f%%",tag,allacc(s));for(int i=0;i<4;i++)printf(" A%dC%d=%6.2f%%",i/2,i%2,100.0*s[i].ok/s[i].n);printf(" K=%d\n",m->births);}
static void print_births(const Model*m){printf("mature:");for(int q=0;q<NPAIR;q++)if(m->mature[q])printf(" (%s*%s hits=%u norm=%.3f)",TN[PID[q].a],TN[PID[q].b],m->hits[q],norm5(m->pair_w[q]));puts("");}

static void run(int seed,float threshold){Model m={0};train_coarse(&m,seed);printf("\n=== seed=%d ===\n",seed);print_eval("before-change",&m,seed,0);RNG r={0x2200u+(uint64_t)seed*1301u};int marks[]={50,100,150,250,500,1000};int mi=0;for(int step=1;step<=1000;step++){int a=ri(&r,2),c=ri(&r,2);phase2_step(&m,a,c,ri(&r,2),ri(&r,2),threshold,1);if(mi<6&&step==marks[mi]){char t[32];snprintf(t,sizeof(t),"adapt@%d",step);print_eval(t,&m,seed,0);mi++;}}
    print_births(&m);print_eval("final-normal",&m,seed,0);print_eval("pair-shift",&m,seed,1);
    Model ctrl={0};train_coarse(&ctrl,seed);RNG rc={0x2200u+(uint64_t)seed*1301u};for(int step=1;step<=1000;step++){int a=ri(&rc,2),c=ri(&rc,2);phase2_step(&ctrl,a,c,ri(&rc,2),ri(&rc,2),threshold,0);}print_eval("no-birth",&ctrl,seed,0);
}
int main(int argc,char**argv){init_pairs();int seeds=argc>1?atoi(argv[1]):5;float threshold=argc>2?(float)atof(argv[2]):1.0f;for(int s=0;s<seeds;s++)run(s,threshold);return 0;}
