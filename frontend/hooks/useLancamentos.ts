import { useState, useEffect, useCallback } from 'react';
import { useTenantData, useTenantCreate, useTenantUpdate, useTenantDelete } from './useTenantData';
import { useTenantApi } from './useTenantApi';
import { Lancamento } from '@/lib/api';

/**
 * Hook for managing lancamentos financeiros with tenant isolation
 */
export function useLancamentos() {
  const tenantApi = useTenantApi();
  
  // Use tenant-aware data fetching
  const { 
    data: lancamentos, 
    isLoading, 
    error, 
    refresh 
  } = useTenantData(tenantApi.getLancamentos, []);
  
  // Use tenant-aware create operation
  const { 
    create, 
    isCreating, 
    error: createError 
  } = useTenantCreate<Lancamento, Omit<Lancamento, 'id'>>(tenantApi.createLancamento);
  
  // Use tenant-aware update operation
  const { 
    update, 
    isUpdating, 
    error: updateError 
  } = useTenantUpdate<Lancamento, Partial<Lancamento>>(tenantApi.updateLancamento);
  
  // Use tenant-aware delete operation
  const { 
    remove, 
    isDeleting, 
    error: deleteError 
  } = useTenantDelete(tenantApi.deleteLancamento);
  
  return {
    lancamentos,
    isLoading,
    error,
    refresh,
    create,
    isCreating,
    createError,
    update,
    isUpdating,
    updateError,
    remove,
    isDeleting,
    deleteError
  };
}