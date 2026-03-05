from typing import List, TypedDict, Dict

class AgentState(TypedDict):
    """Defines the state of an agent, including its name, description, and current task."""
    name: str
    description: str
    website: str
    industry: str

    raw_research_data:List[str]

    report_content: str

    scores: Dict[str, int]
    risk_flags: List[str]
    final_score: float

    analysis_complete: bool