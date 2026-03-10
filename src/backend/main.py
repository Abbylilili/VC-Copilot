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

app = FastAPI(title="AI Startup Investment Copilot API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# IC Partner Personas (used in brainstorm)
# ─────────────────────────────────────────────
PARTNER_PERSONAS = {
    "A": {
        "name": "Partner A — Growth Investor",
        "style": "Sequoia / Benchmark",
        "lens": "TAM size, growth velocity, market timing, winner-take-all dynamics, network effects",
        "instruction": (
            "You are Partner A, a Growth Investor (Sequoia / Benchmark style). "
            "Your framework: massive TAM, exponential growth curves, and market timing are the only things that matter. "
            "You have pattern-matched 100x outcomes — they always start with a huge market shift. "
            "Argue the BULL CASE for this investment based on growth and market opportunity. "
            "Be sharp and specific. 80 words max."
        ),
    },
    "B": {
        "name": "Partner B — Risk Analyst",
        "style": "Tiger Global / Coatue",
        "lens": "Unit economics, burn efficiency, competitive moat durability, market saturation risk",
        "instruction": (
            "You are Partner B, a Risk Analyst (Tiger Global / Coatue style). "
            "Your framework: great companies die from poor unit economics, not bad products. "
            "You've seen countless 'hot markets' turn into bloodbaths. "
            "Steelman the BEAR CASE — identify the single biggest structural risk and why it's fatal. "
            "Be brutally honest. 80 words max."
        ),
    },
    "C": {
        "name": "Partner C — Founder Expert",
        "style": "Andreessen Horowitz / Founders Fund",
        "lens": "Founder-market fit, team pedigree, execution track record, missionary vs mercenary motivation",
        "instruction": (
            "You are Partner C, a Founder-First Partner (a16z / Founders Fund style). "
            "Your framework: bet on the person, not the plan. "
            "Great founders pivot; mediocre teams destroy great opportunities. "
            "Assess EXCLUSIVELY the founding team quality: domain expertise, prior exits, ability to recruit A-players, "
            "and whether they are the ONLY people who could build this. 80 words max."
        ),
    },
    "D": {
        "name": "IC Chair — Managing Partner",
        "style": "Final Verdict",
        "lens": "Synthesis, final conviction, check size, key conditions",
        "instruction": (
            "You are the IC Chair, Managing Partner. "
            "You have heard three distinct analytical perspectives. Your job: reach a FINAL, DECISIVE verdict. "
            "Structure your response as:\n"
            "1. VERDICT: INVEST / WATCH / PASS (one word)\n"
            "2. KEY CONVICTION: The single strongest reason for your verdict (1 sentence)\n"
            "3. BIGGEST RISK: The one thing that could make you wrong (1 sentence)\n"
            "4. NEXT ACTION: The specific due diligence step needed before term sheet (1 sentence)\n"
            "Be decisive. No hedging. 100 words max."
        ),
    },
}

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

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
            "name": request.name, "website": request.website,
            "industry": request.industry, "description": request.location
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
    Virtual IC Debate — 3 Partners + IC Chair, token-by-token streaming.

    Flow:
      A1 (Growth thesis) →
      B1 (Risk challenge) →
      C1 (Team/Founder assessment) →
      A2 (Growth partner responds to challenges) →
      B2 (Risk analyst final point) →
      D  (IC Chair: decisive verdict)
    """
    print(f"\n🧠 [IC Debate] Starting for report: {request.report_id}")

    async def generate_debate():
        try:
            # ── Fetch context from DB ─────────────────────────────────
            report_res = (
                supabase.table("analysis_reports")
                .select("*, companies(*)")
                .eq("id", request.report_id)
                .single()
                .execute()
            )
            data = report_res.data
            company_name = data["companies"]["name"]
            industry     = data["companies"].get("industry", "")
            location     = data["companies"].get("description", "")

            # Original first-draft report (truncated for context)
            first_report = (data.get("report_content") or "")[:3000]

            # Raw research evidence
            research_json = json.loads(data.get("research_context") or "[]")
            formatted_research = "\n".join([
                f"[{item['url']}]: {item['content'][:400]}"
                for item in research_json[:8]
            ])

            # ── Shared debate context (injected into every prompt) ────
            base_context = f"""
==== COMPANY ====
Name: {company_name} | Industry: {industry} | Location: {location}

==== FIRST-DRAFT ANALYST MEMO (v1) ====
{first_report if first_report else "Not yet available."}

==== NEW PROPRIETARY INFORMATION (Expert Input) ====
{request.human_notes}

==== SUPPORTING PUBLIC RESEARCH ====
{formatted_research if formatted_research else "No public research available."}
""".strip()

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.85, streaming=True)
            transcript: list[str] = []

            # ── Streaming helper ──────────────────────────────────────
            async def stream_speaker(role: str, system_msg: str, human_msg: str, msg_id: str):
                full_content = ""
                yield f"data: {json.dumps({'id': msg_id, 'role': role, 'content': '', 'status': 'start'})}\n\n"
                async for chunk in llm.astream(
                    [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]
                ):
                    full_content += chunk.content
                    yield f"data: {json.dumps({'id': msg_id, 'role': role, 'content': full_content, 'status': 'streaming'})}\n\n"
                persona_name = PARTNER_PERSONAS[role]["name"]
                transcript.append(f"[{persona_name}]: {full_content}")
                yield f"data: {json.dumps({'id': msg_id, 'role': role, 'content': full_content, 'status': 'end'})}\n\n"
                await asyncio.sleep(0.2)

            # ── ROUND 1: Partner A — Growth Bull Case ─────────────────
            async for chunk in stream_speaker(
                "A",
                PARTNER_PERSONAS["A"]["instruction"],
                f"Make your opening investment case.\n\n{base_context}",
                "a1",
            ):
                yield chunk

            # ── ROUND 2: Partner B — Risk Bear Case ───────────────────
            async for chunk in stream_speaker(
                "B",
                PARTNER_PERSONAS["B"]["instruction"],
                f"Partner A just argued:\n{transcript[-1]}\n\nNow make the bear case.\n\n{base_context}",
                "b1",
            ):
                yield chunk

            # ── ROUND 3: Partner C — Team / Founder Assessment ────────
            async for chunk in stream_speaker(
                "C",
                PARTNER_PERSONAS["C"]["instruction"],
                (
                    f"Growth case: {transcript[-2]}\n"
                    f"Risk case: {transcript[-1]}\n\n"
                    f"Now assess the founding team exclusively.\n\n{base_context}"
                ),
                "c1",
            ):
                yield chunk

            # ── ROUND 4: Partner A — Responds to B & C ────────────────
            async for chunk in stream_speaker(
                "A",
                (
                    PARTNER_PERSONAS["A"]["instruction"]
                    + " Now directly rebut the risk and team concerns raised. Be specific."
                ),
                (
                    f"B challenged with: {transcript[-2]}\n"
                    f"C raised team concerns: {transcript[-1]}\n\n"
                    f"Rebut both. Base your rebuttal on the proprietary notes and research.\n\n{base_context}"
                ),
                "a2",
            ):
                yield chunk

            # ── ROUND 5: Partner B — Final Risk Point ─────────────────
            async for chunk in stream_speaker(
                "B",
                (
                    PARTNER_PERSONAS["B"]["instruction"]
                    + " This is your final word. Name the ONE risk that would make you vote NO regardless of upside."
                ),
                (
                    f"A's rebuttal: {transcript[-1]}\n\n"
                    f"What is your final, non-negotiable concern?\n\n{base_context}"
                ),
                "b2",
            ):
                yield chunk

            # ── ROUND 6: IC Chair — Final Verdict ─────────────────────
            full_debate_summary = "\n\n".join(transcript)
            async for chunk in stream_speaker(
                "D",
                PARTNER_PERSONAS["D"]["instruction"],
                f"Full debate:\n{full_debate_summary}\n\nNow deliver the IC verdict.",
                "d1",
            ):
                yield chunk

            yield "data: [DONE]\n\n"

        except Exception as e:
            print(f"❌ Brainstorm error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_debate(), media_type="text/event-stream")


@app.post("/refine")
async def refine_final(request: RefinementRequest):
    """
    Regenerate the investment memo incorporating:
    - Original public research data (from DB)
    - Expert's proprietary notes (human_notes)
    - IC debate transcript (debate_transcript)
    """
    try:
        report_res = (
            supabase.table("analysis_reports")
            .select("*, companies(*)")
            .eq("id", request.report_id)
            .single()
            .execute()
        )
        prev = report_res.data

        # Pass original report as context so Analyst can reference delta changes
        original_report = prev.get("report_content", "")

        state = {
            "name": prev["companies"]["name"],
            "website": prev["companies"].get("website", ""),
            "industry": prev["companies"].get("industry", ""),
            "location": prev["companies"].get("description", ""),
            "raw_research_data": json.loads(prev.get("research_context") or "[]"),
            "human_notes": request.human_notes,
            "debate_transcript": request.debate_transcript,
            # Inject original report so Analyst knows what changed
            "original_report": original_report,
        }

        analysis = analyst_node(state)
        scores = scorer_node({**state, **analysis})

        update_data = {
            "report_content": analysis["report_content"],
            "scores": scores["scores"],
            "risk_flags": scores["risk_flags"],
        }
        supabase.table("analysis_reports").update(update_data).eq("id", request.report_id).execute()

        return {"status": "success", "analysis": {**analysis, **scores}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
