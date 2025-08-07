import React from 'react';

export const Features: React.FC = () => {
  const features = [
    {
      icon: "🔄",
      title: "Stepwise Reconstruction",
      description: "A two-step process (text-to-multiview image generation, image-to-3D reconstruction) enabling reliable and stable generation. The innovative use of multi-view images provides strong, classifier-free guidance, significantly enhancing the precision of 3D reconstruction.",
      benefits: ["Reliable generation", "Stable outputs", "Enhanced precision", "Classifier-free guidance"]
    },
    {
      icon: "🤖",
      title: "Agentic Architecture",
      description: "Automatic iterative collaboration among agents to refine outputs at each step, ensuring reliability and accuracy of AI-driven 3D reconstruction. The scalability of a multi-agent system allows agents to be added or removed easily, making it adaptable across diverse vertical applications.",
      benefits: ["Automatic refinement", "Scalable system", "Cross-vertical adaptability", "Reliable accuracy"]
    },
    {
      icon: "👥",
      title: "Human-in-the-Loop Control",
      description: "An interactive multi-agent system enabling detailed customization through human-AI collaboration. Unlike one-click solutions, our conversational workflow allows users to iteratively refine requirements with precision and receive immediate feedback from multiple agents.",
      benefits: ["Interactive customization", "Conversational workflow", "Immediate feedback", "Precision control"]
    }
  ];

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Three Revolutionary Innovations
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Vicino AI's architecture introduces breakthrough innovations that set us apart from 
            traditional one-click 3D generation tools.
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
      </div>
    </section>
  );
};
