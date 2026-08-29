"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Brain, ShieldAlert, FileWarning, Search, Activity, Handshake, Shield, UploadCloud } from "lucide-react";
import { supabase } from "@/lib/supabaseClient";
import { useTheme } from "@/components/ThemeProvider";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001";

export default function IntelligencePage() {
  const router = useRouter();
  
  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const { darkMode } = useTheme();

  const handleFileUpload = (e) => {
    const selectedFile = e.target && e.target.files ? e.target.files[0] : e;
    if (!selectedFile) return;
    setFile(selectedFile);
    setFileUrl(URL.createObjectURL(selectedFile));
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragover") setIsDragging(true);
    else if (e.type === "dragleave") setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    try {
      setIsAnalyzing(true);
      setError(null);

      const formData = new FormData();
      formData.append("file", file);

      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token || "";

      const res = await fetch(`${API_BASE_URL}/analyze-ephemeral`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });

      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.error || d.details || "Analysis failed");
      }

      const data = await res.json();
      if (!data.success) {
        throw new Error(data.errorMessage || "Model analysis failed");
      }
      setAnalysis(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const renderSeverityBadge = (sev) => {
    const s = (sev || "").toUpperCase();
    if (s === "CRITICAL") return <span className="px-2 py-0.5 rounded text-[10px] bg-red-900/40 text-red-400 border border-red-500/30">CRITICAL</span>;
    if (s === "HIGH") return <span className="px-2 py-0.5 rounded text-[10px] bg-orange-900/40 text-orange-400 border border-orange-500/30">HIGH</span>;
    if (s === "MEDIUM") return <span className="px-2 py-0.5 rounded text-[10px] bg-amber-900/40 text-amber-400 border border-amber-500/30">MEDIUM</span>;
    return <span className="px-2 py-0.5 rounded text-[10px] bg-green-900/40 text-green-400 border border-green-500/30">LOW</span>;
  };

  // ─── INITIAL UPLOAD STATE ─────────────────────────────────────────────────────────────
  if (!fileUrl) {
    return (
      <div className={`min-h-screen flex flex-col items-center justify-center p-6 ${
        darkMode ? "bg-[#0D0D0D] text-[#F5E6D8]" : "bg-[#FDFCF9] text-[#2C1810]"
      }`}>
        <button 
          onClick={() => router.push('/dashboard')}
          className={`absolute top-8 left-8 flex items-center gap-2 transition-colors ${
            darkMode ? "text-stone-400 hover:text-[#D4AF37]" : "text-stone-500 hover:text-[#D4AF37]"
          }`}
        >
          <ArrowLeft size={16} /> <span className="text-sm font-semibold tracking-widest uppercase">Dashboard</span>
        </button>

        <div className={`w-24 h-24 mb-6 rounded-3xl flex items-center justify-center shadow-[0_0_40px_rgba(212,175,55,0.2)] ${
          darkMode ? "bg-gradient-to-br from-[#D4AF37] to-[#8B6E1F]" : "bg-gradient-to-br from-[#F5F5DC]/40 to-white border border-[#2C1810]/10"
        }`}>
          <Brain size={48} className={darkMode ? "text-[#1A110D]" : "text-[#D4AF37]"} />
        </div>
        <h1 className="text-4xl font-serif mb-4 flex items-center gap-3">
          LegalT Intelligence
        </h1>
        <p className={`max-w-xl text-center mb-12 ${darkMode ? "text-[#A39284]" : "text-[#6B5A4E]"}`}>
          Secure, ephemeral document analysis. Upload a drafted agreement to audit against multi-jurisdictional precedents. 
          <span className="block mt-2 font-bold text-[#D4AF37]">Documents processed here are NEVER saved to the registry.</span>
        </p>

        <label 
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          className={`cursor-pointer group flex flex-col items-center justify-center w-full max-w-2xl h-64 border-2 border-dashed transition-all rounded-3xl ${
            isDragging 
              ? "border-[#D4AF37] bg-[#D4AF37]/10 shadow-[0_0_30px_rgba(212,175,55,0.1)] scale-[1.02]" 
              : darkMode
                ? "border-[#2B1D16] hover:border-[#D4AF37]/50 bg-[#1A110D] hover:bg-[#2C1810]/30"
                : "border-[#2C1810]/10 hover:border-[#D4AF37]/50 bg-[#F5F5DC]/40 hover:bg-[#F5F5DC]/80"
          }`}
        >
          <UploadCloud size={48} className={`transition-colors ${isDragging ? "text-[#D4AF37] scale-110" : ((darkMode ? "text-[#A39284]" : "text-[#6B5A4E]") + " group-hover:text-[#D4AF37]")} mb-4`} />
          <span className={`text-lg font-serif transition-colors ${isDragging ? "text-[#D4AF37]" : (darkMode ? "text-[#F5E6D8]" : "text-[#2C1810]")}`}>
            {isDragging ? "Drop document to initialize" : "Click to upload or drag and drop"}
          </span>
          <span className={`text-xs mt-2 font-mono uppercase tracking-widest ${darkMode ? "text-[#A39284]" : "text-[#6B5A4E]"}`}>Supports PDF, DOCX, TXT</span>
          <input 
            type="file" 
            className="hidden" 
            accept=".pdf,.docx,.txt"
            onChange={handleFileUpload} 
          />
        </label>
      </div>
    );
  }

  // ─── SPLIT SCREEN ANALYSIS STATE ──────────────────────────────────────────────────────
  return (
    <div className={`flex flex-col h-screen overflow-hidden ${
      darkMode ? "bg-[#0D0D0D] text-[#F5E6D8]" : "bg-[#FDFCF9] text-[#2C1810]"
    }`}>
      {/* Navbar */}
      <header className={`flex items-center justify-between px-6 py-4 border-b ${
        darkMode ? "border-[#2B1D16] bg-[#1A110D]" : "border-[#2C1810]/10 bg-white"
      }`}>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/dashboard')}
            className={`flex items-center gap-2 transition-colors ${
              darkMode ? "text-stone-400 hover:text-[#D4AF37]" : "text-stone-500 hover:text-[#D4AF37]"
            }`}
          >
            <ArrowLeft size={16} /> <span className="text-sm font-semibold tracking-widest uppercase">Dashboard</span>
          </button>
          <div className={`h-6 w-px ${darkMode ? "bg-[#2B1D16]" : "bg-[#2C1810]/10"}`}></div>
          <h1 className="font-serif text-xl tracking-wide flex items-center gap-2">
            <Brain size={20} className="text-[#D4AF37]" /> Ephemeral Intelligence
          </h1>
        </div>
        <div>
          <button 
            onClick={() => { setFile(null); setFileUrl(null); setAnalysis(null); }}
            className={`px-4 py-1.5 rounded border transition-colors text-xs font-bold tracking-widest uppercase ${
              darkMode 
                ? "border-[#2B1D16] text-[#A39284] hover:text-[#F5E6D8] hover:bg-[#2B1D16]" 
                : "border-[#2C1810]/10 text-stone-500 hover:text-[#2C1810] hover:bg-[#2C1810]/5"
            }`}
          >
            Clear Session
          </button>
        </div>
      </header>

      {/* Main Split View */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* Left Side: Document Viewer */}
        <section className={`w-1/2 h-full border-r bg-white ${darkMode ? "border-[#2B1D16]" : "border-[#2C1810]/10"}`}>
          <iframe 
            src={`${fileUrl}#toolbar=0`} 
            className="w-full h-full"
            title="Document Viewer"
          />
        </section>

        {/* Right Side: AI Dashboard */}
        <section className={`w-1/2 h-full overflow-y-auto ${
          darkMode 
            ? "bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[#2C1810]/50 via-[#150D0A] to-[#0D0D0D]"
            : "bg-[#FDFCF9]"
        }`}>
          <div className="p-8">
            
            {/* INITIAL STATE */}
            {!analysis && !isAnalyzing && (
              <div className="h-full flex flex-col items-center justify-center text-center mt-32">
                <div className="w-24 h-24 mb-6 rounded-3xl bg-gradient-to-br from-[#D4AF37] to-[#8B6E1F] flex items-center justify-center shadow-[0_0_40px_rgba(212,175,55,0.2)]">
                  <Brain size={48} className="text-[#1A110D]" />
                </div>
                <h2 className="text-3xl font-serif mb-4">LegalT Intelligence</h2>
                <p className="max-w-md text-[#A39284] mb-12">
                  Execute a deep semantic analysis of the temporary document on the left. Identifies critical risks, missing clauses, and negotiation leverage points instantly.
                </p>
                <div className="space-y-4">
                  <button 
                    onClick={handleAnalyze}
                    className="w-full px-8 py-4 bg-[#D4AF37] hover:bg-[#B8962E] text-[#1A110D] font-bold tracking-widest uppercase text-sm rounded-xl shadow-[0_0_20px_rgba(212,175,55,0.3)] transition-all transform hover:scale-105 flex items-center justify-center gap-2"
                  >
                    <Activity size={18} /> INITIALIZE ANALYSIS PROTOCOL
                  </button>
                  {error && (
                    <div className="p-4 bg-red-900/20 border border-red-900/50 rounded-xl text-red-400 text-sm">
                      {error}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* LOADING STATE */}
            {isAnalyzing && (
              <div className="h-full flex flex-col items-center justify-center text-center mt-40">
                <div className="w-20 h-20 mb-8 rounded-full border-4 border-[#D4AF37]/20 border-t-[#D4AF37] animate-spin"></div>
                <h3 className="text-xl font-serif text-[#D4AF37] animate-pulse">Running Neural Pipeline</h3>
                <div className={`mt-8 text-sm font-mono space-y-2 flex flex-col items-center opacity-80 ${darkMode ? "text-[#A39284]" : "text-[#6B5A4E]"}`}>
                  <p>1 / 5: Vectorizing text nodes...</p>
                  <p>2 / 5: Querying legal knowledge base...</p>
                  <p>3 / 5: Extracting obligations & liabilities...</p>
                  <p className={darkMode ? "text-white" : "text-[#2C1810]"}>4 / 5: Generating negotiation strategy...</p>
                </div>
              </div>
            )}

            {/* ANALYZED STATE */}
            {analysis && (
              <div className="max-w-3xl mx-auto space-y-8 pb-12">
                
                {/* Header Widget */}
                <div className={`p-6 rounded-2xl border flex items-center justify-between ${
                  darkMode 
                    ? "bg-gradient-to-br from-[#1A110D] to-[#0D0D0D] border-[#2B1D16]" 
                    : "bg-white border-[#2C1810]/10 shadow-sm"
                }`}>
                  <div>
                    <h2 className="text-2xl font-serif font-bold mb-1 text-[#D4AF37]">
                      {analysis.metadata?.document_type || "Document"} Analysis
                    </h2>
                    <p className={`text-xs font-mono uppercase tracking-widest ${darkMode ? "text-[#A39284]" : "text-[#6B5A4E]"}`}>
                      Jurisdiction: {analysis.metadata?.jurisdiction || "Unknown"}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold tracking-widest uppercase text-stone-500 mb-1">Risk Index</div>
                    <div className={`text-4xl font-mono font-bold ${
                      (analysis.summary?.overall_risk_score || 0) > 70 ? 'text-red-400' : 'text-[#D4AF37]'
                    }`}>
                      {analysis.summary?.overall_risk_score || 0}<span className="text-xl text-stone-600">/100</span>
                    </div>
                  </div>
                </div>

                {/* Executive Summary */}
                {analysis.summary?.executive_summary && (
                  <div>
                    <h3 className={`flex items-center gap-2 text-sm tracking-widest uppercase mb-3 ${darkMode ? "text-[#A39284]" : "text-[#6B5A4E]"}`}>
                      <Search size={14} /> Executive Summary
                    </h3>
                    <div className={`leading-relaxed font-serif p-5 rounded-xl border ${
                      darkMode 
                        ? "bg-[#1A110D] border-[#2B1D16] text-stone-300"
                        : "bg-white border-[#2C1810]/10 text-[#2C1810] shadow-sm"
                    }`}>
                      {analysis.summary.executive_summary}
                    </div>
                  </div>
                )}

                {/* Red Flags / Risks */}
                {analysis.risks && analysis.risks.length > 0 && (
                  <div>
                    <h3 className="flex items-center gap-2 text-sm tracking-widest uppercase text-red-400 mb-3">
                      <ShieldAlert size={14} /> Critical Risks Identified
                    </h3>
                    <div className="space-y-3">
                      {[...analysis.risks]
                        .sort((a, b) => {
                          const order = {CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1};
                          return (order[b.severity?.toUpperCase()] || 0) - (order[a.severity?.toUpperCase()] || 0);
                        })
                        .map((risk, idx) => (
                        <div key={idx} className={`p-4 rounded-xl border ${
                          darkMode ? "bg-red-950/10 border-red-900/30" : "bg-red-50 border-red-200"
                        }`}>
                          <div className="flex justify-between items-start mb-2">
                            <span className={`font-bold ${darkMode ? "text-red-200" : "text-red-800"}`}>{risk.risk_type}</span>
                            {renderSeverityBadge(risk.severity)}
                          </div>
                          <p className={`text-sm mb-3 ${darkMode ? "text-red-300/80" : "text-red-700/80"}`}>{risk.reason}</p>
                          <div className={`p-3 rounded-lg text-xs font-mono border-l-[3px] mb-3 ${
                            darkMode ? "bg-black/40 text-red-400/70 border-red-500/50" : "bg-white text-red-600/80 border-red-400"
                          }`}>
                            "{risk.risk_sentence}"
                          </div>
                          <div className="text-xs font-semibold text-[#D4AF37] flex items-start gap-2">
                            <Shield size={12} className="mt-0.5 shrink-0" />
                            <span>Remedy: {risk.suggestion}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Missing Clauses */}
                {analysis.missing_clauses && analysis.missing_clauses.length > 0 && (
                  <div>
                    <h3 className="flex items-center gap-2 text-sm tracking-widest uppercase text-orange-400 mb-3">
                      <FileWarning size={14} /> Missing Protections
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {analysis.missing_clauses.map((mc, idx) => (
                        <div key={idx} className={`p-4 rounded-xl border group ${
                          darkMode ? "bg-[#1A110D] border-orange-900/30" : "bg-orange-50 border-orange-200"
                        }`}>
                          <div className="flex justify-between items-center mb-2">
                            <span className={`font-bold ${darkMode ? "text-orange-200" : "text-orange-800"}`}>{mc.clause_type}</span>
                            {renderSeverityBadge(mc.importance)}
                          </div>
                          <p className={`text-xs line-clamp-2 group-hover:line-clamp-none transition-all ${
                            darkMode ? "text-[#A39284]" : "text-[#6B5A4E]"
                          }`}>
                            {mc.reason_needed}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Negotiation Leverage */}
                {analysis.negotiation_points && analysis.negotiation_points.length > 0 && (
                  <div>
                    <h3 className="flex items-center gap-2 text-sm tracking-widest uppercase text-[#D4AF37] mb-3">
                      <Handshake size={14} /> Leverage & Counter-Proposals
                    </h3>
                    <div className="space-y-3">
                      {analysis.negotiation_points.map((np, idx) => (
                        <div key={idx} className={`p-4 rounded-xl border flex flex-col md:flex-row gap-4 ${
                          darkMode ? "bg-[#1A110D] border-[#D4AF37]/20" : "bg-white border-[#D4AF37]/30 shadow-sm"
                        }`}>
                          <div className="flex-1">
                            <h4 className={`text-sm font-bold mb-1 ${darkMode ? "text-stone-200" : "text-[#2C1810]"}`}>{np.issue}</h4>
                            <p className={`text-xs mb-3 ${darkMode ? "text-[#A39284]" : "text-[#6B5A4E]"}`}><span className="text-amber-500/80">Leverage:</span> {np.leverage}</p>
                          </div>
                          <div className={`flex-1 p-3 rounded-lg border ${
                            darkMode ? "bg-black/30 border-white/5" : "bg-stone-50 border-stone-200"
                          }`}>
                            <span className="text-[10px] uppercase tracking-widest text-[#D4AF37] mb-1 block">Add to agreement:</span>
                            <p className={`text-xs font-mono border-l-2 pl-2 ${darkMode ? "text-stone-300 border-[#D4AF37]" : "text-stone-700 border-[#D4AF37]"}`}>"{np.suggested_counter}"</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            )}
            
          </div>
        </section>

      </main>
    </div>
  );
}
