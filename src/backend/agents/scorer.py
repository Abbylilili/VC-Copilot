import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

# Initialize LLM with strict JSON response format
# We use temperature 0.1 for high consistency in scoring
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1).bind(
    response_format={"type": "json_object"}
)

def scorer_node(state: AgentState):
    """
    Scorer Node: Critically evaluates the Technical Investment Memo and outputs 
    quantitative scores and risk flags in JSON format.
    """
    print(f"\n--- [Scorer Agent] Scoring the Technical Memo for: {state.get('name')} ---")
    
    report = state.get('report_content', "")
    
    # Fallback if no report was generated
    if not report or "failed" in report.lower():
        return {
            "scores": {"innovation": 0, "market": 0, "team": 0, "moat": 0},
            "risk_flags": ["Missing or Invalid Report Content"],
            "final_score": 0.0,
            "analysis_complete": False
        }

    system_prompt = """
    You are an Investment Committee (IC) Member at a Deep Tech Venture Capital firm.
    Your task is to critically evaluate a Technical Investment Memo and provide quantitative scores (1-10) and risk assessments.

    Evaluation Dimensions:
    1. innovation: Technical novelty, R&D complexity, and disruptiveness.
    2. market: TAM/SAM/SOM potential and industry tailwinds.
    3. team: Engineering pedigree, technical credibility, and execution track record.
    4. moat: Defensibility (IP, data network effects, hardware complexity, etc.).

    You MUST output a JSON object with this EXACT structure:
    {
        "scores": {
            "innovation": int (1-10),
            "market": int (1-10),
            "team": int (1-10),
            "moat": int (1-10)
        },
        "risk_flags": ["Short string describing a specific risk", "..."],
        "summary_score": float (weighted average, e.g., 7.5)
    }

    Guidelines:
    - Be rigorous. A score of 10 is reserved for industry-redefining technology.
    - Identify at least 2-3 specific technical or market risk flags.
    - The summary_score should reflect your overall conviction in the investment.
    """

    human_prompt = f"Please evaluate this Technical Investment Memo for {state.get('name')}:\n\n{report}"

    try:
        # Call LLM to get JSON output
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        # Parse JSON string into Python dictionary
        result = json.loads(response.content)
        
        print(f"--- [Scorer Agent] Scoring Complete. Final Score: {result.get('summary_score')} ---")
        
        # Update the state with scores and risk flags
        return {
            "scores": result.get("scores"),
            "risk_flags": result.get("risk_flags"),
            "final_score": result.get("summary_score"),
            "analysis_complete": True
        }
    except Exception as e:
        print(f"Error in Scorer Agent: {e}")
        return {
            "scores": {"innovation": 0, "market": 0, "team": 0, "moat": 0},
            "risk_flags": [f"Evaluation Error: {str(e)}"],
            "final_score": 0.0,
            "analysis_complete": False
        }
