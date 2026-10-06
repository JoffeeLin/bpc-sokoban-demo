#ifndef BPC_BINARY_WORLDFIT_V1_13_API_H
#define BPC_BINARY_WORLDFIT_V1_13_API_H

#include <stdint.h>

#define BPC_SCREEN_W 15
#define BPC_SCREEN_H 20
#define BPC_SCREEN_PIXELS (BPC_SCREEN_W * BPC_SCREEN_H)
#define BPC_ACTIONS 5

typedef struct {
    uint8_t px[BPC_SCREEN_PIXELS];
} BPCFrame;

typedef struct {
    float v[BPC_ACTIONS];
} BPCActionWave;

typedef struct BPCModel BPCModel;

BPCModel* bpc_model_load(const char* path);
void bpc_model_free(BPCModel* model);
void bpc_model_reset(BPCModel* model, const BPCFrame* visible);
void bpc_model_step(BPCModel* model, BPCFrame* visible, const BPCActionWave* action);
int bpc_model_relation_count(const BPCModel* model);

#endif
