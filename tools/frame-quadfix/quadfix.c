/* frame_quadfix: an OpenXR API layer for the Steam Frame (SteamVR OpenXR through Proton's wineopenxr).
 *
 * Unreal Revived submits its menu/HUD panel as two XrCompositionLayerQuad layers, one per eye
 * (eyeVisibility LEFT / RIGHT, the right one from array slice 1). On the Frame every xrEndFrame carrying
 * them fails ("compositor failed EndFrame()", XR_ERROR_POSE_INVALID), so the menu never reaches the headset.
 * This layer rewrites each frame before it reaches the runtime. FRAMEXR_QUAD selects the mode:
 *   both (default) - the LEFT quad is shown to both eyes, the RIGHT quad is dropped
 *   drop           - all quads are dropped (scene only; diagnostic)
 *   pass           - frames are passed through untouched (diagnostic)
 * Every mode also normalises quad orientations and logs to frame_quadfix.log next to the game:
 * the first quads seen in full, then accept/reject counts every 600 frames split by "had quads" or not.
 * Built freestanding with clang --target=x86_64-pc-windows-msvc, importing a few msvcrt functions. */
#include <openxr/openxr.h>
#include <openxr/openxr_loader_negotiation.h>

typedef struct FILE FILE;
__declspec(dllimport) FILE *fopen(const char *, const char *);
__declspec(dllimport) int fprintf(FILE *, const char *, ...);
__declspec(dllimport) int fflush(FILE *);
__declspec(dllimport) char *getenv(const char *);
__declspec(dllimport) double sqrt(double);
__declspec(dllimport) void *memcpy(void *, const void *, unsigned long long);
__declspec(dllimport) void *memset(void *, int, unsigned long long);

int _fltused = 0;   /* MSVC ABI marker normally supplied by the CRT (no CRT here) */

static PFN_xrGetInstanceProcAddr next_gipa;
static PFN_xrEndFrame next_end_frame;
static FILE *logf;
static int mode;                 /* 0 both, 1 drop, 2 pass */
static unsigned long long frames, quad_ok, quad_fail, plain_ok, plain_fail;
static int detail_left = 4;

static int streq(const char *a, const char *b) { while (*a && *a == *b) { a++; b++; } return *a == *b; }

static void open_log(void)
{
    if (logf) return;
    logf = fopen("frame_quadfix.log", "w");
    const char *m = getenv("FRAMEXR_QUAD");
    mode = (m && streq(m, "drop")) ? 1 : (m && streq(m, "pass")) ? 2 : 0;
    if (logf) { fprintf(logf, "frame_quadfix loaded, mode=%s\n", mode == 0 ? "both" : mode == 1 ? "drop" : "pass"); fflush(logf); }
}

static void normalise(XrQuaternionf *q)
{
    double n = sqrt((double)q->x * q->x + (double)q->y * q->y + (double)q->z * q->z + (double)q->w * q->w);
    if (n < 1e-6 || n != n) { q->x = q->y = q->z = 0; q->w = 1; return; }   /* zero / NaN -> identity */
    q->x = (float)(q->x / n); q->y = (float)(q->y / n); q->z = (float)(q->z / n); q->w = (float)(q->w / n);
}

static void log_quad(const XrCompositionLayerQuad *q, unsigned i)
{
    if (!logf) return;
    const XrPosef *p = &q->pose;
    double n = sqrt((double)p->orientation.x * p->orientation.x + (double)p->orientation.y * p->orientation.y +
                    (double)p->orientation.z * p->orientation.z + (double)p->orientation.w * p->orientation.w);
    fprintf(logf, "  quad[%u] eye=%d flags=0x%llx space=%p swapchain=%p rect=(%d,%d %dx%d) array=%u size=%.3fx%.3f\n"
                  "           pos=(%.3f %.3f %.3f) quat=(%.4f %.4f %.4f %.4f) |q|=%.6f\n",
            i, (int)q->eyeVisibility, (unsigned long long)q->layerFlags, (void *)q->space, (void *)q->subImage.swapchain,
            q->subImage.imageRect.offset.x, q->subImage.imageRect.offset.y, q->subImage.imageRect.extent.width,
            q->subImage.imageRect.extent.height, q->subImage.imageArrayIndex, q->size.width, q->size.height,
            p->position.x, p->position.y, p->position.z, p->orientation.x, p->orientation.y, p->orientation.z,
            p->orientation.w, n);
}

static XrResult XRAPI_CALL quadfix_end_frame(XrSession session, const XrFrameEndInfo *info)
{
    const XrCompositionLayerBaseHeader *layers[16];
    XrCompositionLayerQuad quads[16];
    XrFrameEndInfo out = *info;
    unsigned n = 0, nquads = 0;
    int detail = 0;
    for (unsigned i = 0; i < info->layerCount && n < 16; i++) {
        const XrCompositionLayerBaseHeader *h = info->layers[i];
        if (h->type == XR_TYPE_COMPOSITION_LAYER_QUAD) {
            const XrCompositionLayerQuad *q = (const XrCompositionLayerQuad *)h;
            nquads++;
            if (detail_left > 0) { if (!detail && logf) fprintf(logf, "frame %llu: %u layers\n", frames, info->layerCount); detail = 1; log_quad(q, i); }
            if (mode == 2) { layers[n++] = h; continue; }
            if (mode == 1) continue;
            if (q->eyeVisibility == XR_EYE_VISIBILITY_RIGHT) continue;
            memcpy(&quads[n], q, sizeof *q);
            quads[n].eyeVisibility = XR_EYE_VISIBILITY_BOTH;
            normalise(&quads[n].pose.orientation);
            layers[n] = (const XrCompositionLayerBaseHeader *)&quads[n];
            n++;
        } else {
            layers[n++] = h;
        }
    }
    if (detail) detail_left--;
    out.layers = layers; out.layerCount = n;
    XrResult r = next_end_frame(session, mode == 2 ? info : &out);
    frames++;
    if (nquads) { if (XR_SUCCEEDED(r)) quad_ok++; else quad_fail++; } else { if (XR_SUCCEEDED(r)) plain_ok++; else plain_fail++; }
    if (logf && (detail || frames % 600 == 0 || (frames < 600 && XR_FAILED(r) && (quad_fail + plain_fail) <= 3))) {
        if (detail || XR_FAILED(r)) fprintf(logf, "  -> submitted %u layers, result %d\n", n, (int)r);
        if (frames % 600 == 0)
            fprintf(logf, "frames %llu: with quads ok %llu fail %llu | without quads ok %llu fail %llu\n",
                    frames, quad_ok, quad_fail, plain_ok, plain_fail);
        fflush(logf);
    }
    return r;
}

/* SteamVR only honours a Frame-typed binding when the app's input context holds ONE interaction profile; the game
 * suggests Touch, Index, Vive, WMR, simple... Forward only the Touch suggestion (FRAMEXR_PROFILES=all disables this)
 * and report success for the rest, which the game treats as optional anyway. */
static PFN_xrSuggestInteractionProfileBindings next_suggest;
static PFN_xrPathToString next_path_to_string;
static XrResult XRAPI_CALL quadfix_suggest(XrInstance instance, const XrInteractionProfileSuggestedBinding *s)
{
    char name[256]; uint32_t len = 0;
    const char *all = getenv("FRAMEXR_PROFILES");
    if ((all && streq(all, "all")) || !next_path_to_string ||
        XR_FAILED(next_path_to_string(instance, s->interactionProfile, sizeof name, &len, name)))
        return next_suggest(instance, s);
    int keep = streq(name, "/interaction_profiles/oculus/touch_controller");
    XrResult r = keep ? next_suggest(instance, s) : XR_SUCCESS;
    if (logf) { fprintf(logf, "suggest %s: %s (%d)\n", name, keep ? "forwarded" : "dropped", (int)r); fflush(logf); }
    return r;
}

static XrResult XRAPI_CALL quadfix_gipa(XrInstance instance, const char *name, PFN_xrVoidFunction *function)
{
    if (streq(name, "xrEndFrame") && next_end_frame) { *function = (PFN_xrVoidFunction)quadfix_end_frame; return XR_SUCCESS; }
    if (streq(name, "xrSuggestInteractionProfileBindings") && next_suggest) { *function = (PFN_xrVoidFunction)quadfix_suggest; return XR_SUCCESS; }
    if (!next_gipa) return XR_ERROR_HANDLE_INVALID;
    return next_gipa(instance, name, function);
}

static XrResult XRAPI_CALL quadfix_create(const XrInstanceCreateInfo *info, const struct XrApiLayerCreateInfo *layer_info,
                                          XrInstance *instance)
{
    open_log();
    next_gipa = layer_info->nextInfo->nextGetInstanceProcAddr;
    struct XrApiLayerCreateInfo next = *layer_info;
    next.nextInfo = layer_info->nextInfo->next;
    XrResult r = layer_info->nextInfo->nextCreateApiLayerInstance(info, &next, instance);
    if (XR_SUCCEEDED(r)) {
        next_gipa(*instance, "xrEndFrame", (PFN_xrVoidFunction *)&next_end_frame);
        next_gipa(*instance, "xrSuggestInteractionProfileBindings", (PFN_xrVoidFunction *)&next_suggest);
        next_gipa(*instance, "xrPathToString", (PFN_xrVoidFunction *)&next_path_to_string);
    }
    if (logf) { fprintf(logf, "xrCreateInstance -> %d, next xrEndFrame %p\n", (int)r, (void *)next_end_frame); fflush(logf); }
    return r;
}

__declspec(dllexport) XrResult XRAPI_CALL xrNegotiateLoaderApiLayerInterface(const XrNegotiateLoaderInfo *loader_info,
                                                                             const char *layer_name,
                                                                             XrNegotiateApiLayerRequest *request)
{
    (void)layer_name;
    if (!loader_info || !request || loader_info->structType != XR_LOADER_INTERFACE_STRUCT_LOADER_INFO ||
        request->structType != XR_LOADER_INTERFACE_STRUCT_API_LAYER_REQUEST)
        return XR_ERROR_INITIALIZATION_FAILED;
    request->layerInterfaceVersion = XR_CURRENT_LOADER_API_LAYER_VERSION;
    request->layerApiVersion = XR_CURRENT_API_VERSION;
    request->getInstanceProcAddr = quadfix_gipa;
    request->createApiLayerInstance = quadfix_create;
    return XR_SUCCESS;
}

int __stdcall DllMain(void *inst, unsigned reason, void *reserved) { (void)inst; (void)reason; (void)reserved; return 1; }
