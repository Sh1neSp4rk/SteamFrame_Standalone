/* frame_doompad: an OpenXR API layer that gives KHARVOX (DOOM 2016 VR) the Steam Frame's full Xbox button set.
 *
 * KHARVOX turns its 12 OpenXR actions into a virtual Xbox pad through an XInputGetState import hook in DOOMx64vk.exe,
 * but it has no action for LT, LB, RB, X, Y, L3, View, Menu or the D-pad: those Xbox buttons are only reachable through
 * Quest-style gestures. The Frame has every Xbox button, so this layer adds an action set "framepad" with them, reads
 * it every xrSyncActions and ORs the matching XInput bits into what DOOM's XInputGetState import returns. DOOM's own
 * campaign gamepad binds then apply exactly as in flat play.
 *
 *  - The import slot is wrapped around whatever it holds at session attach. KHARVOX patches it once, before it even
 *    creates its OpenXR instance, so this wrapper sits outside KHARVOX's hook and sees its finished virtual pad.
 *  - While RB is held DOOM's weapon wheel is open. The physical right stick then goes to DOOM's right stick for wheel
 *    selection and KHARVOX's turn action reads centered, so the view does not turn at the same time.
 *  - The vertical axis of KHARVOX's turn stick reads 0 (KHARVOX maps stick up/down to chainsaw/weapon select, which
 *    X/RB now do; a flat player's "look up" would otherwise rev the chainsaw). FRAMEXR_DOOM_STICK_Y=1 keeps it.
 *  - D-pad right: stock DOOM cycles equipment there, but the KHARVOX launcher rebinds that channel to Use on every
 *    launch. The layer sends D-pad right (menus, Use) plus the keyboard Z key, which the campaign binds to the same
 *    equipment cycle (_quick2).
 *  - A and B match flat with KHARVOX's default (unswapped) jump/crouch: Frame A is a plain Xbox A (DOOM: jump, menu
 *    confirm); Frame B drives KHARVOX's crouch action plus a plain Xbox B (crouch, menu back), see dp_get_state.
 *  - Only the Touch interaction profile is forwarded, so SteamVR honours the Frame-typed binding.
 * Active only in DOOMx64vk.exe / DOOMx64.exe. DISABLE_FRAME_DOOMPAD=1 turns it off. Log: frame_doompad.log beside DOOM.
 * Built freestanding with clang --target=x86_64-pc-windows-msvc, importing a few msvcrt/kernel32/user32 functions. */
#include <openxr/openxr.h>
#include <openxr/openxr_loader_negotiation.h>

typedef struct FILE FILE;
__declspec(dllimport) FILE *fopen(const char *, const char *);
__declspec(dllimport) int fprintf(FILE *, const char *, ...);
__declspec(dllimport) int fflush(FILE *);
__declspec(dllimport) char *getenv(const char *);
__declspec(dllimport) void *memcpy(void *, const void *, unsigned long long);
__declspec(dllimport) void *memset(void *, int, unsigned long long);
__declspec(dllimport) void *__stdcall GetModuleHandleA(const char *);
__declspec(dllimport) int __stdcall VirtualProtect(void *, unsigned long long, unsigned int, unsigned int *);
__declspec(dllimport) unsigned int __stdcall GetModuleFileNameA(void *, char *, unsigned int);
__declspec(dllimport) unsigned int __stdcall SendInput(unsigned int, void *, int);

int _fltused = 0;   /* MSVC ABI marker normally supplied by the CRT (no CRT here) */

static FILE *logf;
static int layer_off, keep_stick_y;
static int streq(const char *a, const char *b) { while (*a && *a == *b) { a++; b++; } return *a == *b; }
static int ieq(const char *a, const char *b)
{
    for (;; a++, b++) {
        char x = *a, y = *b;
        if (x >= 'A' && x <= 'Z') x += 32;
        if (y >= 'A' && y <= 'Z') y += 32;
        if (x != y) return 0;
        if (!x) return 1;
    }
}
static void copy_str(char *d, const char *s, unsigned n) { unsigned i = 0; for (; s[i] && i + 1 < n; i++) d[i] = s[i]; d[i] = 0; }
#define LOG(...) do { if (logf) { fprintf(logf, __VA_ARGS__); fflush(logf); } } while (0)

static void decide_layer_scope(void)
{
    char path[520]; unsigned n = GetModuleFileNameA(0, path, sizeof path - 1);
    if (n >= sizeof path) n = sizeof path - 1;
    path[n] = 0;
    const char *base = path;
    for (unsigned i = 0; i < n; i++) if (path[i] == '\\' || path[i] == '/') base = path + i + 1;
    layer_off = !ieq(base, "DOOMx64vk.exe") && !ieq(base, "DOOMx64.exe");
    if (!layer_off) {
        logf = fopen("frame_doompad.log", "w");
        const char *y = getenv("FRAMEXR_DOOM_STICK_Y");
        keep_stick_y = y && streq(y, "1");
        LOG("frame_doompad active in %s (turn stick vertical %s)\n", base, keep_stick_y ? "kept" : "zeroed");
    }
}

/* ---- the framepad action set ---------------------------------------------------------------------------------- */
enum { P_A, P_B, P_LB, P_RB, P_X, P_Y, P_L3, P_VIEW, P_MENU, P_UP, P_DOWN, P_LEFT, P_RIGHT, P_N };
static const unsigned short pad_bit[P_N] = {0x1000, 0x2000, 0x0100, 0x0200, 0x4000, 0x8000, 0x0040, 0x0020, 0x0010,
                                            0x0001, 0x0002, 0x0004, 0x0008};
static const char *pad_name[P_N] = {"a", "b", "lb", "rb", "x", "y", "l3", "view", "menu",
                                    "dpad_up", "dpad_down", "dpad_left", "dpad_right"};
static const char *pad_label[P_N] = {"A (jump / confirm)", "B (crouch / back)", "LB (equipment)",
                                     "RB (change weapon / wheel)", "X (chainsaw)", "Y (BFG)",
                                     "L3", "View (dossier)", "Menu (Start)", "D-pad up (weapon mod)",
                                     "D-pad down (objectives)", "D-pad left (equipment)", "D-pad right (equipment)"};
/* Touch paths only make SteamVR learn the actions; the Frame binding file decides what really drives them. */
static const char *pad_touch[P_N] = {"/user/hand/right/input/a/click", "/user/hand/right/input/b/click",
    "/user/hand/left/input/squeeze/value", "/user/hand/right/input/squeeze/value",
    "/user/hand/left/input/x/click", "/user/hand/left/input/y/click", "/user/hand/left/input/thumbstick/click",
    "/user/hand/left/input/menu/click", "/user/hand/right/input/a/click", "/user/hand/right/input/b/click",
    "/user/hand/right/input/thumbstick/click", "/user/hand/left/input/thumbrest/touch",
    "/user/hand/right/input/thumbrest/touch"};
static const char *lt_touch = "/user/hand/left/input/trigger/value";

static PFN_xrGetInstanceProcAddr next_gipa;
static PFN_xrSuggestInteractionProfileBindings next_suggest;
static PFN_xrPathToString next_path_to_string;
static PFN_xrStringToPath next_string_to_path;
static PFN_xrCreateActionSet next_create_set;
static PFN_xrCreateAction next_create_action;
static PFN_xrAttachSessionActionSets next_attach;
static PFN_xrSyncActions next_sync;
static PFN_xrGetActionStateBoolean next_get_bool;
static PFN_xrGetActionStateFloat next_get_float;
static PFN_xrGetActionStateVector2f next_get_vec2;

static int pad_ready;
static XrActionSet pad_set;
static XrAction pad_act[P_N], pad_lt, doom_turn;
static XrSession pad_session;
static volatile unsigned short pad_bits;
static volatile unsigned char pad_lt_value;
static volatile int wheel_on;
static volatile short wheel_x, wheel_y;
static volatile unsigned int pad_packet;
static float turn_x, turn_y;   /* physical right stick, from KHARVOX's own doom_turn reads */

static void pad_create(XrInstance instance)
{
    if (pad_ready || !next_create_set || !next_create_action) return;
    XrActionSetCreateInfo si; memset(&si, 0, sizeof si);
    si.type = XR_TYPE_ACTION_SET_CREATE_INFO;
    copy_str(si.actionSetName, "framepad", sizeof si.actionSetName);
    copy_str(si.localizedActionSetName, "Frame pad (Xbox buttons KHARVOX lacks)", sizeof si.localizedActionSetName);
    XrResult r = next_create_set(instance, &si, &pad_set);
    for (int i = 0; XR_SUCCEEDED(r) && i <= P_N; i++) {
        XrActionCreateInfo ai; memset(&ai, 0, sizeof ai);
        ai.type = XR_TYPE_ACTION_CREATE_INFO;
        ai.actionType = i < P_N ? XR_ACTION_TYPE_BOOLEAN_INPUT : XR_ACTION_TYPE_FLOAT_INPUT;
        copy_str(ai.actionName, i < P_N ? pad_name[i] : "lt", sizeof ai.actionName);
        copy_str(ai.localizedActionName, i < P_N ? pad_label[i] : "LT (weapon mod / zoom)", sizeof ai.localizedActionName);
        r = next_create_action(pad_set, &ai, i < P_N ? &pad_act[i] : &pad_lt);
    }
    pad_ready = XR_SUCCEEDED(r);
    LOG("framepad action set %s (%d)\n", pad_ready ? "created" : "FAILED", (int)r);
}

/* Remember KHARVOX's turn action so its stick can be shared with DOOM's weapon wheel. */
static XrResult XRAPI_CALL dp_create_action(XrActionSet set, const XrActionCreateInfo *info, XrAction *action)
{
    XrResult r = next_create_action(set, info, action);
    if (XR_SUCCEEDED(r) && streq(info->actionName, "doom_turn")) { doom_turn = *action; LOG("KHARVOX doom_turn action found\n"); }
    return r;
}

static XrResult XRAPI_CALL dp_get_vec2(XrSession session, const XrActionStateGetInfo *info, XrActionStateVector2f *state)
{
    XrResult r = next_get_vec2(session, info, state);
    if (XR_SUCCEEDED(r) && doom_turn && info->action == doom_turn) {
        turn_x = state->isActive ? state->currentState.x : 0;
        turn_y = state->isActive ? state->currentState.y : 0;
        if (wheel_on) { state->currentState.x = 0; state->currentState.y = 0; }
        else if (!keep_stick_y) state->currentState.y = 0;
    }
    return r;
}

/* Only the Touch suggestion goes through (plus the framepad bindings); see the header. */
static XrResult XRAPI_CALL dp_suggest(XrInstance instance, const XrInteractionProfileSuggestedBinding *s)
{
    char name[256]; uint32_t len = 0;
    if (!next_path_to_string || XR_FAILED(next_path_to_string(instance, s->interactionProfile, sizeof name, &len, name)))
        return next_suggest(instance, s);
    if (!streq(name, "/interaction_profiles/oculus/touch_controller")) { LOG("suggest %s: dropped\n", name); return XR_SUCCESS; }
    pad_create(instance);
    if (!pad_ready || s->countSuggestedBindings > 100) return next_suggest(instance, s);
    XrActionSuggestedBinding b[128];
    unsigned n = s->countSuggestedBindings;
    memcpy(b, s->suggestedBindings, n * sizeof *b);
    for (int i = 0; i <= P_N; i++) {
        XrPath p;
        if (XR_FAILED(next_string_to_path(instance, i < P_N ? pad_touch[i] : lt_touch, &p))) continue;
        b[n].action = i < P_N ? pad_act[i] : pad_lt; b[n].binding = p; n++;
    }
    XrInteractionProfileSuggestedBinding out = *s;
    out.suggestedBindings = b; out.countSuggestedBindings = n;
    XrResult r = next_suggest(instance, &out);
    LOG("suggest %s: %u + %u framepad bindings -> %d\n", name, s->countSuggestedBindings, n - s->countSuggestedBindings, (int)r);
    if (XR_FAILED(r)) { pad_ready = 0; return next_suggest(instance, s); }
    return r;
}

/* ---- XInput ---------------------------------------------------------------------------------------------------- */
typedef struct { unsigned short wButtons; unsigned char bLeftTrigger, bRightTrigger; short sThumbLX, sThumbLY, sThumbRX, sThumbRY; } XPAD;
typedef struct { unsigned int dwPacketNumber; XPAD Gamepad; } XSTATE;
typedef unsigned int(__stdcall *PFN_XGetState)(unsigned int, XSTATE *);
static PFN_XGetState inner_get_state;

static unsigned int __stdcall dp_get_state(unsigned int user, XSTATE *s)
{
    unsigned int r = inner_get_state ? inner_get_state(user, s) : 1167u;
    if (user != 0 || !s) return r;
    unsigned short bits = pad_bits;
    unsigned char lt = pad_lt_value;
    int wheel = wheel_on;
    if (r != 0) {
        if (!bits && !lt && !wheel) return r;
        memset(s, 0, sizeof *s); r = 0;
    }
    /* Frame B also drives KHARVOX's crouch action (its camera tracks crouching). In menus KHARVOX turns crouch into
     * Xbox A (confirm); B means back there, so drop that A unless Frame A itself is held. In gameplay KHARVOX sends B
     * for crouch, and an A beside it (Hands Jump) is kept. */
    unsigned short k = s->Gamepad.wButtons;
    if ((bits & 0x2000) && !(bits & 0x1000) && (k & 0x1000) && !(k & 0x2000)) s->Gamepad.wButtons &= (unsigned short)~0x1000;
    s->Gamepad.wButtons |= bits;
    if (lt > s->Gamepad.bLeftTrigger) s->Gamepad.bLeftTrigger = lt;
    if (wheel) { s->Gamepad.sThumbRX = wheel_x; s->Gamepad.sThumbRY = wheel_y; }
    s->dwPacketNumber += pad_packet;   /* changes whenever KHARVOX's pad or ours does */
    return r;
}

/* Wrap DOOM's XInputGetState import slot around its current target (KHARVOX's hook). */
static void hook_iat(void)
{
    unsigned char *base = (unsigned char *)GetModuleHandleA(0);
    if (!base) return;
    unsigned int pe = *(unsigned int *)(base + 0x3C);
    unsigned int imp = *(unsigned int *)(base + pe + 24 + 112 + 8);   /* OptionalHeader.DataDirectory[1].VirtualAddress */
    if (!imp) return;
    int hooked = 0;
    for (unsigned int *d = (unsigned int *)(base + imp); d[3]; d += 5) {        /* IMAGE_IMPORT_DESCRIPTOR */
        const char *dll = (const char *)(base + d[3]);
        if (!ieq(dll, "xinput1_4.dll") && !ieq(dll, "xinput1_3.dll") && !ieq(dll, "xinput9_1_0.dll")) continue;
        unsigned long long *names = (unsigned long long *)(base + (d[0] ? d[0] : d[4])), *iat = (unsigned long long *)(base + d[4]);
        for (; *names; names++, iat++) {
            int match;
            if (*names >> 63) match = ((*names & 0xFFFF) == 2 || (*names & 0xFFFF) == 100);
            else match = streq((const char *)(base + (unsigned int)*names + 2), "XInputGetState");
            if (!match || *iat == (unsigned long long)(void *)dp_get_state) continue;
            unsigned int old;
            if (!VirtualProtect(iat, 8, 0x04, &old)) continue;
            inner_get_state = (PFN_XGetState)(void *)*iat;
            *iat = (unsigned long long)(void *)dp_get_state;
            VirtualProtect(iat, 8, old, &old);
            hooked++;
        }
    }
    LOG("%d XInputGetState import slot(s) wrapped (inner %p)\n", hooked, (void *)inner_get_state);
}

static XrResult XRAPI_CALL dp_attach(XrSession session, const XrSessionActionSetsAttachInfo *info)
{
    if (!pad_ready || info->countActionSets > 30) return next_attach(session, info);
    XrActionSet sets[32];
    memcpy(sets, info->actionSets, info->countActionSets * sizeof *sets);
    sets[info->countActionSets] = pad_set;
    XrSessionActionSetsAttachInfo out = *info;
    out.actionSets = sets; out.countActionSets = info->countActionSets + 1;
    XrResult r = next_attach(session, &out);
    LOG("attach with framepad -> %d\n", (int)r);
    if (XR_FAILED(r)) { pad_ready = 0; return next_attach(session, info); }
    pad_session = session;
    hook_iat();
    return r;
}

/* Keyboard Z = the campaign's _quick2 (equipment cycle), stock DOOM's D-pad right. */
static void send_key_z(int down)
{
    struct { unsigned int type, pad; unsigned short vk, scan; unsigned int flags, time; unsigned long long extra; unsigned char rest[8]; } in;
    memset(&in, 0, sizeof in);
    in.type = 1; in.scan = 0x2C; in.flags = 0x0008 | (down ? 0 : 0x0002);   /* KEYEVENTF_SCANCODE (| KEYUP) */
    SendInput(1, &in, (int)sizeof in);
}

static short to_short(float v) { if (v > 1) v = 1; if (v < -1) v = -1; return (short)(v * (v < 0 ? 32768.f : 32767.f)); }

static XrResult XRAPI_CALL dp_sync(XrSession session, const XrActionsSyncInfo *info)
{
    if (!pad_ready || session != pad_session || info->countActiveActionSets > 30) return next_sync(session, info);
    XrActiveActionSet sets[32];
    memcpy(sets, info->activeActionSets, info->countActiveActionSets * sizeof *sets);
    sets[info->countActiveActionSets].actionSet = pad_set;
    sets[info->countActiveActionSets].subactionPath = XR_NULL_PATH;
    XrActionsSyncInfo out = *info;
    out.activeActionSets = sets; out.countActiveActionSets = info->countActiveActionSets + 1;
    XrResult r = next_sync(session, &out);
    unsigned short bits = 0;
    unsigned char lt = 0;
    if (XR_SUCCEEDED(r)) {
        for (int i = 0; i < P_N; i++) {
            XrActionStateGetInfo gi; memset(&gi, 0, sizeof gi);
            gi.type = XR_TYPE_ACTION_STATE_GET_INFO; gi.action = pad_act[i];
            XrActionStateBoolean st; memset(&st, 0, sizeof st); st.type = XR_TYPE_ACTION_STATE_BOOLEAN;
            if (XR_SUCCEEDED(next_get_bool(session, &gi, &st)) && st.isActive && st.currentState) bits |= pad_bit[i];
        }
        XrActionStateGetInfo gi; memset(&gi, 0, sizeof gi);
        gi.type = XR_TYPE_ACTION_STATE_GET_INFO; gi.action = pad_lt;
        XrActionStateFloat fs; memset(&fs, 0, sizeof fs); fs.type = XR_TYPE_ACTION_STATE_FLOAT;
        if (XR_SUCCEEDED(next_get_float(session, &gi, &fs)) && fs.isActive && fs.currentState > 0.05f)
            lt = (unsigned char)(fs.currentState >= 1 ? 255 : fs.currentState * 255);
    }
    unsigned short old = pad_bits;
    if ((bits ^ old) & 0x0008) send_key_z(bits & 0x0008);
    int wheel = (bits & 0x0200) != 0;
    short wx = wheel ? to_short(turn_x) : 0, wy = wheel ? to_short(turn_y) : 0;
    if (bits != old || lt != pad_lt_value || wheel != wheel_on || wx != wheel_x || wy != wheel_y) pad_packet++;
    if (bits != old) LOG("buttons 0x%04x\n", bits);
    if (wheel != wheel_on) LOG("RB %s: right stick -> %s\n", wheel ? "held" : "released", wheel ? "DOOM weapon wheel" : "KHARVOX turn");
    wheel_x = wx; wheel_y = wy; wheel_on = wheel; pad_lt_value = lt; pad_bits = bits;
    return r;
}

/* ---- layer plumbing ------------------------------------------------------------------------------------------- */
static XrResult XRAPI_CALL dp_gipa(XrInstance instance, const char *name, PFN_xrVoidFunction *function)
{
    if (!layer_off) {
        if (streq(name, "xrSuggestInteractionProfileBindings") && next_suggest) { *function = (PFN_xrVoidFunction)dp_suggest; return XR_SUCCESS; }
        if (streq(name, "xrCreateAction") && next_create_action) { *function = (PFN_xrVoidFunction)dp_create_action; return XR_SUCCESS; }
        if (streq(name, "xrGetActionStateVector2f") && next_get_vec2) { *function = (PFN_xrVoidFunction)dp_get_vec2; return XR_SUCCESS; }
        if (streq(name, "xrAttachSessionActionSets") && next_attach) { *function = (PFN_xrVoidFunction)dp_attach; return XR_SUCCESS; }
        if (streq(name, "xrSyncActions") && next_sync) { *function = (PFN_xrVoidFunction)dp_sync; return XR_SUCCESS; }
    }
    if (!next_gipa) return XR_ERROR_HANDLE_INVALID;
    return next_gipa(instance, name, function);
}

static XrResult XRAPI_CALL dp_create(const XrInstanceCreateInfo *info, const struct XrApiLayerCreateInfo *layer_info,
                                     XrInstance *instance)
{
    decide_layer_scope();
    next_gipa = layer_info->nextInfo->nextGetInstanceProcAddr;
    struct XrApiLayerCreateInfo next = *layer_info;
    next.nextInfo = layer_info->nextInfo->next;
    XrResult r = layer_info->nextInfo->nextCreateApiLayerInstance(info, &next, instance);
    if (XR_SUCCEEDED(r) && !layer_off) {
        next_gipa(*instance, "xrSuggestInteractionProfileBindings", (PFN_xrVoidFunction *)&next_suggest);
        next_gipa(*instance, "xrPathToString", (PFN_xrVoidFunction *)&next_path_to_string);
        next_gipa(*instance, "xrStringToPath", (PFN_xrVoidFunction *)&next_string_to_path);
        next_gipa(*instance, "xrCreateActionSet", (PFN_xrVoidFunction *)&next_create_set);
        next_gipa(*instance, "xrCreateAction", (PFN_xrVoidFunction *)&next_create_action);
        next_gipa(*instance, "xrAttachSessionActionSets", (PFN_xrVoidFunction *)&next_attach);
        next_gipa(*instance, "xrSyncActions", (PFN_xrVoidFunction *)&next_sync);
        next_gipa(*instance, "xrGetActionStateBoolean", (PFN_xrVoidFunction *)&next_get_bool);
        next_gipa(*instance, "xrGetActionStateFloat", (PFN_xrVoidFunction *)&next_get_float);
        next_gipa(*instance, "xrGetActionStateVector2f", (PFN_xrVoidFunction *)&next_get_vec2);
    }
    LOG("xrCreateInstance -> %d\n", (int)r);
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
    request->getInstanceProcAddr = dp_gipa;
    request->createApiLayerInstance = dp_create;
    return XR_SUCCESS;
}

int __stdcall DllMain(void *inst, unsigned reason, void *reserved) { (void)inst; (void)reason; (void)reserved; return 1; }
