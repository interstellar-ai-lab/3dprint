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
  const { updateSession } = useGenerationStore();

  const feedbackMutation = useMutation(
    ({ sessionId, feedback }: { sessionId: string; feedback: string }) => 
      submitFeedback(sessionId, feedback),
    {
      onSuccess: (data) => {
        updateSession({ status: 'running', user_feedback: feedback });
        onFeedbackSubmitted(feedback);
      },
      onError: (error: any) => {
        console.error('Failed to submit feedback:', error);
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (feedback.trim()) {
      feedbackMutation.mutate({ sessionId, feedback: feedback.trim() });
    } else {
      // If no feedback provided, just continue
      feedbackMutation.mutate({ sessionId, feedback: '' });
    }
  };

  const handleSkip = () => {
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

      {feedbackMutation.isError && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm">
            Error: {feedbackMutation.error?.message || 'Failed to submit feedback'}
          </p>
        </div>
      )}
    </div>
  );
};
