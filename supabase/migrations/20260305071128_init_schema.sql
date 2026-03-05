CREATE TABLE IF NOT EXISTS companies(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    website TEXT,
    industry TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analysis_reports(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    research_context TEXT,      -- researcher agent: serper get url + firecrawl get content
    report_content TEXT,        -- analysis agent: gpt-4o-mini output
    scores JSONB,               -- scoring agent: report_content as input, output like {"innovation": 8, "market_potential": 7, ...}
    risk_flags TEXT[],          -- risk flags
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);