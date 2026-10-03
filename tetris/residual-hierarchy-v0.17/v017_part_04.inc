int v013_main(int argc,char**argv){int warm=argc>1?atoi(argv[1]):12000,q1s=argc>2?atoi(argv[2]):60000,rsteps=argc>3?atoi(argv[3]):180000,N=argc>4?atoi(argv[4]):8000;FC fc={0};QC q1;EnergyCube ec;ShapeCube sc;qi(&q1);ei(&ec);si(&sc);RNG r={0x13131313};Game g;init(&g,ri(&r,7));Pilot po={0};uint8_t a[FRAME],t[FRAME];for(int i=0;i<warm;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);step(&g,ac);render(&g,t);fobs(&fc,a,ac,t);}for(int i=0;i<q1s;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);step(&g,ac);render(&g,t);float fun[FD];Cache c;fw(&fc,ac,fun);cache(a,fun,&c);trainq(&q1,&c,a,fun,t);}printf("DirectFit v0.13 D1 energy*shape warm=%d q1=%d residual=%d\n",warm,q1s,rsteps);eval(&fc,&q1,N,0x1313E,0,"baseline");for(int i=0;i<rsteps;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);step(&g,ac);render(&g,t);float fun[FD],p1[FRAME],er[FRAME];Cache c;fw(&fc,ac,fun);cache(a,fun,&c);predq(&q1,&c,a,fun,p1);float en=residual_energy(t,p1,er);etrain(&ec,a,fun,en);strain(&sc,&c,er,en);}eval_factor(&fc,&q1,&ec,&sc,N,0x1313F,0,"factor-final");printf("writes energy=%llu shape=%llu\n",ec.writes,sc.writes);sf(&sc);ef(&ec);qf(&q1);return 0;}
/* END INLINE direct_residual_factor_v013_lib.c */
#define QD2 61

typedef struct{float w[QD2];float b;} GateWave2;
static void qwave2(const uint8_t*f,const float*p1,const float*fun,float z[QD2]){
  int q=0;
  for(int pa=0;pa<2;pa++)for(int pb=0;pb<2;pb++)for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){
    double s=0,den=0;
    for(int y=0;y<H;y++)for(int x=0;x<W;x++){
      int xx=x+dx,yy=y+dy;if(xx<0||xx>=W||yy<0||yy>=H)continue;
      float aa=(float)f[pa*CELLS+y*W+x],bb=p1[pb*CELLS+yy*W+xx];s+=(double)aa*bb;den+=aa;
    }
    z[q++]=(float)(s/(den>0?den:1.0));
  }
  for(int k=0;k<8;k++){double s=0;for(int i=0;i<16;i++){uint32_t h=mix((uint32_t)(k*977+i*131+17));s+=((h&1u)?1.:-1.)*(double)f[400+i];}z[q++]=(float)(s/4.0);}
  for(int k=0;k<8;k++){double s=0;for(int i=0;i<16;i++){uint32_t h=mix((uint32_t)(k*991+i*137+23));s+=((h&1u)?1.:-1.)*(double)p1[400+i];}z[q++]=(float)(s/4.0);}
  for(int k=0;k<8;k++){double s=0;for(int i=0;i<FD;i++){uint32_t h=mix((uint32_t)(k*983+i*139+29));s+=((h&1u)?1.:-1.)*(double)fun[i];}z[q++]=(float)(s/sqrt((double)FD));}
  z[q++]=1.f;if(q!=QD2){fprintf(stderr,"QD mismatch\n");exit(2);}
}
static float gwpred(const GateWave2*g,const float z[QD2]){double s=g->b;for(int i=0;i<QD2;i++)s+=g->w[i]*z[i];if(s<0)s=0;if(s>1)s=1;return(float)s;}
static void gwtrain(GateWave2*g,const float z[QD2],float t){float p=gwpred(g,z),e=t-p;double n=1e-4;for(int i=0;i<QD2;i++)n+=z[i]*z[i];float lr=.35f*e/(float)n;for(int i=0;i<QD2;i++)g->w[i]+=lr*z[i];g->b+=.02f*e;}
static void eval_wf(const FC*fc,const QC*q1,const ShapeCube*sc,const GateWave2*gw,int N,uint64_t seed,int mode,const char*tag){RNG r={seed};Game g;init(&g,ri(&r,7));Pilot po={0};uint8_t a[FRAME],t[FRAME];float fun[FD],p[FRAME];Cache c;M m={0};GStat ga={0},gm={0},gr={0},gl={0},gc={0};for(int i=0;i<N;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);int ev=step(&g,ac);render(&g,t);fw(fc,ac,fun);cache(a,fun,&c);float p1[FRAME],z[QD2];predq(q1,&c,a,fun,p1);qwave2(a,p1,fun,z);float gg=gwpred(gw,z);if(mode==1)gg=0;else if(mode==2)gg=1.f-gg;for(int j=0;j<FRAME;j++){float v=p1[j]+gg*spred1(sc,&c,j);if(v<.001f)v=.001f;if(v>.999f)v=.999f;p[j]=v;}madd(&m,a,t,p,ev);GStat*arr[5]={&ga,&gm,&gr,&gl,&gc};int use[5]={1,(ev&EV_MOVE)!=0,(ev&EV_ROT)!=0,(ev&EV_LOCK)!=0,(ev&EV_CLEAR)!=0};for(int zc=0;zc<5;zc++)if(use[zc]){arr[zc]->n++;arr[zc]->g+=gg;}}mp(tag,&m);printf("[%s gate] all=%.4f move=%.4f rot=%.4f lock=%.4f clear=%.4f\n",tag,ga.g/(ga.n?ga.n:1),gm.g/(gm.n?gm.n:1),gr.g/(gr.n?gr.n:1),gl.g/(gl.n?gl.n:1),gc.g/(gc.n?gc.n:1));}
int v014_main(int argc,char**argv){int warm=argc>1?atoi(argv[1]):12000,q1s=argc>2?atoi(argv[2]):60000,rsteps=argc>3?atoi(argv[3]):240000,N=argc>4?atoi(argv[4]):10000;FC fc={0};QC q1;ShapeCube sc;GateWave2 gw={0};qi(&q1);si(&sc);RNG r={0x14141414};Game g;init(&g,ri(&r,7));Pilot po={0};uint8_t a[FRAME],t[FRAME];for(int i=0;i<warm;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);step(&g,ac);render(&g,t);fobs(&fc,a,ac,t);}for(int i=0;i<q1s;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);step(&g,ac);render(&g,t);float fun[FD];Cache c;fw(&fc,ac,fun);cache(a,fun,&c);trainq(&q1,&c,a,fun,t);}printf("DirectFit v0.14 continuous residual query wave warm=%d q1=%d residual=%d\n",warm,q1s,rsteps);eval(&fc,&q1,N,0x1414A,0,"baseline");for(int i=0;i<rsteps;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);step(&g,ac);render(&g,t);float fun[FD],p1[FRAME],er[FRAME],z[QD2];Cache c;fw(&fc,ac,fun);cache(a,fun,&c);predq(&q1,&c,a,fun,p1);float en=residual_energy(t,p1,er);qwave2(a,p1,fun,z);gwtrain(&gw,z,en);strain(&sc,&c,er,en);}eval_wf(&fc,&q1,&sc,&gw,N,0x1414B,0,"wave-factor");eval_wf(&fc,&q1,&sc,&gw,N,0x1414B,1,"gate-zero");eval_wf(&fc,&q1,&sc,&gw,N,0x1414B,2,"gate-reflect");printf("shape_writes=%llu\n",sc.writes);sf(&sc);qf(&q1);return 0;}
/* END INLINE direct_residual_wavegate_v014_lib.c */
#define F2D 64
typedef struct{float w[F2D][QD2];float b[F2D];}F2Cube;
