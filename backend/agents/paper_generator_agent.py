# backend/agents/paper_generator_agent.py

import os
import io
import datetime
import base64
import textwrap
import matplotlib.pyplot as plt

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
import numpy as np


# ------------------------
# HTML helper for Limitations
# ------------------------
def format_limitations_html(text):
    """Convert markdown-style limitations to proper HTML"""
    if not text:
        return "Will be expanded in later iterations."
    
    # Replace **text** with <strong>text</strong>
    while "**" in text:
        text = text.replace("**", "<strong>", 1)
        text = text.replace("**", "</strong>", 1)
    
    lines = text.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            if not in_list:
                html_lines.append('<ul style="margin-left: 20px; margin-top: 8px;">')
                in_list = True
            html_lines.append(f'<li>{line[2:]}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if line:
                html_lines.append(f'<p><strong>{line}</strong></p>' if line.endswith(':') else f'<p>{line}</p>')
    
    if in_list:
        html_lines.append('</ul>')
    
    return ''.join(html_lines)



# ================================================================
#                         MAIN AGENT
# ================================================================
async def paper_generator_agent(state):
    """
    Generates HTML + PDF + 3 visualizations:
        - Experiment Metrics Bar Chart  (already existed)
        - Word Frequency Bar Chart      (NEW)
        - TF-IDF PCA 2D Embedding Plot  (NEW)
    """

    logs = state.get("logs", [])
    job_id = state.get("job_id", "unknown")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)


    # ------------------------
    # State data extraction
    # ------------------------
    domains = state.get("domains") or []
    questions = state.get("questions") or []
    experiment = state.get("experiment") or {}
    critique = state.get("critique") or {}
    data_state = state.get("data") or []
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"


    # ------------------------
    # Title + Abstract
    # ------------------------
    domain_name = " / ".join([d.get("name") for d in domains[:2]]) if domains else "AI-Generated Research"
    title = f"Research Report: {domain_name}"

    experiment_summary = experiment.get("summary", "")

    # Generate a better abstract
    abstract = (
        f"This study explores the domain of {domain_name}. "
        f"The system generated research questions, collected public datasets, "
        f"performed lightweight exploratory experiments, and evaluated results using "
        f"a critic agent. Preliminary metrics include: {experiment.get('metrics', {})}. "
        f"Findings and limitations are summarized below."
    )


    # ---------------------------------------------------
    # METHODS SECTION – extract URLs used in data pipeline
    # ---------------------------------------------------
    methods_lines = []
    data_sources = []

    for q in data_state:
        for ds in q.get("datasets", []):
            url = ds.get("source_url") or ""
            if url and url not in data_sources:
                data_sources.append(url)

    if data_sources:
        methods_lines.append("Data sources collected:")
        for u in data_sources[:8]:
            methods_lines.append(f"- {u}")
    else:
        methods_lines.append("Data collected via arXiv, GitHub, Tavily, and local extraction.")


    # ---------------------------------------------------
    # RESULTS + METRICS
    # ---------------------------------------------------
    metrics = experiment.get("metrics", {})
    results_text = experiment_summary or "No experiment summary available."

    numeric_metrics = {}
    for k, v in metrics.items():
        try:
            numeric_metrics[k] = float(v)
        except:
            pass


    # ===============================================================
    #                     VISUALIZATION #1
    #           Experiment Metrics Bar Chart  (existing)
    # ===============================================================
    chart_path_1 = None
    chart_b64_1 = ""

    if numeric_metrics:
        try:
            labels = list(numeric_metrics.keys())
            vals = [numeric_metrics[l] for l in labels]

            plt.figure(figsize=(6,3))
            plt.bar(labels, vals)
            plt.title("Experiment Metrics")
            plt.ylabel("Value")
            plt.xticks(rotation=25, ha='right')
            plt.tight_layout()

            chart_path_1 = os.path.join(output_dir, f"{job_id}_metrics.png")
            plt.savefig(chart_path_1, dpi=150)
            plt.close()

            with open(chart_path_1, "rb") as fh:
                chart_b64_1 = base64.b64encode(fh.read()).decode("utf-8")

            logs.append(f"PaperGenerator: Chart 1 saved → {chart_path_1}")
        except Exception as e:
            logs.append(f"PaperGenerator: Chart 1 failed: {e}")


    # ===============================================================
    #                     VISUALIZATION #2
    #               Word Frequency Bar Chart (NEW)
    # ===============================================================
    chart_path_2 = None
    chart_b64_2 = ""
    corpus_text = ""

    # Collect text from all sources
    for q in data_state:
        for ds in q.get("datasets", []):
            snippet = ds.get("text_snippet", "")
            if snippet:
                corpus_text += " " + snippet

    if len(corpus_text) > 200:
        try:
            # Tokenize simple words
            import re
            words = re.findall(r"[A-Za-z]{4,}", corpus_text.lower())

            # Stopwords
            stopwords = {"this","that","have","with","from","their","there","which",
                         "been","were","also","into","these","those","using","used",
                         "because","while","within","where","when","then","than","however",
                         "analysis","algorithm","model","models","approach","data","research"}

            freq = {}
            for w in words:
                if w not in stopwords:
                    freq[w] = freq.get(w, 0) + 1

            # Take top 20
            sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:20]
            labels = [w for w, c in sorted_words]
            counts = [c for w, c in sorted_words]

            plt.figure(figsize=(7,4))
            plt.bar(labels, counts)
            plt.xticks(rotation=45, ha="right")
            plt.title("Top Word Frequencies in Collected Research Text")
            plt.tight_layout()

            chart_path_2 = os.path.join(output_dir, f"{job_id}_wordfreq.png")
            plt.savefig(chart_path_2, dpi=150)
            plt.close()

            with open(chart_path_2, "rb") as fh:
                chart_b64_2 = base64.b64encode(fh.read()).decode("utf-8")

            logs.append(f"PaperGenerator: Chart 2 saved → {chart_path_2}")

        except Exception as e:
            logs.append(f"PaperGenerator: Chart 2 failed: {e}")


    # ===============================================================
    #                     VISUALIZATION #3
    #              TF-IDF Embedding PCA Plot (NEW)
    # ===============================================================
    chart_path_3 = None
    chart_b64_3 = ""

    if len(corpus_text) > 500:
        try:
            docs = corpus_text.split(".")
            docs = [d.strip() for d in docs if len(d.strip()) > 30][:30]

            vectorizer = TfidfVectorizer(max_features=300)
            X = vectorizer.fit_transform(docs).toarray()

            pca = PCA(n_components=2)
            X2 = pca.fit_transform(X)

            plt.figure(figsize=(6,4))
            plt.scatter(X2[:,0], X2[:,1], alpha=0.7)
            plt.title("TF-IDF PCA Embedding of Extracted Text")
            plt.tight_layout()

            chart_path_3 = os.path.join(output_dir, f"{job_id}_embedding.png")
            plt.savefig(chart_path_3, dpi=150)
            plt.close()

            with open(chart_path_3, "rb") as fh:
                chart_b64_3 = base64.b64encode(fh.read()).decode("utf-8")

            logs.append(f"PaperGenerator: Chart 3 saved → {chart_path_3}")

        except Exception as e:
            logs.append(f"PaperGenerator: Chart 3 failed: {e}")



    # =======================================
    #              BUILD HTML
    # =======================================
    q_html = ""
    for q in questions:
        qtext = q.get("question", "")
        rationale = q.get("short_rationale", "")
        q_html += f"<li><b>{qtext}</b><br><small>{rationale}</small></li>"

    img_html_1 = f'<img src="data:image/png;base64,{chart_b64_1}" style="max-width:100%;">' if chart_b64_1 else ""
    img_html_2 = f'<img src="data:image/png;base64,{chart_b64_2}" style="max-width:100%;">' if chart_b64_2 else ""
    img_html_3 = f'<img src="data:image/png;base64,{chart_b64_3}" style="max-width:100%;">' if chart_b64_3 else ""

    html = f"""
    <html><head><meta charset='utf-8'>
    <title>{title}</title>
    <style>
      body {{ font-family: Arial; margin: 32px; }}
      h1 {{ color:#1a3d7c }}
      h2 {{ margin-top:28px }}
    </style>
    </head>
    <body>
    <h1>{title}</h1>
    <p><i>Generated: {timestamp}</i></p>

    <h2>Abstract</h2>
    <p>{abstract}</p>

    <h2>Research Questions</h2>
    <ul>{q_html}</ul>

    <h2>Methods</h2>
    {"".join(f"<p>{line}</p>" for line in methods_lines)}

    <h2>Results</h2>
    <p>{textwrap.fill(results_text, 400)}</p>

    {img_html_1}
    {img_html_2}
    {img_html_3}

    <h2>Critic Review</h2>
    <p><b>Verdict:</b> {"PASS" if critique.get("pass") else "FAIL"}</p>
    <p><b>Reason:</b> {critique.get("reason","")}</p>

    <h2>Limitations & Future Work</h2>
    {format_limitations_html(critique.get("future",""))}

    </body></html>
    """

    html_path = os.path.join(output_dir, f"{job_id}.html")
    with open(html_path, "w") as fh:
        fh.write(html)


    # =======================================
    #              BUILD PDF
    # =======================================
    pdf_path = os.path.join(output_dir, f"{job_id}.pdf")
    styles = getSampleStyleSheet()
    normal = styles['BodyText']
    title_style = ParagraphStyle("T", parent=styles['Title'], alignment=TA_CENTER)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"<i>Generated: {timestamp}</i>", normal))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Abstract", styles['Heading2']))
    story.append(Paragraph(abstract, normal))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Research Questions", styles['Heading2']))
    for q in questions:
        story.append(Paragraph("• " + q.get("question", ""), normal))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Methods", styles['Heading2']))
    for line in methods_lines:
        story.append(Paragraph(line, normal))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Results", styles['Heading2']))
    story.append(Paragraph(results_text, normal))

    # Insert images into PDF
    for path in [chart_path_1, chart_path_2, chart_path_3]:
        if path and os.path.exists(path):
            story.append(Spacer(1, 0.2*inch))
            img = RLImage(path)
            img.drawHeight = 3*inch
            img.drawWidth = 6*inch
            story.append(img)

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Critic Review", styles['Heading2']))
    story.append(Paragraph(f"Verdict: {'PASS' if critique.get('pass') else 'FAIL'}", normal))
    story.append(Paragraph(f"Reason: {critique.get('reason','')}", normal))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Limitations & Future Work", styles['Heading2']))
    for line in critique.get("future","").split("\n"):
        story.append(Paragraph(line, normal))

    doc.build(story)

    logs.append(f"PaperGenerator: Saved PDF → {pdf_path}")

    return {
        "logs": logs,
        "paper": {"html": html_path, "pdf": pdf_path},
        "results": {"html": html_path, "pdf": pdf_path}
    }
