#ifndef BPC_RAW_HISTORY_MODEL_H
#define BPC_RAW_HISTORY_MODEL_H
#include <stdint.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Physical addresses and anonymous ports, with no game state types. */
#define RW 15
#define RH 20
#define RN (RW * RH)
#define PORTS 6
#define LAGS 3
#define LEVELS 4
#ifndef GLOBAL_SUPPORT
#define GLOBAL_SUPPORT 1
#endif
typedef struct { uint8_t q[RN]; } Raw;
typedef struct { Raw past[LAGS]; uint8_t memory[PORTS][RN]; int with_memory; } Medium;
/* MODE 0: inherited priority; 1: equal probability pooling control;
   2: all-address additive probability residual, BPC-0 equations.
   Every independent model uses one field and the same 32-byte cell budget. */
#ifndef MODE
#define MODE 2
#endif
/* The raw carrier keeps its identity. The candidate local query omits only
   the target site's current bit; its real XOR change is applied to that bit.
   Previous frames, port traces and the inherited global cache remain. */
#ifndef DELTA
#define DELTA 1
#endif
#ifndef BIND_CURRENT
#define BIND_CURRENT 1
#endif
_Static_assert(DELTA == 0 || DELTA == 1, "unknown target encoding");
_Static_assert(BIND_CURRENT == 0 || BIND_CURRENT == 1, "unknown binding mode");
#ifndef MAX_CELLS
#define MAX_CELLS 10000000u
#endif
#define ETA 0.5
_Static_assert(MODE >= 0 && MODE <= 2, "unknown mode");
typedef struct { uint64_t a, b; uint32_t yes, total; double residual; } Cell;
typedef struct { Cell *table; size_t capacity, used; } Field;
_Static_assert(sizeof(Cell) == 32, "field cell layout changed");

static void require(int ok, const char *what) {
    if (!ok) { fprintf(stderr, "%s\n", what); exit(2); }
}
static uint64_t mix64(uint64_t x) {
    x ^= x >> 30; x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27; x *= UINT64_C(0x94d049bb133111eb);
    return x ^ (x >> 31);
}
static void field_init(Field *f, size_t capacity) {
    f->capacity = capacity; f->used = 0;
    f->table = calloc(capacity, sizeof(*f->table));
    require(f->table != NULL, "field allocation failed");
}
static Cell *find_cell(Field *f, uint64_t a, uint64_t b, int create) {
    size_t i = (size_t)a & (f->capacity - 1);
    while (f->table[i].total) {
        if (f->table[i].a == a && f->table[i].b == b) return &f->table[i];
        i = (i + 1) & (f->capacity - 1);
    }
    if (!create) return NULL;
    if (f->used >= MAX_CELLS) return NULL;
    f->table[i].a = a; f->table[i].b = b; f->used++;
    return &f->table[i];
}
static void field_grow(Field *f) {
    Field next; field_init(&next, f->capacity * 2);
    for (size_t i = 0; i < f->capacity; i++) if (f->table[i].total) {
        Cell *c = find_cell(&next, f->table[i].a, f->table[i].b, 1);
        *c = f->table[i];
    }
    free(f->table); *f = next;
}
static void medium_reset(Medium *m, const Raw *initial, int with_memory) {
    memset(m, 0, sizeof(*m)); m->with_memory = with_memory;
    for (int k = 0; k < LAGS; k++) m->past[k] = *initial;
    if (with_memory) memcpy(m->memory[PORTS-1], initial->q, RN);
}
/* The same XOR law applies to every port and every site. No role decoder. */
static void medium_accept(Medium *m, int port, const Raw *next) {
    if (m->with_memory) for (int i = 0; i < RN; i++)
        m->memory[port][i] ^= m->past[0].q[i] ^ next->q[i];
    for (int k = LAGS-1; k > 0; k--) m->past[k] = m->past[k-1];
    m->past[0] = *next;
}
/* An external observation changes current pixels, without inventing a tick. */
static void medium_input(Medium *m, const Raw *next) {
    if (m->with_memory) for (int i = 0; i < RN; i++)
        m->memory[PORTS-1][i] ^= m->past[0].q[i] ^ next->q[i];
    m->past[0] = *next;
}
static void medium_codes(const Medium *m, uint16_t codes[RN]) {
    for (int i = 0; i < RN; i++) {
        unsigned q = 0;
        for (int k = 0; k < LAGS; k++) q |= (unsigned)m->past[k].q[i] << k;
        if (m->with_memory) for (int p = 0; p < PORTS; p++)
            q |= (unsigned)m->memory[p][i] << (LAGS+p);
        codes[i] = (uint16_t)q;
    }
}
/* A physical support hierarchy: radius 0 shared, then addressed radii 0/1/2.
   Fixed supports are an assumption of this candidate, not learned cognition. */
static void support_key(const uint16_t codes[RN], int site, int act, int level,
                        uint64_t *a, uint64_t *b) {
    int radius = level > 1 ? level-1 : 0;
    uint64_t tag = (uint64_t)(act+1) + (uint64_t)level*8;
    if (level) tag += (uint64_t)(site+1)*64;
    uint64_t x = mix64(tag + UINT64_C(0x193607f24ae95bcd));
    uint64_t y = mix64(tag + UINT64_C(0xda4510937468ef2b));
    int sx = site % RW, sy = site / RW;
    for (int dy = -radius; dy <= radius; dy++) for (int dx = -radius; dx <= radius; dx++) {
        int px = sx+dx, py = sy+dy;
        uint64_t q = (px < 0 || px >= RW || py < 0 || py >= RH) ? 512 : codes[py*RW+px];
        if (BIND_CURRENT && dx == 0 && dy == 0) q &= ~UINT64_C(1);
        x = (x ^ (q+1)) * UINT64_C(0x100000001b3);
        y = (y ^ (q+513)) * UINT64_C(0x9e3779b185ebca87);
    }
    *a = mix64(x); *b = mix64(y);
}
/* Residuals may open a whole-medium support. This is a conditional cache,
   not an inferred object, transition rule, or proof of generalization. */
static void global_key(const uint16_t codes[RN], int act, uint64_t *a, uint64_t *b) {
    uint64_t x = mix64((uint64_t)act + UINT64_C(0x4519a97be16f0d83));
    uint64_t y = mix64((uint64_t)act + UINT64_C(0x8293ceae04512fd7));
    for (int i = 0; i < RN; i++) {
        x = (x ^ (codes[i]+1u)) * UINT64_C(0x100000001b3);
        y = (y ^ (codes[i]+513u)) * UINT64_C(0x9e3779b185ebca87);
    }
    *a = mix64(x); *b = mix64(y);
}
static void global_site_key(uint64_t ga, uint64_t gb, int site, uint64_t *a, uint64_t *b) {
    *a = mix64(ga ^ mix64((uint64_t)site + UINT64_C(0x7603abdce1479801)));
    *b = mix64(gb ^ mix64((uint64_t)site + UINT64_C(0x241e7690abcf8523)));
}
/* Physical supports are enumerated, never ranked. An unseen address has
   zero residual; fixed wave norm includes it. Sigmoid readout and its update
   are an additive logistic probability model, not a new mathematical family. */
static double site_probability(Field *f, const Medium *m, const uint16_t codes[RN],
                               int site, int act, uint64_t ga, uint64_t gb) {
    if (MODE == 0) {
        if (GLOBAL_SUPPORT) {
            uint64_t a,b; global_site_key(ga,gb,site,&a,&b); Cell *c=find_cell(f,a,b,0);
            if(c) return (c->yes+1.0)/(c->total+2.0);
        }
        for(int l=LEVELS-1;l>=0;l--){
            uint64_t a,b; support_key(codes,site,act,l,&a,&b); Cell *c=find_cell(f,a,b,0);
            if(c) return (c->yes+1.0)/(c->total+2.0);
        }
        return DELTA ? 0.0 : (double)m->past[0].q[site];
    }
    double sum=0; int known=0;
    for(int l=0;l<LEVELS+GLOBAL_SUPPORT;l++){
        uint64_t a,b;
        if(l<LEVELS) support_key(codes,site,act,l,&a,&b);
        else global_site_key(ga,gb,site,&a,&b);
        Cell *c=find_cell(f,a,b,0); if(!c)continue; known++;
        sum += MODE==1 ? (c->yes+1.0)/(c->total+2.0) : c->residual;
    }
    if(MODE==1) return known ? sum/known : (DELTA ? 0.0 : (double)m->past[0].q[site]);
    double z=sum/sqrt((double)(LEVELS+GLOBAL_SUPPORT));
    return z>=0 ? 1.0/(1.0+exp(-z)) : exp(z)/(1.0+exp(z));
}
static uint8_t raw_readout(double p, uint8_t current) {
    if (DELTA) return current ^ (uint8_t)(p > 0.5);
    return p == 0.5 ? current : (uint8_t)(p > 0.5);
}
static uint8_t predict_site(Field *f, const Medium *m, const uint16_t codes[RN],
                            int site, int act, uint64_t ga, uint64_t gb) {
    double p=site_probability(f,m,codes,site,act,ga,gb);
    return raw_readout(p, m->past[0].q[site]);
}
static void record_cell(Cell *c,uint8_t truth,double error){
    if(!c)return;
    require(c->total!=UINT32_MAX,"count overflow"); c->yes+=truth; c->total++;
    if(MODE==2)c->residual+=ETA*error/sqrt((double)(LEVELS+GLOBAL_SUPPORT));
}
static void field_observe(Field *f, const Medium *m, int act, const Raw *next) {
    uint16_t codes[RN]; medium_codes(m,codes);
    uint64_t ga=0,gb=0; if(GLOBAL_SUPPORT)global_key(codes,act,&ga,&gb);
    if((f->used+RN*(LEVELS+1))*10>f->capacity*7)field_grow(f);
    for(int i=0;i<RN;i++){
        double p=site_probability(f,m,codes,i,act,ga,gb);
        uint8_t bit=raw_readout(p,m->past[0].q[i]);
        uint8_t truth=next->q[i] ^ (DELTA ? m->past[0].q[i] : 0);
        double e=truth-p; /* Real consequence only; never self confirmation. */
        if(GLOBAL_SUPPORT){
            uint64_t a,b;global_site_key(ga,gb,i,&a,&b);
            record_cell(find_cell(f,a,b,bit!=next->q[i]),truth,e);
        }
        for(int l=0;l<LEVELS;l++){
            uint64_t a,b;support_key(codes,i,act,l,&a,&b);
            record_cell(find_cell(f,a,b,1),truth,e);
        }
    }
}
static void field_predict(Field *f, const Medium *m, int act, Raw *next) {
    uint16_t codes[RN]; medium_codes(m, codes);
    uint64_t ga = 0, gb = 0;
    if (GLOBAL_SUPPORT) global_key(codes, act, &ga, &gb);
    for (int i = 0; i < RN; i++) {
        next->q[i] = predict_site(f, m, codes, i, act, ga, gb);
    }
}
static uint64_t field_digest(const Field *f) {
    uint64_t h = UINT64_C(1469598103934665603);
    for (size_t i = 0; i < f->capacity; i++) if (f->table[i].total) {
        const Cell *c = &f->table[i];
        h ^= mix64(c->a ^ c->b ^ ((uint64_t)c->yes << 32) ^ c->total);
    }
    return h;
}
static uint64_t field_bytes_digest(const Field *f) {
    const unsigned char *bytes = (const unsigned char *)f->table;
    uint64_t h = UINT64_C(1469598103934665603);
    for (size_t i = 0; i < f->capacity*sizeof(Cell); i++) {
        h ^= bytes[i]; h *= UINT64_C(1099511628211);
    }
    return h ^ (uint64_t)f->used ^ mix64((uint64_t)f->capacity);
}
static void field_save(const Field *f, const char *path, int with_memory) {
    FILE *fp = fopen(path, "wb"); require(fp != NULL, "cannot save field");
    uint64_t header[5] = {UINT64_C(0x4250435355505031), f->used, (uint64_t)with_memory, LEVELS+GLOBAL_SUPPORT*16, MODE+DELTA*16+BIND_CURRENT*32};
    require(fwrite(header, sizeof(header), 1, fp) == 1, "write header failed");
    for (size_t i = 0; i < f->capacity; i++) if (f->table[i].total)
        require(fwrite(&f->table[i], sizeof(Cell), 1, fp) == 1, "write cell failed");
    require(fclose(fp) == 0, "close failed");
}
static void field_load(Field *f, const char *path, int *with_memory) {
    FILE *fp = fopen(path, "rb"); require(fp != NULL, "cannot load field");
    uint64_t header[5]; require(fread(header, sizeof(header), 1, fp) == 1, "read header failed");
    require(header[0] == UINT64_C(0x4250435355505031) && header[3] == LEVELS+GLOBAL_SUPPORT*16 && header[4] == MODE+DELTA*16+BIND_CURRENT*32 && header[1] <= MAX_CELLS, "field format mismatch");
    size_t cap = 1024; while (cap*7/10 < header[1]+1) cap *= 2;
    field_init(f, cap); *with_memory = (int)header[2];
    for (uint64_t k = 0; k < header[1]; k++) {
        Cell c; require(fread(&c, sizeof(c), 1, fp) == 1 && c.total != 0, "invalid cell");
        require(isfinite(c.residual), "nonfinite residual");
        *find_cell(f, c.a, c.b, 1) = c;
    }
    require(fgetc(fp) == EOF, "unexpected field data"); fclose(fp);
}
#endif
