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
from supabase import create_client, Client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url or "", supabase_key or "")

# 3. Import our AI workflow
from agents.graph import investment_copilot_graph

# 4. Initialize FastAPI App
app = FastAPI(
    title="AI Startup Investment Copilot API",
    description="Automated Venture Capital Deal Analysis & Due Diligence",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Models ---
class AnalysisRequest(BaseModel):
    name: str
    website: str = ""
    industry: str = ""
    location: str = "" # New: location/country
    human_notes: str = ""

class RefinementRequest(BaseModel):
    report_id: str
    human_notes: str

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "AI Investment Copilot API is active", "version": "1.1.0"}

@app.post("/analyze")
async def analyze_startup(request: AnalysisRequest):
    """
    Initial Generation: Researcher -> Analyst -> Scorer.
    """
    print(f"\n🚀 [API] Initial Analysis Request: {request.name} ({request.location})")
    
    initial_state = {
        "name": request.name,
        "website": request.website,
        "industry": request.industry,
        "location": request.location,
        "raw_research_data": [],
        "human_notes": request.human_notes,
        "debate_transcript": [],
        "report_content": "",
        "scores": {},
        "risk_flags": [],
        "analysis_complete": False
    }

    try:
        final_output = investment_copilot_graph.invoke(initial_state)
        
        # 1. Save to 'companies'
        startup_res = supabase.table("companies").insert({
            "name": request.name, 
            "website": request.website, 
            "industry": request.industry,
            "description": request.location # Temporary: storing location in description
        }).execute()
        
        if not startup_res.data:
            raise Exception("Failed to insert company into Supabase")
            
        company_id = startup_res.data[0]["id"]

        # 2. Save to 'analysis_reports'
        report_data = {
            "company_id": company_id,
            "research_context": json.dumps(final_output.get("raw_research_data", [])),
            "report_content": final_output.get("report_content"),
            "scores": final_output.get("scores"),
            "risk_flags": final_output.get("risk_flags")
        }
        res = supabase.table("analysis_reports").insert(report_data).execute()
        
        return {"status": "success", "report_id": res.data[0]["id"], "analysis": final_output}
    except Exception as e:
        print(f"❌ [Analyze Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refine")
async def refine_analysis(request: RefinementRequest):
    """
    Human-in-the-loop Refinement: Debate -> Analyst -> Scorer.
    """
    print(f"\n💡 [API] Refinement Request for Report ID: {request.report_id}")

    try:
        # A. Fetch previous report data
        report_res = supabase.table("analysis_reports").select("*, companies(*)").eq("id", request.report_id).single().execute()
        prev_report = report_res.data
        if not prev_report:
            raise HTTPException(status_code=404, detail="Report not found")

        # B. Parse research data
        raw_data = []
        try:
            raw_data = json.loads(prev_report["research_context"])
        except:
            raw_data = [{"url": "Legacy Data", "content": prev_report["research_context"]}]

        # C. Prepare state
        initial_state = {
            "name": prev_report["companies"]["name"],
            "website": prev_report["companies"]["website"],
            "industry": prev_report["companies"]["industry"],
            "location": prev_report["companies"].get("description", ""), # Load location from description
            "raw_research_data": raw_data,
            "human_notes": request.human_notes,
            "debate_transcript": [],
            "report_content": "",
            "scores": {},
            "risk_flags": [],
            "analysis_complete": False
        }

        # D. Run Graph
        final_output = investment_copilot_graph.invoke(initial_state)

        # E. Update report
        update_data = {
            "report_content": final_output.get("report_content"),
            "scores": final_output.get("scores"),
            "risk_flags": final_output.get("risk_flags"),
            "human_notes": request.human_notes
        }
        supabase.table("analysis_reports").update(update_data).eq("id", request.report_id).execute()

        return {
            "status": "success",
            "debate": final_output.get("debate_transcript"),
            "analysis": final_output
        }

    except Exception as e:
        print(f"❌ [Refine Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history(limit: int = 10):
    try:
        res = supabase.table("analysis_reports").select("*, companies(name, website)").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
