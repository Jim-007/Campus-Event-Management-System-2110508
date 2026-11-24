import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  role: 'user' | 'admin';
  created_at?: string;
}

interface AuthContextType {
  user: UserProfile | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, fullName: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: (updated: UserProfile) => void;
  apiFetch: (url: string, options?: RequestInit) => Promise<Response>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const attemptRefresh = useCallback(async (): Promise<string | null> => {
    try {
      const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) {
        setUser(null);
        setAccessToken(null);
        return null;
      }
      const data = await res.json();
      setAccessToken(data.access_token);
      setUser(data.user);
      return data.access_token;
    } catch {
      setUser(null);
      setAccessToken(null);
      return null;
    }
  }, []);

  useEffect(() => {
    attemptRefresh().finally(() => setLoading(false));
  }, [attemptRefresh]);

  const apiFetch = useCallback(
    async (url: string, options: RequestInit = {}): Promise<Response> => {
      const headers = new Headers(options.headers || {});
      if (accessToken) {
        headers.set('Authorization', `Bearer ${accessToken}`);
      }
      if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
      }

      let res = await fetch(url, { ...options, headers, credentials: 'include' });

      // Automatically refresh once if access token expired (401)
      if (res.status === 401) {
        const newToken = await attemptRefresh();
        if (newToken) {
          headers.set('Authorization', `Bearer ${newToken}`);
          res = await fetch(url, { ...options, headers, credentials: 'include' });
        }
      }
      return res;
    },
    [accessToken, attemptRefresh]
  );

  const login = async (email: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    setAccessToken(data.access_token);
    setUser(data.user);
  };

  const signup = async (email: string, fullName: string, password: string) => {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, full_name: fullName, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Signup failed');
    setAccessToken(data.access_token);
    setUser(data.user);
  };

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    setAccessToken(null);
    setUser(null);
  };

  const refreshUser = (updated: UserProfile) => setUser(updated);

  return (
    <AuthContext.Provider value={{ user, accessToken, loading, login, signup, logout, refreshUser, apiFetch }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};