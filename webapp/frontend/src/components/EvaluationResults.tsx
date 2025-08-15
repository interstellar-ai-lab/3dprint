import React from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ChatBubbleLeftIcon
} from '@heroicons/react/24/outline';
import { FeedbackPrompt } from './FeedbackPrompt';

interface EvaluationResultsProps {
  evaluation?: {
    scores: Record<string, number>;
    issues: string[];
    suggestions: string[];
  };
  sessionId?: string;
  iteration?: number;
  isWaitingForFeedback?: boolean;
  feedbackPrompt?: string;
  userFeedback?: string;
  onFeedbackSubmitted?: (feedback: string) => void;
  isEvaluating?: boolean;
}

export const EvaluationResults: React.FC<EvaluationResultsProps> = ({ 
  evaluation, 
  sessionId, 
  iteration, 
  isWaitingForFeedback, 
  feedbackPrompt, 
  userFeedback, 
  onFeedbackSubmitted,
  isEvaluating = false
}) => {
  const getScoreLabel = (score: number) => {
    if (score >= 9.0) return 'Perfect';
    if (score >= 8.0) return 'Good';
    if (score >= 6.0) return 'Acceptable';
    return 'Poor';
  };

  const getScoreColor = (score: number) => {
    if (score >= 9.0) return 'text-green-600 bg-green-50';
    if (score >= 8.0) return 'text-blue-600 bg-blue-50';
    if (score >= 6.0) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 9.0) return <CheckCircleIcon className="w-4 h-4" />;
    if (score >= 8.0) return <InformationCircleIcon className="w-4 h-4" />;
    if (score >= 6.0) return <ExclamationTriangleIcon className="w-4 h-4" />;
    return <ExclamationTriangleIcon className="w-4 h-4" />;
  };

  const formatMetricName = (metric: string) => {
    return metric
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase());
  };

  // Show evaluation progress if evaluation is not ready yet
  if (isEvaluating) {
    return (
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center space-x-3">
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <div>
            <h5 className="font-semibold text-blue-800">Evaluating Image</h5>
            <p className="text-blue-600 text-sm">Analyzing quality and generating suggestions...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show evaluation results if available
  if (!evaluation) {
    return null;
  }

  return (
    <div className="mt-4 space-y-4">
      {/* Scores */}
      <div>
        {/* Metrics section hidden - all metrics filtered out */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(evaluation.scores)
            .filter(([metric]) => false) // Hide all metrics
            .map(([metric, score]) => (
              <div
                key={metric}
                className={`p-3 rounded-lg border ${getScoreColor(score)}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    {formatMetricName(metric)}
                  </span>
                  {getScoreIcon(score)}
                </div>
                <div className="text-lg font-bold mt-1">
                  {getScoreLabel(score)}
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Suggestions */}
      {evaluation.suggestions.length > 0 && (
        <div>
          <h5 className="font-semibold text-gray-800 mb-3 flex items-center space-x-2">
            <InformationCircleIcon className="w-5 h-5 text-blue-500" />
            <span>Suggestions for Improvement</span>
          </h5>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <ul className="space-y-2">
              {evaluation.suggestions.map((suggestion, index) => (
                <li key={index} className="text-blue-700 text-sm flex items-start space-x-2">
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* User Feedback Section */}
      {sessionId && iteration && (
        <div className="mt-6">
          {isWaitingForFeedback && feedbackPrompt ? (
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
              <FeedbackPrompt
                sessionId={sessionId}
                feedbackPrompt={feedbackPrompt}
                onFeedbackSubmitted={(feedback: string) => {
                  if (onFeedbackSubmitted) {
                    onFeedbackSubmitted(feedback);
                  }
                }}
              />
            </div>
          ) : userFeedback ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <ChatBubbleLeftIcon className="w-5 h-5 text-green-600 mt-0.5" />
                <div className="flex-1">
                  <h5 className="font-semibold text-green-800 mb-2">
                    Your Feedback (Iteration {iteration})
                  </h5>
                  <p className="text-green-700 text-sm">
                    {userFeedback}
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
    </div>
  );
};
