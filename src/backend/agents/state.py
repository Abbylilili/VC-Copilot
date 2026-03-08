from typing import List, TypedDict, Dict, Any

class AgentState(TypedDict):
    """
    The state of the investment copilot agent.
    Includes fields for automated research, human refinement, and internal debate.
    """
    # --- Input Layer ---
    name: str
    website: str
    industry: str
    location: str # New field for country/region
    
    # --- Research & Evidence (Researcher Agent) ---
    # Each item: {"url": "https://...", "content": "Markdown text..."}
    raw_research_data: List[Dict[str, Any]] 
    
    # --- Human Refinement (Manual Input) ---
    human_notes: str 
    
    # --- Virtual IC Debate (Committee Agent) ---
    debate_transcript: List[str]
    
    # --- Final Output Layer (Analyst & Scorer) ---
    report_content: str 
    
    # Quantitative scores and risk assessment.
    scores: Dict[str, int]
    risk_flags: List[str]
    final_score: float
    
    # The simulated vote result (e.g., "INVEST (3/3 Yes Votes)").
    vote_summary: str
    
    # --- Flow Control ---
    analysis_complete: bool
