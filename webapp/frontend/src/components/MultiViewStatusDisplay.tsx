import React, { useState, useEffect } from 'react';
import { CheckCircleIcon, XCircleIcon, ClockIcon } from '@heroicons/react/24/outline';

interface MultiViewStatusDisplayProps {
  recordId: number;
  onComplete?: (data: any) => void;
  onStatusChange?: (status: string) => void;
}

interface StatusData {
  status: 'running' | 'completed' | 'failed' | 'timeout' | 'cancelled';
  task_id?: string;
  error_message?: string;
  model_3d_url?: string;
  updated_at?: string;
}

export const MultiViewStatusDisplay: React.FC<MultiViewStatusDisplayProps> = ({ 
  recordId, 
  onComplete,
  onStatusChange
}) => {
  // API base URL - adjust this according to your backend setup
  const API_BASE = process.env.REACT_APP_API_URL || 'https://vicino.ai';
  
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  const pollStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/generation-status/${recordId}`);
      
      if (!response.ok) {
        // Don't treat 500 errors as fatal during initial polling
        if (response.status === 500 && loading) {
          console.log('Server temporarily unavailable, will retry...');
          return; // Continue polling without setting error
        }
        throw new Error(`Failed to fetch status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Clear any previous errors
      setError(null);
      setStatusData(data);
      
      // Notify parent component of status change
      onStatusChange?.(data.status);
      
      // If completed or failed, stop polling
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'timeout' || data.status === 'cancelled') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        
        if (data.status === 'completed') {
          onComplete?.(data);
        }
      }
      
      setLoading(false);
    } catch (err) {
      // Don't set error immediately for network issues during initial polling
      if (loading) {
        console.log('Network error during initial polling, will retry...');
        return;
      }
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
      setLoading(false);
    }
  };

  useEffect(() => {
    // Add a small delay before starting polling to avoid race conditions
    const initialDelay = setTimeout(() => {
      pollStatus();
      
      // Set up polling interval
      const interval = setInterval(pollStatus, 5000); // Poll every 5 seconds
      setPollingInterval(interval);
    }, 2000); // 2 second delay
    
    return () => {
      clearTimeout(initialDelay);
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [recordId, pollStatus, pollingInterval]);

  const getStatusIcon = () => {
    if (!statusData) return <ClockIcon className="w-6 h-6 text-gray-400" />;
    
    switch (statusData.status) {
      case 'completed':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />;
      case 'failed':
      case 'timeout':
      case 'cancelled':
        return <XCircleIcon className="w-6 h-6 text-red-500" />;
      default:
        return <ClockIcon className="w-6 h-6 text-blue-500 animate-pulse" />;
    }
  };

  const getStatusText = () => {
    if (!statusData) return 'Checking status...';
    
    switch (statusData.status) {
      case 'running':
        return 'Generating 3D model...';
      case 'completed':
        return '3D model generated successfully!';
      case 'failed':
        return 'Generation failed';
      case 'timeout':
        return 'Generation timed out';
      case 'cancelled':
        return 'Generation was cancelled';
      default:
        return 'Unknown status';
    }
  };

  const getProgressPercentage = () => {
    if (!statusData) return 0;
    
    switch (statusData.status) {
      case 'running':
        return 50; // Indeterminate progress
      case 'completed':
        return 100;
      case 'failed':
      case 'timeout':
      case 'cancelled':
        return 0;
      default:
        return 0;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-md">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
          <div>
            <span className="text-gray-700">Initializing 3D generation...</span>
            <p className="text-sm text-gray-500 mt-1">Please wait while we set up your generation task</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <XCircleIcon className="w-5 h-5 text-red-500" />
          <span className="text-red-700">Error: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg p-6 shadow-md">
      <div className="space-y-4">
        {/* Status Header */}
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Multi-View 3D Generation
            </h3>
            <p className="text-sm text-gray-600">{getStatusText()}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${
              statusData?.status === 'completed' 
                ? 'bg-green-500' 
                : statusData?.status === 'failed' || statusData?.status === 'timeout' || statusData?.status === 'cancelled'
                ? 'bg-red-500'
                : 'bg-blue-500'
            }`}
            style={{ width: `${getProgressPercentage()}%` }}
          ></div>
        </div>

        {/* Status Details */}
        {statusData && (
          <div className="text-sm text-gray-600 space-y-1">
            {statusData.updated_at && (
              <p>Last Updated: {new Date(statusData.updated_at).toLocaleString()}</p>
            )}
            {statusData.error_message && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                <p className="text-red-700 text-sm">{statusData.error_message}</p>
              </div>
            )}
          </div>
        )}

        {/* Success Actions */}
        {statusData?.status === 'completed' && statusData.model_3d_url && (
          <div className="mt-4 space-y-2">
            <h4 className="font-medium text-gray-900">Your 3D Model is Ready!</h4>
            <div className="flex space-x-2">
              <a
                href={statusData.model_3d_url}
                download
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
              >
                📥 Download GLB
              </a>
              <button
                onClick={() => {
                  // Open in Studio
                  const baseUrl = process.env.REACT_APP_BASE_URL || window.location.origin;
                  window.open(`${baseUrl}/studio`, '_blank');
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
              >
                🎨 View 3D in Studio
              </button>
            </div>
          </div>
        )}

        {/* Retry Button for Failed Jobs */}
        {(statusData?.status === 'failed' || statusData?.status === 'timeout') && (
          <div className="mt-4">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm"
            >
              🔄 Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
