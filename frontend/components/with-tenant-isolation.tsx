'use client';

import { ComponentType, useEffect, useState } from 'react';
import { useTenantValidation } from '@/hooks/useTenantValidation';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { useTenant } from '@/contexts/TenantProvider';
import { toast } from '@/components/ui/use-toast';

interface WithTenantIsolationProps {
  requiredPermissions?: string[];
  validateWithBackend?: boolean;
  strictValidation?: boolean; // Whether to strictly validate all data against tenant
}

/**
 * Higher-order component that adds tenant isolation to any component
 * Ensures the component only renders if the tenant is valid and the user has required permissions
 * Also provides tenant validation for data
 */
export function withTenantIsolation<P extends object>(
  Component: ComponentType<P>,
  options: WithTenantIsolationProps = {}
) {
  const { requiredPermissions = [], validateWithBackend = false, strictValidation = true } = options;

  return function TenantIsolatedComponent(props: P) {
    const router = useRouter();
    const { tenant, tenantId } = useTenant();
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

    // Function to validate and sanitize data for the component
    const validateTenantData = <T extends { tenant_id?: string }>(data: T | T[] | null | undefined): T | T[] | null | undefined => {
      if (!data || !tenantId) return null;
      
      try {
        // Validate that data belongs to current tenant
        if (!validateDataOwnership(data)) {
          if (strictValidation) {
            toast({
              title: "Erro de validação",
              description: "Os dados não pertencem ao tenant atual.",
              variant: "destructive"
            });
            return null;
          } else {
            console.warn("Data ownership validation failed, but continuing due to non-strict mode");
          }
        }
        
        // Return the validated data
        return data;
      } catch (error) {
        console.error("Error validating tenant data:", error);
        toast({
          title: "Erro de validação",
          description: "Ocorreu um erro ao validar os dados do tenant.",
          variant: "destructive"
        });
        return null;
      }
    };

    // Show loading state
    if (isValidating) {
      return (
        <div className="flex items-center justify-center min-h-[200px]">
          <Card className="w-full max-w-md p-6 rounded-3xl border-0 shadow-lg">
            <CardContent className="flex flex-col items-center justify-center p-6">
              <Loader2 className="h-8 w-8 text-cyan-500 animate-spin mb-4" />
              <p className="text-base text-center text-gray-700 dark:text-gray-300">
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
        <div className="flex items-center justify-center min-h-[200px]">
          <Card className="w-full max-w-md p-6 rounded-3xl border-0 shadow-lg">
            <CardContent className="flex flex-col items-center justify-center p-6">
              <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mb-4">
                <ShieldAlert className="h-6 w-6 text-yellow-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Permissão Insuficiente</h3>
              <p className="text-center text-gray-600 dark:text-gray-400 mb-4">
                Você não tem todas as permissões necessárias para acessar este conteúdo.
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
      return (
        <div className="flex items-center justify-center min-h-[200px]">
          <Card className="w-full max-w-md p-6 rounded-3xl border-0 shadow-lg">
            <CardContent className="flex flex-col items-center justify-center p-6">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <ShieldAlert className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Acesso Negado</h3>
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

    // Render the component if tenant is valid and user has required permissions
    // Pass additional tenant-related props to the component
    return (
      <Component 
        {...props} 
        tenant={tenant}
        tenantId={tenantId}
        validateTenantData={validateTenantData}
      />
    );
  };
}