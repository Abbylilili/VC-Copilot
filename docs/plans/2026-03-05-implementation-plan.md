# Startup Investment Copilot Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use subagent-driven-development to implement this plan task-by-task.

**Goal:** Build a functional AI Startup Investment Copilot with a 3-agent backend (Researcher, Analyst, Scorer) and a polished Next.js dashboard.

**Architecture:** A Python FastAPI backend orchestrates a LangGraph state machine (Researcher -> Analyst -> Scorer). The frontend is a Next.js application that calls the backend and displays analysis results in a structured dashboard. Data is persisted in Supabase.

**Tech Stack:** Python, FastAPI, LangGraph, LangChain, Next.js, Tailwind CSS, Shadcn UI, Supabase.

---

### Phase 1: Environment & Database Setup

#### Task 1: Initialize Backend Environment
**Files:**
- Create: `src/backend/requirements.txt`
- Create: `src/backend/.env.example`
**Step 1:** Define dependencies (fastapi, uvicorn, langgraph, langchain, langchain-openai, firecrawl-py, python-dotenv).
**Step 2:** Create `.env.example` with placeholders for OPENAI_API_KEY, SERPER_API_KEY, FIRECRAWL_API_KEY, SUPABASE_URL, SUPABASE_KEY.

#### Task 2: Supabase Schema Setup
**Files:**
- Create: `docs/sql/schema.sql`
**Step 1:** Define the `startups` and `analysis_reports` tables as specified in the Design Doc.
**Step 2:** Include RLS (Row Level Security) basics if needed for the interview (showing security awareness).

---

### Phase 2: Core Agent Logic (The "Brain")

#### Task 3: Define LangGraph State & Schema
**Files:**
- Create: `src/backend/agents/state.py`
**Step 1:** Define `AgentState` TypedDict with fields for startup info and analysis results.

#### Task 4: Implement Researcher Agent (Serper + Firecrawl)
**Files:**
- Create: `src/backend/agents/researcher.py`
**Step 1:** Write a tool to search via Serper and scrape via Firecrawl.
**Step 2:** Implement the `researcher_node` that updates the state with raw Markdown data.

#### Task 5: Implement Analyst Agent (Memo Generation)
**Files:**
- Create: `src/backend/agents/analyst.py`
**Step 1:** Design a prompt to extract TAM/SAM/SOM, Team, and Product Moat from raw Markdown.
**Step 2:** Implement the `analyst_node` to generate the structured memo content.

#### Task 6: Implement Scorer Agent (VC Rubric)
**Files:**
- Create: `src/backend/agents/scorer.py`
**Step 1:** Design a prompt for the "Investment Committee" to score the project 1-10 on Market, Team, Product, and Traction.
**Step 2:** Implement the `scorer_node` and integrate it into the LangGraph workflow.

---

### Phase 3: Backend API & Integration

#### Task 7: FastAPI Endpoint for Analysis
**Files:**
- Create: `src/backend/main.py`
**Step 1:** Implement a POST `/analyze` endpoint that triggers the LangGraph workflow and saves results to Supabase.
**Step 2:** Add a GET `/history` endpoint to retrieve past analyses.

---

### Phase 4: Frontend Dashboard

#### Task 8: Initialize Next.js Dashboard
**Files:**
- Create: `src/frontend/package.json`
- Create: `src/frontend/tailwind.config.ts`
**Step 1:** Scaffold Next.js with Tailwind and Shadcn UI components (Card, Button, Input, Progress).

#### Task 9: Build Investment Dashboard UI
**Files:**
- Create: `src/frontend/app/page.tsx`
- Create: `src/frontend/components/ScoreCard.tsx`
- Create: `src/frontend/components/MemoViewer.tsx`
**Step 1:** Build the input form and the main display area for scores and the memo.
**Step 2:** Connect the frontend to the FastAPI backend.

---

### Phase 5: Testing & Final Polish

#### Task 10: End-to-End Test
**Files:**
- Create: `tests/test_agent_workflow.py`
**Step 1:** Write a script to test the full Researcher -> Analyst -> Scorer flow with a real startup (e.g., "OpenAI").
**Step 2:** Verify Supabase persistence.
