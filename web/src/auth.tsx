import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useState,
} from 'react';
import { Navigate, useLocation } from 'react-router';

import { fitFlowApi, type UserAccount } from './api/client';

type AuthContextValue = {
  user: UserAccount | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName: string,
  ) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserAccount | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    void fitFlowApi
      .getCurrentUser()
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    const clearUser = () => setUser(null);
    window.addEventListener('fitflow:unauthorized', clearUser);
    return () => {
      active = false;
      window.removeEventListener('fitflow:unauthorized', clearUser);
    };
  }, []);

  const value: AuthContextValue = {
    user,
    loading,
    login: async (email, password) => {
      const response = await fitFlowApi.login(email, password);
      setUser(response.user);
    },
    register: async (email, password, displayName) => {
      const response = await fitFlowApi.register(email, password, displayName);
      setUser(response.user);
    },
    logout: async () => {
      try {
        await fitFlowApi.logout();
      } finally {
        setUser(null);
      }
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth 必须在 AuthProvider 内使用。');
  }
  return context;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="auth-loading">正在恢复登录状态…</div>;
  }
  if (user === null) {
    return <Navigate replace state={{ from: location.pathname }} to="/" />;
  }
  return children;
}
