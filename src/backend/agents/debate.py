import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

# Use a slightly higher temperature (0.4) to encourage diverse perspectives during the debate
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)

def debate_node(state: AgentState):
    """
    Debate Node: Simulates a Virtual Investment Committee (IC) discussion.
    Partners A, B, and C debate the newly provided 'human_notes' against existing research.
    """
    company_name = state.get('name')
    human_notes = state.get('human_notes', "")
    research_context = "\n\n---\n\n".join(state.get('raw_research_data', []))
    
    print(f"\n--- [Virtual IC] Partners are entering the room to debate: {company_name} ---")
    
    # Define the personas based on the firm's philosophy: "We invest in people first."
    
    # 🟢 Partner A: The Visionary (Optimist) - Looks for 'Extraordinary' potential.
    prompt_a = """
    You are Partner A: The Visionary. 
    You focus on identifying the next Canva or Airwallex. 
    Based on the following research and NEW expert notes, advocate for the UPSIDE. 
    How do these new insights prove the founder is 'extraordinary' or has a 'category-defining' vision?
    Be punchy and persuasive. (Max 100 words).
    """
    
    # 🔴 Partner B: The Skeptic (Pessimist) - Protects the fund's capital.
    prompt_b = """
    You are Partner B: The Skeptic. 
    Your job is to find the 'deal-breakers'. 
    Challenge the new expert notes. Is the founder's DNA really that special? 
    Is the 'Unique Insight' just a marginal improvement? Focus on competition, 
    burn rate, and execution risks. Be brutal but professional. (Max 100 words).
    """
    
    # 🔵 Partner C: The Pragmatist (The Closer) - Focuses on 'Founder-Market Fit'.
    prompt_c = """
    You are Partner C: The Pragmatist. 
    You synthesize the points from A and B. 
    Focus on practical next steps: Does this information change our 'Acid Test' questions? 
    Given the notes, is the unit economics story getting better or worse?
    Summarize the path forward for the final memo. (Max 100 words).
    """

    full_context = f"Company: {company_name}\n\nResearch Data:\n{research_context}\n\nNEW Verified Expert Notes:\n{human_notes}"
    
    try:
        # Sequential calls to simulate the conversation flow
        print("🟢 Partner A is speaking...")
        resp_a = llm.invoke([SystemMessage(content=prompt_a), HumanMessage(content=full_context)]).content
        
        print("🔴 Partner B is countering...")
        resp_b = llm.invoke([SystemMessage(content=prompt_b), HumanMessage(content=full_context)]).content
        
        print("🔵 Partner C is concluding...")
        resp_c = llm.invoke([SystemMessage(content=prompt_c), HumanMessage(content=full_context)]).content
        
        # Assemble the transcript for state and frontend display
        transcript = [
            f"🟢 Partner A (Visionary): {resp_a}",
            f"🔴 Partner B (Skeptic): {resp_b}",
            f"🔵 Partner C (Pragmatist): {resp_c}"
        ]
        
        print(f"--- [Virtual IC] Debate Complete. 3 Perspectives captured. ---")
        
        return {
            "debate_transcript": transcript
        }
    except Exception as e:
        print(f"❌ Debate Node Error: {e}")
        return {"debate_transcript": [f"System: Debate simulation failed: {str(e)}"]}
