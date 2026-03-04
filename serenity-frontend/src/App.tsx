import { Route, Routes, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { CheckInPage } from './pages/CheckInPage';
import { StoryPage } from './pages/StoryPage';
import { TherapistDashboardPage } from './pages/TherapistDashboardPage';
import { GradientBackground } from './components/layout/GradientBackground';
import { Navbar } from './components/layout/Navbar';
import { Snowfall } from './components/visual/Snowfall';
import { useAppStore } from './store/useAppStore';

export default function App() {
  const location = useLocation();
  const initialized = useAppStore((s) => s.initialized);

  return (
    <GradientBackground>
      <Snowfall />
      <div className="min-h-screen flex flex-col text-slate-900 dark:text-slate-100 transition-colors duration-500">
        <Navbar />
        <main className="flex-1 flex items-stretch justify-center px-4 py-6 sm:px-6 lg:px-8">
          <div className="w-full max-w-6xl">
            <AnimatePresence mode="wait">
              <Routes location={location} key={location.pathname}>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/check-in" element={<CheckInPage />} />
                <Route path="/story" element={<StoryPage />} />
                <Route
                  path="/therapist"
                  element={<TherapistDashboardPage />}
                />
              </Routes>
            </AnimatePresence>
          </div>
        </main>
        {/* Simple footer */}
        <footer className="py-4 text-center text-xs text-slate-500 dark:text-slate-500/70">
          SERENITY • Built for gentle awareness, not diagnosis.
        </footer>
      </div>
    </GradientBackground>
  );
}

