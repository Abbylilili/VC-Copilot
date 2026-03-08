import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

def analyst_node(state: AgentState):

    name = state.get('name', '该初创公司')
    print(f"\n--- [Analyst Agent] 正在为 {name} 生成深度报告 ---")
    
    # 1. 整理带链接的原始资料
    research_items = state.get('raw_research_data', [])
    
    formatted_context = ""
    sources_summary = []
    
    for item in research_items:
        url = item.get('url', 'Unknown Source')
        content = item.get('content', '')
        if len(content) > 50:
            formatted_context += f"\n\n--- SOURCE: {url} ---\n\n{content}"
            sources_summary.append(url)
    
    print(f"DEBUG: [Analyst Agent] 使用了来自 {len(sources_summary)} 个信源的数据进行分析")

    if not formatted_context or len(formatted_context) < 100:
        print(f"⚠️ 警告: [Analyst Agent] 调研资料太少，无法生成深度报告。")
        return {"report_content": "Failed: Insufficient research data to generate a technical memo."}

    # 2. Professional Deep Tech VC Analyst Prompt (With Citations)
    system_prompt = f"""
    You are a skeptical Senior Technical Partner at a top-tier Venture Capital firm.
    Your PRIMARY job is to conduct a rigorous technical due diligence report for: **{name}**.

    Guidelines:
    - **Cite Sources**: When mentioning specific technical claims or metrics, try to reference the source URL provided in the context.
    - **No Hallucinations**: If data is missing for a section, write "DATA UNAVAILABLE".
    - **Structure**: Follow the Professional Markdown format (Innovation, Moat, Market, Team, Roadmap, Risks, Verdict).
    """
    
    human_prompt = f"Here is the raw research data and source URLs for {name}:\n\n{formatted_context}"
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        # 在报告末尾自动附上引用列表
        sources_list = "\n\n## Data Sources & Evidence\n" + "\n".join([f"- {url}" for url in sources_summary])
        final_report = response.content + sources_list
        
        print(f"✅ [Analyst Agent] 报告生成完毕 (长度: {len(final_report)} 字符) ---")
        return {
            "report_content": final_report
        }
    except Exception as e:
        print(f"❌ Analyst Agent 运行出错: {e}")
        return {"report_content": f"Failed: Error during report generation: {e}"}
