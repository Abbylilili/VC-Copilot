import os
import requests
from typing import List, Dict, Any
from firecrawl import Firecrawl 
from .state import AgentState

def researcher_node(state: AgentState):
    """
    深度调研节点：强制优先抓取官网，确保分析有据可依。
    """
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    
    name = state.get('name')
    website = state.get('website', '')
    industry = state.get('industry', '')
    location = state.get('location', '')
    
    if not firecrawl_key:
        return {"raw_research_data": [{"url": "Error", "content": "FIRECRAWL_API_KEY Missing"}]}

    try:
        app = Firecrawl(api_key=firecrawl_key)
    except Exception as e:
        return {"raw_research_data": [{"url": "Error", "content": f"Init failed: {e}"}]}

    print(f"\n--- [Researcher Agent] Deep Researching: {name} ---")
    
    all_valid_data = []
    urls_to_crawl = []

    # 1. 策略：如果用户提供了官网，它是最高优先级的信源
    if website:
        # 规范化 URL
        clean_url = website if website.startswith("http") else f"https://{website}"
        urls_to_crawl.append(clean_url)
        print(f"🎯 优先锁定官网: {clean_url}")

    # 2. 补充：通过 Serper 寻找新闻和第三方分析
    search_query = f'"{name}" {industry} startup {location} funding tech'
    try:
        headers = {'X-API-KEY': serper_key, 'Content-Type': 'application/json'}
        payload = {"q": search_query, "num": 5}
        res = requests.post("https://google.serper.dev/search", headers=headers, json=payload).json()
        search_urls = [item['link'] for item in res.get('organic', [])]
        for u in search_urls:
            if u not in urls_to_crawl:
                urls_to_crawl.append(u)
    except Exception as e:
        print(f"⚠️ Serper Search failed: {e}")

    # 3. 执行深度抓取
    for url in urls_to_crawl[:4]: # 抓取前 4 个最重要的链接
        if any(bad in url for bad in ["linkedin.com", "twitter.com", "facebook.com"]): continue
        
        try:
            print(f"🌐 Scrapping: {url}...")
            scrape = app.scrape(url, formats=['markdown'])
            content = getattr(scrape, 'markdown', None) or scrape.get('markdown', "")
            
            if content and len(content) > 200:
                print(f"✅ Data secured from {url} ({len(content)} chars)")
                all_valid_data.append({"url": url, "content": content})
            else:
                print(f"⚠️ Content too thin for {url}")
        except Exception as e:
            print(f"❌ Failed to crawl {url}: {e}")

    # 4. 兜底逻辑：如果连官网都爬不到，至少留个记号
    if not all_valid_data:
        print("🚨 CRITICAL: No web data found. Analyst will have to rely on internal knowledge.")

    return {"raw_research_data": all_valid_data}
