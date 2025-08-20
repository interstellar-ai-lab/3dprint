import React, { createContext, useContext, useState, useEffect } from 'react';

interface AccessCodeContextType {
  hasAccess: boolean;
  setAccessCode: (code: string) => boolean;
  clearAccess: () => void;
}

const AccessCodeContext = createContext<AccessCodeContextType | undefined>(undefined);

export const useAccessCode = () => {
  const context = useContext(AccessCodeContext);
  if (!context) {
    throw new Error('useAccessCode must be used within an AccessCodeProvider');
  }
  return context;
};

export const AccessCodeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [hasAccess, setHasAccess] = useState(false);

  // Check for existing access on mount
  useEffect(() => {
    const storedAccess = localStorage.getItem('vicino_access');
    if (storedAccess === 'true') {
      setHasAccess(true);
    }
  }, []);

  const setAccessCode = (code: string): boolean => {
    if (code.toLowerCase() === 'tryvicinoai') {
      setHasAccess(true);
      localStorage.setItem('vicino_access', 'true');
      return true;
    }
    return false;
  };

  const clearAccess = () => {
    setHasAccess(false);
    localStorage.removeItem('vicino_access');
  };

  const value: AccessCodeContextType = {
    hasAccess,
    setAccessCode,
    clearAccess,
  };

  return (
    <AccessCodeContext.Provider value={value}>
      {children}
    </AccessCodeContext.Provider>
  );
};
