import React, { useState, useEffect } from 'react';
import { ThreeViewer } from './ThreeViewer';
import { Online3DViewer } from './Online3DViewer';
import { OrderModal } from './OrderModal';
import { ImageCard } from './ImageCard';

// Interface matching the generated_images table schema
interface GeneratedImage {
  // Database fields from generated_images table
  id: number;
  created_at: string | null;
  target_object: string | null;
  iteration: number | null;
  image_url: string;
  "3d_url": string | null;
}

// Extended interface for frontend display with computed fields
interface StudioImage extends GeneratedImage {
  // Additional computed/display fields
  name: string;
  filename: string;
  size: number;
  updated: string | null;
  content_type: string;
  public_url: string;
  thumbnail_url: string;
  zipurl?: string | null;
  has_3d_model?: boolean;
  authenticated_url?: string;
  model_3d_url?: string;
}

interface BucketInfo {
  name: string;
  location: string;
  storage_class: string;
  created: string | null;
  updated: string | null;
}

export const Studio: React.FC = () => {
  const [images, setImages] = useState<StudioImage[]>([]);
  const [bucketInfo, setBucketInfo] = useState<BucketInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);

  const [selected3DModel, setSelected3DModel] = useState<StudioImage | null>(null);
  const [orderModalOpen, setOrderModalOpen] = useState(false);
  const [viewerEngine, setViewerEngine] = useState<'threejs' | 'online3d'>('threejs');

  // API base URL - adjust this according to your backend setup
  const API_BASE = process.env.REACT_APP_API_URL || 'https://vicino.ai';

  const fetchImages = async (search: string = '') => {
    try {
      setSearchLoading(true);
      // Use Supabase endpoint for data storage
      const url = new URL(`${API_BASE}/api/studio/supabase/images`);
      if (search) {
        url.searchParams.append('search', search);
      }
      url.searchParams.append('max_results', '50');
      
      const response = await fetch(url.toString());
      const data = await response.json();
      
      if (data.success) {
        setImages(data.images);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch images');
      }
    } catch (err) {
      setError('Network error: Failed to fetch images');
      console.error('Error fetching images:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  // Bucket info is not needed for Supabase storage
  const fetchBucketInfo = async () => {
    // Bucket info is not needed for Supabase storage
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchImages(), fetchBucketInfo()]);
      setLoading(false);
    };
    
    loadData();
  }, []);

  // Auto-select the first 3D model when images are loaded
  useEffect(() => {
    console.log('🎯 Auto-select useEffect triggered:', { 
      imagesCount: images.length, 
      hasSelected: !!selected3DModel 
    });
    
    if (images.length > 0 && !selected3DModel) {
      const first3DModel = images.find(img => img.has_3d_model && (img.zipurl || img.model_3d_url));
      if (first3DModel) {
        console.log('🎯 Auto-selecting first 3D model:', {
          name: first3DModel.filename,
          model_3d_url: first3DModel.model_3d_url ? first3DModel.model_3d_url.substring(0, 50) + '...' : null,
          zipurl: first3DModel.zipurl ? first3DModel.zipurl.substring(0, 50) + '...' : null
        });
        setSelected3DModel(first3DModel);
      } else {
        console.log('❌ No 3D models found in images');
      }
    }
  }, [images, selected3DModel]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchImages(searchQuery);
  };

  const handleImageClick = (image: StudioImage) => {
    // Select the image for 3D viewing instead of opening modal
    setSelected3DModel(image);
  };

  const handle3DViewClick = (image: StudioImage, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    setSelected3DModel(image);
  };

  const handleOrderClick = (event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation();
    }
    setOrderModalOpen(true);
  };

  const handleBackClick = () => {
    // Try to close the window if it was opened by another window
    if (window.opener) {
      window.close();
    } else {
      // Otherwise navigate back to home
      const baseUrl = process.env.REACT_APP_BASE_URL || window.location.origin;
      window.location.href = baseUrl;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Studio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Modern Header with Glass Effect */}
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20 sticky top-0 z-40">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <button
                onClick={handleBackClick}
                className="flex items-center text-white/70 hover:text-white transition-all duration-200 group"
              >
                <svg className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">Vicino 3D Studio</h1>
                <p className="text-white/60 text-sm">
                  Professional 3D Model Viewer
                  <span className="text-white/40 ml-2">
                    • {images.length} models available
                  </span>
                </p>
              </div>
            </div>
            
            {/* Modern Search */}
            <form onSubmit={handleSearch} className="flex">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search models..."
                  className="pl-10 pr-4 py-2 bg-white/10 backdrop-blur border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400/50 focus:border-purple-400/50 transition-all w-64"
                />
                <svg className="w-5 h-5 text-white/50 absolute left-3 top-1/2 transform -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <button
                type="submit"
                disabled={searchLoading}
                className="ml-2 px-4 py-2 bg-purple-500/20 backdrop-blur text-white rounded-lg hover:bg-purple-500/30 transition-all disabled:opacity-50 border border-purple-400/30"
              >
                {searchLoading ? '⟳' : '→'}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Modern Layout - Three Panel Design */}
      <div className="flex h-screen">
        {/* Left Sidebar - Model Library */}
        <div className="w-80 bg-slate-900/50 backdrop-blur border-r border-purple-500/20 overflow-y-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Model Library</h2>
              <div className="text-sm text-white/60">{images.length} models</div>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-4">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-red-400 mr-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-red-300 text-sm">{error}</p>
                </div>
              </div>
            )}

            {images.length === 0 && !error ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
                  <svg className="w-8 h-8 text-white/40" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h3 className="text-white/70 font-medium mb-2">No models found</h3>
                <p className="text-white/50 text-sm">
                  {searchQuery ? 'Try a different search term.' : 'The database is empty or not accessible.'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {images.map((image) => (
                  <ImageCard
                    key={image.id || image.name}
                    // Database fields
                    id={image.id}
                    created_at={image.created_at}
                    target_object={image.target_object}
                    iteration={image.iteration}
                    image_url={image.image_url}
                    model_3d_url={image.model_3d_url || image["3d_url"]}
                    
                    // Display fields
                    name={image.name}
                    filename={image.filename}
                    size={image.size}
                    updated={image.updated}
                    content_type={image.content_type}
                    public_url={image.public_url}
                    thumbnail_url={image.thumbnail_url}
                    zipurl={image.zipurl}
                    has_3d_model={image.has_3d_model}
                    authenticated_url={image.authenticated_url}
                    
                    // UI state
                    isSelected={selected3DModel?.name === image.name}
                    onClick={() => handleImageClick(image)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Center Panel - 3D Viewer */}
        <div className="flex-1 flex flex-col bg-gradient-to-br from-slate-800/50 to-slate-900/50">
          {selected3DModel ? (
            <div className="flex flex-col h-full">
              {/* Viewer Header */}
              <div className="bg-white/5 backdrop-blur border-b border-white/10 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-700 rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">{selected3DModel.filename}</h3>
                      <p className="text-white/60 text-sm flex items-center">
                        <span className="w-2 h-2 bg-purple-400 rounded-full mr-2 animate-pulse"></span>
                        Interactive 3D Model
                      </p>
                    </div>
                  </div>
                  
                  {/* Viewer Controls */}
                  <div className="flex items-center space-x-2">
                    {/* Engine Selector */}
                    <div className="flex items-center bg-white/10 rounded-lg p-1">
                      <button
                        onClick={() => setViewerEngine('threejs')}
                        className={`px-3 py-1 text-xs rounded-md transition-all ${
                          viewerEngine === 'threejs' 
                            ? 'bg-purple-500 text-white shadow-lg' 
                            : 'text-white/70 hover:text-white hover:bg-white/10'
                        }`}
                      >
                        Three.js
                      </button>
                      <button
                        onClick={() => setViewerEngine('online3d')}
                        className={`px-3 py-1 text-xs rounded-md transition-all ${
                          viewerEngine === 'online3d' 
                            ? 'bg-green-500 text-white shadow-lg' 
                            : 'text-white/70 hover:text-white hover:bg-white/10'
                        }`}
                      >
                        Online3D
                      </button>
                    </div>

                    <button className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-white/70 hover:text-white">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                      </svg>
                    </button>
                    <button className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-white/70 hover:text-white">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <button 
                      onClick={() => setSelected3DModel(null)}
                      className="p-2 bg-white/10 hover:bg-red-500/20 rounded-lg transition-colors text-white/70 hover:text-red-400"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
              
              {/* 3D Viewport */}
              <div className="flex-1 relative">
                {viewerEngine === 'threejs' ? (
                  <ThreeViewer
                    modelUrl={selected3DModel.model_3d_url || selected3DModel.zipurl || ''}
                    isOpen={true}
                    embedded={true}
                    onClose={() => setSelected3DModel(null)}
                    modelName={selected3DModel.target_object || selected3DModel.filename}
                  />
                ) : (
                  <Online3DViewer
                    zipUrl={selected3DModel.model_3d_url || selected3DModel.zipurl || ''}
                    isOpen={true}
                    onClose={() => setSelected3DModel(null)}
                    modelName={selected3DModel.filename}
                  />
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-md">
                <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-purple-500/20 to-purple-300/20 flex items-center justify-center backdrop-blur border border-purple-300/20">
                  <svg className="w-12 h-12 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Welcome to 3D Studio</h3>
                <p className="text-white/60 leading-relaxed">
                  Select a model from the library to begin exploring in 3D. 
                  Use your mouse to rotate, zoom, and interact with the models.
                </p>
                <div className="mt-6 flex items-center justify-center space-x-6 text-sm text-white/40">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-purple-400 rounded-full mr-2"></div>
                    Drag to rotate
                  </div>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
                    Scroll to zoom
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Properties & Details */}
        <div className="w-80 bg-slate-900/30 backdrop-blur border-l border-purple-500/20 overflow-y-auto">
          {selected3DModel ? (
            <div className="p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Model Properties</h2>
              
              {/* Model Info */}
              <div className="bg-white/5 rounded-lg p-4 mb-4 backdrop-blur border border-white/10">
                <h3 className="text-white font-medium mb-3">Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-white/60">File name:</span>
                    <span className="text-white">{selected3DModel.filename}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/60">Last updated:</span>
                    <span className="text-white">{formatDate(selected3DModel.updated || selected3DModel.created_at || null)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/60">Type:</span>
                    <span className="text-white">{selected3DModel.content_type}</span>
                  </div>
                  {selected3DModel.target_object && (
                    <div className="flex justify-between">
                      <span className="text-white/60">Target Object:</span>
                      <span className="text-white">{selected3DModel.target_object}</span>
                    </div>
                  )}
                  {selected3DModel.iteration && (
                    <div className="flex justify-between">
                      <span className="text-white/60">Iteration:</span>
                      <span className="text-white">{selected3DModel.iteration}</span>
                    </div>
                  )}
                </div>
              </div>



              {/* Actions */}
              <div className="space-y-3">
                {/* Order 3D Print Button */}
                <button
                  onClick={handleOrderClick}
                  className="flex items-center justify-center w-full px-4 py-3 bg-gradient-to-r from-green-500 to-green-700 text-white rounded-lg hover:from-green-600 hover:to-green-800 transition-all font-medium shadow-lg"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                  </svg>
                  Order 3D Print
                </button>

                <a
                  href={selected3DModel.public_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-700 text-white rounded-lg hover:from-purple-600 hover:to-purple-800 transition-all font-medium"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  View Original Image
                </a>
                
                {(selected3DModel.model_3d_url || selected3DModel.zipurl) && (
                  <a
                    href={selected3DModel.model_3d_url || selected3DModel.zipurl || ''}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center w-full px-4 py-3 bg-white/10 backdrop-blur text-white rounded-lg hover:bg-white/20 transition-all border border-white/20"
                  >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                    </svg>
                    Download 3D Model
                  </a>
                )}
              </div>
            </div>
          ) : (
            <div className="p-4">
              <h2 className="text-lg font-semibold text-white mb-4">Properties</h2>
              <div className="text-center py-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
                  <svg className="w-8 h-8 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-white/50 text-sm">Select a model to view its properties and details.</p>
              </div>
            </div>
          )}
        </div>
      </div>



      {/* Order Modal */}
      {orderModalOpen && selected3DModel && (
        <OrderModal
          isOpen={orderModalOpen}
          onClose={() => setOrderModalOpen(false)}
          modelName={selected3DModel.filename}
          modelImage={selected3DModel.public_url}
        />
      )}

    </div>
  );
};
