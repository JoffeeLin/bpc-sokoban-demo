#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "BPC_Binary_WorldFit_v0.73_physical_closure_effects_core.c"
static uint64_t new_compat(int state){return wavecollide(tstate(3),tstate(state));}
static uint64_t new_phys_out(int out){if(out==0)return tstate(3);if(out==1)return wavecollide(trel(0,0),tstate(3));return wavecollide(trel(0,0),tstate(4));}
static uint64_t new_kroute(int a,int out,int c){return w3(ta(a),tfeas(c),new_phys_out(out));}
static uint64_t new_ksplit(int out,int c){uint64_t consequence=out==0?new_phys_out(0):tstate(5);return wavecollide(tfeas(c),consequence);}
static int is_old(uint64_t k,const SharedField*f){for(int s=0;s<3;s++)if(k==kcompat(s))return 1;for(int a=0;a<ACTS;a++)for(int o=0;o<3;o++)for(int c=0;c<2;c++)if(k==kroute(f,a,o,c))return 1;for(int o=0;o<2;o++)for(int c=0;c<2;c++)if(k==ksplit(o,c))return 1;return 0;}
int main(void){SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));FILE*in=fopen("/mnt/data/bpc_best_worldfit/v073_field.bin","rb");if(!in)return 2;if(fread(&old,sizeof(old),1,in)!=1){fclose(in);return 3;}fclose(in);for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!is_old(old.c[i].key,&old)){SFCell*d=sffind(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;}
for(int s=0;s<3;s++){SFCell*x=sffind(&old,kcompat(s),0);if(x){SFCell*d=sffind(&neo,new_compat(s),1);d->yes=x->yes;d->total=x->total;}}
for(int a=0;a<ACTS;a++)for(int o=0;o<3;o++)for(int c=0;c<2;c++){SFCell*x=sffind(&old,kroute(&old,a,o,c),0);if(x){SFCell*d=sffind(&neo,new_kroute(a,o,c),1);d->yes=x->yes;d->total=x->total;}}
for(int o=0;o<2;o++)for(int c=0;c<2;c++){SFCell*x=sffind(&old,ksplit(o,c),0);if(x){SFCell*d=sffind(&neo,new_ksplit(o,c),1);d->yes=x->yes;d->total=x->total;}}
FILE*out=fopen("/mnt/data/bpc_best_worldfit/v074_field.bin","wb");if(!out)return 4;if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);return 5;}fclose(out);printf("old=%d new=%d\n",old.n,neo.n);return 0;}