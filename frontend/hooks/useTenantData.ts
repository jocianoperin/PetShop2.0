import { useState, useEffect, useCallback } from 'react';
import { useTenant } from '@/contexts/TenantProvider';
import { useAuth } from '@/contexts/AuthProvider';

/**
 * Custom hook for fetching tenant-specific data with automatic tenant context
 * This hook ensures all data operations are properly isolated by tenant
 */
export function useTenantData<T>(
  fetchFunction: (tenantId?: string) => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { tenantId } = useTenant();
  const { isAuthenticated } = useAuth();

  const fetchData = useCallback(async () => {
    if (!tenantId || !isAuthenticated) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await fetchFunction(tenantId);
      setData(result);
    } catch (err) {
      console.error('Error fetching tenant data:', err);
      setError(err instanceof Error ? err : new Error('Unknown error occurred'));
    } finally {
      setIsLoading(false);
    }
  }, [tenantId, isAuthenticated, fetchFunction, ...dependencies]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, isLoading, error, refresh };
}

/**
 * Custom hook for creating tenant-specific data with automatic tenant context
 */
export function useTenantCreate<T, D>(
  createFunction: (data: D, tenantId?: string) => Promise<T>
) {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { tenantId } = useTenant();
  const { isAuthenticated } = useAuth();

  const create = useCallback(
    async (data: D) => {
      if (!tenantId || !isAuthenticated) {
        throw new Error('Tenant ID not available or user not authenticated');
      }

      setIsCreating(true);
      setError(null);

      try {
        const result = await createFunction(data, tenantId);
        return result;
      } catch (err) {
        console.error('Error creating tenant data:', err);
        const error = err instanceof Error ? err : new Error('Unknown error occurred');
        setError(error);
        throw error;
      } finally {
        setIsCreating(false);
      }
    },
    [tenantId, isAuthenticated, createFunction]
  );

  return { create, isCreating, error };
}

/**
 * Custom hook for updating tenant-specific data with automatic tenant context
 */
export function useTenantUpdate<T, D>(
  updateFunction: (id: number, data: D, tenantId?: string) => Promise<T>
) {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { tenantId } = useTenant();
  const { isAuthenticated } = useAuth();

  const update = useCallback(
    async (id: number, data: D) => {
      if (!tenantId || !isAuthenticated) {
        throw new Error('Tenant ID not available or user not authenticated');
      }

      setIsUpdating(true);
      setError(null);

      try {
        const result = await updateFunction(id, data, tenantId);
        return result;
      } catch (err) {
        console.error('Error updating tenant data:', err);
        const error = err instanceof Error ? err : new Error('Unknown error occurred');
        setError(error);
        throw error;
      } finally {
        setIsUpdating(false);
      }
    },
    [tenantId, isAuthenticated, updateFunction]
  );

  return { update, isUpdating, error };
}

/**
 * Custom hook for deleting tenant-specific data with automatic tenant context
 */
export function useTenantDelete(
  deleteFunction: (id: number, tenantId?: string) => Promise<void>
) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { tenantId } = useTenant();
  const { isAuthenticated } = useAuth();

  const remove = useCallback(
    async (id: number) => {
      if (!tenantId || !isAuthenticated) {
        throw new Error('Tenant ID not available or user not authenticated');
      }

      setIsDeleting(true);
      setError(null);

      try {
        await deleteFunction(id, tenantId);
      } catch (err) {
        console.error('Error deleting tenant data:', err);
        const error = err instanceof Error ? err : new Error('Unknown error occurred');
        setError(error);
        throw error;
      } finally {
        setIsDeleting(false);
      }
    },
    [tenantId, isAuthenticated, deleteFunction]
  );

  return { remove, isDeleting, error };
}