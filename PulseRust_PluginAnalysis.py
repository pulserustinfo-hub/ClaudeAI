"""
PulseRust Plugin Performance Analysis Report Generator
Covers: PulseDailyGems & Kits
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Flowable
import datetime

# ── Colour palette ─────────────────────────────────────────────────────────────
C_BG        = colors.HexColor("#0D0D0D")
C_CARD      = colors.HexColor("#1A1A1A")
C_BORDER    = colors.HexColor("#2B2B2B")
C_RED       = colors.HexColor("#E84040")
C_ORANGE    = colors.HexColor("#E87C40")
C_YELLOW    = colors.HexColor("#E8C840")
C_GREEN     = colors.HexColor("#4ACF6E")
C_BLUE      = colors.HexColor("#4A8FE8")
C_PURPLE    = colors.HexColor("#9B7FE8")
C_WHITE     = colors.HexColor("#E8E8E8")
C_GREY      = colors.HexColor("#888888")
C_DARKGREY  = colors.HexColor("#333333")
C_RUST      = colors.HexColor("#CD6E3C")

OUTPUT = "/home/user/ClaudeAI/PulseRust_PluginPerformanceReport.pdf"
WIDTH, HEIGHT = A4

# ── Document ───────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    rightMargin=18*mm, leftMargin=18*mm,
    topMargin=18*mm, bottomMargin=18*mm,
    title="PulseRust Plugin Performance Analysis",
    author="Claude — High-Performance Rust Plugin Engineer"
)

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(name, **kw):
    s = ParagraphStyle(name, **kw)
    return s

ST = {
    "title": S("title",
        fontName="Helvetica-Bold", fontSize=28, textColor=C_WHITE,
        alignment=TA_CENTER, spaceAfter=4),
    "subtitle": S("subtitle",
        fontName="Helvetica", fontSize=13, textColor=C_RUST,
        alignment=TA_CENTER, spaceAfter=2),
    "meta": S("meta",
        fontName="Helvetica", fontSize=9, textColor=C_GREY,
        alignment=TA_CENTER, spaceAfter=16),
    "h1": S("h1",
        fontName="Helvetica-Bold", fontSize=16, textColor=C_RUST,
        spaceBefore=12, spaceAfter=4),
    "h2": S("h2",
        fontName="Helvetica-Bold", fontSize=13, textColor=C_WHITE,
        spaceBefore=8, spaceAfter=3),
    "h3": S("h3",
        fontName="Helvetica-Bold", fontSize=11, textColor=C_BLUE,
        spaceBefore=6, spaceAfter=2),
    "body": S("body",
        fontName="Helvetica", fontSize=9, textColor=C_WHITE,
        leading=14, spaceAfter=4, alignment=TA_JUSTIFY),
    "body_l": S("body_l",
        fontName="Helvetica", fontSize=9, textColor=C_WHITE,
        leading=14, spaceAfter=4, alignment=TA_LEFT),
    "code": S("code",
        fontName="Courier", fontSize=8, textColor=C_GREEN,
        backColor=colors.HexColor("#0A1A0A"),
        leading=12, spaceAfter=4, leftIndent=8, rightIndent=8,
        borderPadding=(4,6,4,6)),
    "code_bad": S("code_bad",
        fontName="Courier", fontSize=8, textColor=C_RED,
        backColor=colors.HexColor("#1A0A0A"),
        leading=12, spaceAfter=4, leftIndent=8, rightIndent=8,
        borderPadding=(4,6,4,6)),
    "bullet": S("bullet",
        fontName="Helvetica", fontSize=9, textColor=C_WHITE,
        leading=13, leftIndent=14, spaceAfter=2),
    "note": S("note",
        fontName="Helvetica-Oblique", fontSize=8, textColor=C_GREY,
        leading=12, spaceAfter=4, leftIndent=8),
    "label_red": S("lr",
        fontName="Helvetica-Bold", fontSize=9, textColor=C_RED),
    "label_orange": S("lo",
        fontName="Helvetica-Bold", fontSize=9, textColor=C_ORANGE),
    "label_green": S("lg",
        fontName="Helvetica-Bold", fontSize=9, textColor=C_GREEN),
    "label_blue": S("lb",
        fontName="Helvetica-Bold", fontSize=9, textColor=C_BLUE),
    "toc_entry": S("toc",
        fontName="Helvetica", fontSize=9, textColor=C_GREY,
        leading=14, leftIndent=10),
    "verdict": S("verdict",
        fontName="Helvetica-Bold", fontSize=10, textColor=C_YELLOW,
        alignment=TA_CENTER, spaceAfter=4),
}

# ── Helper flowables ───────────────────────────────────────────────────────────
def HR(color=C_BORDER, thickness=0.8):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=4)

def SP(h=6):
    return Spacer(1, h)

def P(text, style="body"):
    return Paragraph(text, ST[style])

def B(text):
    """Bullet item"""
    return Paragraph(f"<bullet>&bull;</bullet> {text}", ST["bullet"])

def severity_badge_table(label, color, text):
    data = [[Paragraph(f"<b>{label}</b>", ParagraphStyle("b",
                fontName="Helvetica-Bold", fontSize=8,
                textColor=colors.white, alignment=TA_CENTER)),
             Paragraph(text, ST["body_l"])]]
    ts = TableStyle([
        ("BACKGROUND", (0,0),(0,0), color),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",(0,0),(0,0), 6),
        ("RIGHTPADDING",(0,0),(0,0), 6),
        ("TOPPADDING", (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LINEBELOW",  (0,0),(-1,-1), 0.3, C_BORDER),
    ])
    return Table(data, colWidths=[22*mm, None], style=ts, hAlign="LEFT")

def section_header(title, sub=None):
    items = [HR(C_RUST, 1.5), P(title, "h1")]
    if sub:
        items.append(P(sub, "note"))
    items.append(HR())
    return items

def finding_block(severity, code, title, plugin, line_ref, problem, fix, extra=None):
    sev_map = {
        "CRITICAL": C_RED,
        "HIGH":     C_ORANGE,
        "MEDIUM":   C_YELLOW,
        "LOW":      C_BLUE,
        "INFO":     C_GREY,
    }
    c = sev_map.get(severity, C_GREY)
    header_data = [[
        Paragraph(f"<b>{severity}</b>", ParagraphStyle("sh",
            fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, alignment=TA_CENTER)),
        Paragraph(f"<b>[{code}]</b>", ParagraphStyle("sc",
            fontName="Helvetica-Bold", fontSize=8, textColor=C_YELLOW)),
        Paragraph(f"<b>{title}</b>", ParagraphStyle("st",
            fontName="Helvetica-Bold", fontSize=9, textColor=C_WHITE)),
        Paragraph(f"{plugin}", ParagraphStyle("sp",
            fontName="Helvetica-Oblique", fontSize=8, textColor=C_GREY)),
        Paragraph(f"{line_ref}", ParagraphStyle("sl",
            fontName="Courier", fontSize=7, textColor=C_GREEN, alignment=TA_CENTER)),
    ]]
    header_ts = TableStyle([
        ("BACKGROUND", (0,0),(0,0), c),
        ("BACKGROUND", (1,0),(-1,0), C_CARD),
        ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
        ("TOPPADDING", (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("BOX",        (0,0),(-1,-1), 0.5, c),
    ])
    header_t = Table(header_data, colWidths=[19*mm,18*mm,None,28*mm,22*mm], style=header_ts, hAlign="LEFT")

    body_rows = [
        [Paragraph("Problem", ParagraphStyle("pl",fontName="Helvetica-Bold",fontSize=8,textColor=C_RED)),
         Paragraph(problem, ST["body"])],
        [Paragraph("Fix", ParagraphStyle("fl",fontName="Helvetica-Bold",fontSize=8,textColor=C_GREEN)),
         Paragraph(fix, ST["body"])],
    ]
    if extra:
        body_rows.append([
            Paragraph("Note", ParagraphStyle("nl",fontName="Helvetica-Bold",fontSize=8,textColor=C_GREY)),
            Paragraph(extra, ST["note"])
        ])
    body_ts = TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#111111")),
        ("VALIGN",     (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
        ("RIGHTPADDING",(0,0),(-1,-1), 6),
        ("TOPPADDING", (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LINEBEFORE",  (1,0),(1,-1), 0.3, C_BORDER),
        ("LINEBELOW",   (0,0),(-1,-2), 0.3, C_BORDER),
        ("BOX",         (0,0),(-1,-1), 0.5, C_BORDER),
    ])
    body_t = Table(body_rows, colWidths=[16*mm, None], style=body_ts, hAlign="LEFT")

    return KeepTogether([SP(4), header_t, body_t, SP(4)])

# ── CONTENT ────────────────────────────────────────────────────────────────────
story = []

# ══ COVER PAGE ════════════════════════════════════════════════════════════════
story += [
    SP(40),
    P("PULSERUST SERVER", "subtitle"),
    P("Plugin Performance Audit", "title"),
    SP(6),
    HR(C_RUST, 2),
    SP(4),
    P("PulseDailyGems  ·  Kits", "subtitle"),
    SP(4),
    P(f"Prepared: {datetime.date.today().strftime('%d %B %Y')}  ·  Analyst: Claude — High-Performance Rust Plugin Engineer", "meta"),
    HR(C_BORDER),
    SP(8),
]

# Executive summary box
exec_data = [[
    Paragraph("<b>EXECUTIVE SUMMARY</b>", ParagraphStyle("es",
        fontName="Helvetica-Bold", fontSize=11, textColor=C_RUST, alignment=TA_CENTER))
],[
    Paragraph(
        "Both plugins were authored by the same developer and share the same critical architectural defect: "
        "<b>synchronous main-thread disk I/O executed on every player action</b>. On a high-population server "
        "running major raid events, this manifests as recurring main-thread stalls, garbage-collection spikes, "
        "and burst construction-packet queues visible in Carbon profiler. "
        "The Kits plugin is the primary offender: it calls <font name='Courier'>_storage.Save()</font> on "
        "<b>every single kit redemption</b> — a full binary serialise + 5-deep backup-file cascade on the main thread. "
        "PulseDailyGems does the same on every gem claim. "
        "When six sibling plugins with the same pattern all fire during <font name='Courier'>OnServerSave</font>, "
        "the stalls compound. The UI rendering layers of both plugins are well-engineered and are <b>not</b> the problem.",
        ST["body"])
]]
exec_ts = TableStyle([
    ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#1A0A00")),
    ("BOX",        (0,0),(-1,-1), 1.0, C_RUST),
    ("LEFTPADDING",(0,0),(-1,-1), 10),
    ("RIGHTPADDING",(0,0),(-1,-1), 10),
    ("TOPPADDING", (0,0),(-1,-1), 8),
    ("BOTTOMPADDING",(0,0),(-1,-1), 8),
])
story.append(Table(exec_data, colWidths=[None], style=exec_ts))
story.append(SP(14))

# Risk matrix
risk_data = [
    [Paragraph("<b>Finding</b>", ST["label_blue"]),
     Paragraph("<b>Plugin(s)</b>", ST["label_blue"]),
     Paragraph("<b>Severity</b>", ST["label_blue"]),
     Paragraph("<b>Main-Thread Impact</b>", ST["label_blue"])],
    ["Save-on-every-redeem / claim", "Kits + DailyGems",
     Paragraph("<b>CRITICAL</b>", ST["label_red"]),
     Paragraph("<b>HIGH</b> — blocks 10–80 ms per event", ST["label_red"])],
    ["OnServerSave stacking (×6 plugins)", "All siblings",
     Paragraph("<b>CRITICAL</b>", ST["label_red"]),
     Paragraph("<b>HIGH</b> — cascades into save-frame freeze", ST["label_red"])],
    ["GetLastClaim write-on-read / unbounded dict growth", "DailyGems",
     Paragraph("<b>HIGH</b>", ST["label_orange"]),
     "Grows save size every panel open"],
    ["GetOrCreateKitData creates entries on panel build", "Kits",
     Paragraph("<b>HIGH</b>", ST["label_orange"]),
     "Unbounded _usersData growth → heavier serialise"],
    ["No dirty flag — saves identical state repeatedly", "Kits + DailyGems",
     Paragraph("<b>HIGH</b>", ST["label_orange"]),
     "Wastes all disk and CPU on unchanged data"],
    ["String alloc in save path (hot with above bugs)", "Both",
     Paragraph("<b>MEDIUM</b>", ST["label_orange"]),
     "GC pressure compound during claim storms"],
    ["EncodeToPNG round-trip on image load", "Both",
     Paragraph("<b>LOW</b>", ST["label_blue"]),
     "One-time CPU spike on plugin load"],
    ["1.2 MB uncompressed banner image", "DailyGems",
     Paragraph("<b>LOW</b>", ST["label_blue"]),
     "Client connect-storm bandwidth only"],
    ["PlayerHasGroupPermission calls permission.UserHasPermission in overlay loop", "Kits",
     Paragraph("<b>MEDIUM</b>", ST["label_orange"]),
     "Per-open overhead; masked by sig cache"],
]
risk_ts = TableStyle([
    ("BACKGROUND", (0,0),(-1,0), C_DARKGREY),
    ("BACKGROUND", (0,1),(-1,2), colors.HexColor("#1A0500")),
    ("BACKGROUND", (0,3),(-1,5), colors.HexColor("#160D00")),
    ("BACKGROUND", (0,6),(-1,7), colors.HexColor("#0A0F1A")),
    ("BACKGROUND", (0,8),(-1,-1), colors.HexColor("#0A0A0A")),
    ("GRID",       (0,0),(-1,-1), 0.3, C_BORDER),
    ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 8),
    ("TEXTCOLOR",  (0,0),(-1,-1), C_WHITE),
    ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
    ("LEFTPADDING",(0,0),(-1,-1), 5),
    ("RIGHTPADDING",(0,0),(-1,-1), 5),
    ("TOPPADDING", (0,0),(-1,-1), 3),
    ("BOTTOMPADDING",(0,0),(-1,-1), 3),
])
story.append(Table(risk_data,
    colWidths=[70*mm, 32*mm, 22*mm, None],
    style=risk_ts))

story.append(PageBreak())

# ══ SECTION 1 — KITS FINDINGS ════════════════════════════════════════════════
story += section_header("1. Kits — Critical Findings",
    "Plugin: Kits v2.0.2  ·  Author: Mevent")

story.append(finding_block(
    "CRITICAL", "K-01",
    "Synchronous disk save on every kit redemption",
    "Kits", "Line 5209",
    "GiveKitToPlayer() calls <font name='Courier'>_storage.Save(_storagePath)</font> synchronously on the main thread "
    "after every single kit redeem. Save() performs: (1) full protobuf serialisation of <b>all</b> player data into a "
    "pooled BufferStream, (2) ShiftBackups() — a 5-deep cascade of File.Exists / File.Move / File.Copy / File.Delete, "
    "(3) File.OpenWrite + fs.Write for the temp file, (4) File.Copy(tmp, path, true), (5) File.Delete(tmp). "
    "That is <b>10–15 blocking syscalls per redemption</b>. During a wipe-day kit storm with 80+ concurrent players "
    "each opening kits, these stalls queue serially on the main thread. Each call also serialises the entire "
    "<font name='Courier'>_usersData</font> dictionary, whose size grows unboundedly (see K-02), making each save "
    "progressively heavier.",
    "Introduce a dirty flag. Mark dirty in UpdatePlayerData(); do <b>not</b> touch disk. "
    "Flush on OnServerSave, Unload, and a timer.Every(120f) safety interval. "
    "Serialise to byte[] on the main thread (fast — no I/O), then hand to ThreadPool for all file ops. "
    "Unload must flush synchronously since the plugin is shutting down. "
    "This collapses a 80-player kit storm from 80×15 blocking syscalls to a handful of background writes.",
    "buyclass (line 2037) also calls _storage.Save() synchronously — same fix applies there.",
))

story.append(finding_block(
    "CRITICAL", "K-02",
    "GetOrCreateKitData() silently creates player records on every UI panel build",
    "Kits", "Lines 5239, 5266, 5362, 5893",
    "<font name='Courier'>GetOrCreateKitData()</font> and <font name='Courier'>GetOrCreate()</font> are called "
    "from: ComputeKitCd, EmitUsesLabel, AppendUsesText, AppendUsesColor, CanPlayerRedeemKit, ProcessAutoKit, "
    "CanSeeKit. Many of these execute every time a player opens or switches tabs in the kit panel. "
    "If the player has no record in <font name='Courier'>_usersData</font>, the method creates one and inserts it "
    "permanently. Over a wipe on a 100-player server, every player who opens the kits UI gets a "
    "<font name='Courier'>PlayerData</font> entry inserted, and for every kit, a nested "
    "<font name='Courier'>KitData</font> entry. This grows <font name='Courier'>_usersData</font> "
    "unboundedly — which means the protobuf serialisation in Save() gets progressively slower throughout the wipe, "
    "and the save file grows from kilobytes to megabytes of empty/zero records.",
    "Split read paths from write paths. Create two variants: "
    "<font name='Courier'>GetOrLoadKitData()</font> (already exists — use it for UI/display paths, returns null for unknown players) and "
    "<font name='Courier'>GetOrCreateKitData()</font> (only for actual redemption/mutation paths). "
    "Audit every callsite: CanSeeKit (5893), ComputeKitCd (2889), EmitUsesLabel (344), AppendUsesText (2397), "
    "AppendUsesColor (2430), GetAutoKits (5914) — all must use the load-only variant. "
    "Only GiveKitToPlayer / UpdatePlayerData / ProcessAutoKit / SetPlayerKitUses should create entries.",
    "Without this fix, a 4-hour play session on a 100-player server can produce 100 × (kit_count) zero-value KitData "
    "records. With 20 kits that is 2,000 empty records being serialised and backed up on every save.",
))

story.append(finding_block(
    "HIGH", "K-03",
    "No dirty flag — identical state written to disk repeatedly",
    "Kits", "Lines 1771, 5209, 2037",
    "There is no mechanism to detect whether state actually changed between saves. "
    "OnServerSave triggers on the vanilla server-save interval (default every 5 minutes). "
    "Even if not a single player redeemed a kit since the last save, the full serialise+backup cascade still runs. "
    "With 6 sibling plugins all doing the same in the same OnServerSave frame, the main thread stalls for the "
    "sum of all 6 cascades, stacked on top of Rust's own entity serialisation which is already the heaviest "
    "operation of any save tick.",
    "Add <font name='Courier'>private volatile bool _storageDirty;</font>. Set it true in UpdatePlayerData and "
    "buyclass. In OnServerSave and the periodic timer, guard: "
    "<font name='Courier'>if (!_storageDirty) return; _storageDirty = false;</font> before serialising. "
    "This ensures saves only occur when data has actually changed.",
    "Apply the same fix to all 6 sibling plugins simultaneously — the stall budget is the sum of all their save paths.",
))

story.append(finding_block(
    "HIGH", "K-04",
    "ShiftBackups() runs on every save — excessive file ops in hot path",
    "Kits", "Line 6630 (KitsStorage.Save)",
    "ShiftBackups() runs a full 5-level rename/copy cascade on every write — including the per-redemption saves "
    "identified in K-01. This means each kit claim does not just write one file; it also renames up to 5 backup "
    "files. On SSDs this is still measurably expensive at high frequency because the filesystem metadata "
    "operations are synchronous. The cascade also uses <font name='Courier'>File.Copy</font> followed by "
    "<font name='Courier'>File.Delete</font> rather than the atomic <font name='Courier'>File.Move</font>.",
    "Move ShiftBackups() out of the per-claim hot path entirely. With K-01 fixed (saves only on the periodic "
    "flush), backups only need to run at flush time, not per-action. Replace File.Copy+Delete with "
    "<font name='Courier'>File.Replace(tmp, path, backupPath)</font> for an atomic swap with one fewer syscall. "
    "Keep the backup cascade, just don't run it 80 times during a raid-night kit storm.",
))

story.append(finding_block(
    "MEDIUM", "K-05",
    "PlayerHasGroupPermission calls permission.UserHasPermission in overlay loop",
    "Kits", "Line 2222 (PlayerHasGroupPermission)",
    "AppendPlayerOverlays() is called on every tab open and tab switch. Inside it, "
    "<font name='Courier'>PlayerHasGroupPermission()</font> calls "
    "<font name='Courier'>permission.UserHasPermission(player.UserIDString, kit.Permission)</font> directly "
    "(not via the sig cache) for every kit group. The developer already built a "
    "<font name='Courier'>ComputePermSignature</font> + <font name='Courier'>PlayerHasGroupPermBySig</font> "
    "system that avoids live permission calls — but he has two code paths and the overlay path uses the slow one.",
    "Replace all calls to <font name='Courier'>PlayerHasGroupPermission(player, ...)</font> inside "
    "AppendPlayerOverlays with <font name='Courier'>PlayerHasGroupPermBySig(sig, ...)</font> using the sig "
    "already computed at line 2700. The sig infrastructure is already there and correct — just use it consistently.",
))

story.append(finding_block(
    "MEDIUM", "K-06",
    "String interpolation allocations in high-frequency UI overlay paths",
    "Kits", "Multiple — AppendPlayerOverlays, EmitRowOverlays, etc.",
    "Multiple locations inside AppendPlayerOverlays and its callees use C# string interpolation "
    "(<font name='Courier'>$\"...\"</font>) to build layer names and commands: "
    "<font name='Courier'>cardParent + $\".Card.{kitsInGroup[0].ID}.Redeem.Dark\"</font>, "
    "<font name='Courier'>parent + $\".CD.{kit.ID}\"</font>, etc. These allocate on every panel open. "
    "While ZString is used for the builder, the intermediate layer-name strings all go through "
    "the standard string allocator. On a 100-player server with everyone opening kits simultaneously, "
    "this is thousands of short-lived string allocations per second, sustaining GC pressure.",
    "Pre-compute and cache all static layer name strings at cache-build time. For dynamic names (per kit ID), "
    "use <font name='Courier'>ZString.Concat</font> or write directly into the "
    "<font name='Courier'>Utf8ValueStringBuilder</font> to avoid intermediate string objects. "
    "The developer is already using ZString for the JSON body — extend that discipline to layer names.",
))

story.append(PageBreak())

# ══ SECTION 2 — DAILYGEMS FINDINGS ═══════════════════════════════════════════
story += section_header("2. PulseDailyGems — Critical Findings",
    "Plugin: PulseDailyGems v2.0.2  ·  Author: Mevent.Team")

story.append(finding_block(
    "CRITICAL", "DG-01",
    "Synchronous disk save on every gem claim",
    "PulseDailyGems", "Line 1460",
    "CmdClaim() calls <font name='Courier'>_storage.Save(_storagePath)</font> synchronously after every claim. "
    "The same Save() cascade as Kits: full protobuf write + 5-deep backup shuffle + temp-file-copy pattern — "
    "all blocking the main thread. During the daily reset window when many players simultaneously claim gems, "
    "each claim stalls the main thread. Combined with K-01 in Kits and the same pattern in 4 other sibling "
    "plugins, a simultaneous reset storm can block the main thread for hundreds of milliseconds cumulatively.",
    "Identical fix to K-01: dirty flag + threaded write-behind. Claim sets "
    "<font name='Courier'>_storageDirty = true</font>, no disk I/O. "
    "FlushIfDirty() runs on OnServerSave, Unload, and timer.Every(120f). "
    "Serialise to byte[] on main thread; ThreadPool does all file operations under a lock. "
    "Durability window of 120s is acceptable for a daily-gems feature.",
))

story.append(finding_block(
    "HIGH", "DG-02",
    "GetLastClaim() writes to _storage.Claims on every UI panel read",
    "PulseDailyGems", "Lines 1548–1557",
    "GetLastClaim() is called from AppendUiTo (every panel open) and from the claim-display path. "
    "When a player has no prior record, instead of returning 'claimable', the method inserts "
    "<font name='Courier'>_storage.Claims[userId] = (long)now</font> — setting the timestamp to NOW. "
    "This causes two bugs: (1) every new player who opens the panel is immediately put on a 24-hour cooldown "
    "having never received any gems; (2) the Claims dictionary grows every time any player opens the panel, "
    "making serialisation progressively heavier all wipe long.",
    "Return 0 for unknown players (fully claimable) without mutating state: "
    "<font name='Courier'>if (_storage.Claims.TryGetValue(userId, out var v) &amp;&amp; v &gt; 0) return v; return 0d;</font> "
    "Only write to Claims inside CmdClaim() after a successful claim. This also fixes the new-player cooldown bug.",
    "With this fix, Claims only grows when players actually claim gems, keeping the save file compact.",
))

story.append(finding_block(
    "HIGH", "DG-03",
    "No dirty flag — periodic OnServerSave writes unchanged data",
    "PulseDailyGems", "Line 619",
    "OnServerSave calls <font name='Courier'>_storage.Save()</font> unconditionally every server save tick. "
    "For PulseDailyGems this is especially wasteful: Claims only change when a player redeems, which happens "
    "at most once per player per 24 hours. The vast majority of OnServerSave calls write identical data.",
    "Same as K-03: guard with <font name='Courier'>if (!_storageDirty) return;</font>.",
))

story.append(finding_block(
    "MEDIUM", "DG-04",
    "EncodeToPNG round-trip on image load — wasted CPU and GC at startup",
    "PulseDailyGems", "Line 1687",
    "LoadImage() downloads/reads each image via UnityWebRequestTexture, which decodes the PNG into a GPU "
    "Texture2D. It then calls <font name='Courier'>texture.EncodeToPNG()</font> which re-encodes the texture "
    "back to PNG bytes. This round-trip is wasteful: the original file is already valid PNG. "
    "EncodeToPNG allocates a large transient byte array for the recompressed data and triggers a GC event. "
    "For the 1.2 MB banner this is a 1.2+ MB allocation at load time, repeated for every image.",
    "Read the source file directly with <font name='Courier'>File.ReadAllBytes(path)</font> and pass the raw "
    "bytes to <font name='Courier'>FileStorage.server.Store()</font>. Skip UnityWebRequest and the "
    "Texture2D entirely. This removes the decode+encode cycle, cuts startup time, and avoids the GC spike. "
    "One caveat: if images are stored in non-PNG formats, they must be pre-converted to PNG offline.",
))

story.append(finding_block(
    "LOW", "DG-05",
    "1.2 MB banner PNG is unoptimised",
    "PulseDailyGems", "Config: WelcomeBannerUrl",
    "The welcome banner is 1.2 MB (total images 1.8 MB). This does not cause server main-thread stalls but "
    "it does slow client first-open (the client must receive and decode the image on first panel open) and "
    "increases bandwidth consumption during wipe-day connect storms when many players connect simultaneously "
    "and all receive the image for the first time.",
    "Run all banner and background images through <font name='Courier'>pngquant --quality=70-90</font> and "
    "<font name='Courier'>oxipng -o 4</font>. A 1.2 MB banner can typically compress to 120–250 KB with no "
    "perceptible quality loss. This is an art pipeline task, not a code change.",
))

story.append(PageBreak())

# ══ SECTION 3 — What's GOOD ═══════════════════════════════════════════════════
story += section_header("3. Architecture Assessment — What Works Well",
    "Areas that are correctly implemented and should NOT be modified")

story += [
    P("Both plugins contain sophisticated, correct engineering in their UI rendering layers. "
      "The following are genuine strengths that distinguish this code from typical Oxide plugin work:", "body"),
    SP(4),

    P("<b>Binary protobuf-style persistence (both plugins)</b>", "h3"),
    P("Moving from JSON/DataFileSystem to a custom binary format with pooled BufferStream serialisation is "
      "the right architectural choice. The binary format is compact, fast to deserialise, and avoids "
      "Newtonsoft's reflection overhead on every read. The backup-rotation system is also correctly structured "
      "— the only problem is that it runs too frequently.", "body"),

    P("<b>Pre-baked UTF-8 UI cache with byte-level marker splicing (both plugins)</b>", "h3"),
    P("The <font name='Courier'>CachedUi</font> / <font name='Courier'>UiTemplate</font> systems are "
      "excellent. UI JSON is built once into a byte array at load time. At send time, "
      "<font name='Courier'>AppendResolved</font> splices live values (online count, timers, use counts) "
      "directly using <font name='Courier'>ReadOnlySpan&lt;byte&gt;.CopyTo</font> — zero string allocation "
      "in the hot path. This is precisely the correct approach for high-frequency UI updates.", "body"),

    P("<b>Raw RPC packet construction bypassing CuiHelper (both plugins)</b>", "h3"),
    P("<font name='Courier'>SendAddUiRaw</font> / <font name='Courier'>SendAddUiBytes</font> construct the "
      "AddUI RPC packet directly using <font name='Courier'>Network.Net.sv.StartWrite()</font> with a cached "
      "<font name='Courier'>StringPool.Get(\"AddUI\")</font> ID. This avoids CuiHelper's string serialisation, "
      "JSON wrapping overhead, and the intermediate List&lt;CuiElement&gt; allocations. Correct.", "body"),

    P("<b>Permission signature caching in Kits</b>", "h3"),
    P("The <font name='Courier'>ComputePermSignature / _sigPermIndex</font> system is well-designed: it maps "
      "kit permissions to bit positions and represents a player's permission set as a single ulong bitmask. "
      "UI templates can then be cached per-signature rather than per-player. This correctly eliminates "
      "O(players × kits) permission calls. The only issue is that one code path (K-05) bypasses it.", "body"),

    P("<b>Facepunch.Pool usage throughout</b>", "h3"),
    P("Both plugins use <font name='Courier'>Pool.Get&lt;List&lt;T&gt;&gt;()</font> and "
      "<font name='Courier'>Pool.FreeUnmanaged(ref list)</font> correctly for temporary collections in the "
      "hot path. This is the right pattern and meaningfully reduces GC pressure versus allocating new "
      "List&lt;T&gt; instances per call.", "body"),

    P("<b>Partial UI updates (not full rebuilds)</b>", "h3"),
    P("RefreshGemsCard, RefreshEventCardForAll, and HandleKitRedeemedUI all send only the changed sub-panel "
      "to the client — not the full UI hierarchy. On a 100-player server this is the difference between "
      "sending 1–2 KB vs 40–50 KB per update event. Correct.", "body"),
]

story.append(PageBreak())

# ══ SECTION 4 — Fix Priority ═══════════════════════════════════════════════════
story += section_header("4. Recommended Fix Order",
    "Prioritised by impact on main-thread stall reduction")

priority_data = [
    [Paragraph("<b>#</b>", ST["label_blue"]),
     Paragraph("<b>Finding</b>", ST["label_blue"]),
     Paragraph("<b>Plugin(s)</b>", ST["label_blue"]),
     Paragraph("<b>Expected Effect</b>", ST["label_blue"]),
     Paragraph("<b>Effort</b>", ST["label_blue"])],
    ["1", "K-01 + DG-01: Per-claim sync save → dirty flag + threaded flush",
     "Both + all 6 siblings", Paragraph("<b>Removes claim-storm stalls entirely</b>", ST["label_red"]), "Medium"],
    ["2", "K-03 + DG-03: Unconditional OnServerSave flush → guard dirty flag",
     "Both + all 6 siblings", Paragraph("<b>Removes save-tick stacking</b>", ST["label_orange"]), "Low"],
    ["3", "K-02: GetOrCreateKitData on read paths → GetOrLoadKitData",
     "Kits", Paragraph("Stops usersData growth; cuts serialise time", ST["label_orange"]), "Medium"],
    ["4", "DG-02: GetLastClaim write-on-read → read-only path",
     "DailyGems", Paragraph("Stops Claims growth; fixes new-player cooldown bug", ST["label_orange"]), "Low"],
    ["5", "K-04: ShiftBackups in hot path → move to flush only + File.Replace",
     "Both", "Cuts syscalls per write from 15 to 4", "Low"],
    ["6", "K-05: Use sig cache in overlay permission checks",
     "Kits", "Removes live permission calls from panel-open path", "Low"],
    ["7", "K-06 + DG-05: Layer-name string alloc → ZString / pre-cache",
     "Both", "Reduces sustained GC pressure on high-pop", "High"],
    ["8", "DG-04: EncodeToPNG round-trip → File.ReadAllBytes direct store",
     "DailyGems", "One-time startup: removes large transient allocation", "Low"],
    ["9", "DG-05: Compress banner images offline",
     "DailyGems", "Client connect-storm bandwidth; no server benefit", "None (art pipeline)"],
]
priority_ts = TableStyle([
    ("BACKGROUND", (0,0),(-1,0), C_DARKGREY),
    ("BACKGROUND", (0,1),(-1,2), colors.HexColor("#1A0500")),
    ("BACKGROUND", (0,3),(-1,4), colors.HexColor("#160D00")),
    ("BACKGROUND", (0,5),(-1,6), colors.HexColor("#0A0F1A")),
    ("BACKGROUND", (0,7),(-1,-1), colors.HexColor("#0A0A0A")),
    ("GRID",       (0,0),(-1,-1), 0.3, C_BORDER),
    ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",   (0,0),(-1,-1), 8),
    ("TEXTCOLOR",  (0,0),(-1,-1), C_WHITE),
    ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
    ("LEFTPADDING",(0,0),(-1,-1), 5),
    ("RIGHTPADDING",(0,0),(-1,-1), 5),
    ("TOPPADDING", (0,0),(-1,-1), 3),
    ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ("ALIGN",      (0,0),(0,-1), "CENTER"),
])
story.append(Table(priority_data,
    colWidths=[8*mm, 75*mm, 30*mm, None, 18*mm],
    style=priority_ts))

story += [SP(10),
    P("<b>Implementation note on threaded writes:</b> Oxide runs on a Mono runtime where "
      "<font name='Courier'>System.IO</font> calls are thread-safe. "
      "<font name='Courier'>ThreadPool.QueueUserWorkItem</font> is safe for file I/O. "
      "The only main-thread-bound operation is reading from "
      "<font name='Courier'>Facepunch.Pool</font> (which requires main-thread affinity) — "
      "which is why the serialise-to-byte[] step must remain on the main thread, while only the "
      "file write step moves to the thread pool. Use a <font name='Courier'>lock(_ioLock)</font> guard "
      "to prevent concurrent writes from overlapping flushes.", "body"),
]

story.append(PageBreak())

# ══ SECTION 5 — Code snippets ════════════════════════════════════════════════
story += section_header("5. Reference Code — Correct Persistence Pattern",
    "Drop-in replacement for the per-claim Save() calls in both plugins")

story += [
    P("The following pattern applies identically to both Kits and PulseDailyGems. "
      "Adapt field names to match each plugin:", "body"),
    SP(4),
    P("Fields to add:", "h3"),
    Paragraph(
        "private volatile bool _storageDirty;\n"
        "private readonly object _ioLock = new();\n"
        "private Coroutine _flushTimer;",
        ST["code"]),

    P("In OnServerInitialized():", "h3"),
    Paragraph(
        "// Bounded durability window — catches any missed dirty marks\n"
        "_flushTimer = timer.Every(120f, FlushStorageIfDirty);",
        ST["code"]),

    P("Replace every inline _storage.Save() call with:", "h3"),
    Paragraph(
        "// In GiveKitToPlayer / CmdClaim — after state mutation:\n"
        "_storageDirty = true;   // mark dirty, do NOT touch disk here",
        ST["code"]),

    P("Flush method (called by timer, OnServerSave):", "h3"),
    Paragraph(
        "private void FlushStorageIfDirty()\n"
        "{\n"
        "    if (_storage == null || string.IsNullOrEmpty(_storagePath) || !_storageDirty) return;\n"
        "    _storageDirty = false;\n"
        "\n"
        "    // Serialise on main thread (Pool is main-thread bound, no I/O here)\n"
        "    byte[] payload = SerialiseStorage();\n"
        "    var path = _storagePath;\n"
        "\n"
        "    // All file operations on worker thread\n"
        "    ThreadPool.QueueUserWorkItem(_ =>\n"
        "    {\n"
        "        lock (_ioLock)\n"
        "        {\n"
        "            try { WriteWithBackups(path, payload); }\n"
        "            catch (Exception e)\n"
        "            { Interface.Oxide.LogError(\"[Kits] async save failed: \" + e); }\n"
        "        }\n"
        "    });\n"
        "}",
        ST["code"]),

    P("Serialise to bytes on main thread:", "h3"),
    Paragraph(
        "private byte[] SerialiseStorage()\n"
        "{\n"
        "    var stream = Pool.Get<BufferStream>();  // main-thread only\n"
        "    try\n"
        "    {\n"
        "        stream.Initialize();\n"
        "        _storage.WriteHeader(stream);\n"
        "        _storage.WriteState(stream);\n"
        "        var seg = stream.GetBuffer();\n"
        "        var bytes = new byte[seg.Count];\n"
        "        Buffer.BlockCopy(seg.Array, seg.Offset, bytes, 0, seg.Count);\n"
        "        return bytes;\n"
        "    }\n"
        "    finally { Pool.Free(ref stream); }\n"
        "}",
        ST["code"]),

    P("Atomic file write (worker thread):", "h3"),
    Paragraph(
        "private static void WriteWithBackups(string path, byte[] payload)\n"
        "{\n"
        "    var dir = Path.GetDirectoryName(path);\n"
        "    if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))\n"
        "        Directory.CreateDirectory(dir);\n"
        "\n"
        "    // Shift backups (5-deep rotate — now safe, runs off main thread)\n"
        "    ShiftBackups(path);\n"
        "\n"
        "    // Atomic write: write to .new, then replace\n"
        "    var tmp = path + \".new\";\n"
        "    File.WriteAllBytes(tmp, payload);         // single write, no OpenWrite footgun\n"
        "    File.Replace(tmp, path, path + \".bak\"); // atomic swap on supported FS\n"
        "}",
        ST["code"]),

    P("Unload must flush synchronously (plugin going away, no thread pool):", "h3"),
    Paragraph(
        "private void Unload()\n"
        "{\n"
        "    if (_storageDirty && _storage != null && !string.IsNullOrEmpty(_storagePath))\n"
        "    {\n"
        "        lock (_ioLock)\n"
        "        {\n"
        "            try { WriteWithBackups(_storagePath, SerialiseStorage()); }\n"
        "            catch (Exception e) { PrintError(\"Kits unload save: \" + e); }\n"
        "        }\n"
        "    }\n"
        "    // ... rest of cleanup\n"
        "}",
        ST["code"]),

    P("OnServerSave (same for both plugins):", "h3"),
    Paragraph(
        "private void OnServerSave()\n"
        "{\n"
        "    FlushStorageIfDirty();  // no-ops if nothing changed\n"
        "}",
        ST["code"]),
]

# ══ FOOTER ═══════════════════════════════════════════════════════════════════
story += [
    PageBreak(),
    HR(C_RUST, 1),
    SP(4),
    P("PULSERUST — Plugin Performance Audit", "subtitle"),
    P(f"Generated {datetime.datetime.now().strftime('%d %B %Y at %H:%M UTC')}  ·  "
      "Claude — High-Performance Rust Plugin Engineer  ·  "
      "Classification: Internal / Developer Use Only", "meta"),
    SP(4),
    HR(C_BORDER),
    SP(6),
    P("Key Takeaway: The stalls you are experiencing are almost entirely caused by synchronous main-thread "
      "disk I/O in the persistence layer — not by UI rendering, image size, or network traffic. "
      "Fix K-01 and DG-01 (and apply the same pattern to all 6 sibling plugins) and the claim-storm stalls "
      "will disappear. Fix K-03 and DG-03 and the save-tick stacking will disappear. "
      "The remaining findings are genuine improvements but are secondary to these two changes.", "body"),
]

# ── Build ──────────────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    # dark background
    canvas.setFillColor(C_BG)
    canvas.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    # page number
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_GREY)
    canvas.drawRightString(WIDTH - 15*mm, 10*mm, f"Page {doc.page}")
    canvas.drawString(15*mm, 10*mm, "PulseRust — Plugin Performance Audit — CONFIDENTIAL")
    canvas.restoreState()

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF written to: {OUTPUT}")
