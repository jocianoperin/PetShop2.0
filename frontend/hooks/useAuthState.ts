import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/api';
import { User, Tenant } from '@/types';
import { getCurrentTenant, clearCurrentTenant, getTenantHeaders } from '@/lib/tenant';

export function useAuthState() {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const userData = await authService.getCurrentUser(token);
      setUser(userData);
      
      // Set tenant from user data if available
      if (userData.tenant) {
        setTenant(userData.tenant);
      }
    } catch (error) {
      console.error('Erro ao buscar dados do usuário:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setTenant(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (username: string, password: string, tenantId?: string) => {
    try {
      // Use detected tenant if not provided
      const currentTenant = tenantId || getCurrentTenant();
      
      const data = await authService.login({ 
        username, 
        password, 
        tenant_id: currentTenant || undefined 
      });
      
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      setUser(data.user);
      
      // Set tenant from response
      if (data.tenant) {
        setTenant(data.tenant);
      }
      
      return data.user;
    } catch (error) {
      console.error('Erro no login:', error);
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setTenant(null);
    clearCurrentTenant();
    router.push('/login');
  }, [router]);

  const createUser = useCallback(async (userData: { username: string; email: string; password: string }) => {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('Não autenticado');
    
    try {
      const newUser = await authService.createUser(userData, token);
      return newUser;
    } catch (error) {
      console.error('Erro ao criar usuário:', error);
      throw error;
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return {
    user,
    tenant,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    createUser,
  };
}
