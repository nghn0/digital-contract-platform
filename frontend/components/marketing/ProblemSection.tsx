import { Clock, AlertTriangle, Layers } from "lucide-react";

export default function ProblemSection() {
  return (
    <section id="problem" className="w-full py-32 bg-[var(--color-background)] border-t border-[var(--color-border-color)]">
      <div className="max-w-7xl mx-auto px-6">
        
        {/* Header */}
        <div className="max-w-3xl mb-20">
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-serif font-medium leading-tight mb-6 text-[var(--color-primary-text)]">
            A contract can be signed in seconds. <br className="hidden md:block" />
            <span className="text-[var(--color-muted-text)]">Understanding it shouldn't take hours.</span>
          </h2>
          <p className="text-lg text-[var(--color-muted-text)] leading-relaxed">
            Traditional contract execution is broken. You are forced to choose between expensive legal review or accepting unknown risks, all while jumping between disparate tools for analysis, signing, and storage.
          </p>
        </div>

        {/* 3-Column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
          
          {/* Problem 1 */}
          <div className="flex flex-col gap-4">
            <div className="w-12 h-12 flex items-center justify-center rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-color)]">
              <Clock size={20} className="text-[var(--color-primary-gold)]" />
            </div>
            <h3 className="text-xl font-medium text-[var(--color-primary-text)] font-serif mt-2">
              <span className="text-[var(--color-muted-text)] font-mono text-sm mr-2 block mb-1">01</span>
              Manual Review
            </h3>
            <p className="text-sm text-[var(--color-muted-text)] leading-relaxed">
              Hours spent parsing dense legal jargon just to understand basic obligations.
            </p>
          </div>

          {/* Problem 2 */}
          <div className="flex flex-col gap-4">
            <div className="w-12 h-12 flex items-center justify-center rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-color)]">
              <AlertTriangle size={20} className="text-[var(--color-primary-gold)]" />
            </div>
            <h3 className="text-xl font-medium text-[var(--color-primary-text)] font-serif mt-2">
              <span className="text-[var(--color-muted-text)] font-mono text-sm mr-2 block mb-1">02</span>
              Unclear Risk
            </h3>
            <p className="text-sm text-[var(--color-muted-text)] leading-relaxed">
              Hidden clauses and missing protections that expose you to unnecessary liability.
            </p>
          </div>

          {/* Problem 3 */}
          <div className="flex flex-col gap-4">
            <div className="w-12 h-12 flex items-center justify-center rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-color)]">
              <Layers size={20} className="text-[var(--color-primary-gold)]" />
            </div>
            <h3 className="text-xl font-medium text-[var(--color-primary-text)] font-serif mt-2">
              <span className="text-[var(--color-muted-text)] font-mono text-sm mr-2 block mb-1">03</span>
              Fragmented Workflow
            </h3>
            <p className="text-sm text-[var(--color-muted-text)] leading-relaxed">
              Juggling emails, PDFs, e-signature platforms, and static storage drives.
            </p>
          </div>

        </div>
      </div>
    </section>
  );
}
