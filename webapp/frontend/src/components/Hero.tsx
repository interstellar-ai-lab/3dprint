import React, { useState } from 'react';

export const Hero: React.FC = () => {
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://vicino.ai';
  const [isWaitlistModalOpen, setIsWaitlistModalOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleWaitlistSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/waitlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setSubmitStatus('success');
        setTimeout(() => {
          setIsWaitlistModalOpen(false);
          setEmail('');
          setSubmitStatus('idle');
        }, 2000);
      } else {
        console.error('Waitlist submission error:', data.error);
        setSubmitStatus('error');
      }
    } catch (error) {
      console.error('Waitlist submission error:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
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
            <button 
              onClick={() => setIsWaitlistModalOpen(true)}
              className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-8 py-4 rounded-full font-semibold text-lg hover:from-green-600 hover:to-emerald-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
            >
              Join Waitlist
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

      {/* Waitlist Modal */}
      {isWaitlistModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="text-center">
              <div className="text-4xl mb-4">🚀</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Join the Waitlist</h3>
              <p className="text-gray-600 mb-6">
                Be among the first to experience the future of 3D generation. We'll notify you when we launch!
              </p>
              
              {submitStatus === 'success' ? (
                <div className="text-green-600 font-semibold">
                  🎉 Thanks for joining! We'll be in touch soon.
                </div>
              ) : submitStatus === 'error' ? (
                <div className="text-red-600 font-semibold">
                  Something went wrong. Please try again.
                </div>
              ) : (
                <form onSubmit={handleWaitlistSubmit} className="space-y-4">
                  <div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email address"
                      required
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="flex gap-3">
                    <button
                      type="submit"
                      disabled={isSubmitting || !email}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isSubmitting ? 'Joining...' : 'Join Waitlist'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsWaitlistModalOpen(false)}
                      className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-300"
                      disabled={isSubmitting}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
