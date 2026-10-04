#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

enum { NTOK=8, NOFF=5, NPAIR=28, AP=6 };
static const int OFFS[NOFF]={-2,-1,0,1,2};
static const char *TN[NTOK]={"A0","A1","C0","C1","N1=0","N1=1","N2=0","N2=1"};
typedef struct{uint64_t s;}RNG;
static uint32_t ru(RNG*r){r->s^=r->s>>12;r->s^=r->s<<25;r->s^=r->s>>27;return(uint32_t)((r->s*2685821657736338717ULL)>>32);}
static int ri(RNG*r,int n){return n?(int)(ru(r)%(uint32_t)n):0;}
typedef struct{int a,b;}PairID;
static PairID PID[NPAIR];
static int PI[NTOK][NTOK];
static void init_pairs(void){int k=0;memset(PI,-1,sizeof(PI));for(int i=0;i<NTOK;i++)for(int j=i+1;j<NTOK;j++){PID[k]=(PairID){i,j};PI[i][j]=PI[j][i]=k++;}}
typedef struct{float coarse[2][NOFF],dir[NPAIR][NOFF],u[NPAIR],s[NPAIR];unsigned seen[NPAIR],reuse[NPAIR];}Model;
typedef struct{int tok[4],n;}Trace;
static void toks(int a,int c,int n1,int n2,Trace*t){t->n=4;t->tok[0]=a;t->tok[1]=2+c;t->tok[2]=4+n1;t->tok[3]=6+n2;}
static int aps(const Trace*t,int q[AP]){int n=0;for(int i=0;i<t->n;i++)for(int j=i+1;j<t->n;j++)q[n++]=PI[t->tok[i]][t->tok[j]];return n;}
static int oi(int off){for(int i=0;i<NOFF;i++)if(OFFS[i]==off)return i;return -1;}
static int rule(int ph,int a,int c){if(ph==2&&a==0&&c==1)return 2;return a==0?1:-1;}
static void sm(const float z[NOFF],float p[NOFF]){float mx=z[0];for(int i=1;i<NOFF;i++)if(z[i]>mx)mx=z[i];double sum=0;for(int i=0;i<NOFF;i++){p[i]=expf(z[i]-mx);sum+=p[i];}for(int i=0;i<NOFF;i++)p[i]=(float)(p[i]/sum);}
static float loss5(const float p[NOFF],int y){return-logf(fmaxf(p[y],1e-12f));}
static int am(const float p[NOFF]){int b=0;for(int i=1;i<NOFF;i++)if(p[i]>p[b])b=i;return b;}
static float clamp01(float x){return x<0?0:(x>1?1:x);}
static float norm5(const float x[NOFF]){double s=0;for(int i=0;i<NOFF;i++)s+=(double)x[i]*x[i];return(float)sqrt(s);}
typedef struct{float dir_lr,u_ema,u_scale,probe,trace_lr;}Hyper;
typedef enum{NORMAL=0,UOFF=1,USHIFT=2,UREVERSE=3}Mode;

static void relation_effect(const Model*m,const int qq[AP],int n,int remove_q,int add_q,float add_amp,float out[NOFF]){
    for(int o=0;o<NOFF;o++) out[o]=0.f;
    float ss=0.f;
    for(int k=0;k<n;k++){
        int q=qq[k];float w=m->s[q];
        if(q==remove_q)w=0.f;
        if(q==add_q)w+=add_amp;
        if(w<=0.f||!m->seen[q])continue;
        ss+=w;
        for(int o=0;o<NOFF;o++)out[o]+=w*m->dir[q][o];
    }
    float den=ss>1.f?ss:1.f;
    if(den>0.f)for(int o=0;o<NOFF;o++)out[o]/=den;
}
static void logits_variant(const Model*m,int a,const Trace*t,int remove_q,int add_q,float add_amp,float z[NOFF]){
    int qq[AP],n=aps(t,qq);float eff[NOFF];
    relation_effect(m,qq,n,remove_q,add_q,add_amp,eff);
    for(int o=0;o<NOFF;o++)z[o]=m->coarse[a][o]+eff[o];
}
static void predict(const Model*m,int a,const Trace*t,float p[NOFF]){float z[NOFF];logits_variant(m,a,t,-1,-1,0,z);sm(z,p);}
static void train_coarse(Model*m,int seed){
    RNG r={0x7100u+(uint64_t)seed*1009u};
    for(int s=0;s<5000;s++){
        int a=ri(&r,2),c=ri(&r,2);Trace t;toks(a,c,ri(&r,2),ri(&r,2),&t);float p[NOFF];
        predict(m,a,&t,p);int y=oi(rule(1,a,c));
        for(int o=0;o<NOFF;o++)m->coarse[a][o]+=.30f*((o==y)-p[o]);
    }
}
static void step(Model*m,int ph,int a,int c,int n1,int n2,const Hyper*h,Mode mode){
    Trace t;toks(a,c,n1,n2,&t);int qq[AP],n=aps(&t,qq),y=oi(rule(ph,a,c));
    float z[NOFF],p[NOFF];logits_variant(m,a,&t,-1,-1,0,z);sm(z,p);float lf=loss5(p,y);
    float g[AP];
    for(int k=0;k<n;k++){
        int q=qq[k];g[k]=0.f;if(!m->seen[q])continue;
        float zv[NOFF],pv[NOFF];
        if(m->s[q]>.02f)logits_variant(m,a,&t,q,-1,0,zv);
        else logits_variant(m,a,&t,-1,q,h->probe,zv);
        sm(zv,pv);
        g[k]=(m->s[q]>.02f)?loss5(pv,y)-lf:lf-loss5(pv,y);
        m->reuse[q]++;
    }
    for(int k=0;k<n;k++){
        int q=qq[k],src=k;float gg=g[k];
        if(mode==UOFF)gg=0;
        else if(mode==UREVERSE)gg=-gg;
        else if(mode==USHIFT){src=(k+1)%n;gg=g[src];}
        (void)src;
        m->u[q]=(1-h->u_ema)*m->u[q]+h->u_ema*gg;
        m->s[q]=clamp01(h->u_scale*fmaxf(0,m->u[q]));
    }

    float z0[NOFF],p0[NOFF];
    for(int o=0;o<NOFF;o++)z0[o]=m->coarse[a][o];
    sm(z0,p0);
    float e0[NOFF];for(int o=0;o<NOFF;o++)e0[o]=(o==y)-p0[o];
    for(int k=0;k<n;k++){
        int q=qq[k];
        if(!m->seen[q]){m->seen[q]=1;for(int o=0;o<NOFF;o++)m->dir[q][o]=e0[o];}
        else if(m->s[q]<.02f)for(int o=0;o<NOFF;o++)m->dir[q][o]=(1-h->dir_lr)*m->dir[q][o]+h->dir_lr*e0[o];
    }

    float z1[NOFF],p1[NOFF];
    logits_variant(m,a,&t,-1,-1,0,z1);sm(z1,p1);
    float ef[NOFF];for(int o=0;o<NOFF;o++)ef[o]=(o==y)-p1[o];
    float ss=0.f;for(int k=0;k<n;k++)ss+=m->s[qq[k]];
    if(ss>0.f){
        for(int k=0;k<n;k++){
            int q=qq[k];if(m->s[q]<=0.f)continue;
            float share=m->s[q]/ss;
            for(int o=0;o<NOFF;o++)m->dir[q][o]+=h->trace_lr*share*ef[o];
        }
    }
}
typedef struct{unsigned long long n,ok;}Stat;
static void eval(const Model*m,int ph,int seed,int N,Stat s[4]){
    memset(s,0,sizeof(Stat)*4);RNG r={0xC000u+(uint64_t)seed*911u};
    for(int i=0;i<N;i++){
        int a=ri(&r,2),c=ri(&r,2);Trace t;toks(a,c,ri(&r,2),ri(&r,2),&t);float p[NOFF];
        predict(m,a,&t,p);int y=oi(rule(ph,a,c)),ix=a*2+c;s[ix].n++;s[ix].ok+=am(p)==y;
    }
}
static double allacc(const Stat s[4]){unsigned long long n=0,k=0;for(int i=0;i<4;i++){n+=s[i].n;k+=s[i].ok;}return n?100.0*k/n:0.0;}
static void pe(const char*tag,const Model*m,int ph,int seed){Stat s[4];eval(m,ph,seed,4000,s);printf("%-18s acc=%7.3f%%",tag,allacc(s));for(int i=0;i<4;i++)printf(" A%dC%d=%6.2f%%",i/2,i%2,100.0*s[i].ok/s[i].n);putchar('\n');}
static int K(const Model*m,float cut){int k=0;for(int q=0;q<NPAIR;q++)if(m->seen[q]&&m->s[q]>=cut)k++;return k;}
static void top(const Model*m){int id[NPAIR];for(int i=0;i<NPAIR;i++)id[i]=i;for(int i=0;i<NPAIR;i++)for(int j=i+1;j<NPAIR;j++)if(m->s[id[j]]>m->s[id[i]]){int t=id[i];id[i]=id[j];id[j]=t;}printf("top:");for(int i=0;i<8;i++){int q=id[i];if(!m->seen[q])continue;printf(" (%s*%s s=%.3f u=%.5f |d|=%.3f)",TN[PID[q].a],TN[PID[q].b],m->s[q],m->u[q],norm5(m->dir[q]));}puts("");}
static void run(int seed,Mode mode,const Hyper*h,int verbose){
    Model m={0};train_coarse(&m,seed);RNG r={0x8800u+(uint64_t)seed*1301u};
    if(verbose){printf("\n=== seed=%d mode=%d ===\n",seed,(int)mode);pe("before",&m,2,seed);}
    int marks[]={50,100,250,500,1000,2000},mi=0;
    for(int st=1;st<=2000;st++){
        int a=ri(&r,2),c=ri(&r,2);step(&m,2,a,c,ri(&r,2),ri(&r,2),h,mode);
        if(verbose&&mi<6&&st==marks[mi]){char tag[32];snprintf(tag,sizeof(tag),"adapt@%d",st);pe(tag,&m,2,seed);mi++;}
    }
    Stat s2[4];eval(&m,2,seed,4000,s2);double a2=allacc(s2);
    if(verbose){printf("after adapt K05=%d K20=%d\n",K(&m,.05f),K(&m,.20f));top(&m);}
    mi=0;
    for(int st=1;st<=2000;st++){
        int a=ri(&r,2),c=ri(&r,2);step(&m,3,a,c,ri(&r,2),ri(&r,2),h,mode);
        if(verbose&&mi<6&&st==marks[mi]){char tag[32];snprintf(tag,sizeof(tag),"restore@%d",st);pe(tag,&m,3,seed);mi++;}
    }
    Stat s3[4];eval(&m,3,seed,4000,s3);double a3=allacc(s3);
    if(verbose){printf("after restore K05=%d K20=%d\n",K(&m,.05f),K(&m,.20f));top(&m);}
    int q=PI[0][3];
    printf("SUMMARY seed=%d mode=%d phase2=%.3f restore=%.3f target_s=%.5f target_u=%.6f K05=%d K20=%d\n",seed,(int)mode,a2,a3,m.s[q],m.u[q],K(&m,.05f),K(&m,.20f));
}
int main(int argc,char**argv){
    init_pairs();int seeds=argc>1?atoi(argv[1]):5;
    Hyper h={.dir_lr=.05f,.u_ema=.05f,.u_scale=30.f,.probe=.10f,.trace_lr=.35f};
    if(argc>2)h.u_scale=(float)atof(argv[2]);
    if(argc>3)h.probe=(float)atof(argv[3]);
    if(argc>4)h.trace_lr=(float)atof(argv[4]);
    printf("BPC Query-Trace v0.3d conserved trace loop dir_lr=%.3f u_ema=%.3f scale=%.2f probe=%.3f trace_lr=%.3f\n",h.dir_lr,h.u_ema,h.u_scale,h.probe,h.trace_lr);
    for(int s=0;s<seeds;s++)run(s,NORMAL,&h,1);
    puts("\n--- controls ---");
    for(int s=0;s<seeds;s++){run(s,UOFF,&h,0);run(s,USHIFT,&h,0);run(s,UREVERSE,&h,0);}
    return 0;
}
