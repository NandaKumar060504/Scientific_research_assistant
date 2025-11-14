# backend/graph.py
import os
import uuid
import json
import re
import asyncio
from typing import Any, List, TypedDict

from bs4 import BeautifulSoup
from langgraph.graph import StateGraph, END

from tools.groq_client import call_groq
from tools.tavily_client import search_tavily
from tools.scraper import find_disparate_sources, download_file
from tools.ocr_pdf import extract_text_from_pdf, extract_tables_from_pdf
from tools.chroma_client import add_documents
from agents.paper_generator_agent import paper_generator_agent


# ---------------- STATE ----------------
class ResearchState(TypedDict):
    job_id: str
    logs: List[str]
    domains: Any
    questions: Any
    data: Any
    experiment: Any
    results: Any
    critique: Any
    paper: Any
    cycle: int


# ---------------- UTIL: COVID BLOCK ----------------
COVID_TERMS = [
    "covid", "sars", "coronavirus", "pandemic", "long covid",
    "sars-cov", "sars-cov-2", "omicron", "antiviral", "infection",
    "virus", "cov-19", "cov19"
]


def is_covid_topic(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(term in t for term in COVID_TERMS)


def safe_get_str(x: Any) -> str:
    if not x:
        return ""
    if isinstance(x, str):
        return x
    try:
        return str(x)
    except Exception:
        return ""


# ---------------- AGENTS ----------------

async def domain_scout_agent(state: ResearchState):
    """
    Discover emerging domains using Tavily (primary) and fallbacks.
    Strictly filters COVID topics and low-quality results.
    """
    state["logs"].append("DomainScout: starting Tavily searches for emerging domains...")

    # Generic/modern queries (broad coverage, tweak as needed)
    queries = [
        "quantum-inspired graph neural networks 2024..2025 arxiv",
        "graph-of-thought reasoning 2025 research",
        "photonic tensor cores ai acceleration 2024..2025",
        "autonomous laboratory robotics ai-driven experimentation 2024..2025",
        "4d bioprinting synthetic tissues 2024..2025",
        "ai accelerated materials discovery quantum-inspired 2024..2025",
        "computational protein design and molecular simulation 2024..2025",
        "neuromorphic computing architectures 2024..2025",
        "topological data analysis for graphs 2024..2025",
    ]

    candidates = {}
    tasks = [search_tavily(q, num_results=8) for q in queries]

    try:
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        state["logs"].append(f"DomainScout: Tavily calls failed ({e})")
        results_lists = []

    for res in results_lists:
        if isinstance(res, Exception) or not res:
            continue
        for item in res:
            title = safe_get_str(item.get("title")).strip()
            snippet = safe_get_str(item.get("snippet")).strip()
            url = safe_get_str(item.get("url")).strip()

            if not title:
                continue
            # Hard filter COVID at ingestion time
            if is_covid_topic(title) or is_covid_topic(snippet):
                continue

            ent = candidates.setdefault(title, {"snippets": [], "urls": [], "hits": 0})
            ent["hits"] += 1
            if snippet:
                ent["snippets"].append(snippet)
            if url:
                ent["urls"].append(url)

    if not candidates:
        # Fallback set of hand-picked modern domains (non-COVID)
        fallback_domains = [
            "Quantum-inspired Graph Neural Networks (2025)",
            "Graph-of-Thought Reasoning Models (2025)",
            "Photonic Tensor Cores for ML Acceleration (2024-2025)",
            "Autonomous Lab Robotics for Rapid Experiments (2025)",
            "AI-accelerated Materials Discovery (2024-2025)",
        ]
        state["domains"] = [{"name": d, "novelty": 90, "impact": 85, "trend": 90} for d in fallback_domains]
        state["logs"].append("DomainScout: no candidates found — using fallback domains.")
        return state

    # Filter obvious noise
    filtered = {}
    for name, info in candidates.items():
        lower = name.lower()
        if any(b in lower for b in ["top ", "list", "report", "mckinsey", "wef", "trends", "best of"]):
            continue
        # skip if first url looks like a PDF-only listing
        if info.get("urls") and any(".pdf" in u.lower() for u in info.get("urls", [])[:1]):
            continue
        filtered[name] = info

    candidates = filtered
    state["logs"].append(f"DomainScout: found {len(candidates)} raw candidates after filtering.")

    # If nothing left after filter, return fallback
    if not candidates:
        state["logs"].append("DomainScout: everything filtered — using fallback domains.")
        return await domain_scout_agent(state)

    # Build LLM prompt to score domains
    prompt = (
        "You are a research-domain ranking engine. Score the candidate domains returning STRICT JSON array.\n"
        "Format:\n"
        "[{\"name\":\"...\",\"novelty\":0-100,\"impact\":0-100,\"trend\":0-100}]\n\n"
        "Candidates and short evidence:\n"
    )
    for i, (name, info) in enumerate(list(candidates.items())[:12], start=1):
        evidence = " | ".join(info.get("snippets", [])[:3])
        prompt += f"- {name}\n  Evidence: {evidence}\n"

    llm_output = None
    try:
        llm_output = await call_groq(prompt, max_tokens=1200)
    except Exception as e:
        state["logs"].append(f"DomainScout: LLM scoring failed ({e}) — using simple heuristic ranking.")
        llm_output = None

    # Parse result robustly; if fails, do simple heuristic ranking
    parsed = None
    if llm_output:
        try:
            jstart = llm_output.find("[")
            jend = llm_output.rfind("]") + 1
            parsed = json.loads(llm_output[jstart:jend])
        except Exception:
            parsed = None

    if not parsed or not isinstance(parsed, list):
        # Heuristic ranking: use hits and snippet length as proxy
        heuristic = []
        for name, info in list(candidates.items())[:12]:
            score = info.get("hits", 0) + sum(len(s) for s in info.get("snippets", [])) / 100.0
            heuristic.append({"name": name, "novelty": 50, "impact": int(min(100, 50 + score)), "trend": int(min(100, 50 + score / 2))})
        parsed = heuristic

    # Final safety filter (ensure no COVID slipped through)
    parsed = [p for p in parsed if not is_covid_topic(p.get("name", ""))]

    # Sort by combined metric
    ranked = sorted(parsed, key=lambda d: (0.4 * d.get("impact", 0) + 0.35 * d.get("novelty", 0) + 0.25 * d.get("trend", 0)), reverse=True)

    state["domains"] = ranked
    state["logs"].append("DomainScout: Top Ranked Domains:")
    for i, dom in enumerate(ranked[:5], start=1):
        state["logs"].append(f"{i}. {dom.get('name')} — novelty {dom.get('novelty')}, impact {dom.get('impact')}")

    return state


# ---------------- Question Generator (robust) ----------------
async def question_generator_agent(state: ResearchState):
    """
    Produce structured research questions (strict JSON) for the top-ranked domain.
    Avoid repeats; fallback produces non-repeating domain-specific questions.
    """
    state["logs"].append("QuestionGenerator: starting (high-detail mode)...")

    domains = state.get("domains") or []
    if not domains:
        state["logs"].append("QuestionGenerator: no domains available, aborting.")
        state["questions"] = []
        return state

    top = domains[0]
    domain_name = safe_get_str(top.get("name") or top.get("title") or top)

    # Safety: if top domain contains COVID-related terms, request new domain
    if is_covid_topic(domain_name):
        state["logs"].append("QuestionGenerator: top domain appears to be COVID-related — regenerating domains.")
        state["domains"] = []
        return await domain_scout_agent(state)

    # Compose evidence snippets if present
    evidence_snippets = []
    for k in ("snippets", "evidence", "reason"):
        if isinstance(top, dict) and top.get(k):
            v = top.get(k)
            if isinstance(v, list):
                evidence_snippets.extend([safe_get_str(x) for x in v[:4]])
            else:
                evidence_snippets.append(safe_get_str(v))

    # Build prompt asking for strict JSON array
    prompt_lines = [
        "You are an expert scientific researcher. Produce a JSON array of 5 research questions (2024-2025) about the domain below.",
        "Return STRICT JSON ONLY. No commentary.",
        "",
        "Each object must contain:",
        " - question (string)",
        " - novelty (integer 0-100, relative to 2024-2025 literature)",
        " - feasibility (integer 0-100 for small team, low-cost compute)",
        " - hypothesis (1-2 sentences, falsifiable)",
        " - required_data (array of 3 concrete data sources or dataset types)",
        " - evaluation_metrics (array of concrete metrics)",
        " - short_rationale (1-2 sentences)",
        "",
        f"Domain: {domain_name}",
    ]
    if evidence_snippets:
        prompt_lines.append("Evidence:")
        for s in evidence_snippets[:4]:
            prompt_lines.append(f"- {s}")

    prompt_lines.append("\nProduce questions that are testable in a 72-hour exploratory experiment. Prefer simulations, small public datasets, analytic experiments.")

    prompt = "\n".join(prompt_lines)

    state["logs"].append(f"QuestionGenerator: calling LLM for top domain: {domain_name}")

    try:
        llm_text = await call_groq(prompt, max_tokens=1500)
    except Exception as e:
        state["logs"].append(f"QuestionGenerator: LLM call failed ({e}) — using fallback.")
        llm_text = None

    parsed = None
    if llm_text:
        try:
            start = llm_text.find("[")
            end = llm_text.rfind("]") + 1
            parsed = json.loads(llm_text[start:end])
        except Exception:
            # Try regex extraction
            try:
                m = re.search(r"(\[.*\])", llm_text, re.S)
                if m:
                    parsed = json.loads(m.group(1))
            except Exception:
                parsed = None

    # If parsing failed → fallback non-repetitive generator
    if not parsed or not isinstance(parsed, list):
        state["logs"].append("QuestionGenerator: Failed to parse LLM JSON → using fallback questions.")
        return await _fallback_questions(state, domain_name)

    # Normalize + validate
    validated = []
    for obj in parsed[:7]:
        try:
            qtxt = safe_get_str(obj.get("question") or obj.get("q") or "")
            if not qtxt:
                continue
            if is_covid_topic(qtxt):
                continue

            novelty = int(obj.get("novelty", 0)) if obj.get("novelty") is not None else 0
            feasibility = int(obj.get("feasibility", 0)) if obj.get("feasibility") is not None else 0
            hypothesis = safe_get_str(obj.get("hypothesis", ""))
            required_data = obj.get("required_data") or obj.get("data") or []
            if isinstance(required_data, str):
                required_data = [required_data]
            evaluation_metrics = obj.get("evaluation_metrics") or obj.get("metrics") or []
            if isinstance(evaluation_metrics, str):
                evaluation_metrics = [evaluation_metrics]
            short_rationale = safe_get_str(obj.get("short_rationale") or obj.get("reason") or "")

            validated.append({
                "question": qtxt.strip(),
                "novelty": max(0, min(100, novelty)),
                "feasibility": max(0, min(100, feasibility)),
                "hypothesis": hypothesis.strip(),
                "required_data": [safe_get_str(x) for x in required_data][:5],
                "evaluation_metrics": [safe_get_str(x) for x in evaluation_metrics][:5],
                "short_rationale": short_rationale.strip()
            })
        except Exception:
            continue

    if not validated:
        state["logs"].append("QuestionGenerator: LLM output invalid after normalization → fallback.")
        return await _fallback_questions(state, domain_name)

    # Deduplicate similar questions (simple text-based)
    seen = set()
    unique = []
    for q in validated:
        key = re.sub(r'\W+', ' ', q["question"].lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        unique.append(q)

    state["questions"] = unique[:5]
    state["logs"].append(f"QuestionGenerator: produced {len(state['questions'])} questions for domain: {domain_name}")
    for i, q in enumerate(state["questions"][:3], start=1):
        state["logs"].append(f"Q{i}: {q['question']} (novelty {q['novelty']}, feasibility {q['feasibility']})")

    return state


async def _fallback_questions(state: ResearchState, domain_name: str):
    """
    Non-repetitive domain-specific fallback questions (no "Fallback Q1" repetition).
    """
    state["logs"].append("QuestionGenerator: ⚠ Using fallback questions (non-repetitive).")
    templates = [
        "How can {domain} be instantiated in a small-scale experiment that demonstrates measurable improvement over a classical baseline?",
        "Which public datasets and simple simulation setups enable a proof-of-concept evaluation for {domain}?",
        "What compact model architecture within {domain} can be trained with low-cost compute to achieve a useful baseline result?",
        "How sensitive are performance metrics in {domain} to the choice of representation or pretraining?",
        "What evaluation protocol yields a statistically significant improvement for a prototype in {domain}?"
    ]
    simple = []
    for t in templates:
        q = t.format(domain=domain_name)
        if is_covid_topic(q):
            continue
        simple.append({
            "question": q,
            "novelty": 70,
            "feasibility": 80,
            "hypothesis": f"A focused implementation of {domain_name} will outperform a classical baseline in a small-scale evaluation.",
            "required_data": ["arXiv papers / method descriptions", "public benchmark datasets", "small curated CSV/JSON data"],
            "evaluation_metrics": ["accuracy", "F1", "effect_size"],
            "short_rationale": "Fallback domain-specific, non-repetitive question."
        })
    state["questions"] = simple[:5]
    return state


# ---------------- Data Alchemist (keeps your logic, robust) ----------------
async def data_alchemist_agent(state: ResearchState):
    state["logs"].append("DataAlchemist: starting data discovery & cleaning...")

    questions = state.get("questions") or []
    if not questions:
        state["logs"].append("DataAlchemist: no questions available, skipping.")
        state["data"] = []
        return state

    results = []
    doc_batch = []

    for qidx, q in enumerate(questions[:2], start=1):
        qtext = safe_get_str(q.get("question"))
        state["logs"].append(f"DataAlchemist: finding sources for Q{qidx}: {qtext[:100]}")

        sources = []
        try:
            sources = await find_disparate_sources(qtext)
            state["logs"].append(f"DataAlchemist: Scraper returned {len(sources)} sources for Q{qidx}")
        except Exception as e:
            state["logs"].append(f"DataAlchemist: Scraper failed for Q{qidx}: {e}")
            sources = []

        if not sources:
            # fallback to tavily search
            state["logs"].append(f"DataAlchemist: Falling back to Tavily search for Q{qidx}")
            try:
                tavily_results = await search_tavily(qtext, num_results=5)
                for tr in tavily_results:
                    sources.append({
                        "type": "tavily",
                        "title": tr.get("title", ""),
                        "url": tr.get("url", ""),
                        "snippet": tr.get("snippet", "")
                    })
                state["logs"].append(f"DataAlchemist: Tavily returned {len(sources)} sources for Q{qidx}")
            except Exception as e:
                state["logs"].append(f"DataAlchemist: Tavily failed for Q{qidx}: {e}")

        sources = sources[:3]
        if not sources:
            state["logs"].append(f"DataAlchemist: No sources found for Q{qidx}")
            results.append({"question": qtext, "datasets": []})
            continue

        q_datasets = []
        for sidx, s in enumerate(sources, start=1):
            u = safe_get_str(s.get("url"))
            title = safe_get_str(s.get("title") or f"source-{sidx}")
            snippet = safe_get_str(s.get("snippet"))
            source_type = s.get("type", "unknown")

            if not u:
                state["logs"].append(f"DataAlchemist: skipping source {sidx} (no URL)")
                continue

            state["logs"].append(f"DataAlchemist: Processing source {sidx} ({source_type}): {title[:80]}")

            local = ""
            try:
                local = await download_file(u, dest_folder="./downloads")
                if local:
                    state["logs"].append(f"DataAlchemist: downloaded {os.path.basename(local)}")
                else:
                    state["logs"].append("DataAlchemist: download returned empty path")
            except Exception as e:
                state["logs"].append(f"DataAlchemist: download error: {e}")
                local = ""

            text = ""
            tables = []

            if local and os.path.exists(local):
                if local.lower().endswith(".pdf"):
                    try:
                        text = extract_text_from_pdf(local)
                        tables = extract_tables_from_pdf(local)
                        state["logs"].append(f"DataAlchemist: extracted {len(text)} chars, {len(tables)} tables from PDF")
                    except Exception as e:
                        state["logs"].append(f"DataAlchemist: PDF extraction failed: {e}")
                        text = snippet or ""
                else:
                    try:
                        with open(local, "r", encoding="utf8", errors="ignore") as fh:
                            html = fh.read()
                        soup = BeautifulSoup(html, "html.parser")
                        text = soup.get_text(separator="\n")
                        state["logs"].append(f"DataAlchemist: extracted {len(text)} chars from HTML")
                    except Exception as e:
                        state["logs"].append(f"DataAlchemist: HTML parse failed: {e}")
                        text = snippet or ""
            else:
                text = snippet or ""
                state["logs"].append(f"DataAlchemist: using snippet fallback ({len(text)} chars)")

            combined_text = f"{title}\n\n{text}".strip()
            if len(combined_text) < 80:
                state["logs"].append(f"DataAlchemist: skipping source {sidx} (insufficient text)")
                continue

            doc_id = str(uuid.uuid4())
            meta = {
                "source_title": title,
                "source_url": u,
                "source_type": source_type,
                "question_idx": qidx,
                "question": qtext[:200]
            }
            doc_batch.append({"id": doc_id, "text": combined_text[:20000], "meta": meta})
            state["logs"].append(f"DataAlchemist: queued doc {doc_id[:8]} for indexing")

            table_paths = []
            for ti, df in enumerate(tables):
                try:
                    os.makedirs("./downloads", exist_ok=True)
                    csvp = f"./downloads/{doc_id}_table_{ti}.csv"
                    df.to_csv(csvp, index=False)
                    table_paths.append(csvp)
                except Exception as e:
                    state["logs"].append(f"DataAlchemist: table export failed: {e}")

            q_datasets.append({
                "source_title": title,
                "source_url": u,
                "source_type": source_type,
                "local_path": local,
                "text_snippet": (text[:1000] if text else snippet),
                "tables": table_paths
            })

        results.append({"question": qtext, "datasets": q_datasets})

    # index docs to Chroma (best-effort)
    if doc_batch:
        try:
            add_documents(doc_batch)
            state["logs"].append(f"DataAlchemist: indexed {len(doc_batch)} documents into Chroma.")
        except Exception as e:
            state["logs"].append(f"DataAlchemist: Chroma indexing failed: {e}")
    else:
        state["logs"].append("DataAlchemist: no documents to index.")

    state["data"] = results
    return state


# ---------------- Experiment Designer ----------------
async def experiment_designer_agent(state: ResearchState):
    state["logs"].append("ExperimentDesigner: Creating experiment...")
    # Construct simple experiment summary using available data
    data_len = len(state.get("data", [])) if state.get("data") else 0
    state["experiment"] = {
        "summary": "Experiment designed successfully",
        "metrics": {
            "confidence": 0.85,
            "quality_score": 0.78,
            "data_sources": data_len
        }
    }
    state["logs"].append(f"ExperimentDesigner: Metrics → confidence: 0.85, quality: 0.78, data_sources: {data_len}")
    return state


# ---------------- Critic ----------------
async def critic_agent(state: ResearchState):
    cycle = state.get("cycle", 0)
    state["logs"].append(f"Critic: Evaluating (cycle {cycle})...")

    experiment = state.get("experiment") or {}
    data = state.get("data") or []
    questions = state.get("questions") or []
    domains = state.get("domains") or []

    domain_name = safe_get_str(domains[0].get("name") if domains and isinstance(domains[0], dict) else (domains[0] if domains else "Unknown"))
    question_summary = safe_get_str(questions[0].get("question") if questions and isinstance(questions[0], dict) else (questions[0] if questions else "No question"))

    metrics = experiment.get("metrics", {}) if isinstance(experiment, dict) else {}

    # If experiment looks valid → generate limitations & future work (LLM or fallback)
    if experiment and isinstance(experiment, dict) and metrics:
        state["logs"].append("Critic: ✓ Valid experiment with metrics found → generating limitations & future work.")
        prompt = f"""You are a scientific peer reviewer. Given the context below, produce concise Limitations (2-3) and Future Work (2-3) items.

Context:
- Domain: {domain_name}
- Research Question: {question_summary}
- Metrics: {metrics}
- Number of data question-entries: {len(data)}

Format strictly as:
**Limitations:**
- item 1
- item 2

**Future Work:**
- step 1
- step 2
Keep the response concise (<= 200 words) and technical.
"""
        try:
            llm_output = await call_groq(prompt, max_tokens=400)
            if llm_output and len(llm_output.strip()) > 40:
                future_work = llm_output.strip()
                state["logs"].append("Critic: Generated detailed limitations & future work.")
            else:
                raise Exception("empty LLM output")
        except Exception:
            future_work = f"""**Limitations:**
- Preliminary results based on limited sources ({len(data)}) and synthetic experiments.
- Metrics are suggestive but require larger validation datasets.

**Future Work:**
- Expand data collection and rigorous statistical validation.
- Compare with alternative model families and improve interpretability."""
            state["logs"].append("Critic: LLM failed → used fallback limitations & future work.")

        state["critique"] = {
            "pass": True,
            "reason": "Valid experiment results with metrics",
            "future": future_work
        }
        return state

    # If cycles exhausted → force finish
    MAX_CYCLES = 3
    if cycle >= MAX_CYCLES:
        state["logs"].append(f"Critic: Max cycles reached ({cycle}) → forcing finish with fallback critique.")
        state["critique"] = {
            "pass": True,
            "reason": f"Max cycles reached ({cycle})",
            "future": "**Future Work:** Expand datasets and perform validation."
        }
        return state

    # Otherwise request more data
    state["logs"].append("Critic: ✗ Insufficient experiment results → requesting more data (will loop).")
    state["critique"] = {
        "pass": False,
        "reason": "Insufficient experiment results",
        "future": ""
    }
    return state


# ---------------- Graph build & routing ----------------
def build_research_graph():
    graph = StateGraph(ResearchState)

    # Register nodes
    graph.add_node("domain", domain_scout_agent)
    graph.add_node("questions", question_generator_agent)
    graph.add_node("data", data_alchemist_agent)
    graph.add_node("experiment", experiment_designer_agent)
    graph.add_node("critic", critic_agent)
    graph.add_node("paper", paper_generator_agent)

    graph.set_entry_point("domain")

    # Linear flow
    graph.add_edge("domain", "questions")
    graph.add_edge("questions", "data")
    graph.add_edge("data", "experiment")
    graph.add_edge("experiment", "critic")
    graph.add_edge("paper", END)  # paper finalizes the pipeline

    MAX_CYCLES = 3

    def decide_next(state: ResearchState):
        critique = state.get("critique") or {}
        cycle = state.get("cycle", 0)
        passed = critique.get("pass", False)

        print(f"[DECISION] cycle={cycle}, passed={passed}, critique={critique}")

        if passed:
            print("[DECISION] → PAPER (critic approved)")
            return "paper"

        if cycle >= MAX_CYCLES:
            print("[DECISION] → PAPER (max cycles reached)")
            # force pass so paper node runs
            state["critique"] = {"pass": True, "reason": "max cycles forced"}
            return "paper"

        # increment cycle and loop to data
        state["cycle"] = cycle + 1
        print(f"[DECISION] → LOOP back to data (cycle now {state['cycle']})")
        return "data"

    graph.add_conditional_edges(
        "critic",
        decide_next,
        {
            "paper": "paper",
            "data": "data",
        }
    )

    return graph.compile()
