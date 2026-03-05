# Design Doc: 2026-03-05 Startup Investment Copilot (English)

## 1. Core Objective
Build an end-to-end startup analysis tool capable of autonomously retrieving web data and generating professional, high-fidelity investment memos for venture capital firms.

## 2. System Components

### 2.1 Backend: FastAPI + LangGraph
- **State Definition**: The `AgentState` includes: `startup_info`, `raw_data`, `memo_draft`, `scores`, and `risk_flags`.
- **Agent Nodes**:
  - `researcher_node`: Uses `SerperDevTool` for link discovery and `FirecrawlTool` for content scraping (Markdown extraction).
  - `analyst_node`: Parses raw content to extract TAM/SAM/SOM, Team background, Product differentiation, and recent News.
  - `scorer_node`: Evaluates data against a predefined Rubric across 4 dimensions (Market, Team, Product, Traction).
- **Control Flow**: `START -> researcher -> analyst -> scorer -> END`.

### 2.2 Frontend: Next.js + Shadcn UI
- **Dashboard Layout**: Sidebar for history, Main panel for the current report.
- **Components**:
  - `StartupInputForm`: Inputs for Name, Website, and Industry.
  - `AnalysisDashboard`: 
    - `ScoreCard`: Circular progress bar for the final score.
    - `MemoViewer`: Markdown renderer for the multi-section memo.
    - `SignalSignals`: Visual indicators for traction and risks.

### 2.3 Database: Supabase (PostgreSQL)
- **`startups` Table**:
  - `id`: UUID (Primary Key)
  - `name`: Text
  - `website`: Text
  - `industry`: Text
- **`analysis_reports` Table**:
  - `id`: UUID (Primary Key)
  - `startup_id`: FK -> startups.id
  - `research_context`: Text (Raw Markdown)
  - `memo_content`: Text (Formatted Markdown)
  - `scores`: JSONB (Market, Team, Product, Traction scores)
  - `final_score`: Float
  - `risk_flags`: Text[] (Array of flags)

## 3. Key Challenges & Solutions
- **Data Veracity**: Ensuring the analyst only uses the retrieved data to prevent hallucinations.
- **Explainability**: Each score must be accompanied by supporting evidence or logical justification.
- **User Experience**: Implementing streaming outputs or descriptive loading states to manage the 10-20 second agentic delay.

## 4. Implementation Next Steps
1.  Initialize Supabase project and schema.
2.  Develop the Python backend with LangGraph core logic.
3.  Build the Next.js frontend and integrate with the FastAPI backend.
