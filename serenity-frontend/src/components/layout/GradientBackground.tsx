import type { PropsWithChildren } from 'react';
import { motion } from 'framer-motion';
import { useAppStore } from '../../store/useAppStore';

export function GradientBackground({ children }: PropsWithChildren) {
  const theme = useAppStore((s) => s.theme);
  const isDark = theme === 'dark';

  return (
    <div
      className={`relative min-h-screen overflow-hidden transition-colors duration-300 ${
        isDark
          ? 'bg-slate-950 text-slate-50'
          : 'bg-gradient-to-b from-sky-100 via-white to-peach-50/90 text-slate-900'
      }`}
    >
      {/* Pastel gradient – strong in light mode, very subtle in dark */}
      <motion.div
        aria-hidden
        className={`pointer-events-none fixed inset-0 -z-10 ${isDark ? 'opacity-20' : 'opacity-60'}`}
        style={{
          background: 'radial-gradient(circle at top left, #7CC6FE 0, transparent 55%), radial-gradient(circle at top right, #C3B6FF 0, transparent 55%), radial-gradient(circle at bottom, #FFB38A 0, transparent 55%)',
          backgroundSize: '200% 200%',
        }}
        animate={{ backgroundPosition: ['0% 0%', '100% 100%'] }}
        transition={{ repeat: Infinity, duration: 40, ease: 'linear' }}
      />
      {/* Dark mode only: solid dark layer so background is clearly dark */}
      {isDark && (
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 -z-10 bg-slate-950/95"
        />
      )}
      {/* Light: soft white radial; Dark: barely visible */}
      <div
        aria-hidden
        className={`pointer-events-none fixed inset-0 -z-10 ${
          isDark
            ? 'bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.02),_transparent_60%)]'
            : 'bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.4),_transparent_50%)]'
        }`}
      />
      {children}
    </div>
  );
}

