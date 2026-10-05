#ifndef BPC_RAW_HISTORY_MODEL_H
#define BPC_RAW_HISTORY_MODEL_H
#include <stdint.h>
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
typedef struct { uint64_t a, b; uint32_t yes, total; } Cell;
typedef struct { Cell *table; size_t capacity, used; } Field;
_Static_assert(sizeof(Cell) == 24, "field cell layout changed");

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
static uint8_t predict_site(Field *f, const Medium *m, const uint16_t codes[RN],
                            int site, int act, uint64_t ga, uint64_t gb) {
    uint8_t value = m->past[0].q[site];
    if (GLOBAL_SUPPORT) {
        uint64_t a, b; global_site_key(ga, gb, site, &a, &b);
        Cell *c = find_cell(f, a, b, 0);
        if (c) {
            uint64_t twice = (uint64_t)c->yes*2;
            return twice == c->total ? value : (uint8_t)(twice > c->total);
        }
    }
    for (int l = LEVELS-1; l >= 0; l--) {
        uint64_t a, b; support_key(codes, site, act, l, &a, &b);
        Cell *c = find_cell(f, a, b, 0);
        if (!c) continue;
        uint64_t twice = (uint64_t)c->yes*2;
        if (twice != c->total) value = (uint8_t)(twice > c->total);
        break;
    }
    return value;
}
static void field_observe(Field *f, const Medium *m, int act, const Raw *next) {
    uint16_t codes[RN]; medium_codes(m, codes);
    uint64_t ga = 0, gb = 0;
    if (GLOBAL_SUPPORT) global_key(codes, act, &ga, &gb);
    if ((f->used + RN*(LEVELS+1))*10 > f->capacity*7) field_grow(f);
    for (int i = 0; i < RN; i++) {
        if (GLOBAL_SUPPORT) {
            uint64_t a, b; global_site_key(ga, gb, i, &a, &b);
            int residual = predict_site(f, m, codes, i, act, ga, gb) != next->q[i];
            Cell *c = find_cell(f, a, b, residual);
            if (c) {
                require(c->total != UINT32_MAX, "count overflow");
                c->yes += next->q[i]; c->total++;
            }
        }
        for (int l = 0; l < LEVELS; l++) {
            uint64_t a, b; support_key(codes, i, act, l, &a, &b);
            Cell *c = find_cell(f, a, b, 1);
            require(c->total != UINT32_MAX, "count overflow");
            c->yes += next->q[i]; c->total++;
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
    uint64_t header[4] = {UINT64_C(0x5241574849535431), f->used, (uint64_t)with_memory, LEVELS+GLOBAL_SUPPORT*16};
    require(fwrite(header, sizeof(header), 1, fp) == 1, "write header failed");
    for (size_t i = 0; i < f->capacity; i++) if (f->table[i].total)
        require(fwrite(&f->table[i], sizeof(Cell), 1, fp) == 1, "write cell failed");
    require(fclose(fp) == 0, "close failed");
}
static void field_load(Field *f, const char *path, int *with_memory) {
    FILE *fp = fopen(path, "rb"); require(fp != NULL, "cannot load field");
    uint64_t header[4]; require(fread(header, sizeof(header), 1, fp) == 1, "read header failed");
    require(header[0] == UINT64_C(0x5241574849535431) && header[3] == LEVELS+GLOBAL_SUPPORT*16, "field format mismatch");
    size_t cap = 1024; while (cap*7/10 < header[1]+1) cap *= 2;
    field_init(f, cap); *with_memory = (int)header[2];
    for (uint64_t k = 0; k < header[1]; k++) {
        Cell c; require(fread(&c, sizeof(c), 1, fp) == 1 && c.total != 0, "invalid cell");
        *find_cell(f, c.a, c.b, 1) = c;
    }
    require(fgetc(fp) == EOF, "unexpected field data"); fclose(fp);
}
#endif
