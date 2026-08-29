"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Brain, Wallet, ShieldCheck } from "lucide-react";
import CapabilityVisual from "./CapabilityVisual";

const CAPABILITIES = [
  {
    id: 0,
    title: "Contract Intelligence",
    icon: <Brain size={18} />,
    description: "Automated clause extraction and risk analysis. Identify ambiguous language, highlight hidden liabilities, and surface standard protections missing from your agreement.",
  },
  {
    id: 1,
    title: "Cryptographic Execution",
    icon: <Wallet size={18} />,
    description: "Coordinate signatures between senders and receivers. Execute agreements securely using cryptographic wallet signatures to commit to the exact terms.",
  },
  {
    id: 2,
    title: "Blockchain-Backed Verification",
    icon: <ShieldCheck size={18} />,
    description: "Anchor document hashes to the blockchain. Verify the contract's integrity against its recorded hash to independently prove it hasn't been tampered with.",
  }
];

export default function CapabilitiesSection() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <section id="capabilities" className="w-full py-32 bg-[var(--color-surface)] border-t border-[var(--color-border-color)]">
      <div className="max-w-7xl mx-auto px-6">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            className="text-3xl md:text-5xl font-serif text-[var(--color-primary-text)] tracking-tight mb-6"
          >
            From contract text to verified agreement.
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ delay: 0.1 }}
            className="text-lg text-[var(--color-muted-text)]"
          >
            LegalVault provides the necessary tools to understand, execute, and verify your documents securely.
          </motion.p>
        </div>

        {/* =========================================
            DESKTOP & TABLET: INTERACTIVE TABS
            ========================================= */}
        <div className="hidden md:flex flex-col items-center w-full">
          {/* Tab List */}
          <div 
            className="flex flex-wrap justify-center gap-2 mb-16 p-1.5 rounded-2xl bg-[var(--color-background)] border border-[var(--color-border-color)]"
            role="tablist"
          >
            {CAPABILITIES.map((cap) => {
              const isActive = activeTab === cap.id;
              return (
                <button
                  key={cap.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setActiveTab(cap.id)}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                    isActive 
                      ? "bg-[var(--color-surface)] text-[var(--color-primary-gold)] shadow-sm border border-[var(--color-border-color)]" 
                      : "text-[var(--color-muted-text)] hover:text-[var(--color-primary-text)] hover:bg-[var(--color-surface)]/50 border border-transparent"
                  }`}
                >
                  {cap.icon}
                  {cap.title}
                </button>
              );
            })}
          </div>

          {/* Tab Content Box */}
          <div className="w-full grid grid-cols-2 gap-16 items-center bg-[var(--color-background)] rounded-3xl border border-[var(--color-border-color)] p-12 shadow-xl">
            {/* Left: Text */}
            <div className="flex flex-col gap-6 pr-8">
              <div className="w-12 h-12 rounded-xl bg-[var(--color-primary-gold)]/10 border border-[var(--color-primary-gold)]/20 flex items-center justify-center text-[var(--color-primary-gold)]">
                {CAPABILITIES[activeTab].icon}
              </div>
              <h3 className="text-3xl font-serif text-[var(--color-primary-text)]">
                {CAPABILITIES[activeTab].title}
              </h3>
              <p className="text-lg text-[var(--color-muted-text)] leading-relaxed">
                {CAPABILITIES[activeTab].description}
              </p>
            </div>
            
            {/* Right: Visual Showcase */}
            <div className="w-full flex justify-center">
              <CapabilityVisual activeTab={activeTab} />
            </div>
          </div>
        </div>

        {/* =========================================
            MOBILE: VERTICALLY STACKED
            ========================================= */}
        <div className="flex md:hidden flex-col gap-16">
          {CAPABILITIES.map((cap) => (
            <motion.div 
              key={cap.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              className="flex flex-col gap-8 pb-16 border-b border-[var(--color-border-color)] last:border-0 last:pb-0"
            >
              <div className="flex flex-col gap-4">
                <div className="w-10 h-10 rounded-xl bg-[var(--color-primary-gold)]/10 border border-[var(--color-primary-gold)]/20 flex items-center justify-center text-[var(--color-primary-gold)]">
                  {cap.icon}
                </div>
                <h3 className="text-2xl font-serif text-[var(--color-primary-text)]">
                  {cap.title}
                </h3>
                <p className="text-[var(--color-muted-text)] leading-relaxed">
                  {cap.description}
                </p>
              </div>
              
              <div className="w-full flex justify-center">
                <CapabilityVisual activeTab={cap.id} />
              </div>
            </motion.div>
          ))}
        </div>



      </div>
    </section>
  );
}
