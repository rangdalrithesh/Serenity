import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  LabelList
} from "recharts";
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StressGauge } from '../components/visual/StressGauge';
import { CheckinService } from '../services/api';
import { useAppStore } from '../store/useAppStore';
import { Link } from 'react-router-dom';

const quotes = [
  'You are allowed to be a work in progress and a person worthy of gentleness at the same time.',
  'Small pauses count. Even a single slow breath is a tiny act of care.',
  'Awareness is not about fixing yourself; it is about meeting yourself where you are.',
  'Your pace is still valid, even when the world feels fast.',
];

function todayIndex() {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const diff =
    now.getTime() -
    start.getTime() +
    (start.getTimezoneOffset() - now.getTimezoneOffset()) * 60 * 1000;
  const day = Math.floor(diff / (1000 * 60 * 60 * 24));
  return day % quotes.length;
}

export function DashboardPage() {
  const { user, stressScore, featureImportance, setFeatureImportance } = useAppStore();
  const [trend, setTrend] = useState<Array<{ date: string; score: number }>>([]);
  const [breakdown, setBreakdown] = useState<{
    by_relationship: Array<{ name: string; count: number }>;
    by_substance: Array<{ name: string; count: number }>;
    by_sleep: Array<{ name: string; value: number; count: number }>;
    by_social: Array<{ name: string; value: number; count: number }>;
    avg_sleep: number;
    avg_social: number;
  } | null>(null);

  useEffect(() => {
    CheckinService.stressTrend()
      .then(setTrend)
      .catch((e) => console.error('Failed to load trend', e));
    if (!featureImportance.length) {
      CheckinService.featureImportance()
        .then(setFeatureImportance)
        .catch((e) => console.error('Failed to load feature importance', e));
    }
    CheckinService.checkinBreakdown()
      .then(setBreakdown)
      .catch((e) => console.error('Failed to load breakdown', e));
  }, [featureImportance.length, setFeatureImportance]);

  const topFactor = useMemo(
    () =>
      featureImportance.length
        ? featureImportance.reduce((max, current) =>
            current.contribution > max.contribution ? current : max,
          )
        : null,
    [featureImportance],
  );

  const quote = quotes[todayIndex()];

  const avgSleep = breakdown?.avg_sleep ?? 3;
  const avgSocial = breakdown?.avg_social ?? 3;
  const burnoutScore =
    typeof stressScore === 'number'
      ? Math.min(
          1,
          stressScore * 0.6 +
            (1 - avgSleep / 5) * 0.25 +
            (1 - avgSocial / 5) * 0.15,
        )
      : null;

  const wellbeingMetrics = [
    { name: 'Stress awareness', value: typeof stressScore === 'number' ? stressScore : 0, fill: '#7CC6FE' },
    { name: 'Burnout risk',     value: burnoutScore ?? 0,                                 fill: '#FFB38A' },
    { name: 'Sleep quality',    value: avgSleep / 5,                                      fill: '#6ED3CF' },
    { name: 'Social support',   value: avgSocial / 5,                                     fill: '#C3B6FF' },
  ].filter((m) => m.value > 0 || m.name === 'Stress awareness' || m.name === 'Burnout risk');

  // Tooltip styles — work in both modes
  const chartTooltipStyle = {
    background: 'rgba(15, 23, 42, 0.96)',
    borderRadius: 12,
    border: '1px solid rgba(148, 163, 184, 0.4)',
    fontSize: 11,
    color: '#e2e8f0',
  };

  // Tick color works on both white and dark card backgrounds
  const chartTickFill = '#94a3b8'; // slate-400 — readable on both

  const emptyText = 'text-xs text-slate-500 dark:text-slate-400';

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.17em] text-slate-500 dark:text-slate-400">
            Daily dashboard
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-800 dark:text-white sm:text-3xl">
            Hello, {user?.name ?? 'friend'}.
          </h1>
          <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">
            Here is a gentle snapshot of your recent stress awareness. No scores are &ldquo;good&rdquo; or &ldquo;bad&rdquo;—they are just signals.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/check-in"><Button>New check-in</Button></Link>
          <Link to="/story"><Button variant="ghost"className="text-slate-700 dark:text-white border border-slate-300 dark:border-slate-600">View latest story</Button></Link>
          <Link to="/therapist"><Button variant="secondary">Therapist Dashboard</Button></Link>
        </div>
      </div>

      {/* Top 3 cards */}
      <div className="grid gap-5 md:grid-cols-[minmax(0,1fr),minmax(0,1fr),minmax(0,1fr)]">

        {/* Stress gauge */}
        <Card
          title="Current stress awareness score"
          subtitle="Based on your most recent check-in."
          className="flex flex-col items-center justify-center"
        >
          {typeof stressScore === 'number' ? (
            <StressGauge value={stressScore} />
          ) : (
            <p className={emptyText}>
              No score yet. Try completing your first check-in to see this gauge come to life.
            </p>
          )}
        </Card>

        {/* Burnout card – bar style */}
        <Card
          title="Penguin energy status"
          subtitle="A gentle reflection of your current burnout risk."
          className="flex items-center justify-center h-80"
        >
          {burnoutScore !== null ? (
            <div className="flex flex-col items-center justify-center w-full text-center space-y-6">
              <div className="flex flex-col items-center justify-center space-y-4 text-center">
                <img src="/serenity_logo_white.png" alt="Serenity" className="h-20 w-auto object-contain" />
                <div className="text-3xl font-semibold text-slate-800 dark:text-white">
                  {(burnoutScore * 100).toFixed(0)}%
                </div>
              </div>

              {/* Progress bar — fixed for light mode */}
              <div className="w-2/3">
                <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-700/60 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      burnoutScore < 0.4 ? 'bg-emerald-400'
                      : burnoutScore < 0.7 ? 'bg-amber-400'
                      : 'bg-rose-400'
                    }`}
                    style={{ width: `${burnoutScore * 100}%` }}
                  />
                </div>
              </div>

              <div className="text-sm font-medium">
                {burnoutScore < 0.4 && <span className="text-emerald-500 dark:text-emerald-400">Your penguin is feeling steady.</span>}
                {burnoutScore >= 0.4 && burnoutScore < 0.7 && <span className="text-amber-500 dark:text-amber-400">Your penguin needs a little rest.</span>}
                {burnoutScore >= 0.7 && <span className="text-rose-500 dark:text-rose-400">Your penguin is overwhelmed.</span>}
              </div>

              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-[280px]">
                This isn't a diagnosis — just a friendly nudge to take care of yourself.
              </p>
            </div>
          ) : (
            <p className={emptyText}>Complete a check-in to see your penguin's status.</p>
          )}
        </Card>

        {/* Burnout card – ring style */}
        <Card
          title="Penguin energy level"
          subtitle="Your Arctic companion today."
          className="flex items-center justify-center h-80"
        >
          {burnoutScore !== null ? (
            <div className="flex flex-col items-center justify-center space-y-5">
              <div className="relative w-36 h-36 flex items-center justify-center rounded-full bg-gradient-to-br from-sky-100 to-purple-100 dark:from-slate-800 dark:to-slate-700 shadow-inner">
                <svg className="absolute w-full h-full rotate-[-90deg]">
                  <circle cx="72" cy="72" r="60"
                    stroke="rgba(148,163,184,0.25)" strokeWidth="8" fill="none" />
                  <circle cx="72" cy="72" r="60"
                    stroke={burnoutScore < 0.4 ? '#10B981' : burnoutScore < 0.7 ? '#F59E0B' : '#EF4444'}
                    strokeWidth="8"
                    strokeDasharray={2 * Math.PI * 60}
                    strokeDashoffset={2 * Math.PI * 60 * (1 - burnoutScore)}
                    strokeLinecap="round" fill="none"
                  />
                </svg>
                <img src="/serenity_logo_white.png" alt="Serenity" className="h-12 w-auto object-contain" />
              </div>

              <div className="text-3xl font-semibold text-slate-800 dark:text-white">
                {(burnoutScore * 100).toFixed(0)}%
              </div>

              <div className="text-sm font-medium text-center">
                {burnoutScore < 0.4 && <span className="text-emerald-500 dark:text-emerald-400">Gliding smoothly 🌿</span>}
                {burnoutScore >= 0.4 && burnoutScore < 0.7 && <span className="text-amber-500 dark:text-amber-400">A little chilly ❄️</span>}
                {burnoutScore >= 0.7 && <span className="text-rose-500 dark:text-rose-400">Very cold — slow down 🧊</span>}
              </div>
            </div>
          ) : (
            <p className={emptyText}>Complete a check-in to wake your penguin.</p>
          )}
        </Card>
      </div>

      {/* Wellbeing overview */}
      <Card
        title="Wellbeing overview"
        subtitle="All metrics normalized 0–1 (higher is better for sleep & social)."
      >
        {wellbeingMetrics.length ? (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={wellbeingMetrics} layout="vertical" margin={{ left: 8, right: 8 }}>
                <XAxis type="number" domain={[0, 1]} hide />
                <YAxis
                  type="category" dataKey="name" width={120}
                  tick={{ fontSize: 11, fill: chartTickFill }} tickLine={false}
                />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {wellbeingMetrics.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className={emptyText}>Complete a check-in to see your wellbeing overview.</p>
        )}
      </Card>

      {/* Trend + feature importance */}
      <div className="grid gap-5 md:grid-cols-[minmax(0,1.4fr),minmax(0,1fr)]">
        <Card
          title="30-day stress trend"
          subtitle="Area chart: how your stress awareness score has shifted over time."
          className="h-64"
        >
          {trend.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend}>
                <defs>
                  <linearGradient id="stressGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#7CC6FE" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#7CC6FE" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.25)" vertical={false} />
                <XAxis dataKey="date" tickLine={false} tickMargin={8} tick={{ fontSize: 10, fill: chartTickFill }} />
                <YAxis domain={[0, 1]} tickLine={false} tickMargin={6} tick={{ fontSize: 10, fill: chartTickFill }} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Area type="monotone" dataKey="score" stroke="#7CC6FE" strokeWidth={2} fill="url(#stressGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className={emptyText}>When you have a few check-ins, SERENITY will draw your trend here.</p>
          )}
        </Card>

        <Card
          title="What seems to matter most?"
          subtitle="Behavioral vs narrative contributions based on the model."
        >
          {featureImportance.length ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={featureImportance}>
                <defs>
                  <linearGradient id="serenityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#7CC6FE" />
                    <stop offset="50%" stopColor="#C3B6FF" />
                    <stop offset="100%" stopColor="#FFB38A" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.25)" vertical={false} />
                <XAxis dataKey="factor" tickLine={false} tickMargin={6} tick={{ fontSize: 10, fill: chartTickFill }} />
                <YAxis hide />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Bar dataKey="contribution" radius={[8, 8, 0, 0]} fill="url(#serenityGradient)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className={emptyText}>After a few check-ins, this card will gently highlight patterns in your answers.</p>
          )}

          {topFactor && (
            <p className="mt-3 text-xs text-slate-600 dark:text-slate-300">
              Right now, <span className="font-semibold text-slate-800 dark:text-white">{topFactor.factor}</span>{' '}
              appears to be contributing the most to your stress awareness score.
            </p>
          )}
        </Card>
      </div>

      {/* Relationship & substance breakdowns */}
      <div className="grid gap-5 md:grid-cols-2">
        <Card
          title="Check-ins by relationship status"
          subtitle="How you've described your relationship context over time."
          className="h-80"
        >
          {breakdown && breakdown.by_relationship.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[...breakdown.by_relationship].sort((a, b) => b.count - a.count)}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
              >
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11, fill: chartTickFill }} />
                <Tooltip cursor={{ fill: 'rgba(148,163,184,0.1)' }} contentStyle={chartTooltipStyle} />
                <Bar dataKey="count" radius={[0, 10, 10, 0]} fill="#7CC6FE" barSize={20} isAnimationActive>
                  <LabelList dataKey="count" position="right" style={{ fontSize: 11, fill: chartTickFill }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className={emptyText}>After check-ins with relationship status, you'll see a breakdown here.</p>
          )}
        </Card>

        <Card
          title="Check-ins by substance use"
          subtitle="Optional answers; used only to inform your score."
          className="h-80"
        >
          {breakdown && breakdown.by_substance.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[...breakdown.by_substance].sort((a, b) => b.count - a.count)}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
              >
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11, fill: chartTickFill }} />
                <Tooltip cursor={{ fill: 'rgba(148,163,184,0.1)' }} contentStyle={chartTooltipStyle} />
                <Bar dataKey="count" radius={[0, 10, 10, 0]} fill="#6ED3CF" barSize={20} isAnimationActive>
                  <LabelList dataKey="count" position="right" style={{ fontSize: 11, fill: chartTickFill }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className={emptyText}>After check-ins with substance-use answers, you'll see a breakdown here.</p>
          )}
        </Card>
      </div>

      {/* Sleep & social averages */}
      <div className="grid gap-5 sm:grid-cols-2">
        <Card title="Average sleep quality" subtitle="From your check-ins (1 = poor, 5 = restful).">
          {breakdown && breakdown.avg_sleep > 0 ? (
            <div className="flex items-center gap-4">
              <div className="text-3xl font-semibold text-teal-600 dark:text-teal-400">
                {breakdown.avg_sleep.toFixed(1)}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                out of 5 across your recent check-ins.
              </p>
            </div>
          ) : (
            <p className={emptyText}>Complete check-ins with sleep quality to see your average here.</p>
          )}
        </Card>

        <Card title="Average social support" subtitle="From your check-ins (1 = low, 5 = very supported).">
          {breakdown && breakdown.avg_social > 0 ? (
            <div className="flex items-center gap-4">
              <div className="text-3xl font-semibold text-sky-600 dark:text-sky-400">
                {breakdown.avg_social.toFixed(1)}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                out of 5 across your recent check-ins.
              </p>
            </div>
          ) : (
            <p className={emptyText}>Complete check-ins with social support to see your average here.</p>
          )}
        </Card>
      </div>

      {/* Footer reminder */}
      <motion.div
        className="relative mt-2 flex items-center justify-between rounded-2xl bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700/50 px-4 py-3 text-[11px] text-slate-600 dark:text-slate-300 shadow-soft"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        <span>
          Reminder: SERENITY visualizes patterns but does not diagnose or replace professional help.
        </span>
        <Link to="/">
          <img src="/serenity_logo_white.png" alt="Serenity" className="h-8 w-auto object-contain" />
        </Link>
      </motion.div>
    </motion.div>
  );
}