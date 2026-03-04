import { FormEvent, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthLayout } from './AuthLayout';
import { Button } from '../../components/ui/Button';
import { AuthService } from '../../services/api';
import { useAppStore } from '../../store/useAppStore';

export function LoginPage() {
  const navigate = useNavigate();
  const { setUser, setToken } = useAppStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    setLoading(true);
    try {
      const data = await AuthService.login({ email, password });
      setToken(data.token);
      setUser(data.user as any);
      navigate('/dashboard');
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ??
        err?.response?.data?.message ??
        'Unable to log in. Please check your details.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back."
      subtitle="Log in to continue your check-ins and follow your penguin up the mountain."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <p className="rounded-md bg-red-500/10 px-3 py-2 text-xs text-red-200">
            {error}
          </p>
        )}
        <div className="space-y-1.5">
          <label
            htmlFor="email"
            className="text-xs font-medium text-slate-200"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-50 outline-none ring-sky-serenity/60 focus:ring"
            placeholder="you@example.edu"
            autoComplete="email"
          />
        </div>
        <div className="space-y-1.5">
          <label
            htmlFor="password"
            className="text-xs font-medium text-slate-200"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-50 outline-none ring-sky-serenity/60 focus:ring"
            placeholder="••••••••"
            autoComplete="current-password"
            minLength={8}
          />
          <p className="mt-0.5 text-[10px] text-slate-400">
            Use at least 8 characters. Avoid reusing your institution password
            on other sites.
          </p>
        </div>
        <Button type="submit" className="w-full" loading={loading}>
          Login
        </Button>
        <p className="text-center text-[11px] text-slate-400">
          New here?{' '}
          <Link to="/register" className="font-medium text-sky-serenity">
            Create an account
          </Link>
          .
        </p>
      </form>
    </AuthLayout>
  );
}

