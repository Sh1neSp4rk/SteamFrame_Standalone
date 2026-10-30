// Steam Frame -> virtual Xbox controller for Monster Hunter Rise (REFramework VR).
//
// REFramework's VR mod never feeds VR controllers to Rise; it expects a real
// gamepad. This REFramework plugin hooks xinput1_4's XInputGetState /
// XInputGetCapabilities and, while OpenVR is running, reports XInput user 0 as
// an Xbox pad driven by REFramework's own OpenVR actions (same process, same
// action manifest). Without openvr_api.dll loaded (flat launch) it passes
// everything through untouched. A real pad on user 0 is merged, not replaced.
//
// Pairs with _vr\mhrise_frame_binding.json:
//   right A/B/X/Y -> AButton / BButton / Block / Heal
//   Menu (R) / View (L) -> SystemButton      bumpers -> RE2_Quickturn
//   triggers -> Squeeze (analog)             sticks -> Joystick / JoystickClick
//   left D-pad -> DPad_*                      grips -> Grip (not sent to the game)
//
// Build: gcc -O2 -shared -o mhrise_framepad.dll mhrise_framepad.c <minhook>/src/*.c
//        <minhook>/src/hde/hde64.c -I<minhook>/include -static-libgcc

#include <windows.h>
#include <xinput.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include "MinHook.h"

// ---- Minimal OpenVR IVRInput_010 (C view of the C++ vtable) ----
typedef uint64_t VRActionHandle_t;
typedef uint64_t VRInputValueHandle_t;

typedef struct {
    bool bActive;
    VRInputValueHandle_t activeOrigin;
    bool bState;
    bool bChanged;
    float fUpdateTime;
} InputDigitalActionData_t;

typedef struct {
    bool bActive;
    VRInputValueHandle_t activeOrigin;
    float x, y, z;
    float deltaX, deltaY, deltaZ;
    float fUpdateTime;
} InputAnalogActionData_t;

typedef struct IVRInput IVRInput;
typedef struct {
    int (*SetActionManifestPath)(IVRInput*, const char*);
    int (*GetActionSetHandle)(IVRInput*, const char*, uint64_t*);
    int (*GetActionHandle)(IVRInput*, const char*, VRActionHandle_t*);
    int (*GetInputSourceHandle)(IVRInput*, const char*, VRInputValueHandle_t*);
    int (*UpdateActionState)(IVRInput*, void*, uint32_t, uint32_t);
    int (*GetDigitalActionData)(IVRInput*, VRActionHandle_t, InputDigitalActionData_t*, uint32_t, VRInputValueHandle_t);
    int (*GetAnalogActionData)(IVRInput*, VRActionHandle_t, InputAnalogActionData_t*, uint32_t, VRInputValueHandle_t);
} IVRInputVtbl;
struct IVRInput { const IVRInputVtbl* vt; };

typedef void* (*VR_GetGenericInterfaceFn)(const char*, int*);

// ---- Actions ----
enum {
    ACT_A, ACT_B, ACT_X, ACT_Y, ACT_SYSTEM, ACT_BUMPER, ACT_STICK_CLICK,
    ACT_DUP, ACT_DDOWN, ACT_DLEFT, ACT_DRIGHT, ACT_DIGITAL_COUNT
};
static const char* g_digital_names[ACT_DIGITAL_COUNT] = {
    "/actions/default/in/AButton",
    "/actions/default/in/BButton",
    "/actions/default/in/Block",
    "/actions/default/in/Heal",
    "/actions/default/in/SystemButton",
    "/actions/default/in/RE2_Quickturn",
    "/actions/default/in/JoystickClick",
    "/actions/default/in/DPad_Up",
    "/actions/default/in/DPad_Down",
    "/actions/default/in/DPad_Left",
    "/actions/default/in/DPad_Right",
};

static IVRInput* g_input;
static VRActionHandle_t g_digital[ACT_DIGITAL_COUNT];
static VRActionHandle_t g_joystick, g_squeeze;
static VRInputValueHandle_t g_left, g_right;
static DWORD g_next_init_try;
static DWORD g_packet;
static XINPUT_GAMEPAD g_last_pad;
static FILE* g_log;

static void plog(const char* fmt, ...) {
    if (g_log == NULL) {
        return;
    }
    va_list ap;
    va_start(ap, fmt);
    vfprintf(g_log, fmt, ap);
    va_end(ap);
    fputc('\n', g_log);
    fflush(g_log);
}

static bool vr_ready(void) {
    if (g_input != NULL) {
        return true;
    }
    HMODULE ovr = GetModuleHandleA("openvr_api.dll");
    if (ovr == NULL) {
        return false;  // flat launch
    }
    DWORD now = GetTickCount();
    if ((LONG)(now - g_next_init_try) < 0) {
        return false;
    }
    g_next_init_try = now + 1000;

    VR_GetGenericInterfaceFn get_iface = (VR_GetGenericInterfaceFn)GetProcAddress(ovr, "VR_GetGenericInterface");
    if (get_iface == NULL) {
        return false;
    }
    int err = 0;
    IVRInput* input = (IVRInput*)get_iface("IVRInput_010", &err);
    if (input == NULL || err != 0) {
        return false;  // REFramework hasn't run VR_Init yet
    }
    for (int i = 0; i < ACT_DIGITAL_COUNT; i++) {
        input->vt->GetActionHandle(input, g_digital_names[i], &g_digital[i]);
    }
    input->vt->GetActionHandle(input, "/actions/default/in/Joystick", &g_joystick);
    input->vt->GetActionHandle(input, "/actions/default/in/Squeeze", &g_squeeze);
    input->vt->GetInputSourceHandle(input, "/user/hand/left", &g_left);
    input->vt->GetInputSourceHandle(input, "/user/hand/right", &g_right);
    g_input = input;
    plog("OpenVR input ready (left=%llx right=%llx)", (unsigned long long)g_left, (unsigned long long)g_right);
    return true;
}

static bool digital(int act, VRInputValueHandle_t hand) {
    InputDigitalActionData_t d = {0};
    if (g_input->vt->GetDigitalActionData(g_input, g_digital[act], &d, sizeof(d), hand) != 0) {
        return false;
    }
    return d.bActive && d.bState;
}

static InputAnalogActionData_t analog(VRActionHandle_t act, VRInputValueHandle_t hand) {
    InputAnalogActionData_t a = {0};
    if (g_input->vt->GetAnalogActionData(g_input, act, &a, sizeof(a), hand) != 0 || !a.bActive) {
        memset(&a, 0, sizeof(a));
    }
    return a;
}

static SHORT to_axis(float v) {
    if (v > 1.0f) v = 1.0f;
    if (v < -1.0f) v = -1.0f;
    return (SHORT)(v >= 0 ? v * 32767.0f : v * 32768.0f);
}

static BYTE to_trigger(float v) {
    if (v < 0.0f) v = 0.0f;
    if (v > 1.0f) v = 1.0f;
    return (BYTE)(v * 255.0f + 0.5f);
}

static void read_vr_pad(XINPUT_GAMEPAD* p) {
    memset(p, 0, sizeof(*p));
    WORD b = 0;
    if (digital(ACT_A, g_right)) b |= XINPUT_GAMEPAD_A;
    if (digital(ACT_B, g_right)) b |= XINPUT_GAMEPAD_B;
    if (digital(ACT_X, g_right)) b |= XINPUT_GAMEPAD_X;
    if (digital(ACT_Y, g_right)) b |= XINPUT_GAMEPAD_Y;
    if (digital(ACT_SYSTEM, g_right)) b |= XINPUT_GAMEPAD_START;
    if (digital(ACT_SYSTEM, g_left)) b |= XINPUT_GAMEPAD_BACK;
    if (digital(ACT_BUMPER, g_left)) b |= XINPUT_GAMEPAD_LEFT_SHOULDER;
    if (digital(ACT_BUMPER, g_right)) b |= XINPUT_GAMEPAD_RIGHT_SHOULDER;
    if (digital(ACT_STICK_CLICK, g_left)) b |= XINPUT_GAMEPAD_LEFT_THUMB;
    if (digital(ACT_STICK_CLICK, g_right)) b |= XINPUT_GAMEPAD_RIGHT_THUMB;
    if (digital(ACT_DUP, 0)) b |= XINPUT_GAMEPAD_DPAD_UP;
    if (digital(ACT_DDOWN, 0)) b |= XINPUT_GAMEPAD_DPAD_DOWN;
    if (digital(ACT_DLEFT, 0)) b |= XINPUT_GAMEPAD_DPAD_LEFT;
    if (digital(ACT_DRIGHT, 0)) b |= XINPUT_GAMEPAD_DPAD_RIGHT;
    p->wButtons = b;

    InputAnalogActionData_t ls = analog(g_joystick, g_left);
    InputAnalogActionData_t rs = analog(g_joystick, g_right);
    p->sThumbLX = to_axis(ls.x);
    p->sThumbLY = to_axis(ls.y);
    p->sThumbRX = to_axis(rs.x);
    p->sThumbRY = to_axis(rs.y);
    p->bLeftTrigger = to_trigger(analog(g_squeeze, g_left).x);
    p->bRightTrigger = to_trigger(analog(g_squeeze, g_right).x);
}

static SHORT bigger(SHORT a, SHORT b) { return abs(a) >= abs(b) ? a : b; }

// ---- Hooks ----
typedef DWORD (WINAPI* XInputGetStateFn)(DWORD, XINPUT_STATE*);
typedef DWORD (WINAPI* XInputGetCapabilitiesFn)(DWORD, DWORD, XINPUT_CAPABILITIES*);
static XInputGetStateFn o_get_state, o_get_state_ex;
static XInputGetCapabilitiesFn o_get_caps;

static DWORD merged_state(XInputGetStateFn orig, DWORD user, XINPUT_STATE* st) {
    DWORD r = orig(user, st);
    if (user != 0 || st == NULL || !vr_ready()) {
        return r;
    }
    XINPUT_GAMEPAD vr;
    read_vr_pad(&vr);
    if (r != ERROR_SUCCESS) {
        memset(st, 0, sizeof(*st));
    }
    XINPUT_GAMEPAD* p = &st->Gamepad;
    p->wButtons |= vr.wButtons;
    p->bLeftTrigger = max(p->bLeftTrigger, vr.bLeftTrigger);
    p->bRightTrigger = max(p->bRightTrigger, vr.bRightTrigger);
    p->sThumbLX = bigger(p->sThumbLX, vr.sThumbLX);
    p->sThumbLY = bigger(p->sThumbLY, vr.sThumbLY);
    p->sThumbRX = bigger(p->sThumbRX, vr.sThumbRX);
    p->sThumbRY = bigger(p->sThumbRY, vr.sThumbRY);
    if (memcmp(p, &g_last_pad, sizeof(*p)) != 0) {
        g_last_pad = *p;
        g_packet++;
    }
    st->dwPacketNumber = (r == ERROR_SUCCESS ? st->dwPacketNumber : 0) + g_packet;
    return ERROR_SUCCESS;
}

static DWORD WINAPI hk_get_state(DWORD user, XINPUT_STATE* st) { return merged_state(o_get_state, user, st); }
static DWORD WINAPI hk_get_state_ex(DWORD user, XINPUT_STATE* st) { return merged_state(o_get_state_ex, user, st); }

static DWORD WINAPI hk_get_caps(DWORD user, DWORD flags, XINPUT_CAPABILITIES* caps) {
    DWORD r = o_get_caps(user, flags, caps);
    if (r == ERROR_SUCCESS || user != 0 || caps == NULL || !vr_ready()) {
        return r;
    }
    memset(caps, 0, sizeof(*caps));
    caps->Type = XINPUT_DEVTYPE_GAMEPAD;
    caps->SubType = XINPUT_DEVSUBTYPE_GAMEPAD;
    caps->Gamepad.wButtons = 0xF3FF;
    caps->Gamepad.bLeftTrigger = caps->Gamepad.bRightTrigger = 0xFF;
    caps->Gamepad.sThumbLX = caps->Gamepad.sThumbLY = (SHORT)0xFFC0;
    caps->Gamepad.sThumbRX = caps->Gamepad.sThumbRY = (SHORT)0xFFC0;
    caps->Vibration.wLeftMotorSpeed = caps->Vibration.wRightMotorSpeed = 0xFFFF;
    return ERROR_SUCCESS;
}

static void hook(HMODULE mod, LPCSTR name, void* detour, void** orig) {
    void* target = (void*)GetProcAddress(mod, name);
    if (target == NULL) {
        plog("export %s not found", HIWORD(name) ? name : "(ordinal)");
        return;
    }
    MH_STATUS s = MH_CreateHook(target, detour, orig);
    if (s == MH_OK) {
        s = MH_EnableHook(target);
    }
    plog("hook %s: %s", HIWORD(name) ? name : "XInputGetStateEx(#100)", MH_StatusToString(s));
}

static void install(void) {
    char path[MAX_PATH];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    char* slash = strrchr(path, '\\');
    if (slash != NULL) {
        strcpy(slash + 1, "reframework\\data\\mhrise_framepad.log");
        g_log = fopen(path, "w");
    }
    HMODULE xi = LoadLibraryA("xinput1_4.dll");
    if (xi == NULL) {
        plog("xinput1_4.dll not loadable");
        return;
    }
    MH_Initialize();
    hook(xi, "XInputGetState", (void*)hk_get_state, (void**)&o_get_state);
    hook(xi, (LPCSTR)100, (void*)hk_get_state_ex, (void**)&o_get_state_ex);
    hook(xi, "XInputGetCapabilities", (void*)hk_get_caps, (void**)&o_get_caps);
}

// ---- REFramework plugin entry points ----
typedef struct {
    int major;
    int minor;
    int patch;
    const char* game_name;
} REFrameworkPluginVersion;

__declspec(dllexport) void reframework_plugin_required_version(REFrameworkPluginVersion* v) {
    v->major = 1;
    v->minor = 0;
    v->patch = 0;
    v->game_name = NULL;  // any game; only ever installed for Rise
}

__declspec(dllexport) bool reframework_plugin_initialize(const void* param) {
    (void)param;
    install();
    return true;
}
