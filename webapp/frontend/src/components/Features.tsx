import React from 'react';

export const Features: React.FC = () => {
  const features = [
    {
      icon: "🎯",
      title: "Production-Ready Quality",
      description: "Unlike basic 3D generation tools that require hours of manual cleanup, our system delivers export-ready assets with precise control over style and structure. Every output meets professional standards for immediate use in your projects.",
      benefits: ["Zero manual cleanup required", "Professional-grade outputs", "Consistent quality", "Ready for production"]
    },
    {
      icon: "🤖",
      title: "Intelligent AI Collaboration",
      description: "Our advanced AI system works like having a team of expert 3D artists at your fingertips. Multiple AI agents collaborate to refine and perfect your assets, ensuring every detail meets your exact specifications.",
      benefits: ["AI-powered refinement", "Expert-level results", "Automatic optimization", "Smart collaboration"]
    },
    {
      icon: "⚡",
      title: "Real-Time Interactive Control",
      description: "Take full control of your creative process with our conversational interface. Refine, adjust, and perfect your 3D assets through natural dialogue, getting instant feedback and making changes on the fly.",
      benefits: ["Natural conversation interface", "Instant feedback", "Real-time adjustments", "Complete creative control"]
    }
  ];

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Why Choose Vicino AI?
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience the future of 3D asset creation with our revolutionary platform that combines 
            cutting-edge AI with intuitive user control.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {features.map((feature, index) => (
            <div key={index} className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2">
              <div className="text-6xl mb-6 text-center">{feature.icon}</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4 text-center">
                {feature.title}
              </h3>
              <p className="text-gray-600 mb-6 leading-relaxed">
                {feature.description}
              </p>
              <div className="space-y-2">
                {feature.benefits.map((benefit, benefitIndex) => (
                  <div key={benefitIndex} className="flex items-center text-sm text-gray-700">
                    <div className="w-2 h-2 bg-purple-500 rounded-full mr-3"></div>
                    {benefit}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-2xl p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold mb-4">
              Built for Creative Professionals
            </h3>
            <p className="text-lg opacity-90">
              Join thousands of designers, developers, and creators who trust Vicino AI to deliver 
              exceptional 3D assets that bring their visions to life.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
