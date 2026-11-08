# Oxide.Ext.Whispers88.dll — Deobfuscation & Recovery Report

**Target:** `Oxide.Ext.Whispers88.dll` (33,288 bytes)
**SHA-256:** `d70abaa334d375bb0735856458163b771432387dede01b7d423ec836ccb50b2f`
**Type:** .NET assembly (PE32, Mono/.NET), **.NET Framework 4.8**, Oxide/uMod **extension** for a Rust game server
**Assembly version:** `1.1.0.0`
**Author (from metadata):** `Whispers88` — `Copyright (C) Whispers88 2026 - All Rights Reserved.` — contact `rustafarian.server@gmail.com`
**This item corresponds to the commissioned work "Vanilla Patching of Construction" ($400).**

> **Purpose of this document.** You commissioned and paid for this extension, the author stopped responding, declined to hand over the `.cs` source (every other plugin in the order was delivered as source), and the compiled DLL no longer works against current Rust updates. This report recovers what the extension does and gives your new developer a clean starting point to rebuild/update it. It is a **functional reconstruction from static analysis**, not a byte-exact decompile — see *Confidence & caveats* at the end.

---

## 1. TL;DR — what this extension is

It is a **server-performance extension** that uses **Harmony** to replace four of Rust's building-system methods with optimized versions. Rust recomputes building "splits" and "merges" and decay attachment **synchronously every time a building block changes** (placing/destroying walls) — which is a major CPU hotspot during raids. Whispers88 **intercepts those four methods and defers/coalesces the work** into batched queues drained by a timer, instead of recomputing on every single change. That raises server FPS (the Grafana frame-rate graph you were shown).

It registers console commands `whispers88.load` / `whispers88.unload` / `whispers88.status` to toggle and inspect the patches at runtime.

**Why it is broken now:** on load it resolves its four target methods by name via Harmony's `AccessTools`. If Rust has renamed/changed any of them in an update, resolution fails and it logs:

```
target resolve failed: Check={0} Merge={1} Split={2} Attach={3}
[Whispers88] Build failed please update.
```

That is exactly the state your server is in. **Fixing it = re-pointing/adjusting those four patch targets to the current Rust API and recompiling.**

---

## 2. How it was protected, and how it was recovered (safely)

The DLL is protected with the **full ConfuserEx suite**:

| Protection | What it does | Status |
|---|---|---|
| **Symbol renaming** | All type/method/field names replaced with invisible Unicode (zero-width / bidi control characters) | Recovered via sequential re-mapping |
| **Control-flow flattening** | Method logic turned into a `switch`-driven state machine with junk arithmetic | Linearized by hand for the key methods |
| **Ref-proxy** | Direct calls replaced by delegate "stub" methods | Harmony/BCL calls still resolve; helper stubs identified by behaviour |
| **Constant/string encryption** | All string literals RC4-encrypted into an embedded resource | **Fully decrypted statically (49/49 strings)** |
| **Anti-profiling** | Checks `COR_PROFILER`/`COR_ENABLE_PROFILING` env vars | Noted; irrelevant to static analysis |

**Important:** method bodies are **not** encrypted (no anti-tamper body encryption), so everything was recovered **statically — the DLL was never executed.** (Running it was deliberately avoided; it would execute the author's/obfuscator's code on the analysis machine.)

The string encryption turned out to be textbook **RC4**: a static 32-byte key (embedded in the string-decryptor method) applied to the 1,040-byte embedded resource, producing a buffer of length-prefixed UTF-8 strings. This was re-implemented in ~15 lines of Python and recovered all 49 strings. See `decrypted_strings.txt`.

Tooling used: pure-Python `dnfile` + `dncil` (metadata + IL disassembly). The full resolved IL is in `Oxide.Ext.Whispers88.full_IL.txt`.

---

## 3. Class structure

| Class | Base | Role |
|---|---|---|
| `Whispers88Extension` | `Oxide.Core.Extensions.Extension` | Extension entry point & lifecycle. `Name`/`Author` = "Whispers88", `Version` = 1.1.0, `SupportsReloading` = true |
| `CoreLogic` | — | The real logic: apply/remove patches, the four optimized override bodies, command handlers, logging |
| `H` | — | Holds the four Harmony patch methods `M1`–`M4` (thin wrappers that cast args and call into `CoreLogic`) |
| `CoalesceTickComponent` | `UnityEngine.MonoBehaviour` | The timer that drains the deferred work queues each tick; `StartTicking`/`StopTicking`/`Tick` |
| `<Module>` + 11 helper/proxy classes | — | ConfuserEx constant-decryptor and ref-proxy delegate infrastructure (not application logic) |

---

## 4. The four Harmony patches (fully resolved)

On load, `CoreLogic.ApplyPatches()` resolves two types and four methods via `HarmonyLib.AccessTools`, creates `new Harmony("com.Whispers88.whispers88")`, and applies **four prefix patches**:

| # | Vanilla Rust target (prefix-patched) | Harmony method | Optimized body | Override log |
|---|---|---|---|---|
| 1 | `ServerBuildingManager.CheckSplit(DecayEntity)` | `H.M1` | `CoreLogic.obfM_019` | — |
| 2 | `ServerBuildingManager.CheckMerge(DecayEntity)` | `H.M4` | `CoreLogic.obfM_020` | `Running vanilla merge override` |
| 3 | `ServerBuildingManager.Split(BuildingManager+Building)` | `H.M2` | `CoreLogic.obfM_021` | `Running vanilla override` |
| 4 | `DecayEntity.AttachToBuilding(uint buildingID)` | `H.M3` | `CoreLogic.obfM_022` | — |

All four are **`prefix`** patches (the `postfix`/`transpiler`/`finalizer` arguments are null). A prefix that returns `false` **skips the original method**, so these replace vanilla behaviour with the optimized version.

**Recovered behaviour of patch #1 (`CheckSplit` prefix, representative of the pattern):**

```csharp
// CoreLogic.obfM_019  — Harmony prefix for ServerBuildingManager.CheckSplit(DecayEntity)
static bool M1_Prefix(DecayEntity entity) {
    if (!patchesEnabled || !ready) return true;   // fall through to vanilla
    if (entity == null)           return true;
    if (entity.buildingID > 0)
        pendingSplit.Add(entity.buildingID);       // DEFER / COALESCE the work
    return false;                                   // skip vanilla; processed later on tick
}
```

The static fields (created in the `.cctor`) are the coalescing queues:
- `pendingSplit`  (`HashSet<uint>` of building IDs) — filled by CheckSplit/CheckMerge prefixes
- `pendingMerge`  (second `HashSet<uint>`)
- `patchesEnabled` flag — set true after patching, toggled by the console commands
- the `Harmony` instance, and the decrypted-constants buffer

The `CoalesceTickComponent` timer periodically drains these queues and performs the actual split/merge once per batch (and once more on shutdown — the `Final drain error` log guards that path). `obfM_020`/`021`/`022` follow the same defer-then-batch pattern for merge / split / decay-attach.

---

## 5. Lifecycle & console commands

- **`Load()` / `OnModLoad()`** → `ApplyPatches()` + `StartTimer()` (creates `CoalesceTickComponent`) + `RegisterConsoleCommands()` + registers the `whispers88` permission.
- **`OnShutdown()` / `Unload()`** → drains the queues, `harmony.UnpatchAll("com.Whispers88.whispers88")`, unregisters commands, stops the timer.
- **Console commands** (perm `whispers88`, admin):
  - `whispers88.load` — "Load patches" → `[Whispers88] Patches loaded` (or `Build failed please update.`)
  - `whispers88.unload` — "Unload patches" → `[Whispers88] Patches removed`
  - `whispers88.status` — "Show patch status" → `[Whispers88] Patches: ON` / `OFF`
- Related Rust convar referenced: `nav_carve_use_building_optimization` (navmesh-carve/building optimization toggle).

---

## 6. What your developer needs to do to fix it

1. **Start from `Whispers88Extension.reconstructed.cs`** (in this folder) — a clean, commented C# skeleton with correct lifecycle, the four patch targets, and the coalescing design.
2. **Verify the four target methods against the current Rust build.** Open the current `Assembly-CSharp.dll` and confirm these still exist with these signatures (Rust renames/refactors these periodically — this is why it broke):
   - `ServerBuildingManager.CheckSplit(DecayEntity)`
   - `ServerBuildingManager.CheckMerge(DecayEntity)`
   - `ServerBuildingManager.Split(BuildingManager.Building)`
   - `DecayEntity.AttachToBuilding(uint)`
   Update the `AccessTools.Method(...)` targets to whatever the current names/signatures are.
3. **Re-implement / validate the four optimized bodies.** The defer-and-batch logic is documented above and in the `.cs`; your dev should confirm it still matches the current vanilla logic (the whole point is to be *behaviourally equivalent but cheaper*, so it must track any vanilla changes).
4. **Build** against the server's current `Assembly-CSharp.dll`, `Facepunch.*`, `UnityEngine.*`, `Oxide.Core.dll`, and `0Harmony.dll` (2.3.x). Target .NET Framework 4.8. Drop the resulting DLL in `RustDedicated_Data/Managed/` (extensions load from there), or build it as a normal Oxide plugin if you prefer `.cs` distribution.
5. Keep the console commands and permission (`whispers88`) so you can toggle at runtime, exactly as before.

---

## 7. Confidence & caveats

- **High confidence (proven from IL):** identity/metadata; the four Harmony patch targets and that they are prefixes; the Harmony id; all 49 decrypted strings; the console commands/permission; the lifecycle; the defer-and-coalesce design and the `CheckSplit` body.
- **Medium confidence (reconstructed through obfuscation):** the exact statements inside `obfM_020/021/022` (merge/split/attach bodies) and the precise timer-drain algorithm — the control-flow flattening and ref-proxy stubs mean these are reconstructed by behaviour + field usage, not copied line-for-line. They are documented as the defer/batch pattern; your dev should treat the optimized bodies as *to be re-derived/validated* against current vanilla logic.
- This is a **clean-room-style functional reconstruction** intended as a maintenance starting point. It is not a byte-exact decompilation, and (given the obfuscation) it does not need to be — the practical path forward is to re-point the four patches to the current Rust API and rebuild.

### Files in this folder
- `README_ANALYSIS.md` — this report
- `Whispers88Extension.reconstructed.cs` — commented C# skeleton to build from
- `decrypted_strings.txt` — all 49 recovered string constants (with their ids)
- `Oxide.Ext.Whispers88.full_IL.txt` — full resolved IL disassembly (reference)
