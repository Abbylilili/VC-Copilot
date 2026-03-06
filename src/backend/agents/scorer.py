import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

# Initialize LLM with strict JSON formatting
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1).bind(
    # Ensure standard JSON output for reliable parsing
    response_format={"type": "json_object"}
)

def scorer_node(state: AgentState):
    """
    Scorer Node: Simulates a Global Partner Vote (3-Yes System).
    Evaluates based on Founder DNA, Category Creation, and Moat.
    """
    print(f"\n--- [Scorer Agent] Simulating Global Partner Vote for: {state.get('name')} ---")
    
    report = state.get('report_content', "")
    
    if not report or "failed" in report:
        return {
            "scores": {"team_dna": 0, "category": 0, "moat": 0, "economics": 0},
            "risk_flags": ["Briefing Note Missing"],
            "final_score": 0.0,
            "vote_summary": "Process Failed",
            "analysis_complete": False
        }

    system_prompt = """
    You are the Global Investment Committee (IC) of a top-tier early-stage VC firm.
    Our process requires THREE 'YES' votes from the partners to issue a term sheet.

    Evaluation Criteria (Weighted):
    - Team DNA (40%): Extraordinary pedigree, execution signals, and AI immersion.
    - Category Creation (30%): TAM potential, 'Why Now' timing, and industry shift.
    - Moat (20%): Data flywheels, network effects, and defensibility.
    - Economics (10%): LTV/CAC potential and capital efficiency.

    You MUST output a JSON object with this structure:
    {
        "votes": {
            "partner_1": "Yes/No",
            "partner_2": "Yes/No",
            "partner_3": "Yes/No"
        },
        "scores": {
            "team_dna": int (1-10),
            "category": int (1-10),
            "moat": int (1-10),
            "economics": int (1-10)
        },
        "risk_flags": ["string", "string"],
        "summary_conviction": float (1.0 - 10.0),
        "verdict": "INVEST" or "PASS"
    }

    Note: A 'Yes' vote requires a conviction that this could be a $1B+ company.
    If the founders have pedigree from top unicorns (e.g. Canva, Airwallex), weigh the team score higher.
    """

    human_prompt = f"Please evaluate this IC Briefing Note and cast your votes:\n\n{report}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        result = json.loads(response.content)
        
        # Format the summary for the database
        total_yes = list(result['votes'].values()).count("Yes")
        vote_summary = f"Result: {result['verdict']} ({total_yes}/3 Yes Votes)"
        
        print(f"--- [Scorer Agent] Vote Result: {vote_summary} ---")
        
        return {
            "scores": result.get("scores"),
            "risk_flags": result.get("risk_flags"),
            "final_score": result.get("summary_conviction"),
            "vote_summary": vote_summary,
            "analysis_complete": True
        }
    except Exception as e:
        print(f"Scorer Agent Error: {e}")
        return {
            "scores": {"team_dna": 0, "category": 0, "moat": 0, "economics": 0},
            "risk_flags": [f"Scoring System Error: {str(e)}"],
            "final_score": 0.0,
            "vote_summary": "Error",
            "analysis_complete": False
        }
