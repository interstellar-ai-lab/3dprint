import React from 'react';

export const TeamSection: React.FC = () => {
  const teamMembers: Array<{
    name: string;
    role: string;
    bio: string;
    education: string;
    linkedin: string;
    avatar: string;
    website?: string;
  }> = [
    {
      name: "Victoria Yang",
      role: "CEO and Co-founder",
      bio: "Victoria brings cross-disciplinary expertise in AI strategy, product design, and business development. She previously led a successful investor roadshow for a Hong Kong-based AI startup that closed a $10 million seed round. Prior to that, she managed over $20 million in art market transactions across galleries and auction houses.",
      education: "Master's in Technology Innovation (Computer Science) from the University of Washington, and a Bachelor's in Art History from the University of Toronto.",
      linkedin: "https://www.linkedin.com/in/jining-yang/",
      avatar: "👩‍💼"
    },
    {
      name: "Dr. Peter Lin",
      role: "CTO and Co-founder",
      bio: "Peter worked as an Applied Scientist at a leading big tech company, where he led projects such as AgenticRAG and GraphRAG in multi-agent LLM systems. He is also the chief architect of Vicino’s entire technical stack, including its core multi-agent generation engine.",
      education: "PhD in Computer Engineering from the University of British Columbia and was a research faculty member at NYU, contributing to DARPA projects in computer vision and multi-modal AI.",
      linkedin: "https://www.linkedin.com/in/jianzhe-peter-lin-a4135baa/",
      avatar: "👨‍💻"
    },
    {
      name: "Jackson Pan",
      role: "Founding Engineer and Co-founder",
      bio: "Jackson is a senior machine learning engineer at AWS AI with deep experience in large-scale ML infrastructure. When he was at Meta, he built Meta Business Suite from 0 to over 30 million monthly active users and over $100 million in ad revenue. ",
      education: "Master in University of Illinois at Urbana-Champaign, Bachelor in Computer Science from Purdue University",
      linkedin: "https://www.linkedin.com/in/zeyupan1995/",
      avatar: "👨‍🔧"
    }
  ];

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Founding Team
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experienced leaders with deep expertise in AI, product development, and 
            scaling technology companies.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {teamMembers.map((member, index) => (
            <div key={index} className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2">
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">{member.avatar}</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{member.name}</h3>
                <p className="text-purple-600 font-semibold mb-4">{member.role}</p>
              </div>
              
              <div className="space-y-4">
                <p className="text-gray-600 leading-relaxed">
                  {member.bio}
                </p>
                
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">Education & Background</h4>
                  <p className="text-sm text-gray-600">{member.education}</p>
                </div>
                
                <div className="flex justify-center space-x-4">
                  <a 
                    href={member.linkedin} 
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
                  >
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M16.338 16.338H13.67V12.16c0-.995-.017-2.277-1.387-2.277-1.39 0-1.601 1.086-1.601 2.207v4.248H8.014v-8.59h2.559v1.174h.037c.356-.675 1.227-1.387 2.526-1.387 2.703 0 3.203 1.778 3.203 4.092v4.711zM5.005 6.575a1.548 1.548 0 11-.003-3.096 1.548 1.548 0 01.003 3.096zm-1.337 9.763H6.34v-8.59H3.667v8.59zM17.668 1H2.328C1.595 1 1 1.581 1 2.298v15.403C1 18.418 1.595 19 2.328 19h15.34c.734 0 1.332-.582 1.332-1.299V2.298C19 1.581 18.402 1 17.668 1z"/>
                    </svg>
                    LinkedIn
                  </a>
                  {member.website && (
                    <a 
                      href={member.website} 
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200"
                    >
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd"/>
                      </svg>
                      Website
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-2xl p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold mb-4">
              Ready to Build the Future of 3D Generation?
            </h3>
            <p className="text-lg opacity-90 mb-6">
              Join us in revolutionizing how creative professionals create and iterate on 3D assets.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-purple-600 px-6 py-3 rounded-full font-semibold hover:bg-gray-100 transition-all duration-300">
                Contact Us
              </button>
              <button className="border-2 border-white text-white px-6 py-3 rounded-full font-semibold hover:bg-white hover:text-purple-600 transition-all duration-300">
                Join Waitlist
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
