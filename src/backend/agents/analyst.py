import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

def analyst_node(state: AgentState):

    print(f"\n--- [Analyst Agent] 正在为 {state.get('name', '该初创公司')} 生成深度报告 ---")
    
    # 1. 整理原始资料：将列表中的 Markdown 内容合并成一个大文本
    research_context_list = state.get('raw_research_data', [])
    research_context = "\n\n---\n\n".join(research_context_list)
    
    if not research_context:
        print("警告: [Analyst Agent] 原始调研资料为空，无法生成深度报告。")
        return {"report_content": "由于无法获取该公司的足够调研资料，报告生成失败。"}

    # 2. Professional Deep Tech VC Analyst Prompt (English)
    system_prompt = f"""
    You are a Senior Technical Partner at a top-tier Venture Capital (VC) firm.
    Your task is to conduct a deep technical evaluation and business potential analysis for the startup: {state.get('name')}, based on the provided raw research data.

    Structure of the Analysis (Output in professional Markdown):
    # Technical Investment Memo: {state.get('name')}

    ## 1. Deep Tech & Innovation
    - What is the core technical architecture? 
    - What specific, high-difficulty engineering or scientific problems are they solving?
    - Is the technology choice forward-looking and scalable?

    ## 2. Technical Moat & Intellectual Property (IP)
    - How deep is the technical moat? (e.g., algorithmic complexity, data network effects, hardware patents, or extreme engineering execution).
    - How difficult and time-consuming would it be for a competitor to reverse-engineer or replicate this technology?

    ## 3. Market Disruption Potential
    - How does this technology disrupt current industry paradigms or existing solutions?
    - Estimate the market potential (TAM/SAM/SOM), focusing on the incremental market created by this technology.

    ## 4. Technical Team Background
    - Does the founding team have pedigree from top-tier tech companies, research institutions, or elite laboratories?
    - Does the team have a proven track record (Engineering Credibility) of delivering complex technical products from 0 to 1?

    ## 5. R&D Roadmap & Traction
    - What is the current stage? (e.g., Lab/PoC, MVP, Pilot, Commercial Scale).
    - Are there verifiable technical data, PoC results, or feedback from core enterprise customers?

    Requirements:
    - **Rigorous & Evidence-Based**: Avoid empty buzzwords. Focus on technical parameters, architectural logic, and engineering feasibility.
    - **No Hallucinations**: Analyze ONLY based on the provided data. If critical technical details are missing, label them as "Requires further Due Diligence (DD)".
    - **Professional Tone**: Use precise, sophisticated tech-investment terminology.
    """
    
    human_prompt = f"Here is the raw research data for {state.get('name')}:\n\n{research_context}"
    
    # 3. 调用 OpenAI 生成报告
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        # 4. 更新 Agent 状态中的 report_content 字段
        print(f"--- [Analyst Agent] 报告生成完毕 (长度: {len(response.content)} 字符) ---")
        return {
            "report_content": response.content
        }
    except Exception as e:
        print(f"Analyst Agent 运行出错: {e}")
        return {"report_content": f"报告生成过程中发生不可预知的错误: {e}"}
