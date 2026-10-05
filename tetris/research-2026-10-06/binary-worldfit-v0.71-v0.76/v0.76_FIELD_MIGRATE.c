#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "BPC_Binary_WorldFit_v0.75_action_self_reentry_core.c"
static uint64_t new_kclosure(int dx,int dy){return wavecollide(tstate(2),trel(dx,dy));}
static int is_old(uint64_t k){for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++)if(abs(dx)+abs(dy)==1&&k==kclosure(dx,dy))return 1;return 0;}
int main(void){SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));FILE*in=fopen("/mnt/data/bpc_best_worldfit/v075_field.bin","rb");if(!in)return 2;if(fread(&old,sizeof(old),1,in)!=1){fclose(in);return 3;}fclose(in);for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!is_old(old.c[i].key)){SFCell*d=sffind(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;}for(int dy=-1;dy<=1;dy++)for(int dx=-1;dx<=1;dx++)if(abs(dx)+abs(dy)==1){SFCell*x=sffind(&old,kclosure(dx,dy),0);if(x){SFCell*d=sffind(&neo,new_kclosure(dx,dy),1);d->yes=x->yes;d->total=x->total;}}
FILE*out=fopen("/mnt/data/bpc_best_worldfit/v076_field.bin","wb");if(!out)return 4;if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);return 5;}fclose(out);printf("old=%d new=%d\n",old.n,neo.n);return 0;}