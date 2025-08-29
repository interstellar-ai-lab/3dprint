import axios from 'axios';
import { GenerationSession } from '../stores/generationStore';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://vicino.ai';

// Create axios instance with auth interceptor
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor to include token in requests
api.interceptors.request.use(async (config) => {
  try {
    const { data: { session } } = await import('../lib/supabase').then(m => m.supabase.auth.getSession());
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
  } catch (error) {
    console.error('Failed to get auth token:', error);
  }
  return config;
});

export interface GenerationRequest {
  target_object: string;
  mode: 'quick' | 'deep';
  image_size?: string;
}

export const startGeneration = async (request: GenerationRequest): Promise<GenerationSession> => {
  const response = await api.post('/api/generate', request);
  return response.data;
};

export const stopGeneration = async (sessionId: string): Promise<{ session_id: string; status: string; message: string }> => {
  const response = await api.post(`/api/stop/${sessionId}`);
  return response.data;
};

export const submitFeedback = async (sessionId: string, feedback: string): Promise<{ session_id: string; status: string; message: string }> => {
  const response = await api.post(`/api/feedback/${sessionId}`, { feedback });
  return response.data;
};

export const getSessionStatus = async (sessionId: string): Promise<GenerationSession> => {
  const response = await api.get(`/api/status/${sessionId}`);
  return response.data;
};

export const getIterationImage = async (sessionId: string, iteration: number): Promise<string> => {
  const response = await api.get(`/api/image/${sessionId}/${iteration}`, {
    responseType: 'blob',
  });
  return URL.createObjectURL(response.data);
};

export const listSessions = async (): Promise<GenerationSession[]> => {
  const response = await api.get('/api/sessions');
  return response.data.sessions;
};

export const healthCheck = async (): Promise<{ status: string; timestamp: string }> => {
  const response = await api.get('/api/health');
  return response.data;
};

export const checkUserExists = async (email: string): Promise<{ exists: boolean; email: string }> => {
  const response = await api.post('/api/auth/check-user', { email });
  return response.data;
};
