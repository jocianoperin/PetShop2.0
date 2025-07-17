import { useState, useEffect, useCallback } from 'react';
import { useTenantData, useTenantCreate, useTenantUpdate, useTenantDelete } from './useTenantData';
import { useTenantApi } from './useTenantApi';
import { Cliente } from '@/lib/api';

/**
 * Hook for managing clientes with tenant isolation
 */
export function useClientes() {
  const tenantApi = useTenantApi();
  
  // Use tenant-aware data fetching
  const { 
    data: clientes, 
    isLoading, 
    error, 
    refresh 
  } = useTenantData(tenantApi.getClientes, []);
  
  // Use tenant-aware create operation
  const { 
    create, 
    isCreating, 
    error: createError 
  } = useTenantCreate<Cliente, Omit<Cliente, 'id'>>(tenantApi.createCliente);
  
  // Use tenant-aware update operation
  const { 
    update, 
    isUpdating, 
    error: updateError 
  } = useTenantUpdate<Cliente, Partial<Cliente>>(tenantApi.updateCliente);
  
  // Use tenant-aware delete operation
  const { 
    remove, 
    isDeleting, 
    error: deleteError 
  } = useTenantDelete(tenantApi.deleteCliente);
  
  return {
    clientes,
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