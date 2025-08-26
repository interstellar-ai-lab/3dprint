import React, { useState, useRef, useCallback } from 'react';
import { useMutation } from 'react-query';
import { CloudArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { SingleImageStatusDisplay } from './SingleImageStatusDisplay';
import { useAuth } from '../contexts/AuthContext';

interface SingleImageUploadFormProps {
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

export const SingleImageUploadForm: React.FC<SingleImageUploadFormProps> = ({ 
  onSuccess, 
  onError 
}) => {
  const [selectedImage, setSelectedImage] = useState<{ file: File; preview: string; name: string } | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ recordId: number } | null>(null);
  const [generationStatus, setGenerationStatus] = useState<string>('pending');
  const [creditError, setCreditError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();

  // API base URL - adjust this according to your backend setup
  const API_BASE = process.env.REACT_APP_API_URL || 'https://vicino.ai';

  const uploadMutation = useMutation(
    async (formData: FormData) => {
      // Get auth token
      const { data: { session } } = await import('../lib/supabase').then(m => m.supabase.auth.getSession());
      const token = session?.access_token;
      
      if (!token) {
        throw new Error('Authentication required. Please sign in again.');
      }

      const response = await fetch(`${API_BASE}/api/upload-single-image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        
        // Handle credit-related errors
        if (response.status === 402) {
          throw new Error(errorData.message || 'Insufficient credits. Please add funds to your wallet.');
        } else if (response.status === 401) {
          throw new Error('Authentication required. Please sign in again.');
        } else {
          throw new Error(errorData.error || 'Upload failed');
        }
      }
      
      return response.json();
    },
    {
      onSuccess: (data) => {
        setUploadResult({ recordId: data.record_id });
        setCreditError(null);
        onSuccess?.(data);
        // Show success message
        console.log('✅ Single image upload successful! Starting 3D generation...');
      },
      onError: (error: any) => {
        setCreditError(error.message);
        onError?.(error);
      },
    }
  );

  const handleFileSelect = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = e.target?.result as string;
      setSelectedImage({
        file,
        preview,
        name: file.name
      });
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const removeImage = useCallback(() => {
    setSelectedImage(null);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedImage) {
      alert('Please select an image to upload');
      return;
    }

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('image', selectedImage.file);

      await uploadMutation.mutateAsync(formData);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const isGenerating = isUploading || uploadMutation.isLoading || (uploadResult && generationStatus !== 'completed');
  const isCompleted = uploadResult && generationStatus === 'completed';
  const isEnabled = selectedImage && !isGenerating && user;

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">
        Upload Single Image
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Single Image Upload Area */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 transition-all duration-200 min-h-[300px] ${
            dragOver 
              ? 'border-purple-500 bg-purple-50' 
              : selectedImage 
                ? 'border-green-500 bg-green-50' 
                : 'border-gray-300 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          {selectedImage ? (
            // Preview uploaded image
            <div className="relative">
              <div className="w-full h-64 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
                <img
                  src={selectedImage.preview}
                  alt="Image preview"
                  className="max-w-full max-h-full object-contain rounded-lg"
                />
              </div>
              <button
                type="button"
                onClick={removeImage}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
              <p className="text-sm text-gray-600 mt-2 text-center">{selectedImage.name}</p>
            </div>
          ) : (
            // Upload area
            <div className="text-center flex flex-col items-center justify-center h-full min-h-[200px]">
              <CloudArrowUpIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-700 mb-2">Upload a single image</p>
              <p className="text-sm text-gray-500 mb-6 text-center max-w-md">
                Drag & drop an image here or click to browse. We'll generate a 3D model from your single image using AI.
              </p>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-6 py-3 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
              >
                Choose Image
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileSelect(file);
                }}
                className="hidden"
              />
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-800 mb-2">📋 Instructions:</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Upload a single clear image of the object you want to 3D model</li>
            <li>• Ensure the image is well-lit and shows the object clearly</li>
            <li>• The object should be centered and take up most of the frame</li>
            <li>• Supported formats: PNG, JPG, JPEG</li>
          </ul>
        </div>

        {/* Submit Button */}
        {(() => {
          if (!user) {
            return (
              <div className="w-full py-3 px-6 rounded-lg bg-yellow-50 border border-yellow-200 text-center">
                <p className="text-yellow-800 text-sm">
                  Please sign in to generate 3D models
                </p>
              </div>
            );
          }
          
                      return (
              <button
                type={isCompleted ? "button" : "submit"}
                disabled={!isEnabled}
                onClick={isCompleted ? () => window.open('/studio', '_blank') : undefined}
                className={`w-full py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  isEnabled
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
              {isGenerating ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  {uploadResult ? '3D Generation in Progress...' : 'Starting Generation...'}
                </div>
              ) : isCompleted ? (
                '🎨 View 3D in Studio'
              ) : (
                '🚀 Generate 3D Model'
              )}
            </button>
          );
        })()}

        {/* Upload Progress */}
        {uploadMutation.isLoading && !uploadResult && (
          <div className="mt-4">
            <div className="bg-gray-200 rounded-full h-2">
              <div className="bg-purple-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
            <p className="text-sm text-gray-600 mt-2 text-center">
              Uploading image and starting generation...
            </p>
          </div>
        )}

        {/* Error Display */}
        {uploadMutation.isError && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-red-700 text-sm">
                  {uploadMutation.error instanceof Error ? uploadMutation.error.message : 'Upload failed'}
                </p>
                {creditError && creditError.includes('credits') && (
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

        {/* Success Message */}
        {uploadResult && !uploadMutation.isLoading && generationStatus !== 'completed' && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <p className="text-green-700 text-sm font-medium">
                ✅ Upload successful! 3D generation is now in progress...
              </p>
            </div>
          </div>
        )}
      </form>

      {/* Status Display */}
      {uploadResult && (
        <div className="mt-6">
          <SingleImageStatusDisplay 
            recordId={uploadResult.recordId}
            onComplete={(data) => {
              console.log('3D generation completed:', data);
              setGenerationStatus('completed');
            }}
            onStatusChange={(status) => {
              setGenerationStatus(status);
            }}
          />
        </div>
      )}
    </div>
  );
};
