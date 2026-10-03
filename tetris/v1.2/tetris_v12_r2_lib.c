#include "tetris_v08_common.h"

#define OUT (CELLS*2+PREVIEW)
#define LRAD 2
#define LP 18
#define LSZ (1u<<LP)
#define LMASK (LSZ-1u)
#define PRP 14
#define PSZ (1u<<PRP)
#define PMASK (PSZ-1u)
#define LRL .20f
#define GL .95f
#define LRP .15f
#define GP 1.05f

typedef struct{float *w;unsigned long long writes;}LocalR;
typedef struct{float *w;unsigned long long writes;}PairR;
static uint64_t hh(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static uint8_t cval(const uint8_t*f,int x,int y){if(x<0||x>=W||y<0||y>=H)return 4;return(uint8_t)(f[y*W+x]|(f[CELLS+y*W+x]<<1));}
static void li(LocalR*m){memset(m,0,sizeof(*m));m->w=calloc((size_t)LRAD*LSZ*2,sizeof(float));if(!m->w){fprintf(stderr,"alloc local\n");exit(2);}}
static void lf(LocalR*m){free(m->w);}
static void pi(PairR*m){memset(m,0,sizeof(*m));m->w=calloc((size_t)PSZ*OUT,sizeof(float));if(!m->w){fprintf(stderr,"alloc pair\n");exit(2);}}
static void pf(PairR*m){free(m->w);}
static uint32_t la(const uint8_t*f,int cell,int plane,int r,int shift){int x=cell%W,y=cell/W;uint64_t h=0x84222325cbf29ce4ULL^(uint64_t)(r+1)*0x9e37ULL^(uint64_t)(plane+1)*0x1656ULL;for(int dy=-r;dy<=r;dy++)for(int dx=-r;dx<=r;dx++)h=hh(h^((uint64_t)cval(f,x+dx,y+dy)+17u*(dx+r+1)+67u*(dy+r+1)));return((uint32_t)h+(uint32_t)shift)&LMASK;}
static uint16_t p16(const uint8_t*f){uint16_t v=0;for(int k=0;k<PREVIEW;k++)v|=(uint16_t)(f[CELLS*2+k]&1u)<<k;return v;}
static uint32_t pa(const uint8_t*f,int cell,int shift){int x=cell%W,y=cell/W;uint64_t h=0x1234fedcba987654ULL;for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++)h=hh(h^((uint64_t)cval(f,x+dx,y+dy)+13u*(dx+2)+53u*(dy+2)));h=hh(h^((uint64_t)p16(f)<<19));return((uint32_t)h+(uint32_t)shift)&PMASK;}
static int ptoks(const uint8_t*f,uint16_t out[CELLS]){int n=0;for(int i=0;i<CELLS;i++){uint16_t a=(uint16_t)pa(f,i,0);int seen=0;for(int k=0;k<n;k++)if(out[k]==a){seen=1;break;}if(!seen)out[n++]=a;}return n;}
static void bp(const Medium*b,const uint8_t*f,float p[OUT]){uint8_t c[CELLS];for(int i=0;i<CELLS;i++)c[i]=(uint8_t)(f[i]|(f[CELLS+i]<<1));for(int i=0;i<CELLS;i++){p[i]=prob(b,c,i,0);p[CELLS+i]=prob(b,c,i,1);}for(int j=CELLS*2;j<OUT;j++)p[j]=(float)f[j];}
static void addlocal(const LocalR*l,const uint8_t*f,float p[OUT],int mode){if(mode==1)return;for(int cell=0;cell<CELLS;cell++)for(int pl=0;pl<2;pl++){float z=0;for(int r=1;r<=LRAD;r++){int sh=mode==3?71:0;float v=l->w[((size_t)(r-1)*LSZ+la(f,cell,pl,r,sh))*2+pl];z+=v;}z/=LRAD;if(mode==2)z=-z;p[pl*CELLS+cell]=clampf1(p[pl*CELLS+cell]+GL*z,.001f,.999f);}}
static void addpair(const PairR*m,const uint8_t*f,float p[OUT],int mode){if(mode==1)return;uint16_t aa[CELLS];int n=ptoks(f,aa);float nm=1.f/sqrtf((float)(n?n:1));for(int j=0;j<OUT;j++){float z=0;for(int k=0;k<n;k++){uint32_t a=((uint32_t)aa[k]+(mode==3?97:0))&PMASK;z+=m->w[(size_t)a*OUT+j];}z*=nm;if(mode==2)z=-z;p[j]=clampf1(p[j]+GP*z,.001f,.999f);}}
static void predictv(const Medium*b,const LocalR*l,const PairR*m,const uint8_t*f,int lmode,int pmode,uint8_t*out){float p[OUT];bp(b,f,p);addlocal(l,f,p,lmode);addpair(m,f,p,pmode);for(int j=0;j<OUT;j++)out[j]=(uint8_t)(p[j]>=.5f);}
static void train_localr(const Medium*b,LocalR*l,const uint8_t*f,const uint8_t*t){float p[OUT];bp(b,f,p);for(int cell=0;cell<CELLS;cell++)for(int pl=0;pl<2;pl++){int j=pl*CELLS+cell;float z=0;uint32_t aa[LRAD];for(int r=1;r<=LRAD;r++){aa[r-1]=la(f,cell,pl,r,0);z+=l->w[((size_t)(r-1)*LSZ+aa[r-1])*2+pl];}float y=clampf1(p[j]+GL*z/LRAD,.001f,.999f),e=(float)t[j]-y;if(fabsf(e)<.05f)continue;float d=LRL*e/LRAD;for(int r=1;r<=LRAD;r++){float*w=&l->w[((size_t)(r-1)*LSZ+aa[r-1])*2+pl];*w=clampf1(*w+d,-1.5f,1.5f);l->writes++;}}}
static void train_pair(const Medium*b,const LocalR*l,PairR*m,const uint8_t*f,const uint8_t*t){float p[OUT];bp(b,f,p);addlocal(l,f,p,0);uint16_t aa[CELLS];int n=ptoks(f,aa);float nm=1.f/sqrtf((float)(n?n:1));float *z=calloc(OUT,sizeof(float));if(!z)exit(2);for(int k=0;k<n;k++){float*row=&m->w[(size_t)aa[k]*OUT];for(int j=0;j<OUT;j++)z[j]+=row[j];}for(int j=0;j<OUT;j++){float y=clampf1(p[j]+GP*z[j]*nm,.001f,.999f),e=(float)t[j]-y;if(fabsf(e)<.05f)continue;float d=LRP*e*nm;for(int k=0;k<n;k++){float*w=&m->w[(size_t)aa[k]*OUT+j];*w=clampf1(*w+d,-1.5f,1.5f);m->writes++;}}free(z);}
static int hz(const Game*g){Game q=*g;int h=0,pc=q.pieces;while(h<30&&!q.game_over){game_step(&q,ACT_NONE);h++;if(q.pieces!=pc||q.game_over)break;}return h;}
static void adv(Game*g,int n){for(int i=0;i<n&&!g->game_over;i++)game_step(g,ACT_NONE);}
static int samp(RNG*r,Game*g,Pilot*p){for(int z=0;z<3000;z++){if(g->game_over){game_init(g,rng_i(r,7));memset(p,0,sizeof(*p));}int n=1+rng_i(r,6);for(int k=0;k<n;k++){int a=pilot_action(g,p,r,1);game_step(g,a);if(g->game_over)break;}if(!g->game_over&&hz(g)>=1)return 1;}return 0;}
static void pair(RNG*r,Game*g,Pilot*p,int term,uint8_t*in,uint8_t*tar){for(;;){if(!samp(r,g,p))continue;int h=hz(g);Game q=*g;if(term){adv(&q,h-1);render_bits(&q,in);game_step(&q,ACT_NONE);render_bits(&q,tar);return;}if(h<2)continue;adv(&q,rng_i(r,h-1));render_bits(&q,in);game_step(&q,ACT_NONE);render_bits(&q,tar);return;}}
typedef struct{unsigned long long n,full,board,active,preview,ba;double bit;}S;
static int eqv(const uint8_t*a,const uint8_t*b,int s,int n){for(int i=s;i<s+n;i++)if(a[i]!=b[i])return 0;return 1;}
static void av(S*s,const uint8_t*p,const uint8_t*t){s->n++;s->board+=eqv(p,t,0,CELLS);s->active+=eqv(p,t,CELLS,CELLS);s->preview+=eqv(p,t,CELLS*2,PREVIEW);s->ba+=eqv(p,t,0,CELLS*2);s->full+=eqv(p,t,0,OUT);int c=0;for(int i=0;i<OUT;i++)c+=p[i]==t[i];s->bit+=(double)c/OUT;}
static void ps2(const char*n,S*s){printf("%s n=%llu full=%.2f board=%.2f active=%.2f preview=%.2f ba=%.2f bit=%.3f\n",n,s->n,100.0*s->full/s->n,100.0*s->board/s->n,100.0*s->active/s->n,100.0*s->preview/s->n,100.0*s->ba/s->n,100.0*s->bit/s->n);}
static void ev(const Medium*b,const LocalR*l,const PairR*m,int n,uint64_t seed,int lm,int pm,const char*tag){RNG r={seed};Game g;game_init(&g,rng_i(&r,7));Pilot p={0};S sf={0},st={0},sr={0};uint8_t in[FRAME_BITS],tar[FRAME_BITS],o[OUT];for(int i=0;i<n;i++){pair(&r,&g,&p,0,in,tar);predictv(b,l,m,in,lm,pm,o);av(&sf,o,tar);pair(&r,&g,&p,1,in,tar);predictv(b,l,m,in,lm,pm,o);av(&st,o,tar);if(!samp(&r,&g,&p)){i--;continue;}int h=hz(&g);uint8_t cur[FRAME_BITS];render_bits(&g,cur);Game q=g;adv(&q,h);render_bits(&q,tar);for(int z=0;z<h;z++){predictv(b,l,m,cur,lm,pm,o);for(int j=0;j<OUT;j++)cur[j]=o[j];}av(&sr,cur,tar);}char x[64];snprintf(x,sizeof(x),"%s-fall",tag);ps2(x,&sf);snprintf(x,sizeof(x),"%s-terminal",tag);ps2(x,&st);snprintf(x,sizeof(x),"%s-rec",tag);ps2(x,&sr);}
int v12_hidden_main(int argc,char**argv){int nb=argc>1?atoi(argv[1]):15000,nl=argc>2?atoi(argv[2]):5000,np=argc>3?atoi(argv[3]):5000,ne=argc>4?atoi(argv[4]):400,seeds=argc>5?atoi(argv[5]):1;for(int s=0;s<seeds;s++){printf("=== seed=%d base=%d localR=%d pairR=%d ===\n",s,nb,nl,np);Medium b;med_init(&b);if(0)eval(&b,1,0);train(&b,nb,0x121000ULL+1009*s);LocalR l;li(&l);PairR p;pi(&p);RNG r={0x122000ULL+1301*s};Game g;game_init(&g,rng_i(&r,7));Pilot po={0};uint8_t in[FRAME_BITS],tar[FRAME_BITS];for(int t=0;t<nl;t++){pair(&r,&g,&po,t&1,in,tar);train_localr(&b,&l,in,tar);}for(int t=0;t<np;t++){pair(&r,&g,&po,t&1,in,tar);train_pair(&b,&l,&p,in,tar);}printf("writes base=%llu localR=%llu pairR=%llu\n",b.writes,l.writes,p.writes);ev(&b,&l,&p,ne,0x12E000ULL+1601*s,0,0,"normal");ev(&b,&l,&p,ne,0x12E000ULL+1601*s,1,0,"localOff");ev(&b,&l,&p,ne,0x12E000ULL+1601*s,0,1,"pairOff");ev(&b,&l,&p,ne,0x12E000ULL+1601*s,0,2,"pairFlip");ev(&b,&l,&p,ne,0x12E000ULL+1601*s,0,3,"pairShift");pf(&p);lf(&l);med_free(&b);}return 0;}
