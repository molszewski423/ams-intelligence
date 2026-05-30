"""
Generate LinkedIn project overview PDF for the Clinical Intelligence Portal.
"""

import sys
from pathlib import Path
from datetime import datetime
import io

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fpdf import FPDF

OUTPUT = Path("/home/mike/Desktop/Clinical_Intelligence_Portal_Overview.pdf")

BLUE      = (21, 101, 192)
BLUE_LT   = (227, 242, 253)
GREEN     = (46, 125, 50)
GREEN_LT  = (232, 245, 233)
AMBER     = (230, 119, 0)
AMBER_LT  = (255, 243, 224)
WHITE     = (255, 255, 255)
BLACK     = (33, 33, 33)
GREY      = (117, 117, 117)
GREY_LT   = (245, 245, 245)
DARK      = (26, 26, 46)


def s(text: str) -> str:
    return (
        str(text)
        .replace("—", "-").replace("–", "-")
        .replace("‘", "'").replace("’", "'")
        .replace("“", '"').replace("”", '"')
        .replace("•", "-").replace("·", "-")
        .encode("latin-1", errors="replace").decode("latin-1")
    )


class ProjectPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(14, 16, 14)
        self.set_auto_page_break(auto=True, margin=18)

    def normalize_text(self, text: str) -> str:
        return s(text)

    def header(self):
        self.set_xy(14, 4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*BLUE)
        self.cell(120, 5, s("Clinical Intelligence Portal"), ln=False)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*GREY)
        self.set_xy(145, 4)
        self.cell(51, 5, "Michael Olszewski, PharmD, BCPS, BCCCP", align="R", ln=False)
        self.set_xy(145, 9)
        self.cell(51, 4, f"Page {self.page_no()}", align="R")
        self.set_draw_color(*GREY)
        self.set_line_width(0.3)
        self.line(14, 14, 196, 14)
        self.set_draw_color(0, 0, 0)
        self.set_text_color(*BLACK)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*GREY)
        self.set_draw_color(*BLUE)
        self.set_line_width(0.3)
        self.line(14, self.get_y(), 196, self.get_y())
        self.set_xy(14, self.get_y() + 1)
        self.cell(100, 4, s("For professional overview only - Research & Development Portfolio"))
        self.cell(82, 4, f"Generated {datetime.now():%Y-%m-%d}", align="R")
        self.set_text_color(*BLACK)

    def section_header(self, number: str, title: str, color=BLUE):
        self.ln(5)
        self.set_draw_color(*color)
        self.set_line_width(0.5)
        self.line(14, self.get_y(), 196, self.get_y())
        self.ln(2)
        self.set_x(14)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*color)
        self.cell(182, 6, s(f"{number}  {title.upper()}"))
        self.set_text_color(*BLACK)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.ln(9)

    def subsection(self, title: str, color=BLUE):
        self.ln(3)
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*color)
        self.set_x(14)
        self.cell(182, 5, s(title))
        self.set_text_color(*BLACK)
        self.ln(6)

    def body(self, text: str, size: float = 9.0):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*BLACK)
        self.set_x(14)
        self.multi_cell(182, 4.8, s(text))
        self.ln(2)

    def bullet_list(self, items: list[str], indent: int = 6):
        self.set_font("Helvetica", "", 8.8)
        self.set_text_color(*BLACK)
        for item in items:
            self.set_x(14 + indent)
            self.cell(4, 5, "-")
            self.set_x(14 + indent + 4)
            self.multi_cell(182 - indent - 4, 5, s(item))

    def kpi_row(self, items: list[tuple]):
        n = len(items)
        w = 182 // n
        y0 = self.get_y()
        for i, (label, value, color) in enumerate(items):
            x0 = 14 + i * w
            self.set_draw_color(*GREY)
            self.set_line_width(0.3)
            self.rect(x0, y0, w - 3, 16)
            self.set_xy(x0 + 4, y0 + 2)
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*color)
            self.cell(w - 7, 7, s(str(value)))
            self.set_xy(x0 + 4, y0 + 9.5)
            self.set_font("Helvetica", "", 7.5)
            self.set_text_color(*GREY)
            self.cell(w - 7, 5, s(label))
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.set_text_color(*BLACK)
        self.set_y(y0 + 20)

    def two_col(self, left_items: list[str], right_items: list[str], title_l="", title_r=""):
        """Render two logical groups sequentially — avoids page-break positioning bugs."""
        if title_l:
            self.ln(2)
            self.set_x(14)
            self.set_font("Helvetica", "B", 8.5)
            self.set_text_color(*BLUE)
            self.cell(182, 5, s(title_l))
            self.set_text_color(*BLACK)
            self.ln(6)
        self.set_font("Helvetica", "", 8.5)
        for item in left_items:
            self.set_x(14)
            self.cell(4, 5, "-")
            self.set_x(18)
            self.multi_cell(178, 5, s(item))

        if title_r:
            self.ln(2)
            self.set_x(14)
            self.set_font("Helvetica", "B", 8.5)
            self.set_text_color(*BLUE)
            self.cell(182, 5, s(title_r))
            self.set_text_color(*BLACK)
            self.ln(6)
        self.set_font("Helvetica", "", 8.5)
        for item in right_items:
            self.set_x(14)
            self.cell(4, 5, "-")
            self.set_x(18)
            self.multi_cell(178, 5, s(item))
        self.ln(2)

    def tech_table(self, rows: list[tuple[str, str]], header: tuple[str, str] = ("Component", "Details")):
        self.set_draw_color(*GREY)
        self.set_line_width(0.3)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*BLUE)
        self.set_x(14)
        self.cell(55, 6, s(header[0]))
        self.cell(127, 6, s(header[1]))
        self.ln()
        self.line(14, self.get_y(), 196, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*BLACK)
        for i, (k, v) in enumerate(rows):
            self.set_x(14)
            self.set_font("Helvetica", "B", 8.5)
            self.set_text_color(*DARK)
            self.cell(55, 5.5, s(k))
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*BLACK)
            self.cell(127, 5.5, s(v))
            self.ln()
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.ln(3)

    def callout(self, text: str, color=BLUE, bg=BLUE_LT):
        self.ln(2)
        y0 = self.get_y()
        self.set_draw_color(*color)
        self.set_line_width(1.2)
        self.line(14, y0, 14, y0 + 2)   # placeholder — draw after knowing height
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self.set_xy(18, y0 + 1)
        self.set_font("Helvetica", "I", 8.5)
        self.set_text_color(*color)
        self.multi_cell(174, 5, s(text))
        y1 = self.get_y()
        # Draw left accent line now that we know height
        self.set_draw_color(*color)
        self.set_line_width(1.2)
        self.line(14, y0, 14, y1)
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self.set_text_color(*BLACK)
        self.set_y(y1 + 3)


def build():
    pdf = ProjectPDF()
    pdf.add_page()

    # ── Cover block ───────────────────────────────────────────────────────────
    pdf.set_y(22)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*BLUE)
    pdf.cell(182, 11, s("Clinical Intelligence Portal"))
    pdf.ln(12)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*DARK)
    pdf.cell(182, 6, s("Pharmacovigilance & Antimicrobial Stewardship Research Platform"))
    pdf.ln(8)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*GREY)
    pdf.cell(182, 5, s("Michael Olszewski, PharmD, BCPS, BCCCP  |  Critical Care & Infectious Disease Pharmacist"))
    pdf.set_text_color(*BLACK)
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.5)
    pdf.ln(8)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.2)
    pdf.ln(8)

    # ── Executive summary ─────────────────────────────────────────────────────
    pdf.section_header("01", "Project Overview")
    pdf.body(
        "The Clinical Intelligence Portal is a locally-deployed, privacy-preserving AI research platform "
        "purpose-built for clinical pharmacists and antimicrobial stewardship teams. It integrates two "
        "specialized workbenches - the PV AI Workbench for pharmacovigilance signal intelligence and the "
        "AMS Intelligence pipeline for antimicrobial stewardship research - into a unified, authenticated gateway. "
        "All AI inference runs entirely on-premises using locally-hosted large language models via Ollama, "
        "ensuring patient data never leaves the institution."
    )

    pdf.callout(
        "Design philosophy: institution-scale AI pharmacovigilance and stewardship without cloud dependency, "
        "subscription fees, or PHI exposure. Every analysis, summary, and report is generated locally.",
        color=BLUE, bg=BLUE_LT
    )

    pdf.kpi_row([
        ("Research modules", "8+", BLUE),
        ("Data sources integrated", "6", GREEN),
        ("LLM parameters on-device", "26B+", AMBER),
        ("Patient data leaves server", "Zero", GREEN),
    ])

    # ── Platform components ───────────────────────────────────────────────────
    pdf.section_header("02", "Platform Components")

    pdf.subsection("A. PV AI Workbench (Port 8501)", BLUE)
    pdf.body(
        "A full-featured pharmacovigilance signal detection and regulatory intelligence platform. "
        "Designed for daily use by drug safety pharmacists and PV teams managing signal workflows."
    )
    pdf.two_col(
        left_items=[
            "FAERS disproportionality analysis (PRR, ROR, BCPNN, Omega)",
            "Temporal signal trend visualization across reporting years",
            "VigiBase, EMA EVDAS, and Yellow Card signal surveillance",
            "Regulatory document Q&A (FDA, EMA, ICH guidelines via RAG)",
            "Literature signal monitoring with PubMed auto-ingestion",
        ],
        right_items=[
            "Causality assessment (WHO-UMC scale, Naranjo algorithm)",
            "Drug-drug interaction network graph analysis",
            "MedDRA coding assistance via local LLM",
            "ICSR individual case review and narrative generation",
            "Full PDF report generation for all analyses",
        ],
        title_l="Signal Detection & Analysis",
        title_r="Clinical Decision Support",
    )

    pdf.ln(2)
    pdf.subsection("B. AMS Intelligence (Port 8502)", GREEN)
    pdf.body(
        "A specialized antimicrobial stewardship research pipeline that cross-references FAERS adverse "
        "event signals with NHSN utilization data and external resistance surveillance databases to "
        "generate actionable AMS committee insights."
    )
    pdf.two_col(
        left_items=[
            "FAERS PRR/ROR disproportionality with Evans criteria",
            "Pre/post formulary change temporal comparison",
            "NHSN DOT/1000 patient-days trend analysis",
            "WHONET and ATLAS MIC surveillance integration",
            "C. difficile and resistance-driven anomaly flagging",
        ],
        right_items=[
            "ASHP/IDSA/CDC guideline RAG (ChromaDB knowledge vault)",
            "PubMed literature integration across 12 AMS topics",
            "Plain-language P&T committee summaries (local LLM)",
            "Multi-page PDF reports with embedded matplotlib charts",
            "Command-line interface for rapid analyses",
        ],
        title_l="Resistance & Signal Analysis",
        title_r="Stewardship Intelligence",
    )

    pdf.ln(2)
    pdf.subsection("C. Clinical Intelligence Gateway (Port 8500)", BLUE)
    pdf.body(
        "Authenticated portal providing unified access to both workbenches with real-time platform "
        "health monitoring, role-based access control, and quick reference documentation."
    )

    # ── Data sources ──────────────────────────────────────────────────────────
    pdf.section_header("03", "Integrated Data Sources")

    pdf.tech_table([
        ("FAERS (FDA)",        "Live OpenFDA API - adverse event reaction counts, disproportionality analysis across all approved drugs"),
        ("NHSN (CDC)",         "Antimicrobial Use & Resistance module - DOT/1000 patient-days by drug class and facility type"),
        ("WHONET",             "WHO resistance surveillance database - organism-antibiotic susceptibility rates and MIC distributions"),
        ("ATLAS (Pfizer)",     "Global antimicrobial testing leadership database - MIC creep tracking and susceptibility trends"),
        ("PubMed / NCBI",      "Live E-utilities API - 12 curated AMS query sets, abstract and MeSH ingestion into ChromaDB vault"),
        ("ASHP/IDSA/CDC",      "Curated guideline corpus ingested as vector embeddings: 2007, 2016, 2019 AMS guidelines + CDC Core Elements"),
        ("VigiBase / EMA",     "WHO pharmacovigilance database and EMA signal surveillance integration (PV Workbench)"),
    ], header=("Data Source", "Description & Integration Method"))

    pdf.callout(
        "All file-based sources (NHSN, WHONET, ATLAS) use intelligent demo data fallback when real institutional "
        "data files are absent, allowing full functionality out-of-the-box without data export workflows.",
        color=GREEN, bg=GREEN_LT
    )

    # ── Technical architecture ────────────────────────────────────────────────
    pdf.section_header("04", "Technical Architecture")

    pdf.subsection("AI / LLM Stack", BLUE)
    pdf.tech_table([
        ("Reasoning Model",    "gemma4:26b - signal interpretation, AMS summaries, clinical Q&A, regulatory analysis"),
        ("Code/Pipeline Model","qwen3:30b - structured data extraction, JSON output, pipeline orchestration"),
        ("Embeddings Model",   "nomic-embed-text - document chunking, semantic search, RAG retrieval"),
        ("Inference Server",   "Ollama v0.6+ running locally on RTX 5060 Ti (16 GB VRAM)"),
        ("Orchestration",      "LangChain LCEL (ChatOllama + ChatPromptTemplate + StrOutputParser chains)"),
        ("Vector Database",    "ChromaDB persistent collection (cosine similarity, HNSW index)"),
    ])

    pdf.subsection("Application Stack", BLUE)
    pdf.tech_table([
        ("Frontend",           "Streamlit 1.45+ multi-page application with custom theming and authenticated routing"),
        ("Authentication",     "streamlit-authenticator 0.4.2 with bcrypt password hashing and secure cookie sessions"),
        ("Signal Analysis",    "Custom PRR/ROR/chi-squared engine with Evans criteria, log-normal 95% CIs, continuity correction"),
        ("PDF Generation",     "fpdf2 with embedded matplotlib charts (PNG via BytesIO), latin-1 safe unicode sanitization"),
        ("Data Processing",    "pandas, numpy, scipy - cohort filtering, temporal analysis, statistical tests"),
        ("Public Access",      "Cloudflare Quick Tunnels (trycloudflare.com) - no account or domain required"),
    ])

    pdf.subsection("Repository Structure", BLUE)
    pdf.body(
        "ams-intelligence/             AMS pipeline project root\n"
        "  src/\n"
        "    config.py                 Central configuration (models, paths, API endpoints)\n"
        "    auth.py                   Authentication gate (bcrypt + cookie sessions)\n"
        "    data_sources/             FAERS, NHSN, WHONET, ATLAS, PubMed clients\n"
        "    modules/                  resistance_analyzer.py, utilization_detector.py\n"
        "    shared/                   disproportionality.py, pdf_exporter.py, vault_ingestor.py\n"
        "    dashboard/                app.py (home), pages/1_Resistance_Trends.py, 2_Utilization_Signals.py, 3_Files.py\n"
        "  scripts/                    ingest_vault.py, generate_linkedin_pdf.py\n"
        "  data/                       nhsn/, whonet/, atlas/ (CSV files; demo fallback if absent)\n"
        "  output/                     Auto-generated PDF reports\n"
        "  chroma_db/                  Persistent vector store\n"
        "\n"
        "pv-workbench/                 PV Workbench project (parallel structure)\n"
        "ams-gateway/                  Gateway dashboard project (port 8500)"
    )

    # ── Clinical methodology ──────────────────────────────────────────────────
    pdf.section_header("05", "Clinical Methodology")

    pdf.subsection("Disproportionality Signal Detection", BLUE)
    pdf.body(
        "The platform implements the Evans criteria for FAERS pharmacovigilance signal detection, "
        "the same methodology used by regulatory agencies worldwide:"
    )
    pdf.bullet_list([
        "Proportional Reporting Ratio (PRR): ratio of drug-reaction co-occurrence to background rate. "
        "Signal threshold: PRR >= 2.0 (at least twice the background reporting rate).",
        "Reporting Odds Ratio (ROR): case-control analogue with 95% CI using log-normal approximation. "
        "Signal requires lower bound of 95% CI > 1.0.",
        "Chi-squared test (Yates-corrected): statistical significance threshold chi-sq >= 4.0 (p ~0.045). "
        "Continuity correction applied when background count = 0.",
        "Evans criteria: all three must be simultaneously met (PRR >= 2.0, N >= 3, chi-sq >= 4.0) to call a signal.",
        "Temporal analysis: pre/post formulary-change comparison quantifies delta-PRR to identify emerging signals.",
    ])

    pdf.ln(2)
    pdf.subsection("Utilization Signal Detection", GREEN)
    pdf.body("NHSN DOT/1000 patient-days trend analysis with statistical anomaly flagging:")
    pdf.bullet_list([
        "Z-score anomaly detection: periods > mean + 2 SD flagged as 'spike'.",
        "Benchmark deviation: >25% above national benchmark flagged as 'sustained_high'.",
        "Cross-reference: utilization anomaly years correlated with FAERS signal emergence years.",
        "Composite anomaly score (0-1): normalized proportion of anomalous periods, caps at 1.0.",
        "Overall risk tier: 'critical' (score > 0.5 or > 8 signals), 'watch', or 'routine'.",
    ])

    pdf.ln(2)
    pdf.subsection("Knowledge Vault - Retrieval-Augmented Generation", BLUE)
    pdf.body(
        "Guideline documents are chunked (512-token target, 80-token overlap), embedded via "
        "nomic-embed-text, and stored in ChromaDB. At query time, the top-k semantically similar "
        "chunks are retrieved and injected into the LLM context window, grounding responses in "
        "ASHP/IDSA/CDC recommendations rather than model training data alone."
    )
    pdf.bullet_list([
        "IDSA/SHEA 2016 Implementing an Antibiotic Stewardship Program (Barlam et al., CID 2016)",
        "IDSA/SHEA 2007 Guidelines for Developing an Institutional AMS Program (Dellit et al., CID 2007)",
        "ASHP-IDSA-SIDP-SCCM 2019 Implementing Antibiotic Stewardship in Health Systems (AJHP 2019)",
        "CDC Core Elements of Hospital Antibiotic Stewardship Programs (2019 edition)",
        "ASHP Statement on the Pharmacist's Role in Antimicrobial Stewardship (AJHP 2010)",
        "Surviving Sepsis Campaign 2021 - Antimicrobial Management section",
        "IDSA Antimicrobial Resistance Guidelines - key resistance mechanisms and clinical implications",
        "PubMed literature: 300+ articles across 12 AMS topic queries (2019-present, live API)",
    ])

    # ── LLM prompt engineering ────────────────────────────────────────────────
    pdf.ln(2)
    pdf.subsection("LLM Prompt Engineering & Clinical Safety", AMBER)
    pdf.body(
        "Each LLM chain uses a structured system prompt positioning the model as a board-certified "
        "clinical pharmacist. Key design decisions:"
    )
    pdf.bullet_list([
        "System prompts enforce clinical framing: confounding by indication, mechanistic plausibility, "
        "evidence hierarchy, and actionable AMS recommendations.",
        "Temperature = 0.05 (near-deterministic) for reproducible clinical outputs.",
        "Structured output parsing: key_findings as JSON array, INTERPRETATION paragraph separately parsed.",
        "All PDF reports include a prominent DRAFT disclaimer requiring senior pharmacist and P&T committee sign-off.",
        "LLM fallback: all analyses complete without LLM; summaries gracefully degrade to data tables.",
    ])

    # ── Impact & applications ─────────────────────────────────────────────────
    pdf.section_header("06", "Clinical Applications & Impact")

    pdf.two_col(
        left_items=[
            "Formulary switch analysis: quantify safety signal change after substituting one antibiotic for another",
            "C. difficile risk correlation: identify high-use periods preceding CDI rate spikes",
            "Carbapenem stewardship: flag DOT anomalies and cross-reference with CRE signal emergence",
            "Vancomycin AUC monitoring program evaluation: track nephrotoxicity signal trends",
            "Fluoroquinolone restriction policy impact: pre/post PRR comparison for tendinopathy, CDAD",
            "ICU de-escalation auditing: monitor broad-spectrum use and de-escalation signal patterns",
        ],
        right_items=[
            "P&T committee reporting: automated plain-language summaries with data citations",
            "Pharmacist education: real signal cases with PRR/ROR context for stewardship training",
            "Research hypothesis generation: identify novel drug-outcome associations for further study",
            "Drug shortage planning: identify therapeutic alternatives with comparable safety profiles",
            "NHSN AUR module benchmarking: compare DOT against national comparators with statistical flagging",
            "Regulatory submission support: structured signal narrative with temporal analysis for safety reports",
        ],
        title_l="AMS & Formulary Applications",
        title_r="Institutional & Research Applications",
    )

    pdf.callout(
        "This platform was developed to bridge the gap between high-volume FAERS data and actionable "
        "antimicrobial stewardship decisions. As a critical care pharmacist with BCPS and BCCCP "
        "certifications, I designed each module to reflect real-world AMS workflows - from prospective "
        "audit cycles to P&T committee reporting - with clinical rigor as the first priority.",
        color=BLUE, bg=BLUE_LT
    )

    # ── Skills demonstrated ───────────────────────────────────────────────────
    pdf.section_header("07", "Skills & Technologies Demonstrated")

    pdf.tech_table([
        ("Clinical Pharmacy",  "Antimicrobial stewardship, pharmacovigilance, PK/PD, ICU clinical decision-making"),
        ("AI / LLM",           "Local LLM deployment (Ollama), LangChain LCEL orchestration, RAG pipeline design, prompt engineering"),
        ("Data Science",       "Statistical signal detection (PRR/ROR), temporal analysis, anomaly detection, Python/pandas/numpy"),
        ("Software Dev",       "Full-stack Streamlit applications, REST API clients, PDF generation, ChromaDB vector database"),
        ("Data Integration",   "Multi-source API orchestration (FDA/NCBI/NHSN), file-based ETL with intelligent fallback"),
        ("Privacy & Security", "On-premises AI deployment, bcrypt authentication, zero PHI cloud exposure architecture"),
        ("Visualization",      "matplotlib chart embedding in PDFs, Streamlit interactive dashboards, data tables"),
        ("DevOps",             "Process management, Cloudflare tunneling, multi-service orchestration on single GPU server"),
    ])

    # ── Contact ───────────────────────────────────────────────────────────────
    pdf.section_header("08", "About the Developer")

    pdf.body(
        "Michael Olszewski, PharmD, BCPS, BCCCP is a clinical pharmacist specializing in critical care "
        "and infectious diseases with board certifications in Pharmacotherapy (BCPS) and Critical Care "
        "Pharmacy (BCCCP). With extensive ICU clinical experience, he developed the Clinical Intelligence "
        "Portal to apply modern AI and data science methods to real pharmacovigilance and antimicrobial "
        "stewardship challenges."
    )
    pdf.ln(2)
    pdf.body(
        "This platform represents the intersection of deep clinical expertise and applied data science - "
        "every feature was designed with a specific clinical workflow in mind, from the Evans criteria "
        "implementation to the P&T committee-ready report format. The project is actively developed "
        "and open for collaboration with pharmacy, medical informatics, and data science teams."
    )

    pdf.ln(4)
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.5)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.2)
    pdf.ln(4)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*BLUE)
    pdf.cell(182, 5, s("Contact & Collaboration"))
    pdf.ln(7)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BLACK)
    pdf.cell(182, 5, s("Email: molszewski423@gmail.com  |  LinkedIn: linkedin.com/in/michael-olszewski-pharmd"))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT))
    print(f"PDF saved: {OUTPUT}")
    print(f"Size: {OUTPUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    build()
