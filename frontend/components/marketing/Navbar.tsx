import Link from "next/link";
import Image from "next/image";

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-[var(--color-border-color)] bg-[var(--color-background)]/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <Image src="/logo.png" alt="LegalVault Logo" width={36} height={36} className="object-contain" />
          <span className="text-xl font-serif tracking-tight text-[var(--color-primary-text)]">
            Legal<span className="font-bold text-[var(--color-primary-gold)]">Vault</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-[var(--color-muted-text)]">
          <Link href="#problem" className="hover:text-[var(--color-primary-text)] transition-colors">Product</Link>
          <Link href="#workflow" className="hover:text-[var(--color-primary-text)] transition-colors">How it works</Link>
          <Link href="#capabilities" className="hover:text-[var(--color-primary-text)] transition-colors">Capabilities</Link>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-[var(--color-primary-text)] hover:text-[var(--color-primary-gold)] transition-colors hidden sm:block">
            Sign In
          </Link>
          <Link href="/dashboard" className="h-10 px-5 flex items-center justify-center rounded-lg bg-[var(--color-primary-gold)] text-[var(--color-surface)] text-sm font-bold hover:bg-[var(--color-bright-gold)] transition-colors">
            Access Vault
          </Link>
        </div>
      </div>
    </nav>
  );
}
