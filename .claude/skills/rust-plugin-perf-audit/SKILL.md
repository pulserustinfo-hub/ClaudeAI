---
name: rust-plugin-perf-audit
description: >-
  Audits an Oxide Rust plugin for server performance problems and fixes them,
  proving each cost by decompiling the game and Oxide code behind it. Covers
  five patterns: uncached game queries run once per collider or per loop step,
  the same lang text built once per player in a broadcast, values rebuilt every
  tick that change rarely, hook handlers that declare fewer parameters than
  Oxide passes, and failed searches retried with the same inputs. Use when the
  user asks to review, audit, profile or optimise a plugin's performance,
  mentions lag, frame drops, hook time warnings, garbage collection, or a slow
  hook, coroutine, timer or broadcast, even if they do not name a pattern. For
  CUI refresh cost use cui-partial-refresh-audit instead.
---

# Rust plugin performance audit

A one-line call in a plugin can hide a hook dispatch, a physics query and three allocations. This skill finds the places where that hidden cost is multiplied (per collider, per player, per tick, per hook call) and gives the correct shape for each. Its rule is that no cost is reported until the implementation behind the call has been read.

Terms used below. A **hot path** is code that runs per hook call, per tick of a loop, per player or per collider. A **burst** is a hot path that runs for a short time (an event starting, a broadcast). **Verified** means the implementation was read; anything else is **unverified** and is never stated as fact or fixed.

Sources:

- Game and Oxide DLLs: `e:\Rust\Plugins\Oxide\`. `Assembly-CSharp.dll` there is already patched by Oxide, so every `Interface.CallHook("...")` call site is visible in the decompiled code.
- Hook list: `E:\Rust\uMod\Oxide.Rust\resources\Rust.opj` (`HookName`, `TypeName`, `Signature.Name`, `ArgumentString`).
- Other plugins: `e:\Rust\Plugins\Workspace\`.
- CUI send and destroy cost: the `cui-partial-refresh-audit` skill. Do not repeat that audit here.

Follow the target plugin's `AGENTS.md` (pooling, `CoroutineManager`, lang, change review). An audit changes how much work is done, never what a player sees. Ask the user before any fix that would.

## What the code does not tell you

These facts come from decompiled code. Re-check them when the DLLs are updated; they decide every fix.

- **Server-side privilege queries are never cached.** `BaseEntity.GetBuildingPrivilege()` and `BasePlayer.IsBuildingAuthed()` pass `PrivilegeCacheDefaultValue()`, which returns `base.isClient`. On the server that is `false`.
- **A privilege query is also a hook call.** `BaseEntity.GetBuildingPrivilege(OBB, ...)` starts with `Interface.CallHook("OnBuildingPrivilege", ...)`, boxing an `OBB`, two `bool`s and a `float`, before it queries the building-block grid over 16 m plus the entity's extents.
- **A physics query with no mask returns everything.** `Physics.OverlapSphereNonAlloc(position, radius, results)` passes `layerMask = -1` and `QueryTriggerInteraction.UseGlobal`.
- **One entity is many colliders.** `GameObjectEx.ToBaseEntity` walks up the parents with one registry lookup per level. Trees, ores and building blocks each return several colliders for the same entity.
- **Every lang lookup allocates.** `Lang.GetMessage` calls `GetMessageKey`, whose first statement builds `$"{lang}{Path.DirectorySeparatorChar}{plugin.Name}.json"`. `Lang.GetLanguage(userId)` is one dictionary read and allocates nothing.
- **Oxide filters hook calls by argument type, cheaply.** `HookCache` keys on the runtime type of each argument and remembers which handler matches. A handler typed `BasePlayer` is not invoked for other entities, and the miss costs a few hashtable reads.
- **A handler with fewer parameters than the hook passes costs more.** In `CSPlugin.OnCallHook`, when `args.Length != Parameters.Length` Oxide takes an array from `ObjectArrayPool` (lock, pop), copies the arguments, and returns it afterwards (clear, lock, push), on every call.
- **Every hook call into a plugin has a fixed cost.** `Plugin.CallHook` reads `GC.CollectionCount`, starts and stops a stopwatch and tracks the call, before the handler runs. Subscribing only while the feature is live removes that cost the rest of the time.
- **A method group is a new delegate.** `CancelInvoke(entity.Method)` and `Invoke(entity.Method, t)` allocate one each call. `InvokeHandler` matches by delegate equality, so a stored delegate cancels the same invoke.
- **The game already repeats some sends.** `BasePlayer` runs `TeamUpdate` for every player about every 4 s (`InvokeRandomized(TeamUpdate, 1f, 4f, 1f)`). A plugin's own `TeamUpdate` only makes the change show sooner.
- **Fast player queries are coarse and capped.** `BaseEntity.Query.Server.GetPlayersInSphereFast` selects whole 32 m grid cells with no distance test, and `Spatial.Grid<T>.Query` stops when the result array is full.

## Workflow

1. Read the plugin's `AGENTS.md`. Read the whole plugin, not only the hooks.
2. List the hot paths: every Oxide hook, `OnTriggerEnter`, every coroutine loop and timer, every loop over `BasePlayer.activePlayerList` or a collider buffer, and whatever they call.
3. For each hook, find its entry in `Rust.opj`, then read the game method that calls it. Write down what triggers it and what the handler does before its first early-out. `OnItemAddedToContainer`, `CanAcceptItem` and `OnEntityEnter` fire server-wide; hooks behind a player RPC do not.
4. For each game, Oxide or other-plugin call on a hot path, read the implementation before judging it:

   ```powershell
   ilspycmd -t BasePlayer 'e:\Rust\Plugins\Oxide\Assembly-CSharp.dll' | Out-File <scratchpad>\decomp\BasePlayer.cs -Encoding utf8
   ilspycmd -l c 'e:\Rust\Plugins\Oxide\Facepunch.System.dll'   # list types when the assembly is not known
   ```

   Oxide types are in `Oxide.Core.dll` (`Oxide.Core.Libraries.Lang`, `Oxide.Core.Plugins.CSPlugin`, `HookCache`, `PluginManager`). If no decompiler is installed, ask the user before installing one.
5. Run the Checklist. A grep hit is a place to look, not a finding.
6. Write the findings ordered by severity. Each has the plugin line, the decompiled evidence, how often it runs, a severity, the fix, and verified or unverified. State call rates as estimates unless they were measured. Keep guard-rail violations in a separate list.
7. Ask the user about anything uncertain: player counts, config values in production, whether a pattern is intentional.
8. Before the first edit of a file that is not under git, copy it to the scratchpad. Fix one pattern at a time, build, and open the diff in the user's IDE after each group.

Most handlers in a well-kept plugin are already cheap. Say so. Report what was checked and left alone, with the reason, so the user can see it was read.

## Pattern 1: an uncached game query per collider or per loop step

**Recognise.** A loop over a collider buffer (or over candidate positions) whose body calls `GetBuildingPrivilege`, `IsBuildingAuthed`, `GetComponentInParent`, a raycast or another query. Also look at the order of tests around it: an arithmetic test that could reject the candidate sits after the physics.

**Cost.** Each privilege query is uncached, dispatches a hook and searches the building grid. With no layer mask a 20 m sphere returns dozens of colliders in a forest and hundreds near a base, and several belong to the same entity. A search that tries 10 candidates per frame multiplies all of it by 10.

**Correct shape.** Run every test that needs no physics first. Ask each entity once, with a pooled set. Keep the set's `Free` in `finally`.

Before:

```csharp
if (TryPreparePosition(ref point))                       // raycast, sphere check, blocked-point query
{
    Target target = FindTargetInRange(point);            // distance test over a short cached list
    if (target == null)
        rejected++;
    else if (TryGetDestination(target, out Vector3 destination))
    {
        // build the route
    }
}
```

```csharp
int count = Physics.OverlapSphereNonAlloc(position, radius, Buffer);
bool blocked = false;
for (int i = 0; i < count; i++)
{
    Collider collider = Buffer[i];
    Buffer[i] = null;
    if (blocked || collider == null)
        continue;

    BaseEntity entity = collider.ToBaseEntity();
    if (entity != null && entity.GetBuildingPrivilege() != null)   // uncached, once per collider
        blocked = true;
}
```

After:

```csharp
// The range test reads x and z only and needs no physics, so it runs first.
Target target = FindTargetInRange(point);
if (target == null)
{
    rejected++;
}
else if (TryPreparePosition(ref point))
{
    if (TryGetDestination(target, out Vector3 destination))
    {
        // build the route
    }
}
```

```csharp
bool blocked = false;
HashSet<BaseEntity> checkedEntities = Pool.Get<HashSet<BaseEntity>>();
try
{
    for (int i = 0; i < count; i++)
    {
        Collider collider = Buffer[i];
        Buffer[i] = null;
        if (blocked || collider == null)
            continue;

        BaseEntity entity = collider.ToBaseEntity();
        if (entity != null && checkedEntities.Add(entity) && entity.GetBuildingPrivilege() != null)
            blocked = true;
    }
}
finally
{
    Pool.FreeUnmanaged(ref checkedEntities);
}
```

Check before reordering: the cheap test must not depend on anything the expensive step changes (here placement only changed `y`). Tell the user if a diagnostic counter now counts differently. Do not add a layer mask unless the user agrees, because it changes which colliders count.

## Pattern 2: the same text built once per player

**Recognise.** A "send to all" helper that loops `BasePlayer.activePlayerList` and, per player, calls the lang helper, `string.Format`, a time formatter, or clones an argument array.

**Cost.** Every `lang.GetMessage` allocates a string. A message with a formatted time is 3 to 5 lookups, 2 formats and an array per player. At 500 players one broadcast is thousands of allocations in one frame, for a text that is identical for everyone with the same language.

**Correct shape.** Decide first whether the message is enabled. Build the text once per language, keyed on `lang.GetLanguage(userId)`, in a pooled dictionary that lives for one broadcast. Copy the argument array only when a value must be replaced.

Before:

```csharp
public static void SendToAll(string key, params object[] args)
{
    foreach (BasePlayer player in BasePlayer.activePlayerList)
        if (player != null)
            SendToPlayer(player, key, args);
}

public static void SendToPlayer(BasePlayer player, string key, params object[] args)
{
    object[] clone = new object[args.Length];
    for (int i = 0; i < args.Length; i++)
        clone[i] = args[i];

    for (int i = 0; i < clone.Length; i++)
        if (clone[i] is int)
            clone[i] = FormatTime(player.UserIDString, (int)clone[i]);

    MessageConfig config = GetOverride(key);
    if (config != null && !config.Enabled)               // checked after the work
        return;

    Send(config ?? _defaultConfig, player, _ins.L(key, player.UserIDString, clone));
}
```

After:

```csharp
public static void SendToAll(string key, params object[] args)
{
    if (!TryGetMessageConfig(key, out MessageConfig config))
        return;

    Dictionary<string, string> messages = Pool.Get<Dictionary<string, string>>();
    try
    {
        foreach (BasePlayer player in BasePlayer.activePlayerList)
        {
            if (player == null)
                continue;

            string language = _ins.lang.GetLanguage(player.UserIDString) ?? string.Empty;
            if (!messages.TryGetValue(language, out string message))
            {
                message = BuildMessage(key, player.UserIDString, args);
                messages[language] = message;
            }

            Send(config, player, message);
        }
    }
    finally
    {
        Pool.FreeUnmanaged(ref messages);
    }
}

private static string BuildMessage(string key, string userId, object[] args)
{
    object[] formatted = args;
    for (int i = 0; i < args.Length; i++)
    {
        if (!(args[i] is int seconds))
            continue;

        if (ReferenceEquals(formatted, args))            // the caller's array is shared by every recipient
        {
            formatted = new object[args.Length];
            Array.Copy(args, formatted, args.Length);
        }

        formatted[i] = FormatTime(userId, seconds);
    }

    return _ins.L(key, userId, formatted);
}
```

This only works when the text depends on nothing but the language. A message that contains the reader's own name or balance is built per player. Sending one packet to a list of connections (`ConsoleNetwork.SendClientCommand(List<Connection>, ...)`) saves more, but it calls `OnSendCommand` with a list instead of a connection, so ask before using it.

## Pattern 3: a value rebuilt every tick that changes rarely

**Recognise.** Inside a coroutine loop or timer: a string built and then compared with the last one sent, or a method group passed to `CancelInvoke`, `Invoke` or `IsInvoking`.

**Cost.** Small and constant: around ten allocations per second for a name that changes once a minute, one delegate per second for a cancel. It never spikes, but it is garbage for the whole life of the feature.

**Correct shape.** Compare the cheap input (the whole-minute value), not the expensive output (the formatted string). Keep the delegate for as long as the entity is the same.

Before:

```csharp
public void UpdateMarker(Vector3 position)
{
    string name = BuildMarkerName();                      // lang lookups and formats, every second
    bool nameChanged = name != _lastSentName;
```

```csharp
droppedItem.CancelInvoke(droppedItem.IdleDestroy);        // new delegate every tick
```

After:

```csharp
public void UpdateMarker(Vector3 position)
{
    // The name shows hours and minutes only.
    int minutes = GetMarkerMinutes();
    bool nameChanged = minutes != _lastSentMinutes;
    string name = nameChanged ? BuildMarkerName() : _lastSentName;
```

```csharp
if (!ReferenceEquals(_trackedDrop, droppedItem))
{
    _trackedDrop = droppedItem;
    _trackedDropIdleDestroy = droppedItem.IdleDestroy;
}

droppedItem.CancelInvoke(_trackedDropIdleDestroy);
```

Set the cached input wherever the value is first sent, and clear cached entity references when the entity goes away. Before removing a repeated call, check whether the game re-arms what it cancels: `DroppedItem` invokes `IdleDestroy` again after a stack merge and after an unstick, so the cancel has to stay.

## Pattern 4: a hook handler with fewer parameters than the hook passes

**Recognise.** A handler for a server-wide hook whose parameter count is lower than the argument count at the `Interface.CallHook` call site. `ItemContainer.Insert` passes `(this, item, sourcePlayer)` to `OnItemAddedToContainer`. `ItemContainer.CanAcceptItem` passes `(this, item, targetPos, player)` to `CanAcceptItem`.

**Cost.** A pooled array is taken, filled and returned on every call. Small each time, but these hooks fire for every item moved on the server.

**Correct shape.** Declare every argument, in the order of the call site.

Before:

```csharp
private ItemContainer.CanAcceptResult? CanAcceptItem(ItemContainer container, Item item, int targetPos)
private void OnItemAddedToContainer(ItemContainer container, Item item)
```

After:

```csharp
private ItemContainer.CanAcceptResult? CanAcceptItem(ItemContainer container, Item item, int targetPos, BasePlayer sourcePlayer)
private void OnItemAddedToContainer(ItemContainer container, Item item, BasePlayer sourcePlayer)
```

Take the argument list from the decompiled call site and confirm it against `ArgumentString` in `Rust.opj`. Only bother for hooks that fire server-wide. Keep the handler's first statement a cheap rejection (an item id or user id compare) before any other work.

## Pattern 5: a failed search retried with the same inputs

**Recognise.** A method called from a loop that searches (steps outwards, tries candidates), and on failure logs and returns. Nothing records the failure, so the next tick runs the same search and logs again.

**Cost.** The whole search every tick for as long as the situation lasts: in the audited case 40 raycasts, 40 uncached privilege queries with their hook dispatches, and a formatted warning, every second.

**Correct shape.** Remember what failed (who and where) and skip until an input changes. Clear the record on success.

Before:

```csharp
Vector3 origin = player.transform.position;
// ... step outwards, a raycast and a privilege query per step ...
if (!found)
{
    PrintWarning($"Could not find a free position for {player.displayName} at {origin}");
    return;
}
```

After:

```csharp
Vector3 origin = player.transform.position;

// A search that found nothing gives the same answer until this player moves.
if (_failedUserId == player.userID && (origin - _failedOrigin).sqrMagnitude < RetryDistanceSqr)
    return;

// ... step outwards ...
if (!found)
{
    _failedUserId = player.userID;
    _failedOrigin = origin;
    PrintWarning($"Could not find a free position for {player.displayName} at {origin}");
    return;
}

_failedUserId = 0;
```

Key the record on every input that can change the answer. A position alone is wrong when two players can stand on the same spot with different rights.

## Checklist

Run each search over the plugin file, then read every hit.

| Pattern | Search (regex) | It is a finding when |
|---|---|---|
| 1 | `OverlapSphere\|OverlapBox\|Vis\.\w+\(` | the loop over the results calls a game query per collider, or the query has no layer mask and a radius above a few metres |
| 1 | `GetBuildingPrivilege\(\|IsBuildingAuthed\(\|GetComponentInParent<` | the call is inside a loop, or runs before a test that needs no physics |
| 2 | `in BasePlayer\.activePlayerList` | the body builds text, calls the lang helper or formats per player |
| 2 | `lang\.GetMessage\|\bL\(` | the call is reachable from a per-player loop with the same key and arguments |
| 3 | `WaitForSeconds\|timer\.(Every\|Repeat)` | the loop body builds a string or collection that is only compared with the previous one |
| 3 | `(CancelInvoke\|Invoke\|IsInvoking)\(\w+\.\w+[,)]` | it runs every tick |
| 4 | `private \S+ (On\|Can)\w+\(` | the parameter count is lower than the `CallHook` argument count and the hook fires server-wide |
| 4 | `Subscribe\(` | a server-wide hook is never unsubscribed while its feature is idle |
| 5 | `Print(Warning\|Error)\(` | the method is called from a loop and returns after logging without recording the failure |

Also read, since the patterns do not cover them: `OnTriggerEnter` bodies, trigger radius and layer, entity `Spawn` and `Kill` counts per event, `SendNetworkUpdate` frequency on global entities such as map markers, web requests, and data save size. In the audited plugin all of these were light; report them as checked.

## Verification

Build the plugin after each group of fixes and report the real output. Then walk each case through the final code.

| Case | Expected |
|---|---|
| A candidate outside the cheap test's range | no physics query, no privilege query |
| A sphere holding one entity with several colliders | one privilege query |
| Broadcast to N players who share one language | one text build, N sends |
| Broadcast of a message switched off in config | nothing built, nothing sent |
| A tick where the displayed value is unchanged | no string built, no network update |
| A dropped entity that is the same as last tick | no delegate allocated |
| A server-wide hook call for an unrelated item or entity | handler returns on its first comparison, no pooled array taken |
| A search that failed, same player, same position | search skipped, nothing logged |
| The same search after the player moves | search runs again |

Then check what must not have changed: messages, markers and effects are the same for the player, hook signatures still match `Rust.opj`, pooled objects are freed in `finally`, and loops still run through `CoroutineManager`.

Re-run the Checklist on the fixed file. A hit that remains is expected when the call is still needed (the query is still made, once per entity); say why for each.

Reading code and compiling is not a live test. Call rates are estimates and no timing was measured unless the user ran it on a server, so say which results were only read.
