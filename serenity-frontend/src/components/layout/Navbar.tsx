import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MoonIcon, SunIcon } from '@heroicons/react/24/outline';
import { useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';

export function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, theme, setTheme } = useAppStore();
  const dark = theme === 'dark';

  // Apply theme to document (single source of truth from store)
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(dark ? 'light' : 'dark');
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const onHome = location.pathname === '/';

  return (
    <header className="px-4 pt-4 sm:px-8 sm:pt-6">
      <nav className="glass-panel mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
        <div className="flex items-center gap-3">
          <motion.div
            initial={{ y: -10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-serenity/90 dark:bg-white/70 shadow-soft"
          >
            <Link to="/">
  <img
    src="/serenity_logo_white.png"
    alt="Serenity"
    className="h-8 w-auto object-contain"
  />
</Link>
          </motion.div>
          <div>
            <Link
              to="/"
              className="block text-lg font-semibold tracking-tight text-slate-800 dark:text-white"
            >
              SERENITY
            </Link>
            <p className="text-xs text-slate-600 dark:text-slate-200/80">
              Pause. Reflect. Breathe.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!onHome && (
            <Link
              to="/dashboard"
              className="hidden rounded-full bg-slate-200/80 dark:bg-white/10 px-3 py-1.5 text-xs font-medium text-slate-800 dark:text-white shadow-soft backdrop-blur sm:inline-block"
            >
              Dashboard
            </Link>
          )}
          {user ? (
            <button
              onClick={handleLogout}
              className="rounded-full bg-sky-serenity dark:bg-white/90 px-3 py-1.5 text-xs font-semibold text-slate-900 shadow-soft hover:opacity-90"
            >
              Logout
            </button>
          ) : (
            <>
              <Link
                to="/login"
                className="hidden rounded-full border border-slate-300 dark:border-white/40 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-white/90 hover:bg-slate-100 dark:hover:bg-white/10 sm:inline-block"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="hidden rounded-full bg-sky-serenity px-3 py-1.5 text-xs font-semibold text-slate-900 shadow-soft hover:bg-sky-400 sm:inline-block"
              >
                Get Started
              </Link>
            </>
          )}

          <button
            aria-label="Toggle theme"
            onClick={toggleTheme}
            className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 dark:bg-white/20 text-slate-700 dark:text-white hover:bg-slate-300 dark:hover:bg-white/30 transition-colors"
          >
            {dark ? (
              <MoonIcon className="h-4 w-4" />
            ) : (
              <SunIcon className="h-4 w-4" />
            )}
          </button>
        </div>
      </nav>
    </header>
  );
}

