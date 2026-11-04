// LD_PRELOAD heap sampler: size-weighted sampling of malloc/calloc/realloc, tracks live sampled blocks per call stack,
// dumps the top stacks by live bytes to $HEAPSAMPLE_OUT every 30 s. Diagnostic only.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <execinfo.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

#define DEPTH 22
#define NSITES 16384
#define NLIVE (1u << 21)
#define RATE (32 * 1024)

typedef struct { uint64_t key; long live_bytes, live_n, total; void *fr[DEPTH]; int nfr; } site_t;
typedef struct { void *p; int site; long w; } live_t;
static site_t sites[NSITES];
static live_t live[NLIVE];
static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static __thread int guard;
static __thread long acc;
static void *(*r_malloc)(size_t), *(*r_calloc)(size_t, size_t), *(*r_realloc)(void *, size_t);
static void (*r_free)(void *);
static char boot[65536]; static size_t bootn;
static int ready;

static void init(void) {
  if (r_malloc) return;
  r_malloc = dlsym(RTLD_NEXT, "malloc"); r_calloc = dlsym(RTLD_NEXT, "calloc");
  r_realloc = dlsym(RTLD_NEXT, "realloc"); r_free = dlsym(RTLD_NEXT, "free");
}
static unsigned hp(void *p) { uint64_t x = (uint64_t)p >> 4; x *= 0x9E3779B97F4A7C15ull; return (unsigned)(x >> 43) & (NLIVE - 1); }

static void record(void *p, size_t sz) {
  if (!ready || guard || !p) return;
  acc += sz; if (acc < RATE && sz < RATE) return;
  long w = sz >= RATE ? (long)sz : RATE; if (sz < RATE) acc -= RATE; 
  guard = 1;
  void *fr[DEPTH + 2]; int n = backtrace(fr, DEPTH + 2); n -= 2; if (n < 0) n = 0;
  uint64_t k = 1469598103934665603ull; for (int i = 0; i < n; i++) { k ^= (uint64_t)fr[i + 2]; k *= 1099511628211ull; }
  pthread_mutex_lock(&mu);
  unsigned s = (unsigned)(k % NSITES), t = 0;
  while (sites[s].key && sites[s].key != k && t++ < NSITES) s = (s + 1) % NSITES;
  if (!sites[s].key) { sites[s].key = k; sites[s].nfr = n; memcpy(sites[s].fr, fr + 2, n * sizeof(void *)); }
  sites[s].live_bytes += w; sites[s].live_n++; sites[s].total += w;
  unsigned h = hp(p); for (unsigned i = 0; i < 64; i++, h = (h + 1) & (NLIVE - 1))
    if ((uintptr_t)live[h].p <= 1) { live[h].p = p; live[h].site = s; live[h].w = w; break; }
  pthread_mutex_unlock(&mu);
  guard = 0;
}
static void unrecord(void *p) {
  if (!ready || !p || guard) return;
  pthread_mutex_lock(&mu);
  unsigned h = hp(p); for (unsigned i = 0; i < 64; i++, h = (h + 1) & (NLIVE - 1))
    if (live[h].p == p) {
      sites[live[h].site].live_bytes -= live[h].w; sites[live[h].site].live_n--;
      // backward-shift not needed for correctness of lookups within 64 probes if we leave a tombstone
      live[h].p = (void *)1; break; }
  pthread_mutex_unlock(&mu);
}

void *malloc(size_t n) { init(); void *p = r_malloc(n); record(p, n); return p; }
void *calloc(size_t a, size_t b) {
  if (!r_calloc) { if (!r_malloc && !guard) { guard = 1; init(); guard = 0; } if (!r_calloc) { size_t n = (a * b + 15) & ~15ul; void *p = boot + bootn; bootn += n; return p; } }
  void *p = r_calloc(a, b); record(p, a * b); return p; }
void *realloc(void *o, size_t n) { init(); if ((char *)o >= boot && (char *)o < boot + sizeof boot) { void *p = r_malloc(n); memcpy(p, o, n); return p; }
  unrecord(o); void *p = r_realloc(o, n); record(p, n); return p; }
void free(void *p) { if ((char *)p >= boot && (char *)p < boot + sizeof boot) return; init(); unrecord(p); r_free(p); }

static int cmp(const void *a, const void *b) { long x = sites[*(int *)a].live_bytes, y = sites[*(int *)b].live_bytes; return x < y ? 1 : x > y ? -1 : 0; }
static void *dumper(void *u) {
  guard = 1; const char *out = getenv("HEAPSAMPLE_OUT"); if (!out) out = "/tmp/heapsample.txt";
  static int idx[NSITES]; time_t t0 = time(0);
  for (;;) {
    sleep(20);
    static site_t top[20]; pthread_mutex_lock(&mu); int m = 0; for (int i = 0; i < NSITES; i++) if (sites[i].key) idx[m++] = i;
    qsort(idx, m, sizeof(int), cmp); int k = m < 20 ? m : 20; for (int j = 0; j < k; j++) top[j] = sites[idx[j]];
    pthread_mutex_unlock(&mu);
    FILE *f = fopen(out, "w"); if (!f) continue;
    fprintf(f, "t=%lds sites=%d\n", (long)(time(0) - t0), m);
    for (int j = 0; j < k; j++) { site_t *s = &top[j];
      fprintf(f, "\n#%d live=%.1fMB n=%ld total=%.1fMB\n", j, s->live_bytes / 1048576.0, s->live_n, s->total / 1048576.0);
      for (int i = 0; i < s->nfr; i++) { Dl_info d; if (dladdr(s->fr[i], &d) && d.dli_fname)
          fprintf(f, "   %s+%#lx (%s+%#lx)\n", d.dli_sname ? d.dli_sname : "?", (unsigned long)((char *)s->fr[i] - (char *)(d.dli_saddr ? d.dli_saddr : d.dli_fbase)), strrchr(d.dli_fname, '/') ? strrchr(d.dli_fname, '/') + 1 : d.dli_fname, (unsigned long)((char *)s->fr[i] - (char *)d.dli_fbase));
        else fprintf(f, "   %p\n", s->fr[i]); } }
    fclose(f);
  }
  return u;
}
__attribute__((constructor)) static void start(void) {
  init(); guard = 1; void *fr[4]; backtrace(fr, 4); guard = 0;  // load libgcc's unwinder before tracing
  pthread_t th; pthread_create(&th, 0, dumper, 0); pthread_detach(th); ready = 1;
}
