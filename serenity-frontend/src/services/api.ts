import axios from 'axios';
import { useAppStore } from '../store/useAppStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  
});

api.interceptors.request.use((config) => {
  const token = useAppStore.getState().token;
  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    };
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    // Simple centralized logging; UI components surface user-facing messages.
    console.error('API error', error);
    return Promise.reject(error);
  },
);

export type LoginPayload = { email: string; password: string };
export type RegisterPayload = {
  name: string;
  email: string;
  password: string;
};

export const AuthService = {
  async login(payload: LoginPayload) {
    const { data } = await api.post('/api/auth/login', payload);
    return data as { token: string; user: unknown };
  },
  async register(payload: RegisterPayload) {
    const { data } = await api.post('/api/auth/register', payload);
    return data as { token: string; user: unknown };
  },
  async profile() {
    const { data } = await api.get('/api/user/profile');
    return data;
  },
};

export const CheckinService = {
  async submitCheckin(payload: unknown) {
    const { data } = await api.post('/api/checkin', payload);
    return data;
  },
  async predict(payload: unknown) {
    const { data } = await api.post('/api/predict', payload);
    return data as {
      final_score: number;
      top_contributing_factor: string;
    };
  },
  async stressTrend() {
    const { data } = await api.get('/api/stress-trend');
    return data as Array<{ date: string; score: number }>;
  },
  async featureImportance() {
    const { data } = await api.get('/api/feature-importance');
    return data as Array<{ factor: string; contribution: number }>;
  },
  async checkinBreakdown() {
    const { data } = await api.get('/api/checkin-breakdown');
    return data as {
      by_relationship: Array<{ name: string; count: number }>;
      by_substance: Array<{ name: string; count: number }>;
      by_sleep: Array<{ name: string; value: number; count: number }>;
      by_social: Array<{ name: string; value: number; count: number }>;
      avg_sleep: number;
      avg_social: number;
    };
  },
};

export const StoryService = {
  async generate(payload: {
    user_id: string;
    stress_score: number;
    top_contributing_factor: string;
    emotional_context: string;
  }) {
    const { data } = await api.post('/api/story/generate', payload);
    return data as { story_text: string; suggested_reflection_question: string };
  },
  async saveResponse(payload: {
    user_id: string;
    stress_score: number;
    reflection_answer: string;
  }) {
    const { data } = await api.post('/api/story-response', payload);
    return data;
  },
};

export default api;

