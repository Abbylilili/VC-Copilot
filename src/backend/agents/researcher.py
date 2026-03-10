import os
import requests
import json
import re
from typing import List, Dict, Any
from firecrawl import Firecrawl 
from .state import AgentState
from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def researcher_node(state: AgentState):
    """
    终极调研节点：
    1. 域名硬锁定 + LLM 筛选创始人。
    2. 接入 Tavily (竞争对手/融资)。
    3. 接入 NewsAPI (新闻舆情)。
    4. 接入 Exa (市场规模)。
    5. 严格对齐 Analyst 的标签。
    """
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    pdl_key = os.getenv("PDL_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    exa_key = os.getenv("EXA_API_KEY")
    newsapi_key = os.getenv("NEWSAPI_KEY")
    
    name = state.get('name')
    website = state.get('website', '')
    domain = website.replace("https://", "").replace("http://", "").split('/')[0] if website else ""
    
    all_valid_data = []
    identified_founder_names = []
    
    print(f"\n--- [Strategic Researcher] Re-aligning Intelligence for: {name} ---")

    # --- PART 1: Founders & Leadership (Precision Extraction) ---
    combined_text = ""
    if firecrawl_key and domain:
        try:
            app = Firecrawl(api_key=firecrawl_key)
            map_result = app.map(domain)
            links = map_result.get('links', []) if isinstance(map_result, dict) else map_result
            high_value_urls = [l for l in links if any(k in l.lower() for k in ['team', 'leader', 'about', 'founder', 'management'])]
            if not high_value_urls: high_value_urls = [website]
            
            for t_url in high_value_urls[:3]:
                try:
                    t_scrape = app.scrape(t_url, formats=['markdown'])
                    content = getattr(t_scrape, 'markdown', None) or t_scrape.get('markdown', "")
                    if len(content) > 100: combined_text += f"\n{content}\n"
                except: pass
        except: pass

    # Google Fallback for Founders
    if serper_key:
        q = f'who are the founders and leadership of {name} startup'
        try:
            res = requests.post("https://google.serper.dev/search", headers={'X-API-KEY': serper_key}, json={"q": q, "num": 5}).json()
            combined_text += "\n" + "\n".join([item.get('snippet', '') for item in res.get('organic', [])])
        except: pass

    # LLM Entity Resolution
    if combined_text:
        llm_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        extraction_prompt = f"Identify core founders/CEO of {name}. Exclude external advisors or chairmen of other firms. Content: {combined_text[:8000]}. Return comma-separated names or UNKNOWN."
        res_names = llm_mini.invoke([SystemMessage(content=extraction_prompt)]).content
        if "UNKNOWN" not in res_names.upper():
            identified_founder_names = [n.strip() for n in res_names.split(',') if 1 < len(n.split()) < 4]

    # LinkedIn/PDL Deep Dive
    if identified_founder_names:
        for fname in identified_founder_names[:3]:
            q = f'"{fname}" "{name}" linkedin'
            try:
                res = requests.post("https://google.serper.dev/search", headers={'X-API-KEY': serper_key}, json={"q": q, "num": 2}).json()
                for item in res.get('organic', []):
                    link = item.get('link', '')
                    if "linkedin.com/in/" in link:
                        dna_md = f"### FOUNDER DNA: {fname}\n**LinkedIn**: {link}\n**Bio**: {item.get('snippet')}\n"
                        if pdl_key:
                            p_res = requests.get("https://api.peopledatalabs.com/v5/person/enrich", params={'profile': link}, headers={'X-Api-Key': pdl_key})
                            if p_res.status_code == 200:
                                data = p_res.json().get('data', {})
                                for ex in data.get('experience', [])[:5]:
                                    dna_md += f"- **{ex.get('title', {}).get('name')}** at **{ex.get('company', {}).get('name')}**\n"
                        all_valid_data.append({"url": link, "content": dna_md})
                        break
            except: pass

    # --- PART 2: Competitive Intelligence (Crucial Tag Align) ---
    if tavily_key:
        print(f"🕵️ Searching for competitors via Tavily...")
        try:
            tavily = TavilyClient(api_key=tavily_key)
            # 强化搜索，寻找真正的 Peer Startups
            query = f"direct startup competitors and alternatives for {name} ({domain}) -AWS -Azure -Google -Microsoft"
            result = tavily.search(query=query, search_depth="advanced", max_results=5)
            # 必须使用这个标签，否则 Analyst 认不出
            comp_text = "### COMPETITIVE INTELLIGENCE:\n"
            for r in result.get('results', []):
                comp_text += f"- **{r['title']}** ({r['url']}): {r['content'][:350]}\n"
            all_valid_data.append({"url": "Tavily-Comp", "content": comp_text})
        except: pass

    # --- PART 3: Funding & News (NewsAPI) ---
    if newsapi_key:
        try:
            res = requests.get("https://newsapi.org/v2/everything", params={"q": f'"{name}"', "sortBy": "relevancy", "apiKey": newsapi_key}).json()
            news_text = "### RECENT NEWS:\n"
            for art in res.get('articles', [])[:5]:
                news_text += f"- **{art['title']}** ({art['publishedAt'][:10]}): {art.get('description')}\n"
            all_valid_data.append({"url": "NewsAPI", "content": news_text})
        except: pass

    # --- PART 4: Market Size (Exa) ---
    if exa_key:
        try:
            import exa_py
            exa = exa_py.Exa(api_key=exa_key)
            industry = state.get('industry', name)
            res = exa.search_and_contents(f"{industry} market size TAM CAGR research report 2024 2025", num_results=3, text={"max_characters": 600})
            market_text = "### MARKET RESEARCH:\n"
            for r in res.results:
                market_text += f"- **{r.title}** ({r.url}): {r.text}\n"
            all_valid_data.append({"url": "Exa-Market", "content": market_text})
        except: pass

    return {"raw_research_data": all_valid_data}
