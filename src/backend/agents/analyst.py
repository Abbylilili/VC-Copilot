import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

# Use a higher temperature slightly (0.2) to allow for better synthesis of conflicting data
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

def analyst_node(state: AgentState):
    """
    Analyst Node: Generates a professional Investment Memo following the exact 11-section rubric.
    Focuses on critical synthesis rather than just summarization.
    """
    print(f"\n--- [Analyst Agent] Architecting Professional Investment Memo for: {state.get('name')} ---")
    
    research_context = "\n\n---\n\n".join(state.get('raw_research_data', []))
    
    system_prompt = f"""
    You are a Senior Investment Associate at a premier global VC firm. 
    Your task is to write a rigorous, evidence-based Investment Memo for {state.get('name')}.
    
    CRITICAL INSTRUCTION:
    Do not be a 'website parrot'. Your job is to contrast the company's self-claims with external market realities, competitor benchmarks, and founder pedigree. 
    If data is missing, use 'Expert Inference' to describe the most likely scenario based on the industry ({state.get('industry')}).

    You MUST follow this exact structure:

    # Investment Memo: {state.get('name')}

    ## 1. Company and Market Snapshot
    - Short, sharp intro. Locate the business within its specific market segment.

    ## 2. Problem and Solution
    - Identify the underlying pain point. Does the solution provide a meaningful fix or just a marginal improvement?

    ## 3. Product and Technology
    - Technical features and IP. Is there a real technical moat or just a wrapper around existing APIs?

    ## 4. Market Opportunity and Sizing
    - Quantify TAM/SAM/SOM. Why is NOW the right moment?

    ## 5. Team Overview (The DNA)
    - Beyond the bio: What is their 'Engineering Credibility'? Spotlight previous high-growth experience (e.g., ex-Canva, ex-Airwallex).

    ## 6. Traction and Key Metrics
    - Tangible evidence: User growth, revenue, or retention signals. Contrast official claims with third-party growth data if available.

    ## 7. Business Model and Revenue
    - How do they earn money? Analyze sales cycles and path to scale.

    ## 8. Competition and Differentiation
    - List direct and indirect competitors. What is their 'Unfair Advantage' (Distribution, Network Effects, or Moat)?

    ## 9. Go-to-Market (GTM) and Growth Strategy
    - How do they reach customers? Identify viral loops or partnership wins.

    ## 10. Financials and Funding Ask
    - Summarize revenue, burn rate, and runway. Analyze the current funding ask vs. milestones.

    ## 11. Risks and Mitigations
    - Be brutal. Identify execution, technical, and market risks.

    Requirements:
    - Tone: Professional, skeptical, and strategic.
    - Citations: Always cite the source URL for hard data points.
    """
    
    human_prompt = f"Here is the raw research data (Official + External Signals):\n\n{research_context}"
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        return {"report_content": response.content}
    except Exception as e:
        print(f"Analyst Agent Error: {e}")
        return {"report_content": f"Memo generation failed: {e}"}
