## SERENITY – Mental Health Awareness Frontend & Gemini Backend

### Frontend (Vite + React + TS)

- **Install & run**
  - `cd serenity-frontend`
  - Copy env: `cp .env.example .env` and adjust `VITE_API_BASE_URL` to your backend (e.g. `http://localhost:8000`)
  - `npm install`
  - `npm run dev`

- **Tech**
  - Vite + React + TypeScript
  - Tailwind CSS (pastel gradients, glassmorphism)
  - Framer Motion (page and card animations)
  - React Router, Axios, Zustand, Recharts, Heroicons/Lucide

- **Key structure**
  - `src/App.tsx`: Routes and layout shell
  - `src/pages/*`: `LandingPage`, `LoginPage`, `RegisterPage`, `DashboardPage`, `CheckInPage`, `StoryPage`, `TherapistDashboardPage`
  - `src/services/api.ts`: REST API wrapper (auth, check-in, prediction, story)
  - `src/services/geminiService.ts`: Frontend helper that calls `/api/story/generate` and falls back to safe templates
  - `src/store/useAppStore.ts`: Global Zustand store (user, token, stress score, feature importance, check-in data)

### Backend Gemini Integration (Flask)

- **Files**
  - `backend/services/gemini_service.py`: Flask blueprint exposing `POST /api/story/generate`
  - `backend/.env.example`: Gemini configuration

- **Setup**
  - `cd backend`
  - Create and activate a virtualenv
  - `pip install flask google-generativeai python-dotenv`
  - Copy env: `cp .env.example .env` and set `GEMINI_API_KEY`
  - In your Flask app:
    ```python
    from flask import Flask
    from services.gemini_service import gemini_bp

    app = Flask(__name__)
    app.register_blueprint(gemini_bp)
    ```

### Story Flow

1. Student completes multi-step check-in on `CheckInPage`.
2. Frontend calls:
   - `POST /api/checkin`
   - `POST /api/predict` → `{ final_score, top_contributing_factor }`
3. Frontend then calls `POST /api/story/generate` via `generateSupportiveStory` helper.
4. `StoryPage` shows animated penguin story + reflection question and saves responses with `POST /api/story-response`.

