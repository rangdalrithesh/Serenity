import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { CheckinService } from '../services/api';

type AggregatedPoint = {
  date: string;
  avg_score: number;
  n_students: number;
};

export function TherapistDashboardPage() {
  const [trend, setTrend] = useState<AggregatedPoint[]>([]);
  const [featureImportance, setFeatureImportance] = useState<
    Array<{ factor: string; contribution: number }>
  >([]);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    CheckinService.stressTrend()
      .then((data) => {
        setTrend(
          data.map((d) => ({
            date: d.date,
            avg_score: d.score,
            n_students: 0,
          })),
        );
      })
      .catch((e) => console.error('Failed to load therapist trend', e));
    CheckinService.featureImportance()
      .then(setFeatureImportance)
      .catch((e) => console.error('Failed to load therapist importance', e));
  }, []);

  const exportReport = async () => {
    setExporting(true);
    try {
      const response = await fetch('http://localhost:8000/api/reports/export');
      if (!response.ok) throw new Error('Export failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'serenity_cohort_report.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('Failed to export report.');
    } finally {
      setExporting(false);
    }
  };

  // Axis / tooltip tick colour adapts to colour scheme
  const tickColor  = 'var(--chart-tick, #64748b)';
  const gridColor  = 'rgba(148,163,184,0.25)';
  const tooltipBg  = 'var(--tooltip-bg, rgba(255,255,255,0.97))';
  const tooltipBdr = 'var(--tooltip-border, rgba(100,116,139,0.3))';

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.17em] text-slate-500 dark:text-slate-200/70">
            Therapist dashboard
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white sm:text-3xl">
            Cohort-level stress insights.
          </h1>
          <p className="mt-1 max-w-xl text-xs text-slate-600 dark:text-slate-200/80 sm:text-sm">
            These charts summarize anonymized student trends. Use them to open
            conversations—not to label individuals.
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 text-xs text-slate-600 dark:text-slate-200/80">
          <div>
            <span className="font-semibold text-slate-800 dark:text-slate-200">
              Model version:
            </span>{' '}
            <span>students_mh_ml_pipeline v1.0</span>
          </div>
          <Button
            type="button"
            variant="secondary"
            className="px-3 py-1.5 text-xs"
            onClick={exportReport}
            loading={exporting}
          >
            Export report
          </Button>
        </div>
      </div>

      {/* ── Charts ─────────────────────────────────────────────────────── */}
      <div className="grid gap-5 md:grid-cols-[minmax(0,1.3fr),minmax(0,1fr)]">
        <Card
          title="Average stress awareness over time"
          subtitle="Line shows cohort-level mean score; counts are de-identified."
          className="h-64"
        >
          {trend.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={gridColor}
                  vertical={false}
                />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  tickMargin={8}
                  tick={{ fontSize: 10, fill: tickColor }}
                />
                <YAxis
                  domain={[0, 1]}
                  tickLine={false}
                  tickMargin={6}
                  tick={{ fontSize: 10, fill: tickColor }}
                />
                <Tooltip
                  contentStyle={{
                    background: tooltipBg,
                    borderRadius: 12,
                    border: `1px solid ${tooltipBdr}`,
                    fontSize: 11,
                    color: '#1e293b',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="avg_score"
                  stroke="#7CC6FE"
                  strokeWidth={2.4}
                  dot={false}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-xs text-slate-500 dark:text-slate-200/75">
              Once check-ins begin, this chart will show group-level movement in
              stress awareness.
            </p>
          )}
        </Card>

        <Card
          title="Feature importance snapshot"
          subtitle="Helps interpret which patterns the model weighs most heavily."
          className="h-64"
        >
          {featureImportance.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={featureImportance}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={gridColor}
                  vertical={false}
                />
                <XAxis
                  dataKey="factor"
                  tickLine={false}
                  tickMargin={6}
                  tick={{ fontSize: 10, fill: tickColor }}
                />
                <YAxis hide />
                <Tooltip
                  contentStyle={{
                    background: tooltipBg,
                    borderRadius: 12,
                    border: `1px solid ${tooltipBdr}`,
                    fontSize: 11,
                    color: '#1e293b',
                  }}
                />
                <Legend
                  formatter={(value) => (
                    <span
                      style={{
                        fontSize: 11,
                        color: 'var(--legend-text, #475569)',
                      }}
                    >
                      {value}
                    </span>
                  )}
                />
                <Bar
                  dataKey="contribution"
                  name="Relative contribution"
                  radius={[8, 8, 0, 0]}
                  fill="url(#serenityGradientExplain)"
                />
                <defs>
                  <linearGradient
                    id="serenityGradientExplain"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor="#6ED3CF" />
                    <stop offset="50%" stopColor="#7CC6FE" />
                    <stop offset="100%" stopColor="#C3B6FF" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-xs text-slate-500 dark:text-slate-200/80">
              As the model accumulates more data, you&apos;ll see which
              categories (behavioral, narrative, academic) influence scores most
              strongly.
            </p>
          )}
        </Card>
      </div>

      {/* ── Explainability notes ────────────────────────────────────────── */}
      <Card
        title="Explainability notes"
        subtitle="Guidelines for communicating model outputs ethically."
      >
        <ul className="list-disc space-y-1 pl-5 text-[11px] text-slate-600 dark:text-slate-200/85">
          <li>
            Use scores as conversation starters, not labels or diagnostic tools.
          </li>
          <li>
            Combine model outputs with your clinical judgement and the
            student&apos;s own narrative.
          </li>
          <li>
            Avoid sharing precise numeric scores with students; focus on trends
            and themes.
          </li>
          <li>
            Clearly communicate that SERENITY does not provide medical advice or
            crisis guidance.
          </li>
        </ul>
      </Card>
    </motion.div>
  );
}