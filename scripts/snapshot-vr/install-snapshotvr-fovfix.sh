#!/bin/bash
# install-snapshotvr-fovfix.sh
#
# Steam Frame workaround: makes Snapshot VR (built with Unity OpenXR plugin 1.14.x) start in VR
# instead of a flat window. Installs a tiny implicit OpenXR API layer in your home directory.
# Nothing outside $HOME is touched. Run it over SSH on the Frame as the "steamos" user:
#
#     bash install-snapshotvr-fovfix.sh
#
# Needs gcc on the Frame. Without gcc, copy a prebuilt libXrApiLayer_fovfix.so to your home
# directory first (scp libXrApiLayer_fovfix.so steamos@frame.local:~/) and run the script.
#
# Uninstall:
#     rm ~/.local/share/openxr/1/api_layers/implicit.d/XrApiLayer_fovfix.json \
#        ~/.local/share/openxr/1/api_layers/implicit.d/libXrApiLayer_fovfix.so
set -euo pipefail
LAYER_DIR="$HOME/.local/share/openxr/1/api_layers/implicit.d"
SRC_DIR="$HOME/.local/share/xr_fovfix"
mkdir -p "$LAYER_DIR" "$SRC_DIR"

cat > "$SRC_DIR/xr_fovfix_layer.c" <<'EOF'
/*
 * XR_APILAYER_LOCAL_fb_foveation_depfix  (self-contained, no OpenXR headers needed)
 *
 * Implicit OpenXR API layer. When an app calls xrCreateInstance with XR_FB_foveation
 * enabled but without its required dependency XR_FB_swapchain_update_state, this layer
 * appends the dependency so strict runtimes (SteamVR on Steam Frame) accept the instance.
 * Any other xrCreateInstance call passes through untouched.
 *
 * Needed for Unity OpenXR plugin 1.14.x builds (e.g. Snapshot VR), whose Foveated
 * Rendering feature omits the dependency. Unity fixed this in plugin 1.15.
 *
 * Env:  DISABLE_XR_FOVFIX_LAYER=1  -> the OpenXR loader skips this layer entirely
 *       XR_FOVFIX_MODE=strip       -> drop XR_FB_foveation* instead of adding the dependency
 * Log:  ~/.local/share/xr_fovfix/xr_fovfix.log
 */
#define _GNU_SOURCE
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* ---- Minimal OpenXR / loader-negotiation definitions (ABI-identical to openxr.h 1.x) ---- */
typedef int32_t  XrResult;
typedef int32_t  XrStructureType;
typedef uint64_t XrVersion;
typedef uint64_t XrFlags64;
typedef XrFlags64 XrInstanceCreateFlags;
typedef struct XrInstance_T *XrInstance;
typedef void (*PFN_xrVoidFunction)(void);

#define XR_SUCCESS                      0
#define XR_ERROR_OUT_OF_MEMORY         -3
#define XR_ERROR_INITIALIZATION_FAILED -6
#define XR_ERROR_FUNCTION_UNSUPPORTED  -7
#define XR_MAKE_VERSION(major, minor, patch) \
    ((((XrVersion)(major)) << 48) | (((XrVersion)(minor)) << 32) | ((XrVersion)(patch)))

#define XR_MAX_APPLICATION_NAME_SIZE        128
#define XR_MAX_ENGINE_NAME_SIZE             128
#define XR_MAX_API_LAYER_NAME_SIZE          256
#define XR_API_LAYER_MAX_SETTINGS_PATH_SIZE 512

typedef struct XrApplicationInfo {
    char      applicationName[XR_MAX_APPLICATION_NAME_SIZE];
    uint32_t  applicationVersion;
    char      engineName[XR_MAX_ENGINE_NAME_SIZE];
    uint32_t  engineVersion;
    XrVersion apiVersion;
} XrApplicationInfo;

typedef struct XrInstanceCreateInfo {
    XrStructureType       type;
    const void           *next;
    XrInstanceCreateFlags createFlags;
    XrApplicationInfo     applicationInfo;
    uint32_t              enabledApiLayerCount;
    const char *const    *enabledApiLayerNames;
    uint32_t              enabledExtensionCount;
    const char *const    *enabledExtensionNames;
} XrInstanceCreateInfo;

typedef XrResult (*PFN_xrGetInstanceProcAddr)(XrInstance instance, const char *name, PFN_xrVoidFunction *function);

typedef enum XrLoaderInterfaceStructs {
    XR_LOADER_INTERFACE_STRUCT_UNINTIALIZED          = 0,
    XR_LOADER_INTERFACE_STRUCT_LOADER_INFO           = 1,
    XR_LOADER_INTERFACE_STRUCT_API_LAYER_REQUEST     = 2,
    XR_LOADER_INTERFACE_STRUCT_RUNTIME_REQUEST       = 3,
    XR_LOADER_INTERFACE_STRUCT_API_LAYER_CREATE_INFO = 4,
    XR_LOADER_INTERFACE_STRUCT_API_LAYER_NEXT_INFO   = 5,
    XR_LOADER_INTERFACE_STRUCTS_MAX_ENUM             = 0x7FFFFFFF
} XrLoaderInterfaceStructs;

#define XR_LOADER_INFO_STRUCT_VERSION        1
#define XR_API_LAYER_INFO_STRUCT_VERSION     1
#define XR_CURRENT_LOADER_API_LAYER_VERSION  1

typedef struct XrNegotiateLoaderInfo {
    XrLoaderInterfaceStructs structType;
    uint32_t  structVersion;
    size_t    structSize;
    uint32_t  minInterfaceVersion;
    uint32_t  maxInterfaceVersion;
    XrVersion minApiVersion;
    XrVersion maxApiVersion;
} XrNegotiateLoaderInfo;

typedef struct XrApiLayerNextInfo   XrApiLayerNextInfo;
typedef struct XrApiLayerCreateInfo XrApiLayerCreateInfo;
typedef XrResult (*PFN_xrCreateApiLayerInstance)(const XrInstanceCreateInfo *info,
                                                 const XrApiLayerCreateInfo *layerInfo,
                                                 XrInstance *instance);

typedef struct XrNegotiateApiLayerRequest {
    XrLoaderInterfaceStructs structType;
    uint32_t  structVersion;
    size_t    structSize;
    uint32_t  layerInterfaceVersion;
    XrVersion layerApiVersion;
    PFN_xrGetInstanceProcAddr    getInstanceProcAddr;
    PFN_xrCreateApiLayerInstance createApiLayerInstance;
} XrNegotiateApiLayerRequest;

struct XrApiLayerNextInfo {
    XrLoaderInterfaceStructs structType;
    uint32_t structVersion;
    size_t   structSize;
    char     layerName[XR_MAX_API_LAYER_NAME_SIZE];
    PFN_xrGetInstanceProcAddr    nextGetInstanceProcAddr;
    PFN_xrCreateApiLayerInstance nextCreateApiLayerInstance;
    XrApiLayerNextInfo *next;
};

struct XrApiLayerCreateInfo {
    XrLoaderInterfaceStructs structType;
    uint32_t structVersion;
    size_t   structSize;
    void    *loaderInstance;
    char     settings_file_location[XR_API_LAYER_MAX_SETTINGS_PATH_SIZE];
    XrApiLayerNextInfo *nextInfo;
};
/* ---- end definitions ---- */

#define EXT_FOV "XR_FB_foveation"
#define EXT_DEP "XR_FB_swapchain_update_state"

static PFN_xrGetInstanceProcAddr next_gipa = NULL;

static void logmsg(const char *fmt, ...)
{
    const char *home = getenv("HOME");
    char path[1024];
    if (!home) return;
    snprintf(path, sizeof path, "%s/.local/share/xr_fovfix/xr_fovfix.log", home);
    FILE *f = fopen(path, "a");
    if (!f) return;
    va_list ap;
    va_start(ap, fmt);
    fprintf(f, "[pid %d] ", (int)getpid());
    vfprintf(f, fmt, ap);
    fputc('\n', f);
    va_end(ap);
    fclose(f);
}

static XrResult fovfix_xrGetInstanceProcAddr(XrInstance instance, const char *name, PFN_xrVoidFunction *fn)
{
    if (!next_gipa) {
        if (fn) *fn = NULL;
        return XR_ERROR_FUNCTION_UNSUPPORTED;
    }
    return next_gipa(instance, name, fn);
}

static XrResult fovfix_xrCreateApiLayerInstance(const XrInstanceCreateInfo *info,
                                                const XrApiLayerCreateInfo *layerInfo,
                                                XrInstance *instance)
{
    if (!info || !layerInfo || !layerInfo->nextInfo || !layerInfo->nextInfo->nextCreateApiLayerInstance)
        return XR_ERROR_INITIALIZATION_FAILED;

    const XrApiLayerNextInfo *ni = layerInfo->nextInfo;
    next_gipa = ni->nextGetInstanceProcAddr;

    XrApiLayerCreateInfo next_layer_info = *layerInfo;
    next_layer_info.nextInfo = ni->next;

    int has_fov = 0, has_dep = 0;
    for (uint32_t i = 0; i < info->enabledExtensionCount; i++) {
        const char *e = info->enabledExtensionNames[i];
        if (!e) continue;
        if (!strcmp(e, EXT_FOV)) has_fov = 1;
        if (!strcmp(e, EXT_DEP)) has_dep = 1;
    }

    if (!(has_fov && !has_dep))
        return ni->nextCreateApiLayerInstance(info, &next_layer_info, instance);

    const char *mode = getenv("XR_FOVFIX_MODE");
    int strip = (mode && !strcmp(mode, "strip"));

    const char **names = calloc((size_t)info->enabledExtensionCount + 1, sizeof(char *));
    if (!names) return XR_ERROR_OUT_OF_MEMORY;
    uint32_t n = 0;
    for (uint32_t i = 0; i < info->enabledExtensionCount; i++) {
        const char *e = info->enabledExtensionNames[i];
        if (strip && e && (!strncmp(e, "XR_FB_foveation", 15) || !strcmp(e, "XR_META_foveation_eye_tracked")))
            continue;
        names[n++] = e;
    }
    if (!strip) names[n++] = EXT_DEP;

    XrInstanceCreateInfo mod = *info;
    mod.enabledExtensionCount = n;
    mod.enabledExtensionNames = names;

    logmsg("app '%s' (engine '%s') enabled %s without %s -> %s",
           info->applicationInfo.applicationName, info->applicationInfo.engineName,
           EXT_FOV, EXT_DEP, strip ? "stripping XR_FB_foveation* extensions" : "adding " EXT_DEP);
    XrResult r = ni->nextCreateApiLayerInstance(&mod, &next_layer_info, instance);
    logmsg("xrCreateInstance returned %d", (int)r);
    free(names);
    return r;
}

__attribute__((visibility("default")))
XrResult xrNegotiateLoaderApiLayerInterface(const XrNegotiateLoaderInfo *loaderInfo,
                                            const char *layerName,
                                            XrNegotiateApiLayerRequest *req)
{
    (void)layerName;
    if (!loaderInfo || !req ||
        loaderInfo->structType != XR_LOADER_INTERFACE_STRUCT_LOADER_INFO ||
        loaderInfo->structVersion != XR_LOADER_INFO_STRUCT_VERSION ||
        loaderInfo->structSize != sizeof(XrNegotiateLoaderInfo) ||
        req->structType != XR_LOADER_INTERFACE_STRUCT_API_LAYER_REQUEST ||
        req->structVersion != XR_API_LAYER_INFO_STRUCT_VERSION ||
        req->structSize != sizeof(XrNegotiateApiLayerRequest))
        return XR_ERROR_INITIALIZATION_FAILED;
    if (loaderInfo->minInterfaceVersion > XR_CURRENT_LOADER_API_LAYER_VERSION ||
        loaderInfo->maxInterfaceVersion < XR_CURRENT_LOADER_API_LAYER_VERSION)
        return XR_ERROR_INITIALIZATION_FAILED;

    req->layerInterfaceVersion = XR_CURRENT_LOADER_API_LAYER_VERSION;
    req->layerApiVersion = XR_MAKE_VERSION(1, 0, 0);
    req->getInstanceProcAddr = fovfix_xrGetInstanceProcAddr;
    req->createApiLayerInstance = fovfix_xrCreateApiLayerInstance;
    return XR_SUCCESS;
}
EOF

cat > "$LAYER_DIR/XrApiLayer_fovfix.json" <<EOF
{
    "file_format_version": "1.0.0",
    "api_layer": {
        "name": "XR_APILAYER_LOCAL_fb_foveation_depfix",
        "library_path": "$LAYER_DIR/libXrApiLayer_fovfix.so",
        "api_version": "1.0",
        "implementation_version": "1",
        "description": "Adds XR_FB_swapchain_update_state when an app enables XR_FB_foveation without it (Unity OpenXR 1.14 workaround)",
        "disable_environment": "DISABLE_XR_FOVFIX_LAYER"
    }
}
EOF

if command -v gcc >/dev/null 2>&1; then
    echo "Compiling layer with gcc..."
    gcc -O2 -Wall -fPIC -shared -fvisibility=hidden -fno-stack-protector -U_FORTIFY_SOURCE \
        -Wl,-z,defs -o "$SRC_DIR/libXrApiLayer_fovfix.so.tmp" "$SRC_DIR/xr_fovfix_layer.c"
    mv -f "$SRC_DIR/libXrApiLayer_fovfix.so.tmp" "$LAYER_DIR/libXrApiLayer_fovfix.so"
elif [ -f "$HOME/libXrApiLayer_fovfix.so" ]; then
    echo "No gcc found; installing prebuilt ~/libXrApiLayer_fovfix.so"
    mv -f "$HOME/libXrApiLayer_fovfix.so" "$LAYER_DIR/libXrApiLayer_fovfix.so"
else
    echo "ERROR: gcc is not installed and no prebuilt ~/libXrApiLayer_fovfix.so was found." >&2
    echo "       Either install gcc (developer mode) or copy the prebuilt .so to your home directory first." >&2
    exit 1
fi
chmod 755 "$LAYER_DIR/libXrApiLayer_fovfix.so"
echo "Installed:"
ls -la "$LAYER_DIR/XrApiLayer_fovfix.json" "$LAYER_DIR/libXrApiLayer_fovfix.so"
echo "Done. Launch Snapshot VR from the headset. Activity is logged to $SRC_DIR/xr_fovfix.log"
