import os
import requests
import json
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .state import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage


# ──────────────────────────────────────────────
# Helper: Serper Google Search
# ──────────────────────────────────────────────
def _serper_search(serper_key: str, query: str, num: int = 8) -> str:
    """Execute a Google search via Serper and return formatted results."""
    if not serper_key:
        return ""
    try:
        res = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=12,
        ).json()

        parts = []
        # Knowledge Graph (highest value)
        kg = res.get("knowledgeGraph", {})
        if kg:
            parts.append(f"[Knowledge Graph] {json.dumps(kg, ensure_ascii=False)[:600]}")

        # Organic results
        for item in res.get("organic", []):
            title   = item.get("title", "")
            link    = item.get("link", "")
            snippet = item.get("snippet", "")
            sitelinks = " | ".join([s.get("title", "") for s in item.get("sitelinks", [])])
            row = f"[{title}]({link}): {snippet}"
            if sitelinks:
                row += f" (pages: {sitelinks})"
            parts.append(row)

        # News box
        for item in res.get("news", []):
            parts.append(f"[NEWS] {item.get('title','')} ({item.get('date','')}): {item.get('snippet','')}")

        return "\n".join(parts)
    except Exception as e:
        print(f"  ❌ Serper failed for '{query[:60]}': {e}")
        return ""


# ──────────────────────────────────────────────
# Helper: Firecrawl page scraper (SDK-version safe)
# ──────────────────────────────────────────────
def _init_firecrawl(api_key: str):
    """Return a Firecrawl app instance, handling both SDK naming conventions."""
    try:
        from firecrawl import FirecrawlApp
        return FirecrawlApp(api_key=api_key)
    except ImportError:
        pass
    try:
        from firecrawl import Firecrawl
        return Firecrawl(api_key=api_key)
    except ImportError:
        print("  ❌ Firecrawl SDK not installed (pip install firecrawl-py)")
        return None


def _firecrawl_scrape(app, url: str) -> str:
    """Scrape a URL via Firecrawl, handling both old and new SDK response formats."""
    try:
        # New SDK: scrape_url
        try:
            result = app.scrape_url(url, params={"formats": ["markdown"]})
        except AttributeError:
            result = app.scrape(url, formats=["markdown"])

        if isinstance(result, dict):
            return result.get("markdown", "") or result.get("content", "")
        return getattr(result, "markdown", "") or getattr(result, "content", "") or ""
    except Exception as e:
        print(f"  ❌ Firecrawl scrape failed for {url}: {e}")
        return ""


# ══════════════════════════════════════════════
# MAIN RESEARCHER NODE
# ══════════════════════════════════════════════
def researcher_node(state: AgentState) -> dict:
    """
    Maximum-coverage research node for VC due diligence.

    Data collection layers (8 total):
    1.  Website scraping           – Firecrawl (product, team pages)
    2.  Founder identity           – Serper multi-query + LLM entity resolution
    3.  Founder career DNA         – Serper LinkedIn + PDL enrichment
    4.  Funding & Crunchbase       – Serper (CB, Pitchbook, TechCrunch)
    5.  Product & traction         – Serper (ARR, customers, growth signals)
    6.  Competitor landscape       – Tavily deep search + Serper supplement
    7.  News & sentiment           – NewsAPI + Serper news
    8.  Market size (TAM/CAGR)     – Exa + Serper analyst reports
    """
    # ── API keys ──────────────────────────────
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    serper_key    = os.getenv("SERPER_API_KEY")
    pdl_key       = os.getenv("PDL_API_KEY")
    tavily_key    = os.getenv("TAVILY_API_KEY")
    exa_key       = os.getenv("EXA_API_KEY")
    newsapi_key   = os.getenv("NEWSAPI_KEY")

    # ── State ─────────────────────────────────
    name     = state.get("name", "")
    website  = state.get("website", "")
    industry = state.get("industry", name)
    location = state.get("location", "")
    domain   = re.sub(r"^https?://", "", website).split("/")[0] if website else ""

    all_valid_data: List[Dict[str, Any]] = []
    identified_founders: List[str] = []

    print(f"\n{'='*60}")
    print(f"[Researcher] Starting deep-dive on: {name}")
    print(f"  Keys: firecrawl={bool(firecrawl_key)} | serper={bool(serper_key)} | "
          f"tavily={bool(tavily_key)} | newsapi={bool(newsapi_key)} | "
          f"exa={bool(exa_key)} | pdl={bool(pdl_key)}")
    print(f"{'='*60}\n")

    # ══════════════════════════════════════════
    # LAYER 1: Website Scraping (Firecrawl)
    # ══════════════════════════════════════════
    print("🌐 [Layer 1] Scraping company website...")
    website_text = ""

    if firecrawl_key and domain:
        fc_app = _init_firecrawl(firecrawl_key)
        if fc_app:
            try:
                # Map the domain to find all pages
                try:
                    map_result = fc_app.map(f"https://{domain}")
                except Exception:
                    map_result = fc_app.map(domain)

                links = []
                if isinstance(map_result, dict):
                    links = map_result.get("links", [])
                elif isinstance(map_result, list):
                    links = map_result

                print(f"  Found {len(links)} pages on {domain}")

                # Prioritize high-value pages
                priority_keywords = ["team", "about", "founder", "leadership", "management",
                                     "product", "solution", "customer", "case-study",
                                     "pricing", "blog", "press", "news"]
                priority_urls = [l for l in links
                                 if any(k in l.lower() for k in priority_keywords)]
                # Fallback: homepage
                if not priority_urls:
                    priority_urls = [website] if website else []

                # Scrape up to 6 pages concurrently
                scrape_targets = list(dict.fromkeys(priority_urls[:6]))  # deduplicate
                with ThreadPoolExecutor(max_workers=4) as pool:
                    futures = {pool.submit(_firecrawl_scrape, fc_app, u): u
                               for u in scrape_targets}
                    for fut in as_completed(futures):
                        url = futures[fut]
                        content = fut.result()
                        if content and len(content) > 150:
                            website_text += f"\n### PAGE: {url}\n{content[:3000]}\n"
                            print(f"  ✅ Scraped {url} ({len(content)} chars)")

            except Exception as e:
                print(f"  ❌ Firecrawl map failed: {e}")

    if website_text:
        all_valid_data.append({
            "url": f"Website-{domain}",
            "content": f"### COMPANY WEBSITE DATA:\n{website_text}"
        })

    # ══════════════════════════════════════════
    # LAYER 2: Founder Identity Resolution
    # ══════════════════════════════════════════
    print("\n🧑 [Layer 2] Identifying founders & leadership...")
    founder_raw_text = website_text  # seed with website content

    if serper_key:
        founder_queries = [
            f'"{name}" founders CEO CTO founder startup',
            f'"{name}" {domain} leadership team who started',
            f'site:linkedin.com/in "{name}" founder OR CEO OR co-founder',
            f'"{name}" {location} startup founder background',
        ]
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(_serper_search, serper_key, q, 6): q
                       for q in founder_queries}
            for fut in as_completed(futures):
                result = fut.result()
                if result:
                    founder_raw_text += f"\n{result}"

    if founder_raw_text.strip():
        try:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            prompt = (
                f'Identify the core founders and C-suite executives (CEO, CTO, COO, CFO) '
                f'of the startup named "{name}".\n'
                f'Rules: Only include people who directly founded or lead THIS company. '
                f'Exclude external investors, board members of other firms, and advisors.\n'
                f'Content:\n{founder_raw_text[:10000]}\n\n'
                f'Return ONLY a comma-separated list of full names, or UNKNOWN.'
            )
            res = llm.invoke([SystemMessage(content=prompt)]).content.strip()
            print(f"  LLM resolved founders: {res}")
            if "UNKNOWN" not in res.upper() and res:
                identified_founders = [
                    n.strip() for n in res.split(",")
                    if 1 < len(n.strip().split()) <= 4 and len(n.strip()) > 2
                ]
        except Exception as e:
            print(f"  ❌ LLM founder extraction failed: {e}")

    # ══════════════════════════════════════════
    # LAYER 3: Founder Career DNA (LinkedIn + PDL)
    # ══════════════════════════════════════════
    print(f"\n🔬 [Layer 3] Deep-diving {len(identified_founders)} founders...")

    def _build_founder_dna(fname: str) -> Optional[Dict]:
        dna = f"### FOUNDER DNA: {fname}\n"

        if serper_key:
            # Profile search
            profiles = _serper_search(
                serper_key,
                f'"{fname}" "{name}" site:linkedin.com OR site:twitter.com OR site:crunchbase.com',
                num=4,
            )
            if profiles:
                dna += f"**Online Profiles**:\n{profiles}\n\n"

            # Career & education
            background = _serper_search(
                serper_key,
                f'"{fname}" career history education university previous company startup',
                num=5,
            )
            if background:
                dna += f"**Career Background**:\n{background}\n\n"

            # Press mentions
            press = _serper_search(
                serper_key,
                f'"{fname}" interview press TechCrunch Forbes Bloomberg startup founder',
                num=3,
            )
            if press:
                dna += f"**Press & Interviews**:\n{press}\n\n"

        # PDL enrichment via LinkedIn URL
        if pdl_key and serper_key:
            try:
                li_search = _serper_search(
                    serper_key,
                    f'"{fname}" linkedin.com/in site:linkedin.com',
                    num=2,
                )
                li_match = re.search(
                    r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+', li_search
                )
                if li_match:
                    li_url = li_match.group(0).rstrip(")")
                    dna += f"**LinkedIn**: {li_url}\n"
                    p_res = requests.get(
                        "https://api.peopledatalabs.com/v5/person/enrich",
                        params={"profile": li_url},
                        headers={"X-Api-Key": pdl_key},
                        timeout=10,
                    )
                    if p_res.status_code == 200:
                        data = p_res.json().get("data", {})
                        edu = [e.get("school", {}).get("name", "")
                               for e in data.get("education", [])[:3]
                               if e.get("school", {}).get("name")]
                        if edu:
                            dna += f"**Education (PDL)**: {', '.join(edu)}\n"
                        for ex in data.get("experience", [])[:5]:
                            title   = ex.get("title", {}).get("name", "N/A")
                            company = ex.get("company", {}).get("name", "N/A")
                            dna += f"- **{title}** at **{company}**\n"
                    elif p_res.status_code == 404:
                        print(f"  PDL: no record for {fname}")
                    else:
                        print(f"  PDL error {p_res.status_code} for {fname}: {p_res.text[:100]}")
            except Exception as e:
                print(f"  ❌ PDL enrichment failed for {fname}: {e}")

        if len(dna) < 80:
            return None
        return {"url": f"FounderDNA-{fname.replace(' ', '_')}", "content": dna}

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(_build_founder_dna, fn) for fn in identified_founders[:4]]
        for fut in as_completed(futures):
            result = fut.result()
            if result:
                all_valid_data.append(result)
                print(f"  ✅ Founder DNA built: {result['url']}")

    # ══════════════════════════════════════════
    # LAYER 4: Funding & Crunchbase Intelligence
    # ══════════════════════════════════════════
    print("\n💰 [Layer 4] Searching funding & Crunchbase data...")
    funding_parts = []

    if serper_key:
        funding_queries = [
            f'"{name}" funding raised investment round crunchbase pitchbook',
            f'"{name}" series seed angel venture capital raised million',
            f'site:crunchbase.com/organization "{name}"',
            f'"{name}" {domain} valuation investors 2024 2025',
            f'"{name}" term sheet acquisition IPO exit',
        ]
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(_serper_search, serper_key, q, 6): q
                       for q in funding_queries}
            for fut in as_completed(futures):
                r = fut.result()
                if r:
                    funding_parts.append(r)

    if funding_parts:
        all_valid_data.append({
            "url": "Crunchbase-Funding-Intel",
            "content": "### CRUNCHBASE DATA:\n" + "\n\n---\n\n".join(funding_parts),
        })
        print(f"  ✅ Collected {len(funding_parts)} funding data sources")

    # ══════════════════════════════════════════
    # LAYER 5: Product & Traction Signals
    # ══════════════════════════════════════════
    print("\n📊 [Layer 5] Searching product & traction signals...")
    traction_parts = []

    if serper_key:
        traction_queries = [
            f'"{name}" ARR revenue MRR customers growth 2024 2025',
            f'"{name}" product launch feature update case study',
            f'"{name}" enterprise customer logo partnership deal',
            f'"{name}" user growth waitlist sign-up launch',
            f'"{name}" site:techcrunch.com OR site:venturebeat.com OR site:forbes.com',
            f'"{name}" glassdoor headcount employee hiring job',
            f'"{name}" {industry} demo awards recognition',
        ]
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(_serper_search, serper_key, q, 6): q
                       for q in traction_queries}
            for fut in as_completed(futures):
                r = fut.result()
                if r:
                    traction_parts.append(r)

    if traction_parts:
        all_valid_data.append({
            "url": "Traction-Product-Signals",
            "content": "### PRODUCT & TRACTION:\n" + "\n\n---\n\n".join(traction_parts),
        })
        print(f"  ✅ Collected {len(traction_parts)} traction data sources")

    # ══════════════════════════════════════════
    # LAYER 6: Competitive Landscape
    # ══════════════════════════════════════════
    print("\n🕵️ [Layer 6] Mapping competitive landscape...")
    comp_parts = []

    # Tavily deep competitor search
    if tavily_key:
        try:
            from tavily import TavilyClient
            tavily = TavilyClient(api_key=tavily_key)
            tavily_queries = [
                f"direct competitors and alternatives to {name} in {industry} market",
                f"{name} vs competitors comparison {industry} 2024 2025",
                f"top {industry} startups competing with {name}",
            ]
            for tq in tavily_queries:
                try:
                    result = tavily.search(
                        query=tq, search_depth="advanced", max_results=6
                    )
                    rows = [
                        f"- **{r['title']}** ({r['url']}): {r['content'][:400]}"
                        for r in result.get("results", [])
                    ]
                    if rows:
                        comp_parts.append("\n".join(rows))
                        print(f"  ✅ Tavily: {tq[:55]}...")
                except Exception as e:
                    print(f"  ❌ Tavily query failed: {e}")
        except Exception as e:
            print(f"  ❌ Tavily client init failed: {e}")

    # Serper competitor supplement
    if serper_key:
        serper_comp_queries = [
            f'"{name}" alternatives competitors similar startups {industry}',
            f'{industry} startup landscape map 2024 2025 players',
            f'"{name}" competitor analysis {location}',
        ]
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(_serper_search, serper_key, q, 8): q
                       for q in serper_comp_queries}
            for fut in as_completed(futures):
                r = fut.result()
                if r:
                    comp_parts.append(r)

    if comp_parts:
        all_valid_data.append({
            "url": "Competitive-Intel-Combined",
            "content": "### COMPETITIVE INTELLIGENCE:\n" + "\n\n---\n\n".join(comp_parts),
        })
        print(f"  ✅ Collected {len(comp_parts)} competitor sources")

    # ══════════════════════════════════════════
    # LAYER 7: News & Sentiment
    # ══════════════════════════════════════════
    print("\n📰 [Layer 7] Gathering news & sentiment...")
    news_parts = []

    # NewsAPI
    if newsapi_key:
        try:
            res = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": f'"{name}"',
                    "sortBy": "relevancy",
                    "language": "en",
                    "pageSize": 15,
                    "apiKey": newsapi_key,
                },
                timeout=12,
            ).json()
            if res.get("status") == "ok":
                articles = res.get("articles", [])
                rows = [
                    f"- **{a['title']}** ({a['publishedAt'][:10]}, {a.get('source',{}).get('name','')}): {a.get('description','')}"
                    for a in articles[:12]
                ]
                if rows:
                    news_parts.append("\n".join(rows))
                print(f"  ✅ NewsAPI: {res.get('totalResults', 0)} total articles")
            else:
                print(f"  ❌ NewsAPI error: {res.get('message', 'unknown')}")
        except Exception as e:
            print(f"  ❌ NewsAPI request failed: {e}")

    # Serper news supplement
    if serper_key:
        news_queries = [
            f'"{name}" news announcement 2024 2025',
            f'"{name}" press release update site:prnewswire.com OR site:businesswire.com',
        ]
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(_serper_search, serper_key, q, 6): q
                       for q in news_queries}
            for fut in as_completed(futures):
                r = fut.result()
                if r:
                    news_parts.append(r)

    if news_parts:
        all_valid_data.append({
            "url": "News-Sentiment-Combined",
            "content": "### RECENT NEWS:\n" + "\n\n---\n\n".join(news_parts),
        })
        print(f"  ✅ Collected {len(news_parts)} news sources")

    # ══════════════════════════════════════════
    # LAYER 8: Market Size & TAM Research
    # ══════════════════════════════════════════
    print("\n📈 [Layer 8] Researching market size & TAM...")
    market_parts = []

    # Exa for authoritative research reports
    if exa_key:
        try:
            import exa_py
            exa = exa_py.Exa(api_key=exa_key)
            exa_queries = [
                f"{industry} market size TAM CAGR forecast 2024 2025 2026 billion",
                f"{industry} industry report total addressable market growth drivers",
                f"{name} {industry} competitive market analysis 2024",
            ]
            for eq in exa_queries:
                try:
                    res = exa.search_and_contents(eq, num_results=3,
                                                   text={"max_characters": 800})
                    rows = [f"- **{r.title}** ({r.url}): {r.text}" for r in res.results]
                    if rows:
                        market_parts.append("\n".join(rows))
                    print(f"  ✅ Exa: {eq[:55]}...")
                except Exception as e:
                    print(f"  ❌ Exa query failed: {e}")
        except ImportError:
            print("  ❌ exa_py not installed (pip install exa-py)")
        except Exception as e:
            print(f"  ❌ Exa client init failed: {e}")

    # Serper market data supplement
    if serper_key:
        market_queries = [
            f'{industry} market size billion TAM 2024 2025 Gartner IDC Forrester report',
            f'{industry} market growth CAGR forecast 2025 2030',
            f'{name} {industry} industry trends regulatory environment',
            f'{industry} venture capital investment trends 2024 2025',
        ]
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(_serper_search, serper_key, q, 6): q
                       for q in market_queries}
            for fut in as_completed(futures):
                r = fut.result()
                if r:
                    market_parts.append(r)

    if market_parts:
        all_valid_data.append({
            "url": "Market-Research-TAM",
            "content": "### MARKET RESEARCH:\n" + "\n\n---\n\n".join(market_parts),
        })
        print(f"  ✅ Collected {len(market_parts)} market data sources")

    # ══════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════
    total_chars = sum(len(d["content"]) for d in all_valid_data)
    print(f"\n{'='*60}")
    print(f"[Researcher] Complete — {len(all_valid_data)} sources, ~{total_chars:,} chars")
    for item in all_valid_data:
        print(f"  • {item['url']}: {len(item['content']):,} chars")
    print(f"{'='*60}\n")

    return {"raw_research_data": all_valid_data}
