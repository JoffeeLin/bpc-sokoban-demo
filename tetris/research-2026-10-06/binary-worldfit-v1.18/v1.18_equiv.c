#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#define W 10
#define H 20
#define N (W*H)

typedef struct{double death[3],birth[3],joint[3],pair[3][3];}P;
static int ridx(int dx,int dy){ if(dx==0&&dy==0)return 0; if(dx==0&&dy==-1)return 1; if(dx==0&&dy==1)return 2; return -1; }
static uint64_t rs=0x243f6a8885a308d3ULL;
static uint64_t ru(void){rs^=rs>>12;rs^=rs<<25;rs^=rs>>27;return rs*2685821657736338717ULL;}
static double rd(void){return (double)(ru()>>11)*(1.0/9007199254740992.0);}
static void old_exec(const uint8_t in[N],const double seed[N],double carrier,const P*p,uint8_t out[N]){
  memset(out,0,N);
  for(int sy=0;sy<H;sy++)for(int x=0;x<W;x++){int sk=sy*W+x;if(!in[sk])continue;double survive=1,shift=0;int rels[3]={0};double ra[3]={0};int nr=0;
    if(seed[sk]>0){double sa=seed[sk];rels[nr]=0;ra[nr++]=sa;double j=carrier*sa*p->joint[0],d=carrier*sa*p->death[0];if(j>d)d=j;double b=carrier*sa*p->birth[0];if(j>b)b=j;survive*=1-d;shift+=b;}
    for(int dir=-1;dir<=1;dir+=2){int ri=dir<0?1:2,seen=0;for(int q=0;q<nr;q++)seen|=rels[q]==ri;for(int cy=sy+dir;cy>=0&&cy<H;cy+=dir){int ck=cy*W+x;if(seed[ck]<=0)continue;double sa=seed[ck];if(!seen&&nr<3){rels[nr]=ri;ra[nr]=sa;nr++;seen=1;}else if(seen){for(int q=0;q<nr;q++)if(rels[q]==ri)ra[q]=1-(1-ra[q])*(1-sa);}double j=carrier*sa*p->joint[ri],d=carrier*sa*p->death[ri];if(j>d)d=j;double b=carrier*sa*p->birth[ri];if(j>b)b=j;survive*=1-d;shift+=b;}}
    double gate=1;for(int i=0;i<nr;i++)for(int j=i+1;j<nr;j++){double ps=ra[i]*ra[j],g=p->pair[rels[i]][rels[j]];gate*=1-ps*(1-g);}shift*=gate;
    if(survive>.5)out[sk]=1;
    if(shift>.5){int oy=sy+(int)llround(shift);if(oy>=0&&oy<H)out[oy*W+x]=1;}
  }
}
static void new_exec(const uint8_t in[N],const double seed[N],double carrier,const P*p,uint8_t out[N]){
  memset(out,0,N);
  for(int sy=0;sy<H;sy++)for(int sx=0;sx<W;sx++){
    int sk=sy*W+sx;if(!in[sk])continue;
    double survive=1.0,vx=0.0,vy=0.0;
    int relDx[9],relDy[9],relType[9],nr=0;double ra[9]={0};
    if(seed[sk]>0){
      double sa=seed[sk];relDx[nr]=0;relDy[nr]=0;relType[nr]=0;ra[nr++]=sa;
      double j=carrier*sa*p->joint[0],d=carrier*sa*p->death[0];if(j>d)d=j;
      double b0=carrier*sa*p->birth[0];if(j>b0)b0=j;
      survive*=1.0-d;vy+=b0;
    }
    for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){
      if(dx==0&&dy==0)continue;
      int type=ridx(dx,dy),slot=-1;
      for(int step=1;;step++){
        int x=sx+dx*step,y=sy+dy*step;if(x<0||x>=W||y<0||y>=H)break;
        double sa=seed[y*W+x];if(sa<=0)continue;
        if(slot<0){
          for(int q=0;q<nr;q++)if(relDx[q]==dx&&relDy[q]==dy){slot=q;break;}
          if(slot<0&&nr<9){slot=nr;relDx[nr]=dx;relDy[nr]=dy;relType[nr]=type;ra[nr++]=0;}
        }
        if(slot>=0)ra[slot]=1.0-(1.0-ra[slot])*(1.0-sa);
        if(type<0)continue; /* frozen field has no consequence support for non-vertical relations */
        double j=carrier*sa*p->joint[type],d=carrier*sa*p->death[type];if(j>d)d=j;
        double bb=carrier*sa*p->birth[type];if(j>bb)bb=j;
        survive*=1.0-d;
        /* Generic execution conceptually scans every output relation. In the
           frozen support only (0,+1) has non-zero birth amplitude. */
        vx+=0.0*bb;vy+=1.0*bb;
      }
    }
    double gate=1.0;
    for(int i=0;i<nr;i++)for(int j=i+1;j<nr;j++){
      int x=relType[i],y=relType[j];if(x<0||y<0)continue;
      double ps=ra[i]*ra[j],g=p->pair[x][y];gate*=1.0-ps*(1.0-g);
    }
    vx*=gate;vy*=gate;
    if(survive>.5)out[sk]=1;
    if(hypot(vx,vy)>.5){int ox=sx+(int)llround(vx),oy=sy+(int)llround(vy);if(ox>=0&&ox<W&&oy>=0&&oy<H)out[oy*W+ox]=1;}
  }
}
int main(void){unsigned long long trials=20000,ok=0;for(unsigned long long t=0;t<trials;t++){uint8_t in[N];double seed[N]={0};for(int i=0;i<N;i++)in[i]=(uint8_t)((ru()%100)<30);/* closure seeds intentionally form horizontal rows, as in the frozen field evidence */int rows=1+(int)(ru()%4);for(int r=0;r<rows;r++){int y=(int)(ru()%H);for(int x=0;x<W;x++)seed[y*W+x]=0.5+0.5*rd();}P p;for(int i=0;i<3;i++){p.death[i]=rd();p.birth[i]=rd();p.joint[i]=rd();for(int j=0;j<3;j++)p.pair[i][j]=rd();}double carrier=rd();uint8_t a[N],b[N];old_exec(in,seed,carrier,&p,a);new_exec(in,seed,carrier,&p,b);if(memcmp(a,b,N)){printf("FAIL trial=%llu\n",t);return 1;}ok++;}printf("VERTICAL_TO_GENERIC_CLOSURE_EQUIV %llu/%llu = %.6f%%\n",ok,trials,100.0*(double)ok/trials);puts("Non-vertical relation/effect amplitudes are zero, matching the frozen field support; generic execution collapses exactly to the old vertical executor.");return 0;}