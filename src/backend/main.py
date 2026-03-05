import os
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 1. CRITICAL: Load environment variables BEFORE importing anything else
load_dotenv(override=True)
if not os.getenv("SUPABASE_URL"):
    load_dotenv("../../.env", override=True)

# 2. Initialize Supabase Client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SECRET_KEY")

if not supabase_url or not supabase_key:
    print(f"❌ CRITICAL ERROR: Supabase credentials not found in .env!")
    supabase_url = supabase_url or ""
    supabase_key = supabase_key or ""

from supabase import create_client, Client
supabase: Client = create_client(supabase_url, supabase_key)

# 3. Import agent workflow
from agents.graph import investment_copilot_graph

# 4. Initialize FastAPI App
app = FastAPI(
    title="AI Startup Investment Copilot API",
    description="Automated Venture Capital Deal Analysis & Due Diligence",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Define API Schema
class AnalysisRequest(BaseModel):
    name: str
    website: str = ""
    industry: str = ""

@app.get("/")
async def root():
    return {"message": "AI Investment Copilot API is active", "docs": "/docs"}

@app.post("/analyze")
async def analyze_startup(request: AnalysisRequest):
    """
    Triggers the end-to-end AI agent workflow:
    Researcher -> Analyst -> Scorer.
    Saves the full lifecycle to Supabase.
    """
    print(f"\n🚀 [API] Received analysis request for: {request.name}")
    
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is missing in backend .env")

    initial_state = {
        "name": request.name,
        "website": request.website,
        "industry": request.industry,
        "raw_research_data": [],
        "report_content": "",
        "scores": {},
        "risk_flags": [],
        "analysis_complete": False
    }

    try:
        # Run the LangGraph Workflow
        print(f"🧠 [Agent] Starting AI workflow for {request.name}...")
        final_output = investment_copilot_graph.invoke(initial_state)

        # Persist Data to Supabase
        print(f"💾 [Database] Saving results to Supabase...")
        
        # 1. Save to 'companies' table (matches init_schema.sql)
        startup_entry = {
            "name": request.name,
            "website": request.website,
            "industry": request.industry
        }
        startup_res = supabase.table("companies").insert(startup_entry).execute()
        
        if not startup_res.data:
            raise Exception("Failed to insert company record into Supabase")
        
        company_id = startup_res.data[0]["id"]

        # 2. Save to 'analysis_reports' table
        raw_context = "\n\n---\n\n".join(final_output.get("raw_research_data", []))
        
        report_entry = {
            "company_id": company_id,
            "research_context": raw_context,
            "report_content": final_output.get("report_content"),
            "scores": final_output.get("scores"),
            "risk_flags": final_output.get("risk_flags")
        }
        supabase.table("analysis_reports").insert(report_entry).execute()

        print(f"✅ [API] Analysis complete for {request.name}.")
        
        return {
            "status": "success",
            "company_id": company_id,
            "analysis": {
                "report": final_output.get("report_content"),
                "scores": final_output.get("scores"),
                "risk_flags": final_output.get("risk_flags")
            }
        }

    except Exception as e:
        print(f"❌ [API Error] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

@app.get("/history")
async def get_history(limit: int = 10):
    """
    Retrieve the most recent startup analyses from Supabase.
    """
    try:
        # Join with 'companies' instead of 'startups'
        res = supabase.table("analysis_reports").select("*, companies(name, website)").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
