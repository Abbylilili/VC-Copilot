import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

def analyst_node(state: AgentState):
    name = state.get('name', 'Startup')
    print(f"\n--- [Analyst Agent] Synthesizing Intelligence for: {name} ---")
    
    # 1. Gather all inputs
    research_items = state.get('raw_research_data', [])
    human_notes = state.get('human_notes', "")
    debate_transcript = state.get('debate_transcript', [])
    
    # 2. Determine if this is an INITIAL report or a REFINED report
    is_refined = len(debate_transcript) > 0 or len(human_notes) > 0
    
    # 3. Format context
    formatted_context = f"### STARTUP: {name} (Location: {state.get('location')})\n"
    
    if human_notes:
        formatted_context += f"\n### CRITICAL EXPERT NOTES (Added by User):\n{human_notes}\n"
    
    if debate_transcript:
        formatted_context += f"\n### INTERNAL COMMITTEE BRAINSTORMING TRANSCRIPT:\n" + "\n".join(debate_transcript) + "\n"
    
    sources_summary = []
    if research_items:
        formatted_context += "\n### WEB RESEARCH DATA:\n"
        for item in research_items:
            url = item.get('url', 'Unknown')
            content = item.get('content', '')
            formatted_context += f"- SOURCE [{url}]: {content[:2000]}\n"
            sources_summary.append(url)
    
    # 4. Dynamic Prompt based on stage
    debate_instruction = ""
    if is_refined:
        debate_instruction = """
        ## 5. Synthesis of Expert/Internal Debate
        Summarize the key points of disagreement and the final consensus reached during the internal brainstorming session. 
        How did the new expert notes change our initial hypothesis?
        """
    
    system_prompt = f"""
    You are a skeptical Senior Technical Partner. Generate a high-fidelity Technical Investment Memo for: {name}.

    REPORT STRUCTURE:
    # Technical Investment Memo: {name}
    ## 1. Core Innovation & Hypothesis
    ## 2. Competitive Landscape
    ## 3. Technical Feasibility & Moat
    ## 4. Key Risks (Technical & Execution)
    {debate_instruction}

    STRICT RULE:
    - If no internal debate is provided in the context, DO NOT include Section 5 and DO NOT invent any "internal discussions".
    - Focus strictly on the Web Research Data for the initial memo.
    """
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=formatted_context)])
        
        # Append Citations
        citation_footer = "\n\n## Data Sources & Evidence\n"
        if sources_summary:
            citation_footer += "\n".join([f"- {url}" for url in sources_summary])
        if human_notes:
            citation_footer += "\n- [INTERNAL] Proprietary Expert Insights"
            
        return {"report_content": response.content + citation_footer}
    except Exception as e:
        print(f"❌ Analyst Error: {e}")
        return {"report_content": f"Failed to generate report: {e}"}
