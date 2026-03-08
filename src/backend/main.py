import os
import json
import asyncio
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# 1. Load env
load_dotenv(override=True)
if not os.getenv("SUPABASE_URL"):
    load_dotenv("../../.env", override=True)

# 2. Supabase
from supabase import create_client, Client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url or "", supabase_key or "")

# 3. Agent Nodes
from agents.analyst import analyst_node
from agents.scorer import scorer_node
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

app = FastAPI(title="AI Startup Investment Copilot API", version="1.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class AnalysisRequest(BaseModel):
    name: str
    website: str = ""
    industry: str = ""
    location: str = ""

class BrainstormRequest(BaseModel):
    report_id: str
    human_notes: str

class RefinementRequest(BaseModel):
    report_id: str
    human_notes: str
    debate_transcript: list[str] = []

# --- Endpoints ---

@app.post("/analyze")
async def analyze_startup(request: AnalysisRequest):
    from agents.graph import investment_copilot_graph
    initial_state = {
        "name": request.name, "website": request.website, "industry": request.industry,
        "location": request.location, "raw_research_data": [], "human_notes": "",
        "debate_transcript": [], "report_content": "", "scores": {}, "risk_flags": [],
        "analysis_complete": False
    }
    try:
        final_output = investment_copilot_graph.invoke(initial_state)
        startup_res = supabase.table("companies").insert({
            "name": request.name, "website": request.website, "industry": request.industry, "description": request.location
        }).execute()
        company_id = startup_res.data[0]["id"]
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/brainstorm")
async def brainstorm_stream(request: BrainstormRequest):
    """
    ULTIMATE BRAINSTORM: Multi-round Token-by-Token Streaming.
    Sequence: A1 -> B1 -> A2 -> B2 -> Chair.
    """
    print(f"\n🧠 [API] Starting Live Token Stream for Report: {request.report_id}")
    
    async def generate_debate():
        try:
            report_res = supabase.table("analysis_reports").select("*, companies(*)").eq("id", request.report_id).single().execute()
            data = report_res.data
            research_json = json.loads(data["research_context"])
            formatted_research = "\n".join([f"Source: {i['url']}\nContent: {i['content'][:500]}" for i in research_json])
            
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8, streaming=True)
            
            transcript = []

            async def stream_speaker(role, system_msg, human_msg, msg_id):
                full_content = ""
                # Send initial indicator
                yield f"data: {json.dumps({'id': msg_id, 'role': role, 'content': '', 'status': 'start'})}\n\n"
                
                async for chunk in llm.astream([SystemMessage(content=system_msg), HumanMessage(content=human_msg)]):
                    token = chunk.content
                    full_content += token
                    yield f"data: {json.dumps({'id': msg_id, 'role': role, 'content': full_content, 'status': 'streaming'})}\n\n"
                
                transcript.append(f"{role}: {full_content}")
                yield f"data: {json.dumps({'id': msg_id, 'role': role, 'content': full_content, 'status': 'end'})}\n\n"
                await asyncio.sleep(0.3)

            # --- ROUND 1: Partner A Opening ---
            async for chunk in stream_speaker("A", 
                "You are Partner A (Visionary). Highlight the massive potential based on the new notes. 50 words max.",
                f"New Info: {request.human_notes}\nContext: {formatted_research}", "a1"): yield chunk

            # --- ROUND 2: Partner B Challenge ---
            async for chunk in stream_speaker("B", 
                "You are Partner B (Skeptic). Counter Partner A using web research. Point out one huge risk. 50 words max.",
                f"A said: {transcript[-1]}\nEvidence: {formatted_research}", "b1"): yield chunk

            # --- ROUND 3: Partner A Rebuttal ---
            async for chunk in stream_speaker("A", 
                "You are Partner A (Visionary). Rebut Partner B's risk using the founder's insights. 50 words max.",
                f"B challenged: {transcript[-1]}\nFounder note: {request.human_notes}", "a2"): yield chunk

            # --- ROUND 4: Partner B Final Scrutiny ---
            async for chunk in stream_speaker("B", 
                "You are Partner B (Skeptic). One last skeptical check. Is this really defensible? 40 words max.",
                f"Updated Case: {transcript[-1]}", "b2"): yield chunk

            # --- ROUND 5: IC Chair Verdict ---
            async for chunk in stream_speaker("C", 
                "You are the IC Chair. Hear A and B. Reach a final consensus. Be decisive. 80 words max.",
                "\n".join(transcript), "c1"): yield chunk
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_debate(), media_type="text/event-stream")

@app.post("/refine")
async def refine_final(request: RefinementRequest):
    try:
        report_res = supabase.table("analysis_reports").select("*, companies(*)").eq("id", request.report_id).single().execute()
        prev = report_res.data
        state = {
            "name": prev["companies"]["name"],
            "location": prev["companies"].get("description", ""),
            "raw_research_data": json.loads(prev["research_context"]),
            "human_notes": request.human_notes,
            "debate_transcript": request.debate_transcript
        }
        analysis = analyst_node(state)
        scores = scorer_node({**state, **analysis})
        update_data = { "report_content": analysis["report_content"], "scores": scores["scores"], "risk_flags": scores["risk_flags"] }
        supabase.table("analysis_reports").update(update_data).eq("id", request.report_id).execute()
        return {"status": "success", "analysis": {**analysis, **scores}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
