'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useTenant } from '@/contexts/TenantProvider';
import { useAuth } from '@/contexts/AuthProvider';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, AlertTriangle, ShieldAlert } from 'lucide-react';
import { authService } from '@/services/api';
import { toast } from '@/components/ui/use-toast';
import { useTenantValidation } from '@/hooks/useTenantValidation';
import { Button } from '@/components/ui/button';

interface TenantGuardProps {
  children: ReactNode;
  fallback?: ReactNode;
  requiredPermissions?: string[];
  validateWithBackend?: boolean;
}

/**
 * A component that ensures the user has access to the current tenant
 * Redirects to login if not authenticated or shows an error if tenant is invalid
 * Uses the useTenantValidation hook for consistent tenant validation
 */
export function TenantGuard({ 
  children, 
  fallback, 
  requiredPermissions = [],
  validateWithBackend = true
}: TenantGuardProps) {
  const router = useRouter();
  const { tenant, tenantId, isLoading: isTenantLoading } = useTenant();
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  
  // Use the tenant validation hook for consistent validation
  const {
    isValidating,
    isValid,
    hasPermissions,
    error,
    validateDataOwnership
  } = useTenantValidation({
    validateWithBackend,
    requiredPermissions
  });

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isAuthLoading, router]);

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

  // Show permission error if user doesn't have required permissions
  if (isValid && !hasPermissions) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md p-6 rounded-3xl border-0 shadow-lg">
          <CardContent className="flex flex-col items-center justify-center p-6">
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mb-4">
              <ShieldAlert className="h-8 w-8 text-yellow-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Permissão Insuficiente</h3>
            <p className="text-center text-gray-600 dark:text-gray-400 mb-4">
              Você não tem todas as permissões necessárias para acessar esta página.
            </p>
            <Button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-orange-500 text-white rounded-xl hover:from-cyan-600 hover:to-orange-600 transition-colors"
            >
              Voltar para o Dashboard
            </Button>
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
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Acesso Negado</h3>
            <p className="text-center text-gray-600 dark:text-gray-400 mb-4">
              {error || 'Você não tem acesso a este tenant ou o tenant não existe.'}
            </p>
            <Button
              onClick={() => router.push('/login')}
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-orange-500 text-white rounded-xl hover:from-cyan-600 hover:to-orange-600 transition-colors"
            >
              Voltar para o Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Create a tenant context provider for the children
  // This ensures all children have access to tenant validation functions
  return (
    <>
      {children}
    </>
  );
}