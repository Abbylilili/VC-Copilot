import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

def analyst_node(state: AgentState):
    name = state.get('name', 'Startup')
    print(f"\n--- [Analyst Agent] Synthesizing Intelligence for: {name} ---")
    
    # 1. Gather all inputs
    research_items = state.get('raw_research_data', [])
    human_notes = state.get('human_notes', "")
    debate_transcript = state.get('debate_transcript', [])
    
    # 2. Categorize Data (Market vs Founders vs Crunchbase)
    market_data = []
    founder_data = []
    crunchbase_data = []
    sources_summary = []
    
    for item in research_items:
        url = item.get('url', 'Unknown')
        content = item.get('content', '')
        sources_summary.append(url)
        
        if "### FOUNDER DNA" in content:
            founder_data.append(f"SOURCE [{url}]:\n{content}")
        elif "### CRUNCHBASE DATA" in content:
            crunchbase_data.append(f"SOURCE [{url}]:\n{content}")
        else:
            market_data.append(f"SOURCE [{url}]:\n{content[:2000]}")
    
    web_research_data_str = "\n".join(market_data) if market_data else "No specific market data found."
    founder_data_str = "\n".join(founder_data) if founder_data else "No specific founder/team DNA found."
    cb_data_str = "\n".join(crunchbase_data) if crunchbase_data else "No Crunchbase record found for this entity."
    
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
    ### 1️⃣ CRUNCHBASE & FUNDING DATA (Highest Trust)
    {cb_data_str}

    ### 2️⃣ FOUNDER & TEAM DNA (Critical for Early Stage)
    {founder_data_str}

    ### 3️⃣ NEWS, PRODUCT & MARKET INTELLIGENCE
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
    **Direct Competitors:** [Name 3-5 specific companies, not generic categories]

    **Positioning Map:**
    | Competitor | Strength | Weakness | How {name} Differs |
    | :--- | :--- | :--- | :--- |
    | Example Co | Feature X | Slow GTM | {name}'s approach |

    **Market Whitespace Assessment:**
    - Crowded space or genuine innovation?
    - What makes this defensible against incumbents?

    ---

    ## 6. Defensibility & Moat Analysis (20% Weight)
    **Moat Type Identified:**
    - [ ] **Network Effects** (value increases with users, e.g., marketplace)
    - [ ] **Data Moat** (proprietary dataset + ML flywheel)
    - [ ] **Switching Costs** (embedded in workflow, painful to replace)
    - [ ] **Regulatory/IP Moat** (patents, licenses, compliance barriers)
    - [ ] **Brand** (premium positioning, cult following)
    - [ ] ⚠️ **No Clear Moat** (commoditized, replicable)

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
    - [ ] Reference calls with former colleagues
    - [ ] Customer interviews (if applicable)
    - [ ] Financial model review
    - [ ] Term sheet negotiation

    {debate_instruction}

    ---

    ## WRITING STYLE RULES:
    1. **Be concise but comprehensive** - Every word must add value
    2. **Quantify everything** - Avoid vague adjectives like "large market" (say "$50B TAM")
    3. **Be skeptical** - Point out gaps, conflicts, and red flags explicitly
    4. **Use markdown tables** - Ensure EVERY row has a newline for proper rendering
    5. **Cite sources** - Reference specific URLs when making factual claims
    6. **Avoid jargon** - Write for a non-technical GP if needed, explain acronyms

    **CRITICAL TABLE FORMATTING (MUST FOLLOW EXACTLY):**

    ⚠️ TABLES MUST BE FORMATTED LIKE THIS EXAMPLE (EACH ROW ON A NEW LINE):

    | Column 1 | Column 2 | Column 3 |
    | :--- | :---: | :--- |
    | Row 1 Data | Value A | Description here |
    | Row 2 Data | Value B | Description here |
    | Row 3 Data | Value C | Description here |

    ❌ NEVER DO THIS (rows on same line):
    | Column 1 | Column 2 | | Row 1 | Value | | Row 2 | Value |

    ✅ CORRECT FORMAT RULES:
    1. Header row on its own line
    2. Separator row (| :--- |) on its own line
    3. EACH data row on its own separate line
    4. Empty line before and after the entire table
    5. Use literal newline character (\n) between rows

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
            Fix malformed markdown tables where rows might be on the same line.
            Strategy: Find table blocks and ensure each row is on its own line.
            """
            lines = text.split('\n')
            fixed_lines = []
            in_table = False

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Detect table start (line with multiple pipes)
                if stripped.count('|') >= 2:
                    in_table = True

                    # Check if multiple rows are concatenated (heuristic: too many pipes)
                    # A normal table row has N pipes for N-1 columns
                    # If we see pattern like "| A | B | | C | D |", that's 2 rows concatenated

                    # Simple fix: If line has "| |" pattern repeated suspiciously, try to split
                    # Pattern: | content | | content | (double pipe suggests row boundary)
                    if '| |' in line:
                        # Split by double-pipe-space pattern
                        segments = re.split(r'\|\s+\|(?=\s*[^:\s-])', line)
                        for seg in segments:
                            if seg.strip():
                                # Ensure it starts and ends with |
                                if not seg.strip().startswith('|'):
                                    seg = '| ' + seg.strip()
                                if not seg.strip().endswith('|'):
                                    seg = seg.strip() + ' |'
                                fixed_lines.append(seg)
                    else:
                        fixed_lines.append(line)

                    # Check if next line is not a table row (table ended)
                    if i + 1 < len(lines) and lines[i + 1].strip().count('|') < 2:
                        in_table = False
                else:
                    in_table = False
                    fixed_lines.append(line)

            result = '\n'.join(fixed_lines)

            # Ensure separator rows have proper spacing
            result = re.sub(r'(\|[\s:]+\-+[\s:]+\|.*)', r'\n\1\n', result)

            # Clean up excessive newlines
            result = re.sub(r'\n{4,}', '\n\n', result)

            return result

        content = fix_markdown_tables(content)

        # Append Citations with better formatting
        citation_footer = "\n\n---\n\n## 📚 Data Sources & Evidence\n\n"
        if sources_summary:
            unique_sources = list(set(sources_summary))
            citation_footer += "\n".join([f"{i+1}. [{url}]({url})" for i, url in enumerate(unique_sources)])

        # Format checkboxes properly (ensure they have list marker)
        content = re.sub(r'^(\s*)\[ \]', r'\1- [ ]', content, flags=re.MULTILINE)
        content = re.sub(r'^(\s*)\[x\]', r'\1- [x]', content, flags=re.MULTILINE)
        content = re.sub(r'^(\s*)\[X\]', r'\1- [x]', content, flags=re.MULTILINE)

        return {"report_content": content + citation_footer}
    except Exception as e:
        print(f"❌ Analyst Error: {e}")
        return {"report_content": f"Failed to generate report: {e}"}
