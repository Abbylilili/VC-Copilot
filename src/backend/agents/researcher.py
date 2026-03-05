import os
import requests
from typing import List
from firecrawl import Firecrawl  # 注意：新版 SDK 是 Firecrawl 而不是 FirecrawlApp
from .state import AgentState

def researcher_node(state: AgentState):
    """
    调研节点：负责根据公司名称搜索并抓取网页内容。
    """
    # 1. 检查 API Key 并初始化 Firecrawl
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL ERROR: FIRECRAWL_API_KEY is missing in .env.")
    
    # 初始化新版 Firecrawl SDK
    app = Firecrawl(api_key=api_key)
    
    print(f"\n--- [Researcher Agent] 开始调研公司: {state.get('name')} ---")
    
    # 2. 使用 Serper API 进行 Google 搜索
    search_query = f"{state.get('name')} startup tech product team funding"
    serper_url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    payload = {"q": search_query, "num": 3}
    
    try:
        response = requests.post(serper_url, headers=headers, json=payload)
        response.raise_for_status()
        search_results = response.json()
        urls = [item['link'] for item in search_results.get('organic', [])]
        print(f"找到链接: {urls}")
    except Exception as e:
        print(f"Serper 搜索失败: {e}")
        urls = []

    # 3. 使用 Firecrawl 爬取内容
    all_markdown = []
    for url in urls[:3]:
        try:
            print(f"正在深度爬取并解析 (Markdown): {url}")
            # 新版方法是 .scrape()，直接传入参数，不再使用 params
            scrape_result = app.scrape(url, formats=['markdown'])
            
            # DEBUG: Print the keys in scrape_result
            print(f"Scrape result keys for {url}: {list(scrape_result.keys()) if scrape_result else 'None'}")
            
            if scrape_result and 'markdown' in scrape_result:
                markdown_content = scrape_result['markdown']
                print(f"成功获取 Markdown (长度: {len(markdown_content)})")
                content = f"Source: {url}\n\n{markdown_content}"
                all_markdown.append(content)
            else:
                print(f"警告: Scrape result 中未找到 'markdown' 字段")
        except Exception as e:
            print(f"爬取 {url} 失败: {e}")

    print(f"--- [Researcher Agent] 调研结束，共采集到 {len(all_markdown)} 段资料 ---")
    return {"raw_research_data": all_markdown}
