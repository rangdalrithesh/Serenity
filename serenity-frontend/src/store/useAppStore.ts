import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type User = {
  id: string;
  name: string;
  email: string;
  role?: 'student' | 'therapist' | 'admin';
};

export type FeatureImportance = {
  factor: string;
  contribution: number;
}[];

export type CheckInData = {
  bingeEpisodes?: number;
  courseStressLevel?: number;
  narrativeText?: string;
  createdAt?: string;
};

export type Theme = 'light' | 'dark';

type AppState = {
  initialized: boolean;
  theme: Theme;
  user: User | null;
  token: string | null;
  stressScore: number | null;
  featureImportance: FeatureImportance;
  checkinData: CheckInData | null;
  setTheme: (theme: Theme) => void;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setStressScore: (score: number | null) => void;
  setFeatureImportance: (fi: FeatureImportance) => void;
  setCheckinData: (data: CheckInData | null) => void;
  logout: () => void;
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      initialized: true,
      theme: 'dark',
      user: null,
      token: null,
      stressScore: null,
      featureImportance: [],
      checkinData: null,
      setTheme: (theme) => set({ theme }),
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      setStressScore: (stressScore) => set({ stressScore }),
      setFeatureImportance: (featureImportance) => set({ featureImportance }),
      setCheckinData: (checkinData) => set({ checkinData }),
      logout: () =>
        set({
          user: null,
          token: null,
          stressScore: null,
          featureImportance: [],
          checkinData: null,
        }),
    }),
    {
      name: 'serenity-app-store',
      partialize: (state) => ({
        theme: state.theme,
        user: state.user,
        token: state.token,
        stressScore: state.stressScore,
        featureImportance: state.featureImportance,
        checkinData: state.checkinData,
      }),
    },
  ),
);

