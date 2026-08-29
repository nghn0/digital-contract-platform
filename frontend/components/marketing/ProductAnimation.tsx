"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Brain, ShieldAlert, CheckCircle2, Wallet, Link as LinkIcon } from "lucide-react";
import Image from "next/image";

// NOTE: All data shown here is strictly for illustrative marketing purposes.
// No real API calls, blockchain transactions, or AI analysis is performed.

const STATES = 6;
const STATE_DURATIONS = [2000, 2000, 2000, 2500, 2500, 3000];

export default function ProductAnimation() {
  const [currentState, setCurrentState] = useState(0);

  useEffect(() => {
    let timerId: NodeJS.Timeout;

    const nextState = () => {
      setCurrentState((prev) => (prev + 1) % STATES);
    };

    timerId = setTimeout(nextState, STATE_DURATIONS[currentState]);

    return () => clearTimeout(timerId);
  }, [currentState]);

  const variants = {
    initial: { opacity: 0, y: 10, scale: 0.98 },
    animate: { opacity: 1, y: 0, scale: 1 },
    exit: { opacity: 0, y: -10, scale: 0.98 }
  };

  return (
    <div className="relative w-full h-[320px] sm:h-[400px] bg-[var(--color-surface)] border border-[var(--color-border-color)] rounded-2xl overflow-hidden shadow-2xl flex flex-col">
      {/* Header */}
      <div className="h-12 w-full border-b border-[var(--color-border-color)] bg-[var(--color-background)] flex items-center px-4 gap-3">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
          <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Image src="/logo.png" alt="LegalVault" width={16} height={16} className="opacity-50" />
          <span className="text-xs text-[var(--color-muted-text)] font-mono">legalvault_engine</span>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 relative flex items-center justify-center p-6">
        <AnimatePresence mode="wait">

          {/* STATE 0: UPLOAD */}
          {currentState === 0 && (
            <motion.div key="state-0" variants={variants} initial="initial" animate="animate" exit="exit" className="flex flex-col items-center gap-4 w-full max-w-[240px]">
              <FileText size={48} className="text-[var(--color-muted-text)]" />
              <div className="text-sm font-medium text-[var(--color-primary-text)]">Employment_Agreement.pdf</div>
              <div className="w-full h-2 bg-[var(--color-background)] rounded-full overflow-hidden border border-[var(--color-border-color)]">
                <motion.div
                  className="h-full bg-[var(--color-primary-gold)]"
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 1.8, ease: "easeInOut" }}
                />
              </div>
              <div className="text-xs text-[var(--color-muted-text)] font-mono uppercase tracking-wider">Uploading...</div>
            </motion.div>
          )}

          {/* STATE 1: AI ANALYSIS */}
          {currentState === 1 && (
            <motion.div key="state-1" variants={variants} initial="initial" animate="animate" exit="exit" className="flex flex-col items-center gap-6 w-full max-w-[260px]">
              <Brain size={48} className="text-[var(--color-primary-gold)] animate-pulse" />
              <div className="text-sm font-medium text-[var(--color-primary-text)] text-center">AI Analysis Active</div>
              <div className="flex flex-col gap-2 w-full">
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="text-xs text-[var(--color-muted-text)] font-mono flex items-center justify-between">
                  <span>Extracting clauses...</span><span className="text-[var(--color-primary-gold)]">100%</span>
                </motion.div>
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} className="text-xs text-[var(--color-muted-text)] font-mono flex items-center justify-between">
                  <span>Identifying obligations...</span><span className="text-[var(--color-primary-gold)]">100%</span>
                </motion.div>
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.3 }} className="text-xs text-[var(--color-muted-text)] font-mono flex items-center justify-between">
                  <span>Risk modeling...</span><span className="text-[var(--color-primary-gold)]">100%</span>
                </motion.div>
              </div>
            </motion.div>
          )}

          {/* STATE 2: ANALYSIS COMPLETE */}
          {currentState === 2 && (
            <motion.div key="state-2" variants={variants} initial="initial" animate="animate" exit="exit" className="flex flex-col w-full max-w-[260px] gap-4">
              <div className="flex items-end justify-between border-b border-[var(--color-border-color)] pb-3">
                <div className="text-xs text-[var(--color-muted-text)] uppercase tracking-wider">Risk Score</div>
                <div className="text-2xl font-serif text-[var(--color-bright-gold)]">72<span className="text-sm text-[var(--color-muted-text)]">/100</span></div>
              </div>
              <div className="flex flex-col gap-3 mt-2">
                <div className="flex items-center gap-3 text-sm text-[var(--color-primary-text)]">
                  <ShieldAlert size={16} className="text-red-400" />
                  <span>3 potential risks</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-[var(--color-primary-text)]">
                  <ShieldAlert size={16} className="text-yellow-400" />
                  <span>2 missing clauses</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-[var(--color-primary-text)]">
                  <CheckCircle2 size={16} className="text-[var(--color-primary-gold)]" />
                  <span>14 clauses identified</span>
                </div>
              </div>
            </motion.div>
          )}

          {/* STATE 3: CLAUSE REVIEW */}
          {currentState === 3 && (
            <motion.div key="state-3" variants={variants} initial="initial" animate="animate" exit="exit" className="flex flex-col w-full max-w-[280px]">
              <div className="text-xs text-[var(--color-muted-text)] uppercase tracking-wider mb-3">Termination Clause</div>
              <div className="p-4 rounded-lg bg-[var(--color-background)] border border-red-500/20 text-sm text-[var(--color-primary-text)] font-serif leading-relaxed italic relative">
                <div className="absolute -top-2 -right-2 bg-red-500/10 border border-red-500/30 text-red-400 text-[10px] uppercase px-2 py-0.5 rounded shadow-sm backdrop-blur-sm font-mono">⚠ Ambiguous</div>
                &quot;...either party may terminate the agreement at any time without prior written notice...&quot;
              </div>
              <div className="mt-4 flex gap-2">
                <div className="h-8 flex-1 rounded bg-[var(--color-primary-gold)]/10 border border-[var(--color-primary-gold)]/30 flex items-center justify-center text-xs text-[var(--color-primary-gold)]">Flag</div>
                <div className="h-8 flex-1 rounded bg-[var(--color-background)] border border-[var(--color-border-color)] flex items-center justify-center text-xs text-[var(--color-primary-text)]">Accept</div>
              </div>
            </motion.div>
          )}

          {/* STATE 4: SIGNING */}
          {currentState === 4 && (
            <motion.div key="state-4" variants={variants} initial="initial" animate="animate" exit="exit" className="flex flex-col w-full max-w-[260px] items-center text-center gap-6">
              <div className="text-sm font-medium text-[var(--color-primary-text)]">Awaiting Signatures</div>

              <div className="w-full flex flex-col gap-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-background)] border border-[var(--color-primary-gold)]/30">
                  <span className="text-sm">You</span>
                  <motion.div initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.5 }} className="flex items-center gap-1 text-[var(--color-primary-gold)] text-xs">
                    <CheckCircle2 size={14} /> Signed
                  </motion.div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-background)] border border-[var(--color-border-color)]">
                  <span className="text-sm">Counterparty</span>
                  <motion.div initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 1.5 }} className="flex items-center gap-1 text-[var(--color-primary-gold)] text-xs">
                    <CheckCircle2 size={14} /> Signed
                  </motion.div>
                </div>
              </div>

              <motion.div
                initial={{ opacity: 0.5 }}
                animate={{ opacity: 1, textShadow: "0 0 10px rgba(217,173,43,0.5)" }}
                transition={{ delay: 2 }}
                className="flex items-center gap-2 text-xs text-[var(--color-primary-gold)] font-mono"
              >
                <Wallet size={14} /> Signature Executed
              </motion.div>
            </motion.div>
          )}

          {/* STATE 5: VERIFICATION */}
          {currentState === 5 && (
            <motion.div key="state-5" variants={variants} initial="initial" animate="animate" exit="exit" className="flex flex-col items-center text-center w-full max-w-[280px] gap-5">
              <div className="w-12 h-12 rounded-full bg-[var(--color-primary-gold)]/10 flex items-center justify-center">
                <CheckCircle2 size={24} className="text-[var(--color-primary-gold)]" />
              </div>
              <div className="text-lg font-serif text-[var(--color-primary-text)]">Contract Verified</div>

              <div className="w-full p-3 rounded bg-[var(--color-background)] border border-[var(--color-border-color)] flex flex-col gap-2 text-left">
                <div className="text-[10px] text-[var(--color-muted-text)] uppercase tracking-wider flex justify-between">
                  <span>SHA-256</span>
                  <LinkIcon size={10} />
                </div>
                <div className="text-xs text-[var(--color-primary-text)] font-mono truncate">
                  8a2f3c4e...91cd5b
                </div>
              </div>

              <div className="w-full p-3 rounded bg-[var(--color-background)] border border-[var(--color-border-color)] flex flex-col gap-2 text-left">
                <div className="text-[10px] text-[var(--color-muted-text)] uppercase tracking-wider flex justify-between">
                  <span>Blockchain Record</span>
                  <LinkIcon size={10} />
                </div>
                <div className="text-xs text-[var(--color-primary-text)] font-mono truncate text-[var(--color-primary-gold)]">
                  0x73a98b4f...c821
                </div>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </div>
  );
}
