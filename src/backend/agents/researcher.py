import os
import requests
from typing import List
from firecrawl import Firecrawl 
from .state import AgentState

def researcher_node(state: AgentState):
    """
    调研节点：兼容 Firecrawl v2 Document 对象
    """
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    
    if not firecrawl_key or not serper_key:
        print("❌ CRITICAL ERROR: API Keys missing.")
        return {"raw_research_data": []}
    
    try:
        app = Firecrawl(api_key=firecrawl_key)
    except Exception as e:
        print(f"❌ Firecrawl 初始化失败: {e}")
        return {"raw_research_data": []}
    
    print(f"\n--- [Researcher Agent] 开始调研公司: {state.get('name')} ---")
    
    # Serper 搜索
    search_query = f"{state.get('name')} startup tech product team funding"
    serper_url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': serper_key, 'Content-Type': 'application/json'}
    payload = {"q": search_query, "num": 3}
    
    urls = []
    try:
        response = requests.post(serper_url, headers=headers, json=payload)
        search_results = response.json()
        urls = [item['link'] for item in search_results.get('organic', [])]
        print(f"✅ 找到链接: {urls}")
    except Exception as e:
        print(f"❌ Serper 失败: {e}")

    # Firecrawl 抓取
    all_markdown = []
    for url in urls[:3]:
        try:
            print(f"正在深度爬取: {url}")
            scrape_result = app.scrape(url, formats=['markdown'])
            
            if scrape_result:
                # 兼容 v2 Document 对象
                markdown_content = None
                
                # 方式 1: 如果是对象，尝试获取 .markdown 属性
                if hasattr(scrape_result, 'markdown'):
                    markdown_content = scrape_result.markdown
                # 方式 2: 如果是字典，尝试获取 ['markdown']
                elif isinstance(scrape_result, dict):
                    markdown_content = scrape_result.get('markdown')
                
                if markdown_content:
                    print(f"✅ 成功获取 Markdown ({len(str(markdown_content))} 字符)")
                    all_markdown.append(f"Source: {url}\n\n{markdown_content}")
                else:
                    print(f"⚠️ {url} 抓取成功但内容解析为空。")
            else:
                print(f"⚠️ {url} 返回为空。")
                
        except Exception as e:
            print(f"❌ 爬取 {url} 失败: {e}")

    return {"raw_research_data": all_markdown}
