import React, { useState, useEffect } from 'react';

export const Navigation: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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
          <div className="hidden md:flex items-center space-x-8">
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
              onClick={() => scrollToSection('team')}
              className={`font-medium transition-colors ${
                isScrolled ? 'text-gray-700 hover:text-purple-600' : 'text-white/90 hover:text-white'
              }`}
            >
              Team
            </button>
            <button 
              onClick={() => window.open('http://localhost:8000/studio', '_blank')}
              className={`font-medium transition-colors ${
                isScrolled ? 'text-gray-700 hover:text-purple-600' : 'text-white/90 hover:text-white'
              }`}
            >
              Studio
            </button>
            <button className={`px-4 py-2 rounded-full font-medium transition-all ${
              isScrolled 
                ? 'bg-purple-600 text-white hover:bg-purple-700' 
                : 'bg-white text-purple-600 hover:bg-gray-100'
            }`}>
              Contact
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
                onClick={() => scrollToSection('team')}
                className="text-gray-700 hover:text-purple-600 font-medium text-left"
              >
                Team
              </button>
              <button 
                onClick={() => window.open('http://localhost:8000/studio', '_blank')}
                className="text-gray-700 hover:text-purple-600 font-medium text-left"
              >
                Studio
              </button>
              <button className="bg-purple-600 text-white px-4 py-2 rounded-full font-medium hover:bg-purple-700">
                Contact
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};
