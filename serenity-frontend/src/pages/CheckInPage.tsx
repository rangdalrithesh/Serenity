import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { CheckinService } from '../services/api';
import { useAppStore } from '../store/useAppStore';
import { useNavigate } from 'react-router-dom';

type StepId = 'meme' | 'binge' | 'course' | 'relationship' | 'substance' | 'sleep' | 'social' | 'story';

const steps: { id: StepId; label: string; emoji: string }[] = [
  { id: 'meme',         label: 'Vibe check',   emoji: '👁️' },
  { id: 'binge',        label: 'Binge arc',     emoji: '📺' },
  { id: 'course',       label: 'Brain rot',     emoji: '📚' },
  { id: 'relationship', label: 'Situationship', emoji: '💀' },
  { id: 'substance',    label: 'Coping era',    emoji: '🍵' },
  { id: 'sleep',        label: 'Sleep lore',    emoji: '😴' },
  { id: 'social',       label: 'Main chars',    emoji: '🫂' },
  { id: 'story',        label: 'Final boss',    emoji: '✍️' },
];

function sliderMood(val: number, max: number): string {
  const pct = val / max;
  if (pct === 0)   return 'not a thing rn 🫡';
  if (pct <= 0.25) return 'lowkey a little 😶';
  if (pct <= 0.5)  return 'mid-tier struggle 😬';
  if (pct <= 0.75) return `it's giving chaos 😵`;
  return 'send help immediately 🚨';
}

function sleepMood(val: number): string {
  if (val === 1) return 'what even is sleep 💀';
  if (val === 2) return 'barely surviving 😵‍💫';
  if (val === 3) return 'mid. just mid. 😶';
  if (val === 4) return 'actually decent ngl 😌';
  return 'thriving, well-rested era 🌙';
}

function socialMood(val: number): string {
  if (val === 1) return 'main character, alone arc 🌧️';
  if (val === 2) return 'one text away from crying 😭';
  if (val === 3) return 'people exist around me 🤷';
  if (val === 4) return 'got my people fr 🫶';
  return 'literally so supported rn 🌟';
}

function MemeButton({
  selected, onClick, img, fallback, label, caption,
  accentClass = 'border-sky-500 ring-sky-400/40',
  overlayClass = 'bg-sky-500/30',
}: {
  selected: boolean; onClick: () => void; img: string; fallback: string;
  label: string; caption: string; accentClass?: string; overlayClass?: string;
}) {
  const [imgFailed, setImgFailed] = useState(false);
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-2xl border overflow-hidden flex flex-col text-left transition-all duration-200 hover:scale-[1.02] ${
        selected ? `${accentClass} ring-2 scale-[1.02]` : 'border-slate-700 hover:border-slate-500'
      }`}
    >
      <div className="w-full h-full object-contain bg-black aspect-[4/3]">
        {!imgFailed ? (
          <img
  src={img}
  alt={label}
  onError={() => setImgFailed(true)}
  className="w-full h-full object-cover"
/>
        ) : (
          <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '3rem' }}>
            {fallback}
          </div>
        )}
        {selected && (
          <div className={`absolute inset-0 ${overlayClass} flex items-center justify-center text-2xl font-bold text-white`}>✓</div>
        )}
      </div>
      <div className="px-3 py-2 bg-slate-900 flex-1">
        <p className="text-xs font-semibold text-white leading-snug">{label}</p>
        <p className="text-[10px] text-slate-400 mt-0.5">{caption}</p>
      </div>
    </button>
  );
}

export function CheckInPage() {
  const navigate = useNavigate();
  const { user, setStressScore, setFeatureImportance, setCheckinData } = useAppStore();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [memeChoice, setMemeChoice] = useState<string | null>(null);
  const [bingeEpisodes, setBingeEpisodes] = useState(0);
  const [courseStress, setCourseStress] = useState(0);
  const [relationshipStatus, setRelationshipStatus] = useState<string>('');
  const [substanceUse, setSubstanceUse] = useState<string>('');
  const [sleepQuality, setSleepQuality] = useState(3);
  const [socialSupport, setSocialSupport] = useState(3);
  const [narrative, setNarrative] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = steps[currentStepIndex];
  const next = () => setCurrentStepIndex((i) => Math.min(steps.length - 1, i + 1));
  const back = () => setCurrentStepIndex((i) => Math.max(0, i - 1));

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      const payload = {
        meme_mood: memeChoice,
        binge_episodes: bingeEpisodes,
        course_stress: courseStress,
        relationship_status: relationshipStatus,
        substance_use: substanceUse,
        sleep_quality: sleepQuality,
        social_support: socialSupport,
        narrative_text: narrative,
      };
      setCheckinData({
        bingeEpisodes,
        courseStressLevel: courseStress,
        narrativeText: narrative,
        createdAt: new Date().toISOString(),
      });
      await CheckinService.submitCheckin(payload);
      const prediction = await CheckinService.predict(payload);
      setStressScore(prediction.final_score);
      const importance = await CheckinService.featureImportance();
      setFeatureImportance(importance);
      navigate('/story', {
        state: {
          fromCheckIn: true,
          finalScore: prediction.final_score,
          topFactor: prediction.top_contributing_factor,
          emotionalContext: narrative || memeChoice || 'No description given',
        },
      });
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ??
        err?.response?.data?.message ??
        'Something broke. Not you — the app. Try again?';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.17em] text-slate-500 dark:text-slate-400">
            daily check-in ✨
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white sm:text-3xl">
            ok {user?.name ?? 'bestie'}, how are we actually doing?
          </h1>
          <p className="mt-1 max-w-xl text-xs text-slate-600 dark:text-slate-300 sm:text-sm">
            no judgement zone. answer how you actually feel, not how you think you should feel 💅
          </p>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {currentStepIndex + 1} / {steps.length}
        </p>
      </div>

      <div className="flex flex-wrap gap-2 text-[11px]">
        {steps.map((s, idx) => (
          <div
            key={s.id}
            className={`flex items-center gap-1 rounded-full px-3 py-1 transition-all ${
              idx === currentStepIndex
                ? 'bg-sky-serenity/80 text-slate-900 font-semibold scale-105'
                : idx < currentStepIndex
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-100'
                  : 'bg-slate-200 text-slate-500 dark:bg-slate-900/70 dark:text-slate-500'
            }`}
          >
            <span>{s.emoji}</span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {error && (
        <p className="rounded-xl bg-red-500/10 px-4 py-3 text-xs text-red-300">😬 {error}</p>
      )}

      <AnimatePresence mode="wait">
        <motion.div
          key={step.id}
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -40 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        >
          {step.id === 'meme' && (
            <Card title="👁️ ok real talk — current vibe?" subtitle="pick the one that hits. no explanation needed.">
              <div className="grid gap-3 sm:grid-cols-3">
                <MemeButton selected={memeChoice === 'soft'} onClick={() => setMemeChoice('soft')}
                  img="https://images.meme-arsenal.com/1704f010d1ef9519fb5b74b71a2c88ad.jpg" fallback="🪫"
                  label="low battery mode" caption="functioning but barely. doing my best tho." />
                <MemeButton selected={memeChoice === 'spiky'} onClick={() => setMemeChoice('spiky')}
                  img="Gemini_Generated_Image_up6ihvup6ihvup6i.png" fallback="🤯"
                  label="everything at once" caption="47 tabs open and one is playing music." />
                <MemeButton selected={memeChoice === 'calm'} onClick={() => setMemeChoice('calm')}
                  img="imok.png" fallback="😌"
                  label="surprisingly fine" caption="things are actually manageable rn. wild." />
              </div>
            </Card>
          )}

          {step.id === 'binge' && (
            <Card title="📺 the binge arc check" subtitle="how many times did eating feel out of your control this week? zero is valid.">
              <div className="space-y-5">
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  not here to judge — just trying to see the full picture of your week. if this isn't a thing for you rn, leave it at 0 🫡
                </p>
                <div className="flex items-center gap-4">
                  <input type="range" min={0} max={10} value={bingeEpisodes}
                    onChange={(e) => setBingeEpisodes(Number(e.target.value))}
                    className="w-full accent-sky-serenity" />
                  <span className="w-8 text-center text-sm font-bold text-sky-serenity">{bingeEpisodes}</span>
                </div>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 italic">→ {sliderMood(bingeEpisodes, 10)}</p>
              </div>
            </Card>
          )}

          {step.id === 'course' && (
            <Card title="📚 academic brain rot level?" subtitle="0 = chill student energy. 10 = crying in the library.">
              <div className="space-y-5">
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  how cooked are you academically rn? deadlines, exams, that one assignment you've been avoiding — all counts 💀
                </p>
                <div className="flex items-center gap-4">
                  <input type="range" min={0} max={10} value={courseStress}
                    onChange={(e) => setCourseStress(Number(e.target.value))}
                    className="w-full accent-peach-serenity" />
                  <span className="w-8 text-center text-sm font-bold text-peach-serenity">{courseStress}</span>
                </div>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 italic">→ {sliderMood(courseStress, 10)}</p>
              </div>
            </Card>
          )}

          {step.id === 'relationship' && (
            <Card title="💀 the situationship status" subtitle="no judgment. truly. this just helps us understand your support context.">
              <div className="space-y-3">
                <p className="text-xs text-slate-600 dark:text-slate-300">where's your relationship lore at rn?</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <MemeButton selected={relationshipStatus === 'single'} onClick={() => setRelationshipStatus('single')}
                    img="single.png" fallback="🎯"
                    label="🎯 single and staying that way" caption="the main character arc" />
                  <MemeButton selected={relationshipStatus === 'in_relationship'} onClick={() => setRelationshipStatus('in_relationship')}
                    img="relationship.jpg" fallback="🫶"
                    label="🫶 in a relationship" caption="got someone fr" />
                  <MemeButton selected={relationshipStatus === 'complicated'} onClick={() => setRelationshipStatus('complicated')}
                    img="complicated.png" fallback="💀"
                    label="💀 it's... complicated" caption="we don't talk about it" />
                  <MemeButton selected={relationshipStatus === 'prefer_not'} onClick={() => setRelationshipStatus('prefer_not')}
                    img="dont ask man.png" fallback="🤐"
                    label="🤐 not sharing that one" caption="totally valid" />
                </div>
              </div>
            </Card>
          )}

          {step.id === 'substance' && (
            <Card title="🍵 the coping era check" subtitle="how often has alcohol or substances been part of the unwind lately?">
              <div className="space-y-4">
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  zero judgment, full transparency. helps the model see how you're managing stress — not rate you as a person 🫶
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {([
                    { id: 'never',     img: 'https://i.imgflip.com/30b1gx.jpg', fallback: '🌿', label: '🌿 never',    caption: 'not my thing' },
                    { id: 'rarely',    img: 'https://i.imgflip.com/4t0m5.jpg',  fallback: '🫗', label: '🫗 rarely',   caption: 'occasional at most' },
                    { id: 'sometimes', img: 'https://i.imgflip.com/3lmzyx.jpg', fallback: '🍺', label: '🍺 sometimes', caption: 'a few times a month' },
                    { id: 'often',     img: 'https://i.imgflip.com/wxica.jpg',  fallback: '🔄', label: '🔄 often',    caption: 'most days tbh' },
                  ] as const).map((opt) => (
                    <MemeButton key={opt.id}
                      selected={substanceUse === opt.id} onClick={() => setSubstanceUse(opt.id)}
                      img={opt.img} fallback={opt.fallback} label={opt.label} caption={opt.caption}
                      accentClass="border-lavender-serenity ring-lavender-serenity/30"
                      overlayClass="bg-purple-500/30" />
                  ))}
                </div>
              </div>
            </Card>
          )}

          {step.id === 'sleep' && (
            <Card title="😴 sleep lore this week?" subtitle="1 = what even is sleep | 5 = honestly thriving">
              <div className="space-y-5">
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  doomscrolling at 3am counts as not sleeping well btw. be honest with yourself bestie 💀
                </p>
                <div className="flex items-center gap-4">
                  <input type="range" min={1} max={5} value={sleepQuality}
                    onChange={(e) => setSleepQuality(Number(e.target.value))}
                    className="w-full accent-teal-serenity" />
                  <span className="w-8 text-center text-sm font-bold text-teal-serenity">{sleepQuality}</span>
                </div>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 italic">→ {sleepMood(sleepQuality)}</p>
              </div>
            </Card>
          )}

          {step.id === 'social' && (
            <Card title="🫂 who's in your corner rn?" subtitle="1 = completely on your own | 5 = you have your people">
              <div className="space-y-5">
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  not about how many followers you have — about whether you have even one person you could text rn 🫶
                </p>
                <div className="flex items-center gap-4">
                  <input type="range" min={1} max={5} value={socialSupport}
                    onChange={(e) => setSocialSupport(Number(e.target.value))}
                    className="w-full accent-sky-serenity" />
                  <span className="w-8 text-center text-sm font-bold text-sky-serenity">{socialSupport}</span>
                </div>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400 italic">→ {socialMood(socialSupport)}</p>
              </div>
            </Card>
          )}

          {step.id === 'story' && (
            <Card title="✍️ final boss: what's actually going on?" subtitle="dump it here. messy is fine. fragments are fine. emojis are fine.">
              <div className="grid gap-4 md:grid-cols-[minmax(0,1.1fr),minmax(0,0.9fr)]">
                <div className="space-y-3">
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    what's been heavy lately? what's kept you going, even a little?
                    the more real you are, the more the story will actually resonate ✨
                  </p>
                  <textarea
                    value={narrative}
                    onChange={(e) => setNarrative(e.target.value)}
                    rows={5}
                    className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-100 outline-none ring-sky-serenity/60 focus:ring placeholder:text-slate-600"
                    placeholder="e.g. 'been feeling kinda invisible lately but my playlist has been saving me ngl' — anything goes"
                  />
                  <p className="text-[10px] text-slate-500">stays between you and your care team. never shared, never judged 🔒</p>
                </div>
                <div className="relative flex flex-col items-center justify-center gap-3">
                  <div className="relative flex h-36 w-36 items-center justify-center rounded-full bg-gradient-to-b from-sky-serenity via-lavender-serenity to-peach-serenity shadow-soft">
                    <span className="text-4xl" aria-hidden><img
  src="/serenity_logo_white.png"
  alt="Serenity"
  className="h-32 w-32 object-contain"
/></span>
                  </div>
                  <p className="max-w-[180px] rounded-2xl bg-slate-950/85 px-3 py-2 text-[11px] text-slate-100 shadow-soft text-center">
                    &ldquo;one honest sentence is worth more than a perfect paragraph&rdquo;
                  </p>
                </div>
              </div>
            </Card>
          )}
        </motion.div>
      </AnimatePresence>

      <div className="flex items-center justify-between">
        <Button type="button" disabled={currentStepIndex === 0 || submitting} onClick={back}
          className="border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800">
          ← back
        </Button>
        {currentStepIndex < steps.length - 1 ? (
          <Button type="button" onClick={next}>next →</Button>
        ) : (
          <Button type="button" onClick={handleSubmit} loading={submitting} disabled={submitting}>
            {submitting ? 'cooking your story... 🍳' : 'generate my story ✨'}
          </Button>
        )}
      </div>
    </div>
  );
}