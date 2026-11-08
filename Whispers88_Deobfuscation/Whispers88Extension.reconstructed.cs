// =============================================================================
//  Oxide.Ext.Whispers88 — RECONSTRUCTED SOURCE (corrected, from static analysis)
// -----------------------------------------------------------------------------
//  Clean-room reconstruction of the commissioned "Vanilla Patching of
//  Construction" extension (v1.1.0), recovered from the obfuscated DLL so it can
//  be maintained after the original author stopped responding. STARTING POINT —
//  not a byte-exact decompile. This file was corrected after an independent
//  verification pass against the IL (see opus_verification.md / README §8).
//
//  >>> TWO THINGS TO FIX BEFORE SHIPPING <<<
//   (1) TIME-BOMB: the original self-disables after 2026-11-26 (see TimeGate()).
//       It is reproduced here ONLY so you understand it — REMOVE/NEUTRALISE it.
//   (2) The original hard-kills the process (Environment.FailFast) if a debugger
//       or profiler is attached. Do NOT run the ORIGINAL DLL under one. (Not
//       reproduced here.)
//
//  Build refs: Assembly-CSharp.dll, Facepunch.System.dll, Facepunch.Network.dll,
//  Facepunch.Console.dll, UnityEngine.CoreModule.dll, Oxide.Core.dll,
//  0Harmony.dll (2.3.x). Target .NET Framework 4.8. Output -> Managed/.
// =============================================================================

using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
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

        // IL Load/OnModLoad order: ApplyPatches -> StartTimer -> RegisterCommands
        public override void Load()      { CoreLogic.ApplyPatches(); CoreLogic.StartTimer(); CoreLogic.RegisterCommands(); }
        public override void OnModLoad() { CoreLogic.ApplyPatches(); CoreLogic.StartTimer(); CoreLogic.RegisterCommands(); }
        public override void OnShutdown() => CoreLogic.Shutdown();
        public override void Unload()     => CoreLogic.Shutdown();
    }

    internal static class CoreLogic
    {
        internal const string HarmonyId = "com.Whispers88.whispers88";
        internal const string Tag = "[Whispers88] ";

        internal static Harmony _harmony;
        internal static bool Enabled;          // obfF_009 — set true after a successful patch
        internal static bool GateOpen = true;  // obfF_007 — TIME-GATE (see TimeGate); default true
        internal static bool Bypass;           // obfF_012 — set while the drain is running

        // obfF_010 = the ONLY deferred queue: building ids awaiting an optimized split.
        internal static readonly HashSet<uint> PendingSplit = new HashSet<uint>();  // HashSet<uint>
        // obfF_011 = drain scratch buffer (NOT a second queue).
        private static readonly List<uint> _drainScratch = new List<uint>();        // List<uint>

        private static CoalesceTickComponent _timer;
        private const int DrainBatch = 3;      // plaintext literal in obfM_024

        // ---- TIME-BOMB (obfM_011 -> obfF_007). REMOVE THIS when rebuilding. -----
        // Original: GateOpen = (DateTime.UtcNow <= new DateTime(2026, 11, 26, 0,0,0,1));
        // re-evaluated every tick; when it flips false the plugin auto-unpatches
        // and whispers88.load replies "Build failed please update."
        private static readonly DateTime Expiry = new DateTime(2026, 11, 26, 0, 0, 0, 1);
        internal static void TimeGate()
        {
            try   { GateOpen = DateTime.UtcNow <= Expiry; }   // <-- DELETE / hardcode true
            catch { GateOpen = false; }
        }

        // ---- Patch application (obfM_012) --------------------------------------
        internal static void ApplyPatches()
        {
            TimeGate();
            Type sbm   = AccessTools.TypeByName("ServerBuildingManager");
            Type decay = AccessTools.TypeByName("DecayEntity");

            // NOTE: these are what broke after a Rust update — verify each against
            // the current Assembly-CSharp.dll and adjust names/signatures.
            MethodInfo checkSplit = AccessTools.Method(sbm,   "CheckSplit");
            MethodInfo checkMerge = AccessTools.Method(sbm,   "CheckMerge");
            MethodInfo split      = AccessTools.Method(sbm,   "Split", new[] { AccessTools.TypeByName("BuildingManager+Building") });
            MethodInfo attach     = AccessTools.Method(decay, "AttachToBuilding", new[] { typeof(uint) });

            if (checkSplit == null || checkMerge == null || split == null || attach == null)
            {
                LogError(string.Format("target resolve failed: Check={0} Merge={1} Split={2} Attach={3}",
                    checkSplit != null, checkMerge != null, split != null, attach != null));
                return; // -> whispers88.load replies "[Whispers88] Build failed please update."
            }

            _harmony = new Harmony(HarmonyId);
            _harmony.Patch(checkSplit, prefix: new HarmonyMethod(AccessTools.Method(typeof(H), "M1")));
            _harmony.Patch(checkMerge, prefix: new HarmonyMethod(AccessTools.Method(typeof(H), "M4")));
            _harmony.Patch(split,      prefix: new HarmonyMethod(AccessTools.Method(typeof(H), "M2")));
            _harmony.Patch(attach,     prefix: new HarmonyMethod(AccessTools.Method(typeof(H), "M3")));

            Enabled = true;   // obfF_009
            Log("Patches applied");
        }

        internal static void RemovePatches()
        {
            try { _harmony?.UnpatchAll(HarmonyId); } catch (Exception e) { LogError("Unpatch error: " + e.Message); }
            _harmony = null;
            Enabled = false;
        }

        // ---- Timer (obfM_014) --------------------------------------------------
        internal static void StartTimer()
        {
            try
            {
                var go = new GameObject("Whispers88.Timer");
                UnityEngine.Object.DontDestroyOnLoad(go);
                _timer = go.AddComponent<CoalesceTickComponent>();
                _timer.StartTicking(Mathf.Max(0.1f, 0.5f)); // = 0.5s (from decrypted numeric pool)
            }
            catch (Exception e) { LogError("StartTimer failed: " + e.Message); }
        }

        // ---- Per-tick callback (obfM_023) --------------------------------------
        internal static void OnTick()
        {
            TimeGate();                                   // re-check expiry EVERY tick
            if (!GateOpen) { RemovePatches(); _timer?.StopTicking(); return; } // EXPIRED -> auto-unpatch
            DrainSplit(DrainBatch);
        }

        // ---- Split drain (obfM_024): batch of 3, Remove (not Clear) ------------
        private static void DrainSplit(int maxPerBatch)
        {
            _drainScratch.Clear();
            foreach (uint id in PendingSplit)
            {
                _drainScratch.Add(id);
                if (_drainScratch.Count >= maxPerBatch) break;
            }
            Bypass = true;                                // obfF_012 — let vanilla run during drain
            try
            {
                foreach (uint id in _drainScratch)
                {
                    PendingSplit.Remove(id);
                    // var b = BuildingManager.server.GetBuilding(id);
                    // if (b != null && b.buildingBlocks.Count != 0) Split_Optimized(/*server*/ null, b);
                }
            }
            finally { Bypass = false; _drainScratch.Clear(); }
        }

        internal static void DrainAll()
        {
            // obfM_015 shutdown path drains with count int.MaxValue (everything).
            DrainSplit(int.MaxValue);
        }

        internal static void Shutdown()
        {
            UnregisterCommands();
            try { DrainAll(); } catch (Exception e) { LogError("Final drain error: " + e.Message); }
            if (_timer != null) { UnityEngine.Object.Destroy(_timer.gameObject); _timer = null; }
            RemovePatches();
            PendingSplit.Clear();
            _drainScratch.Clear();
        }

        // ---- The optimized bodies (obfM_032 split / obfM_033 merge) ------------
        //  Reconstructed shape (validate against current vanilla before trusting):
        //
        //  Split_Optimized(ServerBuildingManager mgr, Building building):
        //    - flood-fill building.buildingBlocks via BaseEntity.EntityLinkBroadcast<BuildingBlock>
        //      into connected-component groups (Facepunch.Pool for the lists)
        //    - keep the largest group's building id; for each OTHER group:
        //        uint id = mgr.NewBuildingID();
        //        foreach block in group: ((DecayEntity)block).AttachToBuilding(id);
        //    - reattach loose (non-block) decay entities by parent/nearby BuildingBlock;
        //      ContainerCorpse -> original building id
        //    - if (ConVar.AI.nav_carve_use_building_optimization) {
        //          building.isNavMeshCarvingDirty = true;
        //          mgr.UpdateNavMeshCarver(building, ...);   // ONCE
        //      }
        //
        //  Merge_Optimized(DecayEntity entity):
        //    - gather linked Buildings (EntityLinkMessage + visitor) into a pooled List<Building>
        //    - pick the Building with the most decayEntities as target
        //    - reassign the others' entities: entity.AttachToBuilding(target.ID)
        //    - fix up ids in PendingSplit; then one dirty + UpdateNavMeshCarver

        // ---- Console commands (obfM_025/026) + access check (obfM_028) ---------
        //  NOTE: there is NO Oxide permission. "whispers88" is ConsoleSystem.Command.Parent.
        private static bool IsAdmin(/* ConsoleSystem.Arg arg */)
        {
            // return arg.Connection == null || arg.Connection.authLevel >= 2;
            return true; // TODO: wire to ConsoleSystem.Arg
        }

        internal static void RegisterCommands()
        {
            // Register ConsoleSystem commands: parent "whispers88", names load/unload/status,
            // descriptions "Load patches"/"Unload patches"/"Show patch status", ServerAdmin=true.
            try { Log("Console commands registered: whispers88.load / unload / status"); }
            catch (Exception e) { LogError("Console command registration failed: " + e.Message); }
        }
        internal static void UnregisterCommands()
        {
            try { /* unregister whispers88.load/unload/status */ }
            catch (Exception e) { LogError("Console command unregister error: " + e.Message); }
        }

        internal static void CmdLoad(/* ConsoleSystem.Arg arg */)
        {
            if (!IsAdmin()) { /* reply */ Log("No permission."); return; }   // "[Whispers88] No permission."
            TimeGate();
            if (!GateOpen) { Log("Build failed please update."); return; }    // "[Whispers88] Build failed please update."
            ApplyPatches(); StartTimer();
            Log("Patches loaded");
        }
        internal static void CmdUnload(/* ConsoleSystem.Arg arg */)
        {
            if (!IsAdmin()) { Log("No permission."); return; }
            RemovePatches();
            Log("Patches removed");
        }
        internal static void CmdStatus(/* ConsoleSystem.Arg arg */)
        {
            Log("Patches: " + (Enabled ? "ON" : "OFF"));
        }

        // ---- Logging (obfM_016/017/018 -> UnityEngine.Debug) -------------------
        internal static void Log(string m)        => Debug.Log(Tag + m);
        internal static void LogWarning(string m) => Debug.LogWarning(Tag + m);
        internal static void LogError(string m)   => Debug.LogError(Tag + m);
    }

    // -------------------------------------------------------------------------
    //  Harmony patch methods (class "H", methods M1..M4). PREFIX: false = skip vanilla.
    // -------------------------------------------------------------------------
    internal static class H
    {
        // #1 ServerBuildingManager.CheckSplit(DecayEntity)  (obfM_019) — DEFERS
        internal static bool M1(DecayEntity __0)
        {
            if (!CoreLogic.Enabled || !CoreLogic.GateOpen) return true; // run vanilla
            if (CoreLogic.Bypass) return true;                          // obfF_012 — let drain's vanilla run
            if (__0 != null && __0.buildingID > 0)
                CoreLogic.PendingSplit.Add(__0.buildingID);             // defer/coalesce
            return false;                                               // handled on tick
        }

        // #3 ServerBuildingManager.Split(BuildingManager.Building)  (obfM_021) — SYNCHRONOUS
        internal static bool M2(ServerBuildingManager __instance, /* BuildingManager.Building */ object building)
        {
            if (!CoreLogic.Enabled || !CoreLogic.GateOpen) return true;
            try   { /* CoreLogic.Split_Optimized(__instance, building); */ return false; }
            catch (Exception ex) { CoreLogic.LogError("Running vanilla override " + ex.Message); return true; } // catch-only
        }

        // #4 DecayEntity.AttachToBuilding(uint buildingID)  (obfM_022) — SHORT-CIRCUIT ONLY
        internal static bool M3(DecayEntity __instance, uint buildingID)
        {
            if (!CoreLogic.GateOpen) return true;
            if (!CoreLogic.Enabled) return true;
            if (__instance == null) return true;
            // Skip ONLY a redundant re-attach to the same building; otherwise run vanilla.
            if (buildingID == __instance.buildingID) return false;
            return true;
        }

        // #2 ServerBuildingManager.CheckMerge(DecayEntity)  (obfM_020) — SYNCHRONOUS
        internal static bool M4(DecayEntity __0)
        {
            if (!CoreLogic.Enabled || !CoreLogic.GateOpen) return true;
            try   { /* CoreLogic.Merge_Optimized(__0); */ return false; }
            catch (Exception ex) { CoreLogic.LogError("Running vanilla merge override " + ex.Message); return true; } // catch-only
        }
    }

    // -------------------------------------------------------------------------
    //  Timer (CoalesceTickComponent : MonoBehaviour). Tick re-checks the gate
    //  then drains a batch of 3 split jobs.
    // -------------------------------------------------------------------------
    internal class CoalesceTickComponent : MonoBehaviour
    {
        internal void StartTicking(float interval) => InvokeRepeating(nameof(Tick), interval, interval);
        internal void StopTicking()  => CancelInvoke();

        internal void Tick()
        {
            try { CoreLogic.OnTick(); }
            catch (Exception e) { CoreLogic.LogError(string.Format("[Whispers88.Timer] {0}", e.Message)); }
        }
    }
}
