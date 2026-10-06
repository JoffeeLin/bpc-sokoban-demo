#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#define RW 15
#define RH 20
#define RN (RW*RH)
#define CAP 256
#define OFFN ((2*RH+1)*(2*RW+1))

typedef struct{int dx[CAP],dy[CAP],n;double ai[CAP],ao[CAP];}Cache;
static uint64_t rs=0x6a09e667f3bcc909ULL;
static uint64_t ru(void){rs^=rs>>12;rs^=rs<<25;rs^=rs>>27;return rs*2685821657736338717ULL;}
static double rd(void){return (double)(ru()>>11)*(1.0/9007199254740992.0);}
static int oi(int dx,int dy){return (dy+RH)*(2*RW+1)+(dx+RW);}
static void build_cache(const double AI[OFFN],const double AO[OFFN],Cache*c){memset(c,0,sizeof(*c));for(int dy=-RH;dy<=RH;dy++)for(int dx=-RW;dx<=RW;dx++){int j=oi(dx,dy);double ai=AI[j],ao=AO[j];if((ai>0.0||ao>0.0)&&c->n<CAP){int n=c->n++;c->dx[n]=dx;c->dy[n]=dy;c->ai[n]=ai;c->ao[n]=ao;}}}
static void old_field(const Cache*c,const uint8_t src[RN],const double scope[RN],double out[RN]){double miss[RN];for(int i=0;i<RN;i++)miss[i]=1;for(int sy=0;sy<RH;sy++)for(int sx=0;sx<RW;sx++)if(src[sy*RW+sx]){double sc=scope[sy*RW+sx];for(int r=0;r<c->n;r++){double rel=sc*c->ai[r]+(1-sc)*c->ao[r];if(rel<=0)continue;int x=sx+c->dx[r],y=sy+c->dy[r];if(x>=0&&x<RW&&y>=0&&y<RH)miss[y*RW+x]*=1-rel;}}for(int i=0;i<RN;i++)out[i]=1-miss[i];}
static void new_field(const double AI[OFFN],const double AO[OFFN],const uint8_t src[RN],const double scope[RN],double out[RN]){double miss[RN];for(int i=0;i<RN;i++)miss[i]=1;for(int sy=0;sy<RH;sy++)for(int sx=0;sx<RW;sx++)if(src[sy*RW+sx]){double sc=scope[sy*RW+sx];int kept=0;for(int dy=-RH;dy<=RH;dy++)for(int dx=-RW;dx<=RW;dx++){int j=oi(dx,dy);double ai=AI[j],ao=AO[j];if(!(ai>0||ao>0))continue;if(kept>=CAP)continue;kept++;double rel=sc*ai+(1-sc)*ao;if(rel<=0)continue;int x=sx+dx,y=sy+dy;if(x>=0&&x<RW&&y>=0&&y<RH)miss[y*RW+x]*=1-rel;}}for(int i=0;i<RN;i++)out[i]=1-miss[i];}
static double old_carrier(const Cache*c,const uint8_t src[RN],const double scope[RN],const uint8_t world[RN],const double compat[RN]){double C=1;for(int sy=0;sy<RH;sy++)for(int sx=0;sx<RW;sx++)if(src[sy*RW+sx]){double sc=scope[sy*RW+sx];for(int r=0;r<c->n;r++){double rel=sc*c->ai[r]+(1-sc)*c->ao[r];if(rel<=0)continue;int x=sx+c->dx[r],y=sy+c->dy[r];if(x<0||x>=RW||y<0||y>=RH)continue;int k=y*RW+x;(void)world;C*=1-rel*(1-compat[k]);}}return C;}
static double new_carrier(const double AI[OFFN],const double AO[OFFN],const uint8_t src[RN],const double scope[RN],const uint8_t world[RN],const double compat[RN]){double C=1;for(int sy=0;sy<RH;sy++)for(int sx=0;sx<RW;sx++)if(src[sy*RW+sx]){double sc=scope[sy*RW+sx];int kept=0;for(int dy=-RH;dy<=RH;dy++)for(int dx=-RW;dx<=RW;dx++){int j=oi(dx,dy);double ai=AI[j],ao=AO[j];if(!(ai>0||ao>0))continue;if(kept>=CAP)continue;kept++;double rel=sc*ai+(1-sc)*ao;if(rel<=0)continue;int x=sx+dx,y=sy+dy;if(x<0||x>=RW||y<0||y>=RH)continue;int k=y*RW+x;(void)world;C*=1-rel*(1-compat[k]);}}return C;}
int main(void){unsigned long long trials=200,ok=0;double maxerr=0;for(unsigned long long t=0;t<trials;t++){double AI[OFFN],AO[OFFN];for(int i=0;i<OFFN;i++){int dense=(t%7)==0;AI[i]=((dense||((ru()%100)<8))?rd():0);AO[i]=((dense||((ru()%100)<8))?rd():0);}uint8_t src[RN],world[RN];double scope[RN],compat[RN];for(int i=0;i<RN;i++){src[i]=(uint8_t)((ru()%100)<6);world[i]=(uint8_t)((ru()%100)<30);scope[i]=rd();compat[i]=rd();}Cache c;build_cache(AI,AO,&c);double a[RN],b[RN];old_field(&c,src,scope,a);new_field(AI,AO,src,scope,b);double e=0;for(int i=0;i<RN;i++){double d=fabs(a[i]-b[i]);if(d>e)e=d;}double ca=old_carrier(&c,src,scope,world,compat),cb=new_carrier(AI,AO,src,scope,world,compat);double ce=fabs(ca-cb);if(ce>e)e=ce;if(e>maxerr)maxerr=e;if(e==0)ok++;else{printf("FAIL trial=%llu cache_n=%d err=%.17g\n",t,c.n,e);return 1;}}printf("SPAWN_CACHE_TO_DIRECT_EQUIV %llu/%llu = %.6f%% maxerr=%.17g\n",ok,trials,100.0*(double)ok/trials,maxerr);return 0;}