import React from 'react';
import { useQuery } from 'react-query';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  ClockIcon,
  EyeIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { useGenerationStore } from '../stores/generationStore';
import { getSessionStatus } from '../api/generationApi';
import { ImageGrid } from './ImageGrid';
import { EvaluationResults } from './EvaluationResults';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://vicino.ai';

export const StatusDisplay: React.FC = () => {
  const { currentSession, updateSession } = useGenerationStore();

  const { data: sessionData } = useQuery(
    ['session', currentSession?.session_id],
    () => getSessionStatus(currentSession!.session_id),
    {
      enabled: !!currentSession?.session_id,
      refetchInterval: currentSession?.status === 'running' ? 2000 : false,
      onSuccess: (data) => {
        updateSession(data);
      },
    }
  );

  if (!currentSession) return null;

  const getStatusIcon = () => {
    switch (currentSession.status) {
      case 'completed':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />;
      default:
        return <ClockIcon className="w-6 h-6 text-blue-500 animate-spin" />;
    }
  };

  const getStatusColor = () => {
    switch (currentSession.status) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-blue-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <h3 className="text-xl font-semibold text-gray-800">
                Generation Status
              </h3>
              <p className={`text-sm font-medium ${getStatusColor()}`}>
                {currentSession.status === 'running' && 'In Progress'}
                {currentSession.status === 'completed' && 'Completed'}
                {currentSession.status === 'failed' && 'Failed'}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Target Object</p>
            <p className="font-semibold text-gray-800">{currentSession.target_object}</p>
          </div>
        </div>

        {/* Progress Bar */}
        {currentSession.status === 'running' && (
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Iteration {currentSession.current_iteration} of {currentSession.max_iterations}</span>
              <span>{Math.round((currentSession.current_iteration / currentSession.max_iterations) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(currentSession.current_iteration / currentSession.max_iterations) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Evaluation Status */}
        {currentSession.evaluation_status && (
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <EyeIcon className="w-4 h-4" />
            <span>{currentSession.evaluation_status}</span>
          </div>
        )}

        {/* Final Score */}
        {currentSession.status === 'completed' && currentSession.final_score > 0 && (
          <div className="mt-4 p-4 bg-green-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-green-800">Generation Completed</span>
              <span className="text-2xl font-bold text-green-600">
                ✅ Success
              </span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {currentSession.status === 'failed' && currentSession.error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{currentSession.error}</p>
          </div>
        )}
      </div>

      {/* Iterations Display */}
      {currentSession.iterations && currentSession.iterations.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center space-x-2">
            <DocumentTextIcon className="w-5 h-5" />
          </h3>
          
          <div className="space-y-6">
            {currentSession.iterations.map((iteration, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-500">
                    {iteration.evaluation_status}
                  </span>
                </div>

                {/* Image Display */}
                <ImageGrid 
                  imageUrl={`${API_BASE_URL}/api/image/${currentSession.session_id}/${iteration.iteration}`}
                  originalUrl={iteration.image_url}
                  sessionId={currentSession.session_id}
                  iteration={iteration.iteration}
                  targetObject={currentSession.target_object}
                />

                {/* Evaluation Results */}
                {iteration.evaluation && (
                  <EvaluationResults evaluation={iteration.evaluation} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
