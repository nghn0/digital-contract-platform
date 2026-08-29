"use client";

import ProductAnimation from "./ProductAnimation";
import { motion } from "framer-motion";

export default function HeroVisual() {
  return (
    <div className="relative w-full aspect-square md:aspect-[4/3] flex items-center justify-center pointer-events-none select-none">
      
      {/* Ambient Gold Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] rounded-full bg-[var(--color-primary-gold)]/10 blur-[80px]" />

      {/* 2.5D Perspective Wrapper */}
      <div className="relative w-full max-w-[340px] z-10" style={{ perspective: "1000px" }}>
        
        {/* Verification Rings (Background) */}
        <div className="absolute inset-0 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[140%] aspect-square border border-[var(--color-primary-gold)]/5 rounded-full animate-[spin_30s_linear_infinite]" />
        <div className="absolute inset-0 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] aspect-square border border-[var(--color-primary-gold)]/10 rounded-full animate-[spin_20s_linear_infinite_reverse]" border-dashed="true" />
        
        {/* Tilted Container */}
        <div 
          className="relative w-full h-full transform-gpu transition-transform duration-700 ease-out"
          style={{ transform: "rotateX(6deg) rotateY(-8deg)" }}
        >
          {/* Main Animation Component */}
          <ProductAnimation />
          
          {/* Floating decorative elements (Hashes/Particles) */}
          <motion.div 
            animate={{ y: [0, -10, 0], opacity: [0.8, 1, 0.8] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -top-4 -right-4 w-12 h-12 border border-[var(--color-primary-gold)]/20 bg-[var(--color-background)]/50 backdrop-blur-sm rounded flex items-center justify-center"
          >
            <span className="text-[8px] font-mono text-[var(--color-primary-gold)]">0x8F</span>
          </motion.div>
          
          <motion.div 
            animate={{ y: [0, -10, 0], opacity: [0.8, 1, 0.8] }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
            className="absolute -bottom-6 -left-6 w-16 h-8 border border-[var(--color-border-color)] bg-[var(--color-background)]/50 backdrop-blur-sm rounded flex items-center justify-center"
          >
            <span className="text-[8px] font-mono text-[var(--color-muted-text)]">SECURE</span>
          </motion.div>
        </div>

      </div>
    </div>
  );
}
