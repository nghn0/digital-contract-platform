"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Brain, ShieldAlert, CheckCircle2, Wallet, Link as LinkIcon, Download } from "lucide-react";
import WorkflowStep from "./WorkflowStep";

export default function WorkflowSection() {
  const [activeStep, setActiveStep] = useState(1);

  // Transition variants for the visual pane
  const visualVariants = {
    initial: { opacity: 0, scale: 0.95, filter: "blur(4px)" },
    animate: { opacity: 1, scale: 1, filter: "blur(0px)" },
    exit: { opacity: 0, scale: 0.95, filter: "blur(4px)" }
  };

  return (
    <section id="how-it-works" className="w-full bg-[var(--color-surface)] border-t border-[var(--color-border-color)]">
      
      {/* Solution Transition Header */}
      <div className="w-full border-b border-[var(--color-border-color)] bg-[var(--color-background)] py-20 flex flex-col items-center justify-center">
        <h2 className="text-4xl md:text-5xl lg:text-6xl font-serif text-[var(--color-primary-text)] tracking-tight">
          One workflow.
        </h2>
        <div className="w-[1px] h-24 bg-gradient-to-b from-transparent via-[var(--color-primary-gold)] to-transparent mt-12 opacity-50" />
      </div>

      {/* Workflow Scrolling Container */}
      <div className="max-w-7xl mx-auto px-6 relative">
        <div className="flex flex-col md:flex-row relative">
          
          {/* Left Side: Scrolling Text Steps */}
          <div className="w-full md:w-1/2 md:pr-16 relative z-10">
            <WorkflowStep 
              step={1}
              title="Secure Document Ingestion"
              description="Upload your contract in seconds. LegalVault prepares the document for analysis."
              onInView={setActiveStep}
            />
            
            {/* Mobile Visual (Visible only on mobile) */}
            <div className="md:hidden w-full h-[300px] mb-20 flex items-center justify-center">
              <VisualContent activeStep={1} />
            </div>

            <WorkflowStep 
              step={2}
              title="AI-Powered Extraction & Risk Detection"
              description="Our intelligence engine breaks down the contract, extracting key clauses, surfacing hidden risks, and identifying missing standard protections."
              onInView={setActiveStep}
            />

            {/* Mobile Visual */}
            <div className="md:hidden w-full h-[300px] mb-20 flex items-center justify-center">
              <VisualContent activeStep={2} />
            </div>

            <WorkflowStep 
              step={3}
              title="Cryptographic Execution"
              description="Execute the agreement using secure wallet-based signatures. Both sender and receiver cryptographically commit to the exact terms."
              onInView={setActiveStep}
            />

            {/* Mobile Visual */}
            <div className="md:hidden w-full h-[300px] mb-20 flex items-center justify-center">
              <VisualContent activeStep={3} />
            </div>

            <WorkflowStep 
              step={4}
              title="Cryptographic Verification"
              description="The finalized contract is hashed and recorded on the blockchain, allowing its integrity to be checked against the recorded hash."
              onInView={setActiveStep}
            />

            {/* Mobile Visual */}
            <div className="md:hidden w-full h-[300px] mb-20 flex items-center justify-center">
              <VisualContent activeStep={4} />
            </div>
            
            {/* Bottom Spacing */}
            <div className="h-[20vh] hidden md:block" />
          </div>

          {/* Right Side: Sticky Visual (Desktop Only) */}
          <div className="hidden md:flex w-1/2 sticky top-0 h-screen items-center justify-center p-8">
            <div className="w-full max-w-[400px] aspect-square rounded-2xl bg-[var(--color-background)] border border-[var(--color-border-color)] shadow-2xl relative overflow-hidden flex items-center justify-center">
              
              {/* Subtle grid background */}
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz48L3N2Zz4=')] opacity-50" />
              
              <AnimatePresence mode="wait">
                <motion.div 
                  key={activeStep}
                  variants={visualVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={{ duration: 0.4, ease: "easeOut" }}
                  className="w-full h-full flex items-center justify-center p-8 relative z-10"
                >
                  <VisualContent activeStep={activeStep} />
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}

// Sub-component for rendering the specific step visuals
function VisualContent({ activeStep }: { activeStep: number }) {
  if (activeStep === 1) {
    return (
      <div className="flex flex-col items-center justify-center w-full max-w-[240px] h-full gap-6">
        <div className="w-24 h-24 rounded-full bg-[var(--color-surface)] border border-[var(--color-border-color)] flex items-center justify-center">
          <Download size={32} className="text-[var(--color-muted-text)]" />
        </div>
        <div className="w-full p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-primary-gold)]/30 flex items-center gap-4">
          <FileText size={24} className="text-[var(--color-primary-gold)]" />
          <div className="flex flex-col">
            <span className="text-sm text-[var(--color-primary-text)] font-medium">Employment_Agreement.pdf</span>
            <span className="text-xs text-[var(--color-muted-text)] font-mono">1.2 MB</span>
          </div>
        </div>
      </div>
    );
  }

  if (activeStep === 2) {
    return (
      <div className="flex flex-col w-full max-w-[260px] h-full justify-center gap-5">
        <div className="flex items-end justify-between border-b border-[var(--color-border-color)] pb-3">
          <div className="flex items-center gap-2 text-[var(--color-primary-gold)]">
            <Brain size={18} />
            <span className="text-xs uppercase tracking-wider font-bold">Analysis</span>
          </div>
          <div className="text-xl font-serif text-[var(--color-primary-text)]">72<span className="text-sm text-[var(--color-muted-text)]">/100</span></div>
        </div>
        <div className="flex flex-col gap-3 mt-2">
          <div className="p-3 rounded-lg bg-[var(--color-surface)] border border-red-500/20 text-xs text-[var(--color-primary-text)]">
            <div className="flex items-center gap-2 mb-1 text-red-400 font-medium">
              <ShieldAlert size={14} /> High Risk
            </div>
            Uncapped liability clause detected in Section 4.
          </div>
          <div className="p-3 rounded-lg bg-[var(--color-surface)] border border-yellow-500/20 text-xs text-[var(--color-primary-text)]">
            <div className="flex items-center gap-2 mb-1 text-yellow-400 font-medium">
              <ShieldAlert size={14} /> Missing Term
            </div>
            Standard non-compete duration not specified.
          </div>
        </div>
      </div>
    );
  }

  if (activeStep === 3) {
    return (
      <div className="flex flex-col w-full max-w-[260px] h-full justify-center items-center text-center gap-6">
        <div className="w-16 h-16 rounded-full bg-[var(--color-primary-gold)]/10 flex items-center justify-center">
          <Wallet size={24} className="text-[var(--color-primary-gold)]" />
        </div>
        
        <div className="w-full flex flex-col gap-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-surface)] border border-[var(--color-primary-gold)]/30 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--color-primary-gold)]/5 to-transparent animate-[pulse_3s_infinite]" />
            <span className="text-sm text-[var(--color-primary-text)] relative z-10">Sender</span>
            <div className="flex items-center gap-1 text-[var(--color-primary-gold)] text-xs relative z-10">
              <CheckCircle2 size={14} /> Signed
            </div>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border-color)]">
            <span className="text-sm text-[var(--color-primary-text)]">Receiver</span>
            <div className="flex items-center gap-1 text-[var(--color-muted-text)] text-xs">
              Awaiting...
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (activeStep === 4) {
    return (
      <div className="flex flex-col w-full max-w-[260px] h-full justify-center items-center text-center gap-5">
        <div className="text-lg font-serif text-[var(--color-primary-text)] flex items-center gap-2">
          <CheckCircle2 size={20} className="text-[var(--color-primary-gold)]" />
          Integrity Confirmed
        </div>
        
        <div className="w-full p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-color)] flex flex-col gap-4 text-left">
          
          <div className="flex flex-col gap-1">
            <div className="text-[10px] text-[var(--color-muted-text)] uppercase tracking-wider flex justify-between">
              <span>Document Hash</span>
            </div>
            <div className="text-xs text-[var(--color-primary-text)] font-mono truncate p-2 rounded bg-[var(--color-background)] border border-[var(--color-border-color)]">
              8a2f3c4e...91cd5b
            </div>
          </div>

          <div className="flex flex-col items-center justify-center py-1">
            <div className="w-[1px] h-4 bg-[var(--color-primary-gold)]/50" />
            <LinkIcon size={12} className="text-[var(--color-primary-gold)] my-1" />
            <div className="w-[1px] h-4 bg-[var(--color-primary-gold)]/50" />
          </div>

          <div className="flex flex-col gap-1">
            <div className="text-[10px] text-[var(--color-muted-text)] uppercase tracking-wider flex justify-between">
              <span>Blockchain Record</span>
            </div>
            <div className="text-xs text-[var(--color-primary-gold)] font-mono truncate p-2 rounded bg-[var(--color-background)] border border-[var(--color-primary-gold)]/30">
              0x73a98b4f...c821
            </div>
          </div>

        </div>
      </div>
    );
  }

  return null;
}
