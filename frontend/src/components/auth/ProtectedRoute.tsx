'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useEffect } from 'react';

export function ProtectedRoute({ children, requireAdmin = false }: { 
  children: React.ReactNode;
  requireAdmin?: boolean;
}) {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        // Usuário não autenticado, redireciona para login
        router.push('/login');
      } else if (requireAdmin && !isAdmin) {
        // Usuário autenticado, mas não é admin e a rota requer admin
        router.push('/unauthorized');
      }
    }
  }, [isAuthenticated, isAdmin, loading, requireAdmin, router]);

  if (loading || !isAuthenticated || (requireAdmin && !isAdmin)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return <>{children}</>;
}
