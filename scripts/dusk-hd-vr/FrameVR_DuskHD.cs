// FrameVR_DuskHD: Steam Frame tweaks on top of Dusk_HD_VR (BepInEx plugin, C# 5 so .NET 4 csc builds it).
//  - Head-oriented locomotion: the left stick is rotated by the headset's yaw relative to the game body
//    before it reaches the virtual Xbox pad, so "forward" is where you look.
//  - Real menu buttons: the SteamVR Start/Back actions (Frame menu / view buttons in the Frame binding)
//    press Start/Back on the virtual pad. The base mod only offered a hand-near-head + stick-click gesture.
//  - Logs the player's collider height and headset height once per scene, to tune VRCamScale.
using System;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;
using UnityVR_Bepinex.cam;
using UnityVR_Bepinex.input;
using Valve.VR;

namespace FrameVR
{
    [BepInPlugin("framevr.duskhd", "FrameVR DUSK HD", "1.0.0")]
    public class FrameVRPlugin : BaseUnityPlugin
    {
        static ConfigEntry<bool> headLocomotion;
        static ConfigEntry<bool> diag;
        static BepInEx.Logging.ManualLogSource log;
        float nextProbe;
        bool probed;
        string probedScene = "";

        void Awake()
        {
            log = Logger;
            headLocomotion = Config.Bind("Controls", "headOrientedLocomotion", true,
                "Left stick moves toward where the headset faces instead of where the game body faces");
            diag = Config.Bind("Debug", "logInputState", true, "Log the pad state Unity sees once a second");
            Harmony harmony = new Harmony("framevr.duskhd");
            Patch(harmony, "LeftJoystick", "LeftJoystickPrefix", null);
            Patch(harmony, "StartButtonDown", null, "StartDown");
            Patch(harmony, "StartButtonUp", null, "StartUp");
            Patch(harmony, "BackButtonDown", null, "BackDown");
            Patch(harmony, "BackButtonUp", null, "BackUp");
            log.LogInfo("FrameVR DUSK HD loaded, headOrientedLocomotion=" + headLocomotion.Value);
        }

        static void Patch(Harmony harmony, string method, string prefix, string postfix)
        {
            try
            {
                harmony.Patch(AccessTools.Method(typeof(VRInputManagerSteamVR), method),
                    prefix == null ? null : new HarmonyMethod(typeof(FrameVRPlugin), prefix),
                    postfix == null ? null : new HarmonyMethod(typeof(FrameVRPlugin), postfix));
            }
            catch (Exception e)
            {
                log.LogError("patch " + method + " failed: " + e);
            }
        }

        // Head yaw relative to the VR rig root (which follows the game body's yaw), in radians.
        static float HeadYaw()
        {
            if (!headLocomotion.Value || VRHandler.vrCamera == null || VRHandler.camRoot == null) return 0f;
            Quaternion rel = Quaternion.Inverse(VRHandler.camRoot.transform.rotation) * VRHandler.vrCamera.transform.rotation;
            Vector3 f = rel * Vector3.forward;
            if (f.x * f.x + f.z * f.z < 1e-4f) return 0f;
            return Mathf.Atan2(f.x, f.z);
        }

        static Vector2 ToHead(Vector2 v)
        {
            float a = HeadYaw();
            float c = Mathf.Cos(a), s = Mathf.Sin(a);
            return new Vector2(v.x * c + v.y * s, -v.x * s + v.y * c);
        }

        static void LeftJoystickPrefix(ref Vector2 axis)
        {
            if (!VRInputManager._hotkey) axis = ToHead(axis);
        }

        static void SetButton(string name, bool down)
        {
            ViGemVRControllers v = ViGemVRControllers.instance;
            if (v == null || v._controller == null) return;
            v._controller.SetButtonState(v.GetControllerButtonType(name, ViGemVRControllers.InputCategory.button), down);
            v._controller.SubmitReport();
        }

        static void StartDown() { SetButton("start", true); }
        static void StartUp() { SetButton("start", false); }
        static void BackDown() { SetButton("back", true); }
        static void BackUp() { SetButton("back", false); }

        void Update()
        {
            // SteamVR only reports stick changes; keep the direction following the head while the stick is held.
            ViGemVRControllers v = ViGemVRControllers.instance;
            if (headLocomotion.Value && v != null && v._controller != null && !VRInputManager._hotkey)
            {
                Vector2 stick = SteamVR_Actions._default.LeftJoystick.GetAxis(SteamVR_Input_Sources.Any);
                if (stick.sqrMagnitude > 0.0025f)
                {
                    Vector2 m = ToHead(stick);
                    v._controller.SetAxisValue(v.GetControllerButtonType("LeftThumbX", ViGemVRControllers.InputCategory.axis), (short)(Mathf.Clamp(m.x, -1f, 1f) * 32767f));
                    v._controller.SetAxisValue(v.GetControllerButtonType("LeftThumbY", ViGemVRControllers.InputCategory.axis), (short)(Mathf.Clamp(m.y, -1f, 1f) * 32767f));
                }
            }
            Probe();
            if (diag.Value) Diag();
        }

        float nextDiag;

        // Once a second: what Unity itself sees from the pad, and the mod/game state that can swallow input.
        void Diag()
        {
            if (Time.realtimeSinceStartup < nextDiag) return;
            nextDiag = Time.realtimeSinceStartup + 1f;
            string buttons = "";
            for (int i = 0; i < 20; i++)
                if (Input.GetKey(KeyCode.JoystickButton0 + i)) buttons += i + " ";
            string axes = "";
            for (int i = 1; i <= 10; i++)
            {
                float a = 0f;
                try { a = Input.GetAxisRaw("joystickaxis" + i); } catch (Exception) { }
                if (Mathf.Abs(a) > 0.05f) axes += i + "=" + a.ToString("0.00") + " ";
            }
            string hand = "none";
            if (VRInputManager.LeftHand != null && VRHandler.vrCamera != null)
                hand = (VRInputManager.LeftHand.transform.position - VRHandler.vrCamera.transform.position).magnitude.ToString("0.00");
            Vector2 stick = SteamVR_Actions._default.LeftJoystick.GetAxis(SteamVR_Input_Sources.Any);
            InGameMenuScript menu = UnityEngine.Object.FindObjectOfType<InGameMenuScript>();
            log.LogInfo("diag joys=[" + string.Join("|", Input.GetJoystickNames()) + "] btn=" + buttons + " axes=" + axes
                + " vrStick=" + stick + " hotkey=" + VRInputManager._hotkey + " leftHandToHead=" + hand
                + " gamepad=" + (MyInputManager.activeGamepad == null ? "null" : MyInputManager.activeGamepad.GetType().Name)
                + " enable=" + (MyInputManager.Instance != null && MyInputManager.Instance.enablecontroller)
                + " paused=" + (menu != null && menu.isPaused) + " timeScale=" + Time.timeScale);
        }

        void Probe()
        {
            string scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;
            if (scene != probedScene) { probedScene = scene; probed = false; nextProbe = Time.realtimeSinceStartup + 8f; }
            if (probed || Time.realtimeSinceStartup < nextProbe) return;
            nextProbe = Time.realtimeSinceStartup + 5f;
            CharacterController cc = UnityEngine.Object.FindObjectOfType<CharacterController>();
            if (cc == null || VRHandler.vrCamera == null || VRHandler.camRoot == null) return;
            probed = true;
            Transform root = VRHandler.camRoot.transform;
            log.LogInfo("probe scene=" + scene + " player=" + cc.name + " ccHeight=" + cc.height + " ccScaleY=" + cc.transform.lossyScale.y
                + " camRootAboveFeet=" + (root.position.y - (cc.bounds.min.y))
                + " camRootScale=" + root.localScale
                + " hmdLocal=" + VRHandler.vrCamera.transform.localPosition
                + " hmdAboveRoot=" + (VRHandler.vrCamera.transform.position.y - root.position.y));
        }
    }
}
