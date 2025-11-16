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
- Optional: LangGraph (iterative control)

### **Data Layer**
- ChromaDB (local vector DB)
- Firecrawl API
- BeautifulSoup
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
<img width="478" height="1024" alt="image" src="https://github.com/user-attachments/assets/9474c05c-1348-4607-8555-9c1ff959b61b" />
Supervisor → Domain Scout → Question Generator → Data Alchemist → Experiment Designer → Critic → Writer

Multi-Agent Workflow:

---

# 🏁 Running Locally (Step-by-Step)

Below are complete **local development instructions** for running the system **without Docker** using `localhost`.

---

## ✅ **Step 1 — Clone the Repository**
```bash
git clone https://github.com/NandaKumar060504/Scientific_research_assistant.git
cd Scientific_research_assistant
````

---

## ✅ **Step 2 — Backend Setup (FastAPI)**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` inside `/backend`:

```
GROQ_API_KEY=your_groq_api_key
FIRECRAWL_API_KEY=your_firecrawl_key
CHROMA_DB_PATH=./chroma_db
```

---

## ✅ **Step 3 — Run Backend on Localhost**

Start FastAPI:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Backend will be available at:

* [http://localhost:8080](http://localhost:8000)

---

## ✅ **Step 4 — Frontend Setup (Next.js / React)**

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at:
👉 **[http://localhost:8082](http://localhost:8082)**

---

## ✅ **Step 5 — Start ChromaDB (If Required)**

Some setups require manually running Chroma:

```bash
python -m chromadb run --path ./chroma_db
```

ChromaDB will run locally on:
👉 [http://localhost:8001](http://localhost:8001) (default internal port)

---

## ✅ **Step 6 — Access the Full System**

* 🌐 **Web UI**: [http://localhost:8082](http://localhost:8082)
* ⚙️ **Backend API**: [http://localhost:8080](http://localhost:8080)

From the UI, you can:

* Select a research domain
* Trigger the multi-agent pipeline
* View live agent logs
* Download the final research paper + dashboard

---

# 🐳 Running with Docker (Alternative Recommended Setup)

This repository includes a production-ready **Docker Compose** setup.

---

## 🐳 **Step 1 — Add Environment Variables**

Inside `/backend/.env`:

```
GROQ_API_KEY=your_groq_api_key
FIRECRAWL_API_KEY=your_firecrawl_key
CHROMA_DB_PATH=./chroma_db
```

---

## 🐳 **Step 2 — Run Docker Compose**

```bash
docker-compose up --build
```

### Services:

| Component    | URL                                                      |
| ------------ | -------------------------------------------------------- |
| Frontend UI  | [http://localhost:3000](http://localhost:8082)           |
| Backend API  | [http://localhost:8000](http://localhost:8080)           |


---

## 📊 Outputs Generated

### **1. Scientific Research Paper**

* Markdown `.md`
* PDF output
* Structured sections (Abstract, Methods, Results, Discussion)

### **2. Interactive Dashboards**

* Plotly graphs
* Statistical results
* Trends & correlations

### **3. Metadata**

* JSON schema
* Confidence scores
* Dataset lineage

---

## 📁 Repository Structure

```
/backend            → FastAPI, agent logic, vector DB, data pipeline  
/frontend           → Next.js / React UI  
/nginx              → Reverse proxy configs  
docker-compose.yml  → Multi-container orchestration  
Dockerfile          → Multi-stage backend build  
README.md           
```

---

## 🎯 User Journey

1. Select or auto-discover a domain
2. Agents run sequentially in the UI
3. Data scraped + embedded
4. Experiments performed
5. Critic agent refines results
6. Writer produces final paper
7. Download results

---

## 🔮 Future Improvements

* Multimodal scientific figure extraction
* Full simulation engine for experiments
* PubMed + Semantic Scholar integrations
* Persistent long-term research memory
* Offline inference support


---

## 📄 License

MIT License

---

## 📬 Contact

**Name:** Nanda Kumar
**GitHub:** [https://github.com/NandaKumar060504](https://github.com/NandaKumar060504)
**Email:** [nandakumar3446@gmail.com](mailto:nandakumar3446@gmail.com)

```


