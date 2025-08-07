import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { GenerationForm } from './components/GenerationForm';
import { StatusDisplay } from './components/StatusDisplay';
import { useGenerationStore } from './stores/generationStore';
import './App.css';

const queryClient = new QueryClient();

function App() {
  const { currentSession } = useGenerationStore();

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-12 text-center">
              <h1 className="text-4xl md:text-5xl font-light mb-4">
                Multi-Agent 3D Generation
              </h1>
              <p className="text-xl opacity-90">
                Generate high-quality 3D reconstruction images with AI-powered multi-agent system
              </p>
            </div>

            {/* Main Content */}
            <div className="p-8">
              <GenerationForm />
              {currentSession && <StatusDisplay />}
            </div>
          </div>
        </div>
      </div>
    </QueryClientProvider>
  );
}

export default App;
