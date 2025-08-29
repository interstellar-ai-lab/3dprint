import React, { useState } from 'react';
import { GenerationForm } from './GenerationForm';
import { MultiViewUploadForm } from './MultiViewUploadForm';
import { SingleImageUploadForm } from './SingleImageUploadForm';
import { NanoBanana } from './NanoBanana';
import { StatusDisplay } from './StatusDisplay';
import { useGenerationStore } from '../stores/generationStore';

export const DemoSection: React.FC = () => {
  const { currentSession } = useGenerationStore();
  const [mode, setMode] = useState<'ai' | 'upload' | 'single' | 'nano'>('nano');

  const handleUploadSuccess = (data: any) => {
    // Handle successful upload - could set a session or show success message
    console.log('Upload successful:', data);
    // You might want to redirect to a status page or show the 3D model
  };

  const handleUploadError = (error: any) => {
    console.error('Upload failed:', error);
  };

  return (
    <section className="py-20 bg-gradient-to-br from-purple-50 to-blue-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Try Our Multi-Agent 3D Generation
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience the power of our revolutionary multi-agent system. Generate high-quality 
            3D reconstruction images with AI-powered collaboration and real-time refinement.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
            {/* Demo Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-8 text-center">
              <h3 className="text-2xl font-bold mb-2">
                Live Demo
              </h3>
              <p className="opacity-90 mb-6">
                Choose your preferred method to generate high-fidelity 3D assets
              </p>
              
              {/* Mode Toggle */}
              <div className="flex justify-center">
                <div className="bg-white/20 rounded-lg p-1 flex flex-wrap gap-1">
                  <button
                    onClick={() => setMode('nano')}
                    className={`px-4 py-2 rounded-md font-medium transition-all duration-200 text-sm ${
                      mode === 'nano'
                        ? 'bg-white text-purple-600 shadow-sm'
                        : 'text-white hover:bg-white/10'
                    }`}
                  >
                    🎨 AI Image Edit
                  </button>
                  <button
                    onClick={() => setMode('ai')}
                    className={`px-4 py-2 rounded-md font-medium transition-all duration-200 text-sm ${
                      mode === 'ai'
                        ? 'bg-white text-purple-600 shadow-sm'
                        : 'text-white hover:bg-white/10'
                    }`}
                  >
                    🤖 AI Generation
                  </button>
                  <button
                    onClick={() => setMode('single')}
                    className={`px-4 py-2 rounded-md font-medium transition-all duration-200 text-sm ${
                      mode === 'single'
                        ? 'bg-white text-purple-600 shadow-sm'
                        : 'text-white hover:bg-white/10'
                    }`}
                  >
                    📷 Image to 3D
                  </button>
                  <button
                    onClick={() => setMode('upload')}
                    className={`px-4 py-2 rounded-md font-medium transition-all duration-200 text-sm ${
                      mode === 'upload'
                        ? 'bg-white text-purple-600 shadow-sm'
                        : 'text-white hover:bg-white/10'
                    }`}
                  >
                    📤 Multi-View
                  </button>
                </div>
              </div>
            </div>

            {/* Demo Content */}
            <div className="p-8">
              {mode === 'ai' ? (
                <GenerationForm />
              ) : mode === 'nano' ? (
                <NanoBanana />
              ) : mode === 'single' ? (
                <SingleImageUploadForm 
                  onSuccess={handleUploadSuccess}
                  onError={handleUploadError}
                />
              ) : (
                <MultiViewUploadForm 
                  onSuccess={handleUploadSuccess}
                  onError={handleUploadError}
                />
              )}
              {currentSession && <StatusDisplay />}
            </div>
          </div>
        </div>

        {/* Features Highlight */}
        {/* <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-white rounded-xl p-6 shadow-lg text-center">
            <div className="text-3xl mb-4">🎯</div>
            <h4 className="text-lg font-bold text-gray-900 mb-2">Production-Ready Output</h4>
            <p className="text-gray-600 text-sm">
              Export-ready assets with precise stylistic control and structural integrity
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg text-center">
            <div className="text-3xl mb-4">🤖</div>
            <h4 className="text-lg font-bold text-gray-900 mb-2">Multi-Agent Collaboration</h4>
            <p className="text-gray-600 text-sm">
              Intelligent agents work together to refine and improve generation quality
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg text-center">
            <div className="text-3xl mb-4">⚡</div>
            <h4 className="text-lg font-bold text-gray-900 mb-2">Real-time Control</h4>
            <p className="text-gray-600 text-sm">
              Interactive refinement and customization through conversational workflow
            </p>
          </div>
        </div> */}
      </div>
    </section>
  );
};
