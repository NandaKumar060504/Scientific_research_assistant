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

> <img width="478" height="1024" alt="image" src="https://github.com/user-attachments/assets/bf88984c-6cb9-4a10-8570-36881f8c7a90" />


### Multi-Agent Workflow:
Supervisor → Domain Scout → Question Generator → Data Alchemist → Experiment Designer → Critic → Writer

---

````markdown
# 🐳 Running the Project
You can run this project in two ways:

1.  **Using Docker (Recommended):** The easiest way to get all services (backend, frontend, DB, proxy) running together with a single command.
2.  **Running Locally (Manual):** Good for development and running the backend and frontend services individually.

---

## Option 1: Running with Docker (Recommended)

This repo contains a full **Docker Compose setup** including the FastAPI backend, Next.js frontend, ChromaDB, and an Nginx reverse proxy.
### ✅ Step 1 — Clone Repository

```bash
git clone [https://github.com/NandaKumar060504/Scientific_research_assistant.git](https://github.com/NandaKumar060504/Scientific_research_assistant.git)
cd Scientific_research_assistant
````

### ✅ Step 2 — Set Up Environment

You will need to create a `.env` file to store your API keys (like the Groq API key). You can often copy an example file if one is provided.

```bash
# Example: copy an .env.example file (if it exists)
cp .env.example .env

# Now, edit the .env file and add your API keys
nano .env 
```

### ✅ Step 3 — Build and Run

This command will build the images and start all the containers.

```bash
docker compose up -d --build
```

Your application should now be accessible, typically at `http://localhost:80` (or whichever port Nginx is configured to expose).

-----

## Option 2: Running Locally (Manual Setup)

If you prefer to run the backend and frontend services manually without Docker, follow these steps.

### ✅ Step 1 — Clone Repository

```bash
git clone [https://github.com/NandaKumar060504/Scientific_research_assistant.git](https://github.com/NandaKumar060504/Scientific_research_assistant.git)
cd Scientific_research_assistant
```

### ✅ Step 2 — Run the Backend (FastAPI)

1.  Navigate to the backend directory (adjust the path if necessary):
    ```bash
    cd backend 
    ```
2.  Create a virtual environment and install dependencies:
    ```bash
    # Create virtual environment
    python -m venv venv

    # Activate virtual environment
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    # .\venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt
    ```
3.  (Required) Create a `.env` file in this directory and add your API keys.
4.  Run the Uvicorn server:
    ```bash
    uvicorn app:app --reload --port 8080
    ```
    The backend API will now be running on `http://localhost:8080`.

### ✅ Step 3 — Run the Frontend (React/Next.js)

1.  In a **new terminal**, navigate to the frontend directory (adjust the path if necessary):
    ```bash
    # From the root directory
    cd frontend 
    ```
2.  Install the Node.js dependencies:
    ```bash
    npm install
    ```
3.  Run the frontend development server:
    ```bash
    npm run dev
    ```
    The frontend will now be accessible, typically on `http://localhost:3000`.

-----

## 👨‍💻 About the Author

This project was created by **Nanda Kumar** as part of a Scientific Research Assistant Take-Home Assessment.

  * **GitHub:** [@NandaKumar060504](https://www.google.com/search?q=https://github.com/NandaKumar060504)
  * **LinkedIn:** `https://www.linkedin.com/in/nanda-kumar-t-30ba12240/`
 


