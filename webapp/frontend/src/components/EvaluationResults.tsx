import React from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon 
} from '@heroicons/react/24/outline';

interface EvaluationResultsProps {
  evaluation: {
    scores: Record<string, number>;
    issues: string[];
    suggestions: string[];
  };
}

export const EvaluationResults: React.FC<EvaluationResultsProps> = ({ evaluation }) => {
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

  return (
    <div className="mt-4 space-y-4">
      {/* Scores */}
      <div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(evaluation.scores)
            .filter(([metric]) => !metric.toLowerCase().includes('overall'))
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
    </div>
  );
};
