import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AuthService, { User, LoginCredentials, ChangePasswordData } from '../services/AuthService';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (passwordData: ChangePasswordData) => Promise<void>;
  setOfficeType: (employeeCode: string, officeType: string) => Promise<void>;
  checkAuthStatus: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  isAdmin: () => boolean;
  isFirstLogin: () => boolean;
  mustChangePassword: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const authService = AuthService.getInstance();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      setIsLoading(true);
      
      // Try to get user from storage first
      const storedUser = await authService.getUser();
      
      if (storedUser) {
        // Verify with server
        try {
          const currentUser = await authService.getCurrentUser();
          
          if (currentUser) {
            setUser(currentUser);
            setIsAuthenticated(true);
          } else {
            throw new Error('Token invalid');
          }
        } catch (error) {
          // Token invalid, clear storage
          await authService.logout();
          setUser(null);
          setIsAuthenticated(false);
        }
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Auth status check error:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials) => {
    try {
      setIsLoading(true);
      
      const authResponse = await authService.login(credentials);
      
      setUser(authResponse.user);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Login error:', error);
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      
      await authService.logout();
      
      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const changePassword = async (passwordData: ChangePasswordData) => {
    try {
      await authService.changePassword(passwordData);
      
      // Update user state to reflect password change
      if (user) {
        const updatedUser = {
          ...user,
          mustChangePassword: false,
          isFirstLogin: false,
        };
        setUser(updatedUser);
      }
    } catch (error) {
      console.error('Change password error:', error);
      throw error;
    }
  };

  const setOfficeType = async (employeeCode: string, officeType: string) => {
    try {
      await authService.setOfficeType(employeeCode, officeType);
      
      // Update user state to reflect office type
      if (user) {
        const updatedUser = {
          ...user,
          officeType,
        };
        setUser(updatedUser);
      }
    } catch (error) {
      console.error('Set office type error:', error);
      throw error;
    }
  };

  const hasPermission = (permission: string): boolean => {
    return user?.permissions.includes(permission) || false;
  };

  const isAdmin = (): boolean => {
    return user?.role === 'admin';
  };

  const isFirstLogin = (): boolean => {
    return user?.isFirstLogin || false;
  };

  const mustChangePassword = (): boolean => {
    return user?.mustChangePassword || false;
  };

  const contextValue: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    changePassword,
    setOfficeType,
    checkAuthStatus,
    hasPermission,
    isAdmin,
    isFirstLogin,
    mustChangePassword,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;