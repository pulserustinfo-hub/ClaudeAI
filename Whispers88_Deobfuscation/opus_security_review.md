# Independent Security Review — `Oxide.Ext.Whispers88.dll`

**Scope:** PART A — full security sweep for malicious/risky behaviour beyond the two already-known items
(time-bomb + anti-profiling FailFast). PART B — accuracy re-check of the corrected deliverables.
**Method:** **static only.** The DLL was **never executed.** Evidence is drawn from the metadata tables
(TypeRef / MemberRef / TypeSpec / AssemblyRef / ModuleRef / ImplMap / ManifestResource / #US) enumerated
with `dnfile`, plus the resolved IL (`out/disasm.txt`). The metadata enumeration is the *obfuscation-proof*
bound: an assembly can only call externally what appears in MemberRef/TypeRef/TypeSpec/ImplMap, regardless
of control-flow/proxy obfuscation. Scripts: `apisurface.py`, `res2probe.py` (run with `python -I` against the
extracted bytes; the DLL itself was not run).

---

## 1. SECURITY VERDICT

**SAFE to rebuild-from-source and run, once the time-gate is removed** — with the important operational
caveat that this is a *self-protecting* binary (anti-tamper + anti-profiler), so it must be **recompiled from
the reconstructed source, not binary-patched in place** (see New Finding 1).

The complete external API surface contains **no network capability of any kind, no process/shell execution,
no dynamic code loading, no registry access, no P/Invoke, no filesystem writes, and no URL/host/IP/email
literals anywhere.** There is therefore **no phone-home, no remote kill-switch, no license callback, and no
data-exfiltration path** — these are not merely "not observed," they are **impossible** given the referenced
API set (absence from TypeRef/MemberRef is positive proof the capability is not compiled in).

Every externally-facing thing the assembly does falls into one of three buckets:
1. **Its stated job** — Harmony-patch four Rust building methods and run cheaper reimplementations.
2. **Self-protection (ConfuserEx)** — the two known traps *plus three additional self-defence mechanisms*
   found in this review (all self-referential; none harm the host or the player).
3. **A console admin-gate** reading `Connection.authLevel` (not a credential read).

No **second** time-bomb, no hardware/GUID/MAC/license check, and no code that charges/degrades on any
condition other than the single known UTC date gate were found.

### Referenced-vs-Absent API category table (with IL / metadata evidence)

| Risk category | Status | Evidence (metadata + IL) |
|---|---|---|
| **Network** — `System.Net.*`, `Sockets`, `HttpClient`/`WebClient`/`WebRequest`, `Dns` | **ABSENT** | No such TypeRef/MemberRef. `AssemblyRef` has no `System.Net.*`/`System.Net.Http`. `Facepunch.Network` is referenced for exactly ONE member — `Network.Connection::authLevel` (read) — i.e. the console admin check, not sockets. |
| **Unity networking** — `UnityEngine.Networking.UnityWebRequest` | **ABSENT** | `UnityEngine.CoreModule` TypeRefs are only `Debug, GameObject, Mathf, MonoBehaviour, Object`. No `Networking.*`. |
| **URL / host / IP / email literals** | **ABSENT** | All 49 RC4 strings (`decrypted_strings.txt`) are method/type/command names + log text. The entire `#US` stream is 144 bytes: the 2 read resource names + `COR_ENABLE_PROFILING`/`CORECLR_PROFILER`/`COR_PROFILER` + `""`. No scheme/host/IP/`@` anywhere. |
| **Phone-home / remote kill-switch / license callback** | **ABSENT** | Follows from "no network." The only kill-switch is the **local** UTC date gate (offline). |
| **Filesystem WRITE / delete / enumerate** — `File.Write*`, `FileStream` ctor, `File.Create/Open/Delete`, `Directory.*` | **ABSENT** | No `System.IO.Directory`, no `FileStream`, no write/create/delete MemberRef. |
| **Filesystem READ** — `File.ReadAllBytes`, `Stream.Read/get_Length`, `Assembly.get_Location`/`GetManifestResourceStream` | **REFERENCED — self-only** | `File.ReadAllBytes` has exactly **one** call site: `obfM_001` (IL_0276), on `GetExecutingAssembly().Location` (IL_025c/0261) — it reads the assembly's **own file** for an integrity hash (New Finding 1). `GetManifestResourceStream` has exactly **two** call sites (IL_0469, IL_05d4) — reading its **own** embedded RC4 resources res_0/res_1. No arbitrary/config/player-data path is ever read; no path literals exist. |
| **Process / shell** — `System.Diagnostics.Process`, `ProcessStartInfo` | **ABSENT** | Only `System.Diagnostics.Debugger` + `DebuggableAttribute` present; no `Process`. |
| **Dynamic code loading** — `Assembly.Load/LoadFile/LoadFrom`, `AppDomain`, `Reflection.Emit`, `Activator.CreateInstance` | **ABSENT** | `System.Reflection.Assembly` members are only `GetExecutingAssembly`, `GetManifestResourceStream`, `get_Location`. No `Load*`, no `AppDomain`, no `System.Reflection.Emit.*`, no `System.Activator`. **Nothing can load a payload** (and no payload resource is even read — see res_2). |
| **Credential / env access** — `Environment.GetEnvironmentVariable`, registry, tokens | **REFERENCED — 3 profiler vars only** | `Environment.GetEnvironmentVariable` (stub `obfM_074`) called exactly 3× — all in `obfM_010` with the literal names `COR_ENABLE_PROFILING`, `CORECLR_PROFILER`, `COR_PROFILER`. **No** `Microsoft.Win32.Registry`, **no** other env var, **no** auth/RCON/token read. |
| **Process termination** — `Environment.FailFast` | **REFERENCED — anti-profiler** | Stub `obfM_075`, one call site, only from `obfM_010` (the known trap). |
| **Debugger detection** — `Debugger.IsAttached` | **REFERENCED — anti-profiler** | Stub `obfM_073`, one call site, only from `obfM_010` (known). |
| **Date/time kill-switch** — `DateTime.UtcNow/.ctor/.Ticks` | **REFERENCED — ONE gate** | `get_UtcNow` 1 site, `DateTime::.ctor` 1 site — both inside `obfM_011` (the known 2026-11-26 gate). **No second time check.** |
| **Hardware / GUID / MAC / license fingerprint** | **ABSENT** | `GuidAttribute` is only the standard assembly-level attribute. No `NetworkInterface`, `ManagementObject`, `RNGCrypto`, machine-id, or HWID API. |
| **Native / P-Invoke** | **ABSENT** | `ModuleRef` = 0 rows, `ImplMap` = 0 rows → no `DllImport`, no unmanaged entry points. |
| **Reflection (method resolution)** — `Type.GetMethods`, `MethodBase.GetParameters`, `Type.GetTypeFromHandle` | **REFERENCED — benign** | Used by the AccessTools method-resolution helper `obfM_013` and by exception-type logging. No instantiation/invoke of external types. |

`AssemblyRef` (complete dependency set — bounds everything): `mscorlib`, `0Harmony 2.3.1.1`, `System.Core`,
`UnityEngine.CoreModule`, `Assembly-CSharp`, `Facepunch.Console`, `Oxide.Core 2.0.4143`, `Facepunch.System`,
`Facepunch.Network`. Nothing network-, crypto-, management-, or interop-related.

---

## 2. NEW FINDINGS (beyond the two already known)

All three are **ConfuserEx self-protection**, self-referential, and **not harmful to the host/player**. They
are "proven-from-IL" unless marked inferred.

### New Finding 1 — Self-integrity ANTI-TAMPER that silently zeroes the numeric constant pool *(proven)*
`obfM_001` reads the assembly's **own** bytes (`GetExecutingAssembly().Location` → `File.ReadAllBytes`),
computes an **FNV-1a 64-bit** hash over `file[0 : len-8]` (offset basis `0xCBF29CE484222325`, prime
`0x100000001B3` — IL_028b / IL_02a2), reads the trailing 8 bytes as a little-endian u64, and returns
`hash != trailer` (IL_0327-032f). It is called from exactly one place — `obfM_005`, the **numeric**-pool
decryptor (IL_06de). On mismatch, `obfM_005` **replaces the decrypted numeric pool `obfF_002` with a
zero-filled array** (IL_06e5-06f1) instead of calling FailFast or anything external.

- **Consequence for the dev:** if the DLL is **byte-patched in place** (e.g. NOPing the date gate) without
  recompiling, the integrity hash breaks → the numeric pool reads as zeros → `new DateTime(0,0,0,…)` throws
  in `obfM_011` → the catch sets the gate closed (`obfF_007=0`) → `whispers88.load` replies
  `"Build failed please update."`. **This is a self-trap against binary patching, not against the user.**
  The README's "rebuild from source" guidance already sidesteps it; this review makes the mechanism explicit
  so nobody wastes time hex-editing the original.
- **Not harmful:** it only ever reads *its own file*; it writes nothing, launches nothing, and contacts
  nothing. No FailFast on this path (unlike the profiler trap).
- **Scope note:** only the **numeric** pool is tamper-bound; the **string** pool (`obfM_004`) is not
  zero-on-tamper (it carries the profiler trap instead).

### New Finding 2 — the profiler/debugger FailFast trap fires very early and broadly *(proven)*
`obfM_010` (`Debugger.IsAttached || getenv(COR_ENABLE_PROFILING|CORECLR_PROFILER|COR_PROFILER) != null →
Environment.FailFast("")`) is invoked at the **top of `obfM_004`, the string decryptor** (IL_0450), which
is called wherever any obfuscated string is needed. In practice the trap therefore triggers on the **first
string decryption during load**, i.e. almost immediately — reinforcing "never run the original DLL under a
profiler/debugger." (The reconstruction correctly does **not** reproduce this.) Single caller; no other code
path reaches FailFast.

### New Finding 3 — the 3rd embedded resource `res_2.bin` (36 bytes) is INERT / dead data *(proven inert; identity inferred)*
- **Proven:** it is a genuine 36-byte manifest resource (resources blob declared length = 36, verified via
  the Cor header resources directory in `res2probe.py`), and it is **never read by any code** —
  `GetManifestResourceStream` has only **two** call sites and both are accounted for (res_0 strings via
  `obfM_004`; res_1 numerics via `obfM_005`). Its obfuscated name does not even appear as a `ldstr` in `#US`.
  Because nothing reads it — and because the assembly contains **no** `Assembly.Load*`/`Activator`/`Emit` to
  execute anything anyway — it has **zero runtime effect** regardless of content. It is categorically **not a
  loadable payload** and **not a signature the code validates** (nothing validates it).
- **Identity (inferred, best static assessment):** 36 bytes, Shannon entropy ~5.1 bits/byte, 35/36 distinct
  values; does **not** RC4-decrypt to anything meaningful with either the string key `[125,238,…]` or the
  numeric key `[226,94,…]` (with or without a 4-byte length prefix), and is **not** a SHA-256/SHA-1/MD5 digest
  of res_0/res_1 or their concatenation. Hex: `4234e91be0d91efd567ba0f45737602988472b74921158fb61907ced5d6581a0dc7941bc`.
  Most likely a **ConfuserEx constants-protection decoy / unused segment or build leftover** (this build
  already uses an atypical *two-key, two-resource* constant scheme). It could in principle be an external
  watermark/license blob meant for some *other* tool, but the DLL itself never touches it. **No security
  impact either way.**

### Not a finding, but worth stating
- **No player/PII/credential access.** The game-side members touched are building/decay state only
  (`buildingID`, `buildingBlocks`, `decayEntities`, `EntityLinkBroadcast/Message`, `GetBuilding`,
  `NewBuildingID`, `UpdateNavMeshCarver`, `nav_carve_use_building_optimization`) plus `Connection.authLevel`
  for the admin gate and `ConsoleSystem.Index.Server.Dict` for command registration. With no network, none of
  it can leave the box.

---

## 3. ACCURACY RE-CHECK of the corrected deliverables (PART B)

Spot-checked `Whispers88Extension.reconstructed.cs` and `README_ANALYSIS.md` against the IL. **All the
corrections from the verification pass were applied correctly, and I found no NEW substantive errors
introduced.** Details:

| Item | IL evidence | Corrected files | Verdict |
|---|---|---|---|
| Time-gate = 2026-11-26 (`obfM_011`) | `obfM_011`: `UtcNow.Ticks > new DateTime(yr@0,mo@4,day@8, 0,0,0,1).Ticks` then logical-NOT → `obfF_007 = UtcNow <= expiry`; catch → `obfF_007=0`. One UtcNow + one DateTime ctor in whole assembly. Numeric pool @0/@4/@8 = 2026/11/26. | `.cs` `Expiry = new DateTime(2026,11,26,0,0,0,1)`, `GateOpen = UtcNow <= Expiry`, catch→false; re-checked every tick. | **CORRECT** (incl. the `millisecond=1` detail) |
| Four patch targets, all **prefix** | `obfM_012`: Harmony(id209); 4× `Harmony::Patch(HarmonyMethod(AccessTools.Method(typeof(H), "M1"/"M4"/"M2"/"M3")), null, null, null)` — **three `ldnull`** each (IL_09a2-a4, 09c7-c9, 09ec-ee, 0a11-13). Bindings: CheckSplit←M1, CheckMerge←M4, Split←M2, Attach←M3. | `.cs ApplyPatches` matches targets, methods, and prefix-only. | **CORRECT** |
| M1 (CheckSplit) = defer | `obfM_019`: gated `obfF_009 && obfF_007`; `if obfF_012 return true`; valid(`entity!=null && buildingID>0`) → `obfF_010.Add(buildingID)` then `return false`; invalid → `return false`. | `.cs H.M1`: gate+bypass→true; conditional `PendingSplit.Add`; `return false`. | **CORRECT** (matches incl. the invalid→false nuance) |
| M4 (CheckMerge) = synchronous, catch-only log | `obfM_020`: gated; entity!=null → `obfM_033(entity); return false`; catch → log id448 `"Running vanilla merge override "`+ex → `return true`. | `.cs H.M4`: try `return false`; catch LogError(id448 text)+`return true`. | **CORRECT** (log is catch-only) |
| M2 (Split) = synchronous, catch-only log | `obfM_021`: gated + null-checks; `obfM_032(mgr,building); return false`; catch → log id483 `"Running vanilla override "`+ex → `return true`. | `.cs H.M2`: try `return false`; catch LogError(id483 text)+`return true`. | **CORRECT** (log is catch-only) |
| M3 (Attach) = conditional skip, **NOT** unconditional false | `obfM_022`: gate closed→true; not-patched→true; `entity==null`→true; `buildingID == entity.buildingID` (IL_1405-140c `ceq`)→ **return false** (IL_1424); else **return true** (IL_1429). | `.cs H.M3`: 3 guard-returns=true; `if (buildingID == __instance.buildingID) return false; return true;` | **CORRECT — the dangerous unconditional `return false` is fixed** |
| Drain = batch 3, `Remove` (not Clear), bypass flag | `obfM_024(max)`: guard empty/`server==null`; `obfF_011.Clear()`; copy ≤`max` ids from `obfF_010`→`obfF_011`; `obfF_010.Remove(each)`; `obfF_012=1`; per id `GetBuilding`→ if `!=null && buildingBlocks.Count!=0` → `obfM_032`; finally `obfF_012=0`,`obfF_011.Clear()`. Tick calls `obfM_024(3)`. | `.cs DrainSplit`: scratch clear, copy-to-batch, `PendingSplit.Remove`, `Bypass=true/…/false`, `DrainBatch=3`. | **CORRECT** |
| `obfF_010`=`HashSet<uint>`, `obfF_011`=`List<uint>` | TypeSpec table has exactly two uint generic instantiations: `GenericInst CLASS <TypeRef#4> U4` and `… <TypeRef#5> U4`; TypeRef#4=`System.Collections.Generic.HashSet\`1`, #5=`System.Collections.Generic.List\`1`. `obfF_010` uses `Add`(+`pop`)/`GetEnumerator`; `obfF_011` uses `get_Item`/`Clear`/`get_Count`. | `.cs`: `PendingSplit = HashSet<uint>`, `_drainScratch = List<uint>`. | **CORRECT** (independently reconfirmed) |
| No Oxide permission | No `Oxide.Core.Libraries.Permission` TypeRef/MemberRef anywhere; Oxide.Core members used = `Extension::.ctor`, `ExtensionManager`, `VersionNumber::.ctor` only. Admin gate = `Connection==null || authLevel>=2`. | `.cs`: `IsAdmin()` stub (no permission); comment states no Oxide permission. | **CORRECT** |
| UnityEngine.Debug logging | MemberRef `UnityEngine.Debug::Log/LogWarning/LogError`; `obfM_016`=Log (used for id262 "Patches applied"), `obfM_018`=LogError (used in catch paths). | `.cs`: `Debug.Log/LogWarning/LogError` with `"[Whispers88] "` prefix. | **CORRECT** |

### Minor issues in `Whispers88Extension.reconstructed.cs` (none block the security conclusion)
1. **Compile fix needed — missing `using Oxide.Core;`.** `VersionNumber` lives in `Oxide.Core` (the file only
   imports `Oxide.Core.Extensions`), so `new VersionNumber(1,1,0)` will not resolve as written. Add
   `using Oxide.Core;` (or fully-qualify). This is the one concrete compile gap.
2. **Intentional stubs (correctly flagged in-file, listed for completeness):** `Split_Optimized`/`Merge_Optimized`
   bodies are commented out; `IsAdmin()` currently `return true` (TODO to wire to `ConsoleSystem.Arg`);
   `RegisterCommands`/`UnregisterCommands` are placeholders; `Interval`/timer is simplified. These are expected
   for a reconstruction skeleton and are marked as such.
3. **Minor behavioural simplifications vs IL (not bugs):** on expiry the IL tick calls `obfM_015` (full
   teardown = final drain + destroy timer GameObject + `UnpatchAll` + clear sets), whereas `.cs OnTick` does
   `RemovePatches()+StopTicking()`; and teardown order/mechanism in `Shutdown()` differs slightly from
   `obfM_015`. Functionally equivalent for the rebuild; worth a comment but not an error.
4. `H.M2`'s `object building` param and `_timer?.StopTicking()` on a `UnityEngine.Object` are legal C# and fine
   for a skeleton (Harmony accepts the assignable `object`; the Unity `?.`-vs-fake-null nuance is harmless here).

**Bottom line for PART B:** the corrected files faithfully represent the IL. The previously-dangerous
`H.M3` unconditional-`false`, the invented `PendingMerge` queue, the fake "whispers88 permission," and the
missing time-gate are all fixed/correct now. The only concrete code fix is adding `using Oxide.Core;`.

---

## 4. Evidence index
- `apisurface.py` output — AssemblyRef / ModuleRef(0) / ImplMap(0) / full TypeRef / 157 MemberRefs / 15 TypeSpecs / 3 ManifestResources.
- `res2probe.py` output — resources-blob verification + res_2 decrypt/hash attempts.
- `out/disasm.txt` — resolved IL (line refs cited inline above).
- `out/decrypted_strings.txt` — 49 RC4 strings (no network indicators).
- `#US` stream dump — 144 bytes, only 2 resource names + 3 profiler env names + `""`.
