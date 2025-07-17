'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useTenant } from '@/contexts/TenantProvider';
import { useAuth } from '@/contexts/AuthProvider';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

interface TenantGuardProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * A component that ensures the user has access to the current tenant
 * Redirects to login if not authenticated or shows an error if tenant is invalid
 */
export function TenantGuard({ children, fallback }: TenantGuardProps) {
  const { tenant, tenantId, isLoading: isTenantLoading } = useTenant();
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [isValidating, setIsValidating] = useState(true);
  const [isValid, setIsValid] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const validateTenant = async () => {
      // If still loading tenant or auth info, wait
      if (isTenantLoading || isAuthLoading) {
        return;
      }

      // If not authenticated, redirect to login
      if (!isAuthenticated) {
        router.push('/login');
        return;
      }

      // If no tenant ID, show error
      if (!tenantId) {
        setIsValid(false);
        setIsValidating(false);
        return;
      }

      // If tenant is loaded and active, allow access
      if (tenant && tenant.is_active) {
        setIsValid(true);
        setIsValidating(false);
        return;
      }

      // Otherwise, tenant is invalid
      setIsValid(false);
      setIsValidating(false);
    };

    validateTenant();
  }, [tenant, tenantId, isAuthenticated, isTenantLoading, isAuthLoading, router]);

  // Show loading state
  if (isValidating || isTenantLoading || isAuthLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md p-6 rounded-3xl border-0 shadow-lg">
          <CardContent className="flex flex-col items-center justify-center p-6">
            <Loader2 className="h-12 w-12 text-cyan-500 animate-spin mb-4" />
            <p className="text-lg text-center text-gray-700 dark:text-gray-300">
              Verificando acesso ao tenant...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show error state if tenant is invalid
  if (!isValid) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md p-6 rounded-3xl border-0 shadow-lg">
          <CardContent className="flex flex-col items-center justify-center p-6">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-8 w-8 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Acesso Negado</h3>
            <p className="text-center text-gray-600 dark:text-gray-400 mb-4">
              Você não tem acesso a este tenant ou o tenant não existe.
            </p>
            <button
              onClick={() => router.push('/login')}
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-orange-500 text-white rounded-xl hover:from-cyan-600 hover:to-orange-600 transition-colors"
            >
              Voltar para o Login
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render children if tenant is valid
  return <>{children}</>;
}