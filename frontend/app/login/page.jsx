"use client";

import { useState, Suspense } from "react";
import { signInUser } from "@/lib/auth";
import { useRouter, useSearchParams } from "next/navigation";
import { linkContractsAfterLogin } from "@/lib/linkContracts";
import { Mail, Lock, ArrowRight, ArrowLeft, Beaker } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPath = searchParams.get("next");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    try {
      setLoading(true);
      setMsg("");

      await signInUser(email, password);

      // Execute background tasks WITHOUT blocking the critical navigation path
      // This prevents backend latency from stalling the UI on "Verifying..."
      linkContractsAfterLogin().catch((err) => {
        console.error("Background contract link failed:", err);
      });

      // Clear the Next.js client-side router cache to ensure the new session is used
      router.refresh();

      if (nextPath && nextPath.startsWith('/') && !nextPath.startsWith('//') && !nextPath.startsWith('/\\')) {
        router.replace(nextPath);
      } else {
        router.replace("/dashboard");
      }
    } catch (err) {
      setMsg("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    try {
      setDemoLoading(true);
      setMsg("");

      const res = await fetch("/api/auth/demo", { method: "POST" });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Demo authentication failed");
      }

      await linkContractsAfterLogin();

      if (nextPath && nextPath.startsWith('/') && !nextPath.startsWith('//') && !nextPath.startsWith('/\\')) {
        router.replace(nextPath);
      } else {
        router.replace("/dashboard");
      }
    } catch (err) {
      setMsg("❌ " + err.message);
    } finally {
      setDemoLoading(false);
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
            LegalVault Access
          </h1>
          <p className="text-[#A39284] text-xs uppercase tracking-[0.2em] mt-3 font-medium">
            Identity Verification
          </p>
        </div>

        {/* LOGIN CARD */}
        <div className="p-8 rounded-2xl bg-[#0f0f0f] border border-[#1a1a1a] shadow-lg relative overflow-hidden">
          {/* Subtle gradient glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1 bg-gradient-to-r from-transparent via-[#D4AF37]/40 to-transparent"></div>

          <form onSubmit={handleLogin} className="space-y-5">
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
                placeholder="Access Key"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-[#222222] bg-[#0a0a0a] focus:border-[#D4AF37]/50 focus:ring-1 focus:ring-[#D4AF37]/50 text-[#F5E6D8] placeholder-[#A39284]/50 outline-none font-medium transition-all"
              />
            </div>

            {/* LOGIN BUTTON */}
            <button
              type="submit"
              disabled={loading || demoLoading}
              className="group w-full py-4 rounded-xl font-bold text-sm uppercase tracking-[0.15em] transition-all flex items-center justify-center gap-3 bg-[#D4AF37] hover:bg-[#B8962E] text-[#1A110D] disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? "Verifying Identity..." : "Access Vault"}
              {!loading && <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />}
            </button>

            {/* DEMO BUTTON */}
            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={loading || demoLoading}
              className="group w-full py-3.5 rounded-xl font-semibold text-sm tracking-[0.05em] transition-all flex items-center justify-center gap-2 border border-transparent hover:border-[#222222] bg-transparent hover:bg-[#151515] text-[#A39284] hover:text-[#F5E6D8] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Beaker size={16} className="text-[#A39284] group-hover:text-[#D4AF37] transition-colors" />
              {demoLoading ? "Initializing Demo..." : "Try Demo Access"}
            </button>

            {/* SIGNUP LINK */}
            <div className="text-center pt-4 border-t border-[#222222] mt-4">
              <p className="text-sm text-[#A39284]">
                Don't have an account?{' '}
                <Link
                  href="/signup"
                  className="text-[#D4AF37] font-medium hover:text-[#F5E6D8] transition-colors"
                >
                  Sign up
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

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[#0a0a0a]">
        <div className="w-8 h-8 border-2 border-[#D4AF37] border-t-transparent rounded-full animate-spin"></div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
