"""
AMS Intelligence — PowerPoint Slideshow Generator
Produces a professional presentation for LinkedIn / portfolio use.
Run: python3 scripts/generate_ams_slideshow.py
Output: ~/Desktop/AMS_Intelligence_Presentation.pptx
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Color palette ─────────────────────────────────────────────────────────────
GREEN      = RGBColor(0x2E, 0x7D, 0x32)
GREEN_LT   = RGBColor(0xC8, 0xE6, 0xC9)
GREEN_DARK = RGBColor(0x1B, 0x5E, 0x20)
AMBER      = RGBColor(0xE6, 0x51, 0x00)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BLACK      = RGBColor(0x21, 0x21, 0x21)
GREY       = RGBColor(0x75, 0x75, 0x75)
SLATE      = RGBColor(0x37, 0x47, 0x4F)

# ── Slide dimensions (widescreen 16:9) ────────────────────────────────────────
W = Inches(13.33)
H = Inches(7.5)

OUT = Path.home() / "Desktop" / "AMS_Intelligence_Presentation.pptx"


def rgb(r, g, b):
    return RGBColor(r, g, b)


def new_prs() -> Presentation:
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    return prs


def blank_slide(prs: Presentation):
    blank_layout = prs.slide_layouts[6]  # completely blank
    return prs.slides.add_slide(blank_layout)


def fill_bg(slide, color: RGBColor):
    from pptx.oxml.ns import qn
    from lxml import etree
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, x, y, w, h, fill: RGBColor, line: RGBColor = None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def add_text(slide, text, x, y, w, h,
             size=18, bold=False, color=BLACK, align=PP_ALIGN.LEFT,
             italic=False):
    txb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf  = txb.text_frame
    tf.word_wrap = True
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb


def add_multiline(slide, lines: list[tuple[str, int, bool, RGBColor]],
                  x, y, w, h, spacing=1.15):
    """lines: [(text, size, bold, color)]"""
    txb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf  = txb.text_frame
    tf.word_wrap = True
    from pptx.util import Pt as _Pt
    from pptx.oxml.ns import qn
    first = True
    for text, size, bold, color in lines:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(2)
        run = p.add_run()
        run.text = text
        run.font.size  = _Pt(size)
        run.font.bold  = bold
        run.font.color.rgb = color
    return txb


# ── Slide 1: Title ────────────────────────────────────────────────────────────
def slide_title(prs):
    sl = blank_slide(prs)
    fill_bg(sl, GREEN_DARK)

    # Top accent bar
    add_rect(sl, 0, 0, 13.33, 0.08, GREEN)

    # Big white title
    add_text(sl, "AMS Intelligence", 0.8, 1.2, 11, 1.6,
             size=54, bold=True, color=WHITE, align=PP_ALIGN.LEFT)

    # Subtitle
    add_text(sl, "Antimicrobial Stewardship Research Platform",
             0.8, 2.9, 11, 0.7, size=24, color=GREEN_LT, align=PP_ALIGN.LEFT)

    # Divider line (thin rect)
    add_rect(sl, 0.8, 3.75, 4.5, 0.04, GREEN)

    # Description
    add_text(sl,
             "Multi-source surveillance pipeline integrating FAERS, NHSN, WHONET, ATLAS,\n"
             "PubMed, and ASHP/IDSA guidelines — powered by local LLM inference.",
             0.8, 3.9, 11.5, 1.2, size=16, color=GREEN_LT)

    # Author block (bottom right)
    add_text(sl,
             "Michael Olszewski, PharmD, BCPS, BCCCP\n"
             "Critical Care & Infectious Disease Pharmacist",
             7.5, 6.3, 5.5, 0.9, size=13, color=GREEN_LT, align=PP_ALIGN.RIGHT)

    # Bottom bar
    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 2: The Clinical Problem ─────────────────────────────────────────────
def slide_problem(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "The Antimicrobial Resistance Crisis", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    # Left column — stats
    add_rect(sl, 0.4, 1.2, 3.7, 5.9, rgb(0xE8, 0xF5, 0xE9))
    add_text(sl, "By the Numbers", 0.6, 1.35, 3.3, 0.5,
             size=15, bold=True, color=GREEN)
    stats = [
        ("2.8M+", "AMR infections/year\nin the U.S."),
        ("35,000+", "Deaths attributable\nto AMR annually"),
        ("$4.7B", "Annual economic\nburden (U.S.)"),
        (">30%", "Antibiotic use\ndeemed inappropriate"),
    ]
    y = 1.95
    for val, lbl in stats:
        add_text(sl, val, 0.6, y, 3.3, 0.55, size=22, bold=True, color=AMBER)
        add_text(sl, lbl, 0.6, y + 0.52, 3.3, 0.55, size=11, color=SLATE)
        y += 1.28

    # Right column — challenges
    add_rect(sl, 4.4, 1.2, 8.5, 5.9, rgb(0xF5, 0xF5, 0xF5))
    add_text(sl, "Why Stewardship Programs Struggle", 4.6, 1.35, 8.1, 0.5,
             size=15, bold=True, color=GREEN)
    challenges = [
        ("Fragmented data", "FAERS, NHSN, WHONET, and ATLAS data live in separate silos with no unified view."),
        ("Manual analysis", "Resistance trend review is time-intensive; quarterly reports lag behind real-world changes."),
        ("Guideline overload", "ASHP, IDSA, SHEA, and Surviving Sepsis guidelines update frequently — hard to track at point of care."),
        ("No signal correlation", "Utilization spikes and adverse event signals are rarely cross-referenced in real time."),
        ("Report burden", "AMS committee presentations require hours of manual data aggregation and formatting."),
    ]
    y = 1.95
    for title, body in challenges:
        add_rect(sl, 4.5, y, 8.2, 0.08, GREEN)
        add_text(sl, title, 4.6, y + 0.12, 8.0, 0.35, size=13, bold=True, color=GREEN)
        add_text(sl, body, 4.6, y + 0.45, 8.0, 0.6, size=10.5, color=BLACK)
        y += 1.1

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 3: What is AMS Intelligence ─────────────────────────────────────────
def slide_overview(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "What is AMS Intelligence?", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    add_text(sl,
             "A locally-hosted, privacy-preserving research platform that unifies antimicrobial surveillance data, "
             "applies statistical signal detection, and generates plain-language AMS committee summaries — "
             "all without sending patient or institutional data to any external server.",
             0.5, 1.15, 12.3, 1.0, size=14, color=SLATE)

    # Three pillars
    pillars = [
        ("Detect", GREEN,
         "Statistical signal detection across FAERS adverse events, NHSN utilization trends, "
         "and WHONET/ATLAS resistance data using PRR, ROR, chi-squared, and time-series anomaly analysis."),
        ("Interpret", AMBER,
         "Local gemma4:26b reasoning model synthesizes multi-source signals into clinical context, "
         "referencing ASHP/IDSA guidelines via RAG (ChromaDB + nomic-embed-text)."),
        ("Report", GREEN_DARK,
         "Automated PDF generation with embedded charts, signal tables, KPI dashboards, "
         "and AMS committee-ready plain-language summaries — all on-device, no cloud required."),
    ]

    x = 0.4
    for title, color, body in pillars:
        add_rect(sl, x, 2.35, 4.0, 4.7, rgb(0xF9, 0xFB, 0xF9))
        add_rect(sl, x, 2.35, 4.0, 0.65, color)
        add_text(sl, title, x + 0.15, 2.4, 3.7, 0.55,
                 size=20, bold=True, color=WHITE)
        add_text(sl, body, x + 0.15, 3.15, 3.7, 3.7, size=12, color=SLATE)
        x += 4.3

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 4: Architecture ─────────────────────────────────────────────────────
def slide_architecture(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "System Architecture", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    # Layer boxes
    layers = [
        ("Data Layer",       "FAERS live API  ·  NHSN DOT/1000 PD  ·  WHONET resistance CSV  ·  Pfizer ATLAS  ·  PubMed Entrez",  rgb(0xE3, 0xF2, 0xFD), rgb(0x15, 0x65, 0xC0)),
        ("Analytics Layer",  "PRR / ROR / chi-squared  ·  Temporal pre/post comparison  ·  Z-score anomaly detection  ·  AMS category mapping", rgb(0xE8, 0xF5, 0xE9), GREEN),
        ("Intelligence Layer","gemma4:26b (local, 256K ctx)  ·  ChromaDB vault (ASHP/IDSA/Surviving Sepsis)  ·  nomic-embed-text RAG  ·  think=False (stewardship-optimized)", rgb(0xFF, 0xF3, 0xE0), AMBER),
        ("Presentation Layer","Streamlit dashboard (port 8502)  ·  fpdf2 PDF reports  ·  Command Center CLI  ·  Antibiogram upload & comparison", rgb(0xF3, 0xE5, 0xF5), rgb(0x6A, 0x1B, 0x9A)),
    ]

    y = 1.2
    for layer_name, detail, bg_col, accent in layers:
        add_rect(sl, 0.4, y, 12.5, 1.28, bg_col)
        add_rect(sl, 0.4, y, 0.22, 1.28, accent)
        add_text(sl, layer_name, 0.75, y + 0.12, 3.2, 0.45,
                 size=13, bold=True, color=accent)
        add_text(sl, detail, 0.75, y + 0.58, 12.0, 0.6, size=11, color=SLATE)
        y += 1.45

    # Hardware note
    add_rect(sl, 0.4, 6.9, 12.5, 0.4, rgb(0xF5, 0xF5, 0xF5))
    add_text(sl,
             "Hardware: RTX 5060 Ti 16 GB VRAM  ·  32 GB RAM  ·  Ollama @ localhost:11434  "
             "·  All inference fully on-device — zero data egress",
             0.6, 6.95, 12.1, 0.3, size=10, color=SLATE)

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 5: Data Sources ─────────────────────────────────────────────────────
def slide_data_sources(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "Integrated Data Sources", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    sources = [
        ("FDA / FAERS", "Adverse event reporting — live API integration. Real-time PRR/ROR signal detection across 18M+ case reports.", rgb(0x01, 0x57, 0x9B)),
        ("CDC / NHSN", "National Healthcare Safety Network — Days of Therapy (DOT) per 1,000 patient-days, segmented by drug class.", rgb(0x1B, 0x5E, 0x20)),
        ("WHO / WHONET", "Global resistance surveillance — organism-level MIC data, percent resistant trend analysis.", rgb(0x00, 0x63, 0x8A)),
        ("Pfizer / ATLAS", "MIC50/MIC90 susceptibility trend data — MIC creep detection, matched by antibiotic class.", rgb(0x00, 0x3C, 0x6E)),
        ("NCBI / PubMed", "Live literature integration via Entrez API — 12 curated AMS query categories, auto-embedded into ChromaDB.", rgb(0x21, 0x4F, 0x78)),
        ("ASHP / IDSA / SHEA", "Guideline RAG vault — Barlam 2016, Dellit 2007, CDC Core Elements, ASHP Statement, Surviving Sepsis 2021.", rgb(0x33, 0x69, 0x1E)),
    ]

    x, y = 0.35, 1.2
    for i, (name, desc, color) in enumerate(sources):
        col = i % 3
        row = i // 3
        sx = x + col * 4.3
        sy = y + row * 2.9
        add_rect(sl, sx, sy, 4.1, 2.7, rgb(0xF9, 0xFB, 0xF9))
        add_rect(sl, sx, sy, 4.1, 0.6, color)
        add_text(sl, name, sx + 0.12, sy + 0.1, 3.85, 0.42,
                 size=14, bold=True, color=WHITE)
        add_text(sl, desc, sx + 0.12, sy + 0.75, 3.85, 1.8, size=10.5, color=SLATE)

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 6: Resistance Analysis Module ───────────────────────────────────────
def slide_resistance(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "Module: Resistance Trend Analysis", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    # Left panel — how it works
    add_rect(sl, 0.4, 1.2, 5.8, 5.9, rgb(0xE8, 0xF5, 0xE9))
    add_text(sl, "How It Works", 0.6, 1.35, 5.4, 0.45, size=15, bold=True, color=GREEN)
    steps = [
        ("1. FAERS Query", "Pulls all adverse event reports for target drug (e.g., cefazolin) and comparator via live FDA API."),
        ("2. Signal Detection", "Computes PRR, ROR, chi-squared for each reaction PT. Evans criteria: PRR ≥ 2, N ≥ 3, chi² ≥ 4."),
        ("3. Temporal Split", "Compares pre- vs. post-cutoff year PRR to detect emerging or resolving signals."),
        ("4. Multi-source Merge", "Joins WHONET % resistant trends and ATLAS MIC50/MIC90 creep data."),
        ("5. LLM Synthesis", "gemma4:26b generates key findings and clinical interpretation with guideline citations."),
        ("6. PDF Report", "Full report: signal tables, PRR charts, temporal delta chart, WHONET/ATLAS sections."),
    ]
    y = 1.95
    for title, body in steps:
        add_text(sl, title, 0.6, y, 5.4, 0.35, size=11.5, bold=True, color=GREEN_DARK)
        add_text(sl, body, 0.6, y + 0.32, 5.4, 0.5, size=10, color=SLATE)
        y += 0.93

    # Right panel — outputs
    add_rect(sl, 6.5, 1.2, 6.4, 5.9, rgb(0xF5, 0xF5, 0xF5))
    add_text(sl, "Report Outputs", 6.7, 1.35, 6.0, 0.45, size=15, bold=True, color=GREEN)
    outputs = [
        "KPI dashboard (total reports, Evans signal count, top PRR)",
        "Disproportionality signal table with PRR, ROR, chi², signal strength",
        "PRR bar chart with 95% confidence intervals",
        "Temporal comparison table: ΔPRR pre/post cutoff year",
        "WHONET resistance summary: mean/min/max %R, annual trend",
        "ATLAS MIC50/MIC90 susceptibility charts",
        "Key findings (numbered, LLM-generated)",
        "Clinical interpretation with AMS committee recommendation",
        "AMS category breakdown chart (resistance, C. diff, organ injury, etc.)",
        "Draft disclaimer + senior pharmacist sign-off requirement",
    ]
    y = 1.95
    for out in outputs:
        add_rect(sl, 6.55, y + 0.12, 0.08, 0.08, GREEN)
        add_text(sl, out, 6.75, y, 6.0, 0.52, size=10.5, color=SLATE)
        y += 0.54

    # Example drug pair
    add_rect(sl, 0.4, 7.05, 12.5, 0.25, GREEN_LT)
    add_text(sl, "Example: cefazolin vs. cefpodoxime — 18 Evans-positive signals detected, PRR peak 4.31 (C. difficile infection)",
             0.55, 7.07, 12.2, 0.22, size=9.5, color=GREEN_DARK)

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 7: Utilization Analysis Module ──────────────────────────────────────
def slide_utilization(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "Module: Utilization Signal Detection", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    # Drug classes
    add_text(sl, "Monitored Drug Classes:", 0.5, 1.2, 12.0, 0.45, size=13, bold=True, color=GREEN)
    classes = [
        "Fluoroquinolones", "Carbapenems", "Vancomycin", "Cephalosporins (1G/3G)",
        "Piperacillin/Tazobactam", "Azithromycin", "Metronidazole", "TMP-SMX",
    ]
    x = 0.5
    for cls in classes:
        add_rect(sl, x, 1.75, 1.48, 0.38, GREEN_LT)
        add_text(sl, cls, x + 0.06, 1.8, 1.36, 0.3, size=9.5, bold=True, color=GREEN_DARK)
        x += 1.57

    # Two columns
    add_rect(sl, 0.4, 2.35, 6.0, 4.75, rgb(0xE8, 0xF5, 0xE9))
    add_text(sl, "Detection Methods", 0.6, 2.5, 5.6, 0.45, size=14, bold=True, color=GREEN)
    methods = [
        ("NHSN DOT/1000 PD trend", "Days of therapy per 1,000 patient-days — Z-score spike detection and sustained-high flagging."),
        ("Benchmark comparison", "National reference benchmarks per drug class — deviation % calculated quarterly."),
        ("FAERS cross-reference", "Concurrent adverse event signal detection for AMS-relevant reaction categories."),
        ("Anomaly scoring", "Composite score: spike severity × duration × signal correlation → critical / watch / routine."),
        ("Correlation flags", "Utilization spikes co-occurring with FAERS resistance signals trigger escalation alerts."),
    ]
    y = 3.05
    for title, body in methods:
        add_text(sl, title, 0.6, y, 5.6, 0.35, size=11.5, bold=True, color=GREEN_DARK)
        add_text(sl, body, 0.6, y + 0.33, 5.6, 0.5, size=10, color=SLATE)
        y += 0.92

    add_rect(sl, 6.7, 2.35, 6.2, 4.75, rgb(0xF5, 0xF5, 0xF5))
    add_text(sl, "Report Sections", 6.9, 2.5, 5.8, 0.45, size=14, bold=True, color=GREEN)
    sections = [
        "NHSN utilization trend chart with anomaly highlights",
        "Anomaly detail table: DOT/1000 PD vs benchmark, deviation %",
        "FAERS adverse event signal chart (Evans-positive reactions)",
        "AMS category breakdown (resistance, organ injury, C. diff)",
        "Utilization–signal correlation flags",
        "AMS committee plain-language summary (LLM-generated)",
        "Overall flag: CRITICAL / WATCH / ROUTINE with anomaly score",
        "Draft disclaimer for clinical review board",
    ]
    y = 3.05
    for s in sections:
        add_rect(sl, 6.75, y + 0.12, 0.08, 0.08, GREEN)
        add_text(sl, s, 6.95, y, 5.9, 0.48, size=10.5, color=SLATE)
        y += 0.55

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 8: Knowledge Vault & Command Center ─────────────────────────────────
def slide_vault_cmd(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "Knowledge Vault & Command Center", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    # Knowledge Vault
    add_rect(sl, 0.4, 1.2, 6.1, 5.9, rgb(0xE8, 0xF5, 0xE9))
    add_text(sl, "Knowledge Vault (RAG)", 0.6, 1.35, 5.7, 0.45,
             size=15, bold=True, color=GREEN)
    vault_items = [
        ("Guideline corpus", "IDSA/SHEA 2016 (Barlam), IDSA/SHEA 2007 (Dellit), ASHP-IDSA-SIDP-SCCM 2019,\nCDC Core Elements, ASHP Statement 2010, Surviving Sepsis 2021, IDSA Resistance Guidelines"),
        ("PubMed literature", "Live Entrez queries across 12 AMS topic categories (ICU stewardship, PK/PD,\nC. diff, resistance trends) — auto-chunked and embedded on ingestion"),
        ("Embedding model", "nomic-embed-text via Ollama — 768-dim vectors, cosine similarity, ChromaDB persistence"),
        ("Chunk strategy", "~512 tokens / chunk, 80-token overlap — balances retrieval precision with context coverage"),
        ("Query interface", "Top-k semantic search with doc_type filter — returns text, source, and similarity score"),
    ]
    y = 1.95
    for title, body in vault_items:
        add_text(sl, title, 0.6, y, 5.7, 0.35, size=11.5, bold=True, color=GREEN_DARK)
        add_text(sl, body, 0.6, y + 0.34, 5.7, 0.65, size=9.5, color=SLATE)
        y += 1.1

    # Command Center
    add_rect(sl, 6.7, 1.2, 6.2, 5.9, rgb(0x26, 0x32, 0x38))
    add_text(sl, "Command Center (CLI Interface)", 6.9, 1.35, 5.8, 0.45,
             size=15, bold=True, color=GREEN_LT)
    add_text(sl, "Terminal-style interface embedded in the Streamlit dashboard",
             6.9, 1.88, 5.8, 0.38, size=10, color=GREY, italic=True)

    commands = [
        ("run resistance <drug> vs <comparator>",  "Full FAERS + WHONET + ATLAS analysis → PDF"),
        ("run utilization <drug class>",            "NHSN trend + FAERS cross-reference → PDF"),
        ("ask <clinical question>",                 "RAG query over vault + LLM answer"),
        ("status",                                  "Show data source connectivity & analysis counts"),
        ("help",                                    "Display all available commands"),
    ]
    y = 2.5
    for cmd, desc in commands:
        add_rect(sl, 6.75, y, 5.9, 0.85, rgb(0x37, 0x47, 0x4F))
        add_text(sl, f"> {cmd}", 6.88, y + 0.04, 5.7, 0.38, size=9.5, bold=True,
                 color=rgb(0x80, 0xFF, 0x80))
        add_text(sl, desc, 6.88, y + 0.44, 5.7, 0.35, size=9, color=rgb(0xBB, 0xDE, 0xFB))
        y += 1.02

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 9: Antibiogram Upload ───────────────────────────────────────────────
def slide_antibiogram(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "Hospital Antibiogram Integration", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    add_text(sl,
             "AMS Intelligence accepts de-identified institutional antibiogram data for benchmarking against national surveillance sources.",
             0.5, 1.15, 12.3, 0.6, size=14, color=SLATE)

    features = [
        ("CSV Upload", "Upload CSV exports from clinical microbiology systems (WHONET-compatible format supported). Patient-de-identified data only.", rgb(0x01, 0x57, 0x9B)),
        ("Organism-Drug Matrix", "Interactive heatmap comparing institutional %S / %I / %R against WHONET global and ATLAS reference ranges.", GREEN),
        ("Resistance Gap Alerts", "Flags organisms where institutional resistance exceeds national benchmarks by user-configurable threshold (default: +15%).", AMBER),
        ("Temporal Tracking", "Year-over-year antibiogram comparison to identify emerging resistance trends within a single institution.", GREEN_DARK),
        ("FAERS Correlation", "Cross-references institutional high-resistance organisms against FAERS adverse event signals for the same drug class.", rgb(0x6A, 0x1B, 0x9A)),
        ("PDF Report", "Institution-specific resistance report with national benchmark overlay, suitable for P&T committee presentation.", SLATE),
    ]

    x, y = 0.4, 1.95
    for i, (title, desc, color) in enumerate(features):
        col = i % 2
        row = i // 2
        sx = x + col * 6.45
        sy = y + row * 1.7
        add_rect(sl, sx, sy, 6.2, 1.55, rgb(0xF9, 0xFB, 0xF9))
        add_rect(sl, sx, sy, 0.2, 1.55, color)
        add_text(sl, title, sx + 0.3, sy + 0.1, 5.7, 0.42, size=13, bold=True, color=color)
        add_text(sl, desc, sx + 0.3, sy + 0.55, 5.7, 0.85, size=10.5, color=SLATE)

    add_rect(sl, 0.4, 7.0, 12.5, 0.3, rgb(0xFF, 0xF8, 0xE1))
    add_text(sl,
             "Privacy: All uploaded data remains on-device. No institutional data transmitted to external servers.",
             0.6, 7.04, 12.1, 0.25, size=10, color=AMBER)

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 10: Technical Stack ─────────────────────────────────────────────────
def slide_tech(prs):
    sl = blank_slide(prs)
    fill_bg(sl, WHITE)
    add_rect(sl, 0, 0, 13.33, 1.0, GREEN)
    add_text(sl, "Technical Stack", 0.4, 0.15, 12.5, 0.7,
             size=28, bold=True, color=WHITE)

    categories = [
        ("AI / LLM", GREEN, [
            "gemma4:26b — reasoning, synthesis, key findings (256K context)",
            "gemma4:e4b — fast drafting, plain-language summaries",
            "nomic-embed-text — semantic embeddings (768-dim)",
            "Ollama — local LLM serving (GPU: RTX 5060 Ti 16 GB)",
            "LangChain LCEL — prompt chaining, ChatOllama integration",
            "think=False — disables chain-of-thought for efficiency",
        ]),
        ("Data & Analytics", rgb(0x01, 0x57, 0x9B), [
            "pandas / numpy — data manipulation and signal computation",
            "scipy — chi-squared test, Z-score anomaly detection",
            "matplotlib — embedded charts (PRR bars, trend lines, heatmaps)",
            "ChromaDB — persistent vector store for RAG vault",
            "requests — FAERS OpenFDA API, NCBI Entrez, Ollama HTTP",
            "NCBI Bio.Entrez — PubMed structured XML retrieval",
        ]),
        ("Application", rgb(0x6A, 0x1B, 0x9A), [
            "Streamlit — multi-page dashboard (port 8502)",
            "streamlit-authenticator — bcrypt session management",
            "fpdf2 — PDF report generation with embedded figures",
            "Pillow — badge/logo image generation",
            "Python 3.12 — async where needed",
            "Gateway dashboard (port 8500) linking PV + AMS workbenches",
        ]),
    ]

    x = 0.35
    for cat, color, items in categories:
        add_rect(sl, x, 1.2, 4.15, 6.0, rgb(0xF9, 0xFB, 0xF9))
        add_rect(sl, x, 1.2, 4.15, 0.6, color)
        add_text(sl, cat, x + 0.15, 1.28, 3.85, 0.45, size=14, bold=True, color=WHITE)
        y = 2.0
        for item in items:
            add_rect(sl, x + 0.12, y + 0.14, 0.07, 0.07, color)
            add_text(sl, item, x + 0.28, y, 3.75, 0.55, size=10.5, color=SLATE)
            y += 0.84
        x += 4.35

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Slide 11: Clinical Impact ─────────────────────────────────────────────────
def slide_impact(prs):
    sl = blank_slide(prs)
    fill_bg(sl, GREEN_DARK)
    add_rect(sl, 0, 0, 13.33, 0.08, GREEN)

    add_text(sl, "Clinical Impact", 0.6, 0.5, 12.0, 0.9,
             size=38, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    add_text(sl, "Designed by a practicing ICU pharmacist. Built for real AMS committee work.",
             0.6, 1.45, 12.0, 0.5, size=16, color=GREEN_LT)

    impacts = [
        ("Minutes, not hours", "Full resistance trend analysis — FAERS signals, WHONET resistance, ATLAS MIC trends, LLM interpretation, and PDF report — in under 3 minutes."),
        ("Evidence-based", "Every clinical interpretation cites ASHP/IDSA guidelines retrieved in real time from the local knowledge vault."),
        ("Committee-ready", "Plain-language AMS summaries generated by local LLM, formatted for P&T committee presentations without manual editing."),
        ("Zero data risk", "All computation on-device. FAERS queries use de-identified public data. Institutional antibiograms never leave the local machine."),
        ("Extensible", "New drug classes, data sources, and guideline documents added via CLI ingestion — no code changes required."),
    ]

    y = 2.15
    for title, body in impacts:
        add_rect(sl, 0.6, y, 11.8, 0.08, GREEN)
        add_text(sl, title, 0.6, y + 0.15, 3.8, 0.45, size=13, bold=True, color=GREEN_LT)
        add_text(sl, body, 4.55, y + 0.12, 7.8, 0.72, size=11.5, color=WHITE)
        y += 0.98

    # Bottom author
    add_rect(sl, 0.6, 7.0, 12.1, 0.28, rgb(0x2E, 0x7D, 0x32))
    add_text(sl,
             "Michael Olszewski, PharmD, BCPS, BCCCP  ·  Critical Care & Infectious Disease Pharmacist  ·  molszewski423@gmail.com",
             0.75, 7.03, 11.8, 0.24, size=10, color=WHITE, align=PP_ALIGN.CENTER)

    add_rect(sl, 0, 7.35, 13.33, 0.15, GREEN)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    prs = new_prs()
    slide_title(prs)
    slide_problem(prs)
    slide_overview(prs)
    slide_architecture(prs)
    slide_data_sources(prs)
    slide_resistance(prs)
    slide_utilization(prs)
    slide_vault_cmd(prs)
    slide_antibiogram(prs)
    slide_tech(prs)
    slide_impact(prs)
    prs.save(str(OUT))
    print(f"Saved: {OUT}  ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
