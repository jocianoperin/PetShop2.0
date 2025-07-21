import { useEffect, useState, useCallback } from 'react';
import { useTenant } from '@/contexts/TenantProvider';
import { useAuth } from '@/contexts/AuthProvider';
import { authService } from '@/services/api';

interface ValidationOptions {
  validateWithBackend?: boolean;
  requiredPermissions?: string[];
}

/**
 * Hook to validate tenant access for the current user
 * Returns loading state and validation result
 */
export function useTenantValidation(options: ValidationOptions = {}) {
  const { validateWithBackend = false, requiredPermissions = [] } = options;
  const { tenant, tenantId, isLoading: isTenantLoading } = useTenant();
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [isValidating, setIsValidating] = useState(true);
  const [isValid, setIsValid] = useState(false);
  const [hasPermissions, setHasPermissions] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Function to validate data ownership by tenant
  const validateDataOwnership = useCallback(<T extends { tenant_id?: string }>(
    data: T | T[] | null | undefined
  ): boolean => {
    if (!data || !tenantId) return false;
    
    // Handle array of data
    if (Array.isArray(data)) {
      // If empty array, consider it valid
      if (data.length === 0) return true;
      
      // Check if all items belong to current tenant or don't have tenant_id
      return data.every(item => !item.tenant_id || item.tenant_id === tenantId);
    }
    
    // Handle single data object
    return !data.tenant_id || data.tenant_id === tenantId;
  }, [tenantId]);

  // Function to check if user has required permissions
  const checkPermissions = useCallback((permissions: string[]): boolean => {
    if (!user || !permissions.length) return true;
    
    const userPermissions = user.permissions || [];
    return permissions.every(permission => userPermissions.includes(permission));
  }, [user]);

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

      try {
        // Validate with backend if requested
        if (validateWithBackend) {
          const isValidTenant = await authService.validateTenant(tenantId);
          
          if (!isValidTenant) {
            setError('Tenant inválido ou não encontrado');
            setIsValid(false);
            setIsValidating(false);
            return;
          }
        }

        // If tenant is loaded and active, check permissions
        if (tenant && tenant.is_active) {
          setIsValid(true);
          
          // Check if user has required permissions
          if (requiredPermissions.length > 0) {
            const hasAllPermissions = checkPermissions(requiredPermissions);
            setHasPermissions(hasAllPermissions);
            
            if (!hasAllPermissions) {
              setError('Permissões insuficientes');
            }
          }
          
          setIsValidating(false);
          return;
        }

        // Otherwise, tenant is invalid
        setError('Tenant inválido ou inativo');
        setIsValid(false);
        setIsValidating(false);
      } catch (err) {
        console.error('Error validating tenant:', err);
        setError('Erro ao validar tenant');
        setIsValid(false);
        setIsValidating(false);
      }
    };

    validateTenant();
  }, [tenant, tenantId, isAuthenticated, isTenantLoading, isAuthLoading, validateWithBackend, requiredPermissions, checkPermissions]);

  return {
    isValidating,
    isValid,
    hasPermissions,
    error,
    tenant,
    tenantId,
    validateDataOwnership,
    checkPermissions
  };
}