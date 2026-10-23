// FrameVR_CS: Steam Frame bridge for Circuit Superstars VR (Astienth's UnityVR_Bepinex mod, which has no motion
// controller support: the game wants an Xbox pad, and Steam Input's pad goes quiet once SteamVR owns the Frame
// controllers). This BepInEx plugin reads the mod's SteamVR actions every frame and drives a virtual Xbox 360 pad
// through the ViGEm client API; on the Frame that client is framepad's stand-in (shared memory -> uinput_pad).
// Mapping is 1:1 with an Xbox pad: A/B/X/Y, triggers, LeftGrip/RightGrip actions -> LB/RB (the Frame binding feeds
// the bumpers into those), sticks + clicks, d-pad, Start/Back. C# 5 so the .NET Framework csc builds it.
using System;
using System.Collections;
using BepInEx;
using Nefarius.ViGEm.Client;
using Nefarius.ViGEm.Client.Targets;
using Nefarius.ViGEm.Client.Targets.Xbox360;
using UnityEngine;
using Valve.VR;

namespace FrameVR
{
    [BepInPlugin("framevr.circuitsuperstars", "FrameVR Circuit Superstars", "1.0.0")]
    public class FrameVRPlugin : BaseUnityPlugin
    {
        ViGEmClient client;
        IXbox360Controller pad;
        bool ready;
        int frames;

        void Awake()
        {
            StartCoroutine(Init());
        }

        IEnumerator Init()
        {
            float t0 = Time.realtimeSinceStartup;
            while (!SteamVR_Input.initialized && Time.realtimeSinceStartup - t0 < 120f) yield return null;
            if (!SteamVR_Input.initialized)
            {
                Logger.LogError("SteamVR input never initialised; no virtual pad");
                yield break;
            }
            try
            {
                client = new ViGEmClient();
                pad = client.CreateXbox360Controller();
                pad.Connect();
                pad.AutoSubmitReport = false;
                ready = true;
                Logger.LogInfo("FrameVR Circuit Superstars: virtual Xbox pad connected, driven by the SteamVR default action set");
            }
            catch (Exception e)
            {
                Logger.LogError("virtual pad failed: " + e);
            }
        }

        static short Axis(float v)
        {
            return (short)(Mathf.Clamp(v, -1f, 1f) * 32767f);
        }

        void Update()
        {
            if (!ready) return;
            try
            {
                SteamVR_Input_ActionSet_default d = SteamVR_Actions._default;
                SteamVR_Input_Sources any = SteamVR_Input_Sources.Any;
                pad.SetButtonState(Xbox360Button.A, d.ButtonA.GetState(any));
                pad.SetButtonState(Xbox360Button.B, d.ButtonB.GetState(any));
                pad.SetButtonState(Xbox360Button.X, d.ButtonX.GetState(any));
                pad.SetButtonState(Xbox360Button.Y, d.ButtonY.GetState(any));
                pad.SetButtonState(Xbox360Button.LeftShoulder, d.LeftGrip.GetState(any));
                pad.SetButtonState(Xbox360Button.RightShoulder, d.RightGrip.GetState(any));
                pad.SetButtonState(Xbox360Button.Start, d.Start.GetState(any));
                pad.SetButtonState(Xbox360Button.Back, d.Back.GetState(any));
                pad.SetButtonState(Xbox360Button.LeftThumb, d.ClickLeftJoystick.GetState(any));
                pad.SetButtonState(Xbox360Button.RightThumb, d.ClickRightJoystick.GetState(any));
                pad.SetButtonState(Xbox360Button.Up, d.NorthDPAD.GetState(any));
                pad.SetButtonState(Xbox360Button.Down, d.SouthDPAD.GetState(any));
                pad.SetButtonState(Xbox360Button.Left, d.WestDPAD.GetState(any));
                pad.SetButtonState(Xbox360Button.Right, d.EastDPAD.GetState(any));
                pad.SetSliderValue(Xbox360Slider.LeftTrigger, (byte)(Mathf.Clamp01(d.LeftTrigger.GetAxis(any)) * 255f));
                pad.SetSliderValue(Xbox360Slider.RightTrigger, (byte)(Mathf.Clamp01(d.RightTrigger.GetAxis(any)) * 255f));
                Vector2 l = d.LeftJoystick.GetAxis(any);
                Vector2 r = d.RightJoystick.GetAxis(any);
                pad.SetAxisValue(Xbox360Axis.LeftThumbX, Axis(l.x));
                pad.SetAxisValue(Xbox360Axis.LeftThumbY, Axis(l.y));
                pad.SetAxisValue(Xbox360Axis.RightThumbX, Axis(r.x));
                pad.SetAxisValue(Xbox360Axis.RightThumbY, Axis(r.y));
                pad.SubmitReport();
                if (++frames == 600) Logger.LogInfo("FrameVR: pad reports flowing (600 frames)");
            }
            catch (Exception e)
            {
                ready = false;
                Logger.LogError("pad update failed, stopping: " + e);
            }
        }
    }
}
