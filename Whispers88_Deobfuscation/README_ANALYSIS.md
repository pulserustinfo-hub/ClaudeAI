# Oxide.Ext.Whispers88.dll — Deobfuscation & Recovery Report

**Target:** `Oxide.Ext.Whispers88.dll` (33,288 bytes)
**SHA-256:** `d70abaa334d375bb0735856458163b771432387dede01b7d423ec836ccb50b2f`
**Type:** .NET assembly (PE32, Mono/.NET), **.NET Framework 4.8**, Oxide/uMod **extension** for a Rust game server
**Assembly version:** `1.1.0.0`
**Author (from metadata):** `Whispers88` — `Copyright (C) Whispers88 2026 - All Rights Reserved.` — contact `rustafarian.server@gmail.com`
**Corresponds to the commissioned "Vanilla Patching of Construction" ($400).**

> This report was produced by **two independent static-analysis passes** (an initial reconstruction + a skeptical line-by-line verification that re-derived everything from the IL). Several first-pass claims were wrong and have been corrected here; corrections are marked **[corrected]**. The DLL was **never executed** — everything was recovered statically. See §8 for provenance.

---

## 1. TL;DR

It is a **server-performance extension** that uses **Harmony** to intercept four of Rust's building-system methods and run cheaper reimplementations, concentrated on **coalescing the expensive navmesh-carve** and **spreading building-split work across frames**. It cuts raid-time CPU (the Grafana FPS graph you were shown).

**Two things your developer must know up front:**

1. **It contains a hard-coded time-bomb.** On every timer tick it checks `DateTime.UtcNow <= 2026-11-26`. **After 26 November 2026 it auto-unpatches itself and the `whispers88.load` command replies `[Whispers88] Build failed please update.`** — a deliberate expiry/kill-switch. *(Today is before that date, so this is not what broke it in Jul–Aug 2026 — that was a Rust update — but it will disable the plugin on 26 Nov 2026 regardless of any compatibility fix, unless the gate is removed.)*
2. **It has an anti-analysis `Environment.FailFast`** that hard-kills the process if a debugger/profiler is attached (`Debugger.IsAttached` or `COR_ENABLE_PROFILING`/`CORECLR_PROFILER`/`COR_PROFILER`). Your dev should not run the *original* DLL under a profiler/debugger.

**Why it stopped working in Jul–Aug 2026:** on load it resolves its four target methods by name via Harmony's `AccessTools`. When Rust changed them in an update, resolution failed and it logged `target resolve failed: Check/Merge/Split/Attach` → `[Whispers88] Build failed please update.` (the `ProtoBuf`/`ClientRPC` errors in your Discord logs are the same Rust-version drift.) **Fix = re-point the four targets to the current Rust API, remove the time-gate, and recompile.**

---

## 2. How it was protected, and how it was recovered (safely)

Full **ConfuserEx** suite:

| Protection | What it does | Status |
|---|---|---|
| Symbol renaming | Names → invisible Unicode (zero-width/bidi) | Re-mapped |
| Control-flow flattening | Logic → `switch` state machine + junk math | Linearized |
| Ref-proxy | Direct calls → delegate stub methods | Resolved to concrete targets |
| Constant/string encryption | Literals RC4-encrypted in an embedded resource | **Fully decrypted** |
| Constant **numeric** encryption | Dates/intervals RC4-encrypted in a 2nd resource | **Fully decrypted [corrected — now recovered]** |
| Anti-profiling | `Environment.FailFast` on debugger/profiler | Identified |

Method bodies are **not** encrypted (no anti-tamper body encryption), so recovery was fully static — **the DLL was never run** (running it would execute the author's/obfuscator's code, including the `FailFast`). Both string and numeric constant pools turned out to be plain **RC4** (two different embedded 32-byte keys over two embedded resources); re-implemented in ~15 lines of Python, recovering **all 49 strings** and the numeric constants below.

**Decrypted numeric constants** (from the 2nd RC4 pool):
- Expiry date = `DateTime(2026, 11, 26)` → gate is `UtcNow <= 2026-11-26`
- Tick interval = `Mathf.Max(0.1f, 0.5f)` = **0.5 s**
- Per-tick split-drain batch size = **3** (plaintext literal)
- Final-drain count (on shutdown) = `int.MaxValue` (drain everything)

Tooling: pure-Python `dnfile` + `dncil` (metadata + IL). Full resolved IL: `Oxide.Ext.Whispers88.full_IL.txt`. All 49 strings: `decrypted_strings.txt`.

---

## 3. Class structure

| Class | Base | Role |
|---|---|---|
| `Whispers88Extension` | `Oxide.Core.Extensions.Extension` | Entry point/lifecycle. Name/Author "Whispers88", Version 1.1.0, SupportsReloading true |
| `CoreLogic` | — | Patch apply/remove, the time-gate, the four override bodies, the drain, command handlers, logging |
| `H` | — | The four Harmony patch methods `M1`–`M4` (cast args → call `CoreLogic`) |
| `CoalesceTickComponent` | `UnityEngine.MonoBehaviour` | Timer; `Tick` re-checks the gate then drains a batch of 3 split jobs |
| `<Module>` + 11 helper/proxy classes | — | Constant decryptors, anti-profiling, ref-proxy delegate infrastructure |

---

## 4. The four Harmony patches (verified)

`CoreLogic.ApplyPatches()` resolves two types + four methods via `AccessTools`, creates `new Harmony("com.Whispers88.whispers88")`, and applies **four prefix patches** (all `postfix`/`transpiler`/`finalizer` null — confirmed):

| # | Vanilla Rust target (prefix-patched) | Harmony method | Body | Behaviour **[corrected]** |
|---|---|---|---|---|
| 1 | `ServerBuildingManager.CheckSplit(DecayEntity)` | `H.M1` | `obfM_019` | **Defers**: `obfF_010.Add(buildingID); return false` (the only coalesced one) |
| 2 | `ServerBuildingManager.CheckMerge(DecayEntity)` | `H.M4` | `obfM_020` | **Synchronous**: runs optimized merge `obfM_033(entity)`, `return false` |
| 3 | `ServerBuildingManager.Split(BuildingManager.Building)` | `H.M2` | `obfM_021` | **Synchronous**: runs optimized split `obfM_032(mgr, building)`, `return false` |
| 4 | `DecayEntity.AttachToBuilding(uint buildingID)` | `H.M3` | `obfM_022` | **Short-circuit only**: `return false` **iff** `buildingID == entity.buildingID`; otherwise `return true` (run vanilla) |

> **[corrected] Important:** my first pass claimed *all four* defer work into queues — that was wrong. Only **CheckSplit** defers (into `obfF_010`, a `HashSet<uint>`). Merge and Split run their optimized bodies **synchronously**; AttachToBuilding only skips a **redundant re-attach**. The strings `"Running vanilla override "` / `"Running vanilla merge override "` are **catch-only error prefixes** (logged with the exception message if the optimized body throws), *not* normal-path logs.

Each patch body is gated by `obfF_009` (patches enabled) **and** `obfF_007` (the time-gate). If the gate is closed, the prefix returns `true` and the original (vanilla) method runs.

---

## 5. The optimization itself (`obfM_032` split / `obfM_033` merge) — recoverable

- **`obfM_032` (optimized Split):** connected-components flood-fill over `building.buildingBlocks` via `BaseEntity.EntityLinkBroadcast<BuildingBlock>(visitor)` into pooled groups (`Facepunch.Pool`); keep the largest group's id; for every *other* group call `ServerBuildingManager.NewBuildingID()` and `DecayEntity.AttachToBuilding(newId)` on its blocks; reattach loose (non-block) decay entities by parent/nearby `BuildingBlock` (`ContainerCorpse` → original building id); then — **only if `ConVar.AI.nav_carve_use_building_optimization`** — set `building.isNavMeshCarvingDirty = true` and call `ServerBuildingManager.UpdateNavMeshCarver(building, …)` **once**.
- **`obfM_033` (optimized Merge):** pooled `List<Building>` of linked buildings (via `EntityLinkMessage` + visitor); pick the building with the most `decayEntities` as target; reassign the others' entities into it (`AttachToBuilding(target.ID)`); fix up the pending-split ids in `obfF_010`; then one dirty + `UpdateNavMeshCarver`.

**The core win:** collapse the expensive **navmesh-carve** into a single call per operation, and **spread split work across frames** (batch of 3 per 0.5 s tick) instead of doing it all synchronously on every block change.

---

## 6. Lifecycle, timer, commands **[corrected]**

- **`Load` / `OnModLoad`** → `ApplyPatches()` → `StartTimer()` (creates `CoalesceTickComponent`, interval 0.5 s) → `RegisterConsoleCommands()`.
- **Tick** (`obfM_023`, every 0.5 s): re-evaluate the time-gate (`obfM_011`); **if expired → `UnpatchAll` and stop**; else drain up to **3** building ids from `obfF_010`, running optimized split per building (scratch list `obfF_011` = `List<uint>`, ids `Remove`d, bypass flag `obfF_012` set during processing).
- **`OnShutdown` / `Unload`** → `UnregisterCommands()` → drain remaining + destroy the timer `GameObject` + `UnpatchAll("com.Whispers88.whispers88")` + clear `obfF_010`/`obfF_011`.
- **Console commands** (`whispers88.load` / `unload` / `status`): **[corrected] there is NO Oxide permission.** `"whispers88"` is the `ConsoleSystem.Command.Parent`; access is `arg.Connection == null || arg.Connection.authLevel >= 2` (server console or owner). `status` → `[Whispers88] Patches: ON/OFF`; `load` → `Patches loaded` or, if the gate is closed, `Build failed please update.`
- **[corrected] Logging** is via `UnityEngine.Debug.Log/LogWarning/LogError` (prefix `[Whispers88] `), not the Oxide log.

---

## 7. What your developer must do

1. **Start from `Whispers88Extension.reconstructed.cs`** (now corrected to match the IL, with the dangerous unconditional `AttachToBuilding` skip fixed).
2. **Remove/neutralize the time-gate.** Delete `obfM_011`/`obfF_007` logic (the `UtcNow <= 2026-11-26` check) or it will self-disable on 26 Nov 2026.
3. **Re-point the four targets to the current Rust build.** Confirm against the current `Assembly-CSharp.dll` that these still exist and fix names/signatures as needed:
   - `ServerBuildingManager.CheckSplit(DecayEntity)`
   - `ServerBuildingManager.CheckMerge(DecayEntity)`
   - `ServerBuildingManager.Split(BuildingManager.Building)`
   - `DecayEntity.AttachToBuilding(uint)`
4. **Validate the optimized bodies** (§5) against current vanilla logic — the whole point is to stay behaviourally equivalent but cheaper; if vanilla changed, these must track it.
5. **Build** against current `Assembly-CSharp.dll`, `Facepunch.*`, `UnityEngine.*`, `Oxide.Core.dll`, `0Harmony.dll` (2.3.x), target .NET Framework 4.8, output to `RustDedicated_Data/Managed/`.
6. Keep the `whispers88.load/unload/status` console controls.

---

## 8. Provenance & confidence

- **Pass 1** produced the structure, the four patch targets, the decrypted strings, and a first behavioural model.
- **Pass 2** (independent, skeptical re-derivation from the IL + re-run of the RC4) confirmed the identity/strings/targets/mapping/commands/lifecycle-skeleton and **corrected** the behavioural model (only Split defers; no merge queue; the `M3` short-circuit; no Oxide permission; Unity logging) and **found the time-gate** that pass 1 missed. Its full report is in `opus_verification.md`.
- The expiry date and tick constants were then recovered by decrypting the numeric constant pool (resolving pass 2's one open item).
- **High confidence:** identity, SHA-256, all 49 strings + numeric constants, the four prefix targets and M1/M4/M2/M3↔body↔target mapping, the Harmony id, the time-gate and anti-profiling routines, the command set, and the split/merge algorithm shape.
- **Reconstruction, not byte-exact decompile:** exact statement order inside `obfM_032/033` is reconstructed through the obfuscation; treat those bodies as to-be-validated against current vanilla. The practical proof is your dev compiling against the current Rust assemblies and watching the four targets resolve.

### Files
- `README_ANALYSIS.md` — this report
- `Whispers88Extension.reconstructed.cs` — corrected C# skeleton
- `decrypted_strings.txt` — all 49 recovered strings
- `opus_verification.md` — the independent verification pass (what it confirmed/corrected)
- `Oxide.Ext.Whispers88.full_IL.txt` — full resolved IL disassembly
