import { useState, useEffect, useCallback } from 'react';
import { useTenantData, useTenantCreate, useTenantUpdate, useTenantDelete } from './useTenantData';
import { useTenantApi } from './useTenantApi';
import { Hospedagem } from '@/lib/api';

/**
 * Hook for managing hospedagens with tenant isolation
 */
export function useHospedagens() {
  const tenantApi = useTenantApi();
  
  // Use tenant-aware data fetching
  const { 
    data: hospedagens, 
    isLoading, 
    error, 
    refresh 
  } = useTenantData(tenantApi.getHospedagens, []);
  
  // Use tenant-aware create operation
  const { 
    create, 
    isCreating, 
    error: createError 
  } = useTenantCreate<Hospedagem, Omit<Hospedagem, 'id' | 'status'>>(tenantApi.createHospedagem);
  
  // Use tenant-aware update operation
  const { 
    update, 
    isUpdating, 
    error: updateError 
  } = useTenantUpdate<Hospedagem, Partial<Hospedagem>>(tenantApi.updateHospedagem);
  
  // Use tenant-aware delete operation
  const { 
    remove, 
    isDeleting, 
    error: deleteError 
  } = useTenantDelete(tenantApi.deleteHospedagem);
  
  return {
    hospedagens,
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