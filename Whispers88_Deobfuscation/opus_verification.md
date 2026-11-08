# Independent Verification of the Whispers88 Reconstruction

**Verifier:** second analyst (Opus), re-derived from IL independently.
**Inputs checked:** `README_ANALYSIS.md`, `Whispers88Extension.reconstructed.cs`
**Evidence:** `out/disasm.txt` (= `Whispers88_Deobfuscation/Oxide.Ext.Whispers88.full_IL.txt`), `out/decrypted_strings.txt`, re-run of `decrypt_strings.py`, plus my own `disasm2.py` (switch-target expansion + corrected call resolution) and a state-machine linearizer for the control-flow-flattened methods.
**Method:** static only. The DLL was never executed.

Verdict legend: **CONFIRMED** (proven from IL) / **WRONG** (contradicted by IL, correction given) / **MINOR** (true-ish but imprecise) / **UNCERTAIN** (not determinable statically).

---

## A. Coordinator's 6 specific claims

### Claim 1 — four targets, all PREFIX patches → **CONFIRMED**
`obfM_012` (ApplyPatches): `TypeByName("ServerBuildingManager")` and `TypeByName("DecayEntity")` (strings id0/id25); then
- `local_4 = AccessTools.Method(sbm,"CheckSplit")` (id40)
- `local_5 = AccessTools.Method(sbm,"CheckMerge")` (id54)
- `local_6 = obfM_013(sbm,"Split","BuildingManager+Building")` (id68/id77)
- `local_7 = obfM_013(decay,"AttachToBuilding","System.UInt32")` (id105/id125)

The four `callvirt HarmonyLib.Harmony::Patch` calls each push `newobj HarmonyMethod(...)` then **three `ldnull`** (postfix/transpiler/finalizer) → all prefixes. CONFIRMED. Note: CheckSplit/CheckMerge are resolved by *name only* (no signature pin); the `(DecayEntity)` parameter is proven instead by the `H.M1`/`H.M4` `castclass DecayEntity`.

### Claim 2 — patch-method ↔ body bindings & H casts → **CONFIRMED**
At the four Patch sites the `HarmonyMethod` wraps `AccessTools.Method(typeof(H), <id>)` with ids **238="M1", 244="M4", 250="M2", 256="M3"** in that target order. H bodies: `M1`→`castclass DecayEntity`→`obfM_019`; `M4`→`castclass DecayEntity`→`obfM_020`; `M2`→`castclass ServerBuildingManager`+`castclass Building`→`obfM_021`; `M3`→`castclass DecayEntity`+arg1→`obfM_022`. All CONFIRMED.

### Claim 3 — target ↔ patch pairing in the README table → **CONFIRMED**
From the `local_N` used at each Patch site: CheckSplit←M1, CheckMerge←M4, Split←M2, AttachToBuilding←M3. The README's section-4 table is correct, including the two override-log strings (id448 "Running vanilla merge override ", id483 "Running vanilla override ").

### Claim 4 — obfM_019 (CheckSplit prefix) body → **CONFIRMED with 2 nuances**
Proven: gated by `obfF_009` (patched) AND `obfF_007` (gate); reads `DecayEntity.buildingID`; adds it to the static set `obfF_010`; returns `false`. `.cctor` sets `obfF_007=1`, creates `obfF_010`/`obfF_011`; `obfF_009` is set `=1` at the end of `obfM_012` (IL_0a1a). All CONFIRMED.
Two inaccuracies in the README/`.cs` representative body:
- **Missing bypass check.** Real body has `if (obfF_012) return true;` right after the gate (lets vanilla run while the drain is processing, preventing re-queue). Omitted in the reconstruction.
- **Null-entity return value is inverted.** IL computes `valid = (entity != null && buildingID > 0)`; if `!valid` it returns **false** (skips vanilla) — see IL_119a‑11b0 then IL_11e1 `ldc.i4.0; stloc.1; ret`. The README/`.cs` return **true** for `entity == null`. Minor, but it is wrong.
Everything else about #1 is correct: it *is* a defer-into-`obfF_010` prefix.

### Claim 5 — "defer-and-coalesce into queues drained by the timer" → **PARTLY WRONG (important)**
The mechanism is real **only for Split**. The IL does **not** support a general defer model:
- **obfM_019 (CheckSplit)** — the ONLY one that defers: `obfF_010.Add(buildingID); return false`. CONFIRMED.
- **obfM_020 (CheckMerge)** — **synchronous**: `if gated { try { obfM_033(entity); return false; } catch { LogError("Running vanilla merge override "+ex.Message); return true; } }`. No queue. (IL_128b `call obfM_033`.)
- **obfM_021 (Split)** — **synchronous**: `try { obfM_032(mgr,building); return false; } catch { LogError("Running vanilla override "+ex.Message); return true; }`. No queue. (IL_1309 `call obfM_032`.)
- **obfM_022 (AttachToBuilding)** — **short-circuit only**: returns `false` **iff `buildingID == entity.buildingID`** (redundant re-attach); otherwise returns `true` (run vanilla). No queue. (IL_1404/1424.)

The timer path **is** proven and drains, but only the split set:
`CoalesceTickComponent.Tick` → `TickCallback` (an `Action` set in `obfM_014` to `CoreLogic.obfM_023`) → `obfM_023`:
```
obfM_011();                       // re-evaluate the date gate (see W7)
if (obfF_007 == 0) { obfM_015(); return; }   // EXPIRED → auto-Unpatch everything
obfM_024(3);                      // else drain a batch of 3
```
`obfM_024(maxPerBatch)` (the drain): takes up to `maxPerBatch` ids out of `obfF_010` into scratch list `obfF_011`, `Remove`s them from `obfF_010`, sets `obfF_012=1` (bypass), then for each id: `b = BuildingManager.server.GetBuilding(id); if (b!=null && b.buildingBlocks.Count!=0) obfM_032(server,b);` finally `obfF_012=0; obfF_011.Clear()`. So the drain runs the **optimized split** (`obfM_032`) per building, a **batch of 3 per tick**, not a clear-all, and there is **no merge drain**. CONFIRMED that a drain exists; the README/`.cs` characterization of it is wrong (see W1/W2/W6).

### Claim 6 — misc facts in README → **mostly CONFIRMED, two WRONG**
- SHA-256 `d70abaa3…ccb50b2f` — **CONFIRMED** (`sha256sum` matches).
- Version `1.1.0` (`get_Version` → `new VersionNumber(1,1,0)`), Name/Author `"Whispers88"` (id992), `SupportsReloading=true` — CONFIRMED.
- Harmony id `com.Whispers88.whispers88` (id209, used in `new Harmony(...)` and `UnpatchAll(...)`) — CONFIRMED.
- Console commands `whispers88.load/unload/status` with names `load/unload/status`, descriptions `Load patches`/`Unload patches`/`Show patch status`, handlers `obfM_029/030/031`, `Parent="whispers88"`, `ServerAdmin=true` — CONFIRMED (`obfM_025`/`obfM_027`).
- 49/49 strings — **CONFIRMED**: I re-ran `decrypt_strings.py` on `res_0.bin`; output is byte-for-byte identical to `decrypted_strings.txt` (49/49).
- "Build failed please update." path in `obfM_029` — CONFIRMED: `if (!IsAdmin) reply id815; obfM_011(); if (obfF_007==0) reply id846 "Build failed please update."; else obfM_012()+obfM_014()+reply id890 "Patches loaded"`.
- **WRONG — "registers the whispers88 permission".** There is **no Oxide permission** anywhere (grep for permission APIs in the IL returns nothing; no `Oxide.Core.Libraries.Permission`). `"whispers88"` (id801) is the **ConsoleSystem.Command.Parent**. Access control is `obfM_028 = (arg.Connection == null) || (arg.Connection.authLevel >= 2)` — i.e. server console or authLevel≥2 (owner). The `.cs` `const string Permission` + `RegisterPermissionAndCommands()` and README §5 "registers the whispers88 permission" are not supported.
- **Anti-profiling note — CONFIRMED and then some.** `obfM_010` (`<Module>`): `if (Debugger.IsAttached || getenv("COR_ENABLE_PROFILING")!=null || getenv("CORECLR_PROFILER")!=null || getenv("COR_PROFILER")!=null) Environment.FailFast("")`. Those env names are **plaintext** `ldstr`. It is a hard `FailFast` kill, not merely a passive check — the dev should avoid running the original under a profiler/debugger.

---

## B. Additional errors found in the committed files (not in the 6 claims)

- **W1 — `PendingMerge` / `obfF_011` is invented.** Field signatures: `obfF_010 = HashSet<uint>` (sig `06 15 12 11 01 09`; `callvirt Add` is followed by `pop`, i.e. the discarded `bool` return of `HashSet<T>.Add`), **but `obfF_011 = List<uint>`** (sig `06 15 12 15 01 09` — a *different* generic type, TypeRef row 5 vs row 4; it is indexed with `get_Item`). `obfF_011` is the **drain scratch buffer**, not a "second queue of pending merges." The README's "`pendingMerge` (second `HashSet<uint>`)" and the `.cs` `PendingMerge` are wrong on both type and purpose. (The README is, however, correct that `obfF_010`/`PendingSplit` is a `HashSet<uint>`.)

- **W2 — "drains these queues and performs the actual split/merge."** Only split is deferred/drained; merge/split/attach are synchronous or short-circuit (see Claim 5). Merge is never queued.

- **W3 — `.cs H.M4` body is fabricated.** It shows `Log("Running vanilla merge override "); if (buildingID>0) PendingMerge.Add(...); return false`. Real `obfM_020`: synchronous `obfM_033(entity)`, and the string is a **catch-only** error prefix (concatenated with `ex.Message`, logged only on failure, then `return true`). No log on the normal path, no queue.

- **W4 — `.cs H.M2` logs `"Running vanilla override "` unconditionally.** Real `obfM_021`: that string is catch-only; the normal path is `obfM_032(mgr,building); return false`.

- **W5 — `.cs H.M3` returns `false` unconditionally (dangerous).** Real `obfM_022` returns `false` **only** when `buildingID == entity.buildingID`; otherwise `true`. An unconditional-false prefix would suppress *all* `AttachToBuilding` calls and break the game. This body must not be shipped as-is.

- **W6 — `.cs DrainAll` is wrong.** It loops `PendingSplit` + `PendingMerge` and `Clear()`s both. Real `obfM_024`: batch of **3** from `obfF_010` only, `Remove` (not clear), bypass flag `obfF_012` during processing, and calls `obfM_032` (optimized split) per building. No merge drain.

- **W7 — `obfF_007` is a time/expiry gate, not an "init-done" flag (MAJOR, and the README/`.cs` miss it).** `obfM_011`: `obfF_007 = !(DateTime.UtcNow.Ticks > new DateTime(int@0,int@4,int@8,0,0,0,1).Ticks)` (i.e. `UtcNow <= embeddedDate`), and on any exception `obfF_007 = 0`. `.cctor` defaults it `true`. It is **re-evaluated every tick**, and when it goes false `obfM_023` calls `obfM_015` to **auto-unpatch**, while the load command reports **"Build failed please update."** This is an expiry/time-bomb and is a strong candidate for *why the DLL "stopped working"* independent of Rust API drift. The reconstruction labels `obfF_007` as "Ready — set once static init done," which is incorrect and omits the whole gate. A rebuilding dev must neutralize `obfM_011`/`obfF_007` or the patches will self-disable after the embedded date.

- **W8 — `.cs` Tick omits the per-tick gate recheck + auto-unpatch** that `obfM_023` performs before draining (follows from W7).

- **MINOR — lifecycle order.** IL `Load`/`OnModLoad` = `obfM_012`(ApplyPatches) → `obfM_014`(StartTimer) → `obfM_025`(RegisterConsoleCommands) (proven by linearizing the flattened state machine). The `.cs` `Initialize()` runs commands first and injects a `Ready=true` that the IL does not do there. IL `OnShutdown`/`Unload` = `obfM_026`(UnregisterCommands) → `obfM_015`, and `obfM_015` is what drains (try/catch "Final drain error: "), destroys the timer `GameObject`, `UnpatchAll`s, and clears `obfF_010`/`obfF_011`. The `.cs` does drain→unpatch→unregister (reordered) and stops the timer via `StopTicking()` rather than `Destroy(gameObject)`. Functionally close; order and teardown mechanism differ.

- **MINOR — logging sink.** Original logs through **`UnityEngine.Debug.Log/LogWarning/LogError`** (`obfM_102/103/104`) with the `"[Whispers88] "` prefix (id431). The `.cs` routes to `Interface.Oxide.LogInfo/…`. Different destination (Unity console vs Oxide log file).

- **MINOR — timer cadence / batch size.** `StartTicking(interval)` takes the interval as a parameter; `obfM_014` passes `Mathf.Max(float@16, float@20)` (encrypted numeric constants). Drain batch size is the plaintext literal **3**. The `.cs` hardcodes `Interval = 1f` (correctly flagged TODO) and does not reflect the batch-of-3.

---

## C. What the README UNDER-states (not errors, but worth noting)
The README marks `obfM_032`/`obfM_033` (split/merge bodies) as essentially un-recovered/TODO. They are in fact **recoverable in detail** from the IL (all ref-proxy stubs resolve to concrete BCL/Rust/Facepunch calls):
- `obfM_032` (optimized Split): connected-components flood-fill over `building.buildingBlocks` via `BaseEntity.EntityLinkBroadcast<BuildingBlock>(visitor)` into pooled groups (`Facepunch.Pool.Get`/`FreeUnmanaged`), keep the largest group's id, call `ServerBuildingManager.NewBuildingID()` for each other group and `DecayEntity.AttachToBuilding(newId)` its blocks, then reattach non-block decay entities (parent/nearby `BuildingBlock`; `ContainerCorpse`→original building id), and — gated on `ConVar.AI.nav_carve_use_building_optimization` — set `building.isNavMeshCarvingDirty = true` and call `ServerBuildingManager.UpdateNavMeshCarver(building, ref 2, false)` **once**.
- `obfM_033` (optimized Merge): pooled `List<Building>` of linked buildings (via `EntityLinkMessage` + visitor `obfM_038`), pick the building with the most `decayEntities` as target, reassign the others' entities into it (`obfM_034` → per-entity `AttachToBuilding(target.ID)`), fix up `obfF_010` ids, then one dirty+`UpdateNavMeshCarver`.

The core optimization is therefore "coalesce the expensive **navmesh-carve** into one call per split/merge and spread **split** work across frames (batch of 3/tick)." The README's high-level thesis ("intercept building ops, be behaviourally equivalent but cheaper, concentrated around nav carving") is directionally right.

---

## D. UNCERTAIN (not determinable statically here)
- **U1 — exact expiry date** (year/month/day in `obfM_011`): read from the encrypted **numeric** constant pool via `obfM_006(@0/@4/@8)`; not decrypted (the recovered `decrypted_strings.txt` covers strings only). Decryptable with the same RC4/constant machinery.
- **U2 — exact tick interval** (`obfM_008 @16/@20`) and **final-drain count** (`obfM_006 @24`): same encrypted numeric pool; not decrypted. (Per-tick drain batch size **3** is plaintext and known.)

---

## E. Bottom line
- **Solid / trustworthy:** identity + SHA-256, strings (49/49), the four prefix targets and the M1/M4/M2/M3↔body↔target mapping, Harmony id, console command set, the lifecycle *skeleton*, that CheckSplit defers into a `HashSet<uint>` drained by the tick, and the anti-profiling routine.
- **Do not trust as written:** the claim that all four patches defer/coalesce (only Split does); the invented `PendingMerge` queue (`obfF_011` is a `List<uint>` scratch buffer); the `.cs` bodies for `M2`/`M3`/`M4` and `DrainAll` (M3's unconditional `return false` is outright breaking); the "whispers88 permission"; and — most importantly — the omission of the **`obfF_007` UTC time-gate / auto-unpatch / "Build failed please update."** which is likely a real cause of the breakage and must be addressed by whoever rebuilds this.
