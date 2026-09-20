"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import type { CSSProperties, PointerEvent, ReactNode } from "react";

type GlassCardProps = { children: ReactNode; className?: string; interactive?: boolean };

export default function GlassCard({ children, className = "", interactive = true }: GlassCardProps) {
  const rotateX = useSpring(useMotionValue(0), { stiffness: 260, damping: 24 });
  const rotateY = useSpring(useMotionValue(0), { stiffness: 260, damping: 24 });
  const shadow = useTransform([rotateX, rotateY], ([x, y]) => `${Number(y) * -1}px ${Number(x) + 18}px 50px rgba(0, 0, 0, 0.28)`);

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    if (!interactive) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width;
    const y = (event.clientY - bounds.top) / bounds.height;
    rotateY.set((x - 0.5) * 8);
    rotateX.set((0.5 - y) * 8);
  }

  return <motion.div className={`glass-card ${className}`} style={{ rotateX, rotateY, boxShadow: shadow } as unknown as CSSProperties} onPointerMove={handlePointerMove} onPointerLeave={() => { rotateX.set(0); rotateY.set(0); }}>{children}</motion.div>;
}