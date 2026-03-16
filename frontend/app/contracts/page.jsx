"use client";

import { useEffect, useState } from "react";
import { getCurrentUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { signWithMetaMask } from "@/utils/signContract";
import { 
  FileText, 
  ArrowLeft, 
  CheckCircle, 
  XCircle, 
  ExternalLink, 
  Copy, 
  PenTool, 
  Rocket,
  RefreshCw,
  Clock
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export default function ContractsPage() {
  const router = useRouter();
  const [contracts, setContracts] = useState([]);
  const [user, setUser] = useState(null);
  const [loadingId, setLoadingId] = useState(null);
  
  /* ================= THEME SYNC ================= */
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme !== null) {
      setDarkMode(savedTheme === "true");
    }
    init();
  }, []);

  const init = async () => {
    const u = await getCurrentUser();
    if (!u) return router.push("/login");
    setUser(u);
    fetchContracts(u.id);
  };

  /* ================= AUTO REFRESH ================= */
  useEffect(() => {
    if (!user?.id) return;
    const interval = setInterval(() => {
      fetchContracts(user.id);
    }, 6000);
    return () => clearInterval(interval);
  }, [user?.id]);

  const fetchContracts = async (userId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/contracts/all/${userId}`);
      const data = await res.json();
      setContracts(data);
    } catch (err) {
      console.error("Fetch failed:", err);
    }
  };

  /* ================= ACTIONS ================= */
  const handleAccept = async (contractId) => {
    try {
      setLoadingId(contractId);
      await fetch(`${API_BASE_URL}/contracts/${contractId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "PENDING_SIGNATURE_B" }),
      });
      fetchContracts(user.id);
    } catch (err) { console.error(err); } finally { setLoadingId(null); }
  };

  const handleReject = async (contractId) => {
    try {
      setLoadingId(contractId);
      await fetch(`${API_BASE_URL}/contracts/${contractId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "REJECTED" }),
      });
      fetchContracts(user.id);
    } catch (err) { console.error(err); } finally { setLoadingId(null); }
  };

  const handleReceiverSign = async (contract) => {
    try {
      setLoadingId(contract.contract_id);
      const { signature, wallet } = await signWithMetaMask(contract.file_url);
      await fetch(`${API_BASE_URL}/store-signature`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          user_id: user.id,
          wallet_address: wallet,
          signature,
          role: "B",
        }),
      });
      fetchContracts(user.id);
    } catch (err) { console.error(err); } finally { setLoadingId(null); }
  };

  const handleSenderSign = async (contract) => {
    try {
      setLoadingId(contract.contract_id);
      const { signature, wallet } = await signWithMetaMask(contract.file_url);
      await fetch(`${API_BASE_URL}/store-signature`, {
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
      await fetch(`${API_BASE_URL}/contracts/${contract.contract_id}/finalize`, { method: "POST" });
      fetchContracts(user.id);
    } catch (err) { console.error(err); } finally { setLoadingId(null); }
  };

  const copyTx = (tx) => {
    navigator.clipboard.writeText(tx);
    alert("✅ TX Hash copied to clipboard");
  };

  if (!user) return null;

  return (
    <div className={`min-h-screen transition-colors duration-500 p-6 md:p-12 ${
      darkMode 
        ? "bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-[#3E2C23] via-[#150D0A] to-[#0D0D0D] text-[#F5E6D8]" 
        : "bg-[#FDFCF9] text-[#2C1810]"
    }`}>
      <div className="max-w-6xl mx-auto">
        
        {/* HEADER & NAV */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-12">
          <div>
            <button 
              onClick={() => router.push('/dashboard')}
              className={`flex items-center gap-2 mb-4 group uppercase tracking-widest text-xs font-semibold ${
                darkMode ? "text-[#A39284] hover:text-[#D4AF37]" : "text-gray-500 hover:text-[#D4AF37]"
              }`}
            >
              <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
              <span>Dashboard</span>
            </button>
            <h1 className="text-4xl font-serif font-bold tracking-tight">
              Contract <span className="text-[#D4AF37]">Registry</span>
            </h1>
          </div>
          
          
        </div>

        {/* CONTRACT LIST */}
        {contracts.length === 0 ? (
          <div className={`text-center py-20 rounded-3xl border-2 border-dashed ${
            darkMode ? "border-white/10 bg-white/5" : "border-black/10 bg-black/5"
          }`}>
            <FileText size={48} className="mx-auto mb-4 opacity-20" />
            <p className="text-xl font-serif italic opacity-50">The registry is currently empty.</p>
          </div>
        ) : (
          <div className="grid gap-6">
            {contracts.map((c) => {
              const isSender = c.sender_id === user.id;
              const status = c.status?.trim().toUpperCase();

              return (
                <div
                  key={c.contract_id}
                  className={`group rounded-2xl border transition-all duration-300 p-6 ${
                    darkMode 
                      ? "bg-[#1A110D] border-[#2B1D16] hover:border-[#D4AF37]/30 shadow-2xl" 
                      : "bg-white border-gray-200 shadow-lg hover:border-[#D4AF37]"
                  }`}
                >
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    
                    {/* INFO SIDE */}
                    <div className="flex items-center gap-5">
                      <div className={`p-4 rounded-xl transition-colors ${
                        darkMode 
                          ? (isSender ? 'bg-amber-900/20' : 'bg-stone-800/40') 
                          : (isSender ? 'bg-[#D4AF37]/10' : 'bg-stone-100')
                      }`}>
                        <FileText size={28} className={
                          darkMode 
                            ? (isSender ? 'text-[#D4AF37]' : 'text-stone-400') 
                            : (isSender ? 'text-[#8B6E1F]' : 'text-[#2C1810]')
                        } />
                      </div>
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="text-xl font-serif font-bold">
                            {isSender ? "Outbound Transfer" : "Inbound Protocol"}
                          </h3>
                          <span className={`text-[10px] font-bold tracking-widest uppercase px-3 py-1 rounded-full border ${
                            status === "FINALIZED" 
                              ? "bg-green-500/10 border-green-500/30 text-green-500"
                              : "bg-amber-500/10 border-amber-500/30 text-amber-500"
                          }`}>
                            {status === "FINALIZED" ? "ON BLOCKCHAIN" : status.replace(/_/g, ' ')}
                          </span>
                        </div>
                        <p className={`text-sm font-mono opacity-70 flex items-center gap-2 ${darkMode ? 'text-[#A39284]' : 'text-[#6B5A4E]'}`}>
                          <Clock size={12} /> {c.receiver_email}
                        </p>
                      </div>
                    </div>

                    {/* ACTION SIDE */}
                    <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
                      <a
                        href={c.file_url}
                        target="_blank"
                        className={`flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest transition-all ${
                          darkMode ? "bg-white/5 text-[#F5E6D8] hover:bg-white/10" : "bg-stone-100 text-[#2C1810] hover:bg-stone-200"
                        }`}
                      >
                        <ExternalLink size={14} /> Review
                      </a>

                      {c.blockchain_tx_hash && (
                        <button
                          onClick={() => copyTx(c.blockchain_tx_hash)}
                          className={`flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest transition-all ${
                            darkMode ? "bg-black/40 text-[#D4AF37] border border-white/10" : "bg-stone-800 text-white"
                          }`}
                        >
                          <Copy size={14} /> Hash
                        </button>
                      )}

                      {!isSender && status === "SENT" && (
                        <>
                          <button
                            disabled={loadingId === c.contract_id}
                            onClick={() => handleAccept(c.contract_id)}
                            className="bg-green-600 hover:bg-green-700 text-white px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2"
                          >
                            <CheckCircle size={14} /> Accept
                          </button>
                          <button
                            disabled={loadingId === c.contract_id}
                            onClick={() => handleReject(c.contract_id)}
                            className="bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/20 px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2"
                          >
                            <XCircle size={14} /> Reject
                          </button>
                        </>
                      )}

                      {!isSender && status === "PENDING_SIGNATURE_B" && (
                        <button
                          disabled={loadingId === c.contract_id}
                          onClick={() => handleReceiverSign(c)}
                          className="bg-[#D4AF37] hover:bg-[#B8962E] text-[#1A110D] px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest shadow-lg flex items-center gap-2 animate-pulse"
                        >
                          <PenTool size={14} /> Sign Protocol
                        </button>
                      )}

                      {isSender && status === "PENDING_SIGNATURE_A" && (
                        <button
                          disabled={loadingId === c.contract_id}
                          onClick={() => handleSenderSign(c)}
                          className="bg-[#D4AF37] hover:bg-[#B8962E] text-[#1A110D] px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest shadow-lg flex items-center gap-2"
                        >
                          <Rocket size={14} /> Sign & Finalize
                        </button>
                      )}

                      {isSender && status === "REJECTED" && (
                        <button
                          onClick={() => router.push(`/upload?email=${encodeURIComponent(c.receiver_email)}&contractId=${c.contract_id}`)}
                          className="bg-[#8B0000] hover:bg-red-800 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest shadow-lg flex items-center gap-2"
                        >
                          <RefreshCw size={14} /> Reissue
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <footer className="mt-20 text-center">
          <p className={`text-[10px] font-mono tracking-[0.3em] uppercase italic ${
            darkMode ? 'text-[#A39284]/40' : 'text-gray-400'
          }`}>
            Encrypted Registry Protocol • LegalVault v1.0
          </p>
        </footer>
      </div>
    </div>
  );
}
