import { StoryService } from './api';

export type GeneratedStory = {
  storyText: string;
  reflectionQuestion: string;
  fromFallback?: boolean;
};

const fallbackStories: { threshold: number; story: GeneratedStory }[] = [
  {
    threshold: 0.3,
    story: {
      storyText:
        'On a quiet morning by the sea, a small penguin gazed up at a gentle hill. It was not a towering peak, but it still felt new and a little uncertain. With each careful step, the penguin listened to the soft crunch of snow and the slow rhythm of its own breath. The climb was not about speed or impressing anyone else—it was simply about being present for each moment. Now and then, the penguin paused to look back, noticing how far it had already come, even if the path behind looked ordinary to others. A faint warmth settled in its chest as it realized that small, steady efforts were enough. At the top of the hill, the penguin did not find fireworks or fanfare, just a calm view of the sea and the feeling of having shown up for itself today.',
      reflectionQuestion:
        'What is one small, gentle step you can take for yourself today?',
      fromFallback: true,
    },
  },
  {
    threshold: 0.6,
    story: {
      storyText:
        'Under a pale sky, a young penguin stood at the base of a taller, windier mountain. The path twisted and dipped, sometimes disappearing under drifts of snow. The penguin carried a backpack filled with worries—questions about the future, small mistakes replaying in its mind, and the quiet pressure to handle everything perfectly. As the climb began, each gust of wind made the penguin want to turn back. But then it noticed something: every time it stopped to rest, the mountain did not grow taller. The pause did not erase progress. Instead, it gave the penguin a chance to feel its heartbeat, to adjust its footing, and to remind itself that it was allowed to move slowly. Step by step, breath by breath, the penguin discovered that courage could look like simply continuing, even when the journey felt messy and unsure.',
      reflectionQuestion:
        'When things feel heavy, what helps you remember that it is okay to move slowly?',
      fromFallback: true,
    },
  },
  {
    threshold: 1,
    story: {
      storyText:
        'On the edge of a vast, icy valley, a small penguin stared up at a steep, jagged mountain. The air felt thick with unspoken worries and tired thoughts. Some days, the penguin doubted it could climb at all. But the mountain did not demand a perfect performance—it simply waited. So the penguin chose one small section of the path and focused only on that. It took a few steps, then paused, letting the cold wind pass and the tightness in its chest soften. Along the way, the penguin noticed quiet helpers: a sturdy rock to lean on, a patch of sunlight to rest in, the distant sound of waves reminding it that the world was bigger than this difficult moment. By the time it reached a ledge halfway up, the view had already changed. The mountain was still there, but so was the penguin, breathing, present, and still willing to try again tomorrow.',
      reflectionQuestion:
        'When the climb feels overwhelming, what or who helps you feel a little less alone?',
      fromFallback: true,
    },
  },
];

export async function generateSupportiveStory(args: {
  userId: string;
  stressScore: number;
  topContributingFactor: string;
  emotionalContext: string;
}): Promise<GeneratedStory> {
  try {
    const response = await StoryService.generate({
      user_id: args.userId,
      stress_score: args.stressScore,
      top_contributing_factor: args.topContributingFactor,
      emotional_context: args.emotionalContext,
    });

    return {
      storyText: response.story_text,
      reflectionQuestion: response.suggested_reflection_question,
    };
  } catch (error) {
    console.error('Gemini story generation failed, using fallback', error);
    const entry =
      fallbackStories.find((s) => args.stressScore <= s.threshold) ??
      fallbackStories[fallbackStories.length - 1];
    return entry.story;
  }
}

