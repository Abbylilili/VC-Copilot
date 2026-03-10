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
  CheckCircle2, Loader2, Briefcase, Sparkles, RefreshCcw 
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

export default function InvestmentDashboard() {
  const [loading, setLoading] = useState(false)
  const [brainstorming, setBrainstorming] = useState(false)
  const [refining, setRefining] = useState(false)
  const [activeTab, setActiveTab] = useState("notes")
  
  const [formData, setFormData] = useState({ name: "", location: "", website: "", industry: "" })
  const [humanNotes, setHumanNotes] = useState("")
  const [reportId, setReportId] = useState<string | null>(null)
  const [report, setReport] = useState<any>(null)
  const [debate, setDebate] = useState<{id: string, role: string, content: string}[]>([])

  const debateEndRef = useRef<HTMLDivElement>(null)

  // 极致平滑滚动：监听辩论内容变化
  useEffect(() => {
    if (debateEndRef.current) {
      debateEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [debate])

  const handleAnalyze = async () => {
    if (!formData.name) return
    setLoading(true); setReport(null); setReportId(null); setDebate([])
    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      })
      const data = await res.json()
      if (data.status === "success") {
        setReport(data.analysis); setReportId(data.report_id)
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
    try {
      const transcript = debate.map(d => `${d.role}: ${d.content}`)
      const res = await fetch("http://localhost:8000/refine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId, human_notes: humanNotes, debate_transcript: transcript })
      })
      const data = await res.json()
      if (data.status === "success") {
        setReport(data.analysis)
        setActiveTab("notes") // 回到笔记，或者留在辩论
      }
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
          <div className="flex items-center gap-4">
            <Badge className="bg-slate-900 text-white text-[9px] font-bold px-2 py-0">INTERNAL ONLY</Badge>
            <h2 className="font-bold text-sm text-slate-700 truncate">{report ? `Technical DD: ${formData.name}` : "Startup Intelligence"}</h2>
          </div>
          {report && <div className="bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full border text-xs font-bold shadow-sm shrink-0">Fit Score: {(Object.values(report.scores as Record<string, number>).reduce((a,b)=>a+b,0)/4).toFixed(1)}/10</div>}
        </header>
        
        <div className="flex-1 overflow-y-auto custom-scrollbar h-full bg-white">
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
              <div className="flex-1 overflow-y-auto p-6 space-y-8 pb-32">
                {debate.length > 0 ? debate.map((msg) => {
                  let color = "bg-slate-200"; let title = "Partner"; let icon = <Users className="w-3 h-3 text-white" />
                  if (msg.role === 'A') { color = "bg-emerald-500"; title = "Partner A (Visionary)"; icon = <TrendingUp className="w-3 h-3 text-white" /> }
                  if (msg.role === 'B') { color = "bg-rose-500"; title = "Partner B (Skeptic)"; icon = <ShieldAlert className="w-3 h-3 text-white" /> }
                  if (msg.role === 'C') { color = "bg-blue-500"; title = "IC CHAIR (CONSENSUS)"; icon = <CheckCircle2 className="w-3 h-3 text-white" /> }
                  return (
                    <div key={msg.id} className="flex flex-col gap-3 animate-in slide-in-from-right-2 duration-300">
                      <div className="flex items-center gap-2.5 shrink-0"><div className={`${color} w-6 h-6 rounded-lg flex items-center justify-center shadow-sm`}>{icon}</div><span className="text-[10px] font-black uppercase tracking-wider text-slate-400">{title}</span></div>
                      <div className="bg-white border border-slate-100 p-5 rounded-2xl shadow-sm text-xs leading-relaxed text-slate-600 font-medium italic relative overflow-hidden group">
                        <div className="absolute left-0 top-0 w-1 h-full opacity-30" style={{backgroundColor: color.includes('bg-') ? color.replace('bg-', '') : '#94a3b8'}}></div>
                        "{msg.content || "Thinking..."}"
                      </div>
                    </div>
                  )
                }) : <div className="h-[60vh] flex flex-col items-center justify-center text-slate-300 p-12 text-center uppercase text-[10px] tracking-widest font-bold"><Users className="w-12 h-12 opacity-10 mb-4" />Waiting for deliberation...</div>}
                <div ref={debateEndRef} />
              </div>
              {debate.length >= 5 && (
                <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent pt-12 border-t border-slate-100 bg-white z-20">
                  <Button onClick={handleFinalRefine} disabled={refining} className="w-full h-12 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-bold flex gap-3 shadow-xl transition-all active:scale-95">{refining ? <Loader2 className="animate-spin w-4 h-4" /> : <><RefreshCcw className="w-4 h-4" /> UPDATE MEMO BASED ON CONSENSUS</>}</Button>
                </div>
              )}
            </TabsContent>
          </div>
        </Tabs>
      </aside>
    </div>
  )
}
