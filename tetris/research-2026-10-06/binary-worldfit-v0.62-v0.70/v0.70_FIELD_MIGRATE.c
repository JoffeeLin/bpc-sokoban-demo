#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "BPC_Binary_WorldFit_v0.69_direct_action_route_core.c"
static int rel_to_dy(int r){return r==0?0:(r==1?1:-1);}
static uint64_t new_cresp(int dy,int out){return wavecollide(trel(0,dy),teffect(out));}
static uint64_t new_pair(int dy1,int dy2,int effect){uint64_t a=trel(0,dy1),b=trel(0,dy2);if(a>b){uint64_t t=a;a=b;b=t;}return wavecollide(w3(a,b,teffect(effect)),teffect(effect));}
static uint64_t new_joint(int dy){return w3(trel(0,dy),teffect(2),teffect(1));}
static int is_old_addr_key(uint64_t k){for(int r=0;r<3;r++){for(int o=0;o<3;o++)if(k==kcresp(r,o))return 1;if(k==kjointeff(r))return 1;}for(int r1=0;r1<3;r1++)for(int r2=r1+1;r2<3;r2++)for(int e=0;e<3;e++)if(k==kpairgate(r1,r2,e))return 1;return 0;}
int main(void){SharedField old,neo;memset(&old,0,sizeof(old));memset(&neo,0,sizeof(neo));FILE*in=fopen("/mnt/data/bpc_best_worldfit/v069_field.bin","rb");if(!in)return 2;if(fread(&old,sizeof(old),1,in)!=1){fclose(in);return 3;}fclose(in);for(int i=0;i<SFCAP;i++)if(old.c[i].used&&!is_old_addr_key(old.c[i].key)){SFCell*d=sffind(&neo,old.c[i].key,1);d->yes=old.c[i].yes;d->total=old.c[i].total;}
for(int r=0;r<3;r++){int dy=rel_to_dy(r);for(int o=0;o<3;o++){SFCell*s=sffind(&old,kcresp(r,o),0);if(s){SFCell*d=sffind(&neo,new_cresp(dy,o),1);d->yes=s->yes;d->total=s->total;}}SFCell*j=sffind(&old,kjointeff(r),0);if(j){SFCell*d=sffind(&neo,new_joint(dy),1);d->yes=j->yes;d->total=j->total;}}
for(int r1=0;r1<3;r1++)for(int r2=r1+1;r2<3;r2++)for(int e=0;e<3;e++){SFCell*s=sffind(&old,kpairgate(r1,r2,e),0);if(s){SFCell*d=sffind(&neo,new_pair(rel_to_dy(r1),rel_to_dy(r2),e),1);d->yes=s->yes;d->total=s->total;}}
FILE*out=fopen("/mnt/data/bpc_best_worldfit/v070_field.bin","wb");if(!out)return 4;if(fwrite(&neo,sizeof(neo),1,out)!=1){fclose(out);return 5;}fclose(out);printf("old=%d new=%d\n",old.n,neo.n);return 0;}