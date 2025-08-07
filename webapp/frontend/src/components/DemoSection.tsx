import React from 'react';
import { GenerationForm } from './GenerationForm';
import { StatusDisplay } from './StatusDisplay';
import { useGenerationStore } from '../stores/generationStore';

export const DemoSection: React.FC = () => {
  const { currentSession } = useGenerationStore();

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
              <p className="opacity-90">
                Enter a target object and watch our multi-agent system generate high-fidelity 3D assets
              </p>
            </div>

            {/* Demo Content */}
            <div className="p-8">
              <GenerationForm />
              {currentSession && <StatusDisplay />}
            </div>
          </div>
        </div>

        {/* Features Highlight */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
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
        </div>
      </div>
    </section>
  );
};
