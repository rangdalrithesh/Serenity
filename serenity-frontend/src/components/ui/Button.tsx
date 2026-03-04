import type { ButtonHTMLAttributes, PropsWithChildren } from 'react';
import { motion } from 'framer-motion';
import { twMerge } from 'tailwind-merge';

type Props = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: 'primary' | 'secondary' | 'ghost';
    loading?: boolean;
  }
>;

export function Button({
  children,
  className,
  variant = 'primary',
  loading,
  disabled,
  ...rest
}: Props) {
  const base =
    'inline-flex items-center justify-center rounded-full px-4 py-2.5 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-sky-serenity disabled:opacity-60 disabled:cursor-not-allowed transition-colors shadow-soft';

  const variants: Record<typeof variant, string> = {
    primary:
      'bg-sky-serenity text-slate-900 hover:bg-sky-300 ring-offset-slate-900',
    secondary:
      'bg-white/90 text-slate-900 hover:bg-white ring-offset-slate-900',
    ghost:
      'bg-transparent text-white hover:bg-white/10 border border-white/30 ring-offset-slate-900',
  };

  return (
    <motion.button
      whileTap={{ scale: 0.96 }}
      className={twMerge(base, variants[variant], className)}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <span className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-white/40 border-t-white" />
      )}
      {children}
    </motion.button>
  );
}

