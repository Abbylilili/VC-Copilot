import os
import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

def extract_structured_json(content: str) -> dict:
    """从 markdown 末尾提取 ```json ``` 块"""
    match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            return {}
    return {}

def analyst_node(state: AgentState):
    name = state.get('name', 'Startup')
    print(f"\n--- [Analyst Agent] Synthesizing Intelligence for: {name} ---")
    
    # 1. Gather all inputs
    research_items = state.get('raw_research_data', [])
    human_notes = state.get('human_notes', "")
    debate_transcript = state.get('debate_transcript', [])
    
    # 2. Categorize Data (Market vs Founders vs Crunchbase vs Competitors)
    market_data = []
    founder_data = []
    crunchbase_data = []
    competitor_data = []
    sources_summary = []
    
    for item in research_items:
        url = item.get('url', 'Unknown')
        content = item.get('content', '')
        sources_summary.append(url)
        
        if "### FOUNDER DNA" in content:
            founder_data.append(f"SOURCE [{url}]:\n{content}")
        elif "### CRUNCHBASE DATA" in content:
            crunchbase_data.append(f"SOURCE [{url}]:\n{content}")
        elif "### COMPETITIVE INTELLIGENCE" in content:
            competitor_data.append(f"SOURCE [{url}]:\n{content}")
        else:
            market_data.append(f"SOURCE [{url}]:\n{content[:2000]}")
    
    web_research_data_str = "\n".join(market_data) if market_data else "No specific market data found."
    founder_data_str = "\n".join(founder_data) if founder_data else "No specific founder/team DNA found."
    cb_data_str = "\n".join(crunchbase_data) if crunchbase_data else "No Crunchbase record found for this entity."
    comp_data_str = "\n".join(competitor_data) if competitor_data else "No explicit competitive intel found."
    
    # 3. Determine if this is an INITIAL report or a REFINED report
    is_refined = len(debate_transcript) > 0 or len(human_notes) > 0
    
    # 4. Format context
    formatted_context = f"### STARTUP: {name} (Location: {state.get('location')})\n"
    
    if human_notes:
        formatted_context += f"\n### CRITICAL EXPERT NOTES (Added by User):\n{human_notes}\n"
    
    if debate_transcript:
        formatted_context += f"\n### INTERNAL COMMITTEE BRAINSTORMING TRANSCRIPT:\n" + "\n".join(debate_transcript) + "\n"
    
    # 5. Dynamic Prompt
    debate_instruction = ""
    if is_refined:
        debate_instruction = """
        ## 7. Synthesis of Expert/Internal Debate
        Summarize the key points of disagreement and the final consensus reached during the internal brainstorming session. 
        How did the new expert notes change our initial hypothesis?
        """
    
    system_prompt = f"""
    You are a Senior Investment Partner at Sequoia Capital / a16z conducting rigorous due diligence.
    Your task: Generate a **Tier-1 Investment Committee Memo** for: **{name}**.

    This memo will determine whether we issue a term sheet. Apply the same ruthless standards used by top VCs:
    - Data-driven decision making (prefer quantitative evidence)
    - Founder obsession (team > idea)
    - Market timing ("Why Now?")
    - Outcome focus (Can this be a $1B+ outcome?)

    ---

    ## DATA SOURCES (Prioritize in this order):
    ### 1️⃣ COMPETITIVE & PEER INTELLIGENCE
    {comp_data_str}

    ### 2️⃣ CRUNCHBASE & FUNDING DATA (Highest Trust)
    {cb_data_str}

    ### 3️⃣ FOUNDER & TEAM DNA (Critical for Early Stage)
    {founder_data_str}

    ### 4️⃣ NEWS, PRODUCT & MARKET INTELLIGENCE
    {web_research_data_str}

    **DATA QUALITY PROTOCOL:**
    - Prefer third-party validation (news articles, Crunchbase) over company claims
    - Cross-reference multiple sources before stating facts
    - Flag conflicting information explicitly
    - If data is missing/unreliable, write: **"⚠️ INSUFFICIENT DATA"**

    ---

    ## INVESTMENT MEMO STRUCTURE (Follow Sequoia/a16z Format):

    # Executive Summary (2-3 sentences)
    Synthesize the entire investment case into a compelling narrative. Answer:
    - What do they do?
    - Why does this matter now?
    - What's our conviction level?

    ---

    ## 1. Company Overview & Core Hypothesis
    **What They Do (1-liner):** [Clear value proposition]

    **The Big Idea:**
    - What fundamental shift are they betting on?
    - Painkiller or vitamin? (Must be painkiller for early-stage)

    **"Why Now?" Timing Analysis:**
    - What recent technological/market shift enables this?
    - Examples: GPU cost decline, regulatory change, consumer behavior shift

    ---

    ## 2. Founder & Team DNA (40% Weight in Decision)
    **CRITICAL: Early-stage investing is founder arbitrage.**

    For EACH founder identified:
    - **Background Pedigree**: Prior companies (highlight unicorns/FAANG), academic credentials (MIT/Stanford?), domain expertise
    - **Execution Signals**: Previous exits, shipped products at scale, technical depth
    - **Unique Insight**: What do they know that others don't? (10+ years in industry?)
    - **Team Completeness**: Technical co-founder present? Sales/GTM strength?

    **Team-Market Fit Rating:** [🟢 STRONG / 🟡 MODERATE / 🔴 WEAK]
    *Justification:* [One sentence explaining the rating]

    **Red Flags Check:**
    - Solo non-technical founder? ⚠️
    - No prior startup experience? ⚠️
    - Team gaps (e.g., no one with enterprise sales background for B2B)? ⚠️

    ---

    ## 3. Market Opportunity & TAM
    **Total Addressable Market (TAM):**
    - Provide specific dollar figures if available (e.g., "$50B by 2027")
    - Cite sources (Gartner, CB Insights, news articles)

    **Market Structure:**
    - Is this a winner-take-all market (network effects) or fragmented?
    - Concentration: Who are the top 3 incumbents?

    **Growth Trajectory:**
    - What's the CAGR (Compound Annual Growth Rate)?
    - Is the market expanding or contracting?

    ---

    ## 4. Traction & Validation (If Available)
    **Funding Metrics:**
    - Total Raised: [Extract from Crunchbase]
    - Last Round: [Seed/Series A/B, date, amount]
    - Notable Investors: [Blue-chip VCs? Angel investors from target industry?]

    **Product/Revenue Signals:**
    - Revenue (ARR/MRR if mentioned): [$XXX]
    - Customer Count: [# of customers, notable logos]
    - Growth Rate: [MoM/YoY if available]

    **Social Proof:**
    - Press coverage (TechCrunch, Bloomberg mentions?)
    - Partnerships or pilot programs
    - Waitlist size or early demand signals

    ---

    ## 5. Competitive Landscape & Differentiation
    **CRITICAL: IDENTIFY DIRECT PEER COMPETITORS.**

    **Direct Competitors:** [List 3-5 specific peer companies or startups]
    
    ⚠️ **STRICT FILTER:** 
    - DO NOT list generic infrastructure providers (e.g., AWS, Azure, Google Cloud, IBM) unless the startup is literally building a cloud infrastructure platform. 
    - Focus on other startups, direct product-level rivals, or specific business units of large firms that compete directly with {name}.

    **Positioning Map**
    *Instructions: You MUST generate a row for EVERY competitor listed above. 
    Row count MUST equal competitor count. Do not truncate. Do not skip any row.*

    | Competitor | Core Strength | Key Weakness | Why {name} Wins / Differentiation |
    |------------|---------------|--------------|-----------------------------------|
    | [Competitor A] | [e.g., Early mover, brand] | [e.g., Legacy tech, high price] | [e.g., 10x faster inference] |
    | [Competitor B] | [e.g., Large distribution] | [e.g., Product complexity] | [e.g., Native workflow integration] |

    *The rows above are EXAMPLES ONLY. Replace with actual competitor data.*

    **Market Whitespace Assessment:**
    - Is this a crowded "Red Ocean" or a genuine "Blue Ocean" innovation?
    - What is the "unfair advantage" that makes this defensible against both incumbents and new entrants?

    ---

    ## 6. Defensibility & Moat Analysis (20% Weight)
    **Moat Type Identified:**
    - [1] **Network Effects** (value increases with users, e.g., marketplace)
    - [2] **Data Moat** (proprietary dataset + ML flywheel)
    - [3] **Switching Costs** (embedded in workflow, painful to replace)
    - [4] **Regulatory/IP Moat** (patents, licenses, compliance barriers)
    - [5] **Brand** (premium positioning, cult following)
    - [6] ⚠️ **No Clear Moat** (commoditized, replicable)

    **Moat Strength:** [🟢 STRONG / 🟡 DEVELOPING / 🔴 WEAK]

    **Technical Feasibility:**
    - Is the core technology proven or speculative?
    - Technical risk level: [🟢 LOW / 🟡 MEDIUM / 🔴 HIGH]

    ---

    ## 7. Key Risks & Mitigations
    Present top 3-5 risks in a table. Be ruthlessly honest.

    | Risk Category | Severity | Description & Impact | Mitigation Strategy (if any) |
    | :--- | :---: | :--- | :--- |
    | Execution Risk | 🔴 HIGH | Example: No enterprise sales experience on team | Hire VP Sales from Salesforce |
    | Market Timing | 🟡 MED | Example: Market may not be ready for 2 years | Pilot programs validate demand |

    **Critical Assumptions to Validate:**
    - [List 2-3 hypotheses that MUST be true for success]

    ---

    ## 8. Investment Recommendation
    **Verdict:** [✅ PROCEED TO TERM SHEET / 🟡 DEEPER DD REQUIRED / ❌ PASS]

    **Investment Thesis (One-Liner):**
    *[e.g., "Exceptional founding team attacking a $10B market with proven GTM playbook from prior exit"]*

    **Expected Outcome:**
    - Base Case: [$XXM valuation in 3-5 years]
    - Bull Case: [$XXB outcome if category creation succeeds]

    **Next Steps:**
    - [1] Reference calls with former colleagues
    - [2] Customer interviews (if applicable)
    - [3] Financial model review
    - [4] Term sheet negotiation

    {debate_instruction}

    ---

    ## WRITING STYLE RULES:
    1. **Be concise but comprehensive** - Every word must add value
    2. **Quantify everything** - Avoid vague adjectives like "large market" (say "$50B TAM")
    3. **Be skeptical** - Point out gaps, conflicts, and red flags explicitly
    4. **Use markdown tables** - Ensure EVERY row has a newline for proper rendering
    5. **Cite sources** - Reference specific URLs when making factual claims
    6. **Avoid jargon** - Write for a non-technical GP if needed, explain acronyms

    ---

    ## STRUCTURED DATA EXPORT (MANDATORY — Append at the end of your response)

    After your full memo text, append a JSON block between ```json and ``` tags.
    This block is used for document rendering. Follow this schema EXACTLY:
    ```json
    {{
      "meta": {{
        "company_name": "{name}",
        "stage": "",
        "raise_amount": "",
        "valuation": "",
        "sector": "",
        "date": "",
        "recommendation": "INVEST|PASS|WATCH",
        "check_size": ""
      }},
      "team": [
        {{"name": "", "role": "", "background": "", "why_they_win": ""}}
      ],
      "metrics": {{
        "arr": "", "arr_growth": "", "nrr": "",
        "gross_margin": "", "customers": "", "avg_acv": ""
      }},
      "competitors": [
        {{"name": "", "core_strength": "", "key_weakness": "", "why_we_win": ""}}
      ],
      "risks": [
        {{"risk": "", "severity": "High|Medium|Low", "probability": "High|Medium|Low", "mitigant": ""}}
      ],
      "financials": [
        {{"year": "", "arr": "", "revenue": "", "gross_margin": "", "ebitda_margin": ""}}
      ],
      "use_of_proceeds": [
        {{"category": "", "amount": "", "pct": "", "rationale": ""}}
      ],
      "returns": [
        {{"scenario": "Bear|Base|Bull", "arr_at_exit": "", "multiple": "", "valuation": "", "moic": ""}}
      ]
    }}
    ```

    **CRITICAL TABLE FORMATTING (MUST FOLLOW EXACTLY):**

    ⚠️ EVERY TABLE ROW MUST BE ON ITS OWN SEPARATE LINE. NO EXCEPTIONS.

    CORRECT EXAMPLE:
    | Competitor | Core Strength | Key Weakness | Why We Win |
    | :--- | :--- | :--- | :--- |
    | Company A | Strong brand | High cost | We are cheaper |
    | Company B | Large network | Slow innovation | We move faster |
    | Company C | Enterprise focus | Poor UX | We have better UX |

    ❌ NEVER concatenate rows like this:
    | Company A | Strong brand | High cost | We are cheaper | | Company B | Large network | Slow innovation | We move faster |

    ✅ RULES:
    1. One row per line, always
    2. Header row on its own line
    3. Separator line (| :--- |) on its own line
    4. Each data row on its own line with a real newline after it
    5. Empty line before and after the entire table

    **CHECKBOX FORMATTING:**
    - Use `- [ ]` for unchecked (note the dash and space)
    - Use `- [x]` for checked
    - Each checkbox item on its own line
    """
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=formatted_context)])

        # Post-process to fix table formatting issues
        content = response.content
        import re

        def fix_markdown_tables(text):
            """
            Fix malformed markdown tables where multiple rows are concatenated on one line.
            Splits lines like: | A | B | | C | D | into separate rows.
            """
            lines = text.split('\n')
            fixed_lines = []

            for line in lines:
                stripped = line.strip()
                # Only process lines that look like table rows
                if stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 4:
                    # Detect concatenated rows: pattern "| ... | | ..." (pipe-space-pipe not in separator)
                    is_separator = re.match(r'^\|[\s|:\-]+\|$', stripped)
                    if not is_separator:
                        # Split on "| |" boundary (end of one row + start of next)
                        parts = re.split(r'\|\s*\n?\s*\|(?!\s*[-:])', stripped)
                        if len(parts) > 1:
                            for part in parts:
                                part = part.strip().strip('|').strip()
                                if part:
                                    fixed_lines.append('| ' + ' | '.join(c.strip() for c in part.split('|')) + ' |')
                            continue
                fixed_lines.append(line)

            result = '\n'.join(fixed_lines)
            # Clean up excessive newlines
            result = re.sub(r'\n{4,}', '\n\n', result)
            return result

        content = fix_markdown_tables(content)

        # Append Citations with better formatting
        citation_footer = "\n\n# 📚 Data Sources & Evidence\n"
        if sources_summary:
            unique_sources = list(set(sources_summary))
            citation_footer += "\n".join([f"{i+1}. [{url}]({url})" for i, url in enumerate(unique_sources)])

        # Format checkboxes properly (ensure they have list marker)
        content = re.sub(r'^(\s*)\[ \]', r'\1- [ ]', content, flags=re.MULTILINE)
        content = re.sub(r'^(\s*)\[x\]', r'\1- [x]', content, flags=re.MULTILINE)
        content = re.sub(r'^(\s*)\[X\]', r'\1- [x]', content, flags=re.MULTILINE)

        # Extract structured data for document generation
        structured_data = extract_structured_json(content)
        
        # Clean up the report content for frontend display (remove the JSON block)
        display_content = re.sub(r'---[\s\S]*?## STRUCTURED DATA EXPORT[\s\S]*?```json[\s\S]*?```', '', content)
        # Fallback if the above complex regex doesn't match perfectly
        display_content = re.sub(r'```json[\s\S]*?```', '', display_content).strip()

        return {
            "report_content": display_content + citation_footer,
            "structured_data": structured_data
        }
    except Exception as e:
        print(f"❌ Analyst Error: {e}")
        return {"report_content": f"Failed to generate report: {e}"}
