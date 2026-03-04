import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

const FLAKES = 40;

type Flake = {
  id: number;
  left: string;
  delay: number;
  duration: number;
  size: number;
};

export function Snowfall() {
  const [flakes, setFlakes] = useState<Flake[]>([]);

  useEffect(() => {
    const next: Flake[] = Array.from({ length: FLAKES }).map((_, idx) => ({
      id: idx,
      left: `${Math.random() * 100}%`,
      delay: Math.random() * 10,
      duration: 12 + Math.random() * 10,
      size: 2 + Math.random() * 3,
    }));
    setFlakes(next);
  }, []);

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {flakes.map((flake) => (
        <motion.div
          key={flake.id}
          className="absolute rounded-full bg-white/80 shadow"
          style={{ left: flake.left, width: flake.size, height: flake.size }}
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: '110%', opacity: [0, 1, 1, 0] }}
          transition={{
            delay: flake.delay,
            duration: flake.duration,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      ))}
    </div>
  );
}

