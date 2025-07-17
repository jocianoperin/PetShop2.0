import { useState, useEffect, useCallback } from 'react';
import { useTenantData, useTenantCreate, useTenantUpdate, useTenantDelete } from './useTenantData';
import { useTenantApi } from './useTenantApi';
import { Servico } from '@/lib/api';

/**
 * Hook for managing serviços with tenant isolation
 */
export function useServicos() {
  const tenantApi = useTenantApi();
  
  // Use tenant-aware data fetching
  const { 
    data: servicos, 
    isLoading, 
    error, 
    refresh 
  } = useTenantData(tenantApi.getServicos, []);
  
  // Use tenant-aware create operation
  const { 
    create, 
    isCreating, 
    error: createError 
  } = useTenantCreate<Servico, Omit<Servico, 'id'>>(tenantApi.createServico);
  
  // Use tenant-aware update operation
  const { 
    update, 
    isUpdating, 
    error: updateError 
  } = useTenantUpdate<Servico, Partial<Servico>>(tenantApi.updateServico);
  
  // Use tenant-aware delete operation
  const { 
    remove, 
    isDeleting, 
    error: deleteError 
  } = useTenantDelete(tenantApi.deleteServico);
  
  return {
    servicos,
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