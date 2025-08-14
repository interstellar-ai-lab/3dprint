import React from 'react';

export const Hero: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-700 text-white px-8 py-16 text-center relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent"></div>
      </div>
      
      <div className="relative z-10">
        <div className="mb-6 space-y-3">
          <div className="inline-block bg-gradient-to-r from-blue-500 to-green-500 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium">
            🏆 Partner with Google Cloud
          </div>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          <span className="block">Vicino AI</span>
          <span className="text-3xl md:text-4xl font-light opacity-90">Multi-Agent 3D Generation</span>
        </h1>
        
        <p className="text-xl md:text-2xl opacity-90 max-w-4xl mx-auto mb-8 leading-relaxed">
          Transform text and image prompts into high-fidelity, stylized 3D assets with our 
          revolutionary multi-agent platform. Production-ready assets for gaming, AR/VR, 
          product design, and creative workflows.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
          <button 
            onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
            className="bg-white text-purple-600 px-8 py-4 rounded-full font-semibold text-lg hover:bg-gray-100 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
          >
            Try Demo Now
          </button>
          <button 
            onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
            className="border-2 border-white text-white px-8 py-4 rounded-full font-semibold text-lg hover:bg-white hover:text-purple-600 transition-all duration-300"
          >
            Learn More
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
            <div className="text-3xl mb-2">🎯</div>
            <h3 className="font-semibold mb-2">Production-Ready</h3>
            <p className="text-sm opacity-80">Export-ready assets with precise stylistic control</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
            <div className="text-3xl mb-2">🤖</div>
            <h3 className="font-semibold mb-2">Multi-Agent AI</h3>
            <p className="text-sm opacity-80">Intelligent collaboration for superior results</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
            <div className="text-3xl mb-2">⚡</div>
            <h3 className="font-semibold mb-2">Real-time Control</h3>
            <p className="text-sm opacity-80">Interactive refinement and customization</p>
          </div>
        </div>
      </div>
    </div>
  );
};
