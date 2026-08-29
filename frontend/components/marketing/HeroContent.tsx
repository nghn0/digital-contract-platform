import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function HeroContent() {
  return (
    <div className="flex flex-col items-start text-left z-10 w-full">
      <h1 className="text-4xl md:text-5xl lg:text-6xl font-serif font-medium leading-[1.1] tracking-tight mb-6">
        Contracts should be easier to <span className="text-[var(--color-primary-gold)]">understand</span> — and harder to <span className="text-[var(--color-primary-gold)]">tamper with</span>.
      </h1>
      
      <p className="text-lg md:text-xl text-[var(--color-muted-text)] mb-10 max-w-xl leading-relaxed">
        LegalVault combines AI-powered contract analysis with cryptographic verification and blockchain-backed signing to help you review, execute, and verify digital contracts in one workflow.
      </p>

      <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
        <Link 
          href="/intelligence" 
          className="group flex h-14 items-center justify-center gap-3 rounded-xl bg-[var(--color-primary-gold)] px-8 text-lg font-bold text-[var(--color-surface)] transition-all hover:bg-[var(--color-bright-gold)] shadow-xl shadow-[var(--color-primary-gold)]/10"
        >
          Analyze a Contract
          <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
        </Link>
        
        <Link 
          href="#how-it-works"
          className="flex h-14 items-center justify-center rounded-xl border border-[var(--color-border-color)] px-8 text-lg font-medium text-[var(--color-primary-text)] hover:bg-[var(--color-surface)] transition-colors"
        >
          See How It Works
        </Link>
      </div>
      
      <div className="mt-12 flex flex-wrap items-center gap-3 text-xs sm:text-sm text-[var(--color-muted-text)] font-mono uppercase tracking-widest">
        <span>AI Analysis</span>
        <span className="w-1 h-1 rounded-full bg-[var(--color-primary-gold)] hidden sm:block"></span>
        <span className="hidden sm:inline">Wallet Signatures</span>
        <span className="w-1 h-1 rounded-full bg-[var(--color-primary-gold)] hidden sm:block"></span>
        <span className="hidden sm:inline">Blockchain Verification</span>
      </div>
    </div>
  );
}
