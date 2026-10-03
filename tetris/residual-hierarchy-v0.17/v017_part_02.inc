  for(int k=0;k<FD;k++){
    float e=t[k]-p[k];
    c->w[ac][k]+=lr*e;
    if(c->w[ac][k]>12.f)c->w[ac][k]=12.f;
    if(c->w[ac][k]<-12.f)c->w[ac][k]=-12.f;
    c->writes++;
  }
}
static void fw(const FC*c,int ac,float q[FD]){double n=0;for(int k=0;k<FD;k++){q[k]=fsig(c->w[ac][k]);n+=q[k]*q[k];}n=sqrt(n);if(n<1e-9)n=1;for(int k=0;k<FD;k++)q[k]/=(float)n;}
static uint32_t fh(const float*q,int salt){uint32_t h=0x9e3779b9u^(uint32_t)salt*0x85ebca6bu;for(int p=0;p<8;p++){double s=0;for(int k=0;k<FD;k++)s+=((mix((uint32_t)(k*131+p*977+17))&1)?1.:-1.)*q[k];h=mix(h^((uint32_t)(s>0)+0x100u*(p+1)));}return h;}
/* Cube 2: function-wave base dynamics + residual cube. */
#define RBITS 20
#define RSZ (1u<<RBITS)
#define RMASK (RSZ-1u)
typedef struct{float*w[BR];}QC;typedef struct{uint32_t a[BR][FRAME];}Cache;
static void qi(QC*q){for(int b=0;b<BR;b++){q->w[b]=calloc(RSZ,sizeof(float));if(!q->w[b])exit(2);}}
static void qf(QC*q){for(int b=0;b<BR;b++)free(q->w[b]);}
static uint32_t patch3(const uint8_t*f,int x,int y){uint32_t v=0,b=0;for(int pl=0;pl<2;pl++)for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){int xx=x+dx,yy=y+dy;uint32_t bit=(xx<0||xx>=W||yy<0||yy>=H)?1u:f[pl*CELLS+yy*W+xx];v|=bit<<b++;}return v;}
static uint32_t row2(const uint8_t*f,int y){uint32_t a=0,b=0;for(int pl=0;pl<2;pl++)for(int x=0;x<W;x++)a|=(uint32_t)f[pl*CELLS+y*W+x]<<b++;uint32_t c=0,d=0;if(y>0)for(int pl=0;pl<2;pl++)for(int x=0;x<W;x++)c|=(uint32_t)f[pl*CELLS+(y-1)*W+x]<<d++;return mix(a)^mix(c+0x13579u);}
static uint32_t col5(const uint8_t*f,int x,int y){uint32_t v=0,b=0;for(int pl=0;pl<2;pl++)for(int dy=-2;dy<=2;dy++){int yy=y+dy;uint32_t bit=(yy<0||yy>=H)?1u:f[pl*CELLS+yy*W+x];v|=bit<<b++;}return v;}
static uint32_t prev16(const uint8_t*f){uint32_t v=0;for(int k=0;k<16;k++)v|=(uint32_t)f[400+k]<<k;return v;}
static uint32_t top_hash(const uint8_t*f){uint32_t h=1;for(int y=0;y<6;y++)for(int x=0;x<W;x++)h=mix(h^((uint32_t)f[y*W+x]+3u*f[CELLS+y*W+x]+13u*x+67u*y));return h;}
static uint32_t bot_hash(const uint8_t*f){uint32_t h=7;for(int y=H-5;y<H;y++)for(int x=0;x<W;x++)h=mix(h^((uint32_t)f[y*W+x]+17u*x+73u*y));return h;}
static void cache(const uint8_t*f,const float*fun,Cache*c){uint32_t F[BR];for(int b=0;b<BR;b++)F[b]=fh(fun,b+11);uint32_t pv=prev16(f),th=top_hash(f),bh=bot_hash(f);for(int j=0;j<FRAME;j++){if(j<CELLS*2){int plane=j/CELLS,k=j%CELLS,x=k%W,y=k/W;uint32_t p=patch3(f,x,y),r=row2(f,y),cl=col5(f,x,y);c->a[0][j]=mix(F[0]^p^(uint32_t)(plane*0x51ed2705u))&RMASK;c->a[1][j]=mix(F[1]^r^(uint32_t)(plane*0x9e3779b9u))&RMASK;c->a[2][j]=mix(F[2]^cl^mix(pv+0x10001u*plane))&RMASK;}else{uint32_t oi=(uint32_t)(j-400);c->a[0][j]=mix(F[0]^pv^oi*0x9e3779b9u)&RMASK;c->a[1][j]=mix(F[1]^th^oi*0x85ebca6bu)&RMASK;c->a[2][j]=mix(F[2]^bh^pv^oi*0xc2b2ae35u)&RMASK;}}}
static void funcbase(const uint8_t*in,const float*fun,float*out){for(int j=0;j<FRAME;j++)out[j]=(float)in[j];for(int j=CELLS;j<CELLS*2;j++)out[j]=0;double ww[25],sum=0;for(int k=0;k<25;k++){double x=fun[k];if(x<0)x=0;ww[k]=pow(x,10.0);sum+=ww[k];}if(sum<1e-16){for(int j=CELLS;j<CELLS*2;j++)out[j]=in[j];return;}for(int y=0;y<H;y++)for(int x=0;x<W;x++)if(in[CELLS+y*W+x])for(int dy=-2;dy<=2;dy++)for(int dx=-2;dx<=2;dx++){int xx=x+dx,yy=y+dy;if(xx<0||xx>=W||yy<0||yy>=H)continue;float p=(float)(ww[(dy+2)*5+dx+2]/sum);int j=CELLS+yy*W+xx;out[j]=1.f-(1.f-out[j])*(1.f-p);}}
static void predq(const QC*q,const Cache*c,const uint8_t*in,const float*fun,float*p){funcbase(in,fun,p);for(int j=0;j<FRAME;j++){float r=0;for(int b=0;b<BR;b++)r+=q->w[b][c->a[b][j]];p[j]+=r/BR;if(p[j]<.001f)p[j]=.001f;if(p[j]>.999f)p[j]=.999f;}}
static void trainq(QC*q,const Cache*c,const uint8_t*in,const float*fun,const uint8_t*t){float p[FRAME];predq(q,c,in,fun,p);for(int j=0;j<FRAME;j++){float e=(float)t[j]-p[j],d=.24f*e/BR;for(int b=0;b<BR;b++){float*w=&q->w[b][c->a[b][j]];*w+=d;if(*w>1.5f)*w=1.5f;if(*w<-1.5f)*w=-1.5f;}}}
typedef struct{uint64_t n,ex,bits,cor,tp,fp,fn,evn[5],eve[5];}M;static void madd(M*m,const uint8_t*in,const uint8_t*t,const float*p,int ev){int ex=1;for(int j=0;j<FRAME;j++){int q=p[j]>=.5,y=t[j];m->bits++;m->cor+=q==y;if(q!=y)ex=0;int tc=t[j]!=in[j],pc=q!=in[j];if(pc&&tc)m->tp++;else if(pc&&!tc)m->fp++;else if(!pc&&tc)m->fn++;}m->n++;m->ex+=ex;int fl[5]={EV_MOVE,EV_ROT,EV_LOCK,EV_CLEAR,EV_GAMEOVER};for(int i=0;i<5;i++)if(ev&fl[i]){m->evn[i]++;m->eve[i]+=ex;}}static void mp(const char*s,const M*m){double pr=(m->tp+m->fp)?(double)m->tp/(m->tp+m->fp):0,re=(m->tp+m->fn)?(double)m->tp/(m->tp+m->fn):0,f=(pr+re)?2*pr*re/(pr+re):0;printf("[%s] frame=%.3f bit=%.3f f1=%.3f",s,100.0*m->ex/m->n,100.0*m->cor/m->bits,f);const char*n[5]={"move","rot","lock","clear","over"};for(int i=0;i<5;i++)if(m->evn[i])printf(" %s=%.2f(%llu)",n[i],100.0*m->eve[i]/m->evn[i],(unsigned long long)m->evn[i]);puts("");}
static void eval(const FC*fc,const QC*q,int N,uint64_t seed,int ab,const char*tag){RNG r={seed};Game g;init(&g,ri(&r,7));Pilot po={0};uint8_t a[FRAME],t[FRAME];float fun[FD],pr[FRAME];Cache c;M m={0};for(int i=0;i<N;i++){if(g.game_over){init(&g,ri(&r,7));memset(&po,0,sizeof(po));}render(&g,a);int ac=pol(&g,&po,&r,1);int ev=step(&g,ac);render(&g,t);fw(fc,ac,fun);if(ab==1)memset(fun,0,sizeof(fun));else if(ab==2)for(int k=0;k<FD;k++)fun[k]=-fun[k];else if(ab==3){float x=fun[0];for(int k=0;k<FD-1;k++)fun[k]=fun[k+1];fun[FD-1]=x;}cache(a,fun,&c);predq(q,&c,a,fun,pr);madd(&m,a,t,pr,ev);}mp(tag,&m);}
