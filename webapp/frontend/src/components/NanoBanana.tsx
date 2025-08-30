import React, { useState, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface NanoBananaProps {
  onClose?: () => void;
}

interface EditResult {
  success: boolean;
  image?: string;
  filename?: string;
  timestamp?: string;
  error?: string;
}

export const NanoBanana: React.FC<NanoBananaProps> = ({ onClose }) => {
  const { user } = useAuth();
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [referenceImages, setReferenceImages] = useState<File[]>([]);
  const [imagePreview, setImagePreview] = useState<string>('');
  const [referencePreviews, setReferencePreviews] = useState<string[]>([]);
  const [instruction, setInstruction] = useState('Create a 1/7 scale commercialized figure of thecharacter in the illustration, in a realistic styie and environment. Place the figure on a computer desk, using a circular transparent acrylic base without any text.On the computer screen, display the ZBrush modeling process of the figure. Next to the computer screen, place a BANDAl-style toy packaging box printedwith the original artwork');
  const [result, setResult] = useState<EditResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string>('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const referenceFileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Sample instructions for inspiration
  const sampleInstructions = [
    "Make this image look like a painting by Vincent van Gogh, with swirling brushstrokes and vibrant colors",
    "Transform this into a cyberpunk style with neon lights and futuristic elements",
    "Convert this to a watercolor painting with soft, flowing colors",
    "Make this look like it was taken in the 1980s with retro styling",
    "Transform this into a fantasy landscape with magical elements and glowing effects",
    "Convert this to a black and white film noir style with dramatic shadows",
    "Make this look like a comic book illustration with bold colors and outlines",
    "Transform this into a dreamy, ethereal scene with soft lighting and pastel tones"
  ];

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, []);

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
          setReferencePreviews(prev => [...prev, ...newReferencePreviews]);
        }
      };
      reader.readAsDataURL(file);
    }

    setError('');
    setReferenceImages(prev => [...prev, ...newReferenceImages]);
  };

  const handleReferenceFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleReferenceFileSelect(e.target.files);
    }
  };

  const removeReferenceImage = (index: number) => {
    setReferenceImages(prev => prev.filter((_, i) => i !== index));
    setReferencePreviews(prev => prev.filter((_, i) => i !== index));
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
    setSelectedImage(null);
    setReferenceImages([]);
    setImagePreview('');
    setReferencePreviews([]);
    setInstruction('');
    setResult(null);
    setError('');
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
                            <button
                              onClick={downloadResult}
                              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200"
                            >
                              💾 Download
                            </button>
                          </div>
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
