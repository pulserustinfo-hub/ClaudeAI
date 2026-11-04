#!/usr/bin/env python3
"""EventCtf comparison report: Example 1 (v1.1.5) vs Example 2 (v2.0.1)."""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

OUTPUT = "/home/user/ClaudeAI/EventCtf_ComparisonReport.pdf"

# ── Colour palette (same as the ClanTree / UltimateLeaderboard reports) ──────
BG        = colors.HexColor("#0D1117")
PANEL     = colors.HexColor("#161B22")
BORDER    = colors.HexColor("#30363D")
ACCENT    = colors.HexColor("#58A6FF")
RED       = colors.HexColor("#F85149")
ORANGE    = colors.HexColor("#D29922")
YELLOW    = colors.HexColor("#E3B341")
GREEN     = colors.HexColor("#3FB950")
WHITE     = colors.HexColor("#E6EDF3")
MUTED     = colors.HexColor("#8B949E")
CODE_BG   = colors.HexColor("#1C2128")
CODE_TEXT = colors.HexColor("#79C0FF")

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 18 * mm
T_MARGIN = B_MARGIN = 16 * mm
W = PAGE_W - L_MARGIN - R_MARGIN

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=L_MARGIN, rightMargin=R_MARGIN, topMargin=T_MARGIN, bottomMargin=B_MARGIN,
    title="EventCtf v1.1.5 vs v2.0.1 - Comparison",
    author="PulseRust High-Performance Analysis",
)

# ── Styles ────────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()


def S(name, **kw):
    return ParagraphStyle(name, parent=ss["Normal"], **kw)


sTitle    = S("sTitle", fontSize=24, textColor=WHITE, alignment=TA_CENTER, spaceAfter=6,
              fontName="Helvetica-Bold", leading=28)
sSubtitle = S("sSubtitle", fontSize=11.5, textColor=MUTED, alignment=TA_CENTER, spaceAfter=2,
              fontName="Helvetica", leading=15)
sDate     = S("sDate", fontSize=9, textColor=MUTED, alignment=TA_CENTER, spaceAfter=12,
              fontName="Helvetica")
sSect     = S("sSect", fontSize=14, textColor=ACCENT, spaceBefore=10, spaceAfter=4,
              fontName="Helvetica-Bold")
sSub      = S("sSub", fontSize=10.5, textColor=WHITE, spaceBefore=6, spaceAfter=3,
              fontName="Helvetica-Bold")
sBody     = S("sBody", fontSize=9, textColor=WHITE, spaceAfter=4, fontName="Helvetica", leading=13.5)
sBodyJ    = S("sBodyJ", fontSize=9, textColor=WHITE, spaceAfter=4,
              fontName="Helvetica", leading=13.5, alignment=TA_JUSTIFY)
sCell     = S("sCell", fontSize=8, textColor=WHITE, fontName="Helvetica", leading=10.5)
sCellB    = S("sCellB", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold", leading=10.5)
sBullet   = S("sBullet", fontSize=9, textColor=WHITE, fontName="Helvetica", leading=13,
              leftIndent=10, bulletIndent=0, spaceAfter=2)
sPre      = ParagraphStyle("sPre", fontName="Courier", fontSize=7.2, leading=9.4, textColor=CODE_TEXT)
sFix      = S("sFix", fontSize=9, textColor=GREEN, fontName="Helvetica-Bold", spaceAfter=1, leading=12)


def hexof(col):
    return "#" + col.hexval()[2:].upper()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def c(s):
    """Inline code."""
    return f'<font name="Courier" color="#79C0FF">{esc(s)}</font>'


def P(text, style=sBodyJ):
    return Paragraph(text, style)


def bullets(items, style=sBullet):
    return [Paragraph(t, style, bulletText="•") for t in items]


def hr():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6, spaceBefore=2)


def code(text, width=W - 16):
    t = Table([[Preformatted(text.strip("\n"), sPre)]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


SEV_COLOR = {"HIGH": RED, "MEDIUM": ORANGE, "LOW": YELLOW}


def card(fid, sev, title, items, where=None):
    """Finding card. One table row per item so long cards split cleanly across pages."""
    col = SEV_COLOR[sev.split()[0]]
    hx = hexof(col)
    head = Table([[
        Paragraph(f'<font color="{hx}"><b>{fid}</b></font>', sCell),
        Paragraph(f'<font color="{hx}"><b>{sev}</b></font>', sCell),
        Paragraph(f"<b>{title}</b>", S(fid + "h", fontSize=9, textColor=WHITE,
                                        fontName="Helvetica", leading=12)),
    ]], colWidths=[17 * mm, 25 * mm, W - 42 * mm])
    head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    rows = [[head]]
    if where:
        rows.append([Paragraph(f'<font color="#8B949E">Where: {where}</font>', sCell)])
    rows += [[it] for it in items]
    t = Table(rows, colWidths=[W])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, col),
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("LEFTPADDING", (0, 0), (-1, 0), 0), ("RIGHTPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
        ("LEFTPADDING", (0, 1), (-1, -1), 8), ("RIGHTPADDING", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 3), ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ("NOSPLIT", (0, 0), (-1, min(2, len(rows) - 1))),
    ]))
    return t


def grid(data, widths, header=True, valign="TOP"):
    rows = []
    for r_i, row in enumerate(data):
        cells = []
        for cell in row:
            if isinstance(cell, str):
                cells.append(Paragraph(cell, sCellB if (header and r_i == 0) else sCell))
            else:
                cells.append(cell)
        rows.append(cells)
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PANEL, CODE_BG]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), valign),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), BORDER))
    t.setStyle(TableStyle(style))
    return t


def tag(text, col):
    return f'<font color="{hexof(col)}"><b>{text}</b></font>'


V1 = tag("v1.1.5", ORANGE)
V2 = tag("v2.0.1", GREEN)
TIE = tag("Tie", MUTED)

story = []

# ═══════════════════════════════════════════════════════════════════════════════
#  COVER + SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Spacer(1, 14 * mm))
story.append(Paragraph("EventCtf: Capture the Flag", sTitle))
story.append(Paragraph("Example 1 (v1.1.5) vs Example 2 (v2.0.1)", sSubtitle))
story.append(Paragraph("Performance &amp; code quality comparison for a high-population Rust server",
                       sSubtitle))
story.append(Paragraph(f"Generated {datetime.now().strftime('%d %B %Y')}", sDate))
story.append(hr())

verdict = Table([[[
    Paragraph(f'<font color="{hexof(GREEN)}" size="12"><b>Verdict: run Example 2 (v2.0.1).</b></font>',
              S("vt", leading=16, spaceAfter=4)),
    *bullets([
        "It fixes almost every real bug in v1.1.5, including the two that could break a live event, "
        "and closes most of the teleport loophole.",
        "It is only leaner during the spawn search. During a live event it costs exactly the same as "
        "v1.1.5: the two biggest per-second costs were not touched.",
        "It adds six small issues of its own (R-01 to R-06). Each is a short fix.",
    ]),
]]], colWidths=[W])
verdict.setStyle(TableStyle([
    ("BOX", (0, 0), (-1, -1), 1, GREEN), ("BACKGROUND", (0, 0), (-1, -1), PANEL),
    ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
story.append(verdict)
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("Executive Summary", sSect))
story.append(P(
    "Both files are the same event. A flag spawns at a random spot, and the carrier follows a chain of "
    "checkpoints to a monument. While they carry it, vehicles, teleports and safe zones are blocked. "
    "Example 2 (v2.0.1 by Nathan, 3,231 lines) is a rewrite of Example 1 (v1.1.5 by Adem, 2,369 lines). "
    "It keeps the same event loop and config layout."))
story.append(P(
    "<b>Example 2 is the better plugin.</b> It makes 19 improvements over Example 1 (page 2). Two of "
    "them fix bugs that could break a live event. In v1.1.5, a destroyed or despawned flag left the "
    "event running with nothing to capture, and a checkpoint could count twice. v2.0.1 blocks teleports "
    f"through the {c('CanTeleport')} API instead of a four-command chat list. It also adds a permission, "
    "survives a broken config file and cleans up after a crash. Its spawn search only samples valid "
    "land and creates no garbage."))
story.append(P(
    "<b>It is not faster during a live event.</b> The two biggest recurring costs are identical in both "
    "versions. Every second, the carrier is briefly given the admin flag so an on-screen marker can be drawn, "
    "which sends full player updates to everyone nearby. Also every second, both map markers are resent "
    "to every connected player, even when the flag hasn't moved. With 300 players online and 60 near the "
    "flag, that is about 900 marker messages and at least 120 full player updates per second. Fixing "
    "these two (EC-01 and EC-02) is the biggest win available on a high-pop server, and neither fix is "
    "large."))
story.append(P(
    "<b>It also adds six issues of its own</b> (R-01 to R-06). Fix two of them first. A pooled dictionary "
    "is passed to EventManager and recycled as soon as the call returns. The map-marker protection uses "
    "a hook signature that Oxide stopped calling after 31 December 2023. Two gameplay holes remain in "
    "both versions: the carrier can log off with the flag (EC-03), and can ride standing on boats, "
    "trains, balloons and the cargo ship (EC-04)."))

story.append(Paragraph("Scorecard", sSect))
score = [
    ["Area", "v1.1.5 (Example 1)", "v2.0.1 (Example 2)", "Better"],
    ["Cost with no event running", "Hooks off, close to zero", "Hooks off, close to zero; keeps a 4 MB spawn map in memory", TIE],
    ["Plugin load", "Trivial", "Sweeps every player and sleeper; builds the spawn map over ~256 frames", V1],
    ["Spawn search", "Random circle: ~16% of samples off the map, plus ocean; allocates on every check",
     "Pre-filtered land map; no allocations in the checks", V2],
    ["Per-second cost during an event", "Admin-flag screen marker + 3 marker broadcasts", "Identical", TIE],
    ["Busy hooks during an event", "Cheap early exits", "Same, plus O(1) command lookup and one OnEntityEnter", V2],
    ["Flag destroyed or despawned", "Not detected; event runs to timeout", "Detected within 1 s; despawn cancelled on every drop", V2],
    ["Checkpoints", "Can count twice; can throw after a win", "Guarded", V2],
    ["Teleport blocking", "4 chat commands", "Same + CanTeleport API", V2],
    ["Vehicle blocking", "Seats + scrap heli platform", "Same", TIE],
    ["Carrier logs off", "Not handled", "Not handled", TIE],
    ["Safe-zone kick", "Spheres only; ignores scale", "Spheres only; uses world size", V2],
    ["Event marker protection", "Works (current hook signature)", "Retired signature; never runs", V1],
    ["Crash leftovers", "Vending marker can persist", "Markers not saved; startup sweep", V2],
    ["Config handling", "Bad JSON breaks the load", "Backup, safe defaults, migration", V2],
    ["Admin access", "player.IsAdmin", "eventctf.admin permission", V2],
    ["Discord logs", "Wrong duration; posts on every reload", "Correct", V2],
    ["Data passed to EventManager", "Fresh dictionary", "Pooled dictionary, recycled after the call", V1],
]
story.append(grid(score, [38 * mm, 50 * mm, 66 * mm, None], valign="MIDDLE"))
story.append(Spacer(1, 2 * mm))
story.append(P(f"<b>Result:</b> {V2} better in 10 areas, {V1} in 3, tie in 4. All three areas where "
               "v1.1.5 is better are cheap to fix in v2.0.1."))

# ═══════════════════════════════════════════════════════════════════════════════
#  WHAT V2 DOES BETTER
# ═══════════════════════════════════════════════════════════════════════════════
story.append(Spacer(1, 4 * mm))
story.append(Paragraph("What Example 2 (v2.0.1) does better", sSect))
story.append(hr())
story.append(P("Line numbers refer to each file as uploaded. \"v1 L798\" means line 798 of Example 1."))
better = [
    ["#", "Area", "Example 1 (v1.1.5)", "Example 2 (v2.0.1)"],
    ["1", "Flag destroyed or despawned",
     f"{c('_item == null')} can never be true for a removed item (v1 L798), so the event keeps running with no flag",
     f"{c('IsLiveFlag()')} checks {c('Item.IsValid()')} and the stored item ID every tick and ends the event (L2278-2285, L2599)"],
    ["2", "Re-dropped flag despawning",
     "Despawn timer cancelled only on the first spawn (v1 L672). A flag dropped on death can despawn",
     "Cancelled on every dropped copy, every tick (L2640-2644)"],
    ["3", "Nearby alerts",
     "Loops over the whole shared 64-slot AI buffer, so players left over from NPC scans anywhere on the map get alerts (v1 L867, L916)",
     "Loops only over the slots just filled (L2683, L2747)"],
    ["4", "Checkpoints",
     "No 'already used' guard. A checkpoint can count twice, or throw after a win (v1 L1122-1130)",
     f"{c('_consumed')} guard and null checks (L1449-1461)"],
    ["5", "Vending map marker",
     "Saved with the map, so it can stay after a crash (v1 L1169)",
     f"{c('enableSaving = false')} before {c('Spawn()')} (L1518)"],
    ["6", "Teleports",
     "Only /home, /tp, /tpr, /tpa typed in chat (v1 L208-220)",
     f"Adds {c('CanTeleport')}, which blocks the teleport itself in any plugin that calls it, including /town, /outpost and menu buttons (L1755-1767)"],
    ["7", "Blocked-command lookup",
     "Culture-sensitive linear scan with a closure (v1 L213)",
     "O(1) case-insensitive HashSet (L419-433, L1776)"],
    ["8", "Discord logs",
     "Always reports the configured length. Posts 'no winner' on every reload and failed spawn (v1 L984, L265, L71)",
     "Reports the time that actually passed. No post on unload or failed spawn (L2292-2296, L1614, L2381)"],
    ["9", "Config file",
     "Bad JSON breaks the load. The file is rewritten on every load (v1 L1546-1551)",
     "Timestamped backup, safe defaults, migration and filling of missing sections. Saves only when something changed (L84-230, L288-313, L376-410)"],
    ["10", "Admin commands", f"{c('player.IsAdmin')}",
     f"{c('eventctf.admin')} permission. Players using the console commands are checked too (L1581, L1799-1811)"],
    ["11", "Stale markers and crash leftovers",
     "Teammates who went offline keep their CTF marker",
     "Tracks every player given a marker and cleans them up, online or not. Startup and connect sweep (L2266, L2542-2566, L1922-2010)"],
    ["12", "Coroutines",
     f"Run on {c('ServerMgr')} and are stopped by hand",
     "Run on the plugin's own object, destroyed on unload. Every loop checks it still belongs to the current event (L1343-1349, L2315, L2597)"],
    ["13", "Spawn sampling",
     "Random point in a circle 1.2x the map width. About 16% of samples land off the map, and more in the ocean (v1 L1285-1290)",
     f"{c('SpawnDistribution')} over a pre-filtered topology map: every sample is on valid land (L60-68, L1845-1880, L2332)"],
    ["14", "Spawn checks (garbage)",
     "New HashSet, new collider array and 1-2 new strings per collider on every check (v1 L1349-1378)",
     "Shared 512-slot buffer and a type check for safe zones. No allocations (L2899, L3024-3058)"],
    ["15", "Waypoints and spawn terrain",
     "A checkpoint could land on a riverbed or lake bottom",
     "Rejects water deeper than 0.25 m. The flag spawn also excludes lakes and cliffsides (L2996-3007, L66-67)"],
    ["16", "Safe-zone kick",
     "Uses the collider's local radius and ignores its scale (v1 L311)",
     "Uses the zone's real size in the world (L2014-2015)"],
    ["17", "Config lookups",
     "Linear search with a closure for every message (v1 L1425)",
     "Dictionaries built once (L435-479, L3191-3198)"],
    ["18", "/ctfnewendpoint",
     "Uses the nearest monument centre; can throw on custom maps (v1 L433)",
     "Requires standing inside the monument's bounds. Saves 3 decimals in an invariant format (L2156-2248)"],
    ["19", "Messages",
     "'Node Event ends in…' left over from another plugin (v1 L1464)",
     "'Capture The Flag event ends in…' (L1308)"],
]
story.append(grid(better, [7 * mm, 30 * mm, 64 * mm, None]))

# ═══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE BY PHASE
# ═══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story.append(Paragraph("Performance: where v2.0.1 is faster, and where it isn't", sSect))
story.append(hr())
story.append(P(
    "The plugin's cost comes in five phases. v2.0.1 is clearly better in one (the spawn search), slightly "
    "better in two, and identical in the one that runs for the whole event."))
phases = [
    ["Phase", "v1.1.5", "v2.0.1", "Verdict"],
    ["No event running", "Close to zero. All event hooks unsubscribed",
     f"Close to zero. Only {c('OnPlayerConnected')} stays subscribed (cheap). Keeps ~4 MB in memory", TIE],
    ["Plugin load", "Trivial",
     "Synchronous sweep of every player and sleeper. Spawn map built over 256 frames, 16,384 lookups per frame", V1],
    ["Spawn search (event start)",
     "~16% of samples off the map, plus ocean. Each candidate allocates a HashSet, an array and many strings",
     "Every sample on valid land. Physics checks allocate nothing", V2],
    ["Live event, every second",
     "3 map-marker messages to every player + at least 2 full player updates to everyone near the carrier",
     "Identical, line for line", TIE],
    ["Busy hooks during the event", "Cheap early exits on item ID / player checks",
     "Same. One OnEntityEnter instead of two overloads; O(1) command lookup", V2],
    ["Broadcast messages", "Formatted per player; closure + linear search per player",
     "Formatted per player; dictionary lookup per player", V2],
]
story.append(grid(phases, [32 * mm, 54 * mm, 62 * mm, None]))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("What the per-second cost looks like at high pop", sSub))
story.append(P(
    "Example: 300 players online, 60 of them within network range of the flag carrier. These numbers are "
    "the same for both versions."))
load = [
    ["Source", "Per tick", "Recipients", "Per second"],
    ["Map markers (vending + ring)", "3 network messages", "Every connected player (300)", "~900 messages"],
    ["Admin-flag screen marker", f"2x {c('SendNetworkUpdateImmediate()')}", "Everyone near the carrier (60)",
     "at least 120 full player updates"],
]
story.append(grid(load, [44 * mm, 56 * mm, 44 * mm, None]))
story.append(Spacer(1, 3 * mm))
story.append(P(
    "Both run every second for the whole event, which is an hour by default, and both mostly send "
    "nothing new. The flag usually sits still or moves a few metres, and the marker label only changes "
    "once a minute. A full player update is one of the larger messages Rust sends, and here it goes to "
    "the busiest spot on the map. EC-01 cuts the player updates by about 75% (or removes them), and "
    "EC-02 cuts marker traffic by over 99% while the flag is still, without changing what players see."))

story.append(Paragraph("Why the spawn-search change matters", sSub))
story.append(P(
    "In v1.1.5, each candidate spot runs a 20 m physics query with no layer filter, which allocates a "
    "new array of every collider found. Then it creates a new HashSet, reads every collider's name "
    "(a new string each time) and lower-cases it (another string), and builds a closure. All of this "
    "happens up to 10 times per frame, plus up to 10 smaller checks per candidate for the waypoints. "
    "That garbage has to be collected later, and collection on a large high-pop heap is expensive. "
    "v2.0.1 removes all of it, and its sampler never wastes attempts on the ocean or off-map points. The "
    "remaining per-entity work is covered in EC-06."))

story.append(Paragraph("Map sampling and spawn map numbers", sSub))
nums = [
    ["Item", "Value"],
    ["v1.1.5 random-point sampler", "Circle of radius 0.6 x map size; 15.9% of points fall outside the map (simulated)"],
    ["v2.0.1 spawn map size", "ClosestPowerOfTwo(map size / 2) squared: 2048 x 2048 = 4 MB for maps 3,500-6,000; 1 MB for 3,000"],
    ["v2.0.1 spawn map build", "8 rows per frame: 256 frames x 16,384 topology lookups (2048 map)"],
    ["Spawn attempts per frame", "10 in both versions"],
]
story.append(grid(nums, [52 * mm, None]))

# ═══════════════════════════════════════════════════════════════════════════════
#  WHAT V2 DOES WORSE
# ═══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story.append(Paragraph("What Example 2 (v2.0.1) does worse", sSect))
story.append(hr())
story.append(P("These issues are new in v2.0.1. None of them is in v1.1.5."))

story.append(card("R-01", "MEDIUM (risk)", "Pooled dictionary passed to EventManager, then recycled", [
    P(f"{c('OnOwnerWin')} takes a {c('Dictionary')} from the pool and passes it to the "
      f"{c('OnEventEnd')} hook. It returns the dictionary to the pool as soon as the call comes back. If "
      "EventManager, or any plugin listening to that hook, keeps the reference and reads it later (in a "
      "timer, NextTick or a stored list), it will find it empty or holding someone else's data, and the "
      "clan win may not be recorded. v1.1.5 passed a fresh dictionary, which is always safe. Pooling "
      "here saves one tiny allocation per event, so it isn't worth the risk."),
    code("""
// v2.0.1 L2824-2833
Dictionary<string, bool> clansForSending = Pool.Get<Dictionary<string, bool>>();
try   { clansForSending.Add(clanTag, true); Interface.CallHook("OnEventEnd", clansForSending); }
finally { Pool.FreeUnmanaged(ref clansForSending); }   // cleared while EventManager may still hold it
"""),
    Paragraph("Fix", sFix),
    code("""
Interface.CallHook("OnEventEnd", new Dictionary<string, bool> { [clanTag] = true });
"""),
    P("Rule of thumb: never return a pooled object to the pool after giving it to another plugin."),
], where="v2.0.1 L2824-2833 (v1.1.5 L979-981 was safe)"))
story.append(Spacer(1, 4 * mm))

story.append(card("R-02", "LOW", "Map-marker protection uses a hook signature Oxide no longer calls", [
    P(f"v2.0.1 changed the hook to {c('OnMapMarkerRemove(BasePlayer player, MapNote note)')}. Oxide "
      "deprecated that form in 2023 and stopped calling it after 31 December 2023. The current hook is "
      f"{c('OnMapMarkerRemove(BasePlayer player, List<MapNote> mapMarker, int index)')}, which v1.1.5 uses. "
      "In v2.0.1 the method never runs, so players can delete the event's destination marker. The "
      "gameplay impact is small, but the feature has silently stopped working, and the fix is one line."),
    Paragraph("Fix (the v1.1.5 signature)", sFix),
    code("""
private object OnMapMarkerRemove(BasePlayer player, List<MapNote> mapMarker, int index)
{
    if (_eventController == null || player == null || mapMarker == null
        || index < 0 || index >= mapMarker.Count)
        return null;

    return _eventController.IsEventMapMarker(mapMarker[index]) ? (object)true : null;
}
"""),
], where="v2.0.1 L1744-1753"))
story.append(Spacer(1, 4 * mm))

story.append(card("R-03", "LOW", "enableSaving = false set after the flag has already spawned", [
    P(f"{c('SpawnFlag')} and {c('UpdateFlagOwner')} set {c('enableSaving = false')} on the dropped flag "
      f"after {c('Item.Drop()')} has already spawned it. Rust adds an entity to its save list when it "
      f"spawns, and as far as I know only {c('BaseEntity.EnableSaving(false)')} takes it back out; "
      "assigning the field afterwards doesn't. If that's right, the flag is still written to the save. "
      "After a crash it comes back as a normal item on the ground, and the startup sweep doesn't catch "
      "it because it only cleans player inventories. The map markers and spheres set the field before "
      f"{c('Spawn()')}, which is correct."),
    Paragraph("Fix", sFix),
    code("""
DroppedItem droppedItem = _item.Drop(position, Vector3.up) as DroppedItem;
droppedItem.EnableSaving(false);                 // updates the save list, not just the field
droppedItem.CancelInvoke(droppedItem.IdleDestroy);
"""),
], where="v2.0.1 L2433, L2642"))
story.append(Spacer(1, 4 * mm))

story.append(card("R-04", "LOW", "Startup and connect sweeps are too broad and run all at once", [
    P("At startup the plugin walks every online player and every sleeper. It removes every "
      f"{c('twitchrivalsflag')} item and every map note labelled \"CTF\", and does the same for each "
      "player who connects while no event is running. This has two side effects:"),
    *bullets([
        "Any flag or \"CTF\" marker that didn't come from this plugin is deleted too. A player's own "
        "marker named \"CTF\" disappears every time they log in.",
        "Late in a wipe the sleeper list can hold thousands of players. The sweep does them all in a "
        "single frame, so reloading the plugin causes a one-off lag spike.",
    ]),
    Paragraph("Fix", sFix),
    *bullets([
        "Tag the event flag when it's created (" + c('_item.name = "CTF Event Flag";') + ") and only remove "
        "items with that name.",
        f"Save {c('_markedPlayers')} to a small data file and clean only those players, not everyone "
        "with a \"CTF\" note.",
        f"Or spread the sleeper sweep over frames on the existing {c('CoroutineManager')}, for example "
        "200 players per frame.",
    ]),
], where="v2.0.1 L1922-2010"))
story.append(Spacer(1, 4 * mm))

story.append(card("R-05", "LOW", "Spawn map held in memory for the plugin's whole lifetime", [
    P(f"{c('BuildSpawnMap')} allocates a byte map of {c('ClosestPowerOfTwo(World.Size / 2)')} squared: "
      "2048 x 2048 = 4 MB for any map from 3,500 to 6,000. It then keeps that map, plus the quadtree "
      f"{c('SpawnDistribution')} builds on top of it, for as long as the plugin is loaded. Building it "
      "takes 256 frames with 16,384 topology lookups per frame. It's a one-off cost and acceptable, but "
      "1024 x 1024 (1 MB, about 4.4 m cells on a 4,500 map) is plenty for picking a flag spawn."),
    Paragraph("Fix (optional)", sFix),
    code("""
int resolution = Mathf.ClosestPowerOfTwo((int)(World.Size * 0.25f));   // 1024 on 3.5k-6k maps
"""),
], where="v2.0.1 L1845-1880"))
story.append(Spacer(1, 4 * mm))

story.append(card("R-06", "LOW", "Waypoint placement rules changed; flag point checked twice", [
    P("v1.1.5 rejected any waypoint more than 0.5 m above or below bare terrain. v2.0.1 replaced that "
      "with Rust's own spawn placement checks plus a water-depth test. The water test is a real "
      "improvement: no more checkpoints on a riverbed. But if the engine's placement mask accepts rocks "
      "or other world objects, a waypoint can now sit on top of one. Separately, the flag point from "
      f"{c('SpawnDistribution.Sample')} goes through the same placement checks again. As far as I can "
      f"tell, {c('Sample')} already runs them, so that is one extra raycast and sphere check per sample."),
    Paragraph("Fix", sFix),
    code("""
// IsIntermediatePositionSuitable: keep v2's checks and restore v1's terrain test
if (Mathf.Abs(TerrainMeta.HeightMap.GetHeight(position) - position.y) > 0.5f)
    return false;

// TryPrepareFlagPosition: Sample() already placed the point; only run the blocked-area test
return !IsBlockedPoint(position, _ins._config.FlagDelivery.SpawnBlockedRadius);
"""),
], where="v2.0.1 L2340, L2953-3010 (v1.1.5 L1303-1319)"))

# ═══════════════════════════════════════════════════════════════════════════════
#  STILL PRESENT IN BOTH
# ═══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story.append(Paragraph("Still in both versions: what to improve for high pop", sSect))
story.append(hr())
story.append(P("These apply to v2.0.1 (the version to keep). Line numbers are v2.0.1 unless marked v1."))

story.append(card("EC-01", "HIGH", "Admin-flag screen marker: full player updates every second", [
    P(f"To draw the destination marker with {c('ddraw.text')}, {c('UpdateScreenMarkerForOwner')} gives a "
      "non-admin carrier the admin flag, sends the text, then removes the flag again. It does this every "
      f"second, from {c('UpdateFlagOwner')}. Each toggle calls {c('SendNetworkUpdateImmediate()')}, which "
      "sends a full player update to every player in range, not just the carrier. With 60 players near "
      "the flag, that is at least 120 full player updates per second for the whole event, in the "
      "busiest spot on the map. It also keeps running after the carrier disconnects, because their "
      "sleeping body still holds the flag. And handing a client the admin flag every second is "
      "something some anti-cheat setups treat as suspicious."),
    code("""
// v2.0.1 L2463-2478 - runs every second for a non-admin carrier
SwitchMomentRules(_owner, true);    // SetPlayerFlag(IsAdmin, true) + SendNetworkUpdateImmediate()
_owner.SendConsoleCommand("ddraw.text", 1f, Color.white, _currentDestination, text);
SwitchMomentRules(_owner, false);   // SetPlayerFlag(IsAdmin, false) + SendNetworkUpdateImmediate()
"""),
    Paragraph("Fix", sFix),
    *bullets([
        "<b>Best:</b> turn the screen marker off by default. The destination map note already shows on "
        "the player's compass, and the zone sphere appears within 25 m.",
        "<b>If you keep it:</b> draw for 5 s and refresh every 4 s (about 75% fewer updates). Skip "
        "offline carriers, build the text once, and force a redraw when the destination changes.",
    ]),
    code("""
private float _nextScreenMarkerAt;
private string _screenText;                       // build once in StartEvent

private void UpdateScreenMarkerForOwner(bool force = false)
{
    if (_owner == null || !_owner.IsConnected || !_ins._config.ScreenMarkerConfig.Enabled)
        return;

    float now = Time.realtimeSinceStartup;
    if (!force && now < _nextScreenMarkerAt)
        return;
    _nextScreenMarkerAt = now + 4f;               // refresh every 4 s ...
    const float duration = 5f;                    // ... and draw for 5 s, so there is no gap

    if (_owner.IsAdmin)
    {
        _owner.SendConsoleCommand("ddraw.text", duration, Color.white, _currentDestination, _screenText);
        return;
    }

    SwitchMomentRules(_owner, true);
    _owner.SendConsoleCommand("ddraw.text", duration, Color.white, _currentDestination, _screenText);
    SwitchMomentRules(_owner, false);
}
// call UpdateScreenMarkerForOwner(true) on pickup and after UpdateDestination()
"""),
    P("Going further, the temporary admin-flag update could go only to the carrier's own connection "
      "instead of everyone in range. Check which per-connection snapshot method your server build "
      "exposes before relying on that."),
], where="L2456-2478, called every tick at L2660 (v1 L694-716, L852)"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-02", "MEDIUM", "Map markers resent to every player every second", [
    P(f"{c('EventCoroutine')} calls {c('UpdateMapMarker')} on every tick. That moves both markers, "
      "rebuilds the label (up to three lang lookups and a string.Format), and sends three network messages: "
      f"vending {c('SendNetworkUpdate')}, ring {c('SendUpdate')}, and ring {c('SendNetworkUpdate')}. Map "
      "markers go to every connected player, so with 300 online that's about 900 messages per second, "
      "even while the flag lies still on the ground. The label only changes once a minute, because it "
      "shows minutes until the final minute."),
    Paragraph("Fix: only send when something changed", sFix),
    code("""
private Vector3 _lastPos = new Vector3(float.MaxValue, 0f, 0f);
private string _lastName;

public void UpdateMapMarker(Vector3 position)
{
    string name = GetMarkerName();
    bool moved = (position - _lastPos).sqrMagnitude > 9f;      // moved more than 3 m
    if (!moved && name == _lastName)
        return;                                                // nothing new for clients

    _lastPos = position;
    _lastName = name;

    if (_vendingMarker.IsExists())
    {
        _vendingMarker.transform.position = position;
        _vendingMarker.markerShopName = name;
        _vendingMarker.SendNetworkUpdate();
    }

    if (moved && _radiusMarker.IsExists())
    {
        _radiusMarker.transform.position = position;
        _radiusMarker.SendNetworkUpdate();
        // SendUpdate() resends colour and radius. Try without it; restore it if the ring
        // stops following the flag.
    }
}
"""),
    P("A flag on the ground drops from 3 messages a second to 1 a minute. A carrier on the move still "
      "updates every second."),
], where="L2607-2608 -> L1542-1566 (v1 L806-807, L1193-1217)"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-03", "HIGH", "Carrier can log off with the flag", [
    P("Neither version handles a carrier who disconnects. The flag stays in the sleeping body's wear "
      "slot and the map marker keeps pointing at it. The event then only ends when it times out, "
      "unless someone gets to the sleeper. A carrier who logs off inside their own base stalls the "
      "event for everyone. Because of EC-01, the plugin also keeps toggling the admin flag on that "
      "sleeper every second."),
    Paragraph("Fix: drop the flag on disconnect", sFix),
    code("""
// add "OnPlayerDisconnected" to _subscribeMethods so it only runs during an event
private void OnPlayerDisconnected(BasePlayer player, string reason)
{
    if (_eventController != null && _eventController.IsEventPlayer(player.userID))
        _eventController.DropFlag(player);
}

// EventController
public void DropFlag(BasePlayer player)
{
    if (!IsLiveFlag())
        return;

    _item.Drop(player.transform.position + Vector3.up * 0.5f, Vector3.up);
    // On the next tick UpdateFlagOwner sees the dropped flag, cancels its despawn timer
    // and runs OnPlayerLostFlag (team and nearby alerts), exactly as for a death.
}
"""),
], where="no handler in either version"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-04", "MEDIUM", "Vehicle block only covers seats and the scrap heli", [
    P(f"{c('CanMountEntity')} blocks seats, and {c('OnEntityEnter')} only handles the scrap heli's rear "
      "platform. The carrier can still ride standing on a tugboat deck, a train wagon, a hot air "
      "balloon basket or the cargo ship. None of those need a seat."),
    Paragraph("Fix: check the carrier's parent in the 1-second tick", sFix),
    P("This checks one player once a second, so the cost is negligible. Sending the carrier back to "
      "where they last stood on foot also replaces the scrap-heli \"5 m behind\" teleport, which can "
      "drop them from height (EC-09)."),
    code("""
private Vector3 _lastFootPosition;

// in UpdateFlagOwner, after _owner = player;
BaseEntity parent = _owner.GetParentEntity();
if (parent == null)
{
    if (_owner.IsOnGround())
        _lastFootPosition = _owner.transform.position;      // remember a known-good spot
}
else if (parent is BaseVehicle || parent is HotAirBalloon || parent is CargoShip)
{
    NotifyManager.SendMessageToPlayer(_owner, "Flag_Vehicle_Blocked");
    BasePlayer carrier = _owner;
    Vector3 back = _lastFootPosition;
    _ins.NextTick(() => { if (carrier != null && !carrier.IsDead()) carrier.Teleport(back); });
}
"""),
], where="L1694-1742 (v1 L144-176)"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-05", "MEDIUM", "Destination marker skipped when the player has no marker list", [
    P(f"{c('CreateMapMarkerForPlayer')} returns early if {c('player.State.pointsOfInterest')} is null. "
      "As far as I know, Rust only creates that list the first time a player places a marker. If so, a "
      "player who has never placed one gets no destination marker at all. Test it with a fresh account."),
    Paragraph("Fix", sFix),
    code("""
if (player == null || player.State == null || !_ins._config.TargetMapMarkerConfig.Enabled)
    return;

if (player.State.pointsOfInterest == null)
    player.State.pointsOfInterest = Pool.Get<List<MapNote>>();
"""),
], where="L2490 (v1 L728)"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-06", "LOW", "Spawn-block check still does work for every entity it finds", [
    P(f"{c('IsBlockedPoint')} no longer allocates, which is the big win over v1.1.5. But it still "
      "collects every collider in range (up to 512) with no layer filter. For each one it walks up the "
      f"parents looking for a {c('TriggerSafeZone')}, and it calls {c('GetBuildingPrivilege()')} "
      "(itself a physics query) for every entity, trees included. This only runs during the spawn "
      "search, but the search does up to 10 attempts per frame."),
    Paragraph("Fix: one masked query, plus a direct safe-zone test", sFix),
    code("""
private const int StructureMask = (1 << (int)Layer.Construction) | (1 << (int)Layer.Deployed);

private static bool IsBlockedPoint(Vector3 position, float radius)
{
    if (radius <= 0f)
        return false;

    // Any building block or deployable in range: one query, no per-entity work.
    if (Physics.CheckSphere(position, radius, StructureMask, QueryTriggerInteraction.Ignore))
        return true;

    // A map has only a handful of safe zones: test their bounds directly.
    float r2 = radius * radius;
    foreach (TriggerSafeZone zone in TriggerSafeZone.allSafeZones)
    {
        Collider col = zone != null ? zone.triggerCollider : null;
        if (col != null && col.bounds.SqrDistance(position) <= r2)
            return true;
    }
    return false;
}
"""),
    P("This blocks spots near any player structure, not only ones covered by a tool cupboard, which is "
      "usually what you want for a flag spawn."),
], where="L3024-3058 (v1 L1349-1378)"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-07", "LOW", "Countdown runs slow when the server is under load", [
    P("Each tick waits at least one second, then subtracts exactly one. The wait always overshoots by "
      "part of a frame, so the event runs longer than configured. At 20 server FPS, a one-hour event "
      "runs about 90 seconds over, and the end-of-event warnings drift the same way."),
    Paragraph("Fix: count down against the clock", sFix),
    code("""
private float _endsAt;      // in StartEvent: _endsAt = Time.realtimeSinceStartup + EventDuration;

// in EventCoroutine, instead of _remainTime -= tick:
int remain = Mathf.Max(0, Mathf.CeilToInt(_endsAt - Time.realtimeSinceStartup));
foreach (int t in _ins._config.EndEventNotifyTimes)
    if (_remainTime > t && remain <= t)               // crossed a warning time since last tick
        NotifyManager.SendMessageToAll("Event_TimeLeft", _ins._config.ChatPrefix, t);
_remainTime = remain;
if (_remainTime <= 0) { _ins.StopEvent(); yield break; }
"""),
], where="L2595, L2610, L2625 (v1 L809, L824, L827)"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-08", "LOW", "Broadcasts are built once per player", [
    P(f"{c('SendMessageToAll')} builds the message separately for every online player: a new argument "
      "array, the time strings, a lang lookup, string.Format, and its own chat command string. With "
      "300 online that's 300 copies of the same work per broadcast. Broadcasts are rare, so this "
      "matters less than EC-01 and EC-02, but it's an easy win: build the message once per language."),
    Paragraph("Fix", sFix),
    code("""
public static void SendMessageToAll(string langKey, params object[] args)
{
    RedefinedMessageConfig redefined = GetRedefinedMessageConfig(langKey);
    if (redefined != null && !redefined.IsEnable)
        return;
    BaseMessageConfig target = redefined ?? (BaseMessageConfig)_ins._config.NotifyConfig;

    Dictionary<string, string> byLanguage = Pool.Get<Dictionary<string, string>>();
    try
    {
        foreach (BasePlayer player in BasePlayer.activePlayerList)
        {
            if (player == null) continue;
            string language = _ins.lang.GetLanguage(player.UserIDString);
            if (!byLanguage.TryGetValue(language, out string message))
                byLanguage[language] = message = Format(player, langKey, args);  // today's logic
            SendMessage(target, player, message);
        }
    }
    finally { Pool.FreeUnmanaged(ref byLanguage); }
}
"""),
], where="L3151-3189 (v1 L1383-1421)"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-09", "LOW", "Safe-zone and scrap-heli edge cases", [
    *bullets([
        f"Only safe zones with a {c('SphereCollider')} are handled. A box- or mesh-shaped zone can't "
        "eject the carrier (L1685-1687, L1736-1738).",
        "Picking up the flag on a scrap heli's platform returns before the safe-zone check runs "
        "(L1670-1677).",
        "The scrap-heli teleport puts the carrier 5 m behind and 1 m above the heli with no ground "
        "check. If the heli is flying, the carrier falls (L1673, L1729).",
    ]),
    Paragraph("Fix", sFix),
    code("""
// Works for any collider shape; exact for spheres.
Bounds b = zoneCollider.bounds;
Vector3 dir = player.transform.position - b.center;
dir.y = 0f;
dir = dir.sqrMagnitude < 0.001f ? Vector3.forward : dir.normalized;
float reach = zoneCollider is SphereCollider
    ? b.extents.x + 2f
    : new Vector2(b.extents.x, b.extents.z).magnitude + 2f;
Vector3 exit = PositionDefiner.GetGroundPosition(b.center + dir * reach) + Vector3.up * 0.25f;
"""),
    P("Run the safe-zone check before the scrap-heli branch returns. Send a carrier who is on a heli "
      "to their last on-foot position (EC-04) instead of 5 m behind it."),
], where="L1653-1742, L2012-2032"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-10", "LOW", "Nearby alerts capped at 64 players", [
    P(f"The nearby pickup and drop alerts still borrow {c('AIBrainSenses.playerQueryResults')}, a "
      "64-slot buffer that belongs to the NPC AI. v2.0.1 fixed the stale-entry bug, but in a busy event "
      "more than 64 players can be within 100 m, and nobody past the 64th gets an alert."),
    Paragraph("Fix", sFix),
    code("""
private static readonly BasePlayer[] NearbyPlayers = new BasePlayer[256];   // the plugin's own buffer
int count = BaseEntity.Query.Server.GetPlayersInSphereFast(_flagPosition, radius, NearbyPlayers);
"""),
], where="L2679, L2743"))
story.append(Spacer(1, 4 * mm))

story.append(card("EC-11", "LOW", "Small leftovers", [
    *bullets([
        f"{c('Flag_Picked_Up')} fills {c('{0}')} with the chat prefix, so the carrier sees \"[CTF] | "
        "Picked up the flag\" instead of their name. Pass the player's name, or change the lang text "
        "(L1293, L2769).",
        f"{c('/ctffinish')} awards whoever held the flag at the last tick. If it was dropped within that "
        f"second, the wrong player can win. Call {c('UpdateFlagOwner()')} first (L2777-2785).",
        f"{c('OnPlayerCommand')} only sees chat commands. With {c('CanTeleport')} in place this matters "
        "less, but plugins that teleport players directly (some warp and menu plugins) still get "
        "through (L1771-1783).",
        f"{c('CanTeleport')} sends its own message and returns an empty string. Teleport plugins that "
        "print the returned string will add a blank line. Return the message text instead and drop "
        "the extra send (L1760-1763).",
    ]),
]))

# ═══════════════════════════════════════════════════════════════════════════════
#  ROADMAP + VERIFY + REFERENCES
# ═══════════════════════════════════════════════════════════════════════════════
story.append(PageBreak())
story.append(Paragraph("Priority fix roadmap (for v2.0.1)", sSect))
story.append(hr())
roadmap = [
    ["#", "ID", "Action", "Effort", "Impact"],
    ["1", "R-01", "Pass a fresh dictionary to OnEventEnd", "2 min", "Interop safety"],
    ["2", "R-02", "Restore the current OnMapMarkerRemove signature", "5 min", "Regression fix"],
    ["3", "EC-05", "Create pointsOfInterest when it's null", "5 min", "Markers for every player"],
    ["4", "EC-02", "Only resend map markers when they moved or the label changed", "30 min", "Up to 99% fewer broadcasts"],
    ["5", "EC-01", "Screen marker off by default, or 4 s refresh + skip offline carriers", "30 min", "75-100% fewer player updates"],
    ["6", "EC-03", "Drop the flag when the carrier disconnects", "30 min", "Closes the log-off stall"],
    ["7", "EC-04", "Parent check in the tick; send riders back to their last on-foot spot", "1 hr", "Closes vehicle rides"],
    ["8", "R-03", "Use EnableSaving(false) on the dropped flag", "5 min", "Crash safety"],
    ["9", "EC-07", "Count down against the real clock", "30 min", "Correct event length"],
    ["10", "EC-06", "One masked query + direct safe-zone test in IsBlockedPoint", "1 hr", "Cheaper spawn search"],
    ["11", "EC-08", "Build broadcasts once per language", "1 hr", "Fewer allocations"],
    ["12", "EC-09", "Any-shape safe zones; safe-zone check before the heli branch", "1 hr", "Closes edge exploits"],
    ["13", "R-04", "Tag the flag; sweep only tagged items and marked players", "1-2 hrs", "No collateral deletes"],
    ["14", "EC-10, EC-11, R-05, R-06", "Own alert buffer; text, /ctffinish and CanTeleport fixes; smaller spawn map; waypoint terrain check", "1-2 hrs", "Cleanup"],
]
story.append(grid(roadmap, [8 * mm, 24 * mm, None, 17 * mm, 38 * mm], valign="MIDDLE"))
story.append(Spacer(1, 5 * mm))

story.append(Paragraph("Check these on a test server", sSect))
story.append(hr())
story.append(P("I couldn't confirm these without the server's game files. Each one decides whether a "
               "finding applies to your build."))
verify = [
    ["Finding", "What to check"],
    ["EC-05", "Does a fresh account that has never placed a map marker get the CTF destination marker?"],
    ["R-03", f"With the flag on the ground, run a save and restart: does the flag come back? (Use {c('EnableSaving(false)')} either way.)"],
    ["R-01", "Does EventManager read the OnEventEnd dictionary after the hook returns (timer, NextTick, stored list)?"],
    ["EC-02", f"Does the ring marker follow the flag without {c('SendUpdate()')}?"],
    ["Teleports", f"Does your teleport plugin call {c('CanTeleport')}? NTeleportation does. Which plugin calls {c('ShouldInterrupt')}? If none, remove it."],
    ["R-06", "Can waypoints now land on top of rocks or other world objects?"],
    ["EC-06", f"Does {c('TriggerSafeZone.allSafeZones')} exist on your build? It's the static list of safe zones the fix loops over."],
    ["EC-01", "Do your players see the CTF map note on their compass? If so, the screen marker can go."],
]
story.append(grid(verify, [24 * mm, None]))
story.append(Spacer(1, 5 * mm))

story.append(Paragraph("References", sSect))
story.append(hr())
story.extend(bullets([
    "Oxide deprecation of OnMapMarkerRemove (old form stopped working 31 December 2023; replacement "
    f"{c('OnMapMarkerRemove(BasePlayer player, List<MapNote> mapMarker, int index)')}): "
    '<link href="https://umod.org/community/rust/51596-rustcore-v206096-is-using-deprecated-hook-onmapmarkerremove" '
    'color="#58A6FF">umod.org/community/rust/51596</link>',
    "ItemContainer.CanAcceptItem now returns ItemContainer.CanAcceptResult (August 2025), which both "
    "versions already use: "
    '<link href="https://umod.org/community/npc-drop-gun/56685-npc-drop-gun-august-2025-rust-compatibility-update" '
    'color="#58A6FF">umod.org/community/npc-drop-gun/56685</link>',
    "Sampling figure (15.9% off-map) from a 2-million-point simulation of v1.1.5's "
    f"{c('GetRandomMapPoint')}. Spawn map sizes computed from v2.0.1's {c('BuildSpawnMap')}.",
]))


# ── Page background + footer ─────────────────────────────────────────────────
def add_page_bg(canvas, _doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        PAGE_W / 2, 10 * mm,
        f"PulseRust High-Performance Analysis  •  EventCtf v1.1.5 vs v2.0.1  •  "
        f"{datetime.now().strftime('%d %b %Y')}  •  Page {canvas.getPageNumber()}")
    canvas.restoreState()


doc.build(story, onFirstPage=add_page_bg, onLaterPages=add_page_bg)
print(f"PDF written to {OUTPUT}")
