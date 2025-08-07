import React, { useState } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

interface ImageGridProps {
  imageUrl: string;
  originalUrl?: string;
}

export const ImageGrid: React.FC<ImageGridProps> = ({ imageUrl, originalUrl }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  const handleImageError = (error: any) => {
    console.error('Image load error:', error);
    console.error('Image URL:', imageUrl);
    setIsLoading(false);
    setHasError(true);
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
