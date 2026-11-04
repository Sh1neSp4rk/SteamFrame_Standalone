# heap-sampler: find what a native game keeps allocating

A small `LD_PRELOAD` library for native ARM64 Linux games on the Frame. It samples `malloc`, `calloc` and `realloc` weighted by size, about one sample per 32 KB, and records the call stack of each sample. It forgets a sample when the block is freed. Every 20 seconds it writes the 20 call stacks holding the most live sampled memory, with symbols from `dladdr`. Overhead is low enough to play the game in the headset while it runs.

It found the [Counter-Strike VR](../../games/counter-strike-vr/) leak: SteamVR's `vrclient.so` allocating Vulkan command buffers inside `xrBeginFrame` and `xrEndFrame` every frame (see "A stale GL error makes SteamVR leak every frame" in [KNOWN-ISSUES.md](../../KNOWN-ISSUES.md)).

## Use

```bash
gcc -O2 -g -fPIC -shared -o heapsample.so heapsample.c -ldl -lpthread
# in the game's launch wrapper, just before the exec line:
export LD_PRELOAD=/path/to/heapsample.so HEAPSAMPLE_OUT=/path/to/heapsample.txt
```

Watch the process's resident memory alongside it (`ps -o rss= -p <pid>`). A real leak shows as one stack whose `live` figure grows with each dump. Remove the wrapper line afterwards.

Diagnostic only. The report thread copies the table under the lock and writes outside it, and the tracer's own allocations are not traced. Blocks under 32 KB are counted statistically, so `n` is exact only for large blocks. MIT, like the rest of this repository.
