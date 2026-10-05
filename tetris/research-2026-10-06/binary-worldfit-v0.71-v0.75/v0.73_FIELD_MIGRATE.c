#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "BPC_Binary_WorldFit_v0.72_physical_consequence_core.c"
static uint64_t birth_wave(void){return wavecollide(trel(0,1),tstate(4));}
static uint64_t death_wave(void){return wavecollide(trel(0,0),tstate(0));}
static uint64_t new_cresp(int dy,int out){uint64_t e=out==1?birth_wave():death_wave();return wavecollide(trel(0,dy),e);}
static uint64_t new_pair(int dy1,int dy2){uint64_t a=trel(0,dy1),b=trel(0,dy2),e=birth_wave();if(a>b){uint64_t t=a;a=b;b=t;}return wavecollide(w3(a,b,e),e);}
static uint64_t new_joint(int dy){return w3(trel(0,dy),death_wave(),birth_wave());}
static int is_old(uint64_t k){for(int dy=-1;dy<=1;dy++){for(int o=0;o<3;o++)if(k==kcresp(dy,o))return 1;if(k==kjointeff(dy))return 1;}for(int d1=-1;d1<=1;d1++)for(int d2=d1+1;d2<=1;d2++)for(int e=0;e<3;e++)if(k==kpairgate(d1,d2,e))return 1;return 0;}
int main(void){SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));FILE*in=fopen("/mnt/data/bpc_best_worldfit/v072_field.bin","rb");if(!in)return 2;if(fread(&old,sizeof(old),1,in)!=1){fclose(in);return 3;}fclose(in);for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!is_old(old.c[i].key)){SFCell*d=sffind(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;}
for(int dy=-1;dy<=1;dy++)for(int o=1;o<=2;o++){SFCell*s=sffind(&old,kcresp(dy,o),0);if(s){SFCell*d=sffind(&neo,new_cresp(dy,o),1);d->yes=s->yes;d->total=s->total;}}
for(int dy=-1;dy<=1;dy++){SFCell*s=sffind(&old,kjointeff(dy),0);if(s){SFCell*d=sffind(&neo,new_joint(dy),1);d->yes=s->yes;d->total=s->total;}}
for(int d1=-1;d1<=1;d1++)for(int d2=d1+1;d2<=1;d2++){SFCell*s=sffind(&old,kpairgate(d1,d2,1),0);if(s){SFCell*d=sffind(&neo,new_pair(d1,d2),1);d->yes=s->yes;d->total=s->total;}}
FILE*out=fopen("/mnt/data/bpc_best_worldfit/v073_field.bin","wb");if(!out)return 4;if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);return 5;}fclose(out);printf("old=%d new=%d\n",old.n,neo.n);return 0;}