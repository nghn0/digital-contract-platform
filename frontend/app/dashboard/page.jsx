"use client";

import { useEffect, useState } from "react";
import { getCurrentUser, signOutUser } from "@/lib/auth";
import { signWithMetaMask } from "@/utils/signContract";
import { useRouter } from "next/navigation";
import { FileText, LogOut, PlusCircle, Files, Clock, ChevronRight, Moon, Sun, Brain, ShieldCheck } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [recentContracts, setRecentContracts] = useState([]);
  const [signingId, setSigningId] = useState(null);
  
  /* ================= TOGGLE CHANGE START ================= */
  const [darkMode, setDarkMode] = useState(true);

  // Sync theme with localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme !== null) {
      setDarkMode(savedTheme === "true");
    }
  }, []);
  /* ================= TOGGLE CHANGE END ================== */

  useEffect(() => {
    init();
    const interval = setInterval(() => {
      if (user?.id) fetchRecent(user.id);
    }, 8000);
    return () => clearInterval(interval);
  }, [user?.id]);

  const init = async () => {
    const u = await getCurrentUser();
    if (!u) return router.push("/login");
    setUser(u);
    fetchRecent(u.id);
  };

  const fetchRecent = async (userId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/contracts/all/${userId}`);
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ error: "Unknown error" }));
        throw new Error(errorData.error || "Failed to fetch contracts");
      }
      const data = await res.json();
      const sorted = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setRecentContracts(sorted.slice(0, 5));
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    }
  };

  const handleLogout = async () => {
    await signOutUser();
    router.push("/login");
  };

  const handleSenderSign = async (contract) => {
    try {
      setSigningId(contract.contract_id);
      const { signature, wallet } = await signWithMetaMask(contract.file_url);
      await fetch("http://localhost:5001/store-signature", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          user_id: user.id,
          wallet_address: wallet,
          signature,
          role: "A",
        }),
      });
      await fetch(`http://localhost:5001/contracts/${contract.contract_id}/finalize`, { method: "POST" });
      fetchRecent(user.id);
    } catch (err) {
      console.error("Sender finalize failed:", err);
    } finally {
      setSigningId(null);
    }
  };

  if (!user) return null;

  return (
    <div className={`min-h-screen transition-colors duration-500 p-6 md:p-12 ${
      darkMode 
        ? "bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-[#3E2C23] via-[#150D0A] to-[#0D0D0D]" 
        : "bg-[#FDFCF9]"
    }`}>
      <div className="max-w-5xl mx-auto">
        
        {/* HEADER */}
        <header className="flex justify-between items-center mb-16">
          <div className="space-y-1">
            <h1 className={`text-3xl md:text-5xl font-serif font-light tracking-tight transition-colors ${darkMode ? 'text-[#F5E6D8]' : 'text-[#2C1810]'}`}>
              Legal<span className="font-bold text-[#D4AF37]">Vault</span>
            </h1>
            <p className={`${darkMode ? 'text-[#A39284]' : 'text-[#6B5A4E]'} text-sm uppercase tracking-[0.2em] font-medium transition-colors`}>
              Digital Signature Terminal
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* TOGGLE BUTTON UPDATED WITH LOCAL STORAGE */}
            <button
              onClick={() => {
                const newMode = !darkMode;
                setDarkMode(newMode);
                localStorage.setItem("theme", newMode);
              }}
              className={`p-2.5 rounded-full border transition-all ${
                darkMode 
                  ? 'bg-white/5 border-white/10 text-[#D4AF37] hover:bg-white/10' 
                  : 'bg-black/5 border-black/10 text-[#2C1810] hover:bg-black/10'
              }`}
            >
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            <button
              onClick={handleLogout}
              className={`flex items-center gap-2 group transition-all border px-5 py-2 rounded-full backdrop-blur-sm ${
                darkMode 
                  ? 'text-[#F5E6D8] border-white/10 hover:border-[#D4AF37]/50' 
                  : 'text-[#2C1810] border-black/10 hover:border-[#D4AF37]'
              }`}
            >
              <LogOut size={18} className="group-hover:-translate-x-1 transition-transform" />
              <span className="text-sm font-semibold uppercase tracking-wider">Logout</span>
            </button>
          </div>
        </header>

        <main className="space-y-12">
          
          {/* ACTION CARDS */}
          <section className="grid md:grid-cols-2 gap-6 pb-6">
            {/* SEND CONTRACT CARD */}
            <div
              onClick={() => router.push("/upload")}
              className={`group cursor-pointer p-8 rounded-2xl border transition-all duration-300 hover:-translate-y-1 shadow-lg flex flex-col h-full min-h-[220px] backdrop-blur-md ${
                darkMode 
                  ? 'bg-[#F5F5DC]/10 border-[#F5F5DC]/20 hover:bg-yellow-950/40' 
                  : 'bg-[#F5F5DC]/40 border-[#2C1810]/10 hover:bg-[#D4AF37]/40 shadow-sm'
              }`}
            >
              <PlusCircle className={`mb-6 transition-colors ${darkMode ? 'text-[#F5F5DC] opacity-80 group-hover:text-[#D4AF37]' : 'text-[#2C1810]'}`} size={32} />
              <h2 className={`text-2xl font-serif font-bold mb-2 transition-colors ${darkMode ? 'text-[#F5F5DC]' : 'text-[#2C1810]'}`}>
                Send Contract
              </h2>
              <p className={`leading-relaxed font-medium transition-opacity ${darkMode ? 'text-[#F5F5DC]/60 group-hover:opacity-100' : 'text-[#2C1810]/70'}`}>
                Initiate a formal contract request and dispatch for secure cryptographic signature.
              </p>
              <div className="mt-auto pt-6 flex items-center text-[#D4AF37] font-bold text-sm uppercase tracking-wider group-hover:gap-2 transition-all">
                Begin Upload <ChevronRight size={16} />
              </div>
            </div>

            {/* VIEW CONTRACT CARD */}
            <div
              onClick={() => router.push("/contracts")}
              className={`group cursor-pointer p-8 rounded-2xl border transition-all duration-300 hover:-translate-y-1 shadow-lg flex flex-col h-full min-h-[220px] backdrop-blur-md ${
                darkMode 
                  ? 'bg-[#F5F5DC]/10 border-[#F5F5DC]/20 hover:bg-yellow-950/40' 
                  : 'bg-[#F5F5DC]/40 border-[#2C1810]/10 hover:bg-[#D4AF37]/40 shadow-sm'
              }`}
            >
              <Files className={`mb-6 transition-colors ${darkMode ? 'text-[#F5F5DC] opacity-80 group-hover:text-[#D4AF37]' : 'text-[#2C1810]'}`} size={32} />
              <h2 className={`text-2xl font-serif font-bold mb-2 transition-colors ${darkMode ? 'text-[#F5E6D8]' : 'text-[#2C1810]'}`}>
                View Contract
              </h2>
              <p className={`leading-relaxed font-medium transition-opacity ${darkMode ? 'text-[#F5E6D8]/60 group-hover:opacity-100' : 'text-[#2C1810]/70'}`}>
                Review historical records, pending verifications, and finalized legal instruments.
              </p>
              <div className="mt-auto pt-6 flex items-center text-[#D4AF37] font-bold text-sm uppercase tracking-wider group-hover:gap-2 transition-all">
                Open Records <ChevronRight size={16} />
              </div>
            </div>

            {/* LEGALT INTELLIGENCE CARD */}
            <div
              onClick={() => router.push("/intelligence")}
              className={`group cursor-pointer p-8 rounded-2xl border transition-all duration-300 hover:-translate-y-1 shadow-lg flex flex-col h-full min-h-[220px] backdrop-blur-md ${
                darkMode 
                  ? 'bg-[#F5F5DC]/10 border-[#F5F5DC]/20 hover:bg-yellow-950/40' 
                  : 'bg-[#F5F5DC]/40 border-[#2C1810]/10 hover:bg-[#D4AF37]/40 shadow-sm'
              }`}
            >
              <Brain className={`mb-6 transition-colors ${darkMode ? 'text-[#F5F5DC] opacity-80 group-hover:text-[#D4AF37]' : 'text-[#2C1810]'}`} size={32} />
              <h2 className={`text-2xl font-serif font-bold mb-2 transition-colors ${darkMode ? 'text-[#F5E6D8]' : 'text-[#2C1810]'}`}>
                LegalT Intelligence
              </h2>
              <p className={`leading-relaxed font-medium transition-opacity ${darkMode ? 'text-[#F5E6D8]/60 group-hover:opacity-100' : 'text-[#2C1810]/70'}`}>
                Instantly audit any drafted agreement against established multi-jurisdictional precedents and flag critical risks ephemerally.
              </p>
              <div className="mt-auto pt-6 flex items-center text-[#D4AF37] font-bold text-sm uppercase tracking-wider group-hover:gap-2 transition-all">
                Analyze Drafts <ChevronRight size={16} />
              </div>
            </div>

            {/* LEGAL VERIFIER CARD */}
            <div
              onClick={() => router.push("/verifier")}
              className={`group cursor-pointer p-8 rounded-2xl border transition-all duration-300 hover:-translate-y-1 shadow-lg flex flex-col h-full min-h-[220px] backdrop-blur-md ${
                darkMode 
                  ? 'bg-[#F5F5DC]/10 border-[#F5F5DC]/20 hover:bg-yellow-950/40' 
                  : 'bg-[#F5F5DC]/40 border-[#2C1810]/10 hover:bg-[#D4AF37]/40 shadow-sm'
              }`}
            >
              <ShieldCheck className={`mb-6 transition-colors ${darkMode ? 'text-[#F5F5DC] opacity-80 group-hover:text-[#D4AF37]' : 'text-[#2C1810]'}`} size={32} />
              <h2 className={`text-2xl font-serif font-bold mb-2 transition-colors ${darkMode ? 'text-[#F5E6D8]' : 'text-[#2C1810]'}`}>
                Legal Verifier
              </h2>
              <p className={`leading-relaxed font-medium transition-opacity ${darkMode ? 'text-[#F5E6D8]/60 group-hover:opacity-100' : 'text-[#2C1810]/70'}`}>
                Cross-reference local documents against decentralized blockchain ledger to detect tampering immediately.
              </p>
              <div className="mt-auto pt-6 flex items-center text-[#D4AF37] font-bold text-sm uppercase tracking-wider group-hover:gap-2 transition-all">
                Verify Authenticity <ChevronRight size={16} />
              </div>
            </div>
          </section>

          {/* RECENT ACTIVITY */}
          <section className={`rounded-xl p-8 transition-all duration-300 ${
            darkMode 
              ? 'bg-[#1A110D] border border-[#2B1D16]' 
              : 'bg-white border border-yellow-900/10 shadow-sm'
          }`}>
            <div className="flex items-center gap-3 mb-8">
              <Clock className="text-[#D4AF37]" size={20} />
              <h3 className={`text-2xl font-serif ${darkMode ? 'text-[#F5E6D8]' : 'text-[#2C1810]'}`}>
                Recent Activity
              </h3>
            </div>

            {recentContracts.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed border-[#F5E6D8]/10 rounded-lg">
                <p className="text-[#A39284] italic font-serif">No active instruments found in the registry.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentContracts.map((c) => {
                  const isSender = c.sender_id === user.id;
                  const needsSenderSign = isSender && c.status === "AWAITING_SENDER_SIGNATURE";
                  const isRejected = isSender && c.status === "REJECTED";

                  return (
                    <div
                      key={c.contract_id}
                      className={`flex flex-col md:flex-row md:justify-between md:items-center gap-4 p-6 rounded border transition-all ${
                        darkMode 
                          ? 'bg-[#150D0A]/50 border-[#F5E6D8]/10 hover:border-[#D4AF37]/40' 
                          : 'bg-gray-50 border-gray-200 hover:border-red-800/30'
                      }`}
                    >
                      <div className="flex items-center gap-5">
                        <div className={`p-3 rounded-lg transition-colors ${
                          darkMode 
                            ? (isSender ? 'bg-amber-900/20' : 'bg-stone-800/40') 
                            : (isSender ? 'bg-[#D4AF37]/20' : 'bg-stone-200')
                        }`}>
                          <FileText 
                            size={22} 
                            className={
                              darkMode 
                                ? (isSender ? 'text-[#D4AF37]' : 'text-stone-400') 
                                : (isSender ? 'text-[#8B6E1F]' : 'text-[#2C1810]')
                            } 
                          />
                        </div>

                        <div>
                          <p className={`font-serif text-xl mb-1 ${darkMode ? 'text-[#F5E6D8]' : 'text-[#2C1810]'}`}>
                            {isSender ? "Outbound Transfer" : "Inbound Protocol"}
                          </p>
                          <p className={`text-sm font-mono opacity-70 lowercase tracking-tighter ${darkMode ? 'text-[#A39284]' : 'text-[#6B5A4E]'}`}>
                            Ref: {c.receiver_email}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-6">
                        <span className={`text-[10px] font-bold tracking-[0.2em] uppercase px-4 py-1.5 rounded border ${
                          darkMode 
                            ? 'bg-black/40 text-[#A39284] border-white/10' 
                            : 'bg-stone-200 text-[#2C1810] border-stone-300'
                        }`}>
                          {c.status === "FINALIZED" || c.status === "ON_BLOCKCHAIN" 
                            ? "ON BLOCKCHAIN" 
                            : c.status === "AWAITING_SENDER_SIGNATURE" ? "Awaiting sender signature"
                            : c.status === "AWAITING_RECEIVER_SIGNATURE" ? "Awaiting receiver signature"
                            : c.status.replace(/_/g, ' ')}
                        </span>

                        {needsSenderSign && (
                          <button
                            onClick={() => handleSenderSign(c)}
                            disabled={signingId === c.contract_id}
                            className="bg-[#D4AF37] hover:bg-[#B8962E] text-[#1A110D] px-6 py-2 rounded font-bold text-xs uppercase tracking-widest transition-all shadow-lg active:translate-y-0.5"
                          >
                            {signingId === c.contract_id ? "Verifying..." : "Counter-Sign"}
                          </button>
                        )}

                        {isRejected && (
                          <button
                            onClick={() => router.push(`/upload?email=${encodeURIComponent(c.receiver_email)}&contractId=${c.contract_id}`)}
                            className="bg-[#8B0000] hover:bg-red-800 text-white px-6 py-2 rounded font-bold text-xs tracking-widest transition"
                          >
                            Re-Issue
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </main>
        
        <footer className="mt-16 text-center">
            <p className={`text-xs font-mono tracking-tighter uppercase italic ${darkMode ? 'text-[#A39284]/40' : 'text-gray-400'}`}>
              Authenticated via Web3 Protocol • Secured by RSA-2048 Cryptography
            </p>
        </footer>
      </div>
    </div>
  );
}
