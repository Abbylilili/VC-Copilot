# AI Startup Investment Copilot 🚀

**An Intelligent Deal Sourcing & Analysis Platform for Venture Capitalists**

This project is a high-fidelity demo designed for a VC daily work. it demonstrates the power of Multi-Agent Systems (MAS) in processing unstructured data, conducting deep industry research, and performing quantitative investment evaluations.

## 🌟 Hero Features

- **Agentic Deal Sourcing & Research**: Automatically retrieves web data via **Serper** and transforms cluttered web pages into clean, LLM-ready Markdown using **Firecrawl**.
- **3-Agent Collaborative Workflow (LangGraph)**:
  - 🕵️ **Researcher Agent**: Conducts broad searches and deep web crawling.
  - 📊 **Analyst Agent**: Extracts key metrics (TAM/SAM/SOM, Team Strength, Product Moat, Traction).
  - ⚖️ **Investment Committee Agent**: Performs rigorous fact-checking and scoring based on a custom VC Rubric.
- **Investment Dashboard**: A minimalist, high-performance dashboard built with **Next.js + Shadcn/UI**, featuring real-time AI report rendering.
- **Data Persistence**: Hybrid storage of structured profiles and unstructured analysis results using **Supabase (PostgreSQL)**.

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Supabase CLI** (for local database development)
- **Node.js & npm/pnpm** (for the upcoming frontend)

### 1. Backend Setup
Navigate to the backend directory and set up your environment:

```bash
cd src/backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys (OpenAI, Serper, Firecrawl, Supabase)
```

### 2. Database Setup (Supabase)
This project uses Supabase for data persistence. You can run it locally or use a remote project.

**Local Development:**
```bash
# Initialize Supabase (if not already done)
supabase start

# Apply migrations
supabase db reset
```

**Manual Schema Setup:**
If you are using a remote Supabase project, run the SQL found in `supabase/migrations/20260305071128_init_schema.sql` in your Supabase SQL Editor.

### 3. Running the Application

#### Start Backend API
```bash
cd src/backend
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`. You can access the interactive documentation at `http://localhost:8000/docs`.

---

## 🏗️ Architecture Overview

### Tech Stack
- **Frontend**: Next.js 14/15 (React), Tailwind CSS, Shadcn/UI, Lucide-React.
- **Backend**: Python 3.10+, FastAPI, LangGraph (Agentic Orchestration), LangChain.
- **AI Stack**: GPT-4o / Claude 3.5 Sonnet, Firecrawl (Web Scraping), Serper (Search API).
- **Database**: Supabase (PostgreSQL + JSONB for flexible reporting).
- **Deployment**: Vercel (Frontend), Railway/Docker (Backend).

### LangGraph Workflow
1. **Input**: Startup Name + Website URL + Industry.
2. **Step 1 (Researcher)**: `Serper` (5-10 links) -> `Firecrawl` (Clean Markdown).
3. **Step 2 (Analyst)**: Analyze Markdown -> Extract Market, Team, Product, and News signals.
4. **Step 3 (Investment Committee)**: Fact-checking -> Rubric-based Scoring -> Risk Flagging.
5. **Output**: Multi-tab Investment Memo + Final Deal Score (e.g., 7.8/10).


