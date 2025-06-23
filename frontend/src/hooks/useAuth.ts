import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api, Usuario } from '@/lib/api';

export function useAuth() {
  const [user, setUser] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Carrega o usuário atual ao montar o hook
  useEffect(() => {
    const loadUser = async () => {
      try {
        const token = localStorage.getItem('authToken');
        if (token) {
          const userData = await api.getCurrentUser();
          setUser(userData);
        }
      } catch (error) {
        console.error('Erro ao carregar usuário:', error);
        localStorage.removeItem('authToken');
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  // Função de login
  const login = useCallback(
    async (username: string, password: string) => {
      try {
        const { user: userData, access_token } = await api.login({ username, password });
        localStorage.setItem('authToken', access_token);
        setUser(userData);
        return userData;
      } catch (error) {
        console.error('Erro no login:', error);
        throw error;
      }
    },
    []
  );

  // Função de logout
  const logout = useCallback(() => {
    localStorage.removeItem('authToken');
    setUser(null);
    router.push('/login');
  }, [router]);

  // Verifica se o usuário está autenticado
  const isAuthenticated = !!user;

  // Verifica se o usuário é administrador
  const isAdmin = user?.is_admin || false;

  return {
    user,
    loading,
    login,
    logout,
    isAuthenticated,
    isAdmin,
  };
}
