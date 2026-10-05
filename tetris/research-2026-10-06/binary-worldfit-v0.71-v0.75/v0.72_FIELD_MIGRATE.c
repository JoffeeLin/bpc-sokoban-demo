#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "BPC_Binary_WorldFit_v0.71_dead_vocab_removed_core.c"
static uint64_t phys_route_out(int out){if(out==0)return wavecollide(tproposal(),tdest(3));if(out==1)return wavecollide(trel(0,0),tdest(3));return wavecollide(trel(0,0),tdest(4));}
static uint64_t phys_split_out(int out){return out==0?phys_route_out(0):tdest(5);}
static uint64_t new_kroute(int a,int out,int c){return w3(ta(a),tfeas(c),phys_route_out(out));}
static uint64_t new_ksplit(int out,int c){return wavecollide(tfeas(c),phys_split_out(out));}
static int is_old(uint64_t k,const SharedField*f){for(int a=0;a<ACTS;a++)for(int o=0;o<3;o++)for(int c=0;c<2;c++)if(k==kroute(f,a,o,c))return 1;for(int o=0;o<2;o++)for(int c=0;c<2;c++)if(k==ksplit(o,c))return 1;return 0;}
int main(void){SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));FILE*in=fopen("/mnt/data/bpc_best_worldfit/v070_field.bin","rb");if(!in)return 2;if(fread(&old,sizeof(old),1,in)!=1){fclose(in);return 3;}fclose(in);for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!is_old(old.c[i].key,&old)){SFCell*d=sffind(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;}
for(int a=0;a<ACTS;a++)for(int o=0;o<3;o++)for(int c=0;c<2;c++){SFCell*s=sffind(&old,kroute(&old,a,o,c),0);if(s){SFCell*d=sffind(&neo,new_kroute(a,o,c),1);d->yes=s->yes;d->total=s->total;}}
for(int o=0;o<2;o++)for(int c=0;c<2;c++){SFCell*s=sffind(&old,ksplit(o,c),0);if(s){SFCell*d=sffind(&neo,new_ksplit(o,c),1);d->yes=s->yes;d->total=s->total;}}
FILE*out=fopen("/mnt/data/bpc_best_worldfit/v072_field.bin","wb");if(!out)return 4;if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);return 5;}fclose(out);printf("old=%d new=%d\n",old.n,neo.n);return 0;}