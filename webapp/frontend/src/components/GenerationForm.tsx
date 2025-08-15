import React, { useState } from 'react';
import { useMutation } from 'react-query';
import { RocketLaunchIcon, StopIcon } from '@heroicons/react/24/outline';
import { useGenerationStore } from '../stores/generationStore';
import { startGeneration, stopGeneration } from '../api/generationApi';

export const GenerationForm: React.FC = () => {
  const [targetObject, setTargetObject] = useState('');
  const [mode, setMode] = useState<'quick' | 'deep'>('quick');
  const [imageSize, setImageSize] = useState('1024x1024');
  const { currentSession, setCurrentSession, updateSession } = useGenerationStore();

  const generationMutation = useMutation(startGeneration, {
    onSuccess: (data) => {
      setCurrentSession(data);
    },
    onError: (error: any) => {
      console.error('Generation failed:', error);
    },
  });

  const stopMutation = useMutation(stopGeneration, {
    onSuccess: (data) => {
      if (currentSession) {
        updateSession({ status: 'stopped', error: 'Generation stopped by user' });
      }
    },
    onError: (error: any) => {
      console.error('Failed to stop generation:', error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetObject.trim()) return;

    generationMutation.mutate({
      target_object: targetObject.trim(),
      mode,
      image_size: imageSize,
    });
  };

  const handleStop = () => {
    if (currentSession?.session_id) {
      stopMutation.mutate(currentSession.session_id);
    }
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

        {/* Image Size Selection */}
        <div>
          <label htmlFor="imageSize" className="block text-sm font-medium text-gray-700 mb-2">
            Image Size
          </label>
          <select
            id="imageSize"
            value={imageSize}
            onChange={(e) => setImageSize(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors"
          >
            <option value="1024x1024">📐 Square (1024×1024) - Good for most objects (default)</option>
            <option value="1024x1536">📏 Portrait (1024×1536) - Better for tall objects</option>
            <option value="1536x1024">📐 Landscape (1536×1024) - Better for wide objects</option>
          </select>
          <p className="mt-2 text-sm text-gray-600">
            {imageSize === '1024x1024' && 'Best for objects with similar width and height (e.g., coffee mugs, balls)'}
            {imageSize === '1024x1536' && 'Best for tall objects (e.g., people, buildings, trees, bottles)'}
            {imageSize === '1536x1024' && 'Best for wide objects (e.g., cars, furniture, animals, laptops)'}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-4">
          {/* Start/Stop Button */}
          {currentSession?.status === 'running' || currentSession?.status === 'waiting_for_feedback' ? (
            <button
              type="button"
              onClick={handleStop}
              disabled={stopMutation.isLoading}
              className="flex-1 bg-gradient-to-r from-red-600 to-red-700 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:from-red-700 hover:to-red-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <StopIcon className="w-6 h-6" />
              <span>
                {stopMutation.isLoading ? 'Stopping...' : '⏹️ Stop Generation'}
              </span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={generationMutation.isLoading || !targetObject.trim()}
              className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <RocketLaunchIcon className="w-6 h-6" />
              <span>
                {generationMutation.isLoading ? 'Starting Generation...' : '🚀 Start Generation'}
              </span>
            </button>
          )}
        </div>
      </form>

      {/* Status Display */}
      {currentSession && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-800 font-medium">
                Generation Status: {currentSession.status === 'waiting_for_feedback' ? 'Waiting for Feedback' : currentSession.status.charAt(0).toUpperCase() + currentSession.status.slice(1)}
              </p>
              {(currentSession.status === 'running' || currentSession.status === 'waiting_for_feedback') && (
                <p className="text-blue-600 text-sm">
                  Iteration {currentSession.current_iteration} of {currentSession.max_iterations}
                </p>
              )}
              {currentSession.error && (
                <p className="text-red-600 text-sm mt-1">
                  {currentSession.error}
                </p>
              )}
            </div>
            {currentSession.status === 'running' && (
              <div className="w-4 h-4 bg-blue-500 rounded-full animate-pulse"></div>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {(generationMutation.isError || stopMutation.isError) && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">
            Error: {(generationMutation.error || stopMutation.error)?.message || 'Operation failed'}
          </p>
        </div>
      )}
    </div>
  );
};
