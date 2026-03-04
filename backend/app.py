import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from flask_cors import CORS
from services.gemini_service import gemini_bp

from config import DB_PATH


def get_db() -> sqlite3.Connection:
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn


def init_auth_schema() -> None:
  """Create minimal auth + check-in tables if they don't exist."""
  conn = get_db()
  cur = conn.cursor()

  # Users table for authentication
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      role TEXT DEFAULT 'student',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
  )

  # Check-in table to back dashboard charts
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS serenity_checkins (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      meme_mood TEXT,
      binge_episodes INTEGER,
      course_stress INTEGER,
      narrative_text TEXT,
      relationship_status TEXT,
      substance_use TEXT,
      sleep_quality INTEGER,
      social_support INTEGER,
      stress_score REAL,
      top_factor TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
  )
  # Add new columns if table already existed (idempotent)
  for col, typ in [
    ("relationship_status", "TEXT"),
    ("substance_use", "TEXT"),
    ("sleep_quality", "INTEGER"),
    ("social_support", "INTEGER"),
  ]:
    try:
      cur.execute(f"ALTER TABLE serenity_checkins ADD COLUMN {col} {typ}")
    except sqlite3.OperationalError:
      pass  # column exists

  # Story reflections
  cur.execute(
    """
    CREATE TABLE IF NOT EXISTS serenity_story_responses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      stress_score REAL,
      reflection_answer TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
  )

  conn.commit()
  conn.close()


def create_app() -> Flask:
  app = Flask(__name__)

  # Allow frontend dev origin to talk to this API
  CORS(app)

  init_auth_schema()

  # Simple health check
  @app.get("/api/health")
  def health():
    return jsonify({"status": "ok", "service": "serenity-backend"}), 200

  # -----------------------------
  # Auth endpoints
  # -----------------------------
  @app.route("/")
  def home():
    return "Backend is running successfully 🚀"
  @app.post("/api/auth/register")
  def register():
    payload = request.get_json(force=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not name or not email or not password:
      return jsonify({"message": "Name, email, and password are required."}), 400

    if len(password) < 8:
      return jsonify({"message": "Password must be at least 8 characters."}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cur.fetchone():
      conn.close()
      return jsonify({"message": "An account with this email already exists."}), 400

    password_hash = generate_password_hash(password)
    cur.execute(
      "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
      (name, email, password_hash),
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()

    user = {"id": user_id, "name": name, "email": email, "role": "student"}
    # Simple opaque token for demo purposes; frontend only needs a string
    token = f"demo-token-{user_id}"

    return jsonify({"token": token, "user": user}), 201

  @app.post("/api/auth/login")
  def login():
    payload = request.get_json(force=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not email or not password:
      return jsonify({"message": "Email and password are required."}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()

    if not row or not check_password_hash(row["password_hash"], password):
      return jsonify({"message": "Invalid email or password."}), 401

    user = {
      "id": row["id"],
      "name": row["name"],
      "email": row["email"],
      "role": row["role"],
    }
    token = f"demo-token-{row['id']}"
    return jsonify({"token": token, "user": user}), 200

  @app.get("/api/user/profile")
  def profile():
    # For demo, we do not parse JWT; instead return the first user if any.
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role, created_at FROM users ORDER BY id LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if not row:
      return jsonify({"message": "No profile found."}), 404
    return jsonify(
      {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "created_at": row["created_at"],
      }
    )

  # -----------------------------
  # Check-in + prediction
  # -----------------------------

  def _compute_stress_score(
    binge_episodes: int,
    course_stress: int,
    meme_mood: str,
    relationship_status: str = "",
    substance_use: str = "",
    sleep_quality: int = 3,
    social_support: int = 3,
  ) -> Dict[str, Any]:
    """Heuristic 0–1 stress score and top factor using all check-in inputs."""
    binge_norm = max(0, min(10, binge_episodes)) / 10.0
    course_norm = max(0, min(10, course_stress)) / 10.0
    mood_weight = {"soft": 0.25, "spiky": 0.55, "overwhelmed": 0.8}.get(meme_mood or "", 0.4)

    rel_weight = {
      "single": 0.2,
      "in_relationship": 0.15,
      "complicated": 0.5,
      "prefer_not": 0.25,
    }.get((relationship_status or "").strip(), 0.25)

    substance_weight = {
      "never": 0.1,
      "rarely": 0.2,
      "sometimes": 0.45,
      "often": 0.7,
    }.get((substance_use or "").strip().lower(), 0.25)

    # sleep 1–5: 5 = best -> low stress (0.1), 1 = worst -> high (0.7)
    sleep_val = max(1, min(5, sleep_quality or 3))
    sleep_weight = 0.1 + (5 - sleep_val) * 0.15  # 0.1 to 0.7

    # social 1–5: 5 = most support -> low (0.1), 1 = least -> high (0.5)
    social_val = max(1, min(5, social_support or 3))
    social_weight = 0.1 + (5 - social_val) * 0.1  # 0.1 to 0.5

    # Weighted combination (sum of weights ≈ 1)
    score = (
      0.28 * course_norm
      + 0.22 * binge_norm
      + 0.15 * mood_weight
      + 0.12 * rel_weight
      + 0.10 * substance_weight
      + 0.08 * sleep_weight
      + 0.05 * social_weight
    )
    score = max(0.0, min(1.0, score))

    # Pick top factor by contribution
    factors = [
      (course_norm, "Course + academic load"),
      (binge_norm, "Binge / loss-of-control moments"),
      (mood_weight, "Overall emotional tone"),
      (rel_weight, "Relationship / connection"),
      (substance_weight, "Substance use patterns"),
      (sleep_weight, "Sleep quality"),
      (social_weight, "Social support"),
    ]
    top_factor = max(factors, key=lambda x: x[0])[1]
    return {"final_score": score, "top_contributing_factor": top_factor}

  @app.post("/api/checkin")
  def checkin():
    payload = request.get_json(force=True) or {}
    meme_mood = payload.get("meme_mood")
    binge_episodes = int(payload.get("binge_episodes") or 0)
    course_stress = int(payload.get("course_stress") or 0)
    narrative_text = payload.get("narrative_text") or ""
    relationship_status = payload.get("relationship_status") or ""
    substance_use = payload.get("substance_use") or ""
    sleep_quality = int(payload.get("sleep_quality") or 3)
    social_support = int(payload.get("social_support") or 3)

    scores = _compute_stress_score(
      binge_episodes,
      course_stress,
      meme_mood or "",
      relationship_status=relationship_status,
      substance_use=substance_use,
      sleep_quality=sleep_quality,
      social_support=social_support,
    )

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
      """
      INSERT INTO serenity_checkins (
        meme_mood, binge_episodes, course_stress, narrative_text,
        relationship_status, substance_use, sleep_quality, social_support,
        stress_score, top_factor
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """,
      (
        meme_mood,
        binge_episodes,
        course_stress,
        narrative_text,
        relationship_status,
        substance_use,
        sleep_quality,
        social_support,
        scores["final_score"],
        scores["top_contributing_factor"],
      ),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"}), 201

  @app.post("/api/predict")
  def predict():
    payload = request.get_json(force=True) or {}
    meme_mood = payload.get("meme_mood")
    binge_episodes = int(payload.get("binge_episodes") or 0)
    course_stress = int(payload.get("course_stress") or 0)
    relationship_status = payload.get("relationship_status") or ""
    substance_use = payload.get("substance_use") or ""
    sleep_quality = int(payload.get("sleep_quality") or 3)
    social_support = int(payload.get("social_support") or 3)

    scores = _compute_stress_score(
      binge_episodes,
      course_stress,
      meme_mood or "",
      relationship_status=relationship_status,
      substance_use=substance_use,
      sleep_quality=sleep_quality,
      social_support=social_support,
    )
    return jsonify(scores)

  # -----------------------------
  # Story responses
  # -----------------------------

  @app.post("/api/story-response")
  def story_response():
    payload = request.get_json(force=True) or {}
    user_id = payload.get("user_id")
    stress_score = float(payload.get("stress_score") or 0.0)
    reflection_answer = str(payload.get("reflection_answer") or "").strip()

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
      """
      INSERT INTO serenity_story_responses (user_id, stress_score, reflection_answer)
      VALUES (?, ?, ?)
      """,
      (user_id, stress_score, reflection_answer),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "saved"}), 201

  # -----------------------------
  # Dashboard data endpoints
  # -----------------------------

  @app.get("/api/stress-trend")
  def stress_trend():
    """Return last ~30 check-ins aggregated per day."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
      """
      SELECT
        substr(created_at, 1, 10) AS date,
        AVG(stress_score) AS avg_score
      FROM serenity_checkins
      GROUP BY substr(created_at, 1, 10)
      ORDER BY date DESC
      LIMIT 30
      """
    )
    rows = cur.fetchall()
    conn.close()

    # Reverse to chronological order
    data: List[Dict[str, Any]] = [
      {"date": row["date"], "score": round(row["avg_score"] or 0.0, 3)} for row in rows
    ][::-1]
    return jsonify(data)

  @app.get("/api/feature-importance")
  def feature_importance():
    """Feature-importance style data for dashboard & therapist view."""
    return jsonify(
      [
        {"factor": "Course / academics", "contribution": 0.28},
        {"factor": "Binge / control", "contribution": 0.22},
        {"factor": "Emotional tone", "contribution": 0.15},
        {"factor": "Relationship / connection", "contribution": 0.12},
        {"factor": "Substance use", "contribution": 0.10},
        {"factor": "Sleep quality", "contribution": 0.08},
        {"factor": "Social support", "contribution": 0.05},
      ]
    )

  @app.get("/api/checkin-breakdown")
  def checkin_breakdown():
    """Aggregated breakdowns for dashboard charts (relationship, substance, sleep, social)."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
      """
      SELECT relationship_status, COUNT(*) AS count
      FROM serenity_checkins
      WHERE relationship_status IS NOT NULL AND relationship_status != ''
      GROUP BY relationship_status
      ORDER BY count DESC
      """
    )
    by_relationship = [{"name": row["relationship_status"] or "Not set", "count": row["count"]} for row in cur.fetchall()]

    cur.execute(
      """
      SELECT substance_use, COUNT(*) AS count
      FROM serenity_checkins
      WHERE substance_use IS NOT NULL AND substance_use != ''
      GROUP BY substance_use
      ORDER BY count DESC
      """
    )
    by_substance = [{"name": row["substance_use"] or "Not set", "count": row["count"]} for row in cur.fetchall()]

    cur.execute(
      """
      SELECT sleep_quality, COUNT(*) AS count
      FROM serenity_checkins
      WHERE sleep_quality IS NOT NULL
      GROUP BY sleep_quality
      ORDER BY sleep_quality
      """
    )
    by_sleep = [{"name": f"Sleep {row['sleep_quality']}", "value": row["sleep_quality"], "count": row["count"]} for row in cur.fetchall()]

    cur.execute(
      """
      SELECT social_support, COUNT(*) AS count
      FROM serenity_checkins
      WHERE social_support IS NOT NULL
      GROUP BY social_support
      ORDER BY social_support
      """
    )
    by_social = [{"name": f"Support {row['social_support']}", "value": row["social_support"], "count": row["count"]} for row in cur.fetchall()]

    cur.execute(
      """
      SELECT AVG(sleep_quality) AS avg_sleep, AVG(social_support) AS avg_social
      FROM serenity_checkins
      WHERE sleep_quality IS NOT NULL AND social_support IS NOT NULL
      """
    )
    row = cur.fetchone()
    conn.close()

    avg_sleep = round(row["avg_sleep"] or 0, 1)
    avg_social = round(row["avg_social"] or 0, 1)

    return jsonify({
      "by_relationship": by_relationship,
      "by_substance": by_substance,
      "by_sleep": by_sleep,
      "by_social": by_social,
      "avg_sleep": avg_sleep,
      "avg_social": avg_social,
    })

  # Mount Gemini story endpoint at /api/story/generate
  app.register_blueprint(gemini_bp)
  from routes.report_routes import report_bp
  app.register_blueprint(report_bp)
  return app


app = create_app()


if __name__ == "__main__":
  port = int(os.getenv("PORT", "8000"))
  app.run(host="0.0.0.0", port=port, debug=True)

