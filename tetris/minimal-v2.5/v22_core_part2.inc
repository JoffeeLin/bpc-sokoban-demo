static void env_rot_single(int si,uint8_t in[SLOTS],uint8_t out[SLOTS]){
  memset(in,0,SLOTS);memset(out,0,SLOTS);in[si]=1;int sx,sy,ox,oy;lunidx(si,&sx,&sy);rr(sx,sy,&ox,&oy);out[lidx(ox,oy)]=1;
}
static void observe_rot(Rot*r,const uint8_t in[SLOTS],const uint8_t out[SLOTS]){for(int si=0;si<SLOTS;si++)if(in[si])for(int oi=0;oi<SLOTS;oi++){uint32_t*p=out[oi]?&r->o[si][oi]:&r->z[si][oi];(*p)++;}}
static void train_rot(Rot*r,int ep){uint8_t in[SLOTS],out[SLOTS];for(int e=0;e<ep;e++)for(int si=0;si<SLOTS;si++){env_rot_single(si,in,out);observe_rot(r,in,out);}}
static float rp(const Rot*r,int si,int oi){uint32_t z=r->z[si][oi],o=r->o[si][oi];return((float)o+.5f)/((float)(z+o)+1.f);}
static void train_rblock(const Rot*r,RotBlock*b,int ep){(void)r;(void)b;(void)ep;}
static float rot_go(const Rot*r,const RotBlock*b,int si,const uint8_t world[SLOTS]){(void)b;double C=1.0,mass=0.0;for(int oi=0;oi<SLOTS;oi++){float q=rp(r,si,oi);mass+=q;if(world[oi])C*=1.0-(double)q;}if(mass<0.5)return 0.f;if(C<0)C=0;if(C>1)C=1;return(float)C;}
static void rot_local_base(const Rot*r,const uint8_t in[SLOTS],float out[SLOTS]){for(int oi=0;oi<SLOTS;oi++){double miss=1;int any=0;for(int si=0;si<SLOTS;si++)if(in[si]){any=1;miss*=1.0-rp(r,si,oi);}out[oi]=any?(float)(1.0-miss):0.f;}}
typedef struct{float w[2][2];}Couple;
static void train_couple(Couple*c,int ep){float lr=.05f;for(int e=0;e<ep;e++)for(int blocked=0;blocked<2;blocked++){float C=blocked?0.f:1.f,f[2]={C,1.f-C},t[2]={blocked?0.f:1.f,blocked?1.f:0.f};for(int o=0;o<2;o++){float y=c->w[o][0]*f[0]+c->w[o][1]*f[1],er=t[o]-y;for(int k=0;k<2;k++)c->w[o][k]+=lr*er*f[k];}}}
static void cg(const Couple*c,float C,float*gm,float*gl){*gm=c->w[0][0]*C+c->w[0][1]*(1-C);*gl=c->w[1][0]*C+c->w[1][1]*(1-C);if(*gm<0)*gm=0;if(*gm>1)*gm=1;if(*gl<0)*gl=0;if(*gl>1)*gl=1;}
typedef struct{uint32_t z[PREV][N],o[PREV][N];}Spawn;typedef struct{uint32_t z[N],o[N];}SpawnPivot;
static void env_spawn_from_preview(const uint8_t prev[PREV],uint8_t active[N],uint8_t pivot[N]){
  memset(active,0,N);memset(pivot,0,N);for(int sy=0;sy<4;sy++)for(int sx=0;sx<4;sx++)if(prev[sy*4+sx]){int x=3+sx,y=-1+sy;if(y>=0&&y<H&&x>=0&&x<W)active[y*W+x]=1;}pivot[4]=1;
}
static void observe_spawn(Spawn*s,const uint8_t prev[PREV],const uint8_t active[N]){for(int si=0;si<PREV;si++)if(prev[si])for(int oi=0;oi<N;oi++){uint32_t*p=active[oi]?&s->o[si][oi]:&s->z[si][oi];(*p)++;}}
static void train_spawn(Spawn*s,int ep){uint8_t prev[PREV],active[N],pivot[N];for(int e=0;e<ep;e++)for(int si=0;si<PREV;si++){memset(prev,0,PREV);prev[si]=1;env_spawn_from_preview(prev,active,pivot);observe_spawn(s,prev,active);}}
static float sp(const Spawn*s,int si,int oi){uint32_t z=s->z[si][oi],o=s->o[si][oi];return((float)o+.5f)/((float)(z+o)+1.f);}
static void spawn_field(const Spawn*s,const uint8_t prev[PREV],float out[N]){for(int oi=0;oi<N;oi++){double miss=1.0;int any=0;for(int si=0;si<PREV;si++)if(prev[si]){any=1;miss*=1.0-sp(s,si,oi);}out[oi]=any?(float)(1.0-miss):0.f;}}
static float spawn_carrier(const Spawn*s,const uint8_t prev[PREV],const uint8_t world[N]){double C=1.0;for(int si=0;si<PREV;si++)if(prev[si])for(int oi=0;oi<N;oi++)if(world[oi])C*=1.0-(double)sp(s,si,oi);if(C<0)C=0;if(C>1)C=1;return(float)C;}
