import React, { useState } from 'react';
import { useMutation } from 'react-query';
import { ChatBubbleLeftIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';
import { submitFeedback } from '../api/generationApi';
import { useGenerationStore } from '../stores/generationStore';

interface FeedbackPromptProps {
  sessionId: string;
  feedbackPrompt: string;
  onFeedbackSubmitted: (feedback: string) => void;
}

export const FeedbackPrompt: React.FC<FeedbackPromptProps> = ({ 
  sessionId, 
  feedbackPrompt, 
  onFeedbackSubmitted 
}) => {
  const [feedback, setFeedback] = useState('');
  const [creditError, setCreditError] = useState<string | null>(null);
  const { updateSession } = useGenerationStore();

  const feedbackMutation = useMutation(
    ({ sessionId, feedback }: { sessionId: string; feedback: string }) => 
      submitFeedback(sessionId, feedback),
    {
      onSuccess: (data) => {
        updateSession({ status: 'running', user_feedback: feedback });
        onFeedbackSubmitted(feedback);
        setCreditError(null);
      },
      onError: (error: any) => {
        console.error('Failed to submit feedback:', error);
        
        // Handle credit-related errors
        if (error.response?.status === 402) {
          setCreditError(error.response.data.message || 'Insufficient credits. Please add funds to your wallet.');
        } else if (error.response?.status === 401) {
          setCreditError('Authentication required. Please sign in again.');
        } else {
          setCreditError(error.response?.data?.error || error.message || 'Failed to submit feedback');
        }
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCreditError(null);
    if (feedback.trim()) {
      feedbackMutation.mutate({ sessionId, feedback: feedback.trim() });
    } else {
      // If no feedback provided, just continue
      feedbackMutation.mutate({ sessionId, feedback: '' });
    }
  };

  const handleSkip = () => {
    setCreditError(null);
    feedbackMutation.mutate({ sessionId, feedback: '' });
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-2xl shadow-lg p-6 mb-6">
      <div className="flex items-start space-x-3 mb-4">
        <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
          <ChatBubbleLeftIcon className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            💬 Your Feedback Needed
          </h3>
          <p className="text-gray-600 mb-4">
            {feedbackPrompt}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="feedback" className="block text-sm font-medium text-gray-700 mb-2">
            Your Suggestions (Optional)
          </label>
          <textarea
            id="feedback"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="e.g., Make the dog more realistic, Change the background to a park, Adjust the lighting..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors resize-none"
            rows={3}
          />
          <p className="mt-2 text-sm text-gray-500">
            Your feedback will be incorporated into the next iteration to improve the result.
          </p>
        </div>

        {/* Pricing Information */}
        {/* <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700">Feedback submission cost:</span>
            <span className="text-sm font-semibold text-blue-800">$0.10</span>
          </div>
          <p className="text-xs text-blue-600 mt-1">
            This helps improve the next generation iteration.
          </p>
        </div> */}

        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={feedbackMutation.isLoading}
            className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
            <span>
              {feedbackMutation.isLoading ? 'Submitting...' : 'Submit Feedback & Continue'}
            </span>
          </button>
          
          <button
            type="button"
            onClick={handleSkip}
            disabled={feedbackMutation.isLoading}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            Skip & Continue
          </button>
        </div>
      </form>

      {/* Credit Error Display */}
      {creditError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-red-700 text-sm">{creditError}</p>
              {creditError.includes('credits') && (
                <button
                  onClick={() => window.location.href = '/#wallet'}
                  className="mt-1 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Add funds to wallet
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* General Error Display */}
      {feedbackMutation.isError && !creditError && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">
            Error: {feedbackMutation.error?.message || 'Failed to submit feedback'}
          </p>
        </div>
      )}
    </div>
  );
};
