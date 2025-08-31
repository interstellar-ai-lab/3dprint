import React, { useRef, useCallback, useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useGenerationStore } from '../stores/generationStore';

interface NanoBananaProps {
  onClose?: () => void;
}

interface GenerationStatus {
  status: string;
  task_id?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  '3d_url'?: string;
  image_url?: string;
}

export const NanoBanana: React.FC<NanoBananaProps> = ({ onClose }) => {
  const { user } = useAuth();
  const {
    aiImageEdit,
    setSelectedImage,
    setReferenceImages,
    setImagePreview,
    setReferencePreviews,
    setInstruction,
    setResult,
    setIsProcessing,
    setError,
    setDragActive,
    resetAIImageEdit,
    addReferenceImage,
    removeReferenceImage
  } = useGenerationStore();

  const {
    selectedImage,
    referenceImages,
    imagePreview,
    referencePreviews,
    instruction,
    result,
    isProcessing,
    error,
    dragActive
  } = aiImageEdit;

  const fileInputRef = useRef<HTMLInputElement>(null);
  const referenceFileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  
  // Local state for 3D generation
  const [isGenerating3D, setIsGenerating3D] = useState(false);
  const [threeDGenerationStatus, setThreeDGenerationStatus] = useState<'idle' | 'pending' | 'running' | 'completed' | 'failed'>('idle');
  const [threeDModelUrl, setThreeDModelUrl] = useState<string | null>(null);
  const [threeDRecordId, setThreeDRecordId] = useState<number | null>(null);
  const [threeDStatusData, setThreeDStatusData] = useState<GenerationStatus | null>(null);

  // API base URL
  const API_BASE = process.env.REACT_APP_API_URL || 'https://vicino.ai';

  // Button state logic
  const isEnabled = result?.image && user && (
    threeDGenerationStatus === 'idle' || 
    threeDGenerationStatus === 'completed' || 
    threeDGenerationStatus === 'failed'
  );

  // Check if we should show the retry button
  const shouldShowRetry = threeDGenerationStatus === 'failed';

  // Status polling effect
  useEffect(() => {
    if (!threeDRecordId || threeDGenerationStatus === 'completed' || threeDGenerationStatus === 'failed') {
      return;
    }

    const pollStatus = async () => {
      try {
        const { data: { session } } = await import('../lib/supabase').then(m => m.supabase.auth.getSession());
        const token = session?.access_token;
        
        if (!token) {
          console.error('No auth token available for status polling');
          return;
        }

        const response = await fetch(`${API_BASE}/api/generation-status/${threeDRecordId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch status');
        }

        const statusData: GenerationStatus = await response.json();
        setThreeDStatusData(statusData);
        
        // Update status based on response
        if (statusData.status === 'completed') {
          setThreeDGenerationStatus('completed');
          if (statusData['3d_url']) {
            setThreeDModelUrl(statusData['3d_url']);
          } else {
            // If no 3D URL in status, use the studio URL as fallback
            setThreeDModelUrl('/studio');
          }
        } else if (statusData.status === 'failed') {
          setThreeDGenerationStatus('failed');
        } else if (statusData.status === 'running') {
          setThreeDGenerationStatus('running');
        } else if (statusData.status === 'pending') {
          setThreeDGenerationStatus('pending');
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    };

    // Poll every 5 seconds
    const interval = setInterval(pollStatus, 5000);
    
    // Initial poll
    pollStatus();

    return () => clearInterval(interval);
  }, [threeDRecordId, threeDGenerationStatus, API_BASE]);

  // Sample instructions for inspiration
  const sampleInstructions = [
    "Optimize this image for 3D reconstruction with clear edges, consistent lighting, and detailed textures",
    "Make this image look like a painting by Vincent van Gogh, with swirling brushstrokes and vibrant colors",
    "Transform this into a cyberpunk style with neon lights and futuristic elements",
    "Convert this to a watercolor painting with soft, flowing colors",
    "Make this look like it was taken in the 1980s with retro styling",
    "Transform this into a fantasy landscape with magical elements and glowing effects",
  ];

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, [setDragActive]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, [setDragActive]);

  const handleFileSelect = (file: File) => {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, or WebP)');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setError('');
    setSelectedImage(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleReferenceFileSelect = (files: FileList) => {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    const newReferenceImages: File[] = [];
    const newReferencePreviews: string[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Validate file type
      if (!validTypes.includes(file.type)) {
        setError('Please select valid image files (JPEG, PNG, or WebP) for reference images');
        return;
      }

      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        setError('Reference image file size must be less than 10MB');
        return;
      }

      newReferenceImages.push(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        newReferencePreviews.push(e.target?.result as string);
        if (newReferencePreviews.length === files.length) {
          // Add all reference images to the store
          newReferenceImages.forEach((img, idx) => {
            addReferenceImage(img, newReferencePreviews[idx]);
          });
        }
      };
      reader.readAsDataURL(file);
    }

    setError('');
  };

  const handleReferenceFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleReferenceFileSelect(e.target.files);
    }
  };

  const handleSubmit = async () => {
    if (!user) {
      setError('Please sign in to use AI image editing');
      return;
    }

    if (!selectedImage || !instruction.trim()) {
      setError('Please select an image and provide an instruction');
      return;
    }

    setIsProcessing(true);
    setError('');
    setResult(null);

    try {
      // Convert main image to base64
      const base64Image = await fileToBase64(selectedImage);
      
      // Convert reference images to base64
      const referenceImagesBase64: string[] = [];
      for (const refImage of referenceImages) {
        const base64RefImage = await fileToBase64(refImage);
        referenceImagesBase64.push(base64RefImage.split(',')[1]); // Remove data:image/... prefix
      }
      
      // Use the same API base as other components
      const API_BASE = process.env.REACT_APP_API_URL || 'https://vicino.ai';
      
      // Get auth token
      const { data: { session } } = await import('../lib/supabase').then(m => m.supabase.auth.getSession());
      const token = session?.access_token;
      
      if (!token) {
        throw new Error('Authentication required. Please sign in again.');
      }
      
      // Prepare request body
      const requestBody: any = {
        image: base64Image.split(',')[1], // Remove data:image/... prefix
        instruction: instruction.trim()
      };
      
      // Add reference images if any
      if (referenceImagesBase64.length > 0) {
        requestBody.reference_images = referenceImagesBase64;
      }
      
      // Call the Nano Banana API
      const response = await fetch(`${API_BASE}/api/nano/edit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      
      if (data.success) {
        setResult({
          success: true,
          image: `data:image/png;base64,${data.image}`,
          filename: data.filename,
          timestamp: data.timestamp
        });
      } else {
        // Handle specific error cases
        if (response.status === 401) {
          setResult({
            success: false,
            error: 'Authentication required. Please sign in again.'
          });
        } else if (response.status === 402) {
          setResult({
            success: false,
            error: `Insufficient credits. ${data.error}`
          });
        } else {
          setResult({
            success: false,
            error: data.error || 'Failed to process image'
          });
        }
      }
    } catch (err) {
      setResult({
        success: false,
        error: err instanceof Error ? err.message : 'An unexpected error occurred'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  const resetForm = () => {
    resetAIImageEdit();
    // Reset 3D generation state
    setIsGenerating3D(false);
    setThreeDGenerationStatus('idle');
    setThreeDModelUrl(null);
    setThreeDRecordId(null);
    setThreeDStatusData(null);
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (referenceFileInputRef.current) {
      referenceFileInputRef.current.value = '';
    }
  };

  const downloadResult = () => {
    if (result?.image) {
      const link = document.createElement('a');
      link.href = result.image;
      link.download = result.filename || 'nano_banana_result.png';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const generate3D = async () => {
    if (!user) {
      setError('Please sign in to generate 3D models');
      return;
    }

    if (!result?.image) {
      setError('No processed image available for 3D generation');
      return;
    }

    // Reset 3D generation state
    setThreeDGenerationStatus('idle');
    setThreeDModelUrl(null);
    setThreeDRecordId(null);
    setThreeDStatusData(null);
    setError('');

    setIsGenerating3D(true);
    setThreeDGenerationStatus('pending'); // Start with pending

    try {
      // Use the same API base as other components
      const API_BASE = process.env.REACT_APP_API_URL || 'https://vicino.ai';
      
      // Get auth token
      const { data: { session } } = await import('../lib/supabase').then(m => m.supabase.auth.getSession());
      const token = session?.access_token;
      
      if (!token) {
        throw new Error('Authentication required. Please sign in again.');
      }
      
      // Convert base64 data URL to file with proper format handling
      const base64Response = await fetch(result.image);
      const blob = await base64Response.blob();
      
      let imageFile: File;
      
      // Ensure we have a proper image blob
      if (!blob.type.startsWith('image/')) {
        // If blob type is not an image, create a proper PNG blob
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        await new Promise((resolve, reject) => {
          img.onload = resolve;
          img.onerror = reject;
          img.src = result.image!;
        });
        
        canvas.width = img.width;
        canvas.height = img.height;
        ctx?.drawImage(img, 0, 0);
        
        // Convert canvas to blob with proper PNG format
        const pngBlob = await new Promise<Blob>((resolve) => {
          canvas.toBlob((blob) => {
            resolve(blob!);
          }, 'image/png', 0.95);
        });
        
        imageFile = new File([pngBlob], 'edited_image.png', { type: 'image/png' });
      } else {
        // Use the original blob if it's already an image
        imageFile = new File([blob], 'edited_image.png', { type: blob.type });
      }
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('image', imageFile);
      
      // Call the 3D generation API endpoint
      const response = await fetch(`${API_BASE}/api/upload-single-image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          // Don't set Content-Type header - let browser set it with boundary for FormData
        },
        body: formData
      });

      const data = await response.json();
      
      if (response.ok && data.record_id) {
        // Handle successful 3D generation start
        console.log('3D generation started:', data);
        setThreeDRecordId(data.record_id); // Store the record ID for polling
        setThreeDGenerationStatus('pending'); // Start with pending status
        // The status polling will handle the rest
      } else {
        // Handle specific error cases
        if (response.status === 401) {
          setError('Authentication required. Please sign in again.');
        } else if (response.status === 402) {
          setError(`Insufficient credits. ${data.error || 'Please add funds to your wallet.'}`);
        } else {
          setError(data.error || 'Failed to start 3D generation');
          setThreeDGenerationStatus('failed');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred during 3D generation');
      setThreeDGenerationStatus('failed');
    } finally {
      setIsGenerating3D(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-orange-50 to-red-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block mb-6 animate-fade-in">
            <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              AI Image Editor
            </h1>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto animate-fade-in-delay">
            Transform your images with AI magic.
            Upload an image, describe your vision, and watch the magic happen!
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Upload & Input */}
          <div className="space-y-6 animate-slide-in-left">
            {/* Image Upload */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">
                📸 Upload Your Image
              </h3>
              
              <div
                ref={dropZoneRef}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer ${
                  dragActive 
                    ? 'border-orange-400 bg-orange-50' 
                    : 'border-gray-300 hover:border-orange-400 hover:bg-orange-50'
                }`}
                onClick={() => fileInputRef.current?.click()}
              >
                {imagePreview ? (
                  <div className="space-y-4">
                    <img 
                      src={imagePreview} 
                      alt="Preview" 
                      className="max-w-full h-48 object-contain mx-auto rounded-lg shadow-md"
                    />
                    <p className="text-sm text-gray-600">
                      Click to change image
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="text-4xl">📁</div>
                    <p className="text-gray-600">
                      Drag & drop an image here, or click to browse
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports JPEG, PNG, WebP (max 10MB)
                    </p>
                  </div>
                )}
              </div>
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileInput}
                className="hidden"
              />
              
              {error && (
                <div className="mt-4 p-3 bg-red-100 border border-red-300 rounded-lg text-red-700 text-sm animate-fade-in">
                  {error}
                </div>
              )}
            </div>

            {/* Reference Images Upload */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">
                🎯 Reference Images (Optional)
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Upload additional images to guide the AI's style or reference. Maximum 5 images.
              </p>
              
              {/* Reference Images Preview */}
              {referencePreviews.length > 0 && (
                <div className="mb-4">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {referencePreviews.map((preview, index) => (
                      <div key={index} className="relative group">
                        <img 
                          src={preview} 
                          alt={`Reference ${index + 1}`} 
                          className="w-full h-24 object-cover rounded-lg shadow-sm"
                        />
                        <button
                          onClick={() => removeReferenceImage(index)}
                          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Add Reference Images Button */}
              <button
                onClick={() => referenceFileInputRef.current?.click()}
                disabled={referenceImages.length >= 5}
                className={`w-full p-4 border-2 border-dashed rounded-xl text-center transition-all duration-200 ${
                  referenceImages.length >= 5
                    ? 'border-gray-200 text-gray-400 cursor-not-allowed'
                    : 'border-gray-300 hover:border-orange-400 hover:bg-orange-50 text-gray-600 hover:text-orange-600'
                }`}
              >
                <div className="text-2xl mb-2">➕</div>
                <p className="text-sm">
                  {referenceImages.length >= 5 
                    ? 'Maximum 5 reference images reached' 
                    : 'Add Reference Images'
                  }
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {referenceImages.length}/5 images
                </p>
              </button>
              
              <input
                ref={referenceFileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleReferenceFileInput}
                className="hidden"
              />
            </div>

            {/* Instruction Input */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">
                ✍️ Describe Your Vision
              </h3>
              
              <textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="Describe how you want to transform your image... (e.g., 'Make this look like a Van Gogh painting')"
                className="w-full h-32 p-4 border border-gray-300 rounded-xl resize-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200"
                disabled={isProcessing}
              />
              
              {/* Sample Instructions */}
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">💡 Try these examples:</p>
                <div className="grid grid-cols-1 gap-2">
                  {sampleInstructions.slice(0, 4).map((sample, index) => (
                    <button
                      key={index}
                      onClick={() => setInstruction(sample)}
                      className="text-left p-2 text-xs text-gray-600 hover:bg-orange-50 rounded-lg transition-colors duration-200"
                      disabled={isProcessing}
                    >
                      {sample}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              {!user && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-blue-600 text-xs">
                    Please sign in to use AI image editing
                  </p>
                </div>
              )}
              
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleSubmit}
                  disabled={!user || !selectedImage || !instruction.trim() || isProcessing}
                  className={`flex-1 px-6 py-3 rounded-xl font-semibold text-white transition-all duration-200 ${
                    !user || !selectedImage || !instruction.trim() || isProcessing
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 transform hover:scale-105'
                  }`}
                >
                  {isProcessing ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>Processing...</span>
                    </div>
                  ) : (
                    '🚀 Edit Image'
                  )}
                </button>
                
                <button
                  onClick={resetForm}
                  disabled={isProcessing}
                  className="px-6 py-3 rounded-xl font-semibold text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors duration-200"
                >
                  🔄 Reset
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6 animate-slide-in-right">
            {/* Results Display */}
            <div className="bg-white rounded-2xl shadow-xl p-6 min-h-[400px]">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">
                🎨 Your Edited Image
              </h3>
              
              <div className="transition-all duration-300">
                {isProcessing ? (
                  <div className="flex flex-col items-center justify-center h-80 text-center animate-fade-in">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500 mb-4"></div>
                    <h4 className="text-lg font-semibold text-gray-700 mb-2">
                      AI is working its magic! ✨
                    </h4>
                    <p className="text-gray-600">
                      This usually takes 10-30 seconds...
                    </p>
                  </div>
                ) : result ? (
                  <div className="space-y-4 animate-fade-in">
                    {result.success ? (
                      <>
                        <div className="relative">
                          <img 
                            src={result.image} 
                            alt="Transformed image" 
                            className="w-full h-80 object-contain rounded-lg shadow-lg"
                          />
                          <div className="absolute top-2 right-2">
                            <div className="bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                              ✅ Success
                            </div>
                          </div>
                        </div>
                        
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-green-800 font-medium">
                                Image edited successfully!
                              </p>
                            </div>
                            <div className="flex gap-3">
                              <button
                                onClick={downloadResult}
                                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200"
                              >
                                💾 Download
                              </button>
                              <button
                                onClick={threeDGenerationStatus === 'completed' && threeDModelUrl ? 
                                  () => {
                                    // Open studio in a new tab
                                    const baseUrl = process.env.REACT_APP_BASE_URL || window.location.origin;
                                    const studioUrl = `${baseUrl}/studio`;
                                    window.open(studioUrl, '_blank');
                                  } : 
                                  generate3D
                                }
                                disabled={!isEnabled}
                                className={`px-4 py-2 rounded-lg transition-colors duration-200 ${
                                  isEnabled
                                    ? threeDGenerationStatus === 'completed' && threeDModelUrl
                                      ? 'bg-green-500 text-white hover:bg-green-600'
                                      : 'bg-blue-500 text-white hover:bg-blue-600'
                                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                }`}
                              >
                                {isGenerating3D || threeDGenerationStatus === 'pending' || threeDGenerationStatus === 'running' ? (
                                  <div className="flex items-center justify-center">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white inline-block mr-2"></div>
                                    {threeDGenerationStatus === 'pending' ? 'Starting Generation...' : 
                                     threeDGenerationStatus === 'running' ? '3D Generation in Progress...' : 
                                     'Starting Generation...'}
                                  </div>
                                ) : threeDGenerationStatus === 'completed' && threeDModelUrl ? (
                                  '🎨 View 3D in Studio'
                                ) : threeDGenerationStatus === 'failed' ? (
                                  '🔄 Retry 3D Generation'
                                ) : (
                                  '🎨 Generate 3D'
                                )}
                              </button>
                            </div>
                          </div>
                          
                          {/* 3D Generation Status Display */}
                          {(threeDGenerationStatus === 'pending' || threeDGenerationStatus === 'running') && (
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4 animate-fade-in">
                              <div className="flex items-center space-x-3">
                                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                                <div>
                                  <p className="text-blue-800 font-medium">
                                    🎨 {threeDGenerationStatus === 'pending' ? 'Starting 3D Generation...' : 'Generating 3D Model...'}
                                  </p>
                                  <p className="text-blue-600 text-sm">
                                    {threeDGenerationStatus === 'pending' 
                                      ? 'Initializing the generation process...' 
                                      : 'This process may take several minutes. Please wait...'
                                    }
                                  </p>
                                  {threeDStatusData?.created_at && (
                                    <p className="text-blue-500 text-xs mt-1">
                                      Started: {new Date(threeDStatusData.created_at).toLocaleString()}
                                    </p>
                                  )}
                                  {threeDStatusData?.task_id && (
                                    <p className="text-blue-500 text-xs mt-1">
                                      Task ID: {threeDStatusData.task_id}
                                    </p>
                                  )}
                                  
                                  {/* Progress Bar */}
                                  <div className="mt-3">
                                    <div className="bg-gray-200 rounded-full h-2">
                                      <div 
                                        className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-1000 ease-out"
                                        style={{ 
                                          width: `${threeDGenerationStatus === 'pending' ? 25 : 
                                                  threeDGenerationStatus === 'running' ? 60 : 0}%` 
                                        }}
                                      ></div>
                                    </div>
                                    <p className="text-xs text-blue-500 mt-1">
                                      Progress: {threeDGenerationStatus === 'pending' ? '25%' : 
                                                 threeDGenerationStatus === 'running' ? '60%' : '0%'}
                                    </p>
                                  </div>
                                  
                                  {/* Estimated Time */}
                                  <p className="text-blue-500 text-xs mt-2">
                                    {threeDGenerationStatus === 'pending' 
                                      ? 'Estimated time: 1-2 minutes' 
                                      : 'Estimated time: 3-5 minutes'
                                    }
                                  </p>
                                  
                                  {/* Cancel Button for Running Jobs */}
                                  {threeDGenerationStatus === 'running' && (
                                    <button
                                      onClick={() => {
                                        // Note: This would need a cancel endpoint in the backend
                                        alert('Cancel functionality not yet implemented. Please wait for completion or contact support.');
                                      }}
                                      className="mt-2 px-3 py-1 bg-yellow-500 text-white text-xs rounded hover:bg-yellow-600 transition-colors"
                                    >
                                      Cancel Generation
                                    </button>
                                  )}
                                  
                                  {/* Generation Details */}
                                  <details className="mt-3">
                                    <summary className="text-blue-500 text-xs cursor-pointer hover:text-blue-600">
                                      Show Generation Details
                                    </summary>
                                    <div className="mt-2 p-2 bg-blue-50 rounded text-xs text-blue-700">
                                      <p><strong>Status:</strong> {threeDGenerationStatus}</p>
                                      <p><strong>Task ID:</strong> {threeDStatusData?.task_id || 'N/A'}</p>
                                      <p><strong>Started:</strong> {threeDStatusData?.created_at ? new Date(threeDStatusData.created_at).toLocaleString() : 'N/A'}</p>
                                      <p><strong>Last Updated:</strong> {threeDStatusData?.updated_at ? new Date(threeDStatusData.updated_at).toLocaleString() : 'N/A'}</p>
                                      <p><strong>Progress:</strong> {threeDGenerationStatus === 'pending' ? '25%' : threeDGenerationStatus === 'running' ? '60%' : '0%'}</p>
                                    </div>
                                  </details>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {threeDGenerationStatus === 'completed' && threeDModelUrl && (
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-4 animate-fade-in">
                              <div className="flex items-center space-x-3">
                                <div className="text-green-600 text-2xl">✅</div>
                                <div>
                                  <p className="text-green-800 font-medium">
                                    🎨 3D Model Generated Successfully!
                                  </p>
                                  <p className="text-green-600 text-sm">
                                    Click "View 3D in Studio" to open your 3D model.
                                  </p>
                                  {threeDStatusData?.updated_at && (
                                    <p className="text-green-500 text-xs mt-1">
                                      Completed: {new Date(threeDStatusData.updated_at).toLocaleString()}
                                    </p>
                                  )}
                                  {threeDStatusData?.task_id && (
                                    <p className="text-green-500 text-xs mt-1">
                                      Task ID: {threeDStatusData.task_id}
                                    </p>
                                  )}
                                  {threeDStatusData?.image_url && (
                                    <p className="text-green-500 text-xs mt-1">
                                      Preview: <a href={threeDStatusData.image_url} target="_blank" rel="noopener noreferrer" className="underline">View Image</a>
                                    </p>
                                  )}
                                  
                                  {/* Action Buttons */}
                                  <div className="flex gap-2 mt-2">
                                    <button
                                      onClick={() => {
                                        // Open studio in a new tab
                                        const baseUrl = process.env.REACT_APP_BASE_URL || window.location.origin;
                                        const studioUrl = `${baseUrl}/studio`;
                                        window.open(studioUrl, '_blank');
                                      }}
                                      className="px-3 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors"
                                    >
                                      Open in Studio
                                    </button>
                                    {threeDModelUrl && threeDModelUrl !== '/studio' && (
                                      <button
                                        onClick={() => {
                                          // Download the 3D model if it's a direct URL
                                          const link = document.createElement('a');
                                          link.href = threeDModelUrl;
                                          link.download = '3d_model.glb';
                                          document.body.appendChild(link);
                                          link.click();
                                          document.body.removeChild(link);
                                        }}
                                        className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                                      >
                                        Download 3D Model
                                      </button>
                                    )}
                                  </div>
                                  
                                  {/* Generation Details */}
                                  <details className="mt-3">
                                    <summary className="text-green-500 text-xs cursor-pointer hover:text-green-600">
                                      Show Generation Details
                                    </summary>
                                    <div className="mt-2 p-2 bg-green-50 rounded text-xs text-green-700">
                                      <p><strong>Status:</strong> {threeDGenerationStatus}</p>
                                      <p><strong>Task ID:</strong> {threeDStatusData?.task_id || 'N/A'}</p>
                                      <p><strong>Started:</strong> {threeDStatusData?.created_at ? new Date(threeDStatusData.created_at).toLocaleString() : 'N/A'}</p>
                                      <p><strong>Completed:</strong> {threeDStatusData?.updated_at ? new Date(threeDStatusData.updated_at).toLocaleString() : 'N/A'}</p>
                                      <p><strong>3D Model URL:</strong> {threeDModelUrl || 'N/A'}</p>
                                      <p><strong>Preview Image:</strong> {threeDStatusData?.image_url || 'N/A'}</p>
                                    </div>
                                  </details>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {threeDGenerationStatus === 'failed' && (
                            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4 animate-fade-in">
                              <div className="flex items-center space-x-3">
                                <div className="text-red-600 text-2xl">❌</div>
                                <div>
                                  <p className="text-red-800 font-medium">
                                    🎨 3D Generation Failed
                                  </p>
                                  <p className="text-red-600 text-sm">
                                    {threeDStatusData?.error_message || 'The generation process encountered an error. Please try again.'}
                                  </p>
                                  {threeDStatusData?.task_id && (
                                    <p className="text-red-500 text-xs mt-1">
                                      Task ID: {threeDStatusData.task_id}
                                    </p>
                                  )}
                                  {threeDStatusData?.created_at && (
                                    <p className="text-red-500 text-xs mt-1">
                                      Started: {new Date(threeDStatusData.created_at).toLocaleString()}
                                    </p>
                                  )}
                                  <div className="flex gap-2 mt-2">
                                    <button
                                      onClick={() => {
                                        setThreeDGenerationStatus('idle');
                                        setThreeDModelUrl(null);
                                        setThreeDRecordId(null);
                                        setThreeDStatusData(null);
                                        generate3D();
                                      }}
                                      className="px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors"
                                    >
                                      Retry Generation
                                    </button>
                                    <button
                                      onClick={() => {
                                        // Copy error details to clipboard for support
                                        const errorDetails = `Task ID: ${threeDStatusData?.task_id || 'N/A'}\nError: ${threeDStatusData?.error_message || 'Unknown error'}\nStarted: ${threeDStatusData?.created_at || 'N/A'}`;
                                        navigator.clipboard.writeText(errorDetails);
                                        alert('Error details copied to clipboard. Please contact support with this information.');
                                      }}
                                      className="px-3 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600 transition-colors"
                                    >
                                      Copy Error Details
                                    </button>
                                  </div>
                                  
                                  {/* Generation Details */}
                                  <details className="mt-3">
                                    <summary className="text-red-500 text-xs cursor-pointer hover:text-red-600">
                                      Show Generation Details
                                    </summary>
                                    <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700">
                                      <p><strong>Status:</strong> {threeDGenerationStatus}</p>
                                      <p><strong>Task ID:</strong> {threeDStatusData?.task_id || 'N/A'}</p>
                                      <p><strong>Started:</strong> {threeDStatusData?.created_at ? new Date(threeDStatusData.created_at).toLocaleString() : 'N/A'}</p>
                                      <p><strong>Failed:</strong> {threeDStatusData?.updated_at ? new Date(threeDStatusData.updated_at).toLocaleString() : 'N/A'}</p>
                                      <p><strong>Error Message:</strong> {threeDStatusData?.error_message || 'Unknown error'}</p>
                                    </div>
                                  </details>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </>
                    ) : (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                        <div className="text-4xl mb-2">❌</div>
                        <h4 className="text-lg font-semibold text-red-800 mb-2">
                          Edit Failed
                        </h4>
                        <p className="text-red-600 mb-4">
                          {result.error}
                        </p>
                        <button
                          onClick={resetForm}
                          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors duration-200"
                        >
                          Try Again
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-80 text-center text-gray-500 animate-fade-in">
                    <div className="text-6xl mb-4">🎨</div>
                    <h4 className="text-lg font-semibold mb-2">
                      Ready to Transform?
                    </h4>
                    <p>
                      Upload an image and describe your vision to see the magic happen!
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Info Panel */}
            <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-2xl p-6 border border-orange-200">
              <ul className="space-y-2 text-sm text-orange-700">
                <li>• High-quality AI image transformation</li>
                <li>• Fast processing (10-30 seconds)</li>
                <li>• Supports various artistic styles</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Close Button */}
        {onClose && (
          <button
            onClick={onClose}
            className="fixed top-6 right-6 p-3 bg-white rounded-full shadow-lg hover:shadow-xl transition-shadow duration-200 animate-fade-in-delay"
          >
            <span className="text-2xl">✕</span>
          </button>
        )}
      </div>
    </div>
  );
};
