import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

# 使用稍微高一点的温度 (0.5) 让合伙人们吵架更有个性
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

def debate_node(state: AgentState):
    """
    仿真投委会辩论：A 提出观点，B 针对 A 进行反驳，C 总结陈词。
    """
    company_name = state.get('name')
    human_notes = state.get('human_notes', "")
    research_items = state.get('raw_research_data', [])
    
    # 整理背景资料
    formatted_research = "\n".join([f"Evidence from {item['url']}: {item['content'][:1000]}" for item in research_items])

    print(f"\n--- [Virtual IC] Brainstorming session for: {company_name} ---")
    
    # 🟢 Partner A: 乐观派 - 基于新 Note 强行看多
    prompt_a = f"""
    You are Partner A (The Visionary). Your job is to advocate for the investment.
    User provided these NEW INSIGHTS: {human_notes}
    How do these insights change the game? Ignore the risks for a moment and paint the best-case scenario.
    (Keep it sharp, under 80 words).
    """
    
    # 🔴 Partner B: 怀疑派 - 抓着 A 的观点和 Web 证据打脸
    prompt_b_system = f"""
    You are Partner B (The Skeptic). Your job is to challenge Partner A.
    Use the EXISTING WEB RESEARCH to point out why Partner A's optimism might be misplaced.
    Web Research: {formatted_research}
    Be professional but brutal. (Keep it sharp, under 80 words).
    """
    
    # 🔵 IC Chair: 决策者 - 强行定调
    prompt_c_system = """
    You are the IC Chair. You've heard A's optimism and B's skepticism.
    Review the debate and reach a FINAL CONSENSUS. 
    What is our actual stance? (Keep it under 100 words).
    """

    try:
        # A 说话
        resp_a = llm.invoke([SystemMessage(content=prompt_a)]).content
        print("🟢 Partner A offered an opinion.")
        
        # B 听完 A 说话，开始反驳
        resp_b = llm.invoke([
            SystemMessage(content=prompt_b_system), 
            HumanMessage(content=f"Partner A just said: {resp_a}")
        ]).content
        print("🔴 Partner B countered.")
        
        # C 听完两人的争论，做最后决定
        resp_c = llm.invoke([
            SystemMessage(content=prompt_c_system),
            HumanMessage(content=f"A said: {resp_a}\nB countered: {resp_b}")
        ]).content
        print("🔵 IC Chair reached consensus.")
        
        transcript = [
            f"🟢 Partner A (Visionary): {resp_a}",
            f"🔴 Partner B (Skeptic): {resp_b}",
            f"🔵 IC Chair (Final Decision): {resp_c}"
        ]
        
        return {"debate_transcript": transcript}
    except Exception as e:
        print(f"❌ Debate Error: {e}")
        return {"debate_transcript": [f"System: Committee deliberation failed: {e}"]}
