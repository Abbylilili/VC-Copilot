import os
import requests
from typing import List
from firecrawl import Firecrawl
from .state import AgentState
from urllib.parse import urlparse

def researcher_node(state: AgentState):
    """
    Researcher Node: Hunt for 'Hard Signals' (Pricing, Competitors, Pedigree).
    Explicitly looks for evidence outside of the official website.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY is missing.")
    
    app = Firecrawl(api_key=api_key)
    company_name = state.get('name')
    company_url = state.get('website')
    industry = state.get('industry')
    
    print(f"\n--- [Researcher Agent] Hunting for Hard Signals: {company_name} ---")
    
    all_markdown = []
    processed_urls = set()

    # 1. THE FOUNDATION: Get the official vision
    if company_url:
        try:
            print(f"🎯 Step 1: Mapping the official claim - {company_url}")
            res = app.scrape(company_url, formats=['markdown'])
            content = getattr(res, 'markdown', None) or (res.get('markdown') if isinstance(res, dict) else None)
            if content:
                all_markdown.append(f"OFFICIAL WEBSITE CONTENT:\n\n{content}")
                processed_urls.add(company_url)
        except Exception as e:
            print(f"⚠️ Step 1: Failed to scrape official site: {e}")

    # 2. THE MULTI-TRACK HUNT: Diverse queries to bypass the parrot effect
    domain = urlparse(company_url).netloc if company_url else ""
    
    queries = [
        # Track A: Team Pedigree (Looking for DNA)
        f'"{company_name}" founders career team pedigree ex-Canva ex-Airwallex ex-Atlassian',
        # Track B: Market Evidence & Pricing (The 'Hard' Business)
        f'"{company_name}" pricing model customer reviews business model',
        # Track C: Critical Outside-in (The Reality Check)
        f'"{company_name}" competitors vs analysis risks challenges -site:{domain}'
    ]

    print(f"🧠 Step 2: Sourcing Hard Signals (DNA, Business Model, Competitor Analysis)...")

    serper_url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': os.getenv("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    
    search_urls = []
    for q in queries:
        try:
            payload = {"q": q, "num": 5}
            response = requests.post(serper_url, headers=headers, json=payload)
            results = response.json().get('organic', [])
            search_urls.extend([item['link'] for item in results if item['link'] not in processed_urls])
        except Exception as e:
            print(f"Search failed for {q}: {e}")

    # 3. Deep Scrape signal-heavy pages
    blacklist = ["linkedin.com", "twitter.com", "x.com", "facebook.com"]
    
    for url in list(dict.fromkeys(search_urls))[:6]:
        if any(b in url for b in blacklist): continue
        try:
            print(f"Scraping signal-heavy source: {url}")
            res = app.scrape(url, formats=['markdown'])
            content = getattr(res, 'markdown', None) or (res.get('markdown') if isinstance(res, dict) else None)
            if content:
                print(f"✅ Captured Hard Signal ({len(content)} chars)")
                all_markdown.append(f"SIGNAL SOURCE ({url}):\n\n{content}")
        except Exception as e:
            print(f"❌ Scraping failed {url}: {e}")

    print(f"--- [Researcher Agent] Hunt complete. Collected {len(all_markdown)} diverse signal segments ---")
    
    return {
        "raw_research_data": all_markdown
    }
