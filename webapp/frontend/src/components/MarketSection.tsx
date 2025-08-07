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

  const pricingTiers = [
    {
      name: "Studio Subscription",
      price: "$40-100",
      period: "per user/month",
      features: ["Full platform access", "Priority support", "Custom integrations", "Team collaboration"]
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "usage-based",
      features: ["High-volume credits", "API licensing", "Dedicated support", "Custom workflows"]
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

        {/* Market Opportunity */}
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-3xl p-8 mb-20">
          <h3 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Market Opportunity
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {marketData.map((data, index) => (
              <div key={index} className="text-center">
                <div className={`text-4xl font-bold ${data.color} mb-2`}>
                  {data.value}
                </div>
                <div className="text-lg font-semibold text-gray-900 mb-2">
                  {data.label}
                </div>
                <div className="text-gray-600">
                  {data.description}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Business Model */}
        <div className="text-center mb-12">
          <h3 className="text-3xl font-bold text-gray-900 mb-6">
            Business Model
          </h3>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Hybrid SaaS model with subscription pricing and usage-based credit system 
            for high-volume and enterprise accounts.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {pricingTiers.map((tier, index) => (
            <div key={index} className="bg-white border-2 border-gray-200 rounded-2xl p-8 hover:border-purple-500 transition-all duration-300">
              <h4 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h4>
              <div className="mb-6">
                <span className="text-3xl font-bold text-purple-600">{tier.price}</span>
                <span className="text-gray-600 ml-2">{tier.period}</span>
              </div>
              <ul className="space-y-3">
                {tier.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-center text-gray-700">
                    <div className="w-2 h-2 bg-purple-500 rounded-full mr-3"></div>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
