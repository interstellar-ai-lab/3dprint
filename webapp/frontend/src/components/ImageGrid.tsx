import React, { useState } from 'react';
import { MagnifyingGlassIcon, CubeIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://vicino.ai';

interface ImageGridProps {
  imageUrl: string;
  originalUrl?: string;
  sessionId?: string;
  iteration?: number;
  targetObject?: string;
}

export const ImageGrid: React.FC<ImageGridProps> = ({ imageUrl, originalUrl, sessionId, iteration, targetObject }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isGenerating3D, setIsGenerating3D] = useState(false);
  const [threeDModelUrl, setThreeDModelUrl] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleImageLoad = () => {
    setIsLoading(false);
    setHasError(false);
  };

  const handleImageError = (error: any) => {
    console.error('Image load error:', error);
    setIsLoading(false);
    setHasError(true);
  };

  const handleGenerate3D = async () => {
    if (!sessionId || !iteration || !targetObject) {
      console.error('Missing required data for 3D generation');
      return;
    }

    // If 3D model already exists, open studio in new tab
    if (threeDModelUrl) {
      window.open('/studio', '_blank');
      return;
    }

    // Otherwise, generate new 3D model
    setIsGenerating3D(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-3d`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
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
        if (data.model_url) {
          setThreeDModelUrl(data.model_url);
          // Don't automatically open studio - let user click "View 3D in Studio" button
        }
      } else {
        console.error('Failed to generate 3D model');
      }
    } catch (error) {
      console.error('Error generating 3D model:', error);
    } finally {
      setIsGenerating3D(false);
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
        </div>

        {/* Generate 3D Button */}
        {sessionId && iteration && targetObject && (
          <div className="mt-3">
            <button
              onClick={handleGenerate3D}
              disabled={isGenerating3D}
              className={`w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                isGenerating3D
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              <CubeIcon className="w-4 h-4" />
              <span>
                {isGenerating3D 
                  ? 'Generating 3D...' 
                  : threeDModelUrl 
                    ? 'View 3D in Studio' 
                    : 'Generate 3D View'
                }
              </span>
            </button>
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
