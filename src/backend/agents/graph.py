from langgraph.graph import StateGraph, END
from .state import AgentState
from .researcher import researcher_node
from .analyst import analyst_node
from .scorer import scorer_node

def create_agent_graph():
    """
    Creates and connects the Investment Copilot agent nodes into a workflow.
    Workflow: START -> Researcher -> Analyst -> Scorer -> END
    """
    
    # 1. Initialize the StateGraph with our AgentState definition
    # This ensures every node knows the "shape" of the data it receives/returns
    workflow = StateGraph(AgentState)

    # 2. Add all the Nodes to the graph
    # Nodes are the actual functions that perform tasks
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("scorer", scorer_node)

    # 3. Define the Edges (The Flow)
    # This defines the sequential execution: once A finishes, automatically move to B
    workflow.add_edge("researcher", "analyst")
    workflow.add_edge("analyst", "scorer")
    
    # 4. Define the End Point
    # Once the Scorer is done, the entire process finishes
    workflow.add_edge("scorer", END)

    # 5. Set the Entry Point
    # The workflow always starts with the Researcher searching for data
    workflow.set_entry_point("researcher")

    # 6. Compile the Graph
    # Compiling turns the graph into a runnable LangChain "Runnable" object
    app = workflow.compile()
    
    return app

# Export the compiled graph instance for use in our API (main.py)
investment_copilot_graph = create_agent_graph()
