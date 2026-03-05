import os
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 1. CRITICAL: Load environment variables BEFORE importing anything else
# We try to load it from the current folder, then one level up
load_dotenv(override=True)
if not os.getenv("SUPABASE_URL"):
    load_dotenv("../../.env", override=True)

# 2. Initialize Supabase Client (Verify they are not None)
supabase_url = os.getenv("SUPABASE_URL")
# Try multiple common naming conventions to be safe
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SECRET_KEY")

if not supabase_url or not supabase_key:
    # This will prevent the app from crashing silently
    print(f"❌ CRITICAL ERROR: Supabase credentials not found in .env!")
    print(f"DEBUG: SUPABASE_URL: {supabase_url}")
    print(f"DEBUG: SUPABASE_KEY: {'[FOUND]' if supabase_key else '[MISSING]'}")
    # We'll set them to empty strings to avoid crashing on import, 
    # but the first request will fail with a clear message.
    supabase_url = supabase_url or ""
    supabase_key = supabase_key or ""

from supabase import create_client, Client
supabase: Client = create_client(supabase_url, supabase_key)

# 3. Now import our AI workflow
from agents.graph import investment_copilot_graph

# 4. Initialize FastAPI App
app = FastAPI(
    title="AI Startup Investment Copilot API",
    description="Automated Venture Capital Deal Analysis & Due Diligence",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Define API Schema (Pydantic)
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
    
    # Check if we have API keys before running the heavy workflow
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
        "final_score": 0.0,
        "analysis_complete": False
    }

    try:
        # B. Run the LangGraph Workflow
        print(f"🧠 [Agent] Starting AI workflow for {request.name}...")
        final_output = investment_copilot_graph.invoke(initial_state)

        # C. Persist Data to Supabase
        print(f"💾 [Database] Saving results to Supabase...")
        
        # 1. Save to 'startups' table
        startup_entry = {
            "name": request.name,
            "website": request.website,
            "industry": request.industry
        }
        startup_res = supabase.table("startups").insert(startup_entry).execute()
        
        if not startup_res.data:
            raise Exception("Failed to insert startup record into Supabase")
        
        startup_id = startup_res.data[0]["id"]

        # 2. Save to 'analysis_reports' table
        raw_context = "\n\n---\n\n".join(final_output.get("raw_research_data", []))
        
        report_entry = {
            "startup_id": startup_id,
            "research_context": raw_context,
            "report_content": final_output.get("report_content"),
            "scores": final_output.get("scores"),
            "risk_flags": final_output.get("risk_flags"),
            "final_score": final_output.get("final_score")
        }
        supabase.table("analysis_reports").insert(report_entry).execute()

        print(f"✅ [API] Analysis complete for {request.name}.")
        
        return {
            "status": "success",
            "startup_id": startup_id,
            "analysis": {
                "report": final_output.get("report_content"),
                "scores": final_output.get("scores"),
                "risk_flags": final_output.get("risk_flags"),
                "final_score": final_output.get("final_score")
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
        res = supabase.table("analysis_reports").select("*, startups(name, website)").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Start the server: uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
