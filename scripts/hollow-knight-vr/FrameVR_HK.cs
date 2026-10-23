// FrameVR_HK: Steam Frame tweak on top of HollowKnight_VREnhanced (BepInEx plugin, C# 5 so .NET 4 csc builds it).
//  - Real pause/inventory buttons: the SteamVR Start/Back actions (Frame menu / view buttons in the Frame binding)
//    press Start/Back on the mod's virtual Xbox pad. The UnityVR core only reaches them through a stick-click "hotkey".
// build: csc /target:library /out:FrameVR_HK.dll /r:<refs> FrameVR_HK.cs
using System;
using BepInEx;
using HarmonyLib;
using UnityVR_Bepinex.input;
using Valve.VR;

namespace FrameVR
{
    [BepInPlugin("framevr.hollowknight", "FrameVR Hollow Knight", "1.3.0")]
    public class FrameVRPlugin : BaseUnityPlugin
    {
        static BepInEx.Logging.ManualLogSource log;

        void Awake()
        {
            log = Logger;
            Harmony harmony = new Harmony("framevr.hollowknight");
            Patch(harmony, "StartButtonDown", "StartDown");
            Patch(harmony, "StartButtonUp", "StartUp");
            Patch(harmony, "BackButtonDown", "BackDown");
            Patch(harmony, "BackButtonUp", "BackUp");
            // The core's "hotkey" gesture (left controller within 25 cm of the head) buzzes the controller every frame
            // and re-purposes the stick clicks; the Frame has real Start/Back buttons, so it is disabled outright.
            try
            {
                harmony.Patch(AccessTools.Method(typeof(VRInputManager), "UpdateHotKey"),
                    new HarmonyMethod(typeof(FrameVRPlugin), "NoHotKey"));
            }
            catch (Exception e)
            {
                log.LogError("patch UpdateHotKey failed: " + e);
            }
            // The Frame driver reports a held d-pad as ~150 ms pulses every ~250 ms, so the core presses and releases
            // the pad's d-pad per pulse (one step per pulse in game). Latch: each pulse (re)arms the direction for
            // HoldSeconds, the core's release is immediately undone while armed, and Update releases once pulses stop.
            Patch(harmony, "NorthDPADDown", "UpDown"); Patch(harmony, "NorthDPADUp", "UpUp");
            Patch(harmony, "SouthDPADDown", "DownDown"); Patch(harmony, "SouthDPADUp", "DownUp");
            Patch(harmony, "WestDPADDown", "LeftDown"); Patch(harmony, "WestDPADUp", "LeftUp");
            Patch(harmony, "EastDPADDown", "RightDown"); Patch(harmony, "EastDPADUp", "RightUp");
            // ...and the core's left-joystick handler (an every-frame update listener) clears all four d-pad buttons
            // each frame, so the armed directions are re-asserted right after it runs.
            Patch(harmony, "LeftJoystick", "AfterLeftJoystick");
            // The driver's click pulses stop after ~1 s even while held, but the d-pad's (shared) touch sensor follows
            // the thumb. The Frame binding sends d-pad touch to the ClickLeftJoystick action (unused by Hollow Knight):
            // while it is held, every direction pulsed since the touch began stays pressed. Prefixes swallow the core's
            // own L3 handling for it.
            try
            {
                harmony.Patch(AccessTools.Method(typeof(VRInputManagerSteamVR), "ClickLeftJoystickDown"),
                    new HarmonyMethod(typeof(FrameVRPlugin), "TouchDown"));
                harmony.Patch(AccessTools.Method(typeof(VRInputManagerSteamVR), "ClickLeftJoystickUp"),
                    new HarmonyMethod(typeof(FrameVRPlugin), "TouchUp"));
            }
            catch (Exception e)
            {
                log.LogError("patch ClickLeftJoystick failed: " + e);
            }
            if (Environment.GetEnvironmentVariable("FRAMEVR_DEBUG") == "1")
            {
                VRInputManagerSteamVR.OnEastDPADDown += delegate { Trace("dpad_right down"); };
                VRInputManagerSteamVR.OnEastDPADUp += delegate { Trace("dpad_right up"); };
                VRInputManagerSteamVR.OnWestDPADDown += delegate { Trace("dpad_left down"); };
                VRInputManagerSteamVR.OnWestDPADUp += delegate { Trace("dpad_left up"); };
                VRInputManagerSteamVR.OnNorthDPADDown += delegate { Trace("dpad_up down"); };
                VRInputManagerSteamVR.OnNorthDPADUp += delegate { Trace("dpad_up up"); };
            }
            log.LogInfo("FrameVR Hollow Knight loaded: Start/Back on the pad, hotkey gesture off, d-pad pulses latched");
        }

        static bool NoHotKey()
        {
            VRInputManager._hotkey = false;
            return false;
        }

        static void Trace(string what)
        {
            log.LogInfo(string.Format("[trace t={0:F3}] {1}", UnityEngine.Time.realtimeSinceStartup, what));
        }

        static void Patch(Harmony harmony, string method, string postfix)
        {
            try
            {
                harmony.Patch(AccessTools.Method(typeof(VRInputManagerSteamVR), method), null,
                    new HarmonyMethod(typeof(FrameVRPlugin), postfix));
            }
            catch (Exception e)
            {
                log.LogError("patch " + method + " failed: " + e);
            }
        }

        static void SetButton(string name, bool down)
        {
            ViGemVRControllers v = ViGemVRControllers.instance;
            if (v == null || v._controller == null) return;
            v._controller.SetButtonState(v.GetControllerButtonType(name, ViGemVRControllers.InputCategory.button), down);
            v._controller.SubmitReport();
        }

        const float HoldSeconds = 0.4f;
        static readonly string[] Dirs = { "Up", "Down", "Left", "Right" };
        static readonly float[] armedUntil = new float[4];
        static readonly float[] lastPulse = new float[4];
        static readonly bool[] pressed = new bool[4];
        static bool touchHeld;
        static float touchStart;

        static bool Armed(int i)
        {
            float now = UnityEngine.Time.realtimeSinceStartup;
            return now < armedUntil[i] || (touchHeld && lastPulse[i] >= touchStart);
        }

        static void Arm(int i)
        {
            float now = UnityEngine.Time.realtimeSinceStartup;
            // A real d-pad can't hold both directions of one axis: the new pulse releases the opposite one
            // (Up<->Down, Left<->Right) so a thumb rolling across the pad changes direction without lifting.
            int opposite = i ^ 1;
            if (pressed[opposite])
            {
                pressed[opposite] = false;
                armedUntil[opposite] = 0f;
                lastPulse[opposite] = 0f;
                SetButton(Dirs[opposite], false);
            }
            lastPulse[i] = now;
            armedUntil[i] = now + HoldSeconds;
            pressed[i] = true;
            SetButton(Dirs[i], true);
        }

        static void Reassert(int i)
        {
            if (Armed(i)) SetButton(Dirs[i], true);
        }

        static bool TouchDown()
        {
            touchHeld = true;
            touchStart = UnityEngine.Time.realtimeSinceStartup;
            return false;
        }

        static bool TouchUp()
        {
            touchHeld = false;
            return false;
        }

        void Update()
        {
            for (int i = 0; i < 4; i++)
            {
                if (pressed[i] && !Armed(i))
                {
                    pressed[i] = false;
                    SetButton(Dirs[i], false);
                }
            }
        }

        static void AfterLeftJoystick()
        {
            for (int i = 0; i < 4; i++) Reassert(i);
        }

        static void UpDown() { Arm(0); }
        static void UpUp() { Reassert(0); }
        static void DownDown() { Arm(1); }
        static void DownUp() { Reassert(1); }
        static void LeftDown() { Arm(2); }
        static void LeftUp() { Reassert(2); }
        static void RightDown() { Arm(3); }
        static void RightUp() { Reassert(3); }

        static void StartDown() { SetButton("start", true); }
        static void StartUp() { SetButton("start", false); }
        static void BackDown() { SetButton("back", true); }
        static void BackUp() { SetButton("back", false); }
    }
}
