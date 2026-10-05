#include <stdio.h>
#include <stdint.h>
#include <string.h>
#define SFCAP 2048
typedef struct{uint64_t key;double yes,total;uint8_t used;}SFCell;
typedef struct{SFCell c[SFCAP];int n;}SharedField;
static uint64_t h64(uint64_t x){x^=x>>33;x*=0xff51afd7ed558ccdULL;x^=x>>33;x*=0xc4ceb9fe1a85ec53ULL;x^=x>>33;return x;}
static uint64_t primtok(int kind,int a,int b,int c){return h64(((uint64_t)(kind&255)<<48)|((uint64_t)(a&255)<<32)|((uint64_t)(b&255)<<16)|(uint64_t)(c&255));}
static uint64_t wavecollide(uint64_t a,uint64_t b){return h64(a^(h64(b)+0x9e3779b97f4a7c15ULL));}
static uint64_t trel(int dx,int dy){return primtok(3,dx+32,dy+32,0);}
static uint64_t tchan(int a,int b){return primtok(8,a,b,0);}
static uint64_t old_kspawn(int dx,int dy){return wavecollide(tchan(2,0),trel(dx,dy));}
static uint64_t new_kspawn(int rawdx,int rawdy){return trel(rawdx,rawdy);}
static SFCell* find(SharedField*f,uint64_t k,int create){uint32_t j=(uint32_t)(k^(k>>32))&(SFCAP-1u);for(int n=0;n<SFCAP;n++,j=(j+1u)&(SFCAP-1u)){SFCell*e=&f->c[j];if(e->used){if(e->key==k)return e;continue;}if(!create)return NULL;memset(e,0,sizeof(*e));e->used=1;e->key=k;f->n++;return e;}return NULL;}
static int old_spawn_key(uint64_t k){for(int dy=-8;dy<=8;dy++)for(int dx=-8;dx<=8;dx++)if(k==old_kspawn(dx,dy))return 1;return 0;}
int main(void){SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));FILE*in=fopen("/mnt/data/bpc_best_worldfit/v055b_field.bin","rb");if(!in)return 2;if(fread(&old,sizeof(old),1,in)!=1){fclose(in);return 3;}fclose(in);for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!old_spawn_key(old.c[i].key)){SFCell*d=find(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;}for(int dy=-8;dy<=8;dy++)for(int dx=-8;dx<=8;dx++){SFCell*src=find(&old,old_kspawn(dx,dy),0);if(!src)continue;SFCell*dst=find(&neo,new_kspawn(dx-11,dy),1);dst->yes=src->yes;dst->total=src->total;}FILE*out=fopen("/mnt/data/bpc_best_worldfit/v068_field.bin","wb");if(!out)return 4;if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);return 5;}fclose(out);printf("old=%d new=%d\n",old.n,neo.n);return 0;}