#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define PORTS 24
#define CAP 1024
#define MAXDELTA 2048

typedef struct{uint64_t key;double off,on;uint8_t used;}Cell;
typedef struct{Cell c[CAP];int n;}Field;
typedef struct{int s,d;double dm;}Delta;
static uint64_t rs=0x082efa98ec4e6c89ULL;
static uint64_t ru(void){rs^=rs>>12;rs^=rs<<25;rs^=rs>>27;return rs*2685821657736338717ULL;}
static uint64_t key(int s,int d){return((uint64_t)(uint32_t)s<<32)|(uint32_t)d;}
/* The only state-change primitive. Positive dm moves off->on, negative reverses. */
static void move_mass(double *off,double *on,double dm){if(dm>0){if(dm>*off)dm=*off;*off-=dm;*on+=dm;}else if(dm<0){double q=-dm;if(q>*on)q=*on;*on-=q;*off+=q;}}
static int idx(const Field*f,int s,int d){uint64_t k=key(s,d);for(int i=0;i<f->n;i++)if(f->c[i].used&&f->c[i].key==k)return i;return-1;}
static double amp(const Field*f,int s,int d){int i=idx(f,s,d);return i>=0?f->c[i].on:0.0;}
static Cell* ensure(Field*f,int s,int d){int i=idx(f,s,d);if(i>=0)return &f->c[i];for(int j=0;j<f->n;j++)if(!f->c[j].used){f->c[j]=(Cell){key(s,d),1.0,0.0,1};return &f->c[j];}if(f->n>=CAP)return NULL;f->c[f->n]=(Cell){key(s,d),1.0,0.0,1};return &f->c[f->n++];}
static void cleanup(Field*f){for(int i=0;i<f->n;i++)if(f->c[i].used&&f->c[i].on<=0.0)f->c[i].used=0;}
static double pred_prob(const Field*f,const uint8_t now[PORTS],int d){double off=1.0,on=0.0;for(int s=0;s<PORTS;s++)if(now[s]){double a=amp(f,s,d);move_mass(&off,&on,off*a);}return on;}
static void observe(Field*f,const uint8_t now[PORTS],const uint8_t next[PORTS]){Delta ds[MAXDELTA];int nd=0;for(int d=0;d<PORTS;d++){double P=pred_prob(f,now,d),e=(double)next[d]-P;if(e==0.0)continue;for(int s=0;s<PORTS;s++)if(now[s]&&nd<MAXDELTA)ds[nd++]=(Delta){s,d,e};}for(int i=0;i<nd;i++){Cell*q=idx(f,ds[i].s,ds[i].d)>=0?&f->c[idx(f,ds[i].s,ds[i].d)]:NULL;if(!q&&ds[i].dm>0)q=ensure(f,ds[i].s,ds[i].d);if(q)move_mass(&q->off,&q->on,ds[i].dm);}cleanup(f);}
static void predict(const Field*f,const uint8_t now[PORTS],uint8_t next[PORTS]){for(int d=0;d<PORTS;d++)next[d]=(uint8_t)(pred_prob(f,now,d)>.5);}
static int resident(const Field*f){int n=0;for(int i=0;i<f->n;i++)n+=f->c[i].used;return n;}
static int m1[PORTS],m2[PORTS];
static void init(void){for(int i=0;i<PORTS;i++){m1[i]=(7*i+5)%PORTS;m2[i]=(11*i+3)%PORTS;}}
static void reality(const uint8_t now[PORTS],uint8_t next[PORTS]){memset(next,0,PORTS);for(int i=0;i<PORTS;i++)if(now[i]){next[m1[i]]=1;next[m2[i]]=1;}}
int main(void){init();Field f={0};for(int e=0;e<100000;e++){uint8_t now[PORTS]={0},next[PORTS];int a=(int)(ru()%PORTS),b;do{b=(int)(ru()%PORTS);}while(b==a);now[a]=now[b]=1;reality(now,next);observe(&f,now,next);}unsigned long long n=300000,ok=0;for(unsigned long long q=0;q<n;q++){uint8_t now[PORTS]={0},truth[PORTS],pred[PORTS];int bits=2+(int)(ru()%7),count=0;while(count<bits){int s=(int)(ru()%PORTS);if(!now[s]){now[s]=1;count++;}}reality(now,truth);predict(&f,now,pred);ok+=!memcmp(truth,pred,PORTS);}double true_min=1,false_max=0;for(int s=0;s<PORTS;s++)for(int d=0;d<PORTS;d++){double a=amp(&f,s,d);int truth=(d==m1[s]||d==m2[s]);if(truth&&a<true_min)true_min=a;if(!truth&&a>false_max)false_max=a;}printf("INTEGRATED_ONE_MASS_MOTION_KERNEL exact=%llu/%llu=%.6f%% resident=%d true_min=%.6f false_max=%.6f\n",ok,n,100.0*(double)ok/n,resident(&f),true_min,false_max);return ok==n?0:1;}