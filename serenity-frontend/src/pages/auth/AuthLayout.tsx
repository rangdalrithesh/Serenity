import type { PropsWithChildren } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

export function AuthLayout({
  children,
  title,
  subtitle,
}: PropsWithChildren<{ title: string; subtitle?: string }>) {
  return (
    <div className="mx-auto flex w-full max-w-6xl items-center justify-center py-10 sm:py-16">
      <motion.div
        className="grid w-full gap-10 rounded-3xl bg-white/5 p-5 shadow-soft backdrop-blur-xl md:grid-cols-[1.1fr,1fr] md:p-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="space-y-4">
          <h1 className="text-2xl font-semibold text-white sm:text-3xl">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-slate-100/80 sm:text-base">
              {subtitle}
            </p>
          )}
          <p className="text-xs text-slate-200/80">
            SERENITY is not a diagnostic tool. It gently visualizes your stress
            awareness over time and supports reflection with short penguin
            stories.
          </p>
          <div className="mt-4 hidden rounded-2xl bg-gradient-to-br from-sky-serenity/40 via-lavender-serenity/40 to-peach-serenity/40 p-4 text-xs text-slate-900 shadow-soft sm:block">
            <p className="font-semibold">Therapists / staff</p>
            <p className="mt-1 opacity-90">
              Use your institution-provided credentials to access the therapist
              dashboard for aggregated, de-identified insights.
            </p>
          </div>
        </div>

        <div className="rounded-2xl bg-slate-950/80 p-5 shadow-soft">
          {children}
          <p className="mt-4 text-center text-[11px] text-slate-400">
            By continuing, you agree that SERENITY supplements but does not
            replace professional support.
          </p>
          <p className="mt-2 text-center text-[11px] text-slate-400">
            Return to{' '}
            <Link to="/" className="font-medium text-sky-serenity">
              home
            </Link>
            .
          </p>
        </div>
      </motion.div>
    </div>
  );
}

