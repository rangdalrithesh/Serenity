import type { PropsWithChildren, ReactNode } from 'react';
import { twMerge } from 'tailwind-merge';

type Props = PropsWithChildren<{
  title?: ReactNode;
  subtitle?: ReactNode;
  className?: string;
}>;

export function Card({ title, subtitle, className, children }: Props) {
  return (
    <section
      className={twMerge(
        'glass-panel relative overflow-hidden p-5 sm:p-6',
        className,
      )}
    >
      {(title || subtitle) && (
        <header className="mb-3">
          {title && (
            <h2 className="text-sm font-semibold text-slate-800 dark:text-white/90">{title}</h2>
          )}
          {subtitle && (
            <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-200/80">{subtitle}</p>
          )}
        </header>
      )}
      {children}
    </section>
  );
}

