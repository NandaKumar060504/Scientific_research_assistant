# 🧠 Autonomous Scientific Research Assistant
*A Groq-powered multi-agent AI system for autonomous scientific discovery, data acquisition, experimentation, and scientific paper generation.*

---

## 🚀 Overview
The **Autonomous Scientific Research Assistant** is an end-to-end multi-agent AI framework capable of independently conducting a full scientific research lifecycle.  
It discovers emerging domains, generates hypotheses, scrapes and cleans data, runs experiments, iterates through critique loops, and produces a complete scientific research paper with visualizations and metadata.

This project was built as part of a **Scientific Research Assistant Take-Home Assessment**, demonstrating agentic system design, advanced LLM reasoning, and fully containerized deployment.

---

## 🧩 Problem Statement
Modern scientific research is slow and requires many manual, highly specialized steps—domain scouting, hypothesis generation, data extraction, experimentation, visual analysis, and writing.

**Goal:**  
Create an AI system that autonomously performs the *entire* research lifecycle with minimal human input.

The system must:
- Discover emerging scientific topics (post-2024)
- Generate meaningful research questions
- Acquire, parse, and clean real-world data (web pages, PDFs, APIs, ArXiv)
- Run experiments and create visualizations
- Self-critique and iterate for higher quality
- Output a structured research paper with metadata and plots
- Run efficiently on free-tier infrastructure (Groq LPU, local vector DB)
- Provide a functional Web UI for real-time interaction

---

## 🌟 High-Level Solution
A **Groq-accelerated multi-agent research framework** that autonomously executes the scientific pipeline.

### Key components:
- 🧠 **Groq Llama-3.1-70B** for ultra-fast reasoning  
- 🔗 **LangChain** for agent orchestration  
- 🧬 **ChromaDB** for memory + document embeddings  
- 🌐 **Firecrawl + BeautifulSoup** for dynamic scraping  
- 📚 **PDF Extraction & ArXiv API** for scientific ingestion  
- 🧪 **Plotly** for interactive experiment visualizations  
- ⚙️ **FastAPI Backend** + **React/Next.js Frontend**  
- 🐳 **Dockerized Deployment (multi-stage build)**  

### Final outputs:
- Markdown + PDF **scientific research paper**
- Interactive **Plotly dashboards**
- JSON **structured metadata**
- Agent reasoning trace + confidence scores

---

## 🛠 Tech Stack

### **LLM & Reasoning**
- Groq Llama-3.1-70B (Groq API)
- Groq LPU accelerated inference

### **Framework**
- LangChain
- Optional: LangGraph (for iterative loop)

### **Data Layer**
- ChromaDB (local vector DB)
- Firecrawl API
- BeautifulSoup (HTML parsing)
- PDF + OCR Extraction
- ArXiv API

### **Backend**
- FastAPI
- Python 3.10+

### **Frontend**
- React / Next.js
- WebSockets

### **Deployment**
- Docker
- Docker Compose
- Multi-stage Dockerfile
- Nginx Reverse Proxy

---

## 🏗 Architecture

> *(Insert your architecture diagram here — image file in repo)*

### Multi-Agent Workflow:
Supervisor → Domain Scout → Question Generator → Data Alchemist → Experiment Designer → Critic → Writer

---

# 🐳 Running the Project Locally (Docker Recommended)

This repo contains a full **Docker Compose setup** including:
- Backend (FastAPI)
- Frontend (Next.js)
- ChromaDB
- Nginx Reverse Proxy

---

## ✅ Step 1 — Clone Repository
```bash
git clone https://github.com/NandaKumar060504/Scientific_research_assistant.git
cd Scientific_research_assistant
