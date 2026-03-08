import os
import requests
from typing import List, Dict, Any
from firecrawl import Firecrawl 
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

# 使用一个极低温度的 LLM 专门负责“内容分拣”
filter_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def researcher_node(state: AgentState):
    """
    调研节点：引入 location (国家/地区) 过滤，进一步消除重名干扰。
    """
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    
    company_name = state.get('name')
    website = state.get('website', '')
    location = state.get('location', '')
    
    if not firecrawl_key or not serper_key:
        print("❌ CRITICAL ERROR: API Keys missing.")
        return {"raw_research_data": []}
    
    try:
        app = Firecrawl(api_key=firecrawl_key)
    except Exception as e:
        print(f"❌ Firecrawl 初始化失败: {e}")
        return {"raw_research_data": []}
    
    print(f"\n--- [Researcher Agent] 开始调研: {company_name} (地区: {location}) ---")
    
    # 1. 搜索词构建：加入国家/地区关键词
    # 示例: "Stripe" startup tech funding Israel
    search_query = f'"{company_name}" startup OR tech'
    if location:
        search_query += f' "{location}"'
    if website:
        search_query = f"{search_query} OR site:{website}"
        
    serper_url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': serper_key, 'Content-Type': 'application/json'}
    payload = {"q": search_query, "num": 6}
    
    urls = []
    try:
        response = requests.post(serper_url, headers=headers, json=payload)
        search_results = response.json()
        urls = [item['link'] for item in search_results.get('organic', [])]
        print(f"✅ 找到 {len(urls)} 个候选链接")
    except Exception as e:
        print(f"❌ Serper 失败: {e}")

    # 2. 抓取与语义过滤
    all_valid_data = []
    for url in urls[:5]:
        if any(domain in url for domain in ["linkedin.com/in", "twitter.com", "facebook.com"]):
            continue
            
        try:
            print(f"🔍 正在抓取并核对: {url}")
            scrape_result = app.scrape(url, formats=['markdown'])
            
            if scrape_result:
                markdown_content = getattr(scrape_result, 'markdown', None) or scrape_result.get('markdown')
                
                if markdown_content and len(markdown_content) > 200:
                    # --- 增强版 LLM 语义核对 (包含地理位置信息) ---
                    verification_prompt = f"""
                    You are a data validation assistant for a VC firm. 
                    Target Startup: "{company_name}"
                    Expected Location: "{location}"
                    Target Website: "{website}"

                    Task: Is this text about the startup "{company_name}" based in "{location}"? 
                    If the location matches or is plausible for this company, answer YES.
                    If the text is about a different company with the same name in a different country, answer NO.
                    
                    Text snippet:
                    {markdown_content[:2000]}

                    Answer ONLY "YES" or "NO".
                    """
                    
                    try:
                        res = filter_llm.invoke([SystemMessage(content=verification_prompt)]).content.strip().upper()
                        if "YES" in res:
                            print(f"✅ 验证通过 (地区匹配): {url}")
                            all_valid_data.append({"url": url, "content": markdown_content})
                        else:
                            print(f"⚠️ 验证失败 (可能为异地重名): {url}")
                    except:
                        if company_name.lower() in markdown_content.lower():
                            all_valid_data.append({"url": url, "content": markdown_content})
        except Exception as e:
            print(f"❌ 爬取 {url} 失败: {e}")

    return {"raw_research_data": all_valid_data}
