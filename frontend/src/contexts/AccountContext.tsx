import React, { createContext, useContext, useState, ReactNode } from 'react';

interface AccountContextType {
  activeAccount: string;
  setActiveAccount: (email: string) => void;
}

const AccountContext = createContext<AccountContextType | undefined>(undefined);

export const useAccount = () => {
  const context = useContext(AccountContext);
  if (context === undefined) {
    throw new Error('useAccount must be used within an AccountProvider');
  }
  return context;
};

interface AccountProviderProps {
  children: ReactNode;
  initialActiveAccount: string;
}

export const AccountProvider: React.FC<AccountProviderProps> = ({ 
  children, 
  initialActiveAccount 
}) => {
  const [activeAccount, setActiveAccount] = useState(initialActiveAccount);

  return (
    <AccountContext.Provider value={{ activeAccount, setActiveAccount }}>
      {children}
    </AccountContext.Provider>
  );
}; 