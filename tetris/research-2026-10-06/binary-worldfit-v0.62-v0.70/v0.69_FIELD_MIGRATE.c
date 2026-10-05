#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "BPC_Binary_WorldFit_v0.68_raw_screen_relation_core.c"
static uint64_t knewroute(int a,int out,int c){return w3(ta(a),tfeas(c),troute(out));}
static int is_old_route(const SharedField*f,uint64_t k){for(int a=0;a<ACTS;a++)for(int o=0;o<3;o++)for(int c=0;c<2;c++)if(k==kroute(f,a,o,c))return 1;return 0;}
int main(void){
  SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));
  FILE*in=fopen("/mnt/data/bpc_best_worldfit/v068_field.bin","rb");if(!in)return 2;if(fread(&old,sizeof(old),1,in)!=1){fclose(in);return 3;}fclose(in);
  for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!is_old_route(&old,old.c[i].key)){SFCell*d=sffind(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;}
  for(int a=0;a<ACTS;a++)for(int o=0;o<3;o++)for(int c=0;c<2;c++){
    SFCell*src=sffind(&old,kroute(&old,a,o,c),0);if(!src)continue;SFCell*dst=sffind(&neo,knewroute(a,o,c),1);dst->yes=src->yes;dst->total=src->total;
  }
  FILE*out=fopen("/mnt/data/bpc_best_worldfit/v069_field.bin","wb");if(!out)return 4;if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);return 5;}fclose(out);
  printf("old=%d new=%d\n",old.n,neo.n);return 0;
}