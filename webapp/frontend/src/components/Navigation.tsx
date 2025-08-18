import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { AuthModal } from './AuthModal';
import { Wallet } from './Wallet';

export const Navigation: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'signin' | 'signup'>('signin');
  const [walletOpen, setWalletOpen] = useState(false);
  const { user, signOut, loading } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
    setIsMobileMenuOpen(false);
  };

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Sign out failed:', error);
    }
  };

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled 
        ? 'bg-white/95 backdrop-blur-md shadow-lg' 
        : 'bg-transparent'
    }`}>
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className={`text-2xl font-bold ${
              isScrolled ? 'text-purple-600' : 'text-white'
            }`}>
              Vicino AI
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <button 
              onClick={() => scrollToSection('features')}
              className={`font-medium transition-colors ${
                isScrolled ? 'text-gray-700 hover:text-purple-600' : 'text-white/90 hover:text-white'
              }`}
            >
              Features
            </button>
            <button 
              onClick={() => scrollToSection('demo')}
              className={`font-medium transition-colors ${
                isScrolled ? 'text-gray-700 hover:text-purple-600' : 'text-white/90 hover:text-white'
              }`}
            >
              Demo
            </button>
            <button 
              onClick={() => scrollToSection('market')}
              className={`font-medium transition-colors ${
                isScrolled ? 'text-gray-700 hover:text-purple-600' : 'text-white/90 hover:text-white'
              }`}
            >
              Market
            </button>
            <button 
              onClick={() => {
                const baseUrl = process.env.REACT_APP_BASE_URL || window.location.origin;
                window.open(`${baseUrl}/studio`, '_blank');
              }}
              className={`font-medium transition-colors ${
                isScrolled ? 'text-gray-700 hover:text-purple-600' : 'text-white/90 hover:text-white'
              }`}
            >
              Studio
            </button>
            
            {/* Auth Section */}
            <div className="flex items-center space-x-3">
              {loading ? (
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
              ) : user ? (
                <div className="flex items-center space-x-3">
                  {/* Wallet Button */}
                  <button
                    onClick={() => setWalletOpen(true)}
                    className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                      isScrolled 
                        ? 'bg-purple-600 text-white hover:bg-purple-700' 
                        : 'bg-white/20 text-white hover:bg-white/30'
                    }`}
                  >
                    <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                    Wallet
                  </button>
                  
                  <span className={`text-sm ${
                    isScrolled ? 'text-gray-700' : 'text-white/90'
                  }`}>
                    {user.email}
                  </span>
                  <button
                    onClick={handleSignOut}
                    className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                      isScrolled 
                        ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' 
                        : 'bg-white/20 text-white hover:bg-white/30'
                    }`}
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      setAuthModalMode('signin');
                      setAuthModalOpen(true);
                    }}
                    className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                      isScrolled 
                        ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' 
                        : 'bg-white/20 text-white hover:bg-white/30'
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => {
                      setAuthModalMode('signup');
                      setAuthModalOpen(true);
                    }}
                    className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                      isScrolled 
                        ? 'bg-purple-600 text-white hover:bg-purple-700' 
                        : 'bg-purple-600 text-white hover:bg-purple-700'
                    }`}
                  >
                    Sign Up
                  </button>
                </div>
              )}
            </div>

            <button 
              onClick={() => window.open('https://calendar.app.google/mh5rhYuC3D2fec4x9', '_blank')}
              className={`px-4 py-2 rounded-full font-medium transition-all ${
                isScrolled 
                  ? 'bg-purple-600 text-white hover:bg-purple-700' 
                  : 'bg-white text-purple-600 hover:bg-gray-100'
              }`}>
              Schedule Demo
            </button>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className={`p-2 rounded-md ${
                isScrolled ? 'text-gray-700' : 'text-white'
              }`}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden bg-white/95 backdrop-blur-md rounded-lg mt-2 p-4 shadow-lg">
            <div className="flex flex-col space-y-4">
              <button 
                onClick={() => scrollToSection('features')}
                className="text-gray-700 hover:text-purple-600 font-medium text-left"
              >
                Features
              </button>
              <button 
                onClick={() => scrollToSection('demo')}
                className="text-gray-700 hover:text-purple-600 font-medium text-left"
              >
                Demo
              </button>
              <button 
                onClick={() => scrollToSection('market')}
                className="text-gray-700 hover:text-purple-600 font-medium text-left"
              >
                Market
              </button>
              <button 
                onClick={() => {
                  const baseUrl = process.env.REACT_APP_BASE_URL || window.location.origin;
                  window.open(`${baseUrl}/studio`, '_blank');
                }}
                className="text-gray-700 hover:text-purple-600 font-medium text-left"
              >
                Studio
              </button>
              
              {/* Mobile Auth Section */}
              <div className="pt-2 border-t border-gray-200">
                {loading ? (
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
                  </div>
                ) : user ? (
                  <div className="space-y-2">
                    <div className="text-sm text-gray-600">{user.email}</div>
                    <button
                      onClick={handleSignOut}
                      className="w-full bg-gray-200 text-gray-700 px-3 py-2 rounded text-sm font-medium hover:bg-gray-300"
                    >
                      Sign Out
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <button
                      onClick={() => {
                        setAuthModalMode('signin');
                        setAuthModalOpen(true);
                        setIsMobileMenuOpen(false);
                      }}
                      className="w-full bg-gray-200 text-gray-700 px-3 py-2 rounded text-sm font-medium hover:bg-gray-300"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => {
                        setAuthModalMode('signup');
                        setAuthModalOpen(true);
                        setIsMobileMenuOpen(false);
                      }}
                      className="w-full bg-purple-600 text-white px-3 py-2 rounded text-sm font-medium hover:bg-purple-700"
                    >
                      Sign Up
                    </button>
                  </div>
                )}
              </div>

              <button 
                onClick={() => window.open('https://calendar.app.google/mh5rhYuC3D2fec4x9', '_blank')}
                className="bg-purple-600 text-white px-4 py-2 rounded-full font-medium hover:bg-purple-700">
                Schedule Demo
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authModalMode}
      />
      
      {/* Wallet Modal */}
      <Wallet
        isOpen={walletOpen}
        onClose={() => setWalletOpen(false)}
      />
    </nav>
  );
};
