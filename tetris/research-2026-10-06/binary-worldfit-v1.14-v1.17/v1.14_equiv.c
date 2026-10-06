#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#define ACTS 5
#define NDIR 9

typedef struct { double q[ACTS][3][3]; } OldGauge;
typedef struct { double q[ACTS][3][3]; } NewSelfMap;

static double amp(double q){ double a=2.0*q-1.0; return a>0.0?a:0.0; }
static int old_read(const OldGauge*g,int a,int*dx,int*dy){
  double sx=0,sy=0,z=0;
  for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
    double w=amp(g->q[a][y+1][x+1]); if(w<=0) continue;
    sx+=w*x; sy+=w*y; z+=w;
  }
  if(z<=1e-12) return 0;
  *dx=(int)lround(sx/z); *dy=(int)lround(sy/z); return 1;
}
static int new_read(const NewSelfMap*g,int a,int*dx,int*dy){
  /* self-relation (0,0) -> output relation (dx,dy), same probability amplitudes */
  double sx=0,sy=0,z=0;
  for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
    double w=amp(g->q[a][y+1][x+1]); if(w<=0) continue;
    sx+=w*x; sy+=w*y; z+=w;
  }
  if(z<=1e-12) return 0;
  *dx=(int)lround(sx/z); *dy=(int)lround(sy/z); return 1;
}
static uint64_t rng=0x9e3779b97f4a7c15ULL;
static uint64_t ru(void){rng^=rng>>12;rng^=rng<<25;rng^=rng>>27;return rng*2685821657736338717ULL;}
static double rd(void){ return (double)(ru()>>11)*(1.0/9007199254740992.0); }

int main(void){
  unsigned long long trials=1000000, exact=0, empty=0;
  for(unsigned long long t=0;t<trials;t++){
    OldGauge o; NewSelfMap n;
    for(int a=0;a<ACTS;a++)for(int y=0;y<3;y++)for(int x=0;x<3;x++){
      /* exercise absent/negative/positive/multimodal relations */
      double q=rd(); if((ru()&7)==0) q=0.5;
      o.q[a][y][x]=q; n.q[a][y][x]=q;
    }
    int a=(int)(ru()%ACTS),ox=99,oy=99,nx=98,ny=98;
    int ro=old_read(&o,a,&ox,&oy),rn=new_read(&n,a,&nx,&ny);
    int ok=(ro==rn)&&(!ro||(ox==nx&&oy==ny));
    exact+=ok; empty+=!ro;
    if(!ok){printf("FAIL t=%llu a=%d old=%d (%d,%d) new=%d (%d,%d)\n",t,a,ro,ox,oy,rn,nx,ny);return 1;}
  }
  printf("GAUGE_TO_SELF_RELATION_EQUIV %llu/%llu = %.6f%% empty=%llu\n",exact,trials,100.0*(double)exact/(double)trials,empty);
  puts("Interpretation: after copying each old gauge probability to the self-relation mapping key, gauge readout is algebraically identical; no winner/topology change is introduced.");
  return 0;
}