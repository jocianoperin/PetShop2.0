'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthProvider';
import { useUsers } from '@/hooks/useUsers';

export default function UserListPage() {
  const { user } = useAuth();
  const { users, isLoading, error, deleteUser } = useUsers();
  const router = useRouter();

  const handleDelete = async (userId: number) => {
    if (!confirm('Tem certeza que deseja excluir este usuário?')) {
      return;
    }

    try {
      await deleteUser(userId);
    } catch (err) {
      console.error('Erro ao excluir usuário:', err);
      // O erro já é tratado no hook
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  // Se não for admin, não mostra nada (já foi redirecionado)
  if (!user?.is_staff) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Gerenciar Usuários</h1>
        <Link
          href="/register"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Adicionar Usuário
        </Link>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {users.map((userItem) => (
            <li key={userItem.id}>
              <div className="px-4 py-4 sm:px-6 flex items-center justify-between">
                <div className="flex items-center">
                  <div className="min-w-0 flex-1 flex items-center">
                    <div className="min-w-0 flex-1 px-4 md:grid md:grid-cols-2 md:gap-4">
                      <div>
                        <p className="text-sm font-medium text-indigo-600 truncate">
                          {userItem.username}
                        </p>
                        <p className="mt-2 flex items-center text-sm text-gray-500">
                          <span className="truncate">{userItem.email}</span>
                        </p>
                      </div>
                      <div className="hidden md:block">
                        <div>
                          <p className="text-sm text-gray-900">
                            {userItem.is_staff ? 'Administrador' : 'Usuário'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="ml-4 flex-shrink-0">
                  <button
                    onClick={() => handleDelete(userItem.id)}
                    disabled={userItem.id === user.id}
                    className={`font-medium text-red-600 hover:text-red-500 ${userItem.id === user.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                    title={userItem.id === user.id ? 'Você não pode excluir seu próprio usuário' : 'Excluir usuário'}
                  >
                    Excluir
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
