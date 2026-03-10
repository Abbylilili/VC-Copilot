"use client"

import React, { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import {
  Users, ShieldAlert, FileText, Send, Globe, MapPin, TrendingUp, AlertTriangle,
  CheckCircle2, Loader2, Briefcase, Sparkles, RefreshCcw, UserCheck
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

// Persona names matching backend PARTNER_PERSONAS
const PERSONA_NAMES: Record<string, string> = {
  A: "Partner A — Growth Investor",
  B: "Partner B — Risk Analyst",
  C: "Partner C — Founder Expert",
  D: "IC Chair — Managing Partner",
}

export default function InvestmentDashboard() {
  const [loading, setLoading] = useState(false)
  const [brainstorming, setBrainstorming] = useState(false)
  const [refining, setRefining] = useState(false)
  const [refineError, setRefineError] = useState<string | null>(null)
  const [reportVersion, setReportVersion] = useState(1)
  const [activeTab, setActiveTab] = useState("notes")

  const [formData, setFormData] = useState({ name: "", location: "", website: "", industry: "" })
  const [humanNotes, setHumanNotes] = useState("")
  const [reportId, setReportId] = useState<string | null>(null)
  const [report, setReport] = useState<any>(null)
  const [debate, setDebate] = useState<{id: string, role: string, content: string}[]>([])

  const debateEndRef = useRef<HTMLDivElement>(null)
  const mainScrollRef = useRef<HTMLDivElement>(null)

  // 极致平滑滚动：监听辩论内容变化
  useEffect(() => {
    if (debateEndRef.current) {
      debateEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [debate])

  const handleAnalyze = async () => {
    if (!formData.name) return
    setLoading(true); setReport(null); setReportId(null); setDebate([])
    setRefineError(null); setReportVersion(1)
    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      })
      const data = await res.json()
      if (data.status === "success") {
        setReport(data.analysis); setReportId(data.report_id)
        mainScrollRef.current?.scrollTo({ top: 0, behavior: "smooth" })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleBrainstorm = async () => {
    if (!reportId || !humanNotes) return
    setBrainstorming(true); setDebate([]); setActiveTab("debate") 

    try {
      const response = await fetch("http://localhost:8000/brainstorm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId, human_notes: humanNotes })
      })

      const reader = response.body?.getReader()
      if (!reader) return
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        let lines = buffer.split("\n")
        buffer = lines.pop() || ""
        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith("data: ")) {
            const dataStr = trimmed.slice(6)
            if (dataStr === "[DONE]") break
            try {
              const data = JSON.parse(dataStr)
              setDebate(prev => {
                const existingIndex = prev.findIndex(m => m.id === data.id)
                if (existingIndex !== -1) {
                  const updated = [...prev]
                  updated[existingIndex] = { ...updated[existingIndex], content: data.content }
                  return updated
                }
                return [...prev, { id: data.id, role: data.role, content: data.content }]
              })
            } catch (e) {}
          }
        }
      }
    } finally {
      setBrainstorming(false)
    }
  }

  const handleFinalRefine = async () => {
    if (!reportId) return
    setRefining(true)
    setRefineError(null)
    try {
      // Build transcript with full persona names so analyst has context
      const transcript = debate.map(d => {
        const name = PERSONA_NAMES[d.role] ?? d.role
        return `[${name}]: ${d.content}`
      })

      const res = await fetch("http://localhost:8000/refine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_id: reportId,
          human_notes: humanNotes,
          debate_transcript: transcript,
        })
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
        throw new Error(err.detail || `Server error ${res.status}`)
      }

      const data = await res.json()
      if (data.status === "success") {
        setReport(data.analysis)
        setReportVersion(v => v + 1)
        // Scroll main report area to top so user sees updated content
        mainScrollRef.current?.scrollTo({ top: 0, behavior: "smooth" })
      } else {
        throw new Error("Backend returned non-success status")
      }
    } catch (err: any) {
      setRefineError(err.message ?? "Unknown error")
    } finally {
      setRefining(false)
    }
  }

  return (
    <div className="flex h-screen w-full bg-slate-50 text-slate-900 overflow-hidden font-sans fixed inset-0">
      {/* 1. Sidebar */}
      <aside className="w-80 border-r bg-white p-6 flex flex-col gap-6 shadow-sm z-10 h-full overflow-y-auto shrink-0">
        <div className="flex items-center gap-3 mb-2 shrink-0">
          <div className="bg-slate-900 w-9 h-9 rounded-xl flex items-center justify-center shadow-lg"><TrendingUp className="text-white w-5 h-5" /></div>
          <h1 className="font-bold text-lg tracking-tight">VC Copilot</h1>
        </div>
        <div className="space-y-4">
          <div className="space-y-1"><label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Startup</label><Input placeholder="Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="h-9 rounded-lg" /></div>
          <div className="space-y-1"><label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Industry</label><Input placeholder="AI / Fintech" value={formData.industry} onChange={e => setFormData({...formData, industry: e.target.value})} className="h-9 rounded-lg" /></div>
          <div className="space-y-1"><label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Location</label><Input placeholder="e.g. USA" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} className="h-9 rounded-lg" /></div>
          <div className="space-y-1"><label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Website</label><Input placeholder="https://..." value={formData.website} onChange={e => setFormData({...formData, website: e.target.value})} className="h-9 rounded-lg" /></div>
          <Button onClick={handleAnalyze} className="w-full mt-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg h-10 shadow-md transition-all active:scale-95" disabled={loading || !formData.name}>
            {loading ? <Loader2 className="animate-spin w-4 h-4" /> : "Run Deep Analysis"}
          </Button>
        </div>
      </aside>

      {/* 2. Main Area (Scrollable) */}
      <main className="flex-1 flex flex-col bg-white min-w-0 h-screen overflow-hidden">
        <header className="h-14 border-b flex items-center px-8 justify-between shrink-0 bg-white/80 backdrop-blur-md z-20">
          <div className="flex items-center gap-3">
            <Badge className="bg-slate-900 text-white text-[9px] font-bold px-2 py-0">INTERNAL ONLY</Badge>
            <h2 className="font-bold text-sm text-slate-700 truncate">{report ? `Technical DD: ${formData.name}` : "Startup Intelligence"}</h2>
            {reportVersion > 1 && (
              <span className="text-[9px] font-black bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full uppercase tracking-widest">
                v{reportVersion} · IC Updated
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {report && <div className="bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full border text-xs font-bold shadow-sm">Fit Score: {(Object.values(report.scores as Record<string, number>).reduce((a,b)=>a+b,0)/4).toFixed(1)}/10</div>}
          </div>
        </header>

        <div ref={mainScrollRef} className="flex-1 overflow-y-auto custom-scrollbar h-full bg-white">
          <div className="max-w-3xl mx-auto p-8 lg:p-16 pb-32">
            {!report && !loading && <div className="h-[60vh] flex flex-col items-center justify-center text-slate-200"><FileText className="w-16 h-16 opacity-50 mb-4" /><p className="text-xs font-bold tracking-widest uppercase">Perform an inquiry to start</p></div>}
            {loading && <div className="space-y-10 animate-pulse pt-4"><div className="h-8 bg-slate-50 rounded w-1/3"></div><div className="h-64 bg-slate-50/50 rounded-2xl border-dashed border-2 flex items-center justify-center"><Loader2 className="w-8 h-8 text-slate-200 animate-spin" /></div></div>}
            {report && (
              <div className="animate-in fade-in duration-700">
                <div className="grid grid-cols-4 gap-4 mb-12 shrink-0">
                  {Object.entries(report.scores).map(([k,v]) => (<div key={k} className="bg-slate-50 p-4 rounded-2xl border flex flex-col items-center shadow-sm"><span className="text-[9px] font-bold text-slate-400 uppercase mb-1">{k}</span><span className="text-2xl font-black">{v as number}</span></div>))}
                </div>
                <article className="prose prose-slate max-w-none prose-p:text-slate-600 prose-p:leading-relaxed prose-headings:font-black prose-headings:tracking-tighter"><ReactMarkdown remarkPlugins={[remarkGfm]}>{report.report_content || report.report}</ReactMarkdown></article>
                {report.risk_flags && <div className="mt-16 bg-rose-50/30 p-8 rounded-3xl border border-rose-100/50 shadow-sm"><h3 className="font-bold text-rose-900 text-xs uppercase tracking-widest mb-6 flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Risk Assessment</h3><ul className="space-y-3">{report.risk_flags.map((f: string, i: number) => <li key={i} className="text-sm text-rose-800/80 font-medium flex gap-3"><span className="text-rose-200 font-black">0{i+1}</span> {f}</li>)}</ul></div>}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* 3. Right Sidebar (Scrollable) */}
      <aside className="w-[450px] border-l bg-slate-50 flex flex-col h-screen overflow-hidden shadow-2xl relative shrink-0">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col h-full overflow-hidden">
          <div className="px-6 py-6 bg-white border-b shrink-0 z-10">
            <h3 className="font-bold text-[10px] text-slate-400 uppercase tracking-widest flex items-center gap-2 mb-4"><Users className="w-3.5 h-3.5" /> Collaboration Loop</h3>
            <TabsList className="grid grid-cols-2 w-full h-10 bg-slate-100 p-1 rounded-xl">
              <TabsTrigger value="notes" className="rounded-lg text-[10px] font-bold uppercase data-[state=active]:bg-white data-[state=active]:shadow-sm">1. Expert Input</TabsTrigger>
              <TabsTrigger value="debate" className="rounded-lg text-[10px] font-bold uppercase data-[state=active]:bg-white data-[state=active]:shadow-sm">2. Live IC Debate</TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-hidden relative">
            <TabsContent value="notes" className="h-full m-0 p-0 flex flex-col bg-white">
              <div className="flex-1 overflow-y-auto p-6 pb-24">
                <div className="bg-blue-50/50 p-4 rounded-2xl border border-blue-100/50 border-dashed mb-4 font-bold text-[10px] text-blue-600 uppercase tracking-widest text-center">Add proprietary info to trigger deliberation.</div>
                <Textarea value={humanNotes} onChange={e => setHumanNotes(e.target.value)} className="min-h-[500px] w-full p-5 text-sm border-slate-100 rounded-2xl bg-white shadow-inner focus-visible:ring-blue-200 leading-relaxed shrink-0" placeholder="e.g. Founder background, secret tech..." />
              </div>
              <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-white via-white to-transparent pt-10 border-t z-20"><Button onClick={handleBrainstorm} disabled={brainstorming || !humanNotes || !reportId} className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg flex gap-2">{brainstorming ? <Loader2 className="animate-spin w-4 h-4" /> : <><Sparkles className="w-4 h-4" /> Start Live Deliberation</>}</Button></div>
            </TabsContent>

            <TabsContent value="debate" className="h-full m-0 p-0 flex flex-col overflow-hidden bg-slate-50/50">
              {/* IC Partner Legend */}
              {debate.length > 0 && (
                <div className="px-4 pt-4 pb-2 flex gap-2 flex-wrap shrink-0 border-b bg-white">
                  {[
                    { role: "A", label: "Growth Investor", sub: "Sequoia style", color: "bg-emerald-500" },
                    { role: "B", label: "Risk Analyst",    sub: "Tiger style",   color: "bg-rose-500"    },
                    { role: "C", label: "Founder Expert",  sub: "a16z style",    color: "bg-amber-500"   },
                    { role: "D", label: "IC Chair",        sub: "Verdict",       color: "bg-blue-600"    },
                  ].map(p => (
                    <div key={p.role} className="flex items-center gap-1.5">
                      <div className={`${p.color} w-2 h-2 rounded-full`} />
                      <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wide">{p.label}</span>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex-1 overflow-y-auto p-6 space-y-6 pb-32">
                {debate.length > 0 ? debate.map((msg) => {
                  type PartnerConfig = { color: string; bg: string; title: string; icon: React.ReactNode }
                  const partners: Record<string, PartnerConfig> = {
                    A: { color: "bg-emerald-500", bg: "border-emerald-100",  title: "Partner A — Growth Investor",  icon: <TrendingUp  className="w-3 h-3 text-white" /> },
                    B: { color: "bg-rose-500",    bg: "border-rose-100",     title: "Partner B — Risk Analyst",     icon: <ShieldAlert className="w-3 h-3 text-white" /> },
                    C: { color: "bg-amber-500",   bg: "border-amber-100",    title: "Partner C — Founder Expert",   icon: <UserCheck   className="w-3 h-3 text-white" /> },
                    D: { color: "bg-blue-600",    bg: "border-blue-100",     title: "⚖️ IC CHAIR — FINAL VERDICT",  icon: <CheckCircle2 className="w-3 h-3 text-white" /> },
                  }
                  const p = partners[msg.role] ?? { color: "bg-slate-400", bg: "border-slate-100", title: msg.role, icon: <Users className="w-3 h-3 text-white" /> }
                  const isChair = msg.role === "D"
                  return (
                    <div key={msg.id} className="flex flex-col gap-2.5 animate-in slide-in-from-right-2 duration-300">
                      <div className="flex items-center gap-2.5 shrink-0">
                        <div className={`${p.color} w-6 h-6 rounded-lg flex items-center justify-center shadow-sm`}>{p.icon}</div>
                        <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">{p.title}</span>
                      </div>
                      <div className={`bg-white border ${p.bg} p-5 rounded-2xl shadow-sm text-xs leading-relaxed text-slate-700 font-medium relative overflow-hidden ${isChair ? "ring-1 ring-blue-200 bg-blue-50/30" : ""}`}>
                        <div className={`absolute left-0 top-0 w-1 h-full ${p.color}`} />
                        <span className={isChair ? "not-italic font-semibold" : "italic"}>
                          {msg.content || <span className="text-slate-300 animate-pulse">Thinking...</span>}
                        </span>
                      </div>
                    </div>
                  )
                }) : (
                  <div className="h-[60vh] flex flex-col items-center justify-center text-slate-300 p-12 text-center">
                    <Users className="w-12 h-12 opacity-10 mb-4" />
                    <p className="text-[10px] uppercase tracking-widest font-bold">Add expert notes and start deliberation</p>
                  </div>
                )}
                <div ref={debateEndRef} />
              </div>

              {/* Show "Update Memo" button only after IC Chair has spoken (6 messages) */}
              {debate.length >= 6 && (
                <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-slate-50 via-slate-50/95 to-transparent pt-12 border-t border-slate-100 z-20">
                  {refineError && (
                    <div className="mb-3 text-[10px] text-rose-600 bg-rose-50 border border-rose-200 rounded-xl px-4 py-2 font-medium">
                      ❌ Error: {refineError}
                    </div>
                  )}
                  {reportVersion > 1 && !refining && !refineError && (
                    <div className="mb-3 text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2 font-medium text-center">
                      ✅ Memo v{reportVersion} generated — scroll left to read updated report
                    </div>
                  )}
                  <Button
                    onClick={handleFinalRefine}
                    disabled={refining}
                    className="w-full h-12 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-bold flex gap-3 shadow-xl transition-all active:scale-95"
                  >
                    {refining
                      ? <><Loader2 className="animate-spin w-4 h-4" /> Generating v{reportVersion + 1}...</>
                      : <><RefreshCcw className="w-4 h-4" /> {reportVersion > 1 ? `Regenerate Memo (v${reportVersion + 1})` : "Generate Updated Memo (v2)"}</>
                    }
                  </Button>
                  <p className="text-center text-[9px] text-slate-400 mt-2 uppercase tracking-widest">
                    Incorporates IC debate + expert notes → updates left panel
                  </p>
                </div>
              )}
            </TabsContent>
          </div>
        </Tabs>
      </aside>
    </div>
  )
}
