#!/usr/bin/env python3
"""ClanTree.cs Performance & Quality Analysis Report"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import PageBreak
from datetime import datetime

# ── Colour palette ──────────────────────────────────────────────────────────
BG         = colors.HexColor("#0D1117")
PANEL      = colors.HexColor("#161B22")
BORDER     = colors.HexColor("#30363D")
ACCENT     = colors.HexColor("#58A6FF")
RED        = colors.HexColor("#F85149")
ORANGE     = colors.HexColor("#D29922")
YELLOW     = colors.HexColor("#E3B341")
GREEN      = colors.HexColor("#3FB950")
WHITE      = colors.HexColor("#E6EDF3")
MUTED      = colors.HexColor("#8B949E")
CODE_BG    = colors.HexColor("#1C2128")
CODE_TEXT  = colors.HexColor("#79C0FF")

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 18 * mm
T_MARGIN = B_MARGIN = 16 * mm

# ── Document ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    "/home/user/ClaudeAI/ClanTree_PerformanceReport.pdf",
    pagesize=A4,
    leftMargin=L_MARGIN, rightMargin=R_MARGIN,
    topMargin=T_MARGIN, bottomMargin=B_MARGIN,
)

# ── Styles ────────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()

def S(name, **kw):
    base = kw.pop("parent", "Normal")
    s = ParagraphStyle(name, parent=ss[base], **kw)
    return s

sTitle    = S("sTitle",    fontSize=26, textColor=WHITE,  alignment=TA_CENTER, spaceAfter=4,  fontName="Helvetica-Bold")
sSubtitle = S("sSubtitle", fontSize=12, textColor=MUTED,  alignment=TA_CENTER, spaceAfter=2,  fontName="Helvetica")
sDate     = S("sDate",     fontSize=9,  textColor=MUTED,  alignment=TA_CENTER, spaceAfter=16, fontName="Helvetica")
sSect     = S("sSect",     fontSize=14, textColor=ACCENT, spaceBefore=14, spaceAfter=4, fontName="Helvetica-Bold")
sBody     = S("sBody",     fontSize=9,  textColor=WHITE,  spaceAfter=4, fontName="Helvetica", leading=14)
sBodyJ    = S("sBodyJ",    fontSize=9,  textColor=WHITE,  spaceAfter=4, fontName="Helvetica", leading=14, alignment=TA_JUSTIFY)
sBullet   = S("sBullet",   fontSize=9,  textColor=WHITE,  spaceAfter=2, fontName="Helvetica", leftIndent=12, leading=13)
sCode     = S("sCode",     fontSize=7.5,textColor=CODE_TEXT, backColor=CODE_BG, fontName="Courier",
               leading=11, spaceAfter=4, leftIndent=6, rightIndent=6, spaceBefore=2)
sLabel    = S("sLabel",    fontSize=8,  textColor=MUTED,  fontName="Helvetica", spaceAfter=1)
sWarn     = S("sWarn",     fontSize=9,  textColor=ORANGE, fontName="Helvetica-Bold", spaceAfter=2)
sGreen    = S("sGreen",    fontSize=9,  textColor=GREEN,  fontName="Helvetica-Bold", spaceAfter=2)

def hr(): return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=8, spaceBefore=4)

def badge(text, col):
    return Paragraph(f'<font color="#{col.hexval()[2:]}" size="8"><b>{text}</b></font>', sBody)

def finding_table(fid, severity, title, sev_color, body_rows):
    """Render a finding card as a table."""
    sev_str = severity.upper()
    # Build hex string for inline markup — reportlab needs #RRGGBB format
    hex_col = "#" + sev_color.hexval()[2:].upper()
    header_data = [[
        Paragraph(f'<font color="#F85149" size="9"><b>{fid}</b></font>', sBody),
        Paragraph(f'<font color="{hex_col}" size="9"><b>{sev_str}</b></font>', sBody),
        Paragraph(f'<font color="#E6EDF3" size="9"><b>{title}</b></font>', sBody),
    ]]
    header_ts = TableStyle([
        ("BACKGROUND",  (0,0),(-1,-1), PANEL),
        ("LINEBELOW",   (0,0),(-1,0),  0.5, BORDER),
        ("LEFTPADDING", (0,0),(-1,-1), 8),
        ("RIGHTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",  (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("VALIGN",      (0,0),(-1,-1),"MIDDLE"),
    ])
    header = Table(header_data, colWidths=[30*mm, 22*mm, None])
    header.setStyle(header_ts)

    body_items = [header]
    for row in body_rows:
        body_items.append(row)

    outer_data = [[body_items]]
    outer = Table(outer_data, colWidths=[PAGE_W - L_MARGIN - R_MARGIN])
    outer.setStyle(TableStyle([
        ("BOX",         (0,0),(-1,-1), 0.8, sev_color),
        ("LEFTPADDING", (0,0),(-1,-1), 0),
        ("RIGHTPADDING",(0,0),(-1,-1), 0),
        ("TOPPADDING",  (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
        ("BACKGROUND",  (0,0),(-1,-1), PANEL),
    ]))
    return outer

def code_block(lines):
    text = "<br/>".join(lines.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").split("\n"))
    return Paragraph(text, sCode)

# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD STORY
# ═══════════════════════════════════════════════════════════════════════════════
story = []

# ── Cover ─────────────────────────────────────────────────────────────────────
story.append(Spacer(1, 28*mm))
story.append(Paragraph("ClanTree Plugin", sTitle))
story.append(Paragraph("Performance & Code Quality Analysis", sSubtitle))
story.append(Paragraph(f"Generated {datetime.now().strftime('%d %B %Y')}", sDate))
story.append(hr())

story.append(Paragraph("Executive Summary", sSect))
story.append(Paragraph(
    "ClanTree v1.0.0 is a central integration plugin managing personal and clan perk upgrades across "
    "currency, shop, and clan plugins. Its position as a hub means any stall it introduces on the Rust "
    "main thread propagates across every dependent system. This audit identified <b>3 Critical</b>, "
    "<b>5 High</b>, and <b>5 Medium</b> findings. The most severe is that all player and clan data is "
    "loaded and saved synchronously on the main thread using <b>File.ReadAllText / File.WriteAllText + "
    "JsonConvert</b>, with no background I/O worker. On a high-population server this directly produces "
    "the 100 ms stalls observed during peak raid windows.", sBodyJ))
story.append(Spacer(1, 4*mm))

# Risk matrix
risk_data = [
    [Paragraph("<b>ID</b>",    sBody), Paragraph("<b>Severity</b>", sBody),
     Paragraph("<b>Area</b>",  sBody), Paragraph("<b>Title</b>",    sBody)],
    ["CT-01", Paragraph('<font color="#F85149"><b>CRITICAL</b></font>', sBody), "Persistence", "Synchronous File.ReadAllText on player connect"],
    ["CT-02", Paragraph('<font color="#F85149"><b>CRITICAL</b></font>', sBody), "Persistence", "Coroutine HandleSaves() still writes JSON on main thread"],
    ["CT-03", Paragraph('<font color="#F85149"><b>CRITICAL</b></font>', sBody), "Persistence", "SaveClanData() called synchronously on player disconnect"],
    ["CT-04", Paragraph('<font color="#D29922"><b>HIGH</b></font>',    sBody), "Bug",         "RemoveOldClans() calls Directory.Delete() on a file path"],
    ["CT-05", Paragraph('<font color="#D29922"><b>HIGH</b></font>',    sBody), "Persistence", "JSON format vs protobuf binary — significant speed deficit"],
    ["CT-06", Paragraph('<font color="#D29922"><b>HIGH</b></font>',    sBody), "Integration", "IsClanAuthed() deserialises a JObject on every skill purchase"],
    ["CT-07", Paragraph('<font color="#D29922"><b>HIGH</b></font>',    sBody), "UI",          "Full CUI rebuild + CuiHelper.AddUi() on every menu open"],
    ["CT-08", Paragraph('<font color="#D29922"><b>HIGH</b></font>',    sBody), "Memory",      "GetClanMembers() returns pooled List — Pool leak risk"],
    ["CT-09", Paragraph('<font color="#E3B341"><b>MEDIUM</b></font>',  sBody), "Performance", "ShouldRemoveClanData() O(n) scan on every player disconnect"],
    ["CT-10", Paragraph('<font color="#E3B341"><b>MEDIUM</b></font>',  sBody), "Correctness", "TOCTOU race in currency: balance check then separate withdraw"],
    ["CT-11", Paragraph('<font color="#E3B341"><b>MEDIUM</b></font>',  sBody), "Thread-safe", "Instance bool flags IsInstantGathering / Deforesting"],
    ["CT-12", Paragraph('<font color="#E3B341"><b>MEDIUM</b></font>',  sBody), "Thread-safe", "FindEntitiesOfType uses shared Vis.colBuffer"],
    ["CT-13", Paragraph('<font color="#E3B341"><b>MEDIUM</b></font>',  sBody), "Performance", "SubscriptionInfo.subscribers uses List linear-scan Remove"],
]
rm_ts = TableStyle([
    ("BACKGROUND",  (0,0),(-1,0),   BORDER),
    ("BACKGROUND",  (0,1),(-1,-1),  PANEL),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[PANEL, CODE_BG]),
    ("GRID",        (0,0),(-1,-1),  0.3, BORDER),
    ("FONTNAME",    (0,0),(-1,0),   "Helvetica-Bold"),
    ("FONTSIZE",    (0,0),(-1,-1),  8),
    ("TEXTCOLOR",   (0,0),(-1,0),   WHITE),
    ("TEXTCOLOR",   (0,1),(-1,-1),  WHITE),
    ("LEFTPADDING", (0,0),(-1,-1),  5),
    ("RIGHTPADDING",(0,0),(-1,-1),  5),
    ("TOPPADDING",  (0,0),(-1,-1),  3),
    ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ("VALIGN",      (0,0),(-1,-1),  "MIDDLE"),
])
rm = Table(risk_data, colWidths=[13*mm, 22*mm, 26*mm, None])
rm.setStyle(rm_ts)
story.append(rm)
story.append(Spacer(1, 6*mm))

# ═══ CRITICAL ════════════════════════════════════════════════════════════════
story.append(PageBreak())
story.append(Paragraph("Critical Findings", sSect))
story.append(hr())

# CT-01
ct01_body = [
    Paragraph("On every player connect <code>SetupPlayer()</code> calls <code>LoadPlayerData()</code> which executes "
              "a synchronous <b>File.ReadAllText</b> followed by <b>JsonConvert.DeserializeObject</b> on the main thread. "
              "During a raid peak when many players reconnect simultaneously, each call blocks the main thread for the "
              "full disk read and JSON parse time — easily 5-30 ms each — causing cascading stall spikes.", sBodyJ),
    code_block(
        "// Line 697 – LoadPlayerData() – BLOCKS MAIN THREAD\n"
        "private PlayerInfo LoadPlayerData(ulong id)\n"
        "{\n"
        "    var path = $\"{FileDirectory}{id}.json\";\n"
        "    if (!File.Exists(path)) return new PlayerInfo();\n"
        "    var json = File.ReadAllText(path);          // ← blocking syscall\n"
        "    return JsonConvert.DeserializeObject<PlayerInfo>(json); // ← GC pressure\n"
        "}"
    ),
    Paragraph("<b>Fix:</b> Cache all player data at server startup into a dictionary during <code>OnServerInitialized</code> "
              "using a background <b>Thread</b> (not a coroutine). On connect, do a dictionary lookup — zero I/O. "
              "For players whose data is not yet loaded, queue an async read exactly as Kits v2 does with its "
              "<code>PlayerSaveWorker</code> and enqueue the player for delayed setup.", sBodyJ),
    code_block(
        "// Target pattern (Kits v2 style)\n"
        "// Startup: Thread reads all .json files off main thread into _cache\n"
        "// OnPlayerConnected: _cache.TryGetValue(player.userID, out var data)\n"
        "//   → hit: use immediately   → miss: enqueue background read"
    ),
]
story.append(KeepTogether([
    finding_table("CT-01", "CRITICAL", "Synchronous File.ReadAllText on player connect", RED, ct01_body),
    Spacer(1, 5*mm)
]))

# CT-02
ct02_body = [
    Paragraph("<code>HandleSaves()</code> (line 1365) is a Unity coroutine — it yields between batches of 10 writes "
              "using <code>yield return null</code>, but each iteration still calls <b>JsonConvert.SerializeObject + "
              "File.WriteAllText on the main thread</b>. A coroutine does not move work to a background thread; "
              "it merely spreads it across multiple frames. With 100+ online players, each write still stalls the frame "
              "it executes on. The save interval is typically triggered by <code>OnServerSave</code> every 5 minutes, "
              "producing a 10-frame stall cluster.", sBodyJ),
    code_block(
        "// Line 1375 – still on main thread despite yield\n"
        "private IEnumerator HandleSaves(bool saveOnUnload)\n"
        "{\n"
        "    int batchSize = 10;\n"
        "    for (int i = 0; i < players.Count; i += batchSize)\n"
        "    {\n"
        "        foreach (var id in players.GetRange(i, ...))\n"
        "        {\n"
        "            var json = JsonConvert.SerializeObject(data); // ← main thread\n"
        "            File.WriteAllText(path, json);                // ← main thread\n"
        "        }\n"
        "        yield return null; // spreads across frames, does NOT offload I/O\n"
        "    }\n"
        "}"
    ),
    Paragraph("<b>Fix:</b> Introduce a dedicated background <code>Thread</code> with an <code>AutoResetEvent</code> "
              "queue (identical to the <code>PlayerSaveWorker</code> pattern in Kits v2). Serialise to <code>byte[]</code> "
              "on the main thread, then enqueue the byte array. The worker thread calls "
              "<code>File.WriteAllBytes</code>. Add a dirty flag and jitter delay to avoid write storms.", sBodyJ),
    code_block(
        "// Target worker pattern\n"
        "private Thread _saveWorker;\n"
        "private AutoResetEvent _saveSignal = new AutoResetEvent(false);\n"
        "private ConcurrentQueue<(string path, byte[] data)> _saveQueue = new();\n\n"
        "void EnqueueSave(string path, PlayerInfo info)\n"
        "{\n"
        "    var bytes = Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(info));\n"
        "    _saveQueue.Enqueue((path, bytes));\n"
        "    _saveSignal.Set();\n"
        "}\n\n"
        "void SaveWorkerLoop()\n"
        "{\n"
        "    while (_running)\n"
        "    {\n"
        "        _saveSignal.WaitOne();\n"
        "        while (_saveQueue.TryDequeue(out var item))\n"
        "            File.WriteAllBytes(item.path, item.data);\n"
        "    }\n"
        "}"
    ),
]
story.append(KeepTogether([
    finding_table("CT-02", "CRITICAL", "Coroutine HandleSaves() still writes JSON on main thread", RED, ct02_body),
    Spacer(1, 5*mm)
]))

# CT-03
ct03_body = [
    Paragraph("When a player leaves or a clan disbands, <code>HandlePlayerGone()</code> → "
              "<code>ShouldRemoveClanData()</code> → <code>SaveClanData()</code> is called <b>synchronously outside "
              "any coroutine</b> (lines 1951, 769). This runs <code>JsonConvert.SerializeObject + File.WriteAllText</code> "
              "directly on the <code>OnPlayerDisconnected</code> hook — a main-thread event. In a raid scenario with "
              "players cycling in/out frequently, this fires multiple times per second.", sBodyJ),
    code_block(
        "// Line 1951 – OnClanMemberGone path\n"
        "void HandlePlayerGone(ulong id, List<ulong> members, string tag, bool disbanded)\n"
        "{\n"
        "    ...\n"
        "    if (!ShouldRemoveClanData(tag)) return;\n"
        "    SaveClanData(tag, null, true);   // ← SYNCHRONOUS FILE WRITE on disconnect\n"
        "}\n\n"
        "// Line 769 – SaveClanData\n"
        "void SaveClanData(string tag, ClanInfo data, bool remove)\n"
        "{\n"
        "    var json = JsonConvert.SerializeObject(data);\n"
        "    File.WriteAllText(path, json);    // ← blocks caller (main thread)\n"
        "}"
    ),
    Paragraph("<b>Fix:</b> Route all clan saves through the same background worker queue as CT-02. "
              "Mark the <code>ClanInfo.RequiresSave</code> flag on disconnect and let the periodic save cycle "
              "drain the dirty set. Only perform immediate synchronous saves in <code>Unload()</code> where "
              "blocking is acceptable.", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-03", "CRITICAL", "SaveClanData() called synchronously on player disconnect", RED, ct03_body),
    Spacer(1, 5*mm)
]))

# ═══ HIGH ════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story.append(Paragraph("High Severity Findings", sSect))
story.append(hr())

# CT-04
ct04_body = [
    Paragraph("<code>RemoveOldClans()</code> (line 1317) calls <code>Directory.Delete(file)</code> where "
              "<code>file</code> is a <b>file path string</b> obtained from <code>Directory.GetFiles()</code>. "
              "<code>Directory.Delete</code> on a regular file throws an <code>IOException</code>. This means "
              "<b>old clan data files are never actually cleaned up</b>. The exception is silently swallowed "
              "inside the coroutine, so the bug goes unnoticed but disk usage grows unboundedly across wipes.", sBodyJ),
    code_block(
        "// Line 1317-1338 – BUG: Directory.Delete on a file path\n"
        "private IEnumerator RemoveOldClans()\n"
        "{\n"
        "    foreach (string file in Directory.GetFiles(ClanDirectory))\n"
        "    {\n"
        "        ...\n"
        "        Directory.Delete(file);  // ← WRONG: throws IOException\n"
        "        //                            should be: File.Delete(file)\n"
        "    }\n"
        "}"
    ),
    Paragraph("<b>Fix:</b> Replace <code>Directory.Delete(file)</code> with <code>File.Delete(file)</code>. "
              "One character change — but critical for disk hygiene across wipes.", sBodyJ),
    code_block("File.Delete(file);  // correct"),
]
story.append(KeepTogether([
    finding_table("CT-04", "HIGH", "RemoveOldClans() calls Directory.Delete() on a file path (BUG)", ORANGE, ct04_body),
    Spacer(1, 5*mm)
]))

# CT-05
ct05_body = [
    Paragraph("ClanTree uses <b>Newtonsoft.Json</b> (<code>JsonConvert.SerializeObject/DeserializeObject</code>) "
              "for all player and clan persistence. By comparison Kits v2 and UltimateLeaderboard use "
              "<b>custom binary protobuf serialisation</b> to a <code>byte[]</code>. JSON is human-readable "
              "but 3–8× slower to serialise and produces 2–4× larger allocations, "
              "increasing GC pressure on every save cycle.", sBodyJ),
    Paragraph("<b>Impact on your server:</b> With 100 players online and save batches running during "
              "<code>OnServerSave</code>, the JSON serialisation alone adds several milliseconds per frame "
              "per batch. Combined with CT-02 (main-thread writes), this amplifies every stall.", sBodyJ),
    Paragraph("<b>Fix (preferred):</b> Migrate player data to the same <code>.pb</code> binary format used by "
              "Kits v2 — per-player files serialised with <code>ProtocolParser</code>. "
              "<b>Fix (interim):</b> At minimum, move serialisation off the hot path by pre-serialising to "
              "<code>byte[]</code> on a background thread via the worker queue (CT-02 fix).", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-05", "HIGH", "JSON serialisation — 3-8× slower than binary protobuf", ORANGE, ct05_body),
    Spacer(1, 5*mm)
]))

# CT-06
ct06_body = [
    Paragraph("<code>IsClanAuthed()</code> (line 2827) calls <code>Clans.Call&lt;JObject&gt;(\"GetClan\", clan)</code> "
              "on every skill upgrade button press. This crosses the Oxide plugin boundary, executes a "
              "<code>Clans.GetClan</code> handler, and deserialises a <code>JObject</code> — "
              "allocating multiple heap objects per button press. On a busy server where clan officers "
              "rapidly upgrade buffs during an event, this contributes measurable GC pressure.", sBodyJ),
    code_block(
        "// Line 2831 – per-upgrade JObject deserialisation\n"
        "JObject jObj = Clans.Call<JObject>(\"GetClan\", clan);\n"
        "var ownerid = jObj[\"owner\"]?.Value<ulong>() ?? 0;\n"
        "var moderators = jObj[\"moderators\"]?.ToObject<List<ulong>>();  // heap alloc"
    ),
    Paragraph("<b>Fix:</b> Cache clan role data in a local dictionary keyed by clan tag, populated on "
              "<code>OnClanMemberJoined</code> / <code>OnClanCreated</code> and invalidated on role changes. "
              "Alternatively, call a specific <code>IsClanModerator</code> API that returns a <code>bool</code> "
              "instead of a full <code>JObject</code> if the Clans plugin supports it.", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-06", "HIGH", "IsClanAuthed() deserialises JObject on every skill purchase", ORANGE, ct06_body),
    Spacer(1, 5*mm)
]))

# CT-07
ct07_body = [
    Paragraph("Every UI menu open, tree switch, and skill click calls <code>new CuiElementContainer()</code> "
              "and <code>CuiHelper.AddUi(player, container)</code>. <code>CuiHelper.AddUi</code> calls "
              "<code>JsonConvert.SerializeObject</code> on the full container before sending the RPC packet. "
              "This is the slow path — it re-serialises the entire UI on every user interaction.", sBodyJ),
    code_block(
        "// Line 2225, 2235, 2395, 2493, 2499, 2894, 2954 — repeated pattern\n"
        "var container = SendMainMenu(player, true);\n"
        "CuiHelper.AddUi(player, container);   // ← JsonConvert.SerializeObject every call\n\n"
        "// SendMainMenu builds everything from scratch each time:\n"
        "// new CuiElementContainer(), loops all config.PersonalBuffs, etc."
    ),
    Paragraph("The established high-performance pattern (used in PulseDailyGems and UltimateLeaderboard) is: "
              "<b>(1)</b> build the static skeleton once at startup into a <code>byte[] JsonUtf8</code>, "
              "<b>(2)</b> embed named markers for dynamic values, "
              "<b>(3)</b> use <code>ZString.CreateUtf8StringBuilder()</code> to splice dynamic values "
              "into the pre-baked bytes, and "
              "<b>(4)</b> send via raw <code>Network.Net.sv.StartWrite()</code> RPC — bypassing CuiHelper entirely.", sBodyJ),
    Paragraph("<b>Interim fix</b> (low effort): Cache the clan/personal background container JSON per-player "
              "and only rebuild on perk level changes. Do not rebuild the entire container on every tree-switch — "
              "send only the diff (the partial container approach already used in <code>TryLevelSkill</code> is "
              "a step in the right direction but still uses <code>CuiHelper.AddUi</code>).", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-07", "HIGH", "Full CUI rebuild + CuiHelper.AddUi() on every menu open", ORANGE, ct07_body),
    Spacer(1, 5*mm)
]))

# CT-08
ct08_body = [
    Paragraph("<code>GetClanMembers()</code> (line 572) returns a <code>Pool.Get&lt;List&lt;ulong&gt;&gt;()</code> "
              "pooled list. Every call site that forgets to call <code>Pool.FreeUnmanaged(ref list)</code> leaks "
              "that list from the pool permanently, degrading pool efficiency over time. "
              "The <code>OnClanCreated</code> handler (line 1972) correctly uses <code>try/finally</code> to free, "
              "but any future caller added without the pattern will silently leak.", sBodyJ),
    code_block(
        "// Line 572 – returns pooled list, caller MUST free\n"
        "List<ulong> GetClanMembers(string tag)\n"
        "{\n"
        "    var members = Pool.Get<List<ulong>>();  // ← caller owns lifecycle\n"
        "    ...\n"
        "    return members;\n"
        "}\n\n"
        "// Safe usage pattern (OnClanCreated, line 1972)\n"
        "var members = GetClanMembers(tag);\n"
        "try   { foreach (var id in members) ... }\n"
        "finally { Pool.FreeUnmanaged(ref members); }"
    ),
    Paragraph("<b>Fix:</b> Return an <code>IReadOnlyList&lt;ulong&gt;</code> from a cached internal structure "
              "rather than a pooled list, eliminating the lifetime management burden. Alternatively, accept an "
              "<code>Action&lt;IEnumerable&lt;ulong&gt;&gt;</code> callback to guarantee scope safety.", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-08", "HIGH", "GetClanMembers() returns pooled List — Pool leak risk at every call site", ORANGE, ct08_body),
    Spacer(1, 5*mm)
]))

# ═══ MEDIUM ══════════════════════════════════════════════════════════════════
story.append(PageBreak())
story.append(Paragraph("Medium Severity Findings", sSect))
story.append(hr())

# CT-09
ct09_body = [
    Paragraph("<code>ShouldRemoveClanData()</code> (line 1001) iterates the entire "
              "<code>_BuffManager.Buffs</code> dictionary on every <code>OnPlayerDisconnected</code> event "
              "to check whether any remaining online player belongs to the departing player's clan. "
              "With 100 online players this is O(n) on every disconnect.", sBodyJ),
    code_block(
        "// Line 1001 – O(n) on every disconnect\n"
        "bool ShouldRemoveClanData(string tag)\n"
        "{\n"
        "    foreach (var kv in _BuffManager.Buffs)   // iterates ALL online players\n"
        "        if (kv.Value.Clan == tag) return false;\n"
        "    return true;\n"
        "}"
    ),
    Paragraph("<b>Fix:</b> Maintain a <code>Dictionary&lt;string, HashSet&lt;ulong&gt;&gt; _clanOnline</code> "
              "that is updated on connect/disconnect. <code>ShouldRemoveClanData</code> becomes an O(1) "
              "<code>_clanOnline[tag].Count == 0</code> check.", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-09", "MEDIUM", "ShouldRemoveClanData() O(n) scan of all online players on disconnect", YELLOW, ct09_body),
    Spacer(1, 5*mm)
]))

# CT-10
ct10_body = [
    Paragraph("Currency deductions use a two-step pattern: check balance (<code>CanAffordGemCost</code>) "
              "then withdraw (<code>TakeGems</code>). These are two separate <code>Interface.Oxide.CallHook</code> "
              "calls with no atomicity guarantee. A malicious or laggy client could trigger two simultaneous "
              "upgrade presses, both passing the balance check before either deduction occurs (TOCTOU race).", sBodyJ),
    code_block(
        "// Lines 2928-2934 – TryLevelSkill: check then take (not atomic)\n"
        "if (!CanAffordGemCost(player.userID, nextLevelData.gemCost)) { ... return; }\n"
        "if (!TakeGems(player.userID, nextLevelData.gemCost)) return;\n"
        "// Between these two calls a second concurrent request can pass the first check"
    ),
    Paragraph("<b>Fix:</b> Introduce a per-player <code>HashSet&lt;ulong&gt; _purchaseInProgress</code>. "
              "Guard <code>TryLevelSkill</code> / <code>TryLevelClanSkill</code> with an early exit if the "
              "player's ID is already in the set, and remove on completion. Alternatively, request an atomic "
              "<code>TryDeduct</code> API from the currency plugin developer.", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-10", "MEDIUM", "TOCTOU race in currency: balance check then separate withdraw", YELLOW, ct10_body),
    Spacer(1, 5*mm)
]))

# CT-11
ct11_body = [
    Paragraph("Two instance-level boolean fields — <code>IsInstantGathering</code> and <code>Deforesting</code> "
              "(lines ~1570, ~1640) — are set inside <code>OnDispenserGathered</code> and read across method "
              "calls within the same synchronous execution path. While they are accessed only on the main thread "
              "today, their lifetime spans multiple methods without clear ownership, making them fragile state. "
              "If Oxide ever dispatches hooks concurrently (possible in future Rust updates) these will race.", sBodyJ),
    Paragraph("<b>Fix:</b> Replace with local variables passed as parameters, or use a per-player "
              "<code>BuffDetails</code> field if they must span the lifetime of a gather event. "
              "Eliminate implicit shared mutable state between hook methods.", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-11", "MEDIUM", "Instance bool flags IsInstantGathering / Deforesting — implicit shared state", YELLOW, ct11_body),
    Spacer(1, 5*mm)
]))

# CT-12
ct12_body = [
    Paragraph("<code>FindEntitiesOfType&lt;T&gt;</code> (line 1787) uses the global static "
              "<code>Vis.colBuffer</code> collision buffer directly. This buffer is shared across all Unity "
              "physics queries on the main thread. If any other plugin (or Rust itself) calls a physics query "
              "concurrently or if this method is ever called from a non-main-thread context, the buffer "
              "contents will be corrupted, producing missed or phantom entity hits.", sBodyJ),
    code_block(
        "// Line 1787 – shared static buffer\n"
        "int count = Physics.OverlapSphereNonAlloc(pos, radius, Vis.colBuffer, layers);\n"
        "for (int i = 0; i < count; i++) { ... }\n"
        "// Must clear after use — already done at line 1793 (good)\n"
        "// Risk: interleaved physics queries from other plugins"
    ),
    Paragraph("<b>Fix:</b> Allocate a local <code>Collider[]</code> buffer inside the method for safety, "
              "or ensure this method is only called serially from main-thread hooks (document the constraint). "
              "The existing null-clear after use (line 1793) is correct — keep it.", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-12", "MEDIUM", "FindEntitiesOfType uses shared Vis.colBuffer — fragile on concurrent queries", YELLOW, ct12_body),
    Spacer(1, 5*mm)
]))

# CT-13
ct13_body = [
    Paragraph("<code>SubscriptionInfo.subscribers</code> (line 1901) is a <code>List&lt;ulong&gt;</code>. "
              "<code>RemoveSubscriber(id)</code> calls <code>subscribers.Remove(id)</code> which is an O(n) "
              "linear scan. With a large number of players holding a given buff (e.g. WoodcuttingYield active "
              "for all online players), adding and removing on every connect/disconnect becomes measurably slow.", sBodyJ),
    code_block(
        "// Line 1913 – O(n) linear scan on every disconnect\n"
        "public void RemoveSubscriber(ulong id)\n"
        "{\n"
        "    subscribers.Remove(id);   // List.Remove = O(n)\n"
        "    if (subscribers.Count == 0) { Unsubscribe(...); }\n"
        "}"
    ),
    Paragraph("<b>Fix:</b> Replace <code>List&lt;ulong&gt;</code> with <code>HashSet&lt;ulong&gt;</code>. "
              "<code>HashSet.Remove</code> is O(1) amortised. Update <code>AddSubscriber</code> to use "
              "<code>subscribers.Add(id)</code> — no other changes required.", sBodyJ),
]
story.append(KeepTogether([
    finding_table("CT-13", "MEDIUM", "SubscriptionInfo.subscribers uses List — O(n) Remove on each disconnect", YELLOW, ct13_body),
    Spacer(1, 5*mm)
]))

# ═══ POSITIVE PATTERNS ═══════════════════════════════════════════════════════
story.append(PageBreak())
story.append(Paragraph("Architectural Strengths", sSect))
story.append(hr())

positives = [
    ("Subscription system", "Dynamic hook subscribe/unsubscribe based on active buff holders correctly avoids Oxide overhead for hooks with zero subscribers."),
    ("Pool usage in UI", "SendActiveBuffs uses Pool.Get<List<string>>() with try/finally free — correct pattern."),
    ("Image CRC cache", "TryCacheImg correctly checks FileStorage before re-downloading, stores CRC in SettingsData, and sets ReqSave flag rather than writing immediately."),
    ("Partial UI updates", "TryLevelSkill sends only diff panels (SendNodeLevel, SendSkillButton, SendActiveBuffs) rather than the full container after a purchase — reducing packet size per click."),
    ("HarmonyLib patching", "SwitchAmmoTypesIfNeeded_Patch and OnMedicalToolAppliedPatch correctly guard IsSteamId() before buffer lookups."),
    ("Clan event hooks", "OnClanMemberJoined/Gone/Disbanded/Created correctly maintain ClanBuffValues in BuffDetails, keeping in-memory buff state consistent."),
]
pos_data = [[Paragraph(f"<b>{k}</b>", sBody), Paragraph(v, sBody)] for k, v in positives]
pos_ts = TableStyle([
    ("BACKGROUND",    (0,0),(-1,-1), PANEL),
    ("ROWBACKGROUNDS",(0,0),(-1,-1), [PANEL, CODE_BG]),
    ("GRID",          (0,0),(-1,-1), 0.3, BORDER),
    ("FONTSIZE",      (0,0),(-1,-1), 8),
    ("TEXTCOLOR",     (0,0),(-1,-1), WHITE),
    ("LEFTPADDING",   (0,0),(-1,-1), 6),
    ("RIGHTPADDING",  (0,0),(-1,-1), 6),
    ("TOPPADDING",    (0,0),(-1,-1), 4),
    ("BOTTOMPADDING", (0,0),(-1,-1), 4),
    ("VALIGN",        (0,0),(-1,-1), "TOP"),
])
pos_table = Table(pos_data, colWidths=[45*mm, None])
pos_table.setStyle(pos_ts)
story.append(pos_table)
story.append(Spacer(1, 6*mm))

# ═══ PRIORITY FIX TABLE ══════════════════════════════════════════════════════
story.append(Paragraph("Priority Fix Roadmap", sSect))
story.append(hr())

pri_data = [
    [Paragraph("<b>#</b>", sBody), Paragraph("<b>ID</b>", sBody),
     Paragraph("<b>Action</b>", sBody), Paragraph("<b>Effort</b>", sBody), Paragraph("<b>Impact</b>", sBody)],
    ["1", "CT-04", "Fix Directory.Delete → File.Delete in RemoveOldClans()",     "5 min",  "Bug fix"],
    ["2", "CT-10", "Add per-player purchase lock (HashSet) to prevent TOCTOU",    "1 hr",   "Correctness"],
    ["3", "CT-13", "Change SubscriptionInfo.subscribers to HashSet<ulong>",       "15 min", "Medium perf"],
    ["4", "CT-09", "Add _clanOnline dictionary for O(1) ShouldRemoveClanData",    "1 hr",   "Medium perf"],
    ["5", "CT-03", "Route SaveClanData through dirty flag + save queue",           "2 hrs",  "Critical perf"],
    ["6", "CT-02", "Implement PlayerSaveWorker thread for all player/clan writes", "4 hrs",  "Critical perf"],
    ["7", "CT-01", "Preload player data at startup on background thread",          "4 hrs",  "Critical perf"],
    ["8", "CT-06", "Cache clan auth data locally; eliminate per-click JObject",    "2 hrs",  "High perf"],
    ["9", "CT-08", "Remove pooled-list return from GetClanMembers",                "1 hr",   "Safety"],
    ["10","CT-07", "Cache static UI skeleton as byte[]; use raw RPC send",         "8+ hrs", "High perf"],
    ["11","CT-05", "Migrate to binary protobuf serialisation (wipe boundary)",     "8+ hrs", "High perf"],
]
pri_ts = TableStyle([
    ("BACKGROUND",    (0,0),(-1,0),  BORDER),
    ("ROWBACKGROUNDS",(0,1),(-1,-1), [PANEL, CODE_BG]),
    ("GRID",          (0,0),(-1,-1), 0.3, BORDER),
    ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
    ("FONTSIZE",      (0,0),(-1,-1), 8),
    ("TEXTCOLOR",     (0,0),(-1,0),  WHITE),
    ("TEXTCOLOR",     (0,1),(-1,-1), WHITE),
    ("LEFTPADDING",   (0,0),(-1,-1), 5),
    ("RIGHTPADDING",  (0,0),(-1,-1), 5),
    ("TOPPADDING",    (0,0),(-1,-1), 3),
    ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
])
pri_table = Table(pri_data, colWidths=[8*mm, 14*mm, None, 18*mm, 22*mm])
pri_table.setStyle(pri_ts)
story.append(pri_table)
story.append(Spacer(1, 6*mm))

# ═══ COMPARISON TABLE ════════════════════════════════════════════════════════
story.append(Paragraph("Comparison: ClanTree vs Kits v2 / UltimateLeaderboard", sSect))
story.append(hr())

comp_data = [
    [Paragraph("<b>Feature</b>", sBody), Paragraph("<b>ClanTree</b>", sBody),
     Paragraph("<b>Kits v2</b>", sBody), Paragraph("<b>UltimateLeaderboard</b>", sBody)],
    ["Serialisation", Paragraph('<font color="#F85149">JSON (Newtonsoft)</font>', sBody),
     Paragraph('<font color="#3FB950">Binary protobuf</font>', sBody),
     Paragraph('<font color="#3FB950">Binary protobuf</font>', sBody)],
    ["Load on connect", Paragraph('<font color="#F85149">Sync ReadAllText</font>', sBody),
     Paragraph('<font color="#3FB950">Async worker</font>', sBody),
     Paragraph('<font color="#D29922">Sync (partially fixed)</font>', sBody)],
    ["Save on event", Paragraph('<font color="#F85149">Sync WriteAllText</font>', sBody),
     Paragraph('<font color="#3FB950">Dirty + worker queue</font>', sBody),
     Paragraph('<font color="#3FB950">Dirty + worker queue</font>', sBody)],
    ["Background I/O", Paragraph('<font color="#F85149">None</font>', sBody),
     Paragraph('<font color="#3FB950">Dedicated Thread</font>', sBody),
     Paragraph('<font color="#3FB950">Dedicated Thread</font>', sBody)],
    ["Save jitter", Paragraph('<font color="#F85149">No</font>', sBody),
     Paragraph('<font color="#3FB950">Random 5-25s delay</font>', sBody),
     Paragraph('<font color="#3FB950">Random delay</font>', sBody)],
    ["UI send method", Paragraph('<font color="#F85149">CuiHelper.AddUi</font>', sBody),
     Paragraph('<font color="#3FB950">Raw RPC packet</font>', sBody),
     Paragraph('<font color="#3FB950">Raw RPC packet</font>', sBody)],
    ["UI caching", Paragraph('<font color="#F85149">None — full rebuild</font>', sBody),
     Paragraph('<font color="#3FB950">byte[] JsonUtf8 + markers</font>', sBody),
     Paragraph('<font color="#3FB950">byte[] JsonUtf8 + markers</font>', sBody)],
]
comp_ts = TableStyle([
    ("BACKGROUND",    (0,0),(-1,0),  BORDER),
    ("ROWBACKGROUNDS",(0,1),(-1,-1), [PANEL, CODE_BG]),
    ("GRID",          (0,0),(-1,-1), 0.3, BORDER),
    ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
    ("FONTSIZE",      (0,0),(-1,-1), 8),
    ("TEXTCOLOR",     (0,0),(-1,0),  WHITE),
    ("LEFTPADDING",   (0,0),(-1,-1), 5),
    ("RIGHTPADDING",  (0,0),(-1,-1), 5),
    ("TOPPADDING",    (0,0),(-1,-1), 3),
    ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
])
comp_table = Table(comp_data, colWidths=[38*mm, 45*mm, 40*mm, 46*mm])
comp_table.setStyle(comp_ts)
story.append(comp_table)
story.append(Spacer(1, 6*mm))
story.append(Paragraph(
    "ClanTree is structurally the weakest of the three plugins on persistence. As the central plugin "
    "interfacing with currency and clan systems, its I/O improvements should be prioritised before the "
    "next high-population raid event.",
    sBodyJ))

# ── Footer ────────────────────────────────────────────────────────────────────
def add_page_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(PAGE_W / 2, 10 * mm,
        f"PulseRust High-Performance Analysis  •  ClanTree v1.0.0  •  {datetime.now().strftime('%d %b %Y')}")
    canvas.restoreState()

doc.build(story, onFirstPage=add_page_bg, onLaterPages=add_page_bg)
print("PDF written to /home/user/ClaudeAI/ClanTree_PerformanceReport.pdf")
