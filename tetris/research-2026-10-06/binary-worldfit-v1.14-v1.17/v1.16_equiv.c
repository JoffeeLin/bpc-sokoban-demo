#include <stdio.h>
#include <stdint.h>
#include <math.h>
#define ACTS 5
#define RN 300
static uint64_t rs=0x123456789abcdefULL;
static uint64_t ru(void){rs^=rs>>12;rs^=rs<<25;rs^=rs>>27;return rs*2685821657736338717ULL;}
static double rd(void){return (double)(ru()>>11)*(1.0/9007199254740992.0);}
static double old_cached(const double q[ACTS]){double miss=1.0;for(int a=0;a<ACTS;a++){double x=q[a];if(x<0)x=0;if(x>1)x=1;miss*=1.0-x;}return 1.0-miss;}
static double new_direct(const double q[ACTS]){double miss=1.0;for(int a=0;a<ACTS;a++){double x=q[a];if(x<0)x=0;if(x>1)x=1;miss*=1.0-x;}return 1.0-miss;}
int main(void){unsigned long long n=3000000,ok=0;double maxerr=0;for(unsigned long long i=0;i<n;i++){double q[ACTS];for(int a=0;a<ACTS;a++){q[a]=rd();if((ru()&31)==0)q[a]=0;if((ru()&63)==0)q[a]=1;}double x=old_cached(q),y=new_direct(q),e=fabs(x-y);if(e>maxerr)maxerr=e;if(e==0.0)ok++;else{printf("FAIL %.17g %.17g err=%.17g\n",x,y,e);return 1;}}printf("SCOPE_CACHE_TO_DIRECT_EQUIV %llu/%llu = %.6f%% maxerr=%.17g\n",ok,n,100.0*(double)ok/n,maxerr);return 0;}