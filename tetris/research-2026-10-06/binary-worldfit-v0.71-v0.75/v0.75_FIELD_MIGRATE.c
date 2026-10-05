#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "BPC_Binary_WorldFit_v0.74_state_collision_core.c"
static uint64_t new_klife(int a,int c){return wavecollide(ta(a),tfeas(c));}
static int is_old_life(uint64_t k){for(int a=0;a<ACTS;a++)for(int c=0;c<2;c++)if(k==klife(a,c))return 1;return 0;}
int main(void){SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));FILE*in=fopen("/mnt/data/bpc_best_worldfit/v074_field.bin","rb");if(!in)return 2;if(fread(&old,sizeof(old),1,in)!=1){fclose(in);return 3;}fclose(in);for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!is_old_life(old.c[i].key)){SFCell*d=sffind(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;}
for(int a=0;a<ACTS;a++)for(int c=0;c<2;c++){SFCell*x=sffind(&old,klife(a,c),0);if(x){SFCell*d=sffind(&neo,new_klife(a,c),1);d->yes=x->yes;d->total=x->total;}}
FILE*out=fopen("/mnt/data/bpc_best_worldfit/v075_field.bin","wb");if(!out)return 4;if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);return 5;}fclose(out);printf("old=%d new=%d\n",old.n,neo.n);return 0;}