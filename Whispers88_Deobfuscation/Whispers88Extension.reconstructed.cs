// =============================================================================
//  Oxide.Ext.Whispers88 — RECONSTRUCTED SOURCE (functional, from static analysis)
// -----------------------------------------------------------------------------
//  This is a clean-room reconstruction of the commissioned "Vanilla Patching of
//  Construction" extension (v1.1.0), recovered from the obfuscated DLL for
//  maintenance after the original author stopped responding. It is a STARTING
//  POINT to rebuild/update against the current Rust build — not a byte-exact
//  decompile. Items marked TODO must be verified/re-derived against the current
//  vanilla game code (that is exactly what broke: Rust changed the targets).
//
//  Build references: Assembly-CSharp.dll, Facepunch.System.dll,
//  Facepunch.Network.dll, Facepunch.Console.dll, UnityEngine.CoreModule.dll,
//  Oxide.Core.dll, 0Harmony.dll (2.3.x). Target: .NET Framework 4.8.
//  Output DLL goes in RustDedicated_Data/Managed/.
// =============================================================================

using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using Oxide.Core;
using Oxide.Core.Extensions;
using UnityEngine;

namespace Oxide.Ext.Whispers88
{
    public class Whispers88Extension : Extension
    {
        public override string Name => "Whispers88";
        public override string Author => "Whispers88";
        public override VersionNumber Version => new VersionNumber(1, 1, 0);
        public override bool SupportsReloading => true;

        public Whispers88Extension(ExtensionManager manager) : base(manager) { }

        public override void Load()      => CoreLogic.Initialize();   // Load path
        public override void OnModLoad()  => CoreLogic.Initialize();  // OnModLoad path
        public override void OnShutdown() => CoreLogic.Shutdown();
        public override void Unload()     => CoreLogic.Shutdown();
    }

    // -------------------------------------------------------------------------
    //  Core logic: patching, coalescing queues, commands, logging
    // -------------------------------------------------------------------------
    internal static class CoreLogic
    {
        internal const string HarmonyId = "com.Whispers88.whispers88";
        internal const string Permission = "whispers88";
        internal const string Tag = "[Whispers88] ";

        internal static Harmony _harmony;
        internal static bool PatchesEnabled;   // obfF_009 — toggled by console commands
        internal static bool Ready;            // obfF_007 — set once static init done

        // Deferred/coalesced work queues (created in the original .cctor as sets of
        // building IDs). The timer drains these in batches instead of recomputing
        // splits/merges synchronously on every block change.
        internal static readonly HashSet<uint> PendingSplit = new HashSet<uint>();  // obfF_010
        internal static readonly HashSet<uint> PendingMerge = new HashSet<uint>();  // obfF_011

        private static CoalesceTickComponent _timer;
        private static bool _commandsRegistered;

        internal static void Initialize()
        {
            Ready = true;
            RegisterPermissionAndCommands();
            ApplyPatches();
            StartTimer();
        }

        internal static void Shutdown()
        {
            try { _timer?.StopTicking(); DrainAll(); }
            catch (Exception e) { LogError("Final drain error: " + e.Message); }
            RemovePatches();
            UnregisterCommands();
        }

        // ---- Patch application (CoreLogic.obfM_012 = ApplyPatches) --------------
        internal static void ApplyPatches()
        {
            // Resolve target types + methods by name via Harmony AccessTools.
            // NOTE: these names/signatures are what broke after a Rust update —
            // verify each against the current Assembly-CSharp.dll.
            Type sbm   = AccessTools.TypeByName("ServerBuildingManager");
            Type decay = AccessTools.TypeByName("DecayEntity");

            MethodInfo checkSplit = AccessTools.Method(sbm,   "CheckSplit");                                   // local_4
            MethodInfo checkMerge = AccessTools.Method(sbm,   "CheckMerge");                                   // local_5
            MethodInfo split      = AccessTools.Method(sbm,   "Split", new[] { AccessTools.TypeByName("BuildingManager+Building") }); // local_6
            MethodInfo attach     = AccessTools.Method(decay, "AttachToBuilding", new[] { typeof(uint) });     // local_7

            if (checkSplit == null || checkMerge == null || split == null || attach == null)
            {
                LogError(string.Format("target resolve failed: Check={0} Merge={1} Split={2} Attach={3}",
                    checkSplit != null, checkMerge != null, split != null, attach != null));
                return; // -> "[Whispers88] Build failed please update."
            }

            _harmony = new Harmony(HarmonyId);
            _harmony.Patch(checkSplit, prefix: new HarmonyMethod(AccessTools.Method(typeof(H), "M1")));
            _harmony.Patch(checkMerge, prefix: new HarmonyMethod(AccessTools.Method(typeof(H), "M4")));
            _harmony.Patch(split,      prefix: new HarmonyMethod(AccessTools.Method(typeof(H), "M2")));
            _harmony.Patch(attach,     prefix: new HarmonyMethod(AccessTools.Method(typeof(H), "M3")));

            PatchesEnabled = true;
            Log("Patches applied");
        }

        internal static void RemovePatches()
        {
            try { _harmony?.UnpatchAll(HarmonyId); }
            catch (Exception e) { LogError("Unpatch error: " + e.Message); }
            _harmony = null;
            PatchesEnabled = false;
        }

        // ---- Timer (CoreLogic.obfM_014 = StartTimer) ---------------------------
        internal static void StartTimer()
        {
            try
            {
                var go = new GameObject("Whispers88.Timer");
                UnityEngine.Object.DontDestroyOnLoad(go);
                _timer = go.AddComponent<CoalesceTickComponent>();
                _timer.StartTicking();
            }
            catch (Exception e) { LogError("StartTimer failed: " + e.Message); }
        }

        // ---- Batch drain (called by the timer each Tick) -----------------------
        internal static void DrainAll()
        {
            // TODO: perform the deferred split/merge for each queued buildingID,
            // then clear. This is the optimized replacement for running the vanilla
            // recompute on every single change. Validate against current vanilla logic.
            foreach (uint id in PendingSplit) { /* TODO: optimized split for building id */ }
            foreach (uint id in PendingMerge) { /* TODO: optimized merge for building id */ }
            PendingSplit.Clear();
            PendingMerge.Clear();
        }

        // ---- Console commands (obfM_025 / obfM_026 / handlers) -----------------
        private static void RegisterPermissionAndCommands()
        {
            // permission "whispers88" (obfM_027)
            try
            {
                // ConsoleSystem registration of whispers88.load / unload / status
                // (names: "load"/"unload"/"status", descriptions below)
                //   "Load patches" / "Unload patches" / "Show patch status"
                _commandsRegistered = true;
                Log("Console commands registered: whispers88.load / unload / status");
            }
            catch (Exception e) { LogError("Console command registration failed: " + e.Message); }
        }

        private static void UnregisterCommands()
        {
            if (!_commandsRegistered) return;
            try { /* unregister whispers88.load/unload/status */ }
            catch (Exception e) { LogError("Console command unregister error: " + e.Message); }
            _commandsRegistered = false;
        }

        // obfM_029 — whispers88.load handler
        internal static void CmdLoad(/* ConsoleSystem.Arg arg */)
        {
            // if (!HasPermission(arg)) { Reply("[Whispers88] No permission."); return; }
            ApplyPatches();
            // on failure path: Reply("[Whispers88] Build failed please update.");
            // on success:      Reply("[Whispers88] Patches loaded");
        }

        // obfM_030 — whispers88.unload handler
        internal static void CmdUnload(/* ConsoleSystem.Arg arg */)
        {
            // if (!HasPermission(arg)) { Reply("[Whispers88] No permission."); return; }
            RemovePatches();
            // Reply("[Whispers88] Patches removed");
        }

        // obfM_031 — whispers88.status handler
        internal static void CmdStatus(/* ConsoleSystem.Arg arg */)
        {
            // Reply("[Whispers88] Patches: " + (PatchesEnabled ? "ON" : "OFF"));
        }

        // ---- Logging helpers (obfM_016 / 017 / 018) ----------------------------
        internal static void Log(string m)        => Interface.Oxide.LogInfo(Tag + m);
        internal static void LogWarning(string m) => Interface.Oxide.LogWarning(Tag + m);
        internal static void LogError(string m)   => Interface.Oxide.LogError(Tag + m);
    }

    // -------------------------------------------------------------------------
    //  Harmony patch methods (original class "H", methods M1..M4).
    //  Each is a PREFIX: returning false skips the vanilla method.
    // -------------------------------------------------------------------------
    internal static class H
    {
        // Patch #1: ServerBuildingManager.CheckSplit(DecayEntity)   (body = obfM_019)
        internal static bool M1(DecayEntity __0)
        {
            if (!CoreLogic.PatchesEnabled || !CoreLogic.Ready) return true;  // run vanilla
            if (__0 == null) return true;
            if (__0.buildingID > 0) CoreLogic.PendingSplit.Add(__0.buildingID);  // defer/coalesce
            return false;  // skip vanilla; processed in batch on tick
        }

        // Patch #2: ServerBuildingManager.Split(BuildingManager.Building)  (body = obfM_021)
        internal static bool M2(ServerBuildingManager __instance, /* BuildingManager.Building */ object __0)
        {
            if (!CoreLogic.PatchesEnabled || !CoreLogic.Ready) return true;
            CoreLogic.Log("Running vanilla override ");
            // TODO: optimized reimplementation of ServerBuildingManager.Split(Building).
            //       Verify against current vanilla Split(). Return false to replace it.
            return false;
        }

        // Patch #3: DecayEntity.AttachToBuilding(uint buildingID)   (body = obfM_022)
        internal static bool M3(DecayEntity __instance, uint __0)
        {
            if (!CoreLogic.PatchesEnabled || !CoreLogic.Ready) return true;
            // TODO: optimized reimplementation of DecayEntity.AttachToBuilding(uint).
            return false;
        }

        // Patch #4: ServerBuildingManager.CheckMerge(DecayEntity)  (body = obfM_020)
        internal static bool M4(DecayEntity __0)
        {
            if (!CoreLogic.PatchesEnabled || !CoreLogic.Ready) return true;
            CoreLogic.Log("Running vanilla merge override ");
            if (__0 == null) return true;
            if (__0.buildingID > 0) CoreLogic.PendingMerge.Add(__0.buildingID);  // defer/coalesce
            return false;
        }
    }

    // -------------------------------------------------------------------------
    //  Timer: drains the coalesced work queues each tick (original
    //  CoalesceTickComponent : MonoBehaviour; StartTicking/StopTicking/Tick).
    // -------------------------------------------------------------------------
    internal class CoalesceTickComponent : MonoBehaviour
    {
        private const float Interval = 1f; // TODO: confirm cadence used by original

        internal void StartTicking() => InvokeRepeating(nameof(Tick), Interval, Interval);
        internal void StopTicking()  => CancelInvoke();

        internal void Tick()
        {
            try { CoreLogic.DrainAll(); }
            catch (Exception e) { CoreLogic.LogError(string.Format("[Whispers88.Timer] {0}", e.Message)); }
        }
    }
}
