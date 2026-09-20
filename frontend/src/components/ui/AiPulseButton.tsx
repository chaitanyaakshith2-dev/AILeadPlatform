"use client";

import { motion } from "framer-motion";
import { BrainCircuit, Sparkles } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type AiPulseButtonProps = Pick<ButtonHTMLAttributes<HTMLButtonElement>, "onClick" | "disabled" | "className" | "aria-label" | "name" | "value" | "id"> & { loading?: boolean; children: ReactNode };

export default function AiPulseButton({ children, loading = false, className = "", ...props }: AiPulseButtonProps) {
  return <motion.button type="button" className={`ai-pulse-button ${className}`} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} disabled={loading || props.disabled} {...props}><span className="ai-pulse-orb" aria-hidden="true"><Sparkles size={13} /></span>{loading ? "Working..." : children}<BrainCircuit size={15} aria-hidden="true" /></motion.button>;
}