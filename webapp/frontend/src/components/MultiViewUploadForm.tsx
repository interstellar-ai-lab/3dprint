import React, { useState, useRef, useCallback } from 'react';
import { useMutation } from 'react-query';
import { CloudArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { MultiViewStatusDisplay } from './MultiViewStatusDisplay';

interface ViewImage {
  file: File;
  preview: string;
  name: string;
}

interface MultiViewUploadFormProps {
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

export const MultiViewUploadForm: React.FC<MultiViewUploadFormProps> = ({ 
  onSuccess, 
  onError 
}) => {
  const [views, setViews] = useState<Record<string, ViewImage | null>>({
    front: null,
    left: null,
    back: null,
    right: null
  });
  const [dragOver, setDragOver] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ recordId: number } | null>(null);
  const [generationStatus, setGenerationStatus] = useState<string>('pending');
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  // API base URL - adjust this according to your backend setup
  const API_BASE = process.env.REACT_APP_API_URL || 'https://vicino.ai';

  const uploadMutation = useMutation(
    async (formData: FormData) => {
      const response = await fetch(`${API_BASE}/api/upload-multiview`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Upload failed');
      }
      
      return response.json();
    },
    {
      onSuccess: (data) => {
        setUploadResult({ recordId: data.record_id });
        onSuccess?.(data);
        // Show success message
        console.log('✅ Multi-view upload successful! Starting 3D generation...');
      },
      onError: (error: any) => {
        onError?.(error);
      },
    }
  );

  const handleFileSelect = useCallback((viewName: string, file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = e.target?.result as string;
      setViews(prev => ({
        ...prev,
        [viewName]: {
          file,
          preview,
          name: file.name
        }
      }));
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback((viewName: string, e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(null);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(viewName, files[0]);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((viewName: string, e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(viewName);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(null);
  }, []);

  const removeView = useCallback((viewName: string) => {
    setViews(prev => ({
      ...prev,
      [viewName]: null
    }));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Check if all views are uploaded
    const missingViews = Object.entries(views)
      .filter(([_, view]) => !view)
      .map(([name]) => name);
    
    if (missingViews.length > 0) {
      alert(`Please upload all required views: ${missingViews.join(', ')}`);
      return;
    }

    setIsUploading(true);
    
    try {
      const formData = new FormData();
      Object.entries(views).forEach(([viewName, view]) => {
        if (view) {
          formData.append(viewName, view.file);
        }
      });

      await uploadMutation.mutateAsync(formData);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const isAllViewsUploaded = Object.values(views).every(view => view !== null);

  const viewConfig = [
    { key: 'front', label: 'Front View'},
    { key: 'left', label: 'Left View'},
    { key: 'back', label: 'Back View'},
    { key: 'right', label: 'Right View'}
  ];

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6">
        Upload Multi-View Images
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Multi-View Upload Grid */}
        <div className="grid grid-cols-2 gap-6">
          {viewConfig.map(({ key, label }) => (
            <div
              key={key}
              className={`relative border-2 border-dashed rounded-lg p-4 transition-all duration-200 min-h-[200px] ${
                dragOver === key 
                  ? 'border-purple-500 bg-purple-50' 
                  : views[key] 
                    ? 'border-green-500 bg-green-50' 
                    : 'border-gray-300 hover:border-gray-400'
              }`}
              onDrop={(e) => handleDrop(key, e)}
              onDragOver={(e) => handleDragOver(key, e)}
              onDragLeave={handleDragLeave}
            >
              {views[key] ? (
                // Preview uploaded image
                <div className="relative">
                  <div className="w-full h-48 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
                    <img
                      src={views[key]!.preview}
                      alt={`${label} preview`}
                      className="max-w-full max-h-full object-contain rounded-lg"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeView(key)}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                  <p className="text-sm text-gray-600 mt-2 text-center">{label}</p>
                </div>
              ) : (
                // Upload area
                <div className="text-center flex flex-col items-center justify-center h-full min-h-[160px]">
                  <CloudArrowUpIcon className="w-8 h-8 text-gray-400 mx-auto mb-3" />
                  <p className="text-sm font-medium text-gray-700 mb-2">{label}</p>
                  <p className="text-xs text-gray-500 mb-4 text-center">
                    Drag & drop or click to upload
                  </p>
                  <button
                    type="button"
                    onClick={() => fileInputRefs.current[key]?.click()}
                    className="px-4 py-2 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
                  >
                    Choose File
                  </button>
                  <input
                    ref={(el) => fileInputRefs.current[key] = el}
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFileSelect(key, file);
                    }}
                    className="hidden"
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-800 mb-2">📋 Instructions:</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Upload 4 orthogonal views of your 3D object</li>
            <li>• Ensure images are clear and well-lit</li>
            <li>• All views should show the same object from different angles</li>
            <li>• Supported formats: PNG, JPG, JPEG</li>
          </ul>
        </div>

        {/* Submit Button */}
        {(() => {
          const isGenerating = isUploading || uploadMutation.isLoading || uploadResult;
          const isEnabled = isAllViewsUploaded && !isGenerating;
          
          return (
            <button
              type="submit"
              disabled={!isEnabled}
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
              Uploading images and starting generation...
            </p>
          </div>
        )}

        {/* Error Display */}
        {uploadMutation.isError && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">
              Error: {uploadMutation.error instanceof Error ? uploadMutation.error.message : 'Upload failed'}
            </p>
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
          <MultiViewStatusDisplay 
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