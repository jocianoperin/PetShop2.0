import { useState, useEffect, useCallback } from 'react';
import { User } from '@/types';
import { authService } from '@/services/api';

export function useUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchUsers = useCallback(async () => {
    try {
      setIsLoading(true);
      setError('');
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Não autenticado');
      }
      const usersList = await authService.listUsers(token);
      setUsers(usersList);
    } catch (err) {
      console.error('Erro ao buscar usuários:', err);
      setError('Erro ao carregar lista de usuários');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteUser = useCallback(async (userId: number) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Não autenticado');
      }

      const response = await fetch(`http://127.0.0.1:8000/api/users/${userId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao excluir usuário');
      }

      // Atualizar a lista de usuários após exclusão
      await fetchUsers();
    } catch (err) {
      console.error('Erro ao excluir usuário:', err);
      throw err;
    }
  }, [fetchUsers]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  return {
    users,
    isLoading,
    error,
    refresh: fetchUsers,
    deleteUser,
  };
}
