#!/usr/bin/env python3
"""
PulseRust High-Pop Server Tuning Guide
Convars, Facepunch's 2026 engine changes and plugin performance.

Every convar name/default in this report was checked against decompiled server
source, the April 2026 server command list, a 2025-26 convar dump and Facepunch's
2026 devblogs/commit log. See the Sources appendix.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak, CondPageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

OUTPUT = "/home/user/ClaudeAI/PulseRust_HighPop_ConvarGuide.pdf"
RESEARCH_DATE = "5 November 2026"

# ── Colour palette (matches ClanTree / UltimateLeaderboard reports) ──────────
BG        = colors.HexColor("#0D1117")
PANEL     = colors.HexColor("#161B22")
PANEL2    = colors.HexColor("#1C2128")
BORDER    = colors.HexColor("#30363D")
ACCENT    = colors.HexColor("#58A6FF")
RED       = colors.HexColor("#F85149")
ORANGE    = colors.HexColor("#D29922")
YELLOW    = colors.HexColor("#E3B341")
GREEN     = colors.HexColor("#3FB950")
PURPLE    = colors.HexColor("#BC8CFF")
WHITE     = colors.HexColor("#E6EDF3")
MUTED     = colors.HexColor("#8B949E")
CODE_TEXT = colors.HexColor("#79C0FF")

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 16 * mm
T_MARGIN = 16 * mm
B_MARGIN = 18 * mm
CONTENT_W = PAGE_W - L_MARGIN - R_MARGIN

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=L_MARGIN, rightMargin=R_MARGIN,
    topMargin=T_MARGIN, bottomMargin=B_MARGIN,
    title="PulseRust High-Pop Server Tuning Guide",
    author="PulseRust High-Performance Analysis",
    subject="Rust server convars, Facepunch 2026 engine changes and plugin performance",
)

# ── Styles ────────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()

def S(name, **kw):
    parent = kw.pop("parent", "Normal")
    return ParagraphStyle(name, parent=ss[parent], **kw)

sTitle    = S("sTitle",    fontSize=26, leading=31, textColor=WHITE, alignment=TA_CENTER,
              fontName="Helvetica-Bold", spaceAfter=4)
sSubtitle = S("sSubtitle", fontSize=12, leading=16, textColor=ACCENT, alignment=TA_CENTER,
              fontName="Helvetica", spaceAfter=4)
sMeta     = S("sMeta",     fontSize=8.5, leading=12, textColor=MUTED, alignment=TA_CENTER,
              fontName="Helvetica", spaceAfter=10)
sH1       = S("sH1",       fontSize=15, leading=19, textColor=ACCENT, fontName="Helvetica-Bold",
              spaceBefore=6, spaceAfter=4)
sH2       = S("sH2",       fontSize=11.5, leading=15, textColor=WHITE, fontName="Helvetica-Bold",
              spaceBefore=8, spaceAfter=3)
sBody     = S("sBody",     fontSize=9, leading=13.5, textColor=WHITE, fontName="Helvetica", spaceAfter=4)
sBodyJ    = S("sBodyJ",    parent="Normal", fontSize=9, leading=13.5, textColor=WHITE,
              fontName="Helvetica", spaceAfter=4, alignment=TA_JUSTIFY)
sBullet   = S("sBullet",   fontSize=9, leading=13, textColor=WHITE, fontName="Helvetica",
              leftIndent=12, firstLineIndent=-8, spaceAfter=2.5)
sNote     = S("sNote",     fontSize=8, leading=11.5, textColor=MUTED, fontName="Helvetica-Oblique",
              spaceAfter=4)
sCode     = S("sCode",     fontSize=7.4, leading=10.2, textColor=CODE_TEXT, backColor=PANEL2,
              fontName="Courier", leftIndent=6, rightIndent=6, spaceBefore=2, spaceAfter=6,
              borderPadding=(5, 6, 5, 6))
sTH       = S("sTH",       fontSize=7.8, leading=10, textColor=WHITE, fontName="Helvetica-Bold")
sTD       = S("sTD",       fontSize=7.6, leading=10, textColor=WHITE, fontName="Helvetica")
sTDm      = S("sTDm",      fontSize=7.6, leading=10, textColor=MUTED, fontName="Helvetica")
sSrc      = S("sSrc",      fontSize=7.4, leading=10, textColor=WHITE, fontName="Helvetica",
              leftIndent=12, firstLineIndent=-12, spaceAfter=2)


def hexc(c):
    return "#" + c.hexval()[2:].upper()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def C(s, color=CODE_TEXT):
    """Inline monospace (convar / command names)."""
    return f'<font name="Courier" color="{hexc(color)}">{esc(s)}</font>'


def B(s):
    return f"<b>{s}</b>"


def col(s, c):
    return f'<font color="{hexc(c)}">{s}</font>'


def P(text, style=sBody):
    return Paragraph(text, style)


def bullets(items, style=sBullet):
    return [Paragraph(f"•&nbsp;&nbsp;{t}", style) for t in items]


def hr(c=BORDER, t=0.6):
    return HRFlowable(width="100%", thickness=t, color=c, spaceBefore=4, spaceAfter=6)


def sp(h=4):
    return Spacer(1, h * mm / 4)


def code_block(text):
    return Paragraph("<br/>".join(esc(text).replace(" ", "&nbsp;").split("\n")), sCode)


def grid(rows, widths, head=True, font_style=sTD, zebra=True, align_top=True):
    """Table whose string cells are wrapped in Paragraphs."""
    out = []
    for r_i, row in enumerate(rows):
        cells = []
        for c in row:
            if isinstance(c, str):
                cells.append(Paragraph(c, sTH if (head and r_i == 0) else font_style))
            else:
                cells.append(c)
        out.append(cells)
    t = Table(out, colWidths=widths, repeatRows=1 if head else 0)
    st = [
        ("GRID",          (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "TOP" if align_top else "MIDDLE"),
    ]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), BORDER))
    if zebra:
        st.append(("ROWBACKGROUNDS", (0, 1 if head else 0), (-1, -1), [PANEL, PANEL2]))
    t.setStyle(TableStyle(st))
    return t


def card_header(cid, verdict, title, c):
    """Coloured header bar for a finding/verdict block (content follows as normal flowables)."""
    row = [[
        Paragraph(f'<font color="{hexc(c)}" size="9"><b>{cid}</b></font>', sBody),
        Paragraph(f'<font color="{hexc(c)}" size="8.5"><b>{verdict}</b></font>', sBody),
        Paragraph(f'<font color="#E6EDF3" size="9.5"><b>{title}</b></font>', sBody),
    ]]
    t = Table(row, colWidths=[17 * mm, 40 * mm, None])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), PANEL),
        ("BOX",           (0, 0), (-1, -1), 0.9, c),
        ("LINEBEFORE",    (0, 0), (0, -1), 3, c),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def callout(title, body_flowables, c=ACCENT, bg=PANEL):
    inner = [Paragraph(f'<font color="{hexc(c)}"><b>{title}</b></font>', sBody)] + body_flowables
    t = Table([[inner]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 0.8, c),
        ("LEFTPADDING",   (0, 0), (-1, -1), 9),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 9),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def section(num, title):
    return [CondPageBreak(40 * mm), P(f"{num}. {title}", sH1), hr(ACCENT, 0.8)]


def H2(title, need_mm=35):
    """Sub-heading that never strands at the bottom of a page."""
    return [CondPageBreak(need_mm * mm), P(title, sH2)]


def link(url, text=None):
    return f'<link href="{url}" color="#58A6FF">{esc(text or url)}</link>'


# ═══════════════════════════════════════════════════════════════════════════════
story = []

# ── Cover ─────────────────────────────────────────────────────────────────────
story += [Spacer(1, 16 * mm)]
story.append(P("High-Pop Server Tuning Guide", sTitle))
story.append(P("Convars, Facepunch's 2026 engine changes and plugin performance for PulseRust", sSubtitle))
story.append(P(f"Researched {RESEARCH_DATE} (force-wipe day)  •  Covers Rust builds through the October 2026 "
               "Livestock update plus Facepunch's commit log up to 4 November", sMeta))
story.append(hr(ACCENT, 1))

story.append(callout("How this was researched", [
    P("Most Rust \"performance convar\" lists online come from hosting-company blogs. Many repeat settings that "
      "no longer exist, never applied to servers, or do something different from what is claimed. Every "
      "recommendation here was checked against the server's own code or Facepunch's own words:", sBodyJ),
    *bullets([
        "Decompiled Rust server source (late-2023 and August-2024 builds) to see what each convar actually controls.",
        "The April 2026 server command list (1,651 commands generated from the game's own ConsoleGen table) and a "
        "2025-26 convar value dump, for current names and defaults.",
        "Facepunch devblogs, changelists and the main-branch commit log for April to November 2026. "
        "rust.facepunch.com could not be reached from the research environment, so these were read through "
        "search extracts and secondary coverage. Items marked (reported) are not confirmed against the primary text.",
        "Carbon and Oxide framework source for the profiling tools, and a public snapshot of 1,561 uMod plugins.",
    ]),
    P(f"Values marked {col('<b>TEST</b>', YELLOW)} change behaviour in ways that need a staging check first.", sBody),
]))
story += [sp(6)]

story.append(P("Executive Summary", sH1))
story.append(hr(ACCENT, 0.8))
story.append(P(
    "On a 200+ player Rust server in late 2026, four things move server FPS: "
    f"{B('(1) entity count')}, {B('(2) plugin main-thread time and garbage')}, "
    f"{B('(3) Facepunch’s new multithreaded player-update “Jobs” modes')} and {B('(4) the CPU')}. "
    "Of PulseRust's existing changes, reduced animal populations help a little. Reduced tick rates do "
    "essentially nothing, and lowering player tick rates below 16 is silently undone by the game. Reduced "
    "decay can actively hurt if it means bases decay more slowly.", sBodyJ))
story.append(P(
    "The biggest wins available right now cost nothing. Let Jobs 4 run: Facepunch's commit log shows it "
    "becoming the default with today's patch. Stop starving the process of CPU cores, keep decay at full "
    "speed, and remove the plugin disk-I/O stalls already identified in the Kits, PulseDailyGems, "
    "UltimateLeaderboard and ClanTree audits.", sBodyJ))
story += [sp(3)]

story += H2("Top 12 actions, in priority order")
top = [
    ["#", "Action", "Why (evidence)", "Effort / risk"],
    ["1", f"After today's patch, confirm {C('server.useplayerupdatejobs')} reads {B('4')}. Remove any 0/1/2/3 overrides.",
     "Jobs 4 parallelises player updates and entity snapshot serialisation. In Facepunch's synthetic test, "
     "10,000 entities went from 64.4 ms to 10.6 ms. Merged as the default on 3 Nov.",
     "5 min / low"],
    ["2", "Give the Rust process a full CCD of fast cores. Never pin it to 1-2 cores.",
     "Jobs 3/4, navigation and IK now run on worker threads. A 13 Oct Facepunch commit makes job "
     "threads auto-size to the CPU affinity mask.", "15 min / low"],
    ["3", f"Keep {C('decay.scale 1')} and upkeep on. Remove abandoned bases with a cleanup plugin.",
     "Entity count drives late-wipe cost: saves, snapshots, memory. Decay CPU is fixed at ~10 entities "
     "per frame whatever the settings.", "30 min / low-med"],
    ["4", f"Set {C('fps.limit')} back to 240, or at least 100 on a shared host.",
     "Many systems run on per-frame ms budgets, so fewer frames means less AI, turret, IO and decay "
     "work per second.", "1 min / low"],
    ["5", f"Set {C('server.tickrate')} back to the default 10.",
     "It only paces RCON, Rust+, Nexus, auth time-outs and the OnTick plugin hook. It is not the "
     "simulation rate.", "1 min / none"],
    ["6", "Keep animals at ~50% of default. Don't cut further.",
     "Facepunch caps animal AI per frame: more animals means slower reactions, not lower FPS. Animals "
     "are a tiny share of entities.", "done / none"],
    ["7", "Fix critical plugin findings K-01, DG-01, UL-01..03 and CT-01..03. Stagger OnServerSave writes.",
     "Plugin disk I/O lands in the same frames as Rust's own single-frame save write.", "hours / low"],
    ["8", f"Profile every wipe: Carbon {C('c.profile')} and {C('c.hookinfo')}, plus Facepunch "
          f"{C('profile.perfsnapshot')} at peak.",
     "Only measurement shows which hook or system owns the slow frames.", "30 min per wipe / none"],
    ["9", f"Delete dead convars ({C('gc.buffer')}, {C('physics.steps')}, legacy entries; see Section 6).",
     "They do nothing on a 2026 server and hide the real settings.", "10 min / none"],
    ["10", "Shorten lifetimes of abandoned vehicles and dropped items modestly.",
     "Bikes and snowmobiles last 24 h outside by default, and loose items are physics bodies.",
     "10 min / gameplay"],
    ["11", f"Keep {C('server.saveinterval 600')}. Move to 900 only if the save log shows write+disk over ~0.5 s.",
     "Rust writes the whole save buffer in one frame, then writes to disk synchronously.", "5 min / low"],
    ["12", f"On staging, trial {C('-useNewNavmesh')} and the navmesh carve options.",
     "Background build, disk cache and multithreaded pathing. NPC plugins must be checked against it.",
     "1-2 h / medium"],
]
story.append(grid(top, [7 * mm, 62 * mm, 82 * mm, 27 * mm]))

# ═══ 1. Frame anatomy ═════════════════════════════════════════════════════════
story += section(1, "Where a Rust server's frame actually goes")
story.append(P(
    f"{C('ServerMgr.Update()')} runs once per server frame on the main thread. In the August 2024 server source "
    "it calls, in order: EAC and platform updates, network receive, then the building manager (stability "
    "queue, surroundings queue, skin "
    "queue and the decay round-robin), then every player's server update. After that come the budgeted "
    "turret, gun-trap and dropped-item queues, the connection queue, the electricity (IO) queue and the AI "
    "think queues. Human and animal queues alternate frames while " + C("ai.spliceupdates") + " is on. Pets, "
    "growables, life-story stats, junk-pile water, industrial transfers and AntiHack run last. Saves, "
    "population refills and spawns run as coroutines that yield between frames.", sBodyJ))
story.append(P("Four consequences shape every recommendation in this guide:", sBody))
story += bullets([
    f"{B('Most systems are capped by a per-frame millisecond budget.')} When the server is busy, they don't take "
    "more frame time; they fall behind instead. Turrets acquire targets later, electricity lags and animals "
    "react slower. Raising a budget never raises FPS. Lowering one protects FPS at that system's expense.",
    f"{B('Server FPS sets the throughput of those budgets.')} A server held at 30 FPS does half the AI, turret "
    "and IO work per second of one at 60 FPS. Artificially low " + C("fps.limit") + " values hurt for this reason.",
    f"{B('Entity count is the cost that grows all wipe.')} Every entity is serialised on every save, snapshotted "
    "to each player entering its network group and held in memory. Physical ones are also simulated.",
    f"{B('Plugin hooks run inline on the main thread')} inside these same frames, with no budget of their own.",
])
story += H2("Per-frame budgets in the current build")
budgets = [
    ["System", "Budget convar", "2026 value", "If you lower it"],
    ["Animal AI think", C("aithinkmanager.animalframebudgetms"), "2 ms", "Animals react slower"],
    ["NPC / human AI think", C("aithinkmanager.framebudgetms"), "2 ms", "Scientists react slower"],
    ["HTN agents (animal / player / junkpile)", C("aimanager.ai_htn_*_tick_budget"), "4 ms each",
     "Agents tick less often"],
    ["Async pathfinding", C("aimanager.pathfindingiterationsperframe"), "100 nodes",
     "Paths resolve slower (Facepunch tuning range 50-500)"],
    ["Auto-turret target scan", C("autoturret.scan_budget_ms"), "0.5 ms", "Turrets acquire later"],
    ["Shotgun traps", C("guntrap.gun_trap_budget_ms"), "0.5 ms", "Traps react later"],
    ["Electricity (high / low priority)", C("ioentity.framebudgetelectrichighpriorityms") + " / " +
     C("...lowpriorityms"), "1 / 0.5 ms", "Circuits update later"],
    ["Fluid / kinetic / generic / industrial IO", C("ioentity.framebudget{fluid,kinetic,generic,industrial}ms"),
     "0.25 / 1 / 1 / 0.25 ms", "Pumps and conveyors lag"],
    ["Industrial transfers", C("server.industrialframebudgetms"), "0.5 ms", "Conveyors move less per second"],
    ["Planters / growables", C("growableentity.framebudgetms"), "0.25 ms", "Plants update later"],
    ["Ovens / food spoiling", C("server.ovencookbudgetms") + " / " + C("server.foodspoilingbudgetms"),
     "0.25 / 0.05 ms", "Smelting / spoil ticks lag"],
    ["Save-cache warm-up", C("server.saveframebudget"), "5 ms", "Saves take longer wall-time"],
    ["Stability checks", C("stability.stabilityqueue") + " / " + C("stability.surroundingsqueue"),
     "9 / 3 ms", "Collapses resolve later"],
    ["Building + world decay", "hard-coded", "5 + 5 entities per frame", "n/a (see Section 2.3)"],
]
story.append(grid(budgets, [44 * mm, 66 * mm, 26 * mm, 42 * mm]))
story.append(P("Values are from the 2025-26 convar dump and April 2026 help text; the frame order and decay "
               "constants are from the August 2024 server source.", sNote))

# ═══ 2. Review of existing changes ════════════════════════════════════════════
story += section(2, "Review of what PulseRust has already changed")
story.append(P("You mentioned three changes: reduced animal populations, reduced tick rates and reduced decay "
               "rates. Here is what each one actually does in the server code.", sBodyJ))

# 2.1 Animals
story.append(sp(2))
story.append(card_header("2.1", "KEEP - SMALL GAIN", "Reduced animal populations", GREEN))
story.append(sp(2))
story.append(P(
    f"{B('What the code does.')} Each {C('<animal>.population')} convar is a density in animals per km². "
    "The population's target count is map area × density × a population scale. That scale is lerped between "
    f"{C('spawn.min_density')} and {C('spawn.max_density')} by online players ÷ {C('server.maxplayers')}, "
    "so a near-full high-pop server runs at the max value. Populations not flagged to scale with large maps "
    "cap the area at 16 km² (a 4000 map). Refills run every "
    f"{C('spawn.tick_populations')} seconds, one population per frame, with a per-pass spawn cap.", sBodyJ))
story.append(P(
    f"{B('Why the gain is small.')} Facepunch, October 2026 devblog: only a subset of NPCs is processed each "
    "frame, up to a hard-coded time cap, “so when we increase the population, the server doesn't directly lose "
    "FPS, instead NPCs just become slower to react.” Animals far from players also go dormant "
    f"({C('aimanager.ai_dormant')} = true, wake range {C('aimanager.ai_to_player_distance_wakeup_range')} = 160 m). "
    "Animals number in the hundreds; a mid-wipe high-pop map holds hundreds of thousands of player entities.",
    sBodyJ))
story.append(P(
    f"{B('What it still buys.')} Fewer entities to save and network, fewer awake brains around busy areas, and "
    "more AI budget per remaining animal. If your values are already near the suggestions below, cutting "
    f"further gains nothing measurable. After a restart, run {C('spawn.report')} to confirm live counts "
    "match the targets.", sBodyJ))
animals = [
    ["Convar", "2026 default", "Suggested high-pop", "Convar", "2026 default", "Suggested high-pop"],
    [C("bear.population"), "2", "1", C("ridablehorse.population"), "2", "1"],
    [C("polarbear.population"), "1", "0.5", C("tiger.population"), "0.5", "0.25"],
    [C("wolf.population"), "2", "1", C("panther.population"), "0.5", "0.25"],
    [C("boar.population"), "5", "2.5", C("crocodile.population"), "1", "0.5"],
    [C("stag.population"), "3", "1.5", C("snakehazard.population"), "5", "2.5 (optional)"],
    [C("chicken.population"), "3", "1.5", C("zombie.population"), "0", "0"],
]
story.append(grid(animals, [36 * mm, 20 * mm, 30 * mm, 42 * mm, 20 * mm, 30 * mm]))
story.append(P(f"Event populations ({C('halloween.*population')}, {C('halloweendungeon.population')}, "
               f"{C('xmasdungeon.xmaspopulation')}) default to 0 outside events; leave them alone.", sNote))

# 2.2 Tick rates
story.append(sp(3))
story.append(card_header("2.2", "REVERT tickrate", "Reduced tick rates", ORANGE))
story.append(sp(2))
story.append(P(
    f"{B(C('server.tickrate') + ' is not the simulation tick.')} In both the 2023 and 2024 server source it sets "
    f"one thing: how often {C('ServerMgr.DoTick()')} runs. DoTick processes RCON, the Rust+ companion server, "
    "Nexus and authentication time-out kicks. Carbon and Oxide also fire their " + C("OnTick") + " hook from "
    "it. Facepunch's default is 10.", sBodyJ))
story.append(P(
    "Hosting guides recommending 30, 60 or 128 are repeating the 2016 default, which was 30. Raising it "
    "multiplies RCON polling and every plugin's OnTick cost. Lowering it below 10 saves almost nothing and "
    "makes RCON and Rust+ less responsive.", sBodyJ))
story.append(P(
    f"Player tick rates are separate replicated convars: {C('player.tickrate_sv')} (default 16) and "
    f"{C('player.tickrate_cl')} (default 32). Both are clamped in code to 16-128, so anything below 16 "
    "is silently raised to 16. Lowering " + C("tickrate_cl") + " cuts inbound tick packets but coarsens "
    "movement and hit validation, and Jobs 3/4 already moved much of that work off the main thread. Use "
    "Facepunch's values.", sBodyJ))
ticks = [
    ["Convar", "Default", "What it really controls", "Recommendation"],
    [C("server.tickrate"), "10", "ServerMgr.DoTick: RCON, Rust+, Nexus, auth time-outs, OnTick plugin hook",
     B("10")],
    [C("player.tickrate_sv"), "16", "Per-player server update rate (ConnectedPlayerUpdate); clamp 16-128",
     "16 (can't go lower)"],
    [C("player.tickrate_cl"), "32", "Client tick send rate (replicated to clients); clamp 16-128", "32"],
    [C("ai.tickrate"), "5", "AI think ticks per second; already under frame budgets", "5"],
    [C("fps.limit"), "240", "Server frame cap; throughput of every per-frame budget scales with real FPS",
     "240; at least 100 if sharing a host"],
    [C("spawn.tick_populations"), "60 s", "Respawn pass interval; time-sliced, one population per frame",
     "Gameplay lever, not perf"],
    [C("server.planttick") + ", " + C("server.metabolismtick") + ", " + C("server.modifiertickrate"),
     "60 / 1 / 1", "Gameplay timers (growth, hunger, buffs)", "Not perf levers"],
    [C("decay.tick"), "600 s", "Minimum gap between decay evaluations per entity", "Not a CPU lever (2.3)"],
]
story.append(grid(ticks, [44 * mm, 15 * mm, 79 * mm, 40 * mm]))

# 2.3 Decay
story.append(sp(3))
story.append(card_header("2.3", "CHECK - MAY HURT", "Reduced decay rates", RED))
story.append(sp(2))
story.append(P(
    f"{B('What the code does.')} {C('ServerBuildingManager.Cycle()')} runs every frame. It evaluates "
    f"{B('5 building-decay entities and 5 world-decay entities')}, round-robin. Each {C('DecayTick()')} returns "
    f"immediately unless {C('decay.tick')} seconds (default 600) have passed since that entity's last evaluation. "
    f"The damage applied is proportional to the real elapsed time × {C('decay.scale')}.", sBodyJ))
story += bullets([
    "Decay costs a small, fixed amount of CPU per frame whatever you set. Raising " + C("decay.tick") +
    " saves nothing measurable, and lowering it doesn't make bases decay faster.",
    "On a big map the round-robin is the real clock. 300,000 building-decay entities at 50 FPS take about "
    "20 minutes per full pass (300,000 ÷ 5 ÷ 50 = 1,200 s). Total decay is unaffected because damage uses elapsed time.",
    f"{C('decay.scale')} below 1, longer {C('decay.duration_*')} values or added {C('decay.delay_*')} all let "
    "abandoned bases live longer. Every surviving block is serialised on every save and snapshotted to every "
    "player who walks past. This is the opposite of a performance setting.",
])
story.append(P(
    f"{B('Recommendation.')} {C('decay.scale 1')}, {C('decay.upkeep true')} and default durations. Protect active "
    "players through upkeep (TC), not by slowing decay globally. Remove abandoned structures actively "
    f"(Section 7.5). If you want bases to fall faster, {C('decay.scale')} 1.5-2 is the lever, but that is a "
    "gameplay decision.", sBodyJ))
story.append(P("Decay round-robin constants are from the August 2024 source. Facepunch may have retuned them "
               "since, but the per-entity elapsed-time model has been stable for years.", sNote))

# ═══ 3. Facepunch 2026 ════════════════════════════════════════════════════════
story += section(3, "Facepunch's 2026 engine work comes first")
story.append(P(
    "In 2026 Facepunch has been moving the per-player and per-entity main-thread work onto worker threads. "
    "The Spring Clean devblog shows Facepunch profiling a 360-player server and finding AntiHack and network "
    "streaming running serially inside a ~20 ms section. Each monthly patch since has attacked that section. "
    "For a high-pop server, staying on the newest Jobs level is the single largest performance change "
    "available.", sBodyJ))
timeline = [
    ["When", "Update", "Server-relevant change", "Source"],
    ["2 Apr", "Spring Clean", f"{C('server.useplayerupdatejobs')} 2 becomes default. Level 3 added as "
     "experimental: UniTask instead of C# Tasks (fewer allocations), more AntiHack in Burst jobs, player "
     "network streaming parallelised. ~600 MB less runtime memory and ~2.7 GB less disk (reported).",
     "Devblog + patch notes"],
    ["7 May", "Upgrade Hard, Raid Harder", "Entity saving made thread-safe (no Unity API calls), "
     "the prerequisite for Jobs 4. Memory and network optimisations (reported).", "Devblog (secondary)"],
    ["4 Jun", "Built Different", "Unity 6. ~20 server allocation sources removed or amortised; improved hit "
     f"validation. New Facepunch navmesh behind {C('-useNewNavmesh')} (off by default): built in the background "
     "after start, then loaded from disk on restart.", "Devblog / changelist"],
    ["2 Jul", "Common Ground", "Jobs 2 removed, Jobs 3 is the default. Jobs 4 added as experimental.",
     "Changelist"],
    ["6 Aug", "Power Trip", "Jobs 4 = parallel “entity saving”: snapshots grouped into batches "
     "(ParallelNetworkQueueBatchSize, default 256), each serialised as its own thread-pool task. Synthetic "
     "results: 1,000 entities 6.6 -> 3.6 ms; 10,000 entities 64.4 -> 10.6 ms.", "Devblog"],
    ["3 Sep", "Breach and Clear", "Jobs 4 parallel-save improvements; SyncVar buffer leak during parallel "
     "saves fixed; pool leak fixed; server mission memory reduced.", "Changelog (secondary)"],
    ["1 Oct", "Livestock", "New navigation system multithreaded, “at least doubling its performance”. IK "
     "multithreaded (~1 ms/frame saved at 100 players). Unused map data freed (~175 MB on a 4500 map, "
     "reported). New cows and sheep add entities.", "Devblog"],
    ["13 Oct", "commit #167854", "“Auto adjust jobs thread count when changing CPU affinity.”", "Commit log"],
    ["22-23 Oct", "commits", "RustRelay TCP packet overhead reduced; websocket-sharp replaced with Fleck "
     "(lower websocket/RCON bandwidth overhead).", "Commit log"],
    ["3 Nov", "commit #170103", f"“make UsePlayerUpdateJobs default to 4” - expected live with today's "
     "5 Nov update.", "Commit log"],
]
story.append(grid(timeline, [16 * mm, 29 * mm, 103 * mm, 30 * mm]))
story += H2("What to do with this")
story += bullets([
    f"After today's patch, type {C('server.useplayerupdatejobs')} in the console. Expect {B('4')}. If it reads 3, "
    "Jobs 4 didn't ship in this build: test 4 on staging for a day before production.",
    f"Delete any {C('server.useplayerupdatejobs')} line from server.cfg and serverauto.cfg so you follow "
    f"Facepunch's default as it moves. Leave {C('server.emergencydisableplayerjobs')} at true: it runs "
    "extra validation and falls back to vanilla processing instead of crashing.",
    "Don't restrict the process to one or two cores. If you run several instances on one box, give each "
    "its own CCD or core group of at least 8 cores and let the auto-sized job threads use them.",
    "If a plugin misbehaves under Jobs 4, report it to the author (and Facepunch if vanilla). Don't drop the "
    "whole server back to an older mode.",
    f"{C('-useNewNavmesh')} is a launch argument, not a convar. Its benefits are a background build, a disk cache "
    "(fast restarts) and multithreaded pathing. Test it on staging with your NPC and event plugins first, "
    "because anything that samples Unity's NavMesh directly may behave differently.",
])

# ═══ 4. Recommended baseline ══════════════════════════════════════════════════
story += section(4, "Recommended convar baseline")
story.append(P(
    "Defaults below are the current-build values. The recommendation column is a starting point for a "
    "200-300 player PulseRust server. " + col("<b>TEST</b>", YELLOW) + " means trial on staging first, "
    "and “gameplay” marks settings players will notice.", sBodyJ))

story += H2("4A. Core loop, threading and saves")
t4a = [
    ["Convar", "Default", "Recommend", "Why / risk"],
    [C("server.useplayerupdatejobs"), "3 (4 from 5 Nov)", "leave unset", "Track Facepunch's default; verify it reads 4."],
    [C("server.emergencydisableplayerjobs"), "true", "true", "Safety net that falls back to vanilla instead of crashing."],
    [C("fps.limit"), "240", "240", "Use at least 100 on a shared host. Never 30-60 “to save CPU”."],
    [C("server.tickrate"), "10", "10", "See 2.2."],
    [C("server.saveinterval"), "600 s", "600 (900)", "Use 900 only if the save log shows write+disk over ~0.5 s. "
     "Longer means more rollback on a crash."],
    [C("server.saveframebudget"), "5 ms", "5", "ms per frame warming save caches before the write."],
    [C("server.savebackupcount"), "2", "2", "Rotation is rename-based and cheap; the minimum is 2."],
    [C("gc.incremental_milliseconds"), "3", "3", "Incremental GC slice per frame. GC spikes come from plugin "
     "allocations; fix those instead."],
    [C("global.job_system_threads"), "auto", "leave unset", "Auto-sized; made affinity-aware by a 13 Oct commit."],
]
story.append(grid(t4a, [58 * mm, 25 * mm, 20 * mm, 75 * mm]))
story.append(P(
    f"{B('How saves actually cost you.')} {C('SaveRestore.Save()')} has three phases. It warms each entity's "
    f"save cache, spread across frames by {C('server.saveframebudget')}. It writes every cache into one buffer "
    f"{B('inside a single frame')}. It rotates backups and writes the file {B('synchronously on the main thread')}. "
    "The server logs this every save as " + C("Saved N ents, cache(x), write(y), disk(z)") + ". Chart those "
    "numbers across the wipe: write grows with entity count, and disk shows whether storage is too slow "
    "(use NVMe).", sBodyJ))

story += H2("4B. Entity count and cleanup")
t4b = [
    ["Convar", "Default", "Recommend", "Why / risk"],
    [C("decay.scale"), "1", "1", "Never below 1 for performance (2.3)."],
    [C("decay.upkeep"), "true", "true", "Upkeep is what lets you keep decay fast without punishing active players."],
    [C("server.itemdespawn"), "300 s", "240 (gameplay)", "Dropped items are physics bodies; this also scales "
     "loot-bag lifetime."],
    [C("server.itemdespawn_quick"), "30 s", "30", "Already short."],
    [C("server.corpsedespawn"), "300 s", "300", "Keep. Shorter angers players more than it helps."],
    [C("bike.outsidedecayminutes"), "1440", "480 (gameplay)", "Abandoned bikes last 24 h outside by default."],
    [C("snowmobile.outsidedecayminutes"), "1440", "480 (gameplay)", "Same as bikes."],
    [C("modularcar.outsidedecayminutes"), "864", "480 (gameplay)", "Cars are heavy multi-module physics entities."],
    [C("modularcar.population"), "3", "2 (optional)", "Fewer roaming cars to simulate."],
    [C("spawn.max_density"), "1", "1", "Also cuts ores and collectibles. Lower it only with clear entity-pressure "
     "evidence, or use Entity Reducer for targeted cuts."],
]
story.append(grid(t4b, [52 * mm, 18 * mm, 28 * mm, 80 * mm]))
story.append(P(
    "The 2026 naval content adds player-built boats with long decay start delays "
    f"({C('playerboat.decaystartdelayminutes')} 1440, {C('tugboat.tugdecaystartdelayminutes')} 1440). Watch them "
    "in entity reports. They are bases that move.", sNote))

story += H2("4C. AI and navmesh")
t4c = [
    ["Convar", "Default", "Recommend", "Why / risk"],
    [C("aimanager.ai_dormant"), "true", "true", "Agents outside player range go dormant."],
    [C("aimanager.ai_to_player_distance_wakeup_range"), "160 m", "160 (140)", f"Try 140 only if {C('ai.brainstats')} "
     "shows most animals awake at peak."],
    [C("aithinkmanager.animalframebudgetms"), "2 ms", "2 (" + col("TEST", YELLOW) + " 1.5)", "Caps animal "
     "AI time per frame; animals react slower."],
    [C("aimanager.pathfindingiterationsperframe"), "100", "100", "Facepunch's documented tuning range is 50-500."],
    [C("ai.npc_max_junkpile_count"), "30", "20 (optional)", "Fewer roaming junk-pile scientists."],
    [C("aimanager.nav_wait"), "true", "true", "Waits for the navmesh before opening, avoiding generation hitches "
     "while players are on."],
    [C("ai.nav_carve_use_building_optimization"), "false", col("TEST", YELLOW) + " true", "Fewer navmesh carve "
     f"volumes per base (min {C('ai.nav_carve_min_building_blocks_to_apply_optimization')} = 25 blocks)."],
    [C("aimanager.nav_obstacles_carve_state"), "2", col("TEST", YELLOW) + " 1", "1 = only player construction "
     "carves the navmesh; 0 = none. NPCs may path through deployables."],
    [C("aimanager.nav_disable"), "false", "false", "Never enable on a server with NPCs or animals: they can't move."],
    [C("-useNewNavmesh") + " (launch arg)", "off", col("TEST", YELLOW), "See Section 3."],
]
story.append(grid(t4c, [62 * mm, 16 * mm, 26 * mm, 74 * mm]))

story += H2("4D. Per-frame budgets (leave at default unless profiling points at them)")
story.append(P(
    "These caps already protect frame time. Lower one only when " + C("profile.perfsnapshot") + " shows that "
    "system near its cap in your worst frames, and accept that it will lag. Automation-heavy wipes are the "
    "usual reason:", sBodyJ))
t4d = [
    ["Convar", "Default", "Recommend", "Note"],
    [C("server.industrialtransferstricttimelimits"), "true", "true", "Aborts slow transfers (uneven splitting) to protect frame time."],
    [C("server.maxitemstacksmovedpertickindustrial"), "12", "12 (" + col("TEST", YELLOW) + " 8)", "Stacks one conveyor moves per tick."],
    [C("server.industrialframebudgetms"), "0.5 ms", "0.5", "Industrial job queue."],
    [C("server.hopperanimationbudgetms"), "0.1 ms", "0.1", "0 or less = items move instantly (no animation work)."],
    [C("autoturret.scan_budget_ms"), "0.5 ms", "0.5", "Renamed from auto_turret_budget_ms."],
    [C("growableentity.framebudgetms"), "0.25 ms", "0.25", "Large farms on high pop can saturate this."],
    [C("ioentity.framebudget*"), "0.25-1 ms", "default", "Lower the low-priority electric budget first if needed."],
]
story.append(grid(t4d, [64 * mm, 18 * mm, 26 * mm, 70 * mm]))

story += H2("4E. Physics, network and AntiHack")
t4e = [
    ["Convar", "Default", "Recommend", "Why / risk"],
    [C("physics.droppedmode"), "2", col("TEST", YELLOW) + " 3", "Unity collision mode for dropped items and "
     "corpses: 2 = ContinuousDynamic, 3 = ContinuousSpeculative (cheaper; already used for server ragdolls). "
     "Watch for items clipping through floors."],
    [C("physics.sendeffects"), "true", "true", "Collision effects to clients; negligible saving."],
    [C("server.encryption"), "2", "2", "Don't trade security for CPU; network work is threaded."],
    [C("server.netcache"), "true", "true", "Caches entity network serialisation."],
    [C("antihack.*"), "defaults", "defaults", "Jobs 3 moved AntiHack work into Burst jobs. Disabling "
     "protections trades cheaters for microseconds."],
]
story.append(grid(t4e, [40 * mm, 18 * mm, 22 * mm, 98 * mm]))

# ═══ 5. Hardware & operations ═════════════════════════════════════════════════
story += section(5, "What high-pop servers do: hardware and operations")
story.append(P(
    "Large networks don't publish their configs, and no current settings from the big high-pop operators "
    "turned up in public sources. What is documented, and consistent across admin forums, Facepunch's own "
    "notes and hosting guides:", sBodyJ))
ops = [
    ["Area", "Practice", "Evidence"],
    ["CPU", "Single-core speed still sets the ceiling (main thread). Since 2026, worker threads matter too: "
     "Jobs 3/4, navigation and IK. Give each high-pop instance at least 8 fast cores, ideally a whole CCD, "
     "and never share a CCD between two busy instances. X3D parts are popular, but no Rust-server benchmark "
     "was found; measure before buying.", "Facepunch devblogs; admin consensus"],
    ["RAM", "32 GB or more per high-pop instance with plugins. Memory grows across a wipe; the Livestock "
     "update freed ~175 MB of map data.", "Hosting guidance; Livestock notes"],
    ["Storage", "NVMe. The save's write and disk phases run synchronously on the main thread.", "Server source"],
    ["OS", "No measurable Linux vs Windows difference in community reports. Run what your team operates best.",
     "uMod / Oxide forums, r/playrustadmin"],
    ["Restarts", "Daily off-peak restart with a countdown (Smooth Restarter, Timed Execute). Admins report "
     "memory creep over multi-day uptime. Restart before peak, never during it.", "Oxide forum threads"],
    ["Wipe / map", "Entity count sets the practical wipe length. Rustoria's 2018 post described wiping "
     "because ~175k entities broke plugins and restarts; builds handle far more now, but the curve is the "
     "same. 3500-4500 maps for 150-300 pop; custom-map prefab count adds fixed entities.",
     "Rustoria Steam post; hosting guides"],
    ["Framework", "Carbon is the common choice on busy modded servers for its tooling and update speed. No "
     "independent Carbon vs Oxide benchmark exists, so plugin quality dominates either way.",
     "Carbon repo; hosting comparisons"],
    ["Staging", "A staging server that mirrors plugins and config. Test each wipe's patch, Jobs level and "
     "plugin updates there first.", "Standard practice"],
]
story.append(grid(ops, [22 * mm, 116 * mm, 40 * mm]))

# ═══ 6. Myths & dead convars ══════════════════════════════════════════════════
story += section(6, "Myths and dead convars to delete")
story.append(P("Each line below was checked against the 2023/2024 source and against both 2026 command "
               "lists. Delete these from server.cfg, serverauto.cfg and any launch scripts:", sBodyJ))
myths = [
    ["Setting", "Reality", "Action"],
    [C("gc.buffer 4096"), "Client-only ([ClientVar], no [ServerVar]) since at least 2019. The buffer logic "
     "lives in Rust.GC, an IClientComponent, so the server never runs it.", "Delete"],
    [C("gc.interval"), "Not present in 2023+ builds.", "Delete"],
    [C("physics.steps") + ", " + C("physics.minsteps"), "Existed in 2023; absent from both 2026 command lists.",
     "Delete"],
    [C("global.asyncwarmup") + ", " + C("global.preloadconcurrency") + ", " + C("global.warmupconcurrency"),
     "Removed.", "Delete"],
    [C("batching.colliders") + ", bare " + C("nav_disable"), "Don't exist. The navmesh switch is "
     + C("aimanager.nav_disable") + " and must stay false.", "Delete"],
    [C("autoturret.auto_turret_budget_ms"), "Renamed to " + C("autoturret.scan_budget_ms") + ".", "Rename / delete"],
    [C("sleepers.on") + ", " + C("truth.enforce") + ", " + C("cheaters.log") + ", "
     + C("server.maxticketspersecond") + ", " + C("server.clienttimeout") + ", " + C("server.globalchat"),
     "Old or Legacy-era convars; absent from current builds, so they do nothing.", "Delete"],
    [C("server.useplayerupdatejobs 0/1/2"), "Modes 0/1 deprecated; mode 2 removed in July 2026.", "Delete"],
    [C("server.tickrate 30/60/128"), "Not the simulation tick (2.2).", "Set 10"],
    [C("fps.limit 30/60") + " “to save CPU”", "Throttles every per-frame budget (Section 1).", "Set 240"],
    ["Inline comments, e.g. " + C("fps.limit 240 # cap"), "Rust only skips lines whose first character is "
     + C("#") + ". Trailing text is passed to the command.", "Own-line comments only"],
]
story.append(grid(myths, [62 * mm, 92 * mm, 24 * mm]))
story.append(P(
    "Load order matters: " + C("server.readcfg") + " runs " + C("serverauto.cfg") + " first and "
    + C("server.cfg") + " second, so server.cfg wins. " + C("server.writecfg") + " rewrites serverauto.cfg "
    "with every saved convar (fps.limit is one), so check it for stale values after any admin runs it.", sNote))

# ═══ 7. Plugins ═══════════════════════════════════════════════════════════════
story += section(7, "Plugin performance")
story += H2("7.1 Framework")
story.append(P(
    "PulseRust already runs Carbon; the Kits/PulseDailyGems audit cites Carbon profiler output. Keep it. "
    "Carbon's repository is actively maintained (last commit on " + RESEARCH_DATE + ") and has the most "
    "complete built-in profiler in the ecosystem. Update Carbon in the same maintenance window as the "
    "Rust patch every wipe.", sBodyJ))

story += H2("7.2 Profiling toolkit (all verified in source)")
tools = [
    ["Tool", "Command", "What it tells you"],
    ["Carbon", C("c.profile 60") + " then " + C("c.profiler.print -t"),
     "Native Mono profile of everything for 60 s (flags -cm -am -t -c -gc). Exports as table, CSV, JSON or ProtoBuf."],
    ["Carbon", C("c.profile.plugin Kits 60"), "Recompiles one plugin with profiler hooks, records, then reverts. "
     "Needs \"TrackCalls\": true in config.profiler.json."],
    ["Carbon", C("c.hooks") + ", " + C("c.hookinfo OnEntitySpawned"), "Live hooks; per-hook time, memory and "
     "lag-spike counts, and which plugins subscribe."],
    ["Oxide (reference)", C("o.plugins"), "Per-plugin cumulative hook time and hook-allocated memory. "
     "Oxide logs any single hook call over 100 ms, tagged [GARBAGE COLLECT] when a GC ran during it."],
    ["Facepunch", C("profile.perfsnapshot 15 Peak 10"), "Writes a JSON perf snapshot of up to 10 frames "
     "(arguments: delay, name, frames), viewable in Perfetto. Shows main and worker threads."],
    ["Facepunch", C("profile.watchallocs"), "Tracks allocations and dumps a .json.gz with stacks once conditions are met."],
    ["Facepunch", C("profile.profiling_lagspikes") + " + " + C("profile.rpc_lagspike_threshold"),
     "Records inbound RPCs and console commands that caused lag spikes (RCON has its own threshold)."],
    ["RCON", C("serverinfo"), "EntityCount, Framerate, Memory, Collections (GC count), NetworkIn/Out. "
     "Log it every minute."],
    ["Console", C("spawn.report") + ", " + C("ai.brainstats") + ", " + C("pool.print_memory") + ", "
     + C("physics.print_colliders_per_prefab"),
     "Population fill vs target, live AI brains, object pools, and the prefabs carrying the most colliders."],
]
story.append(grid(tools, [26 * mm, 64 * mm, 88 * mm]))
story.append(P("If " + C("c.profile") + " reports that the Mono profiler couldn't start, check the server log. "
               "Carbon also publishes a dedicated profiler build on its GitHub releases page.", sNote))

story += H2("7.3 The hooks that dominate on high pop")
hooks = [
    ["Hook", "How often it fires", "Rule for plugin code"],
    [C("CanNetworkTo"), "Per entity, per client, on every network send", "Avoid unless essential (vanish/hide). "
     "Exit on the first cheap check."],
    [C("OnPlayerInput") + ", " + C("OnPlayerTick"), "Every player tick (16-32 Hz × players)", "No allocations, LINQ, "
     "string building or permission lookups; cache per player."],
    [C("OnEntitySpawned") + ", " + C("OnEntityKill"), "Every entity, including the whole world at startup",
     "Type-check first, then defer real work to a queue."],
    [C("OnEntityTakeDamage"), "Every hit; explosive raids fire thousands", "Cheapest rejections first; no "
     "Physics queries."],
    [C("OnItemAddedToContainer") + ", " + C("CanAcceptItem"), "Every item move; conveyors and crafting", "Very hot "
     "on automation wipes; keep to O(1) work."],
    [C("OnTick"), "server.tickrate per second", "Prefer a timer at the cadence you need."],
    [C("OnServerSave"), "Every saveinterval", "Never write files synchronously here; add 5-25 s random "
     "jitter and write on a worker thread."],
]
story.append(grid(hooks, [50 * mm, 52 * mm, 76 * mm]))

story += H2("7.4 Patterns to remove (and where PulseRust already has them)")
story += bullets([
    f"{B('Synchronous disk I/O on the main thread')}: File.ReadAllText/WriteAllText or JSON serialise on "
    "player actions, connects, disconnects or saves. Found in Kits (K-01), PulseDailyGems (DG-01), "
    "UltimateLeaderboard (UL-02, UL-03) and ClanTree (CT-01..03). It compounds with Rust's own "
    "single-frame save write. Fix with the Kits v2 PlayerSaveWorker pattern: dirty flag, background "
    "thread, binary format and random save jitter.",
    f"{B('Whole-world scans on timers')}: iterating {C('BaseNetworkable.serverEntities')} or calling "
    "FindObjectsOfType every few seconds. Track the entities you care about in spawn/kill hooks instead, or "
    "time-slice the scan with a coroutine as Entity Cleanup does.",
    f"{B('Per-second UI rebuilds for every player')}: HUD and info panels that re-send full CUI JSON. Send once, "
    "then update only the changed element, and pre-serialise static layouts to byte[] (as Kits v2 and "
    "UltimateLeaderboard already do).",
    f"{B('Allocation-heavy hot hooks')}: LINQ, string concatenation, boxing and new lists inside the hooks in "
    "7.3. They don't show in hook time; they show up as GC collections and [GARBAGE COLLECT] hitches.",
    f"{B('Large physics queries')}: OverlapSphere or Vis.Entities with big radii in frequent hooks or timers.",
])

story += H2("7.5 Performance-oriented plugins (confirmed on uMod)")
pl = [
    ["Plugin (author)", "Use", "Caveat"],
    ["Entity Cleanup (2CHEVSKII)", "Removes entities outside building privilege or not authorised on the TC; "
     "time-sliced coroutine.", "Run off-peak; review its config before the first run."],
    ["Auto Decay", "Applies decay damage to objects outside building zones.", "Overlaps vanilla decay; "
     "configure deliberately."],
    ["Entity Limit (Orange / The Friendly Chap)", "Caps entities per player or per building.",
     "Gameplay rule, but the most direct brake on late-wipe growth."],
    ["Entity Reducer (Arainrr)", "Sets exact target counts for any spawn population: ores, collectibles, "
     "barrels, animals.", "Disables population scaling for populations it manages."],
    ["Despawn Config (Wulf)", "Per-item and container despawn times.", "Finer-grained than "
     + C("server.itemdespawn") + "."],
    ["Performance Monitor (Orange)", "Collects server performance information.", "Complements the Carbon profiler."],
    ["Smooth Restarter / Timed Execute", "Scheduled restarts with countdowns.", "-"],
]
story.append(grid(pl, [46 * mm, 80 * mm, 52 * mm]))
story.append(P("Every plugin is itself a cost. Prefer a vanilla convar where one does the job, and profile "
               "new plugins on staging under bots or load before production.", sNote))

story += H2("7.6 PulseRust plugin backlog from earlier audits")
story.append(P("These were the Critical findings in the four previous reports. If any are still open, fix them "
               "before tuning convars: they produce the 100 ms+ stalls that no server setting can absorb.",
               sBodyJ))
backlog = [
    ["ID", "Plugin", "Finding"],
    ["K-01", "Kits", "Synchronous disk save on every kit redemption"],
    ["K-02", "Kits", "GetOrCreateKitData() silently creates player records on every UI panel build"],
    ["DG-01", "PulseDailyGems", "Synchronous disk save on every gem claim"],
    ["UL-01", "UltimateLeaderboard", "GetEntry() blocks on stat-event miss"],
    ["UL-02", "UltimateLeaderboard", "LoadAllClans() synchronous on startup"],
    ["UL-03", "UltimateLeaderboard", "60 serializations on main thread per save"],
    ["CT-01", "ClanTree", "Synchronous File.ReadAllText on player connect"],
    ["CT-02", "ClanTree", "Coroutine HandleSaves() still writes JSON on main thread"],
    ["CT-03", "ClanTree", "SaveClanData() called synchronously on player disconnect"],
]
story.append(grid(backlog, [16 * mm, 40 * mm, 122 * mm]))

# ═══ 8. Rollout ═══════════════════════════════════════════════════════════════
story += section(8, "Measurement and rollout plan")
story += H2("Baseline first (one peak day, before changing anything)")
story += bullets([
    f"Log {C('serverinfo')} every 60 s: Framerate, EntityCount, Memory and Collections. Chart FPS against "
    "entity count across the wipe.",
    "Pull every " + C("Saved N ents, cache(x), write(y), disk(z)") + " line from the server log.",
    f"At peak, capture {C('profile.perfsnapshot 15 PeakDay1 10')} and a Carbon {C('c.profile 120')}.",
    f"Record {C('spawn.report')} and {C('ai.brainstats')} once at peak.",
])
story += H2("Change order (one group at a time; 48 h between groups)")
plan = [
    ["Step", "Changes", "Player-visible?"],
    ["1", "Jobs level check, CPU cores/affinity, fps.limit 240, server.tickrate 10", "No"],
    ["2", "Delete dead convars; clean serverauto.cfg", "No"],
    ["3", "Plugin fixes from 7.6; stagger OnServerSave", "No"],
    ["4", "Entity hygiene: decay.scale 1, cleanup plugin, vehicle/item lifetimes. Announce to players first.", "Yes"],
    ["5", "TEST items on staging, one at a time: -useNewNavmesh, carve options, physics.droppedmode 3, "
          "lower budgets", "Possibly"],
]
story.append(grid(plan, [12 * mm, 136 * mm, 30 * mm]))
story += H2("Success looks like")
story += bullets([
    "Peak FPS stays flat from wipe day to the end of the wipe instead of sliding with entity count.",
    "Save write+disk stays under ~0.5 s at end of wipe.",
    "No hook-time warnings or lag-spike records attributed to PulseRust plugins.",
    "GC collections per minute stay flat at peak.",
])

# ═══ Appendix A ═══════════════════════════════════════════════════════════════
story.append(CondPageBreak(90 * mm))
story.append(P("Appendix A - server.cfg snippet", sH1))
story.append(hr(ACCENT, 0.8))
story.append(P("Also committed as " + C("PulseRust_HighPop_Recommended.cfg") + ". Merge it into "
               + C("server/<identity>/cfg/server.cfg") + "; don't paste it over the top. Lines starting with "
               + C("#") + " are ignored by Rust.", sBody))
with open("/home/user/ClaudeAI/PulseRust_HighPop_Recommended.cfg", encoding="utf-8") as fh:
    story.append(code_block(fh.read().rstrip()))

# ═══ Appendix B ═══════════════════════════════════════════════════════════════
story.append(P("Appendix B - Sources", sH1))
story.append(hr(ACCENT, 0.8))
src_groups = [
    ("Server source, convar lists and framework code (primary, read directly)", [
        (link("https://github.com/MillionthOdin16/RustChangelog", "MillionthOdin16/RustChangelog"),
         "decompiled server, Aug 2024: ServerMgr, ServerBuildingManager, DecayEntity, SaveRestore, SpawnHandler, "
         "DensitySpawnPopulation, ConVar/Server, ConVar/Player, ConVar/Physics, ConVar/Admin"),
        (link("https://github.com/Ailtop/RustDocuments", "Ailtop/RustDocuments"),
         "decompiled server, late 2023: ConVar/GC, ConVar/FPS, ConsoleCommands.json"),
        (link("https://github.com/unet-dev/Decompiled-Assemblies", "unet-dev/Decompiled-Assemblies"),
         "2019: ConVar/GC, Facepunch.Console ConsoleSystem.RunFile (comment handling)"),
        (link("https://github.com/Klobiroff/Rust-217Devblog-Source", "Klobiroff/Rust-217Devblog-Source"),
         "Rust/GC.cs (client-only GC buffer component)"),
        (link("https://github.com/dexsper/RustRcon", "dexsper/RustRcon"),
         "1,651 commands with help text generated from the game's ConsoleGen (commit 21 Apr 2026)"),
        (link("https://github.com/Crushedice/RustManagerAgent", "Crushedice/RustManagerAgent"),
         "2025-26 convar value dump (knowledge/verified/variables_import_lines.jsonl)"),
        (link("https://github.com/CarbonCommunity/Carbon", "CarbonCommunity/Carbon"),
         "Core.Commands.Profiler.cs, Core.Commands.Hooks.cs"),
        (link("https://github.com/OxideMod/Oxide.Core", "OxideMod/Oxide.Core") + " / " +
         link("https://github.com/OxideMod/Oxide.Rust", "Oxide.Rust"),
         "Plugin.cs hook timing and warnings; RustCommands.cs; Rust.opj hook manifest"),
        (link("https://github.com/publicrust/umod-pluigns-dataset", "publicrust/umod-pluigns-dataset"),
         "uMod plugin snapshot used to confirm plugin names and behaviour"),
    ]),
    ("Facepunch 2026 devblogs and changelogs (read via search extracts; site not reachable from the research environment)", [
        (link("https://rust.facepunch.com/news/spring-clean"), "Jobs 2 default, Jobs 3 experimental, 360-player profile"),
        (link("https://rust.facepunch.com/news/upgrade-hard-raid-harder"), "thread-safe entity saving"),
        (link("https://rust.facepunch.com/news/built-different"), "Unity 6, allocation work, -useNewNavmesh"),
        (link("https://rust.facepunch.com/news/common-ground") + ", " + link("https://rust.facepunch.com/changelist/4043"),
         "Jobs 3 default, Jobs 2 removed"),
        (link("https://rust.facepunch.com/news/power-trip"), "Jobs 4 parallel entity saving, benchmark figures"),
        (link("https://rust.facepunch.com/news/livestock"), "multithreaded navigation and IK, NPC frame cap quote"),
        (link("https://rust.facepunch.com/changes"), "changelog entries (parallel save leak fix, mode changes)"),
        (link("https://rustfront.com/news/upcoming-2026-11"), "commit log preview: #167854, #168889, Fleck swap, #170103"),
        (link("https://mixed-news.com/en/rust-npc-per-frame-budget-facepunch-multithreaded-navmesh/"),
         "coverage of the Livestock NPC budget and navmesh claims"),
        (link("https://pinehosting.com/blog/rust-september-update-2026-breach-and-clear-monument-blockers-hqm-nodes-and-more/"),
         "September Jobs 4 improvements (secondary)"),
    ]),
    ("Community and operations evidence (lower confidence)", [
        (link("https://steamcommunity.com/groups/rustoria/discussions/0/1620600279666568817"),
         "Rustoria 2018: entity-driven wipes, ~175k entity breaking point"),
        (link("https://oxidemod.org/threads/rust-server-eating-more-ram-over-time.11698"),
         "RAM growth and daily restarts"),
        (link("https://umod.org/community/rust/11080-better-server-platform-linux-or-windows"),
         "Linux vs Windows discussion"),
        (link("https://physgun.com/help/game-hosting/rust/how-map-size-affects-rust-server-performance/"),
         "map size vs population guidance"),
        (link("https://eastgate.host/rust-server-optimization-high-entities-low-fps/") + ", " +
         link("https://xgamingserver.com/blog/how-do-we-improve-rust-server-performance/") + ", " +
         link("https://supercraft.host/wiki/rust/performance_optimization/"),
         "examples of hosting-guide advice this report corrects (tickrate 30-60, fps caps, gc.buffer variants)"),
    ]),
]
for title, items in src_groups:
    story += H2(title)
    for lnk, desc in items:
        story.append(Paragraph(f"•&nbsp;&nbsp;{lnk}: {esc(desc)}", sSrc))


# ── Page decoration ───────────────────────────────────────────────────────────
def add_page_bg(canvas, _doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(
        PAGE_W / 2, 9 * mm,
        f"PulseRust High-Performance Analysis  •  High-Pop Server Tuning Guide  •  {RESEARCH_DATE}  •  "
        f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


doc.build(story, onFirstPage=add_page_bg, onLaterPages=add_page_bg)
print(f"PDF written to {OUTPUT}")
