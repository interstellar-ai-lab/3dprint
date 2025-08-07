import React, { useState } from 'react';
import { useMutation } from 'react-query';
import { RocketLaunchIcon } from '@heroicons/react/24/outline';
import { useGenerationStore } from '../stores/generationStore';
import { startGeneration } from '../api/generationApi';

export const GenerationForm: React.FC = () => {
  const [targetObject, setTargetObject] = useState('');
  const [mode, setMode] = useState<'quick' | 'deep'>('quick');
  const { setCurrentSession } = useGenerationStore();

  const generationMutation = useMutation(startGeneration, {
    onSuccess: (data) => {
      setCurrentSession(data);
    },
    onError: (error: any) => {
      console.error('Generation failed:', error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetObject.trim()) return;

    generationMutation.mutate({
      target_object: targetObject.trim(),
      mode,
    });
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">
        Start 3D Generation
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Target Object Input */}
        <div>
          <label htmlFor="targetObject" className="block text-sm font-medium text-gray-700 mb-2">
            Target Object
          </label>
          <input
            type="text"
            id="targetObject"
            value={targetObject}
            onChange={(e) => setTargetObject(e.target.value)}
            placeholder="e.g., Golden Retriever, Coffee Mug, Sports Car"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors"
            required
          />
        </div>

        {/* Generation Mode Selection */}
        <div>
          <label htmlFor="mode" className="block text-sm font-medium text-gray-700 mb-2">
            Generation Mode
          </label>
          <select
            id="mode"
            value={mode}
            onChange={(e) => setMode(e.target.value as 'quick' | 'deep')}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors"
          >
            <option value="quick">🚀 Quick Mode (5 minutes)</option>
            <option value="deep">🧠 Deep Think Mode (20 minutes)</option>
          </select>
          <p className="mt-2 text-sm text-gray-600">
            {mode === 'quick' 
              ? 'Best for initial testing and rapid prototyping'
              : 'Best for production-quality results and final outputs'
            }
          </p>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={generationMutation.isLoading || !targetObject.trim()}
          className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2"
        >
          <RocketLaunchIcon className="w-6 h-6" />
          <span>
            {generationMutation.isLoading ? 'Starting Generation...' : '🚀 Start Generation'}
          </span>
        </button>
      </form>

      {/* Error Display */}
      {generationMutation.isError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">
            Error: {generationMutation.error?.message || 'Failed to start generation'}
          </p>
        </div>
      )}
    </div>
  );
};
