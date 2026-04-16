"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { ArrowLeft, Brain, ShieldAlert, FileWarning, Search, ChevronRight, Activity, Handshake, Info, Shield, PlusCircle } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001";

export default function ContractReviewPage() {
  const { id } = useParams();
  const router = useRouter();
  const [contract, setContract] = useState(null);
  const [user, setUser] = useState(null);
  
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    init();
  }, [id]);

  const init = async () => {
    const u = await getCurrentUser();
    if (!u) return router.push("/login");
    setUser(u);
    
    // Fetch contract metadata
    try {
      const res = await fetch(`${API_BASE_URL}/contract/${id}`);
      if (!res.ok) throw new Error("Failed to load contract");
      const data = await res.json();
      setContract(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  };

  const handleAnalyze = async () => {
    try {
      setIsAnalyzing(true);
      setError(null);
      const res = await fetch(`${API_BASE_URL}/contract/${id}/analyze`, {
        method: "POST"
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

  if (!contract) {
    return (
      <div className="min-h-screen bg-[#0D0D0D] flex items-center justify-center text-[#F5E6D8]">
        {error ? <p className="text-red-400">{error}</p> : <div className="animate-pulse">Loading Document Registry...</div>}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-[#0D0D0D] text-[#F5E6D8] overflow-hidden">
      {/* Navbar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-[#2B1D16] bg-[#1A110D]">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => router.push('/contracts')}
            className="flex items-center gap-2 text-stone-400 hover:text-[#D4AF37] transition-colors"
          >
            <ArrowLeft size={16} /> <span className="text-sm font-semibold tracking-widest uppercase">Registry</span>
          </button>
          <div className="h-6 w-px bg-[#2B1D16]"></div>
          <h1 className="font-serif text-xl tracking-wide">{contract.receiver_email}</h1>
        </div>
        <div>
          <span className="px-4 py-1.5 rounded-full text-xs font-bold tracking-widest uppercase bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30">
            {contract.status === "FINALIZED" || contract.status === "ON_BLOCKCHAIN" 
              ? "ON BLOCKCHAIN" 
              : contract.status === "AWAITING_SENDER_SIGNATURE" ? "Awaiting sender signature"
              : contract.status === "AWAITING_RECEIVER_SIGNATURE" ? "Awaiting receiver signature"
              : contract.status.replace(/_/g, " ")}
          </span>
        </div>
      </header>

      {/* Main Split View */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* Left Side: Document Viewer */}
        <section className="w-1/2 h-full border-r border-[#2B1D16] bg-white">
          <iframe 
            src={`${contract.file_url}#toolbar=0`} 
            className="w-full h-full"
            title="Document Viewer"
          />
        </section>

        {/* Right Side: AI Dashboard */}
        <section className="w-1/2 h-full bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[#2C1810]/50 via-[#150D0A] to-[#0D0D0D] overflow-y-auto">
          <div className="p-8">
            
            {/* INITIAL STATE */}
            {!analysis && !isAnalyzing && (
              <div className="h-full flex flex-col items-center justify-center text-center mt-32">
                <div className="w-24 h-24 mb-6 rounded-3xl bg-gradient-to-br from-[#D4AF37] to-[#8B6E1F] flex items-center justify-center shadow-[0_0_40px_rgba(212,175,55,0.2)]">
                  <Brain size={48} className="text-[#1A110D]" />
                </div>
                <h2 className="text-3xl font-serif mb-4">LegalT Intelligence</h2>
                <p className="max-w-md text-[#A39284] mb-12">
                  Execute a deep semantic analysis of the document on the left using the integrated neural network. Identifies critical risks, missing clauses, and negotiation leverage points.
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
                <div className="mt-8 text-sm font-mono text-[#A39284] space-y-2 flex flex-col items-center opacity-80">
                  <p>1 / 5: Vectorizing text nodes...</p>
                  <p>2 / 5: Querying legal knowledge base...</p>
                  <p>3 / 5: Extracting obligations & liabilities...</p>
                  <p className="text-white">4 / 5: Generating negotiation strategy...</p>
                </div>
              </div>
            )}

            {/* ANALYZED STATE */}
            {analysis && (
              <div className="max-w-3xl mx-auto space-y-8 pb-12">
                
                {/* Header Widget */}
                <div className="p-6 rounded-2xl bg-gradient-to-br from-[#1A110D] to-[#0D0D0D] border border-[#2B1D16] flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-serif font-bold mb-1 text-[#D4AF37]">
                      {analysis.metadata?.document_type || "Document"} Analysis
                    </h2>
                    <p className="text-xs font-mono uppercase tracking-widest text-[#A39284]">
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
                    <h3 className="flex items-center gap-2 text-sm tracking-widest uppercase text-[#A39284] mb-3">
                      <Search size={14} /> Executive Summary
                    </h3>
                    <div className="text-stone-300 leading-relaxed font-serif p-5 rounded-xl bg-[#1A110D] border border-[#2B1D16]">
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
                        <div key={idx} className="p-4 rounded-xl bg-red-950/10 border border-red-900/30">
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-bold text-red-200">{risk.risk_type}</span>
                            {renderSeverityBadge(risk.severity)}
                          </div>
                          <p className="text-sm text-red-300/80 mb-3">{risk.reason}</p>
                          <div className="bg-black/40 p-3 rounded-lg text-xs font-mono text-red-400/70 border-l-[3px] border-red-500/50 mb-3">
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
                        <div key={idx} className="p-4 rounded-xl bg-[#1A110D] border border-orange-900/30 group">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-bold text-orange-200">{mc.clause_type}</span>
                            {renderSeverityBadge(mc.importance)}
                          </div>
                          <p className="text-xs text-[#A39284] line-clamp-2 group-hover:line-clamp-none transition-all">
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
                        <div key={idx} className="p-4 rounded-xl bg-[#1A110D] border border-[#D4AF37]/20 flex flex-col md:flex-row gap-4">
                          <div className="flex-1">
                            <h4 className="text-sm font-bold text-stone-200 mb-1">{np.issue}</h4>
                            <p className="text-xs text-[#A39284] mb-3"><span className="text-amber-500/80">Leverage:</span> {np.leverage}</p>
                          </div>
                          <div className="flex-1 bg-black/30 p-3 rounded-lg border border-white/5">
                            <span className="text-[10px] uppercase tracking-widest text-[#D4AF37] mb-1 block">Add to agreement:</span>
                            <p className="text-xs font-mono text-stone-300">"{np.suggested_counter}"</p>
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
