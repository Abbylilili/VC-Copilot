const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, BorderStyle, WidthType, ShadingType, LevelFormat,
        HeadingLevel, Header, Footer, PageNumber } = require('docx');
const fs = require('fs');

const data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const outputPath = process.argv[3];

// ── 颜色常量 ──────────────────────────────────────────────
const BLUE = "1B3A6B", MID_BLUE = "2E5FA3", LIGHT_BLUE = "D6E4F7";
const GRAY = "6B7280", GREEN = "16A34A", ACCENT = "E8F0FB";
const BORDER = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

// ── Helper Functions ──────────────────────────────────────
const h1 = (text) => new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE, space: 4 } },
    children: [new TextRun({ text, bold: true, size: 28, color: BLUE, font: "Arial" })]
});

const h2 = (text) => new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: MID_BLUE, font: "Arial" })]
});

const p = (text, opts = {}) => new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text: text || "", size: 22, font: "Arial", ...opts })]
});

const spacer = () => new Paragraph({ children: [new TextRun("")] });

const kv = (key, value) => new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [
        new TextRun({ text: `${key}: `, bold: true, size: 22, font: "Arial", color: BLUE }),
        new TextRun({ text: value || "N/A", size: 22, font: "Arial" })
    ]
});

const makeTable = (headers, rows, colWidths) => {
    const totalWidth = colWidths.reduce((a, b) => a + b, 0);
    return new Table({
        width: { size: totalWidth, type: WidthType.DXA },
        columnWidths: colWidths,
        rows: [
            new TableRow({
                tableHeader: true,
                children: headers.map((h, i) => new TableCell({
                    borders: BORDERS,
                    width: { size: colWidths[i], type: WidthType.DXA },
                    shading: { fill: BLUE, type: ShadingType.CLEAR },
                    margins: { top: 80, bottom: 80, left: 120, right: 120 },
                    children: [new Paragraph({
                        children: [new TextRun({ text: h, bold: true, size: 20, color: "FFFFFF", font: "Arial" })]
                    })]
                }))
            }),
            ...rows.map((row, ri) => new TableRow({
                children: row.map((cell, ci) => new TableCell({
                    borders: BORDERS,
                    width: { size: colWidths[ci], type: WidthType.DXA },
                    shading: { fill: ri % 2 === 0 ? "FFFFFF" : ACCENT, type: ShadingType.CLEAR },
                    margins: { top: 80, bottom: 80, left: 120, right: 120 },
                    children: [new Paragraph({
                        children: [new TextRun({ text: String(cell || ""), size: 20, font: "Arial" })]
                    })]
                }))
            }))
        ]
    });
};

const scoreRow = (label, score) => {
    const s = Math.min(10, Math.max(0, parseInt(score) || 0));
    const color = s >= 8 ? "16A34A" : s >= 6 ? "2563EB" : "DC2626";
    return new TableRow({
        children: [
            new TableCell({ borders: BORDERS, width: { size: 4680, type: WidthType.DXA },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ children: [new TextRun({ text: label, size: 22, font: "Arial" })] })] }),
            new TableCell({ borders: BORDERS, width: { size: 2340, type: WidthType.DXA },
                shading: { fill: color, type: ShadingType.CLEAR },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `${s}/10`, bold: true, size: 22, color: "FFFFFF", font: "Arial" })] })] }),
            new TableCell({ borders: BORDERS, width: { size: 2340, type: WidthType.DXA },
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({ children: [new TextRun({ text: "█".repeat(s) + "░".repeat(10 - s), size: 18, color, font: "Arial" })] })] }),
        ]
    });
};

// ── Document Assembly ─────────────────────────────────────
const meta = data.meta || {};
const team = data.team || [];
const metrics = data.metrics || {};
const competitors = data.competitors || [];
const risks = data.risks || [];
const financials = data.financials || [];
const scorecard = data.scorecard || [];
const returns = data.returns || [];
const proceeds = data.use_of_proceeds || [];

const verdictColor = meta.recommendation === "INVEST" ? GREEN
    : meta.recommendation === "PASS" ? "DC2626" : "D97706";

const children = [
    // Cover
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 480, after: 120 },
        children: [new TextRun({ text: "INVESTMENT MEMORANDUM", bold: true, size: 48, color: BLUE, font: "Arial" })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 80 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: MID_BLUE, space: 6 } },
        children: [new TextRun({ text: meta.company_name || "Company", bold: true, size: 52, color: MID_BLUE, font: "Arial" })] }),
    spacer(),

    // Deal Snapshot
    makeTable(
        ["Round", "Raise", "Valuation", "Sector"],
        [[meta.stage || "—", meta.raise_amount || "—", meta.valuation || "—", meta.sector || "—"]],
        [2340, 2340, 2340, 2340]
    ),
    spacer(),

    // Recommendation Banner
    new Table({
        width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360],
        rows: [new TableRow({ children: [new TableCell({
            borders: { top: { style: BorderStyle.SINGLE, size: 12, color: verdictColor },
                       bottom: { style: BorderStyle.SINGLE, size: 12, color: verdictColor },
                       left: { style: BorderStyle.SINGLE, size: 12, color: verdictColor },
                       right: { style: BorderStyle.SINGLE, size: 12, color: verdictColor } },
            shading: { fill: "F9FAFB", type: ShadingType.CLEAR },
            margins: { top: 160, bottom: 160, left: 240, right: 240 },
            children: [
                new Paragraph({ alignment: AlignmentType.CENTER,
                    children: [new TextRun({ text: `${meta.recommendation || "PENDING"} — ${data.vote_summary || ""}`, bold: true, size: 32, color: verdictColor, font: "Arial" })] }),
                new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80 },
                    children: [new TextRun({ text: `Recommended Check Size: ${meta.check_size || "TBD"}`, size: 22, color: GRAY, font: "Arial" })] }),
            ]
        })]})]
    }),
    spacer(), spacer(),

    // 1. Company Overview
    h1("1.  Company Overview"),
    ...[
        ["Company", meta.company_name],
        ["Stage", meta.stage],
        ["Raise", meta.raise_amount],
        ["Valuation", meta.valuation],
        ["Sector", meta.sector],
        ["Date", meta.date],
    ].map(([k, v]) => kv(k, v)),
    spacer(),

    // 2. Team
    h1("2.  Founding Team"),
    makeTable(
        ["Name", "Role", "Background", "Why They Win"],
        team.map(t => [t.name, t.role, t.background, t.why_they_win]),
        [1800, 1400, 3160, 3000]
    ),
    spacer(),

    // 3. Key Metrics
    h1("3.  Traction & Metrics"),
    makeTable(
        ["Metric", "Value"],
        Object.entries(metrics).map(([k, v]) => [k.replace(/_/g, ' ').toUpperCase(), v]),
        [4680, 4680]
    ),
    spacer(),

    // 4. Competitive Landscape
    h1("4.  Competitive Landscape"),
    makeTable(
        ["Competitor", "Core Strength", "Key Weakness", `Why ${meta.company_name} Wins`],
        competitors.map(c => [c.name, c.core_strength, c.key_weakness, c.why_we_win]),
        [2000, 2000, 2360, 3000]
    ),
    spacer(),

    // 5. Risks
    h1("5.  Risk Matrix"),
    makeTable(
        ["Risk", "Severity", "Probability", "Mitigant"],
        risks.map(r => [r.risk, r.severity, r.probability, r.mitigant]),
        [2200, 1000, 1000, 5160]
    ),
    spacer(),

    // 6. Financials
    ...(financials.length > 0 ? [
        h1("6.  Financial Projections"),
        makeTable(
            ["Year", "ARR", "Revenue", "Gross Margin", "EBITDA Margin"],
            financials.map(f => [f.year, f.arr, f.revenue, f.gross_margin, f.ebitda_margin]),
            [1872, 1872, 1872, 1872, 1872]
        ),
        spacer()
    ] : []),

    // 7. Use of Proceeds
    ...(proceeds.length > 0 ? [
        h1("7.  Use of Proceeds"),
        makeTable(
            ["Category", "Amount", "%", "Rationale"],
            proceeds.map(p => [p.category, p.amount, p.pct, p.rationale]),
            [2200, 1200, 800, 5160]
        ),
        spacer()
    ] : []),

    // 8. Return Analysis
    ...(returns.length > 0 ? [
        h1("8.  Return Analysis"),
        makeTable(
            ["Scenario", "ARR at Exit", "Multiple", "Valuation", "MOIC"],
            returns.map(r => [r.scenario, r.arr_at_exit, r.multiple, r.valuation, r.moic]),
            [1500, 1800, 1560, 2300, 2200]
        ),
        spacer()
    ] : []),

    // 9. Investment Scorecard
    h1("9.  Investment Scorecard"),
    new Table({
        width: { size: 9360, type: WidthType.DXA }, columnWidths: [4680, 2340, 2340],
        rows: [
            new TableRow({ children: [
                new TableCell({ borders: BORDERS, width: { size: 4680, type: WidthType.DXA }, shading: { fill: BLUE, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Dimension", bold: true, size: 22, color: "FFFFFF", font: "Arial" })] })] }),
                new TableCell({ borders: BORDERS, width: { size: 2340, type: WidthType.DXA }, shading: { fill: BLUE, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 120, right: 120 }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Score", bold: true, size: 22, color: "FFFFFF", font: "Arial" })] })] }),
                new TableCell({ borders: BORDERS, width: { size: 2340, type: WidthType.DXA }, shading: { fill: BLUE, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 120, right: 120 }, children: [new Paragraph({ children: [new TextRun({ text: "Visual", bold: true, size: 22, color: "FFFFFF", font: "Arial" })] })] }),
            ]}),
            ...scorecard.map(s => scoreRow(s.dimension, s.score))
        ]
    }),
];

const doc = new Document({
    numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
    styles: {
        default: { document: { run: { font: "Arial", size: 22 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, font: "Arial", color: BLUE }, paragraph: { spacing: { before: 320, after: 120 }, outlineLevel: 0 } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: "Arial", color: MID_BLUE }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 1 } },
        ]
    },
    sections: [{
        properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
        headers: { default: new Header({ children: [new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE, space: 4 } }, children: [new TextRun({ text: `CONFIDENTIAL — ${(meta.company_name || '').toUpperCase()} INVESTMENT MEMO  |  ${meta.date || ''}`, size: 18, color: GRAY, font: "Arial" })] })] }) },
        footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, border: { top: { style: BorderStyle.SINGLE, size: 2, color: BLUE, space: 4 } }, children: [new TextRun({ text: "Page ", size: 18, color: GRAY, font: "Arial" }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: GRAY, font: "Arial" }), new TextRun({ text: "  |  For Internal Use Only", size: 18, color: GRAY, font: "Arial" })] })] }) },
        children
    }]
});

Packer.toBuffer(doc).then(buf => {
    fs.writeFileSync(outputPath, buf);
    console.log(`✅ Done: ${outputPath}`);
}).catch(err => {
    console.error(`❌ Error: ${err}`);
    process.exit(1);
});
