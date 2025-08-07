import React from 'react';

export const TractionSection: React.FC = () => {
  const milestones = [
    {
      icon: "🚀",
      title: "Early Prototype",
      description: "Operational with live demos available",
      status: "completed"
    },
    {
      icon: "🌐",
      title: "Public Platform Launch",
      description: "Scheduled for August 2025",
      status: "upcoming"
    },
    {
      icon: "💰",
      title: "Fundraising",
      description: "Currently raising millions in pre-seed capital",
      status: "active"
    }
  ];

  const partnerships = [
    {
      name: "Game Studio",
      type: "$10,000 paid pilot",
      status: "Signed",
      icon: "🎮"
    },
    {
      name: "AR/VR Design Firm",
      type: "Letter of Intent",
      status: "Signed",
      icon: "🥽"
    },
    {
      name: "Creative Advertising Agency",
      type: "Paid pilot",
      status: "Signed",
      icon: "🎨"
    }
  ];

  const fundraisingGoals = [
    {
      category: "Core Engineering Team",
      description: "Frontend, multi-agent AI, GTM infrastructure",
      icon: "👥"
    },
    {
      category: "GPU Compute",
      description: "Scale inference and training capabilities",
      icon: "⚡"
    },
    {
      category: "Commercial Deployments",
      description: "Support onboarding of early design partners",
      icon: "🏢"
    },
    {
      category: "Public Launch",
      description: "Prepare for August 2025 launch",
      icon: "🚀"
    }
  ];

  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Traction & Milestones
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Strong validation from early partnerships and clear roadmap for growth.
          </p>
        </div>

        {/* Milestones */}
        <div className="mb-20">
          <h3 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Key Milestones
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {milestones.map((milestone, index) => (
              <div key={index} className="relative">
                <div className={`bg-white rounded-2xl p-8 shadow-lg border-2 ${
                  milestone.status === 'completed' ? 'border-green-500' :
                  milestone.status === 'active' ? 'border-blue-500' :
                  'border-gray-300'
                }`}>
                  <div className="text-4xl mb-4 text-center">{milestone.icon}</div>
                  <h4 className="text-xl font-bold text-gray-900 mb-3 text-center">
                    {milestone.title}
                  </h4>
                  <p className="text-gray-600 text-center">
                    {milestone.description}
                  </p>
                  <div className={`mt-4 text-center px-3 py-1 rounded-full text-sm font-medium ${
                    milestone.status === 'completed' ? 'bg-green-100 text-green-800' :
                    milestone.status === 'active' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {milestone.status === 'completed' ? '✓ Completed' :
                     milestone.status === 'active' ? '🔄 Active' :
                     '⏳ Upcoming'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Partnerships */}
        <div className="mb-20">
          <h3 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Signed Partnerships & Pilots
          </h3>
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-3xl p-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {partnerships.map((partnership, index) => (
                <div key={index} className="bg-white rounded-xl p-6 shadow-md">
                  <div className="text-3xl mb-4 text-center">{partnership.icon}</div>
                  <h4 className="text-lg font-bold text-gray-900 mb-2 text-center">
                    {partnership.name}
                  </h4>
                  <p className="text-gray-600 text-center mb-3">
                    {partnership.type}
                  </p>
                  <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium text-center">
                    ✓ {partnership.status}
                  </div>
                </div>
              ))}
            </div>
            <div className="text-center mt-8">
              <p className="text-gray-700 font-medium">
                These partnerships validate strong demand for fast, stylized 3D content creation 
                with integrated quality control and user-directed customization.
              </p>
            </div>
          </div>
        </div>

        {/* Fundraising Goals */}
        <div>
          <h3 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Fundraising Goals
          </h3>
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-3xl p-8">
            <div className="text-center mb-8">
              <div className="text-4xl font-bold text-purple-600 mb-2">$2M</div>
              <div className="text-xl text-gray-700">Pre-seed Capital Raise</div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {fundraisingGoals.map((goal, index) => (
                <div key={index} className="bg-white rounded-xl p-6 shadow-md">
                  <div className="text-3xl mb-4 text-center">{goal.icon}</div>
                  <h4 className="text-lg font-bold text-gray-900 mb-2 text-center">
                    {goal.category}
                  </h4>
                  <p className="text-gray-600 text-center text-sm">
                    {goal.description}
                  </p>
                </div>
              ))}
            </div>
            <div className="text-center mt-8">
              <p className="text-gray-700">
                The company is in active conversations with early-stage VCs and angels with 
                backgrounds in AI infrastructure, gaming, design software, and creative tooling.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
