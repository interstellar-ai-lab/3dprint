import React, { useRef, useEffect, useState } from 'react';
import JSZip from 'jszip';

// Import the Online3DViewer library
import * as OV from 'online-3d-viewer';

interface Online3DViewerProps {
  zipUrl: string;
  isOpen: boolean;
  onClose: () => void;
  modelName: string;
  imagePath?: string;
  onMaterialDataChange?: (data: {
    materialMode: 'full' | 'texture-only' | 'basic';
    materialBlendMode: 'white-base' | 'mtl-tint' | 'auto';
    availableMaterials: {
      hasMTL: boolean;
      hasTextures: boolean;
      textureCount: number;
    };
    onMaterialModeChange: (mode: 'full' | 'texture-only' | 'basic') => void;
    onMaterialBlendModeChange: (mode: 'white-base' | 'mtl-tint' | 'auto') => void;
  }) => void;
}

export const Online3DViewer: React.FC<Online3DViewerProps> = ({ 
  zipUrl, 
  isOpen, 
  onClose, 
  modelName, 
  imagePath, 
  onMaterialDataChange 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [materialMode, setMaterialMode] = useState<'full' | 'texture-only' | 'basic'>('full');
  const [materialBlendMode, setMaterialBlendMode] = useState<'white-base' | 'mtl-tint' | 'auto'>('white-base');
  const [availableMaterials, setAvailableMaterials] = useState<{
    hasMTL: boolean;
    hasTextures: boolean;
    textureCount: number;
  }>({ hasMTL: false, hasTextures: false, textureCount: 0 });

  // Initialize the Online3D Viewer
  const initViewer = () => {
    if (!containerRef.current) return;

    try {
      // Clear any existing content
      containerRef.current.innerHTML = '';

      // Create viewer instance using EmbeddedViewer
      const camera = new OV.Camera(
        new OV.Coord3D(5.0, 5.0, 5.0),
        new OV.Coord3D(0.0, 0.0, 0.0),
        new OV.Coord3D(0.0, 0.0, 1.0),
        45.0
      );

      const parameters = {
        camera: camera,
        backgroundColor: new OV.RGBAColor(245, 245, 245, 255),
        defaultColor: new OV.RGBColor(200, 200, 200),
        defaultLineColor: new OV.RGBColor(0, 0, 0),
        onModelLoaded: () => {
          console.log('Online3DViewer model loaded successfully');
        }
      };

      const viewer = new OV.EmbeddedViewer(containerRef.current, parameters);
      viewerRef.current = viewer;
      console.log('Online3DViewer initialized successfully');
    } catch (err) {
      console.error('Error initializing Online3DViewer:', err);
      setError('Failed to initialize 3D viewer');
    }
  };

  // Load 3D model from zip
  const loadModel = async () => {
    if (!zipUrl || !viewerRef.current) return;

    setLoading(true);
    setError(null);

    try {
      console.log('Loading model from:', zipUrl);

      // Step 1: Use proxy endpoint to fetch the zip file (bypasses CORS)
      const apiBase = process.env.REACT_APP_API_URL || 'https://vicino.ai';
      const proxyUrl = imagePath 
        ? `${apiBase}/api/studio/proxy-zip/${imagePath}`
        : zipUrl;
      
      console.log('Using proxy URL:', proxyUrl);
      
      const response = await fetch(proxyUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch zip file: ${response.statusText}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      
      // Step 2: Unzip the file
      const zip = new JSZip();
      const zipContents = await zip.loadAsync(arrayBuffer);
      
      console.log('Zip contents:', Object.keys(zipContents.files));

      // Step 3: Find 3D model files and materials
      const modelFiles = Object.keys(zipContents.files).filter(filename => {
        const ext = filename.toLowerCase().split('.').pop();
        return ['obj', 'ply', 'stl', 'dae', 'gltf', 'glb', 'fbx', '3ds', '3dm', 'off', 'wrl', '3mf', 'ifc', 'brep', 'step', 'iges'].includes(ext || '');
      });

      const materialFiles = Object.keys(zipContents.files).filter(filename => 
        filename.toLowerCase().endsWith('.mtl')
      );

      const textureFiles = Object.keys(zipContents.files).filter(filename => {
        const ext = filename.toLowerCase().split('.').pop();
        return ['png', 'jpg', 'jpeg', 'bmp', 'tga', 'tiff', 'gif'].includes(ext || '');
      });

      console.log('Found model files:', modelFiles);
      console.log('Found material files:', materialFiles);
      console.log('Found texture files:', textureFiles);

      if (modelFiles.length === 0) {
        throw new Error('No supported 3D model files found in the archive');
      }

      // Set available materials info
      setAvailableMaterials({
        hasMTL: materialFiles.length > 0,
        hasTextures: textureFiles.length > 0,
        textureCount: textureFiles.length
      });

      // Step 4: Load files into Online3DViewer format
      const inputFiles = [];

      // Add model files
      for (const modelFile of modelFiles) {
        const fileData = await zipContents.files[modelFile].async('blob');
        const file = new File([fileData], modelFile);
        inputFiles.push(new OV.InputFile(modelFile, OV.FileSource.File, file));
      }

      // Add material files
      for (const materialFile of materialFiles) {
        const fileData = await zipContents.files[materialFile].async('blob');
        const file = new File([fileData], materialFile);
        inputFiles.push(new OV.InputFile(materialFile, OV.FileSource.File, file));
      }

      // Add texture files
      for (const textureFile of textureFiles) {
        const fileData = await zipContents.files[textureFile].async('blob');
        const file = new File([fileData], textureFile);
        inputFiles.push(new OV.InputFile(textureFile, OV.FileSource.File, file));
      }

      // Load the model using EmbeddedViewer
      viewerRef.current.LoadModelFromInputFiles(inputFiles);

      console.log('Model loading initiated with', inputFiles.length, 'files');

    } catch (err) {
      console.error('Error loading model:', err);
      setError(`Failed to load 3D model: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // Cleanup
  const cleanup = () => {
    if (viewerRef.current) {
      viewerRef.current.Destroy();
      viewerRef.current = null;
    }
  };

  useEffect(() => {
    if (isOpen) {
      initViewer();
      loadModel();
      
      return () => {
        cleanup();
      };
    }
  }, [isOpen]);

  // Watch for material mode changes
  useEffect(() => {
    if (viewerRef.current && materialMode) {
      // Reload model with new material settings
      loadModel();
    }
  }, [materialMode]);

  // Watch for material blend mode changes
  useEffect(() => {
    if (viewerRef.current && materialBlendMode) {
      // Reload model with new material settings
      loadModel();
    }
  }, [materialBlendMode]);

  // Notify parent component when material data changes
  useEffect(() => {
    if (onMaterialDataChange) {
      onMaterialDataChange({
        materialMode,
        materialBlendMode,
        availableMaterials,
        onMaterialModeChange: setMaterialMode,
        onMaterialBlendModeChange: setMaterialBlendMode
      });
    }
  }, [materialMode, materialBlendMode, availableMaterials, onMaterialDataChange]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (viewerRef.current) {
        viewerRef.current.Resize();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isOpen]);

  return (
    <div className="w-full h-full relative overflow-hidden">
      {/* 3D Canvas Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-900 to-black">
        <div 
          ref={containerRef} 
          className="w-full h-full"
          style={{ minHeight: '400px' }}
        />
      </div>

      {/* Modern Loading State */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur">
          <div className="text-center">
            <div className="relative mb-6">
              <div className="w-16 h-16 border-4 border-purple-500/20 rounded-full mx-auto"></div>
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-16 h-16 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Loading 3D Model</h3>
            <p className="text-white/60 mb-1">Processing with Online3DViewer...</p>
            <p className="text-white/40 text-sm">{modelName}</p>
            <div className="mt-4 w-48 bg-white/10 rounded-full h-1 mx-auto">
              <div className="bg-gradient-to-r from-purple-500 to-purple-700 h-1 rounded-full animate-pulse" style={{ width: '70%' }}></div>
            </div>
          </div>
        </div>
      )}

      {/* Modern Error State */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Failed to Load Model</h3>
            <p className="text-white/60 mb-6 leading-relaxed">{error}</p>
            <button
              onClick={loadModel}
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-700 text-white rounded-lg hover:from-purple-600 hover:to-purple-800 transition-all font-medium flex items-center mx-auto"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Enhanced Controls Guide */}
      {!loading && !error && (
        <div className="absolute bottom-6 left-6 bg-black/20 backdrop-blur-md border border-white/10 rounded-xl p-4 text-white text-sm max-w-xs">
          <h4 className="font-semibold mb-3 flex items-center">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Controls
          </h4>
          <div className="space-y-2">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-purple-400 rounded-full mr-3"></div>
              <span className="text-white/80">Left drag: Rotate</span>
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
              <span className="text-white/80">Right drag: Pan</span>
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
              <span className="text-white/80">Scroll: Zoom</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-white/10 text-xs text-white/60">
            Engine: Online3DViewer • Multi-format support
          </div>
        </div>
      )}

      {/* Viewport Toolbar */}
      {!loading && !error && (
        <div className="absolute top-6 right-6 flex items-center space-x-2">
          <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg px-3 py-2 text-white text-sm">
            <span className="text-white/60">Engine: </span>
            <span className="text-green-400 font-medium">Online3DViewer</span>
          </div>
          <button className="p-2 bg-black/20 backdrop-blur-md border border-white/10 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-all">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};
