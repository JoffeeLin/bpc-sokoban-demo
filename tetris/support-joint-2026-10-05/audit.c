/* State exists only in the external game and auditor. model.h sees raw bits. */
#include "model.h"
#include "environment.h"
#include <time.h>

static const char *tapes[] = {
    "000004", "111114", "0004", "114", "333000004", "311114", "33004",
    "333114", "4", "304", "314", "3304", "3314", "33304", "33314",
    "0003334", "111334"
#ifndef ONLY_ORIGINAL_TAPES
    , "2224", "002224", "112224", "32224", "332224", "3332224"
#endif
};
/* Handwritten operations, executed in the real game; no teaching board. */
static const char *pair_tapes[] = {
    "0000400" "222222222222222222",
    "0040000" "222222222222222222"
};
static void render(const State *s, Raw *r) {
    memset(r, 0, sizeof(*r));
    for (int y = 0; y < H; y++) for (int x = 0; x < W; x++)
        r->q[y*RW+x] = s->active[y*W+x] | s->world[y*W+x];
    for (int y = 0; y < 4; y++) for (int x = 0; x < 4; x++)
        r->q[y*RW+11+x] = s->preview[y*4+x];
    r->q[19*RW+14] = s->gameover;
}
static int raw_equal(const Raw *a, const Raw *b) { return eq(a->q, b->q, RN); }
static void refresh(RNG *rng, State *s, Medium *m) {
    if (s->gameover) return;
    preview_shape(ri(rng, 7), s->preview);
    Raw input = m->past[0];
    for (int y = 0; y < 4; y++) for (int x = 0; x < 4; x++)
        input.q[y*RW+11+x] = s->preview[y*4+x];
    medium_input(m, &input);
}
static uint64_t pair_seed(void) {
    for (uint64_t seed = 1; seed < 100000; seed++) {
        RNG r = {seed};
        int first = ri(&r, 7), second = ri(&r, 7);
        if (first == 1 && second == 1) return seed;
    }
    require(0, "pair seed not found"); return 0;
}
static void actual_tick(Field *fit, RNG *r, State *s, Medium *m, int act) {
    int lock = real_step(s, act); Raw truth; render(s, &truth);
    if (fit) field_observe(fit, m, act, &truth);
    medium_accept(m, act, &truth);
    if (lock) refresh(r, s, m);
}
static void pair_history(Field *fit, int which, int noops, int memory,
                         State *s, Medium *m, RNG *r) {
    r->s = pair_seed(); init_episode(r, s); Raw initial; render(s, &initial);
    medium_reset(m, &initial, memory);
    for (const char *p = pair_tapes[which]; *p; p++) actual_tick(fit, r, s, m, *p-'0');
    for (int j = 0; j < noops; j++) actual_tick(fit, r, s, m, 0);
}
static void alias_proof(void) {
    State s[2]; Medium m[2]; RNG r[2]; Raw next[2];
    for (int i = 0; i < 2; i++) {
        pair_history(NULL, i, 200, 1, &s[i], &m[i], &r[i]);
        real_step(&s[i], 1); render(&s[i], &next[i]);
    }
    int same = 1; for (int k = 0; k < LAGS; k++) same &= raw_equal(&m[0].past[k], &m[1].past[k]);
    int different = !raw_equal(&next[0], &next[1]);
    int memory_diff = memcmp(m[0].memory, m[1].memory, sizeof(m[0].memory)) != 0;
    int delta = 0; for (int i = 0; i < RN; i++) delta += next[0].q[i] != next[1].q[i];
    printf("ALIAS seed=%llu identical_current_and_last_%d_frames=%d repeated_noops=200 same_next_operation=1 different_next=%d differing_bits=%d memory_diff=%d\n",
           (unsigned long long)pair_seed(), LAGS, same, different, delta, memory_diff);
    require(same && different && memory_diff, "alias fixture failed");
}
static int pair_probe(Field *f, int memory, int noops, int mode) {
    State s[2]; Medium m[2]; RNG r[2]; Raw truth[2]; int ok = 0;
    for (int i = 0; i < 2; i++) {
        pair_history(NULL, i, noops, memory, &s[i], &m[i], &r[i]);
        real_step(&s[i], 1); render(&s[i], &truth[i]);
    }
    if (mode == 1) for (int i = 0; i < 2; i++) memset(m[i].memory, 0, sizeof(m[i].memory));
    if (mode == 2) {
        uint8_t saved[PORTS][RN]; memcpy(saved, m[0].memory, sizeof(saved));
        memcpy(m[0].memory, m[1].memory, sizeof(saved)); memcpy(m[1].memory, saved, sizeof(saved));
    }
    for (int i = 0; i < 2; i++) {
        Raw predicted; field_predict(f, &m[i], mode == 3 ? 2 : 1, &predicted);
        ok += raw_equal(&predicted, &truth[i]);
    }
    printf("PAIR_PROBE memory=%d noops=%d mode=%d exact=%d/2\n", memory, noops, mode, ok);
    return ok;
}
static int pair_rollout(Field *f, int memory, int noops) {
    int all = 0;
    for (int which = 0; which < 2; which++) {
        RNG r = {pair_seed()}; State s; init_episode(&r, &s); Raw initial; render(&s, &initial);
        Medium m; medium_reset(&m, &initial, memory); int good = 1, step = 0, first = -1;
        int len = (int)strlen(pair_tapes[which]);
        for (int t = 0; t < len+noops+1; t++) {
            int a = t < len ? pair_tapes[which][t]-'0' : t < len+noops ? 0 : 1;
            int lock = real_step(&s, a); Raw truth, predicted; render(&s, &truth);
            field_predict(f, &m, a, &predicted); medium_accept(&m, a, &predicted);
            if (!raw_equal(&truth, &predicted)) { good = 0; if (first < 0) first = step; }
            if (lock) refresh(&r, &s, &m);
            step++;
        }
        printf("PAIR_SELF_ROLLOUT memory=%d history=%d noops=%d whole_exact=%d first_failure=%d steps=%d\n",
               memory, which, noops, good, first, step);
        all += good;
    }
    return all;
}
static void pair_fit(Field *f, int memory, int repeats) {
    for (int j = 0; j < repeats; j++) for (int which = 0; which < 2; which++) {
        RNG r; State s; Medium m; pair_history(f, which, 6, memory, &s, &m, &r);
        actual_tick(f, &r, &s, &m, 1);
    }
}
static void pair_experiment(void) {
    alias_proof();
    for (int memory = 0; memory < 2; memory++) {
        Field f; field_init(&f, 65536); pair_fit(&f, memory, 100);
        uint64_t before = field_bytes_digest(&f);
        printf("PAIR_FIELD memory=%d global_support=%d cells=%zu digest=%016llx\n", memory, GLOBAL_SUPPORT, f.used, (unsigned long long)field_digest(&f));
        pair_probe(&f, memory, 6, 0); pair_probe(&f, memory, 200, 0);
        pair_rollout(&f, memory, 200);
        if (memory) for (int mode = 1; mode <= 3; mode++) pair_probe(&f, memory, 200, mode);
        printf("PAIR_BYTES_HASH_FROZEN=%d\n", before == field_bytes_digest(&f));
        char name[64]; snprintf(name, sizeof(name), "pair_%s%s.bin", GLOBAL_SUPPORT ? "" : "local_", memory ? "memory" : "raw");
        field_save(&f, name, memory); free(f.table);
    }
}
static void learn(Field *f, int memory, int pieces, uint64_t seed) {
    RNG r = {seed}; State s; init_episode(&r, &s); Raw initial; render(&s, &initial);
    Medium m; medium_reset(&m, &initial, memory);
    unsigned long long actions = 0, over = 0, counts[5] = {0};
    for (int pi = 0; pi < pieces; pi++) {
        if (s.gameover) {
            init_episode(&r, &s); render(&s, &initial); medium_reset(&m, &initial, memory); over++;
        }
        const char *p = tapes[ri(&r, (int)(sizeof(tapes)/sizeof(*tapes)))];
        for (; *p; p++) {
            int a = *p-'0', lock = real_step(&s, a); Raw truth; render(&s, &truth);
            field_observe(f, &m, a, &truth); medium_accept(&m, a, &truth); actions++; counts[a]++;
            if (lock) { refresh(&r, &s, &m); break; }
        }
    }
    printf("LEARN memory=%d seed=%llu pieces=%d actions=%llu gameovers=%llu cells=%zu digest=%016llx\n",
           memory, (unsigned long long)seed, pieces, actions, over, f->used, (unsigned long long)field_digest(f));
    printf("ANONYMOUS_PORT_EXPOSURES %llu %llu %llu %llu %llu\n", counts[0], counts[1], counts[2], counts[3], counts[4]);
}
typedef struct { unsigned long long n, exact, bits, episodes, failed, locks, real_steps; int first_ep, first_t, first_a; } Stats;
static Stats random_games(Field *f, int memory, int episodes, int horizon, uint64_t seed, int teacher, int mode) {
    RNG r = {seed}; Stats z = {0}; z.first_ep = z.first_t = z.first_a = -1;
    for (int ep = 0; ep < episodes; ep++) {
        State s; init_episode(&r, &s); Raw initial; render(&s, &initial);
        Medium m; medium_reset(&m, &initial, memory); z.episodes++; int failed = 0;
        for (int t = 0; t < horizon; t++) {
            int u = ri(&r, 100), a = u < 18 ? 0 : u < 36 ? 1 : u < 50 ? 3 : u < 70 ? 2 : 4;
            int lock = real_step(&s, a); Raw truth, predicted; render(&s, &truth); z.real_steps++;
            /* Finish the actual trajectory after a rejected prediction, so
               every variant receives the same subsequent episode stream. */
            if (failed && !teacher) {
                if (lock) { if (s.gameover) break; refresh(&r, &s, &m); }
                continue;
            }
            if (mode == 2) memset(m.memory, 0, sizeof(m.memory));
            field_predict(f, &m, mode == 1 ? (a+1)%5 : a, &predicted);
            int same = raw_equal(&truth, &predicted); z.n++; z.exact += same; z.locks += !!lock;
            for (int i = 0; i < RN; i++) z.bits += predicted.q[i] == truth.q[i];
            medium_accept(&m, a, teacher ? &truth : &predicted);
            if (!same) {
                if (z.first_ep < 0) { z.first_ep = ep; z.first_t = t; z.first_a = a; }
                failed = 1;
            }
            if (lock) { if (s.gameover) break; refresh(&r, &s, &m); }
        }
        z.failed += !!failed;
    }
    return z;
}
static void stats_print(const Stats *z, const char *label, int memory, uint64_t seed, int mode) {
    printf("%s memory=%d seed=%llu mode=%d exact=%llu/%llu bits=%llu/%llu failed_episodes=%llu/%llu locks=%llu real_steps=%llu first=%d:%d:%d\n",
           label, memory, (unsigned long long)seed, mode, z->exact, z->n, z->bits, z->n*RN,
           z->failed, z->episodes, z->locks, z->real_steps, z->first_ep, z->first_t, z->first_a);
}
static void play(Field *f, int memory, int pieces, uint64_t seed, int teacher) {
    RNG r = {seed}; State s; init_episode(&r, &s); Raw initial; render(&s, &initial);
    Medium m; medium_reset(&m, &initial, memory);
    unsigned long long n = 0, exact = 0; int first_piece = -1, first_a = -1, failed_episode = 0, failed_episodes = 0, episodes = 1;
    for (int pi = 0; pi < pieces; pi++) {
        if (s.gameover) {
            failed_episodes += failed_episode; failed_episode = 0; episodes++;
            init_episode(&r, &s); render(&s, &initial); medium_reset(&m, &initial, memory);
        }
        const char *p = tapes[ri(&r, (int)(sizeof(tapes)/sizeof(*tapes)))];
        for (; *p; p++) {
            int a = *p-'0', lock = real_step(&s, a); Raw truth, predicted; render(&s, &truth);
            field_predict(f, &m, a, &predicted); int same = raw_equal(&truth, &predicted); n++; exact += same;
            if (!same) {
                failed_episode = 1;
                if (first_piece < 0) { first_piece = pi; first_a = a; }
            }
            medium_accept(&m, a, teacher ? &truth : &predicted);
            if (lock) { refresh(&r, &s, &m); break; }
        }
    }
    failed_episodes += failed_episode;
    printf("PLAY_%s memory=%d seed=%llu pieces=%d exact=%llu/%llu failed_episodes=%d/%d first_piece=%d action=%d\n",
           teacher ? "TEACHER" : "SELF", memory, (unsigned long long)seed, pieces, exact, n, failed_episodes, episodes, first_piece, first_a);
}
int main(int argc, char **argv) {
    setbuf(stdout, NULL); clock_t start = clock();
    if (argc == 2 && !strcmp(argv[1], "pair")) { pair_experiment(); return 0; }
    if (argc < 3) { fprintf(stderr, "usage: audit pair | learn OUT memory pieces seed | eval FIELD first count episodes horizon teacher | play FIELD pieces count seed teacher | controls FIELD\n"); return 2; }
    Field f; int memory;
    if (!strcmp(argv[1], "learn")) {
        require(argc >= 6, "learn arguments missing"); memory = atoi(argv[3]); field_init(&f, 65536);
        learn(&f, memory, atoi(argv[4]), strtoull(argv[5], NULL, 10));
        pair_fit(&f, memory, 100); field_save(&f, argv[2], memory);
        printf("SAVED cells=%zu digest=%016llx CPU_SECONDS=%.3f\n", f.used, (unsigned long long)field_digest(&f), (double)(clock()-start)/CLOCKS_PER_SEC);
        free(f.table); return 0;
    }
    field_load(&f, argv[2], &memory); uint64_t before = field_bytes_digest(&f);
    if (!strcmp(argv[1], "eval")) {
        require(argc >= 8, "eval arguments missing");
        int first = atoi(argv[3]), count = atoi(argv[4]), eps = atoi(argv[5]), horizon = atoi(argv[6]), teacher = atoi(argv[7]);
        unsigned long long n = 0, exact = 0, failed = 0;
        for (int k = first; k < first+count; k++) {
            uint64_t seed = 98765ULL+200003ULL*(uint64_t)k;
            Stats z = random_games(&f, memory, eps, horizon, seed, teacher, 0);
            stats_print(&z, teacher ? "TEACHER" : "SELF", memory, seed, 0); n += z.n; exact += z.exact; failed += z.failed;
        }
        printf("TOTAL_%s exact=%llu/%llu failed_episodes=%llu\n", teacher ? "TEACHER" : "SELF", exact, n, failed);
    } else if (!strcmp(argv[1], "play")) {
        require(argc >= 7, "play arguments missing");
        for (int i = 0; i < atoi(argv[4]); i++) play(&f, memory, atoi(argv[3]), strtoull(argv[5], NULL, 10)+(uint64_t)i, atoi(argv[6]));
    } else if (!strcmp(argv[1], "controls")) {
        for (int mode = 0; mode < 3; mode++) {
            Stats z = random_games(&f, memory, 100, 120, 20261006ULL, 0, mode);
            stats_print(&z, "CONTROL", memory, 20261006ULL, mode);
        }
        pair_probe(&f, memory, 200, 0);
        if (memory) for (int mode = 1; mode <= 3; mode++) pair_probe(&f, memory, 200, mode);
        Field empty; field_init(&empty, 1024);
        Stats z = random_games(&empty, memory, 100, 120, 20261006ULL, 0, 0);
        stats_print(&z, "FIELD_OFF", memory, 20261006ULL, 0); free(empty.table);
    } else { free(f.table); return 2; }
    int frozen = before == field_bytes_digest(&f);
    printf("FIELD_BYTES_HASH_FROZEN=%d cells=%zu digest=%016llx CPU_SECONDS=%.3f\n", frozen, f.used, (unsigned long long)field_digest(&f), (double)(clock()-start)/CLOCKS_PER_SEC);
    free(f.table); require(frozen, "field changed during validation"); return 0;
}
