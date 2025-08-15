import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Navigation } from './components/Navigation';
import { Hero } from './components/Hero';
// import { Features } from './components/Features';
import { MarketSection } from './components/MarketSection';
// import { TeamSection } from './components/TeamSection';
import { DemoSection } from './components/DemoSection';
import { Studio } from './components/Studio';
import { Footer } from './components/Footer';
import './App.css';

const queryClient = new QueryClient();

// Main landing page component
const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <Navigation />
      
      {/* Hero Section */}
      <Hero />
      
      {/* Features Section */}
      {/* <section id="features">
        <Features />
      </section> */}
      
      {/* Demo Section */}
      <section id="demo">
        <DemoSection />
      </section>
      
      {/* Market Section */}
      <section id="market">
        <MarketSection />
      </section>
      
      {/* Team Section */}
      {/* <section id="team">
        <TeamSection />
      </section> */}
      
      {/* Footer */}
      <Footer />
    </div>
  );
};

// Studio page component (full screen)
const StudioPage: React.FC = () => {
  return (
    <div className="min-h-screen">
      <Studio />
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/studio" element={<StudioPage />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
