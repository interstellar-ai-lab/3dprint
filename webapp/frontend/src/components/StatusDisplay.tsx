import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  ClockIcon,
  DocumentTextIcon,
  ChatBubbleLeftIcon
} from '@heroicons/react/24/outline';
import { useGenerationStore } from '../stores/generationStore';
import { getSessionStatus } from '../api/generationApi';
import { ImageGrid } from './ImageGrid';
import { FeedbackPrompt } from './FeedbackPrompt';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://vicino.ai';

export const StatusDisplay: React.FC = () => {
  const { currentSession, updateSession } = useGenerationStore();
  const [iterationFeedback, setIterationFeedback] = useState<Record<number, string>>({});

  const { data: sessionData } = useQuery(
    ['session', currentSession?.session_id],
    () => getSessionStatus(currentSession!.session_id),
    {
      enabled: !!currentSession?.session_id,
      refetchInterval: currentSession?.status === 'running' ? 2000 : false,
      onSuccess: (data) => {
        console.log('Session data received:', data);
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
      case 'waiting_for_feedback':
        return <ChatBubbleLeftIcon className="w-6 h-6 text-blue-500" />;
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
      case 'waiting_for_feedback':
        return 'text-blue-600';
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
                {currentSession.status === 'waiting_for_feedback' && 'Waiting for Feedback'}
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
                  <div className="flex items-center space-x-2">
                    {/* Progress indicator for current iteration */}
                    {currentSession.status === 'running' && 
                     iteration.iteration === currentSession.current_iteration && (
                      <div className="flex items-center space-x-1 text-blue-600">
                        <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-xs font-medium">In Progress</span>
                      </div>
                    )}
                  </div>
                  <span className="text-sm font-medium text-gray-700">
                    Iteration {iteration.iteration}
                  </span>
                </div>

                {/* Image Display */}
                <ImageGrid 
                  imageUrl={`${API_BASE_URL}/api/image/${currentSession.session_id}/${iteration.iteration}`}
                  originalUrl={iteration.image_url}
                  sessionId={currentSession.session_id}
                  iteration={iteration.iteration}
                  targetObject={currentSession.target_object}
                  isGenerating={
                    currentSession.status === 'running' && 
                    iteration.iteration === currentSession.current_iteration &&
                    !iteration.image_url
                  }
                />

                {/* User Feedback Section */}
                {currentSession.session_id && iteration.iteration && (
                  <div className="mt-6">
                    {currentSession.status === 'waiting_for_feedback' && 
                     iteration.iteration === currentSession.current_iteration && 
                     currentSession.feedback_prompt ? (
                      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                        <FeedbackPrompt
                          sessionId={currentSession.session_id}
                          feedbackPrompt={currentSession.feedback_prompt}
                          onFeedbackSubmitted={(feedback: string) => {
                            console.log('Feedback submitted for iteration', iteration.iteration, feedback);
                            setIterationFeedback(prev => ({
                              ...prev,
                              [iteration.iteration]: feedback
                            }));
                          }}
                        />
                      </div>
                    ) : iterationFeedback[iteration.iteration] ? (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-start space-x-3">
                          <ChatBubbleLeftIcon className="w-5 h-5 text-green-600 mt-0.5" />
                          <div className="flex-1">
                            <h5 className="font-semibold text-green-800 mb-2">
                              Your Feedback (Iteration {iteration.iteration})
                            </h5>
                            <p className="text-green-700 text-sm">
                              {iterationFeedback[iteration.iteration]}
                            </p>
                            <p className="text-green-600 text-xs mt-2">
                              This feedback will be incorporated into the next iteration.
                            </p>
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </div>
                )}

                {/* Next Generation Indicator - Show at bottom of previous iteration */}
                {currentSession.status === 'running' && 
                 iteration.iteration === currentSession.current_iteration - 1 && (
                  <div className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-5 h-5 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
                      <div>
                        <h5 className="font-semibold text-purple-800">Generating Next Iteration</h5>
                        <p className="text-purple-600 text-sm">
                          Creating iteration {currentSession.current_iteration} based on feedback...
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
