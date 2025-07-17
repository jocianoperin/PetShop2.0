import { useEffect, useState } from 'react';
import { useTenant } from '@/contexts/TenantProvider';
import { useAuth } from '@/contexts/AuthProvider';

/**
 * Hook to validate tenant access for the current user
 * Returns loading state and validation result
 */
export function useTenantValidation() {
  const { tenant, tenantId, isLoading: isTenantLoading } = useTenant();
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [isValidating, setIsValidating] = useState(true);
  const [isValid, setIsValid] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const validateTenant = async () => {
      // Reset state
      setError(null);
      
      // If still loading tenant or auth info, wait
      if (isTenantLoading || isAuthLoading) {
        return;
      }

      // If not authenticated, show error
      if (!isAuthenticated) {
        setError('Usuário não autenticado');
        setIsValid(false);
        setIsValidating(false);
        return;
      }

      // If no tenant ID, show error
      if (!tenantId) {
        setError('Tenant não especificado');
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
      setError('Tenant inválido ou inativo');
      setIsValid(false);
      setIsValidating(false);
    };

    validateTenant();
  }, [tenant, tenantId, isAuthenticated, isTenantLoading, isAuthLoading]);

  return {
    isValidating,
    isValid,
    error,
    tenant,
    tenantId,
  };
}