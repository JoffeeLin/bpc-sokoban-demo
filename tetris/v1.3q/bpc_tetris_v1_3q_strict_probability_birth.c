#include "tetris_v08_common.h"

/* v1.3q: anonymous region relation birth by independent reality validation.
   Uniform 16-bit source/output regions. Every source candidate is trained in an
   isolated v1.2-style sparse relation field, then frozen and tested on new
   experience. A source->output relation matures only when its Beta posterior
   of reducing residual exceeds a fixed task-independent lifecycle boundary.
   No top-k, ranking, named Preview, Lock, Spawn, event or object labels. */
#define OUT (CELLS*2+PREVIEW)
#define LRAD 2
#define LP 18
#define LSZ (1u<<LP)
#define LMASK (LSZ-1u)
#define BB 16
#define NB (OUT/BB)
#define PP 14
#define PSZ (1u<<PP)
#define PMASK (PSZ-1u)
#define LRL .20f
#define GL .95f
#define PRL .15f
#define GP 1.05f
#define MIN_EVID 64
#define MAT_Q .80f
#define MAXREL (NB*NB)

typedef struct{float*w;unsigned long long writes;}LocalR;
typedef struct{float*w;}Candidate;
typedef struct{int sb,ob;float amp;float*w;}Rel;
typedef struct{Rel r[MAXREL];int n;unsigned long long births;}Mature;
static uint64_t hh(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static uint8_t cv(const uint8_t*f,int x,int y){if(x<0||x>=W||y<0||y>=H)return 4;return(uint8_t)(f[y*W+x]|(f[CELLS+y*W+x]<<1));}
static uint16_t b16(const uint8_t*f,int b){uint16_t v=0;for(int k=0;k<BB;k++)v|=(uint16_t)(f[b*BB+k]&1u)<<k;return v;}
static uint32_t la(const uint8_t*f,int cell,int pl,int r){int x=cell%W,y=cell/W;uint64_t h=0x84222325cbf29ce4ULL^(uint64_t)(r+1)*0x9e37ULL^(uint64_t)(pl+1)*0x1656ULL;for(int dy=-r;dy<=r;dy++)for(int dx=-r;dx<=r;dx++)h=hh(h^((uint64_t)cv(f,x+dx,y+dy)+17u*(dx+r+1)+67u*(dy+r+1)));return(uint32_t)h&LMASK;}
static uint32_t pa(const uint8_t*f,int cell,int sb,int shift){int x=cell%W,y=cell/W;uint64_t h=0x1234fedcba987654ULL;for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++)h=hh(h^((uint64_t)cv(f,x+dx,y+dy)+13u*(dx+2)+53u*(dy+2)));h=hh(h^((uint64_t)b16(f,sb)<<19));return((uint32_t)h+(uint32_t)shift)&PMASK;}
static int toks(const uint8_t*f,int sb,uint16_t out[CELLS],int shift){int n=0;for(int i=0;i<CELLS;i++){uint16_t a=(uint16_t)pa(f,i,sb,shift);int seen=0;for(int k=0;k<n;k++)if(out[k]==a){seen=1;break;}if(!seen)out[n++]=a;}return n;}
static void bp(const Medium*b,const uint8_t*f,float p[OUT]){uint8_t c[CELLS];for(int i=0;i<CELLS;i++)c[i]=(uint8_t)(f[i]|(f[CELLS+i]<<1));for(int i=0;i<CELLS;i++){p[i]=prob(b,c,i,0);p[CELLS+i]=prob(b,c,i,1);}for(int j=CELLS*2;j<OUT;j++)p[j]=(float)f[j];}
static void addlocal(const LocalR*l,const uint8_t*f,float p[OUT],int off){if(off)return;for(int cell=0;cell<CELLS;cell++)for(int pl=0;pl<2;pl++){float z=0;for(int r=1;r<=LRAD;r++)z+=l->w[((size_t)(r-1)*LSZ+la(f,cell,pl,r))*2+pl];p[pl*CELLS+cell]=clampf1(p[pl*CELLS+cell]+GL*z/LRAD,.001f,.999f);}}
static void trainlocal(const Medium*b,LocalR*l,const uint8_t*f,const uint8_t*t){float p[OUT];bp(b,f,p);for(int c=0;c<CELLS;c++)for(int pl=0;pl<2;pl++){int j=pl*CELLS+c;float z=0;uint32_t a[LRAD];for(int r=1;r<=LRAD;r++){a[r-1]=la(f,c,pl,r);z+=l->w[((size_t)(r-1)*LSZ+a[r-1])*2+pl];}float y=clampf1(p[j]+GL*z/LRAD,.001f,.999f),e=t[j]-y;if(fabsf(e)<.05f)continue;for(int r=0;r<LRAD;r++){float*w=&l->w[((size_t)r*LSZ+a[r])*2+pl];*w=clampf1(*w+LRL*e/LRAD,-1.5f,1.5f);l->writes++;}}}
static void addcandidate(const Candidate*m,const uint8_t*f,int sb,float p[OUT],int shift){uint16_t a[CELLS];int n=toks(f,sb,a,shift);float nm=1.f/sqrtf((float)(n?n:1));for(int j=0;j<OUT;j++){float z=0;for(int k=0;k<n;k++)z+=m->w[(size_t)a[k]*OUT+j];p[j]=clampf1(p[j]+GP*z*nm,.001f,.999f);}}
static void traincandidate(const Medium*b,const LocalR*l,Candidate*m,const uint8_t*f,const uint8_t*t,int sb){float p[OUT];bp(b,f,p);addlocal(l,f,p,0);uint16_t a[CELLS];int n=toks(f,sb,a,0);float nm=1.f/sqrtf((float)(n?n:1));float*z=calloc(OUT,sizeof(float));if(!z)exit(2);for(int k=0;k<n;k++){float*row=&m->w[(size_t)a[k]*OUT];for(int j=0;j<OUT;j++)z[j]+=row[j];}for(int j=0;j<OUT;j++){float y=clampf1(p[j]+GP*z[j]*nm,.001f,.999f),e=t[j]-y;if(fabsf(e)<.05f)continue;float d=PRL*e*nm;for(int k=0;k<n;k++){float*w=&m->w[(size_t)a[k]*OUT+j];*w=clampf1(*w+d,-1.5f,1.5f);}}free(z);}
static void birth(Mature*m,const Candidate*c,int sb,int ob,float amp){if(m->n>=MAXREL)return;Rel*r=&m->r[m->n++];r->sb=sb;r->ob=ob;r->amp=amp;r->w=calloc((size_t)PSZ*BB,sizeof(float));if(!r->w)exit(2);int s=ob*BB;for(unsigned a=0;a<PSZ;a++)for(int k=0;k<BB;k++)r->w[(size_t)a*BB+k]=c->w[(size_t)a*OUT+s+k];m->births++;}
static void freemature(Mature*m){for(int i=0;i<m->n;i++)free(m->r[i].w);memset(m,0,sizeof(*m));}
static void addmature(const Mature*m,const uint8_t*f,float p[OUT],int mode){if(mode==1)return;for(int ri=0;ri<m->n;ri++){const Rel*r=&m->r[ri];uint16_t a[CELLS];int n=toks(f,r->sb,a,mode==3?97:0);float nm=r->amp/sqrtf((float)(n?n:1));int s=r->ob*BB;for(int k=0;k<BB;k++){float z=0;for(int q=0;q<n;q++)z+=r->w[(size_t)a[q]*BB+k];if(mode==2)z=-z;p[s+k]=clampf1(p[s+k]+GP*z*nm,.001f,.999f);}}}
static void pred(const Medium*b,const LocalR*l,const Mature*m,const uint8_t*f,int lm,int mm,uint8_t*out){float p[OUT];bp(b,f,p);addlocal(l,f,p,lm);addmature(m,f,p,mm);for(int j=0;j<OUT;j++)out[j]=(uint8_t)(p[j]>=.5f);}
static int hz(const Game*g){Game q=*g;int h=0,pc=q.pieces;while(h<30&&!q.game_over){game_step(&q,ACT_NONE);h++;if(q.pieces!=pc||q.game_over)break;}return h;}static void adv(Game*g,int n){for(int i=0;i<n&&!g->game_over;i++)game_step(g,ACT_NONE);}static int samp(RNG*r,Game*g,Pilot*p){for(int z=0;z<3000;z++){if(g->game_over){game_init(g,rng_i(r,7));memset(p,0,sizeof(*p));}int n=1+rng_i(r,6);for(int k=0;k<n;k++){int a=pilot_action(g,p,r,1);game_step(g,a);if(g->game_over)break;}if(!g->game_over&&hz(g)>=1)return 1;}return 0;}static void pairx(RNG*r,Game*g,Pilot*p,int term,uint8_t*in,uint8_t*tar){for(;;){if(!samp(r,g,p))continue;int h=hz(g);Game q=*g;if(term){adv(&q,h-1);render_bits(&q,in);game_step(&q,ACT_NONE);render_bits(&q,tar);return;}if(h<2)continue;adv(&q,rng_i(r,h-1));render_bits(&q,in);game_step(&q,ACT_NONE);render_bits(&q,tar);return;}}
static int block_exact_f(const float*p,const uint8_t*t,int ob){int s=ob*BB;for(int k=0;k<BB;k++)if((p[s+k]>=.5f)!=(t[s+k]!=0))return 0;return 1;}
static void mature_source(const Medium*b,const LocalR*l,Mature*m,int sb,int nt,int nv,uint64_t seed){
  Candidate c={calloc((size_t)PSZ*OUT,sizeof(float))};if(!c.w)exit(2);
  RNG r={seed};Game g;game_init(&g,rng_i(&r,7));Pilot p={0};uint8_t in[FRAME_BITS],tar[FRAME_BITS];
  for(int t=0;t<nt;t++){pairx(&r,&g,&p,rng_i(&r,2),in,tar);traincandidate(b,l,&c,in,tar,sb);}
  unsigned ok[NB]={0},bad[NB]={0};
  for(int t=0;t<nv;t++){
    pairx(&r,&g,&p,rng_i(&r,2),in,tar);float base[OUT],pc[OUT];bp(b,in,base);addlocal(l,in,base,0);memcpy(pc,base,sizeof(base));addcandidate(&c,in,sb,pc,0);
    for(int ob=0;ob<NB;ob++){
      if(block_exact_f(base,tar,ob))continue;
      if(block_exact_f(pc,tar,ob))ok[ob]++;else bad[ob]++;
    }
  }
  printf("src=%d mature",sb);
  for(int ob=0;ob<NB;ob++){unsigned n=ok[ob]+bad[ob];float q=(ok[ob]+1.f)/(n+2.f);if(n>=MIN_EVID&&q>=MAT_Q){birth(m,&c,sb,ob,q);printf(" %d:q%.2f/%u",ob,q,n);}}
  puts("");free(c.w);
}
typedef struct{unsigned long long n,full,board,active,preview,ba;double bit;}S;static int eq(const uint8_t*a,const uint8_t*b,int s,int n){for(int i=s;i<s+n;i++)if(a[i]!=b[i])return 0;return 1;}static void addS(S*s,const uint8_t*p,const uint8_t*t){s->n++;s->board+=eq(p,t,0,CELLS);s->active+=eq(p,t,CELLS,CELLS);s->preview+=eq(p,t,CELLS*2,PREVIEW);s->ba+=eq(p,t,0,CELLS*2);s->full+=eq(p,t,0,OUT);int c=0;for(int i=0;i<OUT;i++)c+=p[i]==t[i];s->bit+=(double)c/OUT;}static void ps(const char*n,S*s){printf("%s n=%llu full=%.2f board=%.2f active=%.2f preview=%.2f ba=%.2f bit=%.3f
",n,s->n,100.0*s->full/s->n,100.0*s->board/s->n,100.0*s->active/s->n,100.0*s->preview/s->n,100.0*s->ba/s->n,100.0*s->bit/s->n);}
static void evalm(const Medium*b,const LocalR*l,const Mature*m,int ne,uint64_t seed,int mm,const char*tag){RNG r={seed};Game g;game_init(&g,rng_i(&r,7));Pilot p={0};S sf={0},st={0},sr={0};uint8_t in[FRAME_BITS],tar[FRAME_BITS],o[OUT];for(int i=0;i<ne;i++){pairx(&r,&g,&p,0,in,tar);pred(b,l,m,in,0,mm,o);addS(&sf,o,tar);pairx(&r,&g,&p,1,in,tar);pred(b,l,m,in,0,mm,o);addS(&st,o,tar);if(!samp(&r,&g,&p)){i--;continue;}int h=hz(&g);uint8_t cur[FRAME_BITS];render_bits(&g,cur);Game q=g;adv(&q,h);render_bits(&q,tar);for(int z=0;z<h;z++){pred(b,l,m,cur,0,mm,o);memcpy(cur,o,OUT);}addS(&sr,cur,tar);}char x[64];snprintf(x,sizeof(x),"%s-fall",tag);ps(x,&sf);snprintf(x,sizeof(x),"%s-terminal",tag);ps(x,&st);snprintf(x,sizeof(x),"%s-rec",tag);ps(x,&sr);}
int main(int argc,char**argv){int nb=argc>1?atoi(argv[1]):10000,nl=argc>2?atoi(argv[2]):3000,nt=argc>3?atoi(argv[3]):4000,nv=argc>4?atoi(argv[4]):1200,ne=argc>5?atoi(argv[5]):300,so=argc>6?atoi(argv[6]):0;uint64_t off=(uint64_t)(unsigned)so*1000003ULL;printf("=== v1.3q seed=%d ===
",so);Medium b;med_init(&b);if(0)eval(&b,1,0);train(&b,nb,0x13aa10ULL+off);LocalR l={calloc((size_t)LRAD*LSZ*2,sizeof(float)),0};if(!l.w)exit(2);RNG r={0x13aa20ULL+off};Game g;game_init(&g,rng_i(&r,7));Pilot p={0};uint8_t in[FRAME_BITS],tar[FRAME_BITS];for(int t=0;t<nl;t++){pairx(&r,&g,&p,rng_i(&r,2),in,tar);trainlocal(&b,&l,in,tar);}Mature m={0};for(int sb=0;sb<NB;sb++)mature_source(&b,&l,&m,sb,nt,nv,0x13bb00ULL+off+7919u*(unsigned)sb);printf("mature_relations=%d births=%llu
",m.n,m.births);evalm(&b,&l,&m,ne,0x13cc00ULL+off,0,"normal");evalm(&b,&l,&m,ne,0x13cc00ULL+off,1,"relOff");evalm(&b,&l,&m,ne,0x13cc00ULL+off,2,"relFlip");evalm(&b,&l,&m,ne,0x13cc00ULL+off,3,"relShift");freemature(&m);free(l.w);med_free(&b);return 0;}
