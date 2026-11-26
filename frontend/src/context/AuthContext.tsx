import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, UserRole } from '../api/types';
import { authService } from '../api/services';

interface AuthContextType {
  user: User | null;
  role: UserRole;
  selectedRole: UserRole;
  setSelectedRole: (role: UserRole) => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  socialLogin: (provider: 'google' | 'microsoft', targetRole?: UserRole, email?: string, fullName?: string) => Promise<void>;
  logout: () => void;
  setUser: React.Dispatch<React.SetStateAction<User | null>>;
  setRole: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [role, setRoleState] = useState<UserRole>('patient');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize auth state from localStorage on load
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user_info');
      const savedRole = (localStorage.getItem('user_role') as UserRole) || 'patient';

      if (savedRole) {
        setRoleState(savedRole);
      }

      if (token) {
        if (savedUser) {
          try {
            setUser(JSON.parse(savedUser));
          } catch {
            // parse error
          }
        }
        try {
          const freshUser = await authService.getMe();
          setUser(freshUser);
          setRoleState(freshUser.role);
          localStorage.setItem('user_info', JSON.stringify(freshUser));
          localStorage.setItem('user_role', freshUser.role);
        } catch {
          // Token might be invalid or network offline
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await authService.login({ email, password });
    localStorage.setItem('access_token', res.access_token);
    localStorage.setItem('refresh_token', res.refresh_token);
    localStorage.setItem('user_role', res.role);

    const userInfo: User = {
      id: res.user_id,
      email: res.email,
      full_name: res.full_name,
      role: res.role,
      preferred_language: 'en',
      is_active: true,
      created_at: new Date().toISOString(),
    };

    setUser(userInfo);
    setRoleState(res.role);
    localStorage.setItem('user_info', JSON.stringify(userInfo));
  };

  const socialLogin = async (
    provider: 'google' | 'microsoft',
    targetRole?: UserRole,
    customEmail?: string,
    customFullName?: string
  ) => {
    const chosenRole = targetRole || role;
    const res = await authService.socialLogin({
      provider,
      role: chosenRole,
      email: customEmail,
      full_name: customFullName,
    });
    localStorage.setItem('access_token', res.access_token);
    localStorage.setItem('refresh_token', res.refresh_token);
    localStorage.setItem('user_role', res.role);

    const userInfo: User = {
      id: res.user_id,
      email: res.email,
      full_name: res.full_name,
      role: res.role,
      preferred_language: 'en',
      is_active: true,
      created_at: new Date().toISOString(),
    };

    setUser(userInfo);
    setRoleState(res.role);
    localStorage.setItem('user_info', JSON.stringify(userInfo));
  };

  const logout = () => {
    authService.logout().catch(() => {});
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('user_role');
    setUser(null);
    setRoleState('patient');
  };

  const setRole = (newRole: UserRole) => {
    setRoleState(newRole);
    localStorage.setItem('user_role', newRole);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        selectedRole: role,
        setSelectedRole: setRole,
        isAuthenticated: !!user || !!localStorage.getItem('access_token'),
        isLoading,
        login,
        socialLogin,
        logout,
        setUser,
        setRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
