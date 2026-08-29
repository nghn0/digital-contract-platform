"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ShieldAlert, FileWarning, Search, CheckCircle2, Wallet, Link as LinkIcon } from "lucide-react";

interface CapabilityVisualProps {
  activeTab: number;
}

export default function CapabilityVisual({ activeTab }: CapabilityVisualProps) {
  const variants = {
    initial: { opacity: 0, y: 10, filter: "blur(4px)" },
    animate: { opacity: 1, y: 0, filter: "blur(0px)" },
    exit: { opacity: 0, y: -10, filter: "blur(4px)" }
  };

  return (
    <div className="w-full max-w-[400px] aspect-square mx-auto bg-[var(--color-background)] border border-[var(--color-border-color)] rounded-2xl shadow-2xl relative overflow-hidden flex items-center justify-center p-8">
      {/* Background glow */}
      <div className="absolute inset-0 bg-[var(--color-primary-gold)]/5 blur-3xl pointer-events-none" />

      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          variants={variants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="w-full h-full relative z-10 flex items-center justify-center"
        >
          {activeTab === 0 && <IntelligenceVisual />}
          {activeTab === 1 && <ExecutionVisual />}
          {activeTab === 2 && <VerificationVisual />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------
// INTELLIGENCE VISUAL
// ---------------------------------------------
function IntelligenceVisual() {
  return (
    <div className="w-full h-full flex flex-col justify-center gap-6">
      
      {/* Extracted Clause */}
      <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-color)] shadow-sm">
        <div className="flex items-center gap-2 mb-3 pb-3 border-b border-[var(--color-border-color)]">
          <Search size={14} className="text-[var(--color-primary-gold)]" />
          <span className="text-xs uppercase tracking-widest font-bold text-[var(--color-primary-text)]">Extracted Clause</span>
        </div>
        <p className="text-xs text-[var(--color-primary-text)] font-serif italic mb-3">
          &quot;...party shall hold harmless from any and all claims, without limitation to time or scope...&quot;
        </p>
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 }}
          className="p-2 rounded bg-red-500/10 border border-red-500/20 flex items-start gap-2"
        >
          <ShieldAlert size={14} className="text-red-400 mt-0.5 shrink-0" />
          <span className="text-xs text-red-400 font-medium leading-tight">
            Ambiguous liability timeframe detected.
          </span>
        </motion.div>
      </div>

      {/* Missing Protections */}
      <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-color)] shadow-sm">
        <div className="flex items-center gap-2 mb-3 pb-3 border-b border-[var(--color-border-color)]">
          <FileWarning size={14} className="text-orange-400" />
          <span className="text-xs uppercase tracking-widest font-bold text-[var(--color-primary-text)]">Missing Protections</span>
        </div>
        <motion.div 
          initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.6 }}
          className="flex items-center gap-2"
        >
          <CheckCircle2 size={14} className="text-[var(--color-primary-gold)]" />
          <span className="text-xs text-[var(--color-primary-text)] font-medium">Force Majeure clause recommended.</span>
        </motion.div>
      </div>

    </div>
  );
}

// ---------------------------------------------
// EXECUTION VISUAL
// ---------------------------------------------
function ExecutionVisual() {
  return (
    <div className="w-full flex flex-col gap-5 items-center text-center">
      <div className="w-16 h-16 rounded-full bg-[var(--color-primary-gold)]/10 border border-[var(--color-primary-gold)]/20 flex items-center justify-center mb-2">
        <Wallet size={24} className="text-[var(--color-primary-gold)]" />
      </div>
      <div className="text-lg font-serif text-[var(--color-primary-text)] mb-2">Signature Status</div>
      
      <div className="w-full flex flex-col gap-3">
        {/* Sender */}
        <div className="flex flex-col gap-2 p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-primary-gold)]/40 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--color-primary-gold)]/5 to-transparent animate-[pulse_3s_infinite]" />
          <div className="flex justify-between items-center relative z-10">
            <span className="text-sm font-medium text-[var(--color-primary-text)]">Sender</span>
            <motion.div initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 }} className="flex items-center gap-1 text-[var(--color-primary-gold)] text-xs font-bold">
              <CheckCircle2 size={14} /> Signed
            </motion.div>
          </div>
          <div className="text-left text-[10px] text-[var(--color-muted-text)] font-mono">0x74a9...3B1A</div>
        </div>

        {/* Receiver */}
        <div className="flex flex-col gap-2 p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-color)]">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-[var(--color-primary-text)]">Receiver</span>
            <div className="text-xs text-[var(--color-muted-text)] animate-pulse">Awaiting...</div>
          </div>
          <div className="text-left text-[10px] text-[var(--color-muted-text)] font-mono">Pending Connection</div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------
// VERIFICATION VISUAL
// ---------------------------------------------
function VerificationVisual() {
  return (
    <div className="w-full h-full flex flex-col justify-center items-center text-center gap-6">
      
      <motion.div 
        initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2, type: "spring" }}
        className="text-lg font-serif text-[var(--color-primary-text)] flex items-center gap-2 mb-2"
      >
        <CheckCircle2 size={24} className="text-[var(--color-primary-gold)]" />
        Integrity Confirmed
      </motion.div>
      
      <div className="w-full flex flex-col gap-4 text-left">
        
        {/* Document Hash */}
        <div className="flex flex-col gap-1 p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-color)] relative">
          <div className="text-[10px] text-[var(--color-muted-text)] uppercase tracking-wider mb-1">
            Document SHA-256
          </div>
          <div className="text-xs text-[var(--color-primary-text)] font-mono">
            8a2f3c4e...91cd5b
          </div>
        </div>

        {/* Connecting Line */}
        <div className="flex flex-col items-center justify-center -my-2 relative z-10">
          <motion.div 
            initial={{ height: 0 }} animate={{ height: 24 }} transition={{ delay: 0.5 }}
            className="w-[1px] bg-[var(--color-primary-gold)]/50" 
          />
          <motion.div initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.8 }}>
            <LinkIcon size={12} className="text-[var(--color-primary-gold)] my-1 bg-[var(--color-background)] rounded-full p-0.5 box-content border border-[var(--color-primary-gold)]/20" />
          </motion.div>
          <motion.div 
            initial={{ height: 0 }} animate={{ height: 24 }} transition={{ delay: 0.9 }}
            className="w-[1px] bg-[var(--color-primary-gold)]/50" 
          />
        </div>

        {/* Blockchain Record */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.1 }}
          className="flex flex-col gap-1 p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-primary-gold)]/40 shadow-[0_0_15px_rgba(217,173,43,0.1)]"
        >
          <div className="text-[10px] text-[var(--color-muted-text)] uppercase tracking-wider mb-1">
            Blockchain Record
          </div>
          <div className="text-xs text-[var(--color-primary-gold)] font-mono">
            0x73a98b4f...c821
          </div>
        </motion.div>

      </div>
    </div>
  );
}
