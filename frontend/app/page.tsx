"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, ArrowRight, PenTool, Globe, Lock, UserPlus } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme !== null) {
      setDarkMode(savedTheme === "true");
    }
  }, []);

  return (
    <div className={`min-h-screen transition-colors duration-500 font-sans ${
      darkMode 
        ? "bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-[#3E2C23] via-[#150D0A] to-[#0D0D0D] text-[#F5E6D8]" 
        : "bg-[#FDFCF9] text-[#2C1810]"
    }`}>
      
      {/* BACKGROUND DECORATION */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute -top-24 -right-24 w-96 h-96 rounded-full blur-3xl opacity-20 ${darkMode ? 'bg-[#D4AF37]' : 'bg-[#D4AF37]/30'}`}></div>
        <div className={`absolute top-1/2 -left-24 w-72 h-72 rounded-full blur-3xl opacity-10 ${darkMode ? 'bg-[#D4AF37]' : 'bg-[#D4AF37]/20'}`}></div>
      </div>

      <main className="relative z-10 max-w-6xl mx-auto px-6 py-20 md:py-32 flex flex-col items-center">
        
        {/* LOGO SECTION */}
        <div className="flex items-center gap-3 mb-12 animate-fade-in">
          <div className="p-3 rounded-2xl bg-[#D4AF37]/10 border border-[#D4AF37]/20 backdrop-blur-sm">
            <ShieldCheck size={40} className="text-[#D4AF37]" />
          </div>
          <h1 className="text-4xl font-serif font-light tracking-tighter">
            Legal<span className="font-bold text-[#D4AF37]">Vault</span>
          </h1>
        </div>

        {/* HERO TEXT */}
        <div className="text-center max-w-4xl space-y-8 mb-16">
          <h2 className="text-5xl md:text-7xl font-serif font-bold leading-tight tracking-tight">
            The Future of <span className="italic text-[#D4AF37]">Legal Integrity</span> on the Blockchain.
          </h2>
          
          <p className={`text-xl md:text-2xl leading-relaxed max-w-2xl mx-auto ${darkMode ? 'text-[#A39284]' : 'text-gray-600'}`}>
            Securely upload, execute, and archive legal instruments with 
            cryptographic precision. LegalVault bridges traditional law with decentralized security.
          </p>
        </div>

        {/* PRIMARY ACTIONS */}
        <div className="flex flex-col sm:flex-row gap-6 mb-20 w-full justify-center items-center">
          <button
            onClick={() => router.push("/login")}
            className="group flex h-14 w-full sm:w-64 items-center justify-center gap-3 rounded-2xl bg-[#D4AF37] px-8 text-lg font-bold text-[#1A110D] transition-all hover:bg-[#B8962E] hover:scale-[1.02] active:scale-95 shadow-xl shadow-[#D4AF37]/10"
          >
            Access Vault
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </button>
          
          <button
            onClick={() => router.push("/signup")}
            className={`flex h-14 w-full sm:w-64 items-center justify-center gap-3 rounded-2xl border-2 px-8 text-lg font-bold transition-all active:scale-95 ${
              darkMode 
                ? 'border-[#2B1D16] bg-white/5 text-[#F5E6D8] hover:bg-white/10' 
                : 'border-gray-200 bg-white text-[#2C1810] hover:bg-gray-50'
            }`}
          >
            <UserPlus size={20} />
            Contract Registartion
          </button>
        </div>

        {/* FEATURE HIGHLIGHTS */}
        <div className="grid md:grid-cols-3 gap-8 w-full">
          <div className={`p-8 rounded-3xl border transition-all ${darkMode ? 'bg-[#1A110D] border-[#2B1D16]' : 'bg-white border-gray-100 shadow-lg'}`}>
            <Lock className="text-[#D4AF37] mb-4" size={28} />
            <h3 className="text-xl font-bold mb-2">Immutable Records</h3>
            <p className={`${darkMode ? 'text-[#A39284]' : 'text-gray-500'}`}>Every signature is timestamped and recorded forever on the blockchain ledger.</p>
          </div>
          
          <div className={`p-8 rounded-3xl border transition-all ${darkMode ? 'bg-[#1A110D] border-[#2B1D16]' : 'bg-white border-gray-100 shadow-lg'}`}>
            <PenTool className="text-[#D4AF37] mb-4" size={28} />
            <h3 className="text-xl font-bold mb-2">Digital Signatures</h3>
            <p className={`${darkMode ? 'text-[#A39284]' : 'text-gray-500'}`}>Execute agreements instantly using industry-standard Web3 wallet verification.</p>
          </div>

          <div className={`p-8 rounded-3xl border transition-all ${darkMode ? 'bg-[#1A110D] border-[#2B1D16]' : 'bg-white border-gray-100 shadow-lg'}`}>
            <Globe className="text-[#D4AF37] mb-4" size={28} />
            <h3 className="text-xl font-bold mb-2">Global Access</h3>
            <p className={`${darkMode ? 'text-[#A39284]' : 'text-gray-500'}`}>Manage your legal archives from anywhere in the world with zero downtime.</p>
          </div>
        </div>

        {/* SIGNUP PROMPT */}
        <div className="mt-24 text-center">
          <p className={`text-lg mb-4 ${darkMode ? 'text-[#A39284]' : 'text-gray-500'}`}>
            New to the terminal? 
          </p>
          <button 
            onClick={() => router.push("/signup")}
            className="text-[#D4AF37] font-bold text-xl hover:underline underline-offset-8 decoration-2"
          >
            Create your account here.
          </button>
        </div>

      </main>

      {/* FOOTER */}
      <footer className="w-full py-12 border-t border-white/5 text-center px-6">
        <p className={`text-xs font-mono tracking-[0.3em] uppercase italic transition-colors ${darkMode ? 'text-[#A39284]/40' : 'text-gray-400'}`}>
          Authenticated via Web3 Protocol • Secured by RSA-2048 • LegalVault v1.0
        </p>
      </footer>
    </div>
  );
}
