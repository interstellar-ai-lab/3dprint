import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { CheckCircleIcon, ExclamationTriangleIcon, ClockIcon } from '@heroicons/react/24/outline';

interface SingleImageStatusDisplayProps {
  recordId: number;
  onComplete?: (data: any) => void;
  onStatusChange?: (status: string) => void;
}

interface GenerationStatus {
  status: string;
  task_id?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export const SingleImageStatusDisplay: React.FC<SingleImageStatusDisplayProps> = ({
  recordId,
  onComplete,
  onStatusChange
}) => {
  const [pollingInterval, setPollingInterval] = useState(5000); // Start with 5 seconds

  const API_BASE = process.env.REACT_APP_API_URL || 'https://vicino.ai';

  const { data: statusData, error, isLoading } = useQuery(
    ['single-image-status', recordId],
    async (): Promise<GenerationStatus> => {
      const { data: { session } } = await import('../lib/supabase').then(m => m.supabase.auth.getSession());
      const token = session?.access_token;
      
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`${API_BASE}/api/generation-status/${recordId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }

      return response.json();
    },
    {
      refetchInterval: pollingInterval,
      refetchIntervalInBackground: true,
      retry: 3,
      retryDelay: 1000,
      onSuccess: (data) => {
        // Notify parent of status change
        onStatusChange?.(data.status);
        
        // If completed, stop polling and notify parent
        if (data.status === 'completed') {
          setPollingInterval(0); // Stop polling
          onComplete?.(data);
        } else if (data.status === 'failed') {
          setPollingInterval(0); // Stop polling
        }
      },
    }
  );

  const getStatusIcon = () => {
    if (isLoading) {
      return <ClockIcon className="w-6 h-6 text-gray-400 animate-pulse" />;
    }

    if (error) {
      return <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />;
    }

    switch (statusData?.status) {
      case 'pending':
        return <ClockIcon className="w-6 h-6 text-yellow-500 animate-pulse" />;
      case 'running':
        return <ClockIcon className="w-6 h-6 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />;
      default:
        return <ClockIcon className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    if (isLoading) return 'Loading status...';
    if (error) return 'Error loading status';

    switch (statusData?.status) {
      case 'pending':
        return 'Queued for processing...';
      case 'running':
        return 'Generating 3D model...';
      case 'completed':
        return '3D model generated successfully!';
      case 'failed':
        return 'Generation failed';
      default:
        return 'Unknown status';
    }
  };

  const getStatusDescription = () => {
    if (isLoading) return 'Fetching current status...';
    if (error) return 'Unable to load generation status. Please refresh the page.';

    switch (statusData?.status) {
      case 'pending':
        return 'Your image is in the queue and will be processed shortly.';
      case 'running':
        return 'Our AI is analyzing your image and creating a detailed 3D model. This may take a few minutes.';
      case 'completed':
        return 'Your 3D model is ready! Click the button above to view it in the studio.';
      case 'failed':
        return statusData.error_message || 'The generation process encountered an error. Please try again.';
      default:
        return 'Processing your request...';
    }
  };

  const getProgressPercentage = () => {
    if (isLoading || error) return 0;
    
    switch (statusData?.status) {
      case 'pending':
        return 10;
      case 'running':
        return 60;
      case 'completed':
        return 100;
      case 'failed':
        return 0;
      default:
        return 0;
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          {getStatusIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {getStatusText()}
          </h3>
          
          <p className="text-sm text-gray-600 mb-4">
            {getStatusDescription()}
          </p>

          {/* Progress Bar */}
          {statusData?.status === 'running' && (
            <div className="mb-4">
              <div className="bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-1000 ease-out"
                  style={{ width: `${getProgressPercentage()}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Progress: {getProgressPercentage()}%
              </p>
            </div>
          )}

          {/* Task ID */}
          {statusData?.task_id && (
            <div className="text-xs text-gray-500">
              Task ID: {statusData.task_id}
            </div>
          )}

          {/* Error Details */}
          {statusData?.status === 'failed' && statusData.error_message && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-700">
                <strong>Error:</strong> {statusData.error_message}
              </p>
            </div>
          )}

          {/* Timestamps */}
          <div className="mt-4 text-xs text-gray-400 space-y-1">
            {statusData?.created_at && (
              <div>Started: {new Date(statusData.created_at).toLocaleString()}</div>
            )}
            {statusData?.updated_at && statusData.updated_at !== statusData.created_at && (
              <div>Last updated: {new Date(statusData.updated_at).toLocaleString()}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
