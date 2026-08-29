"use client";

import { motion } from "framer-motion";

interface WorkflowStepProps {
  step: number;
  title: string;
  description: string;
  onInView: (step: number) => void;
}

export default function WorkflowStep({ step, title, description, onInView }: WorkflowStepProps) {
  return (
    <motion.div 
      className="min-h-[60vh] flex flex-col justify-center py-20 w-full max-w-lg mx-auto md:mx-0 md:max-w-none text-center md:text-left items-center md:items-start"
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ margin: "-20% 0px -20% 0px", once: false }}
      onViewportEnter={() => onInView(step)}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div className="text-[var(--color-primary-gold)] font-mono text-sm mb-4 tracking-widest">
        0{step}
      </div>
      <h3 className="text-3xl md:text-4xl font-serif font-medium mb-6 text-[var(--color-primary-text)]">
        {title}
      </h3>
      <p className="text-lg md:text-xl text-[var(--color-muted-text)] leading-relaxed max-w-lg">
        {description}
      </p>
    </motion.div>
  );
}
