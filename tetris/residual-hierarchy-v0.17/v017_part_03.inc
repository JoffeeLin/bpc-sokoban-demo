int main(int argc,char**argv){int warm=argc>1?atoi(argv[1]):12000,tr=argc>2?atoi(argv[2]):50000,ev=argc>3?atoi(argv[3]):5000;FC fc={0};QC q;qi(&q);RNG r={0x1234567};Game g;init(&g,ri(&r,7));Pilot po={0};uint8_t a[FRAME],t[FRAME];for(int i=0;i<warm;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);step(&g,ac);render(&g,t);fobs(&fc,a,ac,t);}printf("direct-full-tetris ERROR-WRITEBACK function-cube warm=%d train=%d\n",warm,tr);for(int i=0;i<tr;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);step(&g,ac);render(&g,t);float fun[FD];Cache c;fw(&fc,ac,fun);cache(a,fun,&c);trainq(&q,&c,a,fun,t);if((i+1)%10000==0){char s[32];snprintf(s,sizeof(s),"hold@%d",i+1);eval(&fc,&q,1500,0xABC000u+(uint64_t)i,0,s);}}eval(&fc,&q,ev,0xDEADBEEFu,0,"final");eval(&fc,&q,ev,0xDEADBEEFu,1,"F-zero");eval(&fc,&q,ev,0xDEADBEEFu,2,"F-flip");eval(&fc,&q,ev,0xDEADBEEFu,3,"F-shift");qf(&q);return 0;}
/* END INLINE direct_errorwrite_cube1.c */
#undef main

/* v0.13: D1 = residual energy * residual shape.
   Both are accumulated by error writeback from complete real Tetris streams.
   No event labels are used by learning. */
#define EB 3
#define EABITS 16
#define EASZ (1u<<EABITS)
#define EAMASK (EASZ-1u)

typedef struct{float *w[EB];unsigned long long writes;} EnergyCube;
typedef struct{float *w[BR];unsigned long long writes;} ShapeCube;

static uint64_t mh64(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static uint64_t p5h(const uint8_t*f,int cx,int cy,int salt){uint64_t h=0x243f6a8885a308d3ULL^(uint64_t)(salt+1)*0x9e3779b97f4a7c15ULL;for(int pl=0;pl<2;pl++)for(int dy=-2;dy<=2;dy++)for(int dx=-2;dx<=2;dx++){int x=cx+dx,y=cy+dy;uint64_t bit=(x<0||x>=W||y<0||y>=H)?1u:(uint64_t)f[pl*CELLS+y*W+x];h=mh64(h^(bit+5u*(uint64_t)(pl+1)+17u*(uint64_t)(dx+3)+71u*(uint64_t)(dy+3)));}return h;}
static uint32_t estate_addr(const uint8_t*f,const float*fun,int b){uint64_t s1=0x9e3779b97f4a7c15ULL^(uint64_t)(b+1)*0x94d049bb133111ebULL,s2=0x632be59bd9b4e019ULL;int n=0;for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(f[CELLS+y*W+x]){uint64_t h=p5h(f,x,y,b);s1+=mh64(h+0x9e3779b97f4a7c15ULL);s2+=mh64(h^0xd1b54a32d192ed03ULL);n++;}uint64_t h=mh64(s1^(s2<<1)^((uint64_t)prev16(f)<<13)^top_hash(f)^((uint64_t)bot_hash(f)<<7)^((uint64_t)fh(fun,61+b)<<21)^(uint64_t)(n+1)*0x27d4eb2dULL);return(uint32_t)h&EAMASK;}
static void ei(EnergyCube*e){memset(e,0,sizeof(*e));for(int b=0;b<EB;b++){e->w[b]=calloc(EASZ,sizeof(float));if(!e->w[b])exit(2);}}
static void ef(EnergyCube*e){for(int b=0;b<EB;b++)free(e->w[b]);}
static float epred(const EnergyCube*e,const uint8_t*f,const float*fun){float v=0;for(int b=0;b<EB;b++)v+=e->w[b][estate_addr(f,fun,b)];v/=EB;if(v<0)v=0;if(v>1)v=1;return v;}
static void etrain(EnergyCube*e,const uint8_t*f,const float*fun,float target){float p=epred(e,f,fun),er=target-p,d=.48f*er/EB;for(int b=0;b<EB;b++){float*w=&e->w[b][estate_addr(f,fun,b)];*w+=d;if(*w<0)*w=0;if(*w>1)*w=1;e->writes++;}}

static void si(ShapeCube*s){memset(s,0,sizeof(*s));for(int b=0;b<BR;b++){s->w[b]=calloc(RSZ,sizeof(float));if(!s->w[b])exit(2);}}
static void sf(ShapeCube*s){for(int b=0;b<BR;b++)free(s->w[b]);}
static float spred1(const ShapeCube*s,const Cache*c,int j){float v=0;for(int b=0;b<BR;b++)v+=s->w[b][c->a[b][j]];return v/BR;}
static void strain(ShapeCube*s,const Cache*c,const float*e,float energy){if(energy<1e-5f)return;float wt=energy;if(wt>0.25f)wt=.25f;for(int j=0;j<FRAME;j++){float target=e[j]/energy;if(target>6.f)target=6.f;if(target<-6.f)target=-6.f;float p=spred1(s,c,j);float er=target-p,d=.36f*wt*er/BR;for(int b=0;b<BR;b++){float*w=&s->w[b][c->a[b][j]];*w+=d;if(*w>6.f)*w=6.f;if(*w<-6.f)*w=-6.f;s->writes++;}}}
static float residual_energy(const uint8_t*t,const float*p,float e[FRAME]){double ss=0;for(int j=0;j<FRAME;j++){e[j]=(float)t[j]-p[j];ss+=(double)e[j]*e[j];}return(float)sqrt(ss/FRAME);}
static void pred_factor(const QC*q1,const Cache*c1,const EnergyCube*ec,const ShapeCube*sc,const uint8_t*in,const float*fun,float out[FRAME],float *gout){float p1[FRAME];predq(q1,c1,in,fun,p1);float g=epred(ec,in,fun);for(int j=0;j<FRAME;j++){float v=p1[j]+g*spred1(sc,c1,j);if(v<.001f)v=.001f;if(v>.999f)v=.999f;out[j]=v;}if(gout)*gout=g;}

typedef struct{unsigned long long n;double g;} GStat;
static void eval_factor(const FC*fc,const QC*q1,const EnergyCube*ec,const ShapeCube*sc,int N,uint64_t seed,int ab,const char*tag){RNG r={seed};Game g;init(&g,ri(&r,7));Pilot po={0};uint8_t a[FRAME],t[FRAME];float fun[FD],p[FRAME];Cache c;M m={0};GStat ga={0},gm={0},gr={0},gl={0},gc={0};for(int i=0;i<N;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);int ev=step(&g,ac);render(&g,t);fw(fc,ac,fun);if(ab==1)memset(fun,0,sizeof(fun));else if(ab==2)for(int k=0;k<FD;k++)fun[k]=-fun[k];cache(a,fun,&c);float gg=0;pred_factor(q1,&c,ec,sc,a,fun,p,&gg);if(ab==3){for(int j=0;j<FRAME;j++){float p1[FRAME];(void)p1;/* handled below by direct zeroing impossible here */}}
    madd(&m,a,t,p,ev);GStat*arr[5]={&ga,&gm,&gr,&gl,&gc};int use[5]={1,(ev&EV_MOVE)!=0,(ev&EV_ROT)!=0,(ev&EV_LOCK)!=0,(ev&EV_CLEAR)!=0};for(int z=0;z<5;z++)if(use[z]){arr[z]->n++;arr[z]->g+=gg;}}
  mp(tag,&m);printf("[%s gate] all=%.4f move=%.4f rot=%.4f lock=%.4f clear=%.4f\n",tag,ga.g/(ga.n?ga.n:1),gm.g/(gm.n?gm.n:1),gr.g/(gr.n?gr.n:1),gl.g/(gl.n?gl.n:1),gc.g/(gc.n?gc.n:1));}
