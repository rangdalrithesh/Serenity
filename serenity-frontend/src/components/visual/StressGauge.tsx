import { motion, useSpring, useTransform } from 'framer-motion';
import { useEffect } from 'react';

type Props = {
  value: number;
};

export function StressGauge({ value }: Props) {
  const clamped = Math.max(0, Math.min(1, value));
  const spring = useSpring(0, { stiffness: 80, damping: 16 });

  useEffect(() => {
    spring.set(clamped);
  }, [clamped, spring]);

  const rotation = useTransform(spring, [0, 1], [-90, 90]);
  const background = useTransform(spring, [0, 0.3, 0.6, 1], [
    '#22c55e',
    '#22c55e',
    '#eab308',
    '#f97316',
  ]);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-32 w-64 overflow-hidden rounded-full bg-slate-900/40">
        <div className="absolute inset-x-6 bottom-3 h-3 rounded-full bg-slate-800/70" />
        <motion.div
          className="absolute bottom-3 left-1/2 h-20 w-1 origin-bottom rounded-full"
          style={{ rotate: rotation, background }}
        />
        <div className="absolute inset-x-8 top-6 flex justify-between text-[10px] font-medium text-slate-300/80">
          <span>Calm</span>
          <span>Elevated</span>
          <span>High</span>
        </div>
      </div>
      <motion.div
        className="text-sm font-semibold text-white"
        style={{ color: background }}
      >
        {Math.round(clamped * 100)} / 100
      </motion.div>
    </div>
  );
}

