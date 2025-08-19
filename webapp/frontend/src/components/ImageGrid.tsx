import React, { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, CubeIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://vicino.ai';

interface ImageGridProps {
  imageUrl: string;
  originalUrl?: string;
  sessionId?: string;
  iteration?: number;
  targetObject?: string;
  isGenerating?: boolean;
}

export const ImageGrid: React.FC<ImageGridProps> = ({ imageUrl, originalUrl, sessionId, iteration, targetObject, isGenerating = false }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isGenerating3D, setIsGenerating3D] = useState(false);
  const [threeDModelUrl, setThreeDModelUrl] = useState<string | null>(null);
  const [generationStatus, setGenerationStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');
  const [recordId, setRecordId] = useState<number | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [creditError, setCreditError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  // Cleanup polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  const handleImageLoad = () => {
    setIsLoading(false);
    setHasError(false);
  };

  const handleImageError = (error: any) => {
    console.error('Image load error:', error);
    setIsLoading(false);
    setHasError(true);
  };

  const pollJobStatus = async (recordId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/generation-status/${recordId}`);
      if (response.ok) {
        const status = await response.json();
        console.log('Polling status for record', recordId, ':', status.status);
        
        switch (status.status) {
          case 'completed':
            console.log('✅ 3D generation completed!');
            setGenerationStatus('completed');
            setThreeDModelUrl(status['3d_url']);
            setIsGenerating3D(false);
            // Clear polling interval
            if (pollingInterval) {
              clearInterval(pollingInterval);
              setPollingInterval(null);
            }
            break;
            
          case 'failed':
          case 'cancelled':
          case 'timeout':
            console.log('❌ 3D generation failed:', status.error_message);
            setGenerationStatus('failed');
            setIsGenerating3D(false);
            // Clear polling interval
            if (pollingInterval) {
              clearInterval(pollingInterval);
              setPollingInterval(null);
            }
            break;
            
          case 'running':
            console.log('🔄 3D generation still running...');
            setGenerationStatus('running');
            // Continue polling
            break;
            
          default:
            console.log('Unknown status:', status.status);
            break;
        }
      } else {
        console.error('Failed to get job status');
      }
    } catch (error) {
      console.error('Error polling job status:', error);
    }
  };

  const handleGenerate3D = async () => {
    if (!sessionId || !iteration || !targetObject) {
      console.error('Missing required data for 3D generation');
      return;
    }

    // Check if user is authenticated
    if (!user) {
      setCreditError('Please sign in to generate 3D models');
      return;
    }

    // If 3D model already exists, open studio in new tab
    if (threeDModelUrl) {
      window.open('/studio', '_blank');
      return;
    }

    // If already generating, don't start another job
    if (isGenerating3D) {
      return;
    }

    // Start new 3D generation job
    setIsGenerating3D(true);
    setGenerationStatus('running');
    setCreditError(null);
    
    try {
      // Get auth token
      const { data: { session } } = await import('../lib/supabase').then(m => m.supabase.auth.getSession());
      const token = session?.access_token;
      
      if (!token) {
        setCreditError('Authentication required. Please sign in again.');
        setIsGenerating3D(false);
        setGenerationStatus('failed');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/generate-3d`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          sessionId,
          iteration,
          targetObject,
          imageUrl: originalUrl || imageUrl
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.record_id) {
          setRecordId(data.record_id);
          
          // Start polling for status updates
          const interval = setInterval(() => {
            pollJobStatus(data.record_id);
          }, 10000); // Poll every 10 seconds
          
          setPollingInterval(interval);
          
          // Do initial status check
          pollJobStatus(data.record_id);
        } else {
          console.error('Failed to submit 3D generation job');
          setIsGenerating3D(false);
          setGenerationStatus('failed');
        }
      } else {
        const errorData = await response.json();
        console.error('Failed to submit 3D generation job:', errorData);
        
        // Handle credit-related errors
        if (response.status === 402) {
          setCreditError(errorData.message || 'Insufficient credits. Please add funds to your wallet.');
        } else if (response.status === 401) {
          setCreditError('Authentication required. Please sign in again.');
        } else {
          setCreditError(errorData.error || 'Failed to submit 3D generation job');
        }
        
        setIsGenerating3D(false);
        setGenerationStatus('failed');
      }
    } catch (error) {
      console.error('Error submitting 3D generation job:', error);
      setIsGenerating3D(false);
      setGenerationStatus('failed');
    }
  };

  if (hasError) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
        <div className="text-center">
          <p className="text-gray-500">Failed to load image</p>
          <p className="text-xs text-gray-400 mt-1">API URL: {imageUrl}</p>
          {originalUrl && (
            <p className="text-xs text-gray-400">Original: {originalUrl}</p>
          )}
          <button 
            onClick={() => {
              setHasError(false);
              setIsLoading(true);
            }}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="relative group">
        <div className="relative overflow-hidden rounded-lg bg-gray-100">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          )}
          
          <img
            src={imageUrl}
            alt="Generated 3D reconstruction image"
            className={`w-full h-auto transition-opacity duration-300 ${
              isLoading ? 'opacity-0' : 'opacity-100'
            }`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            onClick={() => setIsModalOpen(true)}
          />
          
          {/* Hover overlay */}
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <MagnifyingGlassIcon className="w-8 h-8 text-white" />
            </div>
          </div>

          {/* Generation Progress Overlay */}
          {isGenerating && (
            <div className="absolute inset-0 bg-blue-900 bg-opacity-75 flex items-center justify-center">
              <div className="text-center text-white">
                <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                <p className="text-sm font-medium">Generating Image...</p>
                <p className="text-xs opacity-75">Please wait</p>
              </div>
            </div>
          )}
        </div>

        {/* Generate 3D Button */}
        {sessionId && iteration && targetObject && (
          <div className="mt-3">
            {/* Pricing Info */}
            {/* <div className="mb-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-xs text-blue-700">3D Generation Cost:</span>
                <span className="text-xs font-semibold text-blue-800">$0.50</span>
              </div>
            </div> */}
            
            <button
              onClick={handleGenerate3D}
              disabled={isGenerating3D || generationStatus === 'running'}
              className={`w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                isGenerating3D || generationStatus === 'running'
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : generationStatus === 'failed'
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              <CubeIcon className="w-4 h-4" />
              <span>
                {generationStatus === 'running' || isGenerating3D
                  ? 'Generating 3D...' 
                  : generationStatus === 'completed' || threeDModelUrl 
                    ? 'View 3D in Studio' 
                    : generationStatus === 'failed'
                    ? 'Retry 3D Generation'
                    : 'Generate 3D View'
                }
              </span>
            </button>
            
            {/* Credit Error Display */}
            {creditError && (
              <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-800">{creditError}</p>
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
          </div>
        )}

        {/* 3D Model Display */}
        {threeDModelUrl && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CubeIcon className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-800">3D Model Ready</span>
              </div>
              <a
                href={threeDModelUrl}
                download
                className="text-sm text-green-600 hover:text-green-800 underline"
              >
                Download GLB
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Modal for full-size image */}
      {isModalOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setIsModalOpen(false)}
        >
          <div className="relative max-w-4xl max-h-full">
            <img
              src={imageUrl}
              alt="Generated 3D reconstruction image"
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-white bg-black bg-opacity-50 rounded-full p-2 hover:bg-opacity-75 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </>
  );
};
