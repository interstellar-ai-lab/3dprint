import React, { useState, useEffect } from 'react';
import { ThreeViewer } from './ThreeViewer';

interface StudioImage {
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
  const [selectedImage, setSelectedImage] = useState<StudioImage | null>(null);
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [selected3DModel, setSelected3DModel] = useState<StudioImage | null>(null);
  
  // Material settings state
  const [materialData, setMaterialData] = useState<{
    materialMode: 'full' | 'texture-only' | 'basic';
    availableMaterials: {
      hasMTL: boolean;
      hasTextures: boolean;
      textureCount: number;
    };
    onMaterialModeChange: (mode: 'full' | 'texture-only' | 'basic') => void;
  } | null>(null);

  // API base URL - adjust this according to your backend setup
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8001';

  const fetchImages = async (search: string = '') => {
    try {
      setSearchLoading(true);
      const url = new URL(`${API_BASE}/api/studio/images`);
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

  const fetchBucketInfo = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/studio/bucket-info`);
      const data = await response.json();
      
      if (data.success) {
        setBucketInfo(data.bucket_info);
      } else {
        console.error('Failed to fetch bucket info:', data.error);
      }
    } catch (err) {
      console.error('Error fetching bucket info:', err);
    }
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
    if (images.length > 0 && !selected3DModel) {
      const first3DModel = images.find(img => img.has_3d_model && img.zipurl);
      if (first3DModel) {
        setSelected3DModel(first3DModel);
      }
    }
  }, [images, selected3DModel]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchImages(searchQuery);
  };

  const handleImageClick = (image: StudioImage) => {
    setSelectedImage(image);
    setImageModalOpen(true);
  };

  const handle3DViewClick = (image: StudioImage, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation(); // Prevent triggering the image modal
    }
    setSelected3DModel(image);
  };

  const handleBackClick = () => {
    // Try to close the window if it was opened by another window
    if (window.opener) {
      window.close();
    } else {
      // Otherwise navigate back to home
      window.location.href = 'http://localhost:8000';
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
                  {bucketInfo && (
                    <span className="text-white/40 ml-2">
                      • {images.length} models available
                    </span>
                  )}
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
                  {searchQuery ? 'Try a different search term.' : 'The library is empty or not accessible.'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {images.map((image) => (
                  <div
                    key={image.name}
                    className={`group relative rounded-xl overflow-hidden transition-all duration-300 cursor-pointer ${
                      selected3DModel?.name === image.name 
                        ? 'bg-gradient-to-r from-purple-600/30 to-purple-400/20 border border-purple-400/50 shadow-lg shadow-purple-500/20' 
                        : 'bg-white/5 backdrop-blur border border-white/10 hover:bg-white/10 hover:border-purple-300/20'
                    }`}
                    onClick={() => handleImageClick(image)}
                  >
                    <div className="flex p-3">
                      {/* Thumbnail */}
                      <div className="relative w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
                        <img
                          src={image.public_url}
                          alt={image.filename}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        {image.has_3d_model && (
                          <div className="absolute inset-0 bg-gradient-to-t from-purple-600/80 to-transparent">
                            <div className="absolute bottom-1 right-1">
                              <div className="w-4 h-4 bg-white rounded-full flex items-center justify-center">
                                <svg className="w-3 h-3 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Info */}
                      <div className="ml-3 flex-1 min-w-0">
                        <h3 className="font-medium text-white truncate text-sm" title={image.filename}>
                          {image.filename}
                        </h3>
                        <div className="mt-1 space-y-1">
                          <p className="text-white/60 text-xs">{formatFileSize(image.size)}</p>
                          <p className="text-white/40 text-xs">{formatDate(image.updated)}</p>
                        </div>
                        {image.has_3d_model && image.zipurl && (
                          <button
                            onClick={(e) => handle3DViewClick(image, e)}
                            className={`mt-2 px-3 py-1 text-xs rounded-md transition-all flex items-center ${
                              selected3DModel?.name === image.name 
                                ? 'bg-purple-500 text-white shadow-lg' 
                                : 'bg-white/10 text-white/80 hover:bg-white/20'
                            }`}
                          >
                            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {selected3DModel?.name === image.name ? 'Viewing' : 'View 3D'}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Selection indicator */}
                    {selected3DModel?.name === image.name && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-purple-400 to-purple-600"></div>
                    )}
                  </div>
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
                <ThreeViewer
                  zipUrl={selected3DModel.zipurl || ''}
                  isOpen={true}
                  onClose={() => setSelected3DModel(null)}
                  modelName={selected3DModel.filename}
                  imagePath={selected3DModel.name}
                  onMaterialDataChange={setMaterialData}
                />
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
                    <span className="text-white/60">File size:</span>
                    <span className="text-white">{formatFileSize(selected3DModel.size)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/60">Last updated:</span>
                    <span className="text-white">{formatDate(selected3DModel.updated)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/60">Type:</span>
                    <span className="text-white">{selected3DModel.content_type}</span>
                  </div>
                </div>
              </div>

              {/* Material Settings */}
              {materialData && (materialData.availableMaterials.hasMTL || materialData.availableMaterials.hasTextures) && (
                <div className="bg-white/5 rounded-lg p-4 mb-4 backdrop-blur border border-white/10">
                  <h3 className="text-white font-medium mb-3 flex items-center">
                    <svg className="w-4 h-4 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5H9m12 0v12a4 4 0 01-4 4H9" />
                    </svg>
                    Material Settings
                  </h3>
                  
                  <div className="space-y-3">
                    {/* Full Material Option */}
                    {materialData.availableMaterials.hasMTL && materialData.availableMaterials.hasTextures && (
                      <label className="flex items-center space-x-3 cursor-pointer group">
                        <input
                          type="radio"
                          name="materialMode"
                          value="full"
                          checked={materialData.materialMode === 'full'}
                          onChange={(e) => materialData.onMaterialModeChange(e.target.value as 'full' | 'texture-only' | 'basic')}
                          className="w-4 h-4 text-purple-500 border-white/30 focus:ring-purple-500 focus:ring-2 bg-transparent"
                        />
                        <span className="text-white text-sm group-hover:text-purple-300 transition-colors">Full Material + Texture</span>
                      </label>
                    )}
                    
                    {/* Texture Only Option */}
                    {materialData.availableMaterials.hasTextures && (
                      <label className="flex items-center space-x-3 cursor-pointer group">
                        <input
                          type="radio"
                          name="materialMode"
                          value="texture-only"
                          checked={materialData.materialMode === 'texture-only'}
                          onChange={(e) => materialData.onMaterialModeChange(e.target.value as 'full' | 'texture-only' | 'basic')}
                          className="w-4 h-4 text-purple-500 border-white/30 focus:ring-purple-500 focus:ring-2 bg-transparent"
                        />
                        <span className="text-white text-sm group-hover:text-purple-300 transition-colors">
                          Texture Only ({materialData.availableMaterials.textureCount})
                        </span>
                      </label>
                    )}
                    
                    {/* Basic Material Option */}
                    <label className="flex items-center space-x-3 cursor-pointer group">
                      <input
                        type="radio"
                        name="materialMode"
                        value="basic"
                        checked={materialData.materialMode === 'basic'}
                        onChange={(e) => materialData.onMaterialModeChange(e.target.value as 'full' | 'texture-only' | 'basic')}
                        className="w-4 h-4 text-purple-500 border-white/30 focus:ring-purple-500 focus:ring-2 bg-transparent"
                      />
                      <span className="text-white text-sm group-hover:text-purple-300 transition-colors">Basic Material</span>
                    </label>
                  </div>
                  
                  {/* Material Info */}
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <div className="text-xs text-white/60 space-y-2">
                      {materialData.availableMaterials.hasMTL && (
                        <div className="flex items-center">
                          <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                          MTL Material Available
                        </div>
                      )}
                      {materialData.availableMaterials.hasTextures && (
                        <div className="flex items-center">
                          <div className="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
                          {materialData.availableMaterials.textureCount} Texture(s) Available
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="space-y-3">
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
                
                {selected3DModel.zipurl && (
                  <a
                    href={selected3DModel.zipurl}
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

      {/* Image Modal */}
      {imageModalOpen && selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-medium text-gray-900">{selectedImage.filename}</h3>
              <button
                onClick={() => setImageModalOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1">
                  <img
                    src={selectedImage.public_url}
                    alt={selectedImage.filename}
                    className="w-full h-auto max-h-96 object-contain rounded"
                  />
                </div>
                <div className="lg:w-80 space-y-2">
                  <div>
                    <span className="font-medium text-gray-700">Size:</span>
                    <span className="ml-2 text-gray-600">{formatFileSize(selectedImage.size)}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Type:</span>
                    <span className="ml-2 text-gray-600">{selectedImage.content_type}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Updated:</span>
                    <span className="ml-2 text-gray-600">{formatDate(selectedImage.updated)}</span>
                  </div>
                  <div className="pt-2 space-y-2">
                    <a
                      href={selectedImage.public_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors mr-2"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Open Original
                    </a>
                    {selectedImage.zipurl && (
                      <a
                        href={selectedImage.zipurl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                        </svg>
                        Download 3D Model
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}


    </div>
  );
};
