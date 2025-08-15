import React from 'react';

export const MarketSection: React.FC = () => {
  const useCases = [
    {
      icon: "🎮",
      title: "Game Studios",
      description: "AA/AAA asset creation, prop design, stylistic prototyping",
      color: "from-red-500 to-pink-500"
    },
    {
      icon: "🎨",
      title: "Creative Agencies",
      description: "3D assets for immersive campaigns and advertising",
      color: "from-purple-500 to-indigo-500"
    },
    {
      icon: "🏭",
      title: "Product Design Teams",
      description: "Instant early-stage visualization and prototyping",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: "🥽",
      title: "AR/VR Developers",
      description: "Digital twin providers and immersive experiences",
      color: "from-green-500 to-emerald-500"
    }
  ];

  const marketData = [
    {
      label: "Total Addressable Market (TAM)",
      value: "$60B",
      description: "Global 3D digital asset market by 2030",
      color: "text-blue-600"
    },
    {
      label: "Serviceable Available Market (SAM)",
      value: "$15B",
      description: "Focused on AI-generated 3D content",
      color: "text-purple-600"
    },
    {
      label: "Serviceable Obtainable Market (SOM)",
      value: "$300-500M",
      description: "Near term through early adopters",
      color: "text-green-600"
    }
  ];



  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        {/* Market Focus */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Market Focus & Use Cases
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Serving professional creative workflows across multiple industries with 
            production-ready 3D assets.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
          {useCases.map((useCase, index) => (
            <div key={index} className="group">
              <div className={`bg-gradient-to-br ${useCase.color} p-6 rounded-2xl text-white text-center h-full transform transition-all duration-300 group-hover:scale-105 group-hover:shadow-xl`}>
                <div className="text-4xl mb-4">{useCase.icon}</div>
                <h3 className="text-xl font-bold mb-3">{useCase.title}</h3>
                <p className="text-sm opacity-90">{useCase.description}</p>
              </div>
            </div>
          ))}
        </div>


      </div>
    </section>
  );
};
