import React from 'react';

interface ImageData {
  public_url: string;
  gcs_image_path: string;
  zipurl?: string;
  has_3d?: boolean;
  size?: number;
  updated?: string;
}

interface ImageCardProps {
  img: ImageData;
  onView3D: (zipurl: string) => void;
  onGenerate3D: () => void;
}

export const ImageCard: React.FC<ImageCardProps> = ({ img, onView3D, onGenerate3D }) => {
  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
      <img
        src={img.public_url}
        alt={img.gcs_image_path}
        className="w-full h-auto object-contain bg-gray-100"
        data-attempt="0"
        onError={(e) => {
          const el = e.currentTarget as HTMLImageElement;
          const attempt = el.getAttribute('data-attempt') || '0';
          if (attempt === '0') {
            el.setAttribute('data-attempt', '1');
            el.src = `http://localhost:8001/api/gcs-image/${encodeURIComponent(img.gcs_image_path)}`;
          } else {
            el.src = '/placeholder-image.png';
          }
        }}
      />
      <div className="p-4">
        {/* 3D Model Actions */}
        <div className="flex gap-2">
          {img.has_3d && img.zipurl ? (
            <button
              onClick={() => onView3D(img.zipurl!)}
              className="flex-1 px-3 py-2 bg-green-600 text-white text-center rounded-lg hover:bg-green-700 transition-colors text-sm"
            >
              🎯 View 3D
            </button>
          ) : (
            <button
              onClick={onGenerate3D}
              className="flex-1 px-3 py-2 bg-orange-600 text-white text-center rounded-lg hover:bg-orange-700 transition-colors text-sm"
            >
              🏗️ Generate 3D
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
