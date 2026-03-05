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


