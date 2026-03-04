import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
export function LandingPage() {
  return (
    <motion.div
      className="mx-auto flex max-w-6xl flex-col items-center justify-center gap-10 py-10 sm:py-16 lg:py-20"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: 'easeOut' }}
    >
      <div className="grid w-full items-center gap-10 md:grid-cols-[1.2fr,1fr]">
        {/* LEFT SIDE */}
        <div className="space-y-6 text-center md:text-left">
          <motion.h1
            className="bg-gradient-to-b from-slate-900 via-sky-500 to-indigo-500 dark:from-white dark:via-sky-serenity dark:to-lavender-serenity bg-clip-text text-4xl font-semibold leading-tight text-transparent sm:text-5xl lg:text-6xl"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.6 }}
          >
            Pause. Reflect. <span className="font-extrabold">Breathe.</span>
          </motion.h1>

          <motion.p
            className="max-w-xl text-sm leading-relaxed text-slate-700 dark:text-slate-300 sm:text-base"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            SERENITY is a gentle check-in space for students. No judgement,
            no labels—just soft data, reflective stories, and a tiny penguin
            cheering you on as you notice your emotional weather.
          </motion.p>

          <motion.div
            className="flex flex-wrap items-center justify-center gap-3 md:justify-start"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
          >
            <Link to="/login">
              <Button>Login</Button>
            </Link>
            <Link to="/register">
              <Button variant="secondary">Create account</Button>
            </Link>
          </motion.div>

          <p className="text-[11px] text-slate-500 dark:text-slate-400">
            Not a crisis tool. If you're in immediate danger, please reach
            out to local emergency services or trusted adults.
          </p>
        </div>

        {/* RIGHT SIDE */}
        <motion.div
          className="relative mx-auto flex h-72 w-full max-w-sm items-center justify-center"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.25, duration: 0.7 }}
        >
          {/* Soft background panel */}
          <div className="absolute inset-0 -z-10 rounded-3xl bg-white dark:bg-slate-900 shadow-lg" />

          <motion.div
            className="absolute -top-4 left-6 rounded-3xl bg-white px-3 py-2 text-xs font-medium text-slate-800 shadow-md dark:bg-slate-800 dark:text-slate-200"
            initial={{ y: -12, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            “Today I feel... gently hopeful.”
          </motion.div>

          <motion.div
            className="relative flex h-40 w-40 items-center justify-center rounded-full bg-gradient-to-b from-sky-200 via-white to-peach-200 dark:from-sky-serenity dark:via-white dark:to-peach-serenity shadow-md"
            animate={{ y: [0, -6, 0] }}
            transition={{ repeat: Infinity, duration: 4, ease: 'easeInOut' }}
          >
            <img  
  src="/serenity_logo_white.png"  
  alt="Serenity Logo"  
  className="h-40 w-40 object-contain"  
/>
          </motion.div>

          <motion.div
            className="absolute bottom-4 right-4 rounded-2xl bg-slate-900 text-slate-100 px-3 py-2 text-[11px] shadow-md dark:bg-slate-800 dark:text-slate-200"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            Soft, data-backed reflections about your stress patterns.
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
}