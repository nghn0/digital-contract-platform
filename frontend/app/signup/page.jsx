"use client";

import { useState, useEffect } from "react";
import { signUpUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { ShieldCheck, Mail, Lock, UserPlus, ArrowRight } from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  /* ================= THEME SYNC ================= */
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme !== null) {
      setDarkMode(savedTheme === "true");
    }
  }, []);

  const handleSignup = async () => {
    try {
      setLoading(true);
      setMsg("");

      await signUpUser(email, password);

      setMsg("✅ Account created! Redirecting to login...");
      setTimeout(() => {
        router.push("/login");
      }, 1500);
    } catch (err) {
      setMsg("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-500 flex items-center justify-center p-6 ${
      darkMode 
        ? "bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-[#3E2C23] via-[#150D0A] to-[#0D0D0D]" 
        : "bg-[#FDFCF9]"
    }`}>
      <div className="w-full max-w-md">
        
        {/* BRANDING */}
        <div className="text-center mb-10">
          <div className="inline-block p-4 rounded-2xl bg-[#D4AF37]/10 border border-[#D4AF37]/20 mb-4">
            <ShieldCheck size={48} className="text-[#D4AF37]" />
          </div>
          <h1 className={`text-4xl font-serif font-light tracking-tight ${darkMode ? 'text-[#F5E6D8]' : 'text-[#2C1810]'}`}>
            Legal<span className="font-bold text-[#D4AF37]">Vault</span>
          </h1>
          <p className={`${darkMode ? 'text-[#A39284]' : 'text-gray-500'} text-xs uppercase tracking-[0.3em] mt-2 font-medium`}>
            Registry Enrollment
          </p>
        </div>

        {/* SIGNUP CARD */}
        <div className={`p-8 rounded-3xl border transition-all duration-300 shadow-2xl ${
          darkMode 
            ? 'bg-[#1A110D] border-[#2B1D16]' 
            : 'bg-white border-gray-200 shadow-xl'
        }`}>
          <h2 className={`text-xl font-serif font-bold mb-8 text-center ${darkMode ? 'text-[#F5E6D8]' : 'text-[#2C1810]'}`}>
            Create Legal Identity
          </h2>

          <div className="space-y-6">
            {/* EMAIL */}
            <div className="relative">
              <Mail className={`absolute left-4 top-1/2 -translate-y-1/2 ${darkMode ? 'text-[#A39284]' : 'text-gray-400'}`} size={18} />
              <input
                type="email"
                placeholder="Official Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={`w-full pl-12 pr-4 py-4 rounded-2xl border transition-all outline-none font-medium ${
                  darkMode
                    ? "bg-black/20 border-[#2B1D16] focus:border-[#D4AF37]/50 text-[#F5E6D8]"
                    : "bg-gray-50 border-gray-200 focus:border-[#D4AF37] text-gray-900"
                }`}
              />
            </div>

            {/* PASSWORD */}
            <div className="relative">
              <Lock className={`absolute left-4 top-1/2 -translate-y-1/2 ${darkMode ? 'text-[#A39284]' : 'text-gray-400'}`} size={18} />
              <input
                type="password"
                placeholder="Secure Access Key"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`w-full pl-12 pr-4 py-4 rounded-2xl border transition-all outline-none font-medium ${
                  darkMode
                    ? "bg-black/20 border-[#2B1D16] focus:border-[#D4AF37]/50 text-[#F5E6D8]"
                    : "bg-gray-50 border-gray-200 focus:border-[#D4AF37] text-gray-900"
                }`}
              />
            </div>

            {/* SIGNUP BUTTON */}
            <button
              onClick={handleSignup}
              disabled={loading}
              className={`group w-full py-4 rounded-2xl font-bold text-sm uppercase tracking-[0.2em] transition-all shadow-lg active:scale-[0.98] flex items-center justify-center gap-3 ${
                loading 
                  ? "bg-white/5 text-[#A39284] cursor-wait" 
                  : "bg-[#D4AF37] hover:bg-[#B8962E] text-[#1A110D]"
              }`}
            >
              {loading ? "Registering..." : "Create Account"}
              {!loading && <UserPlus size={18} className="group-hover:scale-110 transition-transform" />}
            </button>

            {/* LOGIN REDIRECT */}
            <div className="text-center pt-2">
              <p className={`text-sm ${darkMode ? 'text-[#A39284]' : 'text-gray-500'}`}>
                Already have an account?{' '}
                <button 
                  onClick={() => router.push("/login")}
                  className="text-[#D4AF37] font-bold hover:underline underline-offset-4 decoration-[#D4AF37]/50"
                >
                  Login
                </button>
              </p>
            </div>
          </div>

          {/* STATUS MESSAGE */}
          {msg && (
            <div className={`mt-6 p-4 rounded-xl text-center text-xs font-bold border ${
              msg.includes('❌') 
                ? 'bg-red-500/10 border-red-500/20 text-red-400' 
                : 'bg-green-500/10 border-green-500/20 text-green-400'
            }`}>
              {msg}
            </div>
          )}
        </div>

        {/* FOOTER */}
        <p className={`mt-10 text-center text-[10px] font-mono tracking-widest uppercase italic transition-colors ${
          darkMode ? 'text-[#A39284]/40' : 'text-gray-400'
        }`}>
          Blockchain Identity Protocol • Secured by RSA-2048
        </p>
      </div>
    </div>
  );
}
