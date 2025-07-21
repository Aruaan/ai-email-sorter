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
  // Get stored active account from localStorage, fallback to initialActiveAccount
  const storedAccount = localStorage.getItem('activeAccount');
  const [activeAccount, setActiveAccountState] = useState(storedAccount || initialActiveAccount);

  const setActiveAccount = (email: string) => {
    setActiveAccountState(email);
    localStorage.setItem('activeAccount', email);
  };

  // Update active account when initialActiveAccount changes (e.g., fresh login)
  React.useEffect(() => {
    if (initialActiveAccount && initialActiveAccount !== activeAccount) {
      setActiveAccount(initialActiveAccount);
    }
  }, [initialActiveAccount]);

  return (
    <AccountContext.Provider value={{ activeAccount, setActiveAccount }}>
      {children}
    </AccountContext.Provider>
  );
}; 