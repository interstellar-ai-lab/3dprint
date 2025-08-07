import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Navigation } from './components/Navigation';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { MarketSection } from './components/MarketSection';
import { TeamSection } from './components/TeamSection';
import { DemoSection } from './components/DemoSection';
import { Footer } from './components/Footer';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen">
        {/* Navigation */}
        <Navigation />
        
        {/* Hero Section */}
        <Hero />
        
        {/* Features Section */}
        <section id="features">
          <Features />
        </section>
        
        {/* Demo Section */}
        <section id="demo">
          <DemoSection />
        </section>
        
        {/* Market Section */}
        <section id="market">
          <MarketSection />
        </section>
        

        
        {/* Team Section */}
        <section id="team">
          <TeamSection />
        </section>
        
        {/* Footer */}
        <Footer />
      </div>
    </QueryClientProvider>
  );
}

export default App;
