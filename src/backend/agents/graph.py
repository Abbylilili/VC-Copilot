from langgraph.graph import StateGraph, END
from .state import AgentState
from .researcher import researcher_node
from .analyst import analyst_node
from .scorer import scorer_node
from .debate import debate_node

def route_start(state: AgentState):
    """
    Router: Determines where to start the workflow.
    If human_notes are present, we skip research and start with a committee debate.
    Otherwise, we start with standard automated research.
    """
    if state.get("human_notes") and len(state.get("human_notes", "").strip()) > 0:
        print("💡 [Router] Human notes detected. Starting with Virtual IC Debate.")
        return "debate"
    print("🚀 [Router] No human notes. Starting with Automated Research.")
    return "researcher"

def create_agent_graph():
    """
    Creates the Investment Copilot workflow with Human-in-the-Loop capabilities.
    Flow 1 (Initial): Start -> Researcher -> Analyst -> Scorer -> END
    Flow 2 (Refine):  Start -> Debate -> Analyst -> Scorer -> END
    """
    
    # 1. Initialize StateGraph
    workflow = StateGraph(AgentState)

    # 2. Add all Nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("debate", debate_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("scorer", scorer_node)

    # 3. Set Conditional Entry Point
    # This allows us to use the same graph for both first-time generation and refinement.
    workflow.set_conditional_entry_point(
        route_start,
        {
            "researcher": "researcher",
            "debate": "debate"
        }
    )

    # 4. Define Edges
    # Researcher leads to initial analysis
    workflow.add_edge("researcher", "analyst")
    
    # Debate (after human input) also leads to analysis (refinement)
    workflow.add_edge("debate", "analyst")
    
    # Analysis always leads to scoring
    workflow.add_edge("analyst", "scorer")
    
    # Scoring ends the process
    workflow.add_edge("scorer", END)

    # 5. Compile
    app = workflow.compile()
    
    return app

# Export the compiled graph instance
investment_copilot_graph = create_agent_graph()
