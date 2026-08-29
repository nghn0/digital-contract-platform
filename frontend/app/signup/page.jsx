"use client";

import { useState } from "react";
import { signUpUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { Mail, Lock, UserPlus, ArrowLeft } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleSignup = async (e) => {
    if (e) e.preventDefault();
    
    if (!consent) {
      setMsg("❌ You must agree to the Terms of Service, Privacy Policy, and Disclaimer.");
      return;
    }

    if (password !== confirmPassword) {
      setMsg("❌ Passwords do not match.");
      return;
    }

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
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#0a0a0a] relative">
      {/* RETURN NAVIGATION */}
      <div className="absolute top-6 left-6 md:top-10 md:left-10 z-20">
        <Link href="/" className="inline-flex items-center gap-2 text-[#A39284] hover:text-[#F5E6D8] transition-colors text-sm font-medium opacity-80 hover:opacity-100">
          <ArrowLeft size={14} />
          Return to LegalVault
        </Link>
      </div>

      <div className="w-full max-w-md relative z-10">

        {/* BRANDING */}
        <div className="text-center mb-10">
          <div className="flex justify-center mb-6">
            <Image
              src="/logo.png"
              alt="LegalVault Logo"
              width={80}
              height={80}
              className="object-contain"
            />
          </div>
          <h1 className="text-3xl font-serif font-bold tracking-tight text-[#F5E6D8]">
            Create your LegalVault account
          </h1>
          <p className="text-[#A39284] text-xs uppercase tracking-[0.2em] mt-3 font-medium">
            Create Secure Access
          </p>
        </div>

        {/* SIGNUP CARD */}
        <div className="p-8 rounded-2xl bg-[#0f0f0f] border border-[#1a1a1a] shadow-lg relative overflow-hidden">
          {/* Subtle gradient glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1 bg-gradient-to-r from-transparent via-[#D4AF37]/40 to-transparent"></div>

          <form onSubmit={handleSignup} className="space-y-5">
            {/* EMAIL */}
            <div className="relative group">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-[#A39284] group-focus-within:text-[#D4AF37] transition-colors" size={18} />
              <input
                type="email"
                placeholder="Official Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-[#222222] bg-[#0a0a0a] focus:border-[#D4AF37]/50 focus:ring-1 focus:ring-[#D4AF37]/50 text-[#F5E6D8] placeholder-[#A39284]/50 outline-none font-medium transition-all"
              />
            </div>

            {/* PASSWORD */}
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-[#A39284] group-focus-within:text-[#D4AF37] transition-colors" size={18} />
              <input
                type="password"
                placeholder="Secure Access Key"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-[#222222] bg-[#0a0a0a] focus:border-[#D4AF37]/50 focus:ring-1 focus:ring-[#D4AF37]/50 text-[#F5E6D8] placeholder-[#A39284]/50 outline-none font-medium transition-all"
              />
            </div>

            {/* CONFIRM PASSWORD */}
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-[#A39284] group-focus-within:text-[#D4AF37] transition-colors" size={18} />
              <input
                type="password"
                placeholder="Confirm Access Key"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-[#222222] bg-[#0a0a0a] focus:border-[#D4AF37]/50 focus:ring-1 focus:ring-[#D4AF37]/50 text-[#F5E6D8] placeholder-[#A39284]/50 outline-none font-medium transition-all"
              />
            </div>

            {/* CONSENT CHECKBOX */}
            <div className="flex items-start gap-3 mt-4">
              <input
                type="checkbox"
                id="consent"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-1 w-4 h-4 rounded border-[#222222] bg-[#0a0a0a] text-[#D4AF37] focus:ring-[#D4AF37]/50 focus:ring-offset-0 transition-all cursor-pointer"
              />
              <label htmlFor="consent" className="text-xs text-[#A39284] leading-relaxed select-none">
                I agree to the <Link href="/terms" className="text-[#D4AF37] hover:text-[#F5E6D8] underline decoration-[#D4AF37]/30 hover:decoration-[#D4AF37] transition-all" target="_blank">Terms of Service</Link> and acknowledge the <Link href="/privacy" className="text-[#D4AF37] hover:text-[#F5E6D8] underline decoration-[#D4AF37]/30 hover:decoration-[#D4AF37] transition-all" target="_blank">Privacy Policy</Link> and <Link href="/disclaimer" className="text-[#D4AF37] hover:text-[#F5E6D8] underline decoration-[#D4AF37]/30 hover:decoration-[#D4AF37] transition-all" target="_blank">Disclaimer</Link>.
              </label>
            </div>

            {/* SIGNUP BUTTON */}
            <button
              type="submit"
              disabled={loading || !consent}
              className="group w-full py-4 rounded-xl font-bold text-sm uppercase tracking-[0.15em] transition-all flex items-center justify-center gap-3 bg-[#D4AF37] hover:bg-[#B8962E] text-[#1A110D] disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? "Registering..." : "Create Account"}
              {!loading && <UserPlus size={18} className="group-hover:scale-110 transition-transform" />}
            </button>

            {/* LOGIN REDIRECT */}
            <div className="text-center pt-4 border-t border-[#222222] mt-4">
              <p className="text-sm text-[#A39284]">
                Already have an account?{' '}
                <Link
                  href="/login"
                  className="text-[#D4AF37] font-medium hover:text-[#F5E6D8] transition-colors"
                >
                  Access Vault
                </Link>
              </p>
            </div>
          </form>

          {/* STATUS MESSAGE */}
          {msg && (
            <div className={`mt-5 p-3 rounded-lg text-center text-sm font-medium border transition-all ${msg.includes('❌')
                ? 'bg-red-500/10 border-red-500/20 text-red-400'
                : 'bg-green-500/10 border-green-500/20 text-green-400'
              }`}>
              {msg}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
