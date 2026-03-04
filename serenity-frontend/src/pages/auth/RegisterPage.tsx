import { FormEvent, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AuthLayout } from './AuthLayout';
import { Button } from '../../components/ui/Button';
import { AuthService } from '../../services/api';
import { useAppStore } from '../../store/useAppStore';

const passwordValid = (value: string) =>
  value.length >= 8 &&
  /[A-Za-z]/.test(value) &&
  /\d/.test(value) &&
  /[^A-Za-z0-9]/.test(value);

export function RegisterPage() {
  const navigate = useNavigate();
  const { setUser, setToken } = useAppStore();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!name || !email || !password) {
      setError('Please fill in all fields.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    if (!passwordValid(password)) {
      setError(
        'Password must be at least 8 characters and include a number, letter, and symbol.',
      );
      return;
    }
    setLoading(true);
    try {
      const data = await AuthService.register({ name, email, password });
      setToken(data.token);
      setUser(data.user as any);
      navigate('/dashboard');
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ??
        err?.response?.data?.message ??
        'Unable to register. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create your SERENITY space."
      subtitle="A soft place to check in with yourself and notice your patterns over time."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <p className="rounded-md bg-red-500/10 px-3 py-2 text-xs text-red-200">
            {error}
          </p>
        )}
        <div className="space-y-1.5">
          <label
            htmlFor="name"
            className="text-xs font-medium text-slate-200"
          >
            Name
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-50 outline-none ring-sky-serenity/60 focus:ring"
            placeholder="How should we greet you?"
            autoComplete="name"
          />
        </div>
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
            placeholder="Create a strong password"
            autoComplete="new-password"
          />
          <p className="mt-0.5 text-[10px] text-slate-400">
            Use at least 8 characters, including a letter, number, and symbol.
          </p>
        </div>
        <div className="space-y-1.5">
          <label
            htmlFor="confirm"
            className="text-xs font-medium text-slate-200"
          >
            Confirm password
          </label>
          <input
            id="confirm"
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-50 outline-none ring-sky-serenity/60 focus:ring"
            placeholder="Repeat your password"
            autoComplete="new-password"
          />
        </div>
        <Button type="submit" className="w-full" loading={loading}>
          Create account
        </Button>
        <p className="text-center text-[11px] text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-sky-serenity">
            Log in
          </Link>
          .
        </p>
      </form>
    </AuthLayout>
  );
}

