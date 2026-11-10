#!/usr/bin/env python3
"""EventRoams.cs map marker + HUD performance audit report (same house style as the other reports)."""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

OUT = "/home/user/ClaudeAI/EventRoams_PerformanceReport.pdf"

BG = colors.HexColor("#0D1117")
PANEL = colors.HexColor("#161B22")
BORDER = colors.HexColor("#30363D")
ACCENT = colors.HexColor("#58A6FF")
RED = colors.HexColor("#F85149")
ORANGE = colors.HexColor("#D29922")
YELLOW = colors.HexColor("#E3B341")
GREEN = colors.HexColor("#3FB950")
WHITE = colors.HexColor("#E6EDF3")
MUTED = colors.HexColor("#8B949E")
CODE_BG = colors.HexColor("#1C2128")
CODE_TEXT = colors.HexColor("#79C0FF")

PAGE_W, PAGE_H = A4
LM = RM = 18 * mm
TM = BM = 16 * mm
CONTENT_W = PAGE_W - LM - RM

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                        title="EventRoams - Map Marker and HUD Performance Audit")

ss = getSampleStyleSheet()


def S(name, **kw):
    return ParagraphStyle(name, parent=ss["Normal"], **kw)


sTitle = S("sTitle", fontSize=26, leading=32, textColor=WHITE, alignment=TA_CENTER, spaceAfter=4, fontName="Helvetica-Bold")
sSub = S("sSub", fontSize=12, leading=16, textColor=MUTED, alignment=TA_CENTER, spaceAfter=2, fontName="Helvetica")
sDate = S("sDate", fontSize=9, textColor=MUTED, alignment=TA_CENTER, spaceAfter=16, fontName="Helvetica")
sSect = S("sSect", fontSize=14, textColor=ACCENT, spaceBefore=14, spaceAfter=4, fontName="Helvetica-Bold")
sBody = S("sBody", fontSize=9, textColor=WHITE, spaceAfter=4, fontName="Helvetica", leading=14)
sBullet = S("sBullet", fontSize=9, textColor=WHITE, spaceAfter=2, fontName="Helvetica", leftIndent=12,
            bulletIndent=2, leading=13)
sCode = S("sCode", fontSize=7.5, textColor=CODE_TEXT, backColor=CODE_BG, fontName="Courier", leading=11,
          spaceAfter=6, spaceBefore=2, leftIndent=6, rightIndent=6)
sCell = S("sCell", fontSize=8.5, textColor=WHITE, fontName="Helvetica", leading=12)
sCellB = S("sCellB", fontSize=8.5, textColor=WHITE, fontName="Helvetica-Bold", leading=12)


def hr():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=8, spaceBefore=4)


def hexcol(c):
    return "#" + c.hexval()[2:].upper()


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def code(text):
    return Paragraph("<br/>".join(esc(text).split("\n")).replace(" ", "&nbsp;"), sCode)


def bullets(items):
    return [Paragraph(i, sBullet, bulletText="•") for i in items]


def finding(fid, sev, sev_color, title, flow):
    """Header bar plus body flowables. The header is kept with the first paragraph."""
    header = Table([[
        Paragraph(f'<font color="{hexcol(sev_color)}" size="9"><b>{fid}</b></font>', sBody),
        Paragraph(f'<font color="{hexcol(sev_color)}" size="9"><b>{sev}</b></font>', sBody),
        Paragraph(f'<font color="#E6EDF3" size="9"><b>{title}</b></font>', sBody),
    ]], colWidths=[14 * mm, 34 * mm, None])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 0.8, sev_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return [KeepTogether([header, Spacer(1, 3 * mm), flow[0]]), *flow[1:], Spacer(1, 4 * mm)]


def grid(rows, widths, header=True):
    data = []
    for r, row in enumerate(rows):
        data.append([Paragraph(c, sCellB if (header and r == 0) else sCell) for c in row])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), CODE_BG))
    t.setStyle(TableStyle(style))
    return t


story = []

# ── Cover ────────────────────────────────────────────────────────────────────
story += [
    Spacer(1, 22 * mm),
    Paragraph("EventRoams Plugin", sTitle),
    Paragraph("Map Marker &amp; HUD Performance Audit", sSub),
    Paragraph(f"Generated {datetime.now().strftime('%d %B %Y')}", sDate),
    hr(),
]

story.append(Paragraph("Summary", sSect))
story.append(Paragraph(
    "The map marker and the HUD are already well built. No large allocation problems and no per-player text building "
    "were found: the marker name and the HUD status text are already compared on their inputs or built once per "
    "language, the HUD uses partial refresh with shared template values, collections are pooled and freed, and the "
    "scoreboard rebuild is coalesced to at most once per 5 s. The remaining issues are a few paths a player can "
    "trigger on purpose, and some sends that repeat without need.", sBody))
story.append(Spacer(1, 2 * mm))

story.append(grid([
    ["#", "Severity", "Finding", "Status"],
    ["1", "Medium", "Repeated crossing of the zone border runs the full HUD / enter path each time",
     "Verified in code; rate estimated"],
    ["2", "Low-Medium", "EnterPlayer calls ServerPanel before the already-inside check", "Verified in code"],
    ["3", "Low-Medium", "Radius marker re-sent every 10 s although nothing in it changes",
     "Unverified (needs decompile)"],
    ["4", "Low", "HUD re-sent to every viewer every 5 s even when nothing changed", "Verified in code"],
    ["5", "Low", "BasePlayer.FindByID used in several loops", "Unverified (needs decompile)"],
], [8 * mm, 24 * mm, CONTENT_W - 8 * mm - 24 * mm - 44 * mm, 44 * mm]))
story.append(Spacer(1, 3 * mm))

story.append(Paragraph("Scope and limits", sSect))
story += bullets([
    "Read: about 900 of the 7,039 lines. That covers the map marker, the HUD controller, both zones, the scoreboard "
    "rebuild path and the image helpers.",
    "<b>Verified</b> means the plugin code was read. Anything about vanilla Rust or Oxide behaviour that could not be "
    "decompiled in this session is marked <b>unverified</b> and is not stated as fact.",
    "The CUI send and destroy cost itself belongs to the cui-partial-refresh-audit skill, which was not available. "
    "It is not audited here; this report only covers how often the plugin sends.",
    "The plugin's AGENTS.md and the game and Oxide DLLs were not available. Nothing was compiled or measured on a "
    "server. Call rates are estimates.",
    "No code was changed. The fixes below are proposals; findings 1, 2 and 4 change timing or behaviour and need "
    "approval.",
])

# ── Findings ─────────────────────────────────────────────────────────────────
story.append(Paragraph("Findings", sSect))

story += finding("1", "MEDIUM", ORANGE,
                 "Crossing the zone border over and over runs the whole HUD path each time", [
    Paragraph(
        "A player can cross the GUI zone edge as fast as they can strafe. Each crossing does the following "
        "(lines refer to EventRoams.cs):", sBody),
    *bullets([
        "<b>Enter HUD zone (:3313, :5395):</b> UpdateFields() loops over everyone in the zone for the team count "
        "(:5164). Then ShowFull runs: a Clans plugin call, a full HUD build and send with per-player element clones, "
        "TryResetPlayerSkins and the OnEventEnter hook into other plugins.",
        "<b>At night:</b> SwitchTimeForPlayer toggles the admin flag and calls SendNetworkUpdateImmediate() twice, "
        "plus console commands (:3338, :3342). The cost of that player update is unverified.",
        "<b>Enter event zone (:3256):</b> a chat or toast message, another Clans call and crafting.CancelAll().",
        "<b>Leave (:5415):</b> DestroyUi, which also fires the OnDestroyUI hook into other plugins.",
    ]),
    Paragraph(
        "The cost grows with the number of players in the zone, because of the team count. With 20 players jittering "
        "on the edge at a couple of crossings per second, that is dozens of full HUD sends a second (estimate).",
        sBody),
    Paragraph("<b>Proposed fix (needs approval):</b> only run the HUD part of the enter path if the last full show for "
              "that player was more than 3 s ago. GuiCoroutine already sends the full HUD to anyone in the zone who has "
              "no mask, so a skipped player gets it within one 5 s pass. Players see no difference apart from a short "
              "delay when they re-enter quickly.", sBody),
    code(
        "private const float EnterShowCooldown = 3f;\n"
        "private Dictionary<ulong, float> _lastFullShow =\n"
        "    Pool.Get<Dictionary<ulong, float>>();   // free in Delete()\n"
        "\n"
        "public void OnPlayerEnterToGuiZone(BasePlayer player)\n"
        "{\n"
        "    if (_deleted) return;\n"
        "\n"
        "    float now = Time.realtimeSinceStartup;\n"
        "    if (_lastFullShow.TryGetValue(player.userID, out float last) && now - last < EnterShowCooldown)\n"
        "        return;                       // GuiCoroutine sends the HUD on its next pass\n"
        "\n"
        "    _lastFullShow[player.userID] = now;\n"
        "    UpdateFields();\n"
        "    ShowFull(player);\n"
        "}"),
    Paragraph("The same cooldown idea can be applied to the event-zone enter message and the night time switch.",
              sBody),
])

story += finding("2", "LOW-MEDIUM", YELLOW,
                 "EnterPlayer calls ServerPanel before the already-inside check", [
    Paragraph(
        "Line :3698 runs DeleteOtherPluginsUi(player), a plugin call, before the PlayersInZone.Add check at :3700. "
        "OnTriggerEnter finds the player with GetComponentInParent&lt;BasePlayer&gt;. If it fires once per collider "
        "of the player, every entry makes several of these calls. How often the trigger fires per player was not "
        "verified.", sBody),
    Paragraph("<b>Proposed fix</b>, if the repeated panel close is not intended:", sBody),
    code(
        "if (!PlayersInZone.Add(player.userID)) return;\n"
        "_ins.DeleteOtherPluginsUi(player);\n"
        "OnPlayerEnterZone(player);"),
])

story += finding("3", "LOW-MEDIUM", YELLOW,
                 "Radius marker re-sent every 10 s although nothing in it changes", [
    Paragraph(
        "Lines :1534-1540 call UpdateMapMarker() every 10 s. That calls SendUpdate() and then SendNetworkUpdate() on "
        "the radius marker (:3145-3146). Its radius, colours and alpha are set once at spawn (:3097-3100). The marker "
        "is global, so each send goes to every connected player. PlayerLogin already sends the marker to anyone who "
        "joins (:252).", sBody),
    Paragraph(
        "<b>Unverified:</b> SendUpdate() may already include a network update, which would make the second call a "
        "duplicate. The decompiled MapMarkerGenericRadius.SendUpdate is needed to confirm. If the periodic send "
        "exists only to catch late joiners, it can be removed or stretched to about 60 s.", sBody),
    Paragraph("The vending marker is fine: it only sends when the minute shown in its name changes (:3156-3162).",
              sBody),
])

story += finding("4", "LOW", GREEN,
                 "HUD re-sent to every viewer every 5 s even when nothing changed", [
    Paragraph(
        "The time label and the status countdown already tick on the client. The progress bar moves less than one "
        "unit per pass (a 1,800 s event across a 200-unit bar is about 0.55 units per 5 s). The counters rarely "
        "change. Most of the traffic is therefore resync.", sBody),
    Paragraph(
        "<b>Proposed fix (needs approval):</b> in GuiCoroutine, skip the per-player refresh unless something changed: "
        "a counter value, a crate-state flip, a top rebuild, or the bar moving by 1 unit or more. Resync the timer "
        "every 30-60 s regardless. This only changes how often sends happen. Their per-send cost is for the CUI audit.",
        sBody),
])

story += finding("5", "LOW", GREEN, "BasePlayer.FindByID used in several loops", [
    Paragraph(
        "It is called per player in GuiCoroutine (:5213), per solo scorer in GetSortedTop (:2876) and in "
        "RemovePlayersFromZone (:3723). If it scans activePlayerList, the cost is players times active players every "
        "5-10 s: tens of thousands of comparisons, which is negligible today. This is unverified. If it ever matters, "
        "store BasePlayer references and skip the lookup.", sBody),
])

# ── Checked and left alone ───────────────────────────────────────────────────
story.append(Paragraph("Checked and left alone", sSect))
story += bullets([
    "<b>GetMarkerNameKey:</b> compares the whole-minute input, not the built string (Pattern 3 already done).",
    "<b>Status text and dot position:</b> built once per language per pass (Pattern 2 already done).",
    "<b>HUD updates:</b> pooled collections are freed in Delete; partial refresh with per-group containers; destroys "
    "go only to confirmed viewers; shared values are written on the templates without per-player clones; the "
    "scoreboard rebuild is coalesced to at most once per 5 s.",
    "<b>Image lookups:</b> misses are cached for 10 s, so an unresolved URL costs two plugin calls per window.",
    "<b>Zone checks:</b> IsPositionInZone uses cached copies of the position and radius.",
    "<b>Event-zone dome spheres:</b> spawned once. Their count comes from the config (Darkening and Brightness), so "
    "keep those low.",
])

# ── Open questions ───────────────────────────────────────────────────────────
story.append(Paragraph("Open questions for the dev", sSect))
story += bullets([
    "Apply fixes 1, 2 and 4? The plugin needs to be in the repo, and it has to be compiled and tested on your side.",
    "Is the repeated ServerPanel close in finding 2 intentional?",
    "Please run <font face='Courier'>ilspycmd -t MapMarkerGenericRadius</font> and "
    "<font face='Courier'>ilspycmd -t BasePlayer</font> to settle findings 3 and 5.",
    "Roughly how many players are usually in the zone?",
])


def page_bg(canvas, _doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=True, stroke=False)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(PAGE_W / 2, 10 * mm,
                             f"PulseRust High-Performance Analysis  •  EventRoams  •  "
                             f"{datetime.now().strftime('%d %b %Y')}  •  page {_doc.page}")
    canvas.restoreState()


doc.build(story, onFirstPage=page_bg, onLaterPages=page_bg)
print("PDF written to", OUT)
