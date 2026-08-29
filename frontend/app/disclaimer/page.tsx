import Link from "next/link";
import { ArrowLeft, ShieldAlert } from "lucide-react";
import Image from "next/image";

export default function DisclaimerPage() {
  return (
    <div className="min-h-screen bg-[var(--color-background)] font-sans selection:bg-[var(--color-primary-gold)] selection:text-[var(--color-surface)]">
      <div className="max-w-3xl mx-auto px-6 py-20">
        <Link href="/" className="inline-flex items-center gap-2 mb-12 text-[var(--color-muted-text)] hover:text-[var(--color-primary-text)] transition-colors text-sm font-medium">
          <ArrowLeft size={16} />
          Return to LegalVault
        </Link>
        
        <div className="flex items-center gap-4 mb-10">
          <Image src="/logo.png" alt="LegalVault Logo" width={40} height={40} className="object-contain" />
          <h1 className="text-4xl font-serif font-bold text-[var(--color-primary-text)] tracking-tight">Legal Disclaimer</h1>
        </div>

        <div className="p-6 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border-color)] mb-10">
          <div className="flex items-start gap-4">
            <div className="mt-1 bg-red-500/10 p-2 rounded-full border border-red-500/20">
              <ShieldAlert size={24} className="text-red-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-2">AI Analysis is Not Legal Advice</h2>
              <p className="text-[var(--color-muted-text)] leading-relaxed text-[15px]">
                LegalVault's AI-generated analysis is provided for informational purposes only and does not constitute legal advice. The AI is designed to assist in reviewing documents but is strictly an automated tool.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-10 text-[var(--color-muted-text)] leading-relaxed text-[15px]">
          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">Accuracy of AI Analysis</h2>
            <p>
              While the intelligence engine aims to identify potential risks and missing clauses, AI analysis can be incomplete or inaccurate. It may miss critical legal issues, misinterpret nuances, or flag false positives. LegalVault does not guarantee that a contract is safe, enforceable, complete, or free of risk based on its analysis. Users must review important contracts carefully themselves.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">No Substitute for a Lawyer</h2>
            <p>
              Using LegalVault does not establish an attorney-client relationship. The insights provided by our AI should never be treated as a substitute for professional legal review. Professional legal advice should always be obtained from a qualified attorney before executing any legally binding document.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">Digital Signatures</h2>
            <p>
              LegalVault provides a mechanism for digital signatures and blockchain-based record keeping. However, utilizing these tools does not automatically make a document legally valid or enforceable in your jurisdiction. We make no guarantees or representations regarding the legal enforceability of contracts executed through this platform.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">Demonstration Purposes Only</h2>
            <p>
              LegalVault is a software demonstration project. It is not an established legal entity or certified service provider. By using this service, you acknowledge that you do so entirely at your own risk. The creators of LegalVault shall not be held liable for any damages, losses, or legal consequences resulting from your reliance on the platform's features, analysis, or outputs.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
