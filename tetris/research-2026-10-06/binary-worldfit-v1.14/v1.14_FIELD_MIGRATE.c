#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define SFCAP 2048
#define ACTS 5

typedef struct{uint64_t key;double yes,total;uint8_t used;}SFCell;
typedef struct{SFCell c[SFCAP];int n;}SharedField;

static uint64_t h64(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static uint64_t primtok(int kind,int a,int b,int c){return h64(((uint64_t)(kind&255)<<48)|((uint64_t)(a&255)<<32)|((uint64_t)(b&255)<<16)|(uint64_t)(c&255));}
static uint64_t wavecollide(uint64_t a,uint64_t b){return h64(a^(h64(b)+0x9e3779b97f4a7c15ULL));}
static uint64_t w3(uint64_t a,uint64_t b,uint64_t c){return wavecollide(a,wavecollide(b,c));}
static uint64_t trel(int dx,int dy){return primtok(3,dx+32,dy+32,0);}
static uint64_t tbit(int b){return primtok(21,b,0,0);}
static uint64_t ta(int a){return wavecollide(trel(64+a,0),tbit(1));}
static uint64_t old_kgauge(int a,int dx,int dy){return wavecollide(ta(a),trel(dx,dy));}
static uint64_t new_selfmap(int a,int dx,int dy){return w3(ta(a),trel(0,0),trel(dx,dy));}

static SFCell* find(SharedField*f,uint64_t k,int create){
  uint32_t j=(uint32_t)(k^(k>>32))&(SFCAP-1u);
  for(int n=0;n<SFCAP;n++,j=(j+1u)&(SFCAP-1u)){
    SFCell*e=&f->c[j];
    if(e->used){if(e->key==k)return e;continue;}
    if(!create)return NULL;
    memset(e,0,sizeof(*e));e->used=1;e->key=k;f->n++;return e;
  }
  return NULL;
}
static int is_old_gauge(uint64_t k){
  for(int a=0;a<ACTS;a++)for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++)
    if(k==old_kgauge(a,dx,dy))return 1;
  return 0;
}
int main(int argc,char**argv){
  if(argc!=3){fprintf(stderr,"usage: %s old_field.bin new_field.bin\n",argv[0]);return 2;}
  SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));
  FILE*in=fopen(argv[1],"rb");if(!in){perror("open input");return 3;}
  if(fread(&old,sizeof(old),1,in)!=1){fclose(in);fprintf(stderr,"short input\n");return 4;}fclose(in);
  for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!is_old_gauge(old.c[i].key)){
    SFCell*d=find(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;
  }
  int moved=0;
  for(int a=0;a<ACTS;a++)for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++){
    SFCell*src=find(&old,old_kgauge(a,dx,dy),0);if(!src)continue;
    uint64_t nk=new_selfmap(a,dx,dy);SFCell*prior=find(&neo,nk,0);
    if(prior && prior->total>0.0){fprintf(stderr,"collision with pre-existing self-map key a=%d d=(%d,%d)\n",a,dx,dy);return 5;}
    SFCell*d=find(&neo,nk,1);d->yes=src->yes;d->total=src->total;moved++;
  }
  FILE*out=fopen(argv[2],"wb");if(!out){perror("open output");return 6;}
  if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);fprintf(stderr,"short output\n");return 7;}fclose(out);
  printf("old_relations=%d new_relations=%d gauge_entries_moved=%d\n",old.n,neo.n,moved);
  return 0;
}
