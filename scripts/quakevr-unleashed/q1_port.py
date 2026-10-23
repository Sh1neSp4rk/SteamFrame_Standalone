# License note: the replacement source fragments in this file derive from vittorioromeo/quakevr (Ironwail / QuakeSpasm), GPL-2.0,
# and are offered under that same license. The rest of this repository is MIT (see LICENSE).
"""QuakeVR v1.1.0-beta3 on linux-arm64 (Steam Frame): route the VR module's SSE/AVX intrinsics through SIMDe
(~/PCVR/QuakeVR/simde, native aliases) on non-x86, and keep the AVX target attribute x86-only. Idempotent.
Usage: python3 -I q1_port.py <repo dir>"""
import os, sys

root = sys.argv[1]
X86 = "#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__) || defined(_M_IX86)\n"

def patch(rel, pairs):
    path = os.path.join(root, rel)
    s = open(path).read()
    for old, new in pairs:
        if new in s:
            continue
        assert s.count(old) == 1, (rel, old[:60], s.count(old))
        s = s.replace(old, new)
    open(path, "w").write(s)
    print("patched", rel)

patch("Quake/vr/vr_ao.cpp", [
    ("#include <immintrin.h> // (the bake's rays: SSE2, x64's baseline, four at a time; AVX, when there, eight)\n",
     X86 + "#include <immintrin.h> // (the bake's rays: SSE2, x64's baseline, four at a time; AVX, when there, eight)\n"
     "#else // ARM (Steam Frame): SSE/AVX through SIMDe on NEON; the runtime check never picks the AVX path here\n"
     "#define SIMDE_ENABLE_NATIVE_ALIASES\n#include <simde/x86/avx.h>\n#endif\n"),
    ("#if defined(__clang__) || defined(__GNUC__)\n#define QVR_TARGET_AVX __attribute__((target(\"avx\")))\n",
     "#if (defined(__clang__) || defined(__GNUC__)) && (defined(__x86_64__) || defined(__i386__))\n"
     "#define QVR_TARGET_AVX __attribute__((target(\"avx\")))\n"),
])
# Steam Frame (zink on Turnip): QVR_GLSAFE_OFF=<VR_GLSAFE_* mask> turns single GL features off (the "vendor
# workaround" path) without full safe mode, whose fallbacks drew the world black there.
patch("Quake/vr/vr_glsafe.cpp", [
    ("    glsafe.vendorOff = amd && vr_gl_workarounds.value != 0.f ? amdDefaults : 0u;\n",
     "    glsafe.vendorOff = amd && vr_gl_workarounds.value != 0.f ? amdDefaults : 0u;\n"
     "    if(const char* mask = getenv(\"QVR_GLSAFE_OFF\"))\n    {\n"
     "        glsafe.vendorOff |= static_cast<unsigned>(strtoul(mask, nullptr, 0));\n"
     "        VR_GLStep(\"QVR_GLSAFE_OFF=%s\", mask);\n    }\n"),
])
# Steam Frame (zink): QVR_XR_SYNC=1 glFlush, 2 glFinish before each swapchain image's release, so the compositor
# doesn't read an eye image zink hasn't finished (0/unset: as upstream).
patch("Quake/vr/vr_backend_openxr.cpp", [
    ('#include "vr_xr_linuxgl.hpp"\n',
     '#include "vr_xr_linuxgl.hpp"\nextern "C" void* SDL_GL_GetProcAddress(const char* proc); // Steam Frame: QVR_XR_SYNC\n'),
    ("    bool releaseImage(const Swapchain& sc) const\n    {\n"
     "        XrSwapchainImageReleaseInfo releaseInfo{XR_TYPE_SWAPCHAIN_IMAGE_RELEASE_INFO};\n",
     "    bool releaseImage(const Swapchain& sc) const\n    {\n"
     "#ifndef _WIN32\n"
     "        { // Steam Frame/zink: the image complete before the compositor reads it (QVR_XR_SYNC)\n"
     "            static const int mode = getenv(\"QVR_XR_SYNC\") ? atoi(getenv(\"QVR_XR_SYNC\")) : 0;\n"
     "            static void (*syncFn)(void) = mode == 0 ? nullptr : reinterpret_cast<void (*)(void)>(\n"
     "                SDL_GL_GetProcAddress(mode == 1 ? \"glFlush\" : \"glFinish\"));\n"
     "            if(syncFn)\n                syncFn();\n        }\n"
     "#endif\n"
     "        XrSwapchainImageReleaseInfo releaseInfo{XR_TYPE_SWAPCHAIN_IMAGE_RELEASE_INFO};\n"),
])
patch("Quake/vr/vr_audio.cpp", [
    ("#include <emmintrin.h> // (SSE2: x64's baseline)\n",
     X86 + "#include <emmintrin.h> // (SSE2: x64's baseline)\n"
     "#else // ARM (Steam Frame): SSE2 through SIMDe on NEON\n"
     "#define SIMDE_ENABLE_NATIVE_ALIASES\n#include <simde/x86/sse2.h>\n#endif\n"),
])
