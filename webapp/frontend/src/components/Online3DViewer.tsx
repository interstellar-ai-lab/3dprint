import React, { useRef, useEffect, useState } from 'react';

interface Online3DViewerProps {
  modelUrl: string;
  isOpen: boolean;
  onClose: () => void;
  modelName: string;
  embedded?: boolean;
}

export const Online3DViewer: React.FC<Online3DViewerProps> = ({ 
  modelUrl, 
  isOpen, 
  onClose, 
  modelName,
  embedded = false
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !modelUrl) return;

    setLoading(true);
    setError(null);

    // Download the model and create a temporary blob URL
    const downloadAndDisplayModel = async () => {
      try {
        const response = await fetch(modelUrl);
        if (!response.ok) {
          throw new Error(`Failed to download model: ${response.status} ${response.statusText}`);
        }
        
        const blob = await response.blob();
        const tempBlobUrl = URL.createObjectURL(blob);
        setBlobUrl(tempBlobUrl);
        
        // Create the 3D viewer iframe
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
          
          const iframe = document.createElement('iframe');
          const viewerUrl = `https://3dviewer.net/embed/?url=${encodeURIComponent(tempBlobUrl)}`;
          
          iframe.src = viewerUrl;
          iframe.style.width = '100%';
          iframe.style.height = '100%';
          iframe.style.border = 'none';
          iframe.style.borderRadius = '8px';
          
          iframe.onload = () => {
            setLoading(false);
          };
          
          iframe.onerror = () => {
            setError('Failed to load 3D model');
            setLoading(false);
          };
          
          containerRef.current.appendChild(iframe);
        }
      } catch (err) {
        console.error('Error downloading model:', err);
        setError(err instanceof Error ? err.message : 'Failed to download 3D model');
        setLoading(false);
      }
    };

    downloadAndDisplayModel();

    return () => {
      // Clean up the blob URL when component unmounts or modelUrl changes
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
        setBlobUrl(null);
      }
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [isOpen, modelUrl]);

  // Cleanup blob URL when component unmounts
  useEffect(() => {
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [blobUrl]);

  if (!isOpen) return null;

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

      {/* Loading State */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur">
          <div className="text-center">
            <div className="relative mb-6">
              <div className="w-16 h-16 border-4 border-green-500/20 rounded-full mx-auto"></div>
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-16 h-16 border-4 border-transparent border-t-green-500 rounded-full animate-spin"></div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Loading 3D Model</h3>
            <p className="text-white/60">Online3DViewer...</p>
            <p className="text-white/40 text-sm">{modelName}</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3">Failed to Load Model</h3>
            <p className="text-white/60 mb-6">{error}</p>
          </div>
        </div>
      )}

      {/* Controls Guide */}
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
              <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
              <span className="text-white/80">Drag: Rotate</span>
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
              <span className="text-white/80">Scroll: Zoom</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-white/10 text-xs text-white/60">
            Engine: Online3DViewer
          </div>
        </div>
      )}

      {/* Engine Badge */}
      {!loading && !error && (
        <div className="absolute top-6 right-6">
          <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg px-3 py-2 text-white text-sm">
            <span className="text-white/60">Engine: </span>
            <span className="text-green-400 font-medium">Online3DViewer</span>
          </div>
        </div>
      )}
    </div>
  );
};
