import { create } from 'zustand';

export interface GenerationSession {
  session_id: string;
  status: 'running' | 'completed' | 'failed';
  target_object: string;
  mode: string;
  max_iterations: number;
  current_iteration: number;
  iterations: IterationResult[];
  final_score: number;
  error?: string;
  evaluation_status?: string;
}

export interface IterationResult {
  iteration: number;
  image_url: string;
  evaluation?: EvaluationResult;
  metadata_file?: string;
  evaluation_status: string;
}

export interface EvaluationResult {
  scores: Record<string, number>;
  issues: string[];
  suggestions: string[];
}

interface GenerationStore {
  currentSession: GenerationSession | null;
  setCurrentSession: (session: GenerationSession | null) => void;
  updateSession: (updates: Partial<GenerationSession>) => void;
  clearSession: () => void;
}

export const useGenerationStore = create<GenerationStore>((set) => ({
  currentSession: null,
  setCurrentSession: (session) => set({ currentSession: session }),
  updateSession: (updates) =>
    set((state) => ({
      currentSession: state.currentSession
        ? { ...state.currentSession, ...updates }
        : null,
    })),
  clearSession: () => set({ currentSession: null }),
}));
