import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { useAppStore } from '../store/useAppStore';
import { generateSupportiveStory } from '../services/geminiService';
import { StoryService } from '../services/api';

type LocationState = {
  fromCheckIn?: boolean;
  finalScore?: number;
  topFactor?: string;
  emotionalContext?: string;
};

function useTypedLocation() {
  return useLocation() as ReturnType<typeof useLocation> & {
    state?: LocationState;
  };
}

export function StoryPage() {
  const { state } = useTypedLocation();
  const navigate = useNavigate();
  const { user, stressScore } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [story, setStory] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [reflectionAnswer, setReflectionAnswer] = useState('');
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effectiveScore = state?.finalScore ?? stressScore ?? 0.4;
  const effectiveFactor =
    state?.topFactor ?? 'recent habits and daily narratives';
  const emotionalContext =
    state?.emotionalContext ?? 'No specific emotional notes were shared.';

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const generated = await generateSupportiveStory({
          userId: user?.id ?? 'anonymous',
          stressScore: effectiveScore,
          topContributingFactor: effectiveFactor,
          emotionalContext,
        });
        if (cancelled) return;
        setStory(generated.storyText);
        setQuestion(generated.reflectionQuestion);
      } catch (err: any) {
        console.error('Story rendering failed', err);
        if (!cancelled) {
          setError(
            'We could not generate a story right now. Please try again in a little while.',
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, [effectiveFactor, effectiveScore, emotionalContext, user?.id]);

  const saveReflection = async () => {
    if (!reflectionAnswer.trim()) {
      setSaved(false);
      return;
    }
    try {
      await StoryService.saveResponse({
        user_id: user?.id ?? 'anonymous',
        stress_score: effectiveScore,
        reflection_answer: reflectionAnswer.trim(),
      });
      setSaved(true);
      navigate('/dashboard');
    } catch (err) {
      console.error('Failed to save reflection', err);
      setSaved(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
<p className="text-xs font-semibold uppercase tracking-[0.17em] text-slate-200/70">            Story mode
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white sm:text-3xl">
            A story for where you are.
          </h1>
          <p className="mt-1 max-w-xl text-xs text-slate-600 dark:text-slate-300 sm:text-sm">
            This short story is shaped by your latest check-in and stress
            awareness score. It&apos;s not advice—just a gentle mirror.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
          <span>Current score:</span>
<span className="rounded-full bg-slate-900/70 px-3 py-1 font-semibold text-sky-serenity">            {Math.round(effectiveScore * 100)} / 100
          </span>
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-[minmax(0,1.1fr),minmax(0,0.9fr)]">
        <Card
          title="Your reflective penguin story"
          subtitle="Text animates softly to keep the tone gentle and spacious."
        >
          {loading ? (
            <div className="space-y-3">
              <div className="h-3 w-3/4 animate-pulse rounded-full bg-slate-300 dark:bg-slate-700/60" />
              <div className="h-3 w-full animate-pulse rounded-full bg-slate-300 dark:bg-slate-700/60" />
              <div className="h-3 w-5/6 animate-pulse rounded-full bg-slate-300 dark:bg-slate-700/60" />
              <div className="h-3 w-4/6 animate-pulse rounded-full bg-slate-300 dark:bg-slate-700/60" />
            </div>
          ) : error ? (
            <p className="text-xs text-red-600 dark:text-red-300">{error}</p>
          ) : (
            <motion.p
  className="whitespace-pre-line text-sm leading-relaxed text-slate-800 dark:text-slate-100"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8 }}
            >
              {story}
            </motion.p>
          )}
        </Card>

        <Card
          title="Reflective question"
          subtitle="Your response will be saved (optionally) as part of your story log."
        >
          <div className="space-y-3">
            {question && (
              <p className="text-xs text-slate-700 dark:text-slate-200">{question}</p>
            )}

            <textarea
              value={reflectionAnswer}
              onChange={(e) => setReflectionAnswer(e.target.value)}
              rows={4}
             className="w-full rounded-2xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs text-slate-900 dark:text-slate-100 outline-none ring-sky-500/60 focus:ring"
              placeholder="You can answer in a sentence, a few words, or leave this blank if now is not the right time."
            />
            <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
              <span>
                Saving is optional. You can revisit this question any time.
              </span>
              <Button
                type="button"
                variant="secondary"
                className="px-3 py-1 text-xs"
                onClick={saveReflection}
              >
                Save reflection
              </Button>
            </div>
            {saved && (
              <p className="text-[11px] text-emerald-600 dark:text-emerald-300">
                Reflection saved softly to your story log.
              </p>
            )}
          </div>
        </Card>
      </div>

      <Card
        title="The climb continues"
        subtitle="Optional therapist view highlights stay de-identified and aggregated."
      >
        <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-200/80">
          <span>
            Your score and story inform gentle visualizations—and never replace
            the care of a human professional.
          </span>
          
          <span aria-hidden className="text-lg">🌿</span>
        </div>
      </Card>
    </div>
  );
}

