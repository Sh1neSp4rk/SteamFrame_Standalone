
/* ---- Frame pad bridge (Halo MCC VR) ------------------------------------------------------------------------------
 * The MCCVR mod turns its OpenXR actions into a virtual Xbox pad but has no Back (View) or D-pad action, so the Frame
 * View button and D-pad cannot reach MCC in VR. This adds a second action set ("framepad": view + four d-pad buttons)
 * to the app's Touch suggestion, attach and sync, reads it every sync, and ORs XINPUT Back / D-pad bits into what the
 * game's XInputGetState import returns. The import slot is wrapped around the real xinput export (never around another
 * shim, so the mod's own periodic re-claim of the slot chains through this one without recursion).
 * FRAMEXR_PAD=0 disables the bridge. */
typedef unsigned short WORD16;
typedef struct { WORD16 wButtons; unsigned char bLeftTrigger, bRightTrigger; short sThumbLX, sThumbLY, sThumbRX, sThumbRY; } XPAD;
typedef struct { unsigned int dwPacketNumber; XPAD Gamepad; } XSTATE;
typedef unsigned int(__stdcall *PFN_XGetState)(unsigned int, XSTATE *);
__declspec(dllimport) void *__stdcall GetModuleHandleA(const char *);
__declspec(dllimport) void *__stdcall GetProcAddress(void *, const char *);
__declspec(dllimport) int __stdcall VirtualProtect(void *, unsigned long long, unsigned int, unsigned int *);

enum { PAD_VIEW, PAD_UP, PAD_DOWN, PAD_LEFT, PAD_RIGHT, PAD_N };
static const unsigned short pad_bit[PAD_N] = {0x0020, 0x0001, 0x0002, 0x0004, 0x0008};
static const char *pad_name[PAD_N] = {"view", "dpad_up", "dpad_down", "dpad_left", "dpad_right"};
static const char *pad_label[PAD_N] = {"View (Back)", "D-pad up", "D-pad down", "D-pad left", "D-pad right"};
/* Touch paths only make SteamVR learn the actions; the Frame binding file decides what really drives them. */
static const char *pad_touch[PAD_N] = {"/user/hand/left/input/menu/click", "/user/hand/left/input/y/click",
    "/user/hand/left/input/x/click", "/user/hand/left/input/thumbstick/click", "/user/hand/left/input/thumbrest/touch"};
static int pad_enabled = 1, pad_ready;
static XrActionSet pad_set;
static XrAction pad_act[PAD_N];
static volatile unsigned short pad_bits;
static unsigned int pad_packet;
static XrSession pad_session;
static PFN_xrCreateActionSet next_create_set;
static PFN_xrCreateAction next_create_action;
static PFN_xrStringToPath next_string_to_path;
static PFN_xrAttachSessionActionSets next_attach;
static PFN_xrSyncActions next_sync;
static PFN_xrGetActionStateBoolean next_get_bool;
static PFN_XGetState real_get_state;

/* Scope: on Windows an implicit layer loads into every OpenXR app. Everything here is for Halo MCC, so the layer
 * passes straight through in any other process (FRAMEXR_ALL=1 overrides). */
__declspec(dllimport) unsigned int __stdcall GetModuleFileNameA(void *, char *, unsigned int);
static int layer_off;
static int ieq(const char *a, const char *b);
static void decide_layer_scope(void)
{
    char path[520]; unsigned n = GetModuleFileNameA(0, path, sizeof path - 1);
    if (n >= sizeof path) n = sizeof path - 1;
    path[n] = 0;
    const char *base = path;
    for (unsigned i = 0; i < n; i++) if (path[i] == '\\' || path[i] == '/') base = path + i + 1;
    const char *all = getenv("FRAMEXR_ALL");
    layer_off = !(all && streq(all, "1")) && !ieq(base, "MCC-Win64-Shipping.exe");
    if (logf) { fprintf(logf, "process %s: layer %s\n", base, layer_off ? "PASS-THROUGH (not Halo MCC)" : "active"); fflush(logf); }
}

static void copy_str(char *d, const char *s, unsigned n) { unsigned i = 0; for (; s[i] && i + 1 < n; i++) d[i] = s[i]; d[i] = 0; }

static unsigned int __stdcall pad_get_state(unsigned int user, XSTATE *s)
{
    unsigned int r = real_get_state ? real_get_state(user, s) : 1167u;
    unsigned short bits = pad_bits;
    if (user == 0 && s && bits) {
        if (r != 0) { memset(s, 0, sizeof *s); r = 0; }
        s->Gamepad.wButtons |= bits;
        s->dwPacketNumber += ++pad_packet;
    }
    return r;
}

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

/* Wrap XInputGetState in the game exe's import table. */
static void pad_hook_iat(void)
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
        void *mod = GetModuleHandleA(dll);
        PFN_XGetState real = mod ? (PFN_XGetState)GetProcAddress(mod, "XInputGetState") : 0;
        if (!real) continue;
        unsigned long long *names = (unsigned long long *)(base + d[0]), *iat = (unsigned long long *)(base + d[4]);
        for (; *names; names++, iat++) {
            int match;
            if (*names >> 63) match = ((*names & 0xFFFF) == 2 || (*names & 0xFFFF) == 100);
            else match = streq((const char *)(base + (unsigned int)*names + 2), "XInputGetState");
            if (!match) continue;
            unsigned int old;
            if (!VirtualProtect(iat, 8, 0x04, &old)) continue;
            real_get_state = real;
            *iat = (unsigned long long)(void *)pad_get_state;
            VirtualProtect(iat, 8, old, &old);
            hooked++;
        }
    }
    if (logf) { fprintf(logf, "pad bridge: %d XInputGetState import slot(s) wrapped\n", hooked); fflush(logf); }
}

static void pad_create(XrInstance instance)
{
    if (pad_ready || !pad_enabled || !next_create_set || !next_create_action) return;
    XrActionSetCreateInfo si; memset(&si, 0, sizeof si);
    si.type = XR_TYPE_ACTION_SET_CREATE_INFO;
    copy_str(si.actionSetName, "framepad", sizeof si.actionSetName);
    copy_str(si.localizedActionSetName, "Frame pad (View, D-pad)", sizeof si.localizedActionSetName);
    XrResult r = next_create_set(instance, &si, &pad_set);
    for (int i = 0; XR_SUCCEEDED(r) && i < PAD_N; i++) {
        XrActionCreateInfo ai; memset(&ai, 0, sizeof ai);
        ai.type = XR_TYPE_ACTION_CREATE_INFO;
        ai.actionType = XR_ACTION_TYPE_BOOLEAN_INPUT;
        copy_str(ai.actionName, pad_name[i], sizeof ai.actionName);
        copy_str(ai.localizedActionName, pad_label[i], sizeof ai.localizedActionName);
        r = next_create_action(pad_set, &ai, &pad_act[i]);
    }
    pad_ready = XR_SUCCEEDED(r);
    if (logf) { fprintf(logf, "pad bridge: action set %s (%d)\n", pad_ready ? "created" : "FAILED", (int)r); fflush(logf); }
}

/* Touch suggestion: the app's bindings plus ours. */
static XrResult pad_suggest_touch(XrInstance instance, const XrInteractionProfileSuggestedBinding *s)
{
    pad_create(instance);
    if (!pad_ready || s->countSuggestedBindings > 120) return next_suggest(instance, s);
    XrActionSuggestedBinding b[128];
    unsigned n = s->countSuggestedBindings;
    memcpy(b, s->suggestedBindings, n * sizeof *b);
    for (int i = 0; i < PAD_N; i++) {
        XrPath p;
        if (XR_FAILED(next_string_to_path(instance, pad_touch[i], &p))) continue;
        b[n].action = pad_act[i]; b[n].binding = p; n++;
    }
    XrInteractionProfileSuggestedBinding out = *s;
    out.suggestedBindings = b; out.countSuggestedBindings = n;
    XrResult r = next_suggest(instance, &out);
    if (logf) { fprintf(logf, "pad bridge: Touch suggestion %u + %u bindings -> %d\n", s->countSuggestedBindings, n - s->countSuggestedBindings, (int)r); fflush(logf); }
    if (XR_FAILED(r)) { pad_ready = 0; return next_suggest(instance, s); }
    return r;
}

static XrResult XRAPI_CALL pad_attach(XrSession session, const XrSessionActionSetsAttachInfo *info)
{
    if (!pad_ready || info->countActionSets > 30) return next_attach(session, info);
    XrActionSet sets[32];
    memcpy(sets, info->actionSets, info->countActionSets * sizeof *sets);
    sets[info->countActionSets] = pad_set;
    XrSessionActionSetsAttachInfo out = *info;
    out.actionSets = sets; out.countActionSets = info->countActionSets + 1;
    XrResult r = next_attach(session, &out);
    if (XR_SUCCEEDED(r)) { pad_session = session; pad_hook_iat(); }
    if (logf) { fprintf(logf, "pad bridge: attach with framepad -> %d\n", (int)r); fflush(logf); }
    if (XR_FAILED(r)) { pad_ready = 0; return next_attach(session, info); }
    return r;
}

/* In Halo CE (as in Halo 2) MCC's Back is the instant Classic/Anniversary graphics switch, which drops the mod's
 * camera and crashes the game in VR; the mod swallows a pad's Back only in Halo 2. Follow the active title from the
 * mod's own "Title adapter: detected ..." log lines and hold Back back while CE is active. */
__declspec(dllimport) int fseek(FILE *, long, int);
__declspec(dllimport) unsigned long long fread(void *, unsigned long long, unsigned long long, FILE *);
static FILE *title_log;
static int title_log_tried, title_is_ce;
static unsigned title_polls;
static char title_buf[65536 + 64];
static unsigned title_carry;

static void title_poll(void)
{
    if (++title_polls % 45) return;                    /* about twice a second at the game's sync rate */
    if (!title_log) {
        if (title_log_tried > 20) return;
        title_log_tried++;
        title_log = fopen("..\\..\\..\\Halo_MCC_VR\\HaloMCCVR.log", "rb");
        if (logf) { fprintf(logf, "pad bridge: mod log %s\n", title_log ? "opened for title tracking" : "not readable yet"); fflush(logf); }
        if (!title_log) return;
    }
    static const char key[] = "Title adapter: detected ";
    const unsigned klen = sizeof key - 1;
    for (;;) {
        unsigned long long got = fread(title_buf + title_carry, 1, 65536, title_log);
        if (!got) { fseek(title_log, 0, 1); return; }   /* clear EOF so later appends are read */
        unsigned n = title_carry + (unsigned)got;
        for (unsigned i = 0; i + klen + 2 <= n; i++) {
            unsigned k = 0;
            while (k < klen && title_buf[i + k] == key[k]) k++;
            if (k < klen) continue;
            const char *t = title_buf + i + klen;
            int ce = (t[0] == 'C' && t[1] == 'E');
            if (ce != title_is_ce && logf) { fprintf(logf, "pad bridge: Halo CE %s; Back %s\n", ce ? "active" : "inactive", ce ? "held back" : "passed"); fflush(logf); }
            title_is_ce = ce;
        }
        title_carry = n < 48 ? n : 48;                  /* keep a tail so a split key is still found */
        memcpy(title_buf, title_buf + n - title_carry, title_carry);
    }
}

static XrResult XRAPI_CALL pad_sync(XrSession session, const XrActionsSyncInfo *info)
{
    title_poll();
    if (!pad_ready || session != pad_session || info->countActiveActionSets > 30) return next_sync(session, info);
    XrActiveActionSet sets[32];
    memcpy(sets, info->activeActionSets, info->countActiveActionSets * sizeof *sets);
    sets[info->countActiveActionSets].actionSet = pad_set;
    sets[info->countActiveActionSets].subactionPath = XR_NULL_PATH;
    XrActionsSyncInfo out = *info;
    out.activeActionSets = sets; out.countActiveActionSets = info->countActiveActionSets + 1;
    XrResult r = next_sync(session, &out);
    unsigned short bits = 0;
    if (XR_SUCCEEDED(r))
        for (int i = 0; i < PAD_N; i++) {
            XrActionStateGetInfo gi; memset(&gi, 0, sizeof gi);
            gi.type = XR_TYPE_ACTION_STATE_GET_INFO; gi.action = pad_act[i];
            XrActionStateBoolean st; memset(&st, 0, sizeof st); st.type = XR_TYPE_ACTION_STATE_BOOLEAN;
            if (XR_SUCCEEDED(next_get_bool(session, &gi, &st)) && st.isActive && st.currentState) bits |= pad_bit[i];
        }
    if (title_is_ce) bits &= (unsigned short)~0x0020;
    if (bits != pad_bits && logf) { fprintf(logf, "pad bridge: buttons 0x%04x\n", bits); fflush(logf); }
    pad_bits = bits;
    return r;
}
