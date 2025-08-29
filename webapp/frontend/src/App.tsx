import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { AccessCodeProvider, useAccessCode } from './contexts/AccessCodeContext';
import { AuthProvider } from './contexts/AuthContext';
import { GoogleOneTap } from './components/GoogleOneTap';
import { Navigation } from './components/Navigation';
import { Wallet } from './components/Wallet';
import { Hero } from './components/Hero';
// import { Features } from './components/Features';
import { MarketSection } from './components/MarketSection';
// import { TeamSection } from './components/TeamSection';
import { DemoSection } from './components/DemoSection';
import { Studio } from './components/Studio';
import { Footer } from './components/Footer';
import { AuthCallback } from './pages/AuthCallback';
import { ResetPassword } from './pages/ResetPassword';
import './App.css';

const queryClient = new QueryClient();

// Conditional wrapper for auth components
const ConditionalAuthWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // const { hasAccess } = useAccessCode();
  
  // if (!hasAccess) {
  //   return <>{children}</>;
  // }
  
  return (
    <AuthProvider>
      {children}
      <GoogleOneTap />
    </AuthProvider>
  );
};

// Main landing page component
const HomePage: React.FC = () => {
  const [walletOpen, setWalletOpen] = useState(false);
  // const { hasAccess } = useAccessCode();

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <Navigation onWalletOpen={() => setWalletOpen(true)} />
      
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
      
      {/* Wallet Modal */}
      <Wallet
        isOpen={walletOpen}
        onClose={() => setWalletOpen(false)}
      />
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
      <AccessCodeProvider>
        <ConditionalAuthWrapper>
          <Router>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/studio" element={<StudioPage />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route path="/auth/reset-password" element={<ResetPassword />} />
            </Routes>
          </Router>
        </ConditionalAuthWrapper>
      </AccessCodeProvider>
    </QueryClientProvider>
  );
}

export default App;
