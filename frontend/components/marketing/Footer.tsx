import Link from "next/link";
import Image from "next/image";

export default function Footer() {
  return (
    <footer className="w-full border-t border-[var(--color-border-color)] bg-[var(--color-background)] pt-20 pb-10">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">

        {/* Brand Column */}
        <div className="col-span-1 md:col-span-1 flex flex-col gap-4">
          <Link href="/" className="flex items-center gap-3">
            <Image src="/logo.png" alt="LegalVault Logo" width={32} height={32} className="object-contain" />
            <span className="text-xl font-serif tracking-tight text-[var(--color-primary-text)]">
              Legal<span className="font-bold text-[var(--color-primary-gold)]">Vault</span>
            </span>
          </Link>
          <p className="text-sm text-[var(--color-muted-text)] mt-2 leading-relaxed">
            AI-powered contract analysis and verifiable signing.
          </p>
        </div>

        {/* Product Column */}
        <div className="flex flex-col gap-4">
          <h3 className="font-bold text-[var(--color-primary-text)] mb-2 tracking-wide uppercase text-sm">Product</h3>
          <Link href="#problem" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">Problem</Link>
          <Link href="#workflow" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">How it works</Link>
          <Link href="#capabilities" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">Capabilities</Link>
        </div>

        {/* Resources Column */}
        <div className="flex flex-col gap-4">
          <h3 className="font-bold text-[var(--color-primary-text)] mb-2 tracking-wide uppercase text-sm">Resources</h3>
          <Link href="/intelligence" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">Contract analysis</Link>
          <Link href="/dashboard" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">Signing</Link>
          <Link href="/verifier" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">Verification</Link>
        </div>

        {/* Legal Column */}
        <div className="flex flex-col gap-4">
          <h3 className="font-bold text-[var(--color-primary-text)] mb-2 tracking-wide uppercase text-sm">Legal</h3>
          <Link href="/privacy" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">Privacy Policy</Link>
          <Link href="/terms" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">Terms of Service</Link>
          <Link href="/disclaimer" className="text-sm text-[var(--color-muted-text)] hover:text-[var(--color-primary-gold)] transition-colors">Disclaimer</Link>
        </div>

      </div>

      <div className="max-w-7xl mx-auto px-6 pt-8 border-t border-[var(--color-border-color)] flex flex-col md:flex-row items-center justify-between gap-4">
        <p className="text-xs text-[var(--color-muted-text)]">
          © {new Date().getFullYear()} LegalVault. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
