# pdf_generator.py
import os
import datetime
import base64
import textwrap
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA

import re
from bs4 import BeautifulSoup


# ---------------------------------------------------------
# REMOVE ALL HTML AND HEADING MARKERS (critical for PDF safety)
# ---------------------------------------------------------
def strip_html(text):
    """Remove headings like H1:, H2:, markdown, and HTML so ReportLab never errors."""
    if not text:
        return ""
    
    try:
        # Use BeautifulSoup to get raw text
        soup = BeautifulSoup(text, "html.parser")
        txt = soup.get_text(separator="\n")
        
        # --- Start regex cleaning ---
        
        # CRITICAL FIX: Remove headings like "H1:", "/H1", "'H1'" etc.
        # This regex looks for H1-H6 that might be preceded by a space, slash, quote, or start-of-line
        # Replaces with a space to prevent words from merging.
        # NEW LINE:
        txt = re.sub(r"(^|\s|/|'|\")(H[1-6]|P\d+)\b[:.]?\s*", " ", txt, flags=re.IGNORECASE)
        
        # Remove markdown headers (# ## ###)
        txt = re.sub(r"^#+\s*", "", txt, flags=re.MULTILINE)
        
        # Remove bold markers ** ** or __ __
        txt = txt.replace("**", "").replace("__", "")
        
        # Collapse excessive whitespace
        txt = re.sub(r"\s+", " ", txt).strip()
        
        return txt
        
    except Exception:
        # Fallback to regex-only cleaning if BeautifulSoup fails
        txt = re.sub(r"<[^>]+>", "", text) # Remove HTML
        
        # CRITICAL FIX: Remove headings like "H1:", "/H1", "'H1'" etc.
        # NEW LINE:
        txt = re.sub(r"(^|\s|/|'|\")(H[1-6]|P\d+)\b[:.]?\s*", " ", txt, flags=re.IGNORECASE)
        
        txt = re.sub(r"^#+\s*", "", txt, flags=re.MULTILINE) # Remove #
        txt = txt.replace("**", "").replace("__", "") # Remove bold
        txt = re.sub(r"\s+", " ", txt).strip() # Collapse whitespace
        return txt


# ---------------------------------------------------------
# HTML renderer for web (allowed HTML only)
# ---------------------------------------------------------
def format_limitations_html(text):
    if not text:
        return "<p>Will be expanded later.</p>"

    # Convert markdown bold
    while "**" in text:
        text = text.replace("**", "<strong>", 1)
        text = text.replace("**", "</strong>", 1)

    lines = text.split("\n")
    html = []
    in_list = False

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("- "):
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{s[2:]}</li>")
        else:
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<p>{s}</p>")

    if in_list:
        html.append("</ul>")

    return "".join(html)


# ---------------------------------------------------------
# CLEAN bullet points for PDF
# ---------------------------------------------------------
def format_limitations_text(text):
    if not text:
        return ["Will be expanded later."]
    lines = []
    for line in strip_html(text).split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("- "):
            lines.append("• " + s[2:])
        else:
            lines.append(s)
    return lines


# ---------------------------------------------------------
# Helper for Base64 images
# ---------------------------------------------------------
def encode_img(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ---------------------------------------------------------
# MAIN AGENT
# ---------------------------------------------------------
async def paper_generator_agent(state):

    logs = state.get("logs", [])
    job_id = state.get("job_id", "report")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    domains = state.get("domains", [])
    questions = state.get("questions", [])
    experiment = state.get("experiment", {})
    critique = state.get("critique", {})
    data_state = state.get("data", [])

    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    # -----------------------------------------------------
    # TITLE + ABSTRACT
    # -----------------------------------------------------
    domain_name = " / ".join([d.get("name", "") for d in domains[:2]]) or "AI Research"
    title = f"Research Report: {domain_name}"

    abstract = experiment.get("summary") or (
        f"This study explores the domain of {domain_name} using automated research agents. "
        "It generates questions, collects datasets, performs experiments, and produces critique."
    )

    abstract_clean = strip_html(abstract)

    # ADD THESE TWO DEBUG LINES HERE:
    print("DEBUG ABSTRACT:", repr(abstract_clean[:200]))
    print("DEBUG CRITIQUE:", repr(critique.get("future","")[:200]))

    # -----------------------------------------------------
    # METHODS
    # -----------------------------------------------------
    methods_lines = []
    urls = []

    for q in data_state:
        for ds in q.get("datasets", []):
            u = ds.get("source_url")
            if u and u not in urls:
                urls.append(u)

    if urls:
        methods_lines.append("Data sources used:")
        for u in urls[:8]:
            methods_lines.append(f"- {u}")
    else:
        methods_lines.append("Data retrieved from arXiv, GitHub, Tavily, and parsed documents.")

    # -----------------------------------------------------
    # RESULTS
    # -----------------------------------------------------
    results_text = experiment.get("summary", "No experiment summary.")
    results_clean = strip_html(results_text)

    metrics = experiment.get("metrics", {})
    numeric_metrics = {}
    for k, v in metrics.items():
        try:
            numeric_metrics[k] = float(v)
        except:
            pass

    # -----------------------------------------------------
    # VISUALIZATIONS
    # -----------------------------------------------------
    chart1 = chart2 = chart3 = None
    b64_1 = b64_2 = b64_3 = ""

    corpus = ""
    for q in data_state:
        for ds in q.get("datasets", []):
            txt = ds.get("text_snippet", "")
            if txt:
                corpus += " " + txt

    # 1 — Metrics Chart
    if numeric_metrics:
        plt.figure(figsize=(6,3))
        plt.bar(list(numeric_metrics.keys()), list(numeric_metrics.values()))
        plt.xticks(rotation=25)
        plt.tight_layout()
        chart1 = f"{output_dir}/{job_id}_metrics.png"
        plt.savefig(chart1, dpi=150)
        plt.close()
        b64_1 = encode_img(chart1)

    # 2 — Word Frequency
    if len(corpus) > 200:
        import re
        words = re.findall(r"[A-Za-z]{4,}", corpus.lower())
        stop = {"this","that","with","from","used","using","data","model","research"}
        freq = {}
        for w in words:
            if w not in stop:
                freq[w] = freq.get(w, 0) + 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:20]
        if top:
            plt.figure(figsize=(6,4))
            plt.bar([w for w,_ in top], [c for _,c in top])
            plt.xticks(rotation=45)
            plt.tight_layout()
            chart2 = f"{output_dir}/{job_id}_freq.png"
            plt.savefig(chart2, dpi=150)
            plt.close()
            b64_2 = encode_img(chart2)

    # 3 — TF-IDF PCA
    if len(corpus) > 400:
        docs = [d.strip() for d in corpus.split(".") if len(d.strip()) > 30][:25]
        X = TfidfVectorizer(max_features=200).fit_transform(docs).toarray()
        X2 = PCA(n_components=2).fit_transform(X)
        plt.figure(figsize=(5,4))
        plt.scatter(X2[:,0], X2[:,1])
        plt.tight_layout()
        chart3 = f"{output_dir}/{job_id}_pca.png"
        plt.savefig(chart3, dpi=150)
        plt.close()
        b64_3 = encode_img(chart3)

    # -----------------------------------------------------
    # HTML OUTPUT (FOR FRONTEND)
    # -----------------------------------------------------
    q_html = "".join(
        f"<li><b>{strip_html(q.get('question',''))}</b><br><small>{strip_html(q.get('short_rationale',''))}</small></li>"
        for q in questions
    )

    html = f"""
    <html><body>
    <h1>{strip_html(title)}</h1>
    <p><i>Generated: {timestamp}</i></p>

    <h2>Abstract</h2>
    <p>{strip_html(abstract)}</p>

    <h2>Research Questions</h2>
    <ul>{q_html}</ul>

    <h2>Methods</h2>
    {"".join(f"<p>{strip_html(m)}</p>" for m in methods_lines)}

    <h2>Results</h2>
    <p>{strip_html(results_text)}</p>

    <img src="data:image/png;base64,{b64_1}" />
    <img src="data:image/png;base64,{b64_2}" />
    <img src="data:image/png;base64,{b64_3}" />

    <h2>Critic Review</h2>
    <p><b>Verdict:</b> {"PASS" if critique.get("pass") else "FAIL"}</p>
    <p><b>Reason:</b> {strip_html(critique.get("reason",""))}</p>

    <h2>Limitations & Future Work</h2>
    {format_limitations_html(critique.get("future",""))}

    </body></html>
    """

    html_path = f"{output_dir}/{job_id}.html"
    with open(html_path, "w") as f:
        f.write(html)

    # -----------------------------------------------------
    # PDF OUTPUT (NO HTML ANYWHERE - EVERY TEXT CLEANED)
    # -----------------------------------------------------
    pdf_path = f"{output_dir}/{job_id}.pdf"

    styles = getSampleStyleSheet()
    normal = styles["BodyText"]

    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], alignment=TA_CENTER
    )

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)

    story = []
    story.append(Paragraph(strip_html(title), title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Generated: {timestamp}", normal))

    # Abstract
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Abstract", styles["Heading2"]))
    story.append(Paragraph(strip_html(abstract), normal))

    # Questions
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Research Questions", styles["Heading2"]))
    for q in questions:
        q_text = strip_html(q.get("question",""))
        story.append(Paragraph("• " + q_text, normal))
        # Also clean rationale if present
        rationale = strip_html(q.get("short_rationale", ""))
        if rationale:
            story.append(Paragraph(rationale, normal))

    # Methods
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Methods", styles["Heading2"]))
    for m in methods_lines:
        story.append(Paragraph(strip_html(m), normal))

    # Results
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Results", styles["Heading2"]))
    story.append(Paragraph(strip_html(results_clean), normal))

    # Images
    for chart in [chart1, chart2, chart3]:
        if chart and os.path.exists(chart):
            story.append(Spacer(1, 0.2*inch))
            img = RLImage(chart)
            img.drawWidth = 5.5 * inch
            img.drawHeight = 3 * inch
            story.append(img)

    # Critic Review
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Critic Review", styles["Heading2"]))
    verdict = "PASS" if critique.get("pass") else "FAIL"
    story.append(Paragraph(f"Verdict: {verdict}", normal))
    story.append(Paragraph(f"Reason: {strip_html(critique.get('reason',''))}", normal))

    # Limitations
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Limitations & Future Work", styles["Heading2"]))
    for line in format_limitations_text(critique.get("future","")):
        story.append(Paragraph(strip_html(line), normal))

    doc.build(story)

    logs.append(f"Saved PDF → {pdf_path}")

    return {
        "logs": logs,
        "paper": {"html": html_path, "pdf": pdf_path},
        "results": {"html": html_path, "pdf": pdf_path}
    }