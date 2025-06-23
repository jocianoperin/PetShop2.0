'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthProvider';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Se não estiver carregando e o usuário não for admin, redirecionar
    if (!isLoading && (!user || !user.is_staff)) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

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
    <div className="min-h-screen bg-gray-50">
      <div className="bg-indigo-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-white font-bold">Painel Administrativo</h1>
              </div>
              <nav className="ml-6 flex space-x-8">
                <a
                  href="/admin/usuarios"
                  className="text-indigo-100 hover:bg-indigo-500 hover:bg-opacity-25 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Usuários
                </a>
              </nav>
            </div>
            <div className="hidden md:block">
              <div className="ml-4 flex items-center md:ml-6">
                <a
                  href="/dashboard"
                  className="text-indigo-100 hover:bg-indigo-500 hover:bg-opacity-25 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Voltar para o Painel
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="py-10">
        <main>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
