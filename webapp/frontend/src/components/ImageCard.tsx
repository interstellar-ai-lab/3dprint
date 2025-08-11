import React from 'react';

interface ImageCardProps {
  // Database fields from generated_images table
  id: number;
  created_at: string | null;
  target_object: string | null;
  iteration: number | null;
  image_url: string;
  model_3d_url: string | null;
  
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
  
  // UI state
  isSelected: boolean;
  onClick: () => void;
}

export const ImageCard: React.FC<ImageCardProps> = ({
  id,
  created_at,
  target_object,
  iteration,
  image_url,
  model_3d_url,
  name,
  filename,
  size,
  updated,
  content_type,
  public_url,
  thumbnail_url,
  zipurl,
  has_3d_model,
  authenticated_url,
  isSelected,
  onClick
}) => {
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Unknown date';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid date';
      
      const now = new Date();
      const diffInMs = now.getTime() - date.getTime();
      const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
      const diffInHours = Math.floor(diffInMinutes / 60);
      const diffInDays = Math.floor(diffInHours / 24);
      
      if (diffInMinutes < 1) return 'Just now';
      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
      if (diffInHours < 24) return `${diffInHours}h ago`;
      if (diffInDays < 7) return `${diffInDays}d ago`;
      
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      });
    } catch (error) {
      return 'Invalid date';
    }
  };

  const displayName = target_object || filename || `Image ${id}`;
  const displayDate = updated || created_at;

  return (
    <div
      className={`group relative rounded-xl overflow-hidden transition-all duration-300 cursor-pointer ${
        isSelected
          ? 'bg-gradient-to-r from-purple-600/30 to-purple-400/20 border border-purple-400/50 shadow-lg shadow-purple-500/20' 
          : 'bg-white/5 backdrop-blur border border-white/10 hover:bg-white/10 hover:border-purple-300/20'
      }`}
      onClick={onClick}
    >
      <div className="flex p-3">
        {/* Thumbnail */}
        <div className="relative w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
          <img
            src={public_url}
            alt={displayName}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={(e) => {
              // Fallback for broken images
              (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjMzc0MTUxIi8+CjxwYXRoIGQ9Ik0yMCAyMEw0NCA0NE0yMCA0NEw0NCAyMCIgc3Ryb2tlPSIjOUI5Qjk5IiBzdHJva2Utd2lkdGg9IjIiLz4KPC9zdmc+';
            }}
          />
          {has_3d_model && (
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
          <h3 className="font-medium text-white truncate text-sm" title={displayName}>
            {displayName}
          </h3>
          <div className="mt-1 space-y-1">
            <p className="text-white/40 text-xs">{formatDate(displayDate)}</p>
            {iteration && (
              <p className="text-white/40 text-xs">Iteration: {iteration}</p>
            )}
            <p className="text-white/40 text-xs">ID: {id}</p>
          </div>
          {has_3d_model && (zipurl || model_3d_url) && (
            <div className="mt-2">
              <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-purple-600/20 text-purple-300 rounded-full">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd"/>
                </svg>
                3D Model
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col items-end justify-between">
          <div className="flex space-x-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                window.open(public_url, '_blank');
              }}
              className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md bg-white/10 hover:bg-white/20 text-white/70 hover:text-white"
              title="Open image in new tab"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
              </svg>
            </button>
            {has_3d_model && (zipurl || model_3d_url) && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  const downloadUrl = zipurl || model_3d_url;
                  if (downloadUrl) {
                    window.open(downloadUrl, '_blank');
                  }
                }}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 hover:text-purple-200"
                title="Download 3D model"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
              </button>
            )}
          </div>
          {iteration && (
            <div className="text-xs text-white/30 font-mono">
              #{iteration}
            </div>
          )}
        </div>
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute inset-0 ring-2 ring-purple-400/50 rounded-xl pointer-events-none"></div>
      )}
    </div>
  );
};
