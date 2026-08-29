"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

export default function ClosingCTA() {
  return (
    <section className="w-full py-32 md:py-48 bg-[var(--color-background)] border-t border-[var(--color-border-color)] relative overflow-hidden flex flex-col items-center justify-center">
      
      {/* Subtle background glow to differentiate from Capabilities */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1/2 aspect-square rounded-full bg-[var(--color-primary-gold)]/5 blur-[120px] pointer-events-none" />

      <div className="max-w-4xl mx-auto px-6 text-center relative z-10 flex flex-col items-center">
        
        <motion.h2 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-4xl md:text-5xl lg:text-6xl font-serif text-[var(--color-primary-text)] tracking-tight mb-12"
        >
          Ready to analyze a contract?
        </motion.h2>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
        >
          <Link 
            href="/upload"
            className="group inline-flex h-16 items-center justify-center gap-3 rounded-2xl bg-[var(--color-primary-gold)] px-10 text-lg font-bold text-[var(--color-surface)] transition-all hover:bg-[var(--color-bright-gold)] shadow-xl shadow-[var(--color-primary-gold)]/10"
          >
            Analyze a Contract
            <ArrowRight size={24} className="group-hover:translate-x-1 transition-transform" />
          </Link>
        </motion.div>

      </div>
    </section>
  );
}
