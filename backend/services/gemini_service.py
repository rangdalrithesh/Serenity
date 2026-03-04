import os
from dotenv import load_dotenv
load_dotenv()
import random
from dataclasses import dataclass
from typing import Dict, Any

from flask import Blueprint, jsonify, request
from google import genai


gemini_bp = Blueprint("gemini", __name__)


@dataclass
class StoryRequest:
    user_id: str
    stress_score: float
    top_contributing_factor: str
    emotional_context: str


def _load_config():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return genai.Client(api_key=api_key)


def _build_prompt(payload: StoryRequest) -> str:
    """
    Build a prompt for Gemini using one of several safe, metaphorical templates.

    All variants:
    - stay under ~180 words
    - avoid medical / diagnostic / crisis language
    - end with subtle hope
    - end with ONE reflective question
    """
    base_context = (
        f"The student's stress awareness score is: {payload.stress_score}.\n"
        f"The main contributing factor is: {payload.top_contributing_factor}.\n"
        f"Additional emotional context from the student: {payload.emotional_context}\n\n"
        "Write a short reflective story (max 180 words) that:\n"
        "- Reflects emotional struggle gently\n"
        "- Encourages resilience\n"
        "- Avoids medical or diagnostic language\n"
        "- Avoids crisis advice or emergency instructions\n"
        "- Ends with subtle hope\n\n"
        "After the story, provide one reflective question.\n\n"
    )

    # Multiple gentle metaphors; one is the original penguin story, others add variety.
    templates = [
    "You are creating a metaphorical story about a student traveling along a winding forest path at dusk.",
    "You are creating a metaphorical story about a small boat crossing a calm-but-shifting lake under changing skies.",
    "You are creating a metaphorical story about a stargazer watching constellations appear slowly in a quiet night sky.",
    "You are creating a metaphorical story about a young gardener tending to plants through an unpredictable season.",
    "You are creating a metaphorical story about a traveler resting at a crossroads between two unknown paths.",
    "You are creating a metaphorical story about a lighthouse keeper watching storms pass from a steady shore.",
    "You are creating a metaphorical story about a musician learning a difficult piece one note at a time.",
    ]

    chosen_intro = random.choice(templates)

    return f"{chosen_intro}\n\n{base_context}"


def _fallback_story(stress_score: float) -> Dict[str, str]:
    # Simple tiered fallback stories aligned with frontend.
    if stress_score <= 0.3:
        story_text = (
            "On a calm shoreline of snow and sea, a small penguin eyed a gentle hill. "
            "The climb was not dramatic, but the penguin still felt a quiet flutter in its chest. "
            "With each small step, it noticed the cool air, the sound of distant waves, and the steady rhythm of its breath. "
            "Halfway up, the penguin paused and looked back—noticing that even light days still ask for effort. "
            "At the top, there were no trumpets or fireworks, just a soft view of the sea and a sense of quiet pride for simply showing up."
        )
        question = "What is one small, kind thing you can offer yourself today?"
    elif stress_score <= 0.6:
        story_text = (
            "Beneath a pale sky, a young penguin faced a taller, twistier mountain. "
            "Some paths were packed with footprints from busy days; others were untouched and uncertain. "
            "The penguin carried a backpack of buzzing thoughts—deadlines, what-ifs, and moments replayed in its mind. "
            "Now and then, the wind pushed hard enough that the penguin wanted to turn back. "
            "But every time it paused to rest against a rock, it realised the mountain did not grow. "
            "Rest did not erase progress; it simply gave space for a steadier next step."
        )
        question = (
            "When life feels crowded, what helps you remember that it is okay to pause?"
        )
    else:
        story_text = (
            "At the edge of a wide, icy valley, a small penguin studied a steep, jagged mountain. "
            "The air felt heavy with unspoken worries and tiredness. "
            "Some days, the penguin doubted it could climb at all. "
            "So it chose a different rule: instead of conquering the mountain, it would focus on a single patch of snow at a time. "
            "Step, breath, pause. Step, breath, pause. "
            "Along the way, it leaned on sturdy rocks, pockets of sunlight, and the distant sound of waves that reminded it the world was bigger than this climb. "
            "By the time it reached a resting ledge, the view had shifted just enough to feel a little more possible."
        )
        question = (
            "When everything feels steep, who or what helps you feel a little less alone?"
        )

    return {
        "story_text": story_text,
        "suggested_reflection_question": question,
    }


@gemini_bp.route("/api/story/generate", methods=["POST"])
def generate_story() -> Any:
    try:
        payload = request.get_json(force=True) or {}
        story_request = StoryRequest(
            user_id=str(payload.get("user_id", "anonymous")),
            stress_score=float(payload.get("stress_score", 0.0)),
            top_contributing_factor=str(
                payload.get("top_contributing_factor", "recent patterns")
            ),
            emotional_context=str(payload.get("emotional_context", "")),
        )

        try:
            client = _load_config()
        except RuntimeError as e:
            # Gemini misconfigured: return graceful fallback without 500
            return jsonify(_fallback_story(story_request.stress_score)), 200

        system_prompt = (
            "You are an emotionally supportive storytelling assistant.\n"
            "You create short reflective stories (150–200 words).\n"
            "You do NOT provide medical advice.\n"
            "You do NOT diagnose mental illness.\n"
            "Tone must be gentle, hopeful, and reflective."
        )

        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        

        prompt = _build_prompt(story_request)
        result = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        text = result.text.strip() if result and getattr(result, "text", None) else ""

        if not text:
            return jsonify(_fallback_story(story_request.stress_score)), 200

        # Heuristic split: story vs question
        if "?" in text:
            # take last question mark sentence as reflective question
            parts = text.rsplit("?", 1)
            story_text = parts[0].strip() + "."
            question = parts[1].strip()
            if question:
                question = question + "?"
        else:
            story_text = text
            question = "What part of this story felt closest to your own experience today?"

        return jsonify(
            {
                "story_text": story_text,
                "suggested_reflection_question": question,
            }
        )
    except Exception as exc:  # noqa: BLE001
        # Log server-side and respond with safe fallback.
        print(f"[Gemini] Error generating story: {exc}")
        body = request.get_json(silent=True) or {}
        stress_score = float(body.get("stress_score", 0.0))
        return jsonify(_fallback_story(stress_score)), 200

