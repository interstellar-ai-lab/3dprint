import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface GenerationSession {
  session_id: string;
  status: 'running' | 'completed' | 'failed' | 'stopped' | 'waiting_for_feedback';
  target_object: string;
  mode: string;
  max_iterations: number;
  current_iteration: number;
  iterations: IterationResult[];
  error?: string;
  feedback_prompt?: string;
  user_feedback?: string;
}

export interface IterationResult {
  iteration: number;
  image_url: string;
}

// AI Image Edit state interface
export interface AIImageEditState {
  selectedImage: File | null;
  referenceImages: File[];
  imagePreview: string;
  referencePreviews: string[];
  instruction: string;
  result: EditResult | null;
  isProcessing: boolean;
  error: string;
  dragActive: boolean;
}

// Persistable state (without File objects)
export interface PersistableAIImageEditState {
  imagePreview: string;
  referencePreviews: string[];
  instruction: string;
  result: EditResult | null;
  error: string;
}

export interface EditResult {
  success: boolean;
  image?: string;
  filename?: string;
  timestamp?: string;
  error?: string;
}

interface GenerationStore {
  currentSession: GenerationSession | null;
  setCurrentSession: (session: GenerationSession | null) => void;
  updateSession: (updates: Partial<GenerationSession>) => void;
  clearSession: () => void;
  
  // AI Image Edit state
  aiImageEdit: AIImageEditState;
  setSelectedImage: (image: File | null) => void;
  setReferenceImages: (images: File[]) => void;
  setImagePreview: (preview: string) => void;
  setReferencePreviews: (previews: string[]) => void;
  setInstruction: (instruction: string) => void;
  setResult: (result: EditResult | null) => void;
  setIsProcessing: (processing: boolean) => void;
  setError: (error: string) => void;
  setDragActive: (active: boolean) => void;
  resetAIImageEdit: () => void;
  addReferenceImage: (image: File, preview: string) => void;
  removeReferenceImage: (index: number) => void;
}

export const useGenerationStore = create<GenerationStore>()(
  persist(
    (set, get) => ({
      currentSession: null,
      setCurrentSession: (session) => set({ currentSession: session }),
      updateSession: (updates) =>
        set((state) => ({
          currentSession: state.currentSession
            ? { ...state.currentSession, ...updates }
            : null,
        })),
      clearSession: () => set({ currentSession: null }),
      
      // AI Image Edit state management
      aiImageEdit: {
        selectedImage: null,
        referenceImages: [],
        imagePreview: '',
        referencePreviews: [],
        instruction: 'Create a 1/7 scale commercialized figure of thecharacter in the illustration, in a realistic styie and environment. Place the figure on a computer desk, using a circular transparent acrylic base without any text.On the computer screen, display the ZBrush modeling process of the figure. Next to the computer screen, place a BANDAl-style toy packaging box printedwith the original artwork',
        result: null,
        isProcessing: false,
        error: '',
        dragActive: false,
      },
      
      setSelectedImage: (image) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, selectedImage: image }
      })),
      
      setReferenceImages: (images) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, referenceImages: images }
      })),
      
      setImagePreview: (preview) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, imagePreview: preview }
      })),
      
      setReferencePreviews: (previews) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, referencePreviews: previews }
      })),
      
      setInstruction: (instruction) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, instruction }
      })),
      
      setResult: (result) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, result }
      })),
      
      setIsProcessing: (isProcessing) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, isProcessing }
      })),
      
      setError: (error) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, error }
      })),
      
      setDragActive: (dragActive) => set((state) => ({
        aiImageEdit: { ...state.aiImageEdit, dragActive }
      })),
      
      resetAIImageEdit: () => set((state) => ({
        aiImageEdit: {
          selectedImage: null,
          referenceImages: [],
          imagePreview: '',
          referencePreviews: [],
          instruction: 'Create a 1/7 scale commercialized figure of thecharacter in the illustration, in a realistic styie and environment. Place the figure on a computer desk, using a circular transparent acrylic base without any text.On the computer screen, display the ZBrush modeling process of the figure. Next to the computer screen, place a BANDAl-style toy packaging box printedwith the original artwork',
          result: null,
          isProcessing: false,
          error: '',
          dragActive: false,
        }
      })),
      
      addReferenceImage: (image, preview) => set((state) => ({
        aiImageEdit: {
          ...state.aiImageEdit,
          referenceImages: [...state.aiImageEdit.referenceImages, image],
          referencePreviews: [...state.aiImageEdit.referencePreviews, preview]
        }
      })),
      
      removeReferenceImage: (index) => set((state) => ({
        aiImageEdit: {
          ...state.aiImageEdit,
          referenceImages: state.aiImageEdit.referenceImages.filter((_, i) => i !== index),
          referencePreviews: state.aiImageEdit.referencePreviews.filter((_, i) => i !== index)
        }
      })),
    }),
    {
      name: 'generation-store',
      // Only persist the serializable parts of AI Image Edit state
      partialize: (state) => ({
        aiImageEdit: {
          selectedImage: null, // Don't persist File objects
          referenceImages: [], // Don't persist File objects
          imagePreview: state.aiImageEdit.imagePreview,
          referencePreviews: state.aiImageEdit.referencePreviews,
          instruction: state.aiImageEdit.instruction,
          result: state.aiImageEdit.result,
          isProcessing: false, // Don't persist processing state
          error: state.aiImageEdit.error,
          dragActive: false, // Don't persist drag state
        }
      }),
    }
  )
);
