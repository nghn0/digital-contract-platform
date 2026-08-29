import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import Image from "next/image";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[var(--color-background)] font-sans selection:bg-[var(--color-primary-gold)] selection:text-[var(--color-surface)]">
      <div className="max-w-3xl mx-auto px-6 py-20">
        <Link href="/" className="inline-flex items-center gap-2 mb-12 text-[var(--color-muted-text)] hover:text-[var(--color-primary-text)] transition-colors text-sm font-medium">
          <ArrowLeft size={16} />
          Return to LegalVault
        </Link>
        
        <div className="flex items-center gap-4 mb-10">
          <Image src="/logo.png" alt="LegalVault Logo" width={40} height={40} className="object-contain" />
          <h1 className="text-4xl font-serif font-bold text-[var(--color-primary-text)] tracking-tight">Privacy Policy</h1>
        </div>

        <div className="space-y-10 text-[var(--color-muted-text)] leading-relaxed text-[15px]">
          
          <section>
            <p className="mb-4">
              LegalVault is a software project designed to demonstrate digital contract analysis, electronic signatures, and cryptographic verification. This Privacy Policy describes how information is collected, used, and protected when you interact with the service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">1. Information We Collect</h2>
            <p className="mb-3">When you use LegalVault, we collect the following types of information:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong>Account Information:</strong> We collect your email address and authentication credentials to secure your account.</li>
              <li><strong>Contract Documents:</strong> Documents (e.g., PDF contracts) you upload for analysis, review, or signing.</li>
              <li><strong>Signatures and Verification Data:</strong> Electronic signatures, transaction hashes, timestamps, and related metadata generated when you execute a document.</li>
              <li><strong>Technical and Session Information:</strong> Basic usage data and securely encrypted session tokens necessary for the operation and security of the platform.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">2. How Information Is Used</h2>
            <p className="mb-3">Your information is used exclusively to operate the LegalVault service:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong>Authentication:</strong> To verify your identity and protect your account from unauthorized access.</li>
              <li><strong>Contract Processing:</strong> To extract clauses, identify potential risks, and generate AI-assisted summaries of your uploaded documents.</li>
              <li><strong>Verification:</strong> To execute electronic signatures and log cryptographic hashes of finalized agreements on a blockchain to ensure document integrity.</li>
            </ul>
            <p className="mt-3">We do not sell your personal information or use your uploaded documents for advertising purposes.</p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">3. Authentication Cookies</h2>
            <p>
              LegalVault uses strictly necessary authentication and session cookies. These cookies are essential to maintain your signed-in session, securely authenticate requests, and protect access to your account across pages. Because these cookies are strictly necessary for the core functionality and security of the application, we do not require a separate cookie-consent popup. LegalVault does not currently use optional tracking, advertising, or behavioral analytics cookies.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">4. Third-Party Infrastructure</h2>
            <p className="mb-3">We utilize trusted third-party service providers to support the application's infrastructure:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong>Authentication & Database:</strong> We use Supabase to securely manage authentication, user identities, and database storage.</li>
              <li><strong>AI-Assisted Analysis:</strong> Uploaded contract text is processed by third-party Large Language Models (LLMs) via API to generate the intelligence reports.</li>
              <li><strong>Blockchain Services:</strong> Cryptographic hashes of finalized contracts are submitted to an external blockchain network for immutable verification.</li>
            </ul>
            <p className="mt-3">These providers only process your data to the extent necessary to perform these technical functions.</p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">5. Data Storage and Retention</h2>
            <p>
              Documents and user data are stored securely using industry-standard infrastructure. Raw contract documents remain in our secure database and are not published to the public blockchain. Only cryptographic hashes (which cannot be reverse-engineered into the original document) are recorded on the blockchain. Because LegalVault is currently a demonstration project, data retention periods are not guaranteed, and data may be cleared periodically as the project evolves.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">6. Security</h2>
            <p>
              We implement reasonable security measures, including Row Level Security (RLS) and server-side route protection, to prevent unauthorized access to your account and documents. However, no internet-based service can be 100% secure. You are responsible for keeping your login credentials confidential.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-[var(--color-primary-text)] mb-3">7. Contact</h2>
            <p>
              If you have any questions regarding this Privacy Policy or how LegalVault processes your data, please contact the LegalVault development team.
            </p>
          </section>

        </div>
      </div>
    </div>
  );
}
